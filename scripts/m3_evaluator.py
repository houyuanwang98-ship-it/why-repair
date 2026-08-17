"""Evaluate Evaluator v1 outputs against proof- and node-level M3 gold data."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


MISSING = "__missing__"
NODE_STATUS_GROUPS = {
    "closed": "accepted",
    "valid_with_gap": "gap",
    "missing_bridge_lemma": "gap",
    "missing_assumption": "invalid",
    "theorem_misuse": "invalid",
    "algebraic_invalidity": "invalid",
    "false_theorem": "invalid",
    "downstream_invalid": "invalid",
    "undetermined": "undetermined",
}
ERROR_TYPE_MAP = {
    "missing_bridge_lemma": "proof_gap",
    "false_theorem": "false_generalization",
    "false_local_claim": "false_generalization",
    "dependency_error": "false_generalization",
}
NODE_TYPE_MAP = {"calculation": "calculation_step", "citation": "introduction"}


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def load_predictions(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.is_dir():
        return [json.loads(item.read_text(encoding="utf-8")) for item in sorted(source.glob("*.json"))]
    return read_jsonl(source)


def sha256_path(path: str | Path) -> str:
    source = Path(path)
    digest = hashlib.sha256()
    items = sorted(source.glob("*.json")) if source.is_dir() else [source]
    for item in items:
        if source.is_dir():
            digest.update(item.name.encode("utf-8"))
            digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def sample_id(row: dict[str, Any]) -> str:
    value = row.get("proof_id", row.get("sample_id", row.get("id", "")))
    return value if isinstance(value, str) else ""


def normalize_node_id(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value[1:] if value.startswith("n") else value
        return int(text) if text.isdigit() else None
    return None


def prediction_error_type(row: dict[str, Any]) -> Any:
    value = row.get("error_type")
    if value is None and row.get("validity_status") == "valid":
        value = "no_error"
    if value is None and row.get("validity_status") == "valid_with_gap":
        value = "proof_gap"
    if value is None and row.get("validity_status") == "undetermined":
        value = "undetermined"
    if value is None:
        graph = row.get("proof_graph", [])
        invalid_step = row.get("first_invalid_step")
        invalid_id = normalize_node_id(invalid_step)
        if invalid_id is not None:
            node = next((n for n in graph if normalize_node_id(n.get("node_id")) == invalid_id), None)
            value = node.get("error_type") if node else None
    return ERROR_TYPE_MAP.get(value, value)


def prediction_validity(row: dict[str, Any]) -> Any:
    value = row.get("validity_status", MISSING)
    return "invalid" if value == "false_theorem" else value


def classification_metrics(gold: list[Any], predicted: list[Any]) -> dict[str, Any]:
    if len(gold) != len(predicted):
        raise ValueError("gold and predicted label arrays must have equal length")
    labels = sorted(set(gold), key=str)
    per_label = {}
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[str(label)] = {
            "support": sum(g == label for g in gold),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {
        "count": len(gold),
        "accuracy": sum(g == p for g, p in zip(gold, predicted)) / len(gold) if gold else None,
        "macro_f1": sum(item["f1"] for item in per_label.values()) / len(per_label) if per_label else None,
        "per_label": per_label,
    }


def localization_metrics(gold: list[int | None], predicted: list[int | None]) -> dict[str, Any]:
    applicable = [(g, p) for g, p in zip(gold, predicted) if g is not None]
    null_gold = [(g, p) for g, p in zip(gold, predicted) if g is None]
    return {
        "applicable_count": len(applicable),
        "exact_accuracy": sum(g == p for g, p in applicable) / len(applicable) if applicable else None,
        "false_positive_rate_when_absent": (
            sum(p is not None for _, p in null_gold) / len(null_gold) if null_gold else None
        ),
    }


def _gold_nodes(row: dict[str, Any]) -> list[dict[str, Any]]:
    value = row.get("gold_nodes", [])
    return value if isinstance(value, list) else []


def _prediction_nodes(row: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {}
    for node in row.get("proof_graph", []):
        node_id = normalize_node_id(node.get("node_id"))
        if node_id is not None:
            result[node_id] = node
    return result


def evaluate(gold_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gold_map = {sample_id(row): row for row in gold_rows}
    pred_map = {sample_id(row): row for row in prediction_rows}
    if "" in gold_map or len(gold_map) != len(gold_rows):
        raise ValueError("gold rows require unique identifiers")
    if "" in pred_map or len(pred_map) != len(prediction_rows):
        raise ValueError("prediction rows require unique identifiers")

    ids = sorted(gold_map)
    proof_gold, proof_pred = [], []
    error_gold, error_pred = [], []
    gap_gold, gap_pred, invalid_gold, invalid_pred = [], [], [], []
    node_type_gold, node_type_pred = [], []
    node_status_gold, node_status_pred = [], []
    gold_edges, pred_edges = set(), set()
    details = []

    for item_id in ids:
        gold = gold_map[item_id]
        pred = pred_map.get(item_id, {})
        proof_gold.append(gold["gold_validity_status"])
        proof_pred.append(prediction_validity(pred))
        error_gold.append(gold["gold_error_type"])
        error_pred.append(prediction_error_type(pred) if pred else MISSING)
        gap_gold.append(gold.get("gold_first_gap_step"))
        gap_pred.append(normalize_node_id(pred.get("first_gap_step")))
        invalid_gold.append(gold.get("gold_first_invalid_step"))
        invalid_pred.append(normalize_node_id(pred.get("first_invalid_step")))

        pred_nodes = _prediction_nodes(pred)
        for node in _gold_nodes(gold):
            node_id = normalize_node_id(node.get("node_id"))
            predicted_node = pred_nodes.get(node_id, {})
            gold_type = NODE_TYPE_MAP.get(node["node_type"], node["node_type"])
            pred_type = NODE_TYPE_MAP.get(predicted_node.get("node_type"), predicted_node.get("node_type", MISSING))
            node_type_gold.append(gold_type)
            node_type_pred.append(pred_type)
            node_status_gold.append(node["verdict_group"])
            node_status_pred.append(NODE_STATUS_GROUPS.get(predicted_node.get("status"), MISSING))
            for parent in node.get("depends_on", []):
                parent_id = normalize_node_id(parent)
                if parent_id is not None:
                    gold_edges.add((item_id, parent_id, node_id))
            for parent in predicted_node.get("depends_on", []):
                parent_id = normalize_node_id(parent)
                if parent_id is not None:
                    pred_edges.add((item_id, parent_id, node_id))

        details.append({
            "sample_id": item_id,
            "prediction_present": item_id in pred_map,
            "gold_validity_status": proof_gold[-1],
            "predicted_validity_status": proof_pred[-1],
            "validity_correct": proof_gold[-1] == proof_pred[-1],
            "gold_first_gap_step": gap_gold[-1],
            "predicted_first_gap_step": gap_pred[-1],
            "gold_first_invalid_step": invalid_gold[-1],
            "predicted_first_invalid_step": invalid_pred[-1],
        })

    true_edges = len(gold_edges & pred_edges)
    edge_precision = true_edges / len(pred_edges) if pred_edges else (1.0 if not gold_edges else 0.0)
    edge_recall = true_edges / len(gold_edges) if gold_edges else (1.0 if not pred_edges else 0.0)
    edge_f1 = 2 * edge_precision * edge_recall / (edge_precision + edge_recall) if edge_precision + edge_recall else 0.0
    report = {
        "schema_version": "m3-evaluator-report-0.1",
        "sample_count": len(ids),
        "prediction_coverage": sum(item_id in pred_map for item_id in ids) / len(ids) if ids else None,
        "proof_validity": classification_metrics(proof_gold, proof_pred),
        "error_type": classification_metrics(error_gold, error_pred),
        "first_gap_localization": localization_metrics(gap_gold, gap_pred),
        "first_invalid_localization": localization_metrics(invalid_gold, invalid_pred),
        "node_type": classification_metrics(node_type_gold, node_type_pred),
        "node_verdict_group": classification_metrics(node_status_gold, node_status_pred),
        "dependency_edges": {
            "gold_count": len(gold_edges), "predicted_count": len(pred_edges), "true_positive": true_edges,
            "precision": edge_precision, "recall": edge_recall, "f1": edge_f1,
        },
        "node_gold_coverage": {
            "samples": sum(bool(_gold_nodes(row)) for row in gold_rows),
            "nodes": len(node_type_gold),
        },
        "unexpected_prediction_ids": sorted(set(pred_map) - set(gold_map)),
    }
    return report, details


def write_json(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True, help="JSONL file or directory of JSON predictions")
    parser.add_argument("--report", required=True)
    parser.add_argument("--details")
    parser.add_argument("--ids", nargs="*", help="Optional proof IDs to evaluate")
    args = parser.parse_args()
    gold_rows = read_jsonl(args.gold)
    prediction_rows = load_predictions(args.predictions)
    if args.ids:
        selected = set(args.ids)
        gold_rows = [row for row in gold_rows if sample_id(row) in selected]
        prediction_rows = [row for row in prediction_rows if sample_id(row) in selected]
        missing = selected - {sample_id(row) for row in gold_rows}
        if missing:
            raise SystemExit(f"Unknown gold IDs: {', '.join(sorted(missing))}")
    report, details = evaluate(gold_rows, prediction_rows)
    report["inputs"] = {
        "gold_sha256": sha256_path(args.gold),
        "predictions_sha256": sha256_path(args.predictions),
    }
    write_json(args.report, report)
    if args.details:
        write_jsonl(args.details, details)
    print(f"Evaluated {report['sample_count']} samples; coverage={report['prediction_coverage']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
