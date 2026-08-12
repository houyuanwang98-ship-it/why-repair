"""M3-alpha module runner and metrics without a benchmark Gold dependency.

This module is owned by the execution harness.  It deliberately does not map
M2 labels to M1 verdicts and does not modify the frozen M1 v0.3 contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from time import perf_counter
from typing import Any, Callable, Iterable, Mapping


M3_ALPHA_VERSION = "m3-alpha.1"
MODULES = ("segmentation", "classification", "dependency", "localization", "verdict")
UPSTREAM_MODES = {"gold_upstream", "predicted_upstream"}
NODE_LABELS = {"definition", "assumption", "introduction", "claim", "calculation", "conclusion", "citation"}
NORMALIZED_VERDICTS = {"accepted", "accepted_with_gap", "invalid", "undetermined"}


class M3AlphaError(ValueError):
    """Raised when an M3-alpha run or metric input is malformed."""


@dataclass(frozen=True)
class AdapterResponse:
    output: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float | None = None


Adapter = Callable[[str, dict[str, Any]], AdapterResponse]


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_module(module: str, upstream_mode: str) -> None:
    if module not in MODULES:
        raise M3AlphaError(f"unknown module: {module!r}")
    if upstream_mode not in UPSTREAM_MODES:
        raise M3AlphaError(f"unknown upstream mode: {upstream_mode!r}")


def _validate_spans(value: Any, *, path: str) -> list[tuple[int, int]]:
    if not isinstance(value, list) or not value:
        raise M3AlphaError(f"{path} must be a nonempty array")
    spans: list[tuple[int, int]] = []
    for index, span in enumerate(value):
        if (
            not isinstance(span, (list, tuple))
            or len(span) != 2
            or any(not isinstance(item, int) or isinstance(item, bool) for item in span)
            or span[0] < 0
            or span[0] >= span[1]
        ):
            raise M3AlphaError(f"{path}[{index}] must be an increasing nonnegative [start, end] pair")
        spans.append((span[0], span[1]))
    if spans[0][0] != 0:
        raise M3AlphaError(f"{path} must start at offset 0")
    if any(left[1] != right[0] for left, right in zip(spans, spans[1:])):
        raise M3AlphaError(f"{path} must be ordered, contiguous, and non-overlapping")
    return spans


def _node_count(sample: Mapping[str, Any], module: str) -> int:
    key = "node_count"
    value = sample.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise M3AlphaError(f"{module} sample requires positive {key}")
    return value


def _validate_edges(value: Any, *, path: str, node_count: int | None = None) -> set[tuple[int, int]]:
    if not isinstance(value, list):
        raise M3AlphaError(f"{path} must be an array")
    edges: set[tuple[int, int]] = set()
    for index, edge in enumerate(value):
        if (
            not isinstance(edge, (list, tuple))
            or len(edge) != 2
            or any(not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in edge)
        ):
            raise M3AlphaError(f"{path}[{index}] must be a pair of positive node ids")
        source, target = edge
        if source >= target:
            raise M3AlphaError(f"{path}[{index}] must point from an earlier node to a later node")
        if node_count is not None and target > node_count:
            raise M3AlphaError(f"{path}[{index}] references an unknown node")
        if (source, target) in edges:
            raise M3AlphaError(f"{path} contains duplicate edges")
        edges.add((source, target))
    return edges


def validate_module_output(module: str, sample: Mapping[str, Any], output: Any) -> dict[str, Any]:
    """Fail closed on malformed or semantically impossible adapter output."""
    if not isinstance(output, dict):
        raise M3AlphaError("adapter output must be an object")
    expected = {
        "segmentation": {"spans"},
        "classification": {"labels"},
        "dependency": {"edges"},
        "localization": {"first_error_step"},
        "verdict": {"verdicts"},
    }[module]
    if set(output) != expected:
        raise M3AlphaError(f"{module} output fields must be exactly {sorted(expected)}")
    if module == "segmentation":
        spans = _validate_spans(output["spans"], path="output.spans")
        source_length = sample.get("source_length")
        if not isinstance(source_length, int) or isinstance(source_length, bool) or source_length < 1:
            raise M3AlphaError("segmentation sample requires positive source_length")
        if spans[-1][1] != source_length:
            raise M3AlphaError("output.spans must cover the complete source")
    elif module == "classification":
        count = _node_count(sample, module)
        labels = output["labels"]
        if not isinstance(labels, list) or len(labels) != count or any(label not in NODE_LABELS for label in labels):
            raise M3AlphaError("classification labels must cover every node with allowed labels")
    elif module == "dependency":
        _validate_edges(output["edges"], path="output.edges", node_count=_node_count(sample, module))
    elif module == "localization":
        count = _node_count(sample, module)
        step = output["first_error_step"]
        if step is not None and (not isinstance(step, int) or isinstance(step, bool) or not 1 <= step <= count):
            raise M3AlphaError("first_error_step must be null or a valid 1-based node index")
    else:
        count = _node_count(sample, module)
        verdicts = output["verdicts"]
        if not isinstance(verdicts, list) or len(verdicts) != count or any(item not in NORMALIZED_VERDICTS for item in verdicts):
            raise M3AlphaError("verdicts must cover every node with normalized M3 verdicts")
    return output


def run_module(
    *,
    module: str,
    samples: Iterable[Mapping[str, Any]],
    adapter: Adapter,
    adapter_id: str,
    model: str,
    prompt_version: str,
    upstream_mode: str,
    run_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Run one isolated module and return predictions plus an audit manifest."""
    _validate_module(module, upstream_mode)
    if not all(isinstance(value, str) and value.strip() for value in (adapter_id, model, prompt_version)):
        raise M3AlphaError("adapter_id, model, and prompt_version must be nonempty strings")
    rows = [dict(row) for row in samples]
    if any(not isinstance(row.get("sample_id"), str) or not row["sample_id"] for row in rows):
        raise M3AlphaError("every sample requires a nonempty sample_id")
    if len({row["sample_id"] for row in rows}) != len(rows):
        raise M3AlphaError("sample_id values must be unique")
    input_digest = _digest(rows)
    from .contracts import ContractError, validate_contract
    try:
        frozen_manifest = dict(run_manifest)
        validate_contract("run_manifest", frozen_manifest)
    except (ContractError, TypeError, ValueError) as exc:
        raise M3AlphaError(f"invalid M1 RunManifest: {exc}") from exc
    if frozen_manifest["input_digest"] != input_digest:
        raise M3AlphaError("RunManifest input_digest does not bind the exact module inputs")
    if frozen_manifest["agents"]["evaluator"] != adapter_id:
        raise M3AlphaError("RunManifest evaluator does not match adapter_id")
    if frozen_manifest["prompt_versions"]["evaluator"] != prompt_version:
        raise M3AlphaError("RunManifest evaluator prompt does not match prompt_version")
    if frozen_manifest["model_parameters"].get("model") != model:
        raise M3AlphaError("RunManifest model_parameters.model does not match model")

    predictions = []
    calls = []
    started = perf_counter()
    for row in rows:
        call_started = perf_counter()
        response: AdapterResponse | None = None
        try:
            response = adapter(module, row)
            if not isinstance(response, AdapterResponse):
                raise M3AlphaError("adapter must return AdapterResponse")
            if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in (response.input_tokens, response.output_tokens)):
                raise M3AlphaError("token counts must be nonnegative integers")
            if response.estimated_cost is not None and (
                not isinstance(response.estimated_cost, (int, float))
                or isinstance(response.estimated_cost, bool)
                or not math.isfinite(response.estimated_cost)
                or response.estimated_cost < 0
            ):
                raise M3AlphaError("estimated_cost must be a finite nonnegative number or null")
            output = validate_module_output(module, row, response.output)
            predictions.append({"sample_id": row["sample_id"], "output": output})
            call = {
                "sample_id": row["sample_id"], "status": "completed",
                "input_tokens": response.input_tokens, "output_tokens": response.output_tokens,
                "estimated_cost": response.estimated_cost, "error_type": None, "error": None,
            }
        except Exception as exc:  # preserve every failed external call in the audit
            valid_input_tokens = (
                response.input_tokens if response and isinstance(response.input_tokens, int)
                and not isinstance(response.input_tokens, bool) and response.input_tokens >= 0 else 0
            )
            valid_output_tokens = (
                response.output_tokens if response and isinstance(response.output_tokens, int)
                and not isinstance(response.output_tokens, bool) and response.output_tokens >= 0 else 0
            )
            valid_cost = (
                response.estimated_cost if response and isinstance(response.estimated_cost, (int, float))
                and not isinstance(response.estimated_cost, bool)
                and math.isfinite(response.estimated_cost) and response.estimated_cost >= 0 else None
            )
            call = {
                "sample_id": row["sample_id"], "status": "failed",
                "input_tokens": valid_input_tokens,
                "output_tokens": valid_output_tokens,
                "estimated_cost": valid_cost,
                "error_type": type(exc).__name__, "error": str(exc),
            }
        call["latency_ms"] = round((perf_counter() - call_started) * 1000, 3)
        calls.append(call)
    elapsed_ms = (perf_counter() - started) * 1000
    return {
        "contract_version": M3_ALPHA_VERSION,
        "module": module,
        "upstream_mode": upstream_mode,
        "predictions": predictions,
        "run_manifest": frozen_manifest,
        "manifest": {
            "adapter_id": adapter_id,
            "model": model,
            "prompt_version": prompt_version,
            "input_digest": input_digest,
            "run_manifest_digest": _digest(frozen_manifest),
            "status": "completed" if len(predictions) == len(rows) else ("failed" if not predictions else "partial"),
            "sample_count": len(rows),
            "model_call_count": len(calls),
            "successful_call_count": len(predictions),
            "failed_call_count": len(calls) - len(predictions),
            "input_tokens": sum(call["input_tokens"] for call in calls),
            "output_tokens": sum(call["output_tokens"] for call in calls),
            "estimated_cost": (
                None if any(call["estimated_cost"] is None for call in calls)
                else sum(call["estimated_cost"] for call in calls)
            ),
            "latency_ms": round(elapsed_ms, 3),
            "calls": calls,
        },
    }


def _prf(predicted: set[Any], gold: set[Any]) -> dict[str, float | int]:
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / (tp + fp) if tp + fp else (1.0 if not gold else 0.0)
    recall = tp / (tp + fn) if tp + fn else (1.0 if not predicted else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def segmentation_metrics(predicted_spans: Iterable[Iterable[int]], gold_spans: Iterable[Iterable[int]]) -> dict[str, Any]:
    """Score exact nonterminal boundaries derived from [start, end] spans."""
    def boundaries(spans: Iterable[Iterable[int]]) -> set[int]:
        normalized = _validate_spans(list(spans), path="spans")
        return {span[1] for span in normalized[:-1]}
    return _prf(boundaries(predicted_spans), boundaries(gold_spans))


def macro_f1(predicted: Iterable[str], gold: Iterable[str]) -> dict[str, Any]:
    pred, truth = list(predicted), list(gold)
    if len(pred) != len(truth):
        raise M3AlphaError("predicted and gold labels must have equal length")
    if any(not isinstance(value, str) or not value for value in pred + truth):
        raise M3AlphaError("labels must be nonempty strings")
    labels = sorted(set(pred) | set(truth))
    per_label = {}
    for label in labels:
        per_label[label] = _prf(
            {i for i, value in enumerate(pred) if value == label},
            {i for i, value in enumerate(truth) if value == label},
        )
    return {
        "macro_f1": sum(item["f1"] for item in per_label.values()) / len(labels) if labels else 1.0,
        "labels": per_label,
        "count": len(truth),
    }


def dependency_edge_metrics(predicted: Iterable[Iterable[Any]], gold: Iterable[Iterable[Any]]) -> dict[str, Any]:
    return _prf(
        _validate_edges(list(predicted), path="predicted edges"),
        _validate_edges(list(gold), path="gold edges"),
    )


def first_error_metrics(predicted: Iterable[int | None], gold: Iterable[int | None]) -> dict[str, Any]:
    pred, truth = list(predicted), list(gold)
    if len(pred) != len(truth):
        raise M3AlphaError("predicted and gold locations must have equal length")
    if any(value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1) for value in pred + truth):
        raise M3AlphaError("locations must be null or positive 1-based indices")
    correct = sum(left == right for left, right in zip(pred, truth))
    return {"accuracy": correct / len(truth) if truth else 1.0, "correct": correct, "count": len(truth)}


def false_acceptance_rate(predicted: Iterable[str], gold: Iterable[str]) -> dict[str, Any]:
    """Rate at which truly invalid nodes are predicted as accepted."""
    pred, truth = list(predicted), list(gold)
    if len(pred) != len(truth):
        raise M3AlphaError("predicted and gold verdicts must have equal length")
    if any(value not in NORMALIZED_VERDICTS for value in pred + truth):
        raise M3AlphaError("false acceptance requires normalized M3 verdicts")
    invalid_indices = [i for i, value in enumerate(truth) if value == "invalid"]
    false_accepts = sum(pred[i] in {"accepted", "accepted_with_gap"} for i in invalid_indices)
    return {
        "false_acceptance_rate": false_accepts / len(invalid_indices) if invalid_indices else 0.0,
        "false_accepts": false_accepts,
        "gold_invalid": len(invalid_indices),
    }


def evaluate_module(module: str, predicted: Mapping[str, Any], gold: Mapping[str, Any], *, upstream_mode: str) -> dict[str, Any]:
    """Dispatch one module metric while preserving the isolation mode."""
    _validate_module(module, upstream_mode)
    if module == "segmentation":
        metrics = segmentation_metrics(predicted["spans"], gold["spans"])
    elif module == "classification":
        metrics = macro_f1(predicted["labels"], gold["labels"])
    elif module == "dependency":
        metrics = dependency_edge_metrics(predicted["edges"], gold["edges"])
    elif module == "localization":
        metrics = first_error_metrics(predicted["first_error_steps"], gold["first_error_steps"])
    else:
        metrics = {
            **macro_f1(predicted["verdicts"], gold["verdicts"]),
            **false_acceptance_rate(predicted["verdicts"], gold["verdicts"]),
        }
    return {"contract_version": M3_ALPHA_VERSION, "module": module, "upstream_mode": upstream_mode, "metrics": metrics}


def evaluate_dataset(
    module: str,
    predicted_rows: Iterable[Mapping[str, Any]],
    gold_rows: Iterable[Mapping[str, Any]],
    *,
    upstream_mode: str,
) -> dict[str, Any]:
    """Align normalized module artifacts by sample id and score a full dataset."""
    _validate_module(module, upstream_mode)

    def indexed(rows: Iterable[Mapping[str, Any]], side: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for index, raw in enumerate(rows):
            row = dict(raw)
            sample_id = row.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id:
                raise M3AlphaError(f"{side}[{index}] requires a nonempty sample_id")
            if set(row) != {"sample_id", "output"} or not isinstance(row["output"], dict):
                raise M3AlphaError(f"{side}[{index}] must contain exactly sample_id and object output")
            if sample_id in result:
                raise M3AlphaError(f"{side} contains duplicate sample_id {sample_id!r}")
            result[sample_id] = row["output"]
        return result

    predicted = indexed(predicted_rows, "predicted")
    gold = indexed(gold_rows, "gold")
    if set(predicted) != set(gold):
        missing = sorted(set(gold) - set(predicted))
        extra = sorted(set(predicted) - set(gold))
        raise M3AlphaError(f"prediction/Gold sample mismatch; missing={missing}, extra={extra}")

    sample_ids = sorted(gold)
    if module == "segmentation":
        pred_boundaries: set[tuple[str, int]] = set()
        gold_boundaries: set[tuple[str, int]] = set()
        for sample_id in sample_ids:
            pred_spans = _validate_spans(predicted[sample_id].get("spans"), path=f"predicted[{sample_id}].spans")
            gold_spans = _validate_spans(gold[sample_id].get("spans"), path=f"gold[{sample_id}].spans")
            if pred_spans[-1][1] != gold_spans[-1][1]:
                raise M3AlphaError(f"segmentation source length mismatch for {sample_id!r}")
            pred_boundaries |= {(sample_id, span[1]) for span in pred_spans[:-1]}
            gold_boundaries |= {(sample_id, span[1]) for span in gold_spans[:-1]}
        metrics = _prf(pred_boundaries, gold_boundaries)
    elif module in {"classification", "verdict"}:
        key = "labels" if module == "classification" else "verdicts"
        pred_labels: list[str] = []
        gold_labels: list[str] = []
        for sample_id in sample_ids:
            left, right = predicted[sample_id].get(key), gold[sample_id].get(key)
            if not isinstance(left, list) or not isinstance(right, list):
                raise M3AlphaError(f"{module} dataset outputs require {key} arrays")
            pred_labels.extend(left)
            gold_labels.extend(right)
        if module == "classification" and any(label not in NODE_LABELS for label in pred_labels + gold_labels):
            raise M3AlphaError("classification dataset requires normalized node labels")
        metrics = macro_f1(pred_labels, gold_labels)
        if module == "verdict":
            metrics.update(false_acceptance_rate(pred_labels, gold_labels))
    elif module == "dependency":
        pred_edges: set[tuple[str, int, int]] = set()
        gold_edges: set[tuple[str, int, int]] = set()
        for sample_id in sample_ids:
            left = _validate_edges(predicted[sample_id].get("edges"), path=f"predicted[{sample_id}].edges")
            right = _validate_edges(gold[sample_id].get("edges"), path=f"gold[{sample_id}].edges")
            pred_edges |= {(sample_id, *edge) for edge in left}
            gold_edges |= {(sample_id, *edge) for edge in right}
        metrics = _prf(pred_edges, gold_edges)
    else:
        pred_steps = [predicted[sample_id].get("first_error_step") for sample_id in sample_ids]
        gold_steps = [gold[sample_id].get("first_error_step") for sample_id in sample_ids]
        metrics = first_error_metrics(pred_steps, gold_steps)
    return {
        "contract_version": M3_ALPHA_VERSION,
        "module": module,
        "upstream_mode": upstream_mode,
        "sample_count": len(sample_ids),
        "sample_ids_digest": _digest(sample_ids),
        "metrics": metrics,
    }
