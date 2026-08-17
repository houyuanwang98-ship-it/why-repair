"""Compatible M3 evaluator report v0.2 with the full acceptance-plan metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import m3_evaluator as v1


def _first(gap, invalid):
    values = [value for value in (gap, invalid) if value is not None]
    return min(values) if values else None


def evaluate(gold_rows, prediction_rows):
    report, details = v1.evaluate(gold_rows, prediction_rows)
    pred_map = {v1.sample_id(row): row for row in prediction_rows}
    first_gold = [_first(row.get("gold_first_gap_step"), row.get("gold_first_invalid_step")) for row in gold_rows]
    first_pred = [
        _first(
            v1.normalize_node_id(pred_map.get(v1.sample_id(row), {}).get("first_gap_step")),
            v1.normalize_node_id(pred_map.get(v1.sample_id(row), {}).get("first_invalid_step")),
        )
        for row in gold_rows
    ]
    gold_statuses = []
    predicted_statuses = []
    for gold in gold_rows:
        predicted_nodes = v1._prediction_nodes(pred_map.get(v1.sample_id(gold), {}))
        for node in v1._gold_nodes(gold):
            gold_statuses.append(node["verdict_group"])
            predicted = predicted_nodes.get(v1.normalize_node_id(node["node_id"]), {})
            predicted_statuses.append(v1.NODE_STATUS_GROUPS.get(predicted.get("status"), v1.MISSING))
    invalid_indices = [index for index, value in enumerate(gold_statuses) if value == "invalid"]
    false_accepts = sum(predicted_statuses[index] in {"accepted", "gap"} for index in invalid_indices)
    proof_predictions = [v1.prediction_validity(pred_map.get(v1.sample_id(row), {})) for row in gold_rows]
    proof_invalid_indices = [index for index, row in enumerate(gold_rows) if row["gold_validity_status"] == "invalid"]
    proof_false_accepts = sum(proof_predictions[index] in {"valid", "valid_with_gap"} for index in proof_invalid_indices)
    first_error = v1.localization_metrics(first_gold, first_pred)
    first_error.update({
        "overall_count": len(first_gold),
        "overall_correct": sum(gold == predicted for gold, predicted in zip(first_gold, first_pred)),
        "overall_accuracy": sum(gold == predicted for gold, predicted in zip(first_gold, first_pred)) / len(first_gold) if first_gold else None,
    })
    report.update({
        "schema_version": "m3-evaluator-report-0.2",
        "segmentation": {
            "status": "not_evaluable",
            "reason": "frozen M3 Gold has ordered proof steps but no character-span boundaries",
            "boundary_f1": None,
        },
        "first_error_localization": first_error,
        "safety_rates": {
            "node_false_acceptance_rate": false_accepts / len(invalid_indices) if invalid_indices else 0.0,
            "node_false_accepts": false_accepts,
            "gold_invalid_nodes": len(invalid_indices),
            "proof_false_acceptance_rate": proof_false_accepts / len(proof_invalid_indices) if proof_invalid_indices else 0.0,
            "proof_false_accepts": proof_false_accepts,
            "gold_invalid_proofs": len(proof_invalid_indices),
            "proof_abstention_rate": sum(value == "undetermined" for value in proof_predictions) / len(proof_predictions) if proof_predictions else 0.0,
            "node_abstention_rate": sum(value == "undetermined" for value in predicted_statuses) / len(predicted_statuses) if predicted_statuses else 0.0,
        },
    })
    report["dependency_edges"]["critical_dependency_omission_rate"] = 1.0 - report["dependency_edges"]["recall"]
    return report, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--details")
    args = parser.parse_args()
    gold_rows = v1.read_jsonl(args.gold)
    prediction_rows = v1.load_predictions(args.predictions)
    report, details = evaluate(gold_rows, prediction_rows)
    report["inputs"] = {
        "gold_sha256": v1.sha256_path(args.gold),
        "predictions_sha256": v1.sha256_path(args.predictions),
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if args.details:
        v1.write_jsonl(args.details, details)
    print(f"Evaluated {report['sample_count']} samples; coverage={report['prediction_coverage']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
