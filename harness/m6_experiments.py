"""M6 Person B experiment definitions and pre-entry fixture machinery.

This module deliberately cannot run a pilot while the bound M5 gate is closed.
It implements configuration, isolation and scoring contracts only; model/provider
execution remains a later Controller action after human sign-off.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from harness.execution_release import release_allows


M6_PERSON_B_VERSION = "m6-person-b-0.1"
METHOD_IDS = (
    "direct_judgment", "self_reflection", "generator_critic", "no_graph",
    "no_structured_certificate", "no_counterexample_protocol",
    "no_descendant_invalidation", "single_round_repair", "full_system",
)
FAILURE_TYPES = {
    "api_error", "timeout", "budget_exhausted", "schema_invalid",
    "tool_error", "retry_exhausted",
}
GOLD_VERDICTS = {"accepted", "gap", "invalid", "undetermined"}
PREDICTED_VERDICTS = GOLD_VERDICTS | {"accepted_with_gap"}


class M6ExperimentError(ValueError):
    """Raised when a proposed M6 configuration violates the locked protocol."""


@dataclass(frozen=True)
class MethodSpec:
    method_id: str
    sees_nodes: bool
    sees_graph: bool
    structured_certificate: bool
    counterexample_protocol: bool
    descendant_invalidation: bool
    produces_patch: bool
    max_patch_rounds: int
    role_calls: int


METHOD_SPECS = {
    spec.method_id: spec for spec in (
        MethodSpec("direct_judgment", False, False, False, False, False, False, 0, 1),
        MethodSpec("self_reflection", False, False, False, False, False, False, 0, 2),
        MethodSpec("generator_critic", False, False, False, False, False, False, 0, 2),
        MethodSpec("no_graph", True, False, True, True, False, True, 3, 4),
        MethodSpec("no_structured_certificate", True, True, False, True, True, True, 3, 4),
        MethodSpec("no_counterexample_protocol", True, True, True, False, True, True, 3, 4),
        MethodSpec("no_descendant_invalidation", True, True, True, True, False, True, 3, 4),
        MethodSpec("single_round_repair", True, True, True, True, True, True, 1, 4),
        MethodSpec("full_system", True, True, True, True, True, True, 3, 4),
    )
}
ABLATION_DIFFERENCES = {
    "no_graph": {"sees_graph", "descendant_invalidation"},
    "no_structured_certificate": {"structured_certificate"},
    "no_counterexample_protocol": {"counterexample_protocol"},
    "no_descendant_invalidation": {"descendant_invalidation"},
    "single_round_repair": {"max_patch_rounds"},
}
COMPARISON_FAMILIES = {
    "H1": {"full_system", "direct_judgment", "self_reflection", "generator_critic"},
    "H2": {"full_system", "no_structured_certificate", "no_counterexample_protocol"},
    "H3": {"full_system", "no_graph", "no_descendant_invalidation", "single_round_repair"},
}
REPAIR_SUCCESS_GATES = (
    "independent_review_accepted", "problem_preserved", "failed_edge_resolved",
    "no_new_errors", "operationally_minimal", "descendants_revalidated",
    "final_path_clear",
)


def validate_ablation_purity() -> None:
    """Ensure every causal ablation differs from the full method only as locked."""
    full = asdict(METHOD_SPECS["full_system"])
    for method_id, allowed in ABLATION_DIFFERENCES.items():
        candidate = asdict(METHOD_SPECS[method_id])
        differences = {key for key in full if key != "method_id" and full[key] != candidate[key]}
        if differences != allowed:
            raise M6ExperimentError(
                f"{method_id} changes {sorted(differences)}; expected exactly {sorted(allowed)}"
            )


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


FIXTURE_DIGEST = canonical_digest("m6-fixture-placeholder")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def build_experiment_config(
    method_id: str, *, model_id: str | Mapping[str, str], prompt_digest: str,
    dataset_digest: str, theorem_bank_digest: str, tool_digest: str,
    code_digest: str = FIXTURE_DIGEST, scorer_digest: str = FIXTURE_DIGEST,
    schema_digest: str = FIXTURE_DIGEST, sampling_digest: str = FIXTURE_DIGEST,
    truncation_digest: str = FIXTURE_DIGEST, token_limit: int,
    call_limit: int, timeout_seconds: int, retry_limit: int = 1,
    role_mode: str = "same_model",
) -> dict[str, Any]:
    """Build one immutable, uniquely identified, budget-comparable config."""
    if method_id not in METHOD_SPECS:
        raise M6ExperimentError(f"unknown method_id: {method_id!r}")
    if role_mode not in {"same_model", "different_models"}:
        raise M6ExperimentError("role_mode must be same_model or different_models")
    if isinstance(model_id, str):
        models = {"generator": model_id, "critic": model_id}
    elif isinstance(model_id, Mapping):
        models = dict(model_id)
    else:
        models = {}
    if set(models) != {"generator", "critic"} or any(not isinstance(v, str) or not v for v in models.values()):
        raise M6ExperimentError("model_id must be a nonempty string or exact generator/critic mapping")
    if role_mode == "same_model" and len(set(models.values())) != 1:
        raise M6ExperimentError("same_model requires identical generator and critic models")
    if role_mode == "different_models" and len(set(models.values())) != 2:
        raise M6ExperimentError("different_models requires distinct generator and critic models")
    if any(not _is_sha256(v) for v in (
        prompt_digest, dataset_digest, theorem_bank_digest, tool_digest,
        code_digest, scorer_digest, schema_digest, sampling_digest, truncation_digest,
    )):
        raise M6ExperimentError("all artifact digest fields must be lowercase SHA-256 values")
    for name, value in {
        "token_limit": token_limit, "call_limit": call_limit,
        "timeout_seconds": timeout_seconds,
    }.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise M6ExperimentError(f"{name} must be a positive integer")
    if not isinstance(retry_limit, int) or isinstance(retry_limit, bool) or retry_limit < 0:
        raise M6ExperimentError("retry_limit must be a nonnegative integer")
    body = {
        "schema_version": M6_PERSON_B_VERSION,
        "method": asdict(METHOD_SPECS[method_id]),
        "models": models, "role_mode": role_mode,
        "prompt_digest": prompt_digest, "dataset_digest": dataset_digest,
        "theorem_bank_digest": theorem_bank_digest, "tool_digest": tool_digest,
        "code_digest": code_digest, "scorer_digest": scorer_digest,
        "schema_digest": schema_digest, "sampling_digest": sampling_digest,
        "truncation_digest": truncation_digest,
        "budget": {"total_tokens": token_limit, "model_calls": call_limit,
                   "timeout_seconds": timeout_seconds, "retry_limit": retry_limit},
    }
    return {**body, "experiment_id": f"m6-{method_id}-{canonical_digest(body)[:16]}"}


def validate_experiment_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Reject stale, incomplete, or post-build-mutated experiment configs."""
    row = dict(config)
    expected_fields = {
        "schema_version", "method", "models", "role_mode", "prompt_digest",
        "dataset_digest", "theorem_bank_digest", "tool_digest", "code_digest",
        "scorer_digest", "schema_digest", "sampling_digest", "truncation_digest",
        "budget", "experiment_id",
    }
    if set(row) != expected_fields:
        raise M6ExperimentError(f"config fields must be exactly {sorted(expected_fields)}")
    if row["schema_version"] != M6_PERSON_B_VERSION:
        raise M6ExperimentError("unsupported schema_version")
    method = row.get("method")
    method_id = method.get("method_id") if isinstance(method, Mapping) else None
    if method_id not in METHOD_SPECS or method != asdict(METHOD_SPECS[method_id]):
        raise M6ExperimentError("method spec is unknown or mutated")
    models = row.get("models")
    if not isinstance(models, Mapping) or set(models) != {"generator", "critic"} or any(
        not isinstance(value, str) or not value for value in models.values()
    ):
        raise M6ExperimentError("models must bind exact nonempty generator/critic IDs")
    if row["role_mode"] == "same_model" and len(set(models.values())) != 1:
        raise M6ExperimentError("same_model config contains different models")
    if row["role_mode"] == "different_models" and len(set(models.values())) != 2:
        raise M6ExperimentError("different_models config does not contain distinct models")
    if row["role_mode"] not in {"same_model", "different_models"}:
        raise M6ExperimentError("unknown role_mode")
    digest_fields = expected_fields - {"schema_version", "method", "models", "role_mode", "budget", "experiment_id"}
    if any(not _is_sha256(row[field]) for field in digest_fields):
        raise M6ExperimentError("all artifact digest fields must be lowercase SHA-256 values")
    budget = row.get("budget")
    if not isinstance(budget, Mapping) or set(budget) != {"total_tokens", "model_calls", "timeout_seconds", "retry_limit"}:
        raise M6ExperimentError("budget has an invalid shape")
    for key in ("total_tokens", "model_calls", "timeout_seconds"):
        if not isinstance(budget[key], int) or isinstance(budget[key], bool) or budget[key] < 1:
            raise M6ExperimentError(f"budget.{key} must be a positive integer")
    if not isinstance(budget["retry_limit"], int) or isinstance(budget["retry_limit"], bool) or budget["retry_limit"] < 0:
        raise M6ExperimentError("budget.retry_limit must be a nonnegative integer")
    body = {key: row[key] for key in row if key != "experiment_id"}
    expected_id = f"m6-{method_id}-{canonical_digest(body)[:16]}"
    if row["experiment_id"] != expected_id:
        raise M6ExperimentError("experiment_id does not bind current config content")
    return row


def _validate_shared_configs(configs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate configs and enforce the assets/budgets shared by every method."""
    validate_ablation_purity()
    rows = [validate_experiment_config(row) for row in configs]
    if len(rows) < 2:
        raise M6ExperimentError("experiment set requires at least two configs")
    if len({row.get("experiment_id") for row in rows}) != len(rows):
        raise M6ExperimentError("experiment_id values must be unique")
    shared = ("models", "role_mode", "dataset_digest", "theorem_bank_digest", "tool_digest", "code_digest",
              "scorer_digest", "schema_digest", "sampling_digest", "truncation_digest", "budget")
    for field in shared:
        if len({canonical_digest(row.get(field)) for row in rows}) != 1:
            raise M6ExperimentError(f"comparison configs differ on {field}")
    return rows


def validate_comparison(configs: Iterable[Mapping[str, Any]]) -> None:
    """Require one complete preregistered H1, H2, or H3 comparison family."""
    rows = _validate_shared_configs(configs)
    method_ids = {row["method"]["method_id"] for row in rows}
    matching = [family for family, required in COMPARISON_FAMILIES.items()
                if method_ids == required]
    if len(matching) != 1:
        raise M6ExperimentError("comparison must contain one complete preregistered H1/H2/H3 family")


def validate_experiment_suite(configs: Iterable[Mapping[str, Any]]) -> None:
    """Require the complete nine-method suite for one model/role configuration."""
    rows = _validate_shared_configs(configs)
    method_ids = [row["method"]["method_id"] for row in rows]
    if len(method_ids) != len(METHOD_IDS) or set(method_ids) != set(METHOD_IDS):
        raise M6ExperimentError("experiment suite must contain every preregistered method exactly once")


def cache_fingerprint(config: Mapping[str, Any], sample_id: str, serialized_input: Any) -> str:
    """Bind cache entries to method/config/prompt/model/data/tool and exact input."""
    if not isinstance(sample_id, str) or not sample_id:
        raise M6ExperimentError("sample_id must be nonempty")
    row = validate_experiment_config(config)
    required = set(row)
    return canonical_digest({key: row[key] for key in sorted(required)} |
                            {"sample_id": sample_id, "serialized_input": serialized_input})


def assert_execution_allowed(m5_gate: Mapping[str, Any], signatures: Mapping[str, Any], *,
                             fixture_only: bool,
                             user_release: Mapping[str, Any] | None = None) -> None:
    """Fail closed for any non-fixture execution until every prerequisite is signed."""
    if fixture_only:
        return
    if release_allows(user_release, "m6"):
        return
    if m5_gate.get("m6_entry_allowed") is not True:
        raise M6ExperimentError("M6 execution blocked: M5 m6_entry_allowed is not true")
    raise M6ExperimentError(
        "M6 execution blocked: authentic detached-signature and live-manifest verification are not implemented"
    )


def score_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Score hand fixtures using the locked M6 intention-to-treat definitions."""
    rows = [dict(row) for row in records]
    if len({row.get("sample_id") for row in rows}) != len(rows):
        raise M6ExperimentError("sample_id values must be nonempty and unique")
    for row in rows:
        required = {"sample_id", "gold_verdict", "gold_first_error_evaluable",
                    "gold_first_error_reason", "gold_repairability",
                    "gold_counterexample_eligible", "failure_type"}
        if not required.issubset(row):
            raise M6ExperimentError("scoring record is missing required Gold or failure fields")
        if not isinstance(row.get("sample_id"), str) or not row["sample_id"]:
            raise M6ExperimentError("sample_id values must be nonempty and unique")
        if row.get("failure_type") is not None and row["failure_type"] not in FAILURE_TYPES:
            raise M6ExperimentError("unknown failure_type")
        if row.get("gold_verdict") not in GOLD_VERDICTS:
            raise M6ExperimentError("unknown gold_verdict")
        if not isinstance(row.get("gold_first_error_evaluable"), bool):
            raise M6ExperimentError("gold_first_error_evaluable must be boolean")
        if row.get("gold_repairability") not in {"repairable", "irreparable", "undetermined"}:
            raise M6ExperimentError("unknown gold_repairability")
        if not isinstance(row["gold_counterexample_eligible"], bool):
            raise M6ExperimentError("gold_counterexample_eligible must be boolean")
        if row.get("gold_counterexample_eligible") is True and row["gold_verdict"] != "invalid":
            raise M6ExperimentError("counterexample-eligible Gold must be invalid")
        if row.get("predicted_verdict") is not None and row["predicted_verdict"] not in PREDICTED_VERDICTS:
            raise M6ExperimentError("unknown predicted_verdict")
        if row.get("failure_type") is None and row.get("predicted_verdict") is None:
            raise M6ExperimentError("successful infrastructure record requires a mathematical prediction")
        for field in ("gold_first_error", "predicted_first_error"):
            value = row.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
                raise M6ExperimentError(f"{field} must be null or a positive node id")
        if row.get("gold_first_error_evaluable") is True and row.get("gold_first_error") is None:
            raise M6ExperimentError("evaluable Gold first error requires a node id")
        if row.get("gold_first_error_evaluable") is True and row.get("gold_first_error_reason") != "evaluable":
            raise M6ExperimentError("evaluable Gold first error requires reason=evaluable")
        if row.get("gold_first_error_evaluable") is False and row.get("gold_first_error") is not None:
            raise M6ExperimentError("nonevaluable Gold first error cannot have a node id")
        if row.get("gold_first_error_evaluable") is False and row.get("gold_first_error_reason") not in {
            "absent", "undetermined", "not_evaluable",
        }:
            raise M6ExperimentError("nonevaluable Gold first error requires a frozen reason")
        if row.get("gold_first_error_reason") == "absent" and row.get("gold_first_error") is not None:
            raise M6ExperimentError("absent Gold first error cannot have a node id")
        if row.get("failure_type") is not None and any(row.get(field) is not None for field in ("predicted_verdict", "predicted_first_error")):
            raise M6ExperimentError("infrastructure failure cannot contain a mathematical prediction")
        if row.get("failure_type") is not None and any(row.get(field, 0) != 0 for field in (
            "counterexample_candidate_count", "valid_counterexample_count", "new_error_count",
        )):
            raise M6ExperimentError("infrastructure failure cannot contain mathematical evidence counts")
        if row.get("failure_type") is not None and any(row.get(field) is True for field in (
            "claimed_repair_success", "patch_applied", "verified_repair_success", "false_repair",
        )):
            raise M6ExperimentError("infrastructure failure cannot claim a patch outcome")
        for field in ("claimed_repair_success", "patch_applied", "verified_repair_success",
                      "false_repair", "new_error_introduced", *REPAIR_SUCCESS_GATES):
            if field in row and not isinstance(row[field], bool):
                raise M6ExperimentError(f"{field} must be boolean when present")
        if row.get("patch_applied") is True:
            required_patch_fields = {"new_error_introduced", "new_error_count", *REPAIR_SUCCESS_GATES}
            if not required_patch_fields.issubset(row):
                raise M6ExperimentError("applied patch requires complete mathematical review fields")
        elif any(row.get(field) is True for field in REPAIR_SUCCESS_GATES):
            raise M6ExperimentError("repair success gates require an applied patch")
        gates_pass = all(row.get(field) is True for field in REPAIR_SUCCESS_GATES)
        derived_verified = (
            row.get("gold_repairability") == "repairable"
            and row.get("claimed_repair_success") is True
            and row.get("patch_applied") is True
            and gates_pass
        )
        if (row.get("verified_repair_success") is True) != derived_verified:
            raise M6ExperimentError("verified repair success has inconsistent mathematical prerequisites")
        derived_false_repair = row.get("claimed_repair_success") is True and not derived_verified
        if (row.get("false_repair") is True) != derived_false_repair:
            raise M6ExperimentError("false repair must be derived from claimed and verified success")
        new_error_count = row.get("new_error_count", 0)
        if not isinstance(new_error_count, int) or isinstance(new_error_count, bool) or new_error_count < 0:
            raise M6ExperimentError("new_error_count must be a nonnegative integer")
        if (new_error_count > 0) != (row.get("new_error_introduced") is True):
            raise M6ExperimentError("new_error_count and new_error_introduced disagree")
        if new_error_count > 0 and row.get("patch_applied") is not True:
            raise M6ExperimentError("new errors cannot be introduced without an applied patch")
        if row.get("no_new_errors") is True and new_error_count > 0:
            raise M6ExperimentError("no_new_errors contradicts introduced errors")

    def ratio(n: int, d: int) -> float | str:
        return n / d if d else "undefined (0/0)"

    evaluable = [r for r in rows if r.get("gold_first_error_evaluable") is True]
    exact = sum(r.get("failure_type") is None and r.get("predicted_first_error") == r.get("gold_first_error") for r in evaluable)
    absent = [r for r in rows if r.get("gold_first_error_reason") == "absent"]
    absent_fp = sum(r.get("failure_type") is None and r.get("predicted_first_error") is not None for r in absent)
    invalid = [r for r in rows if r["gold_verdict"] == "invalid"]
    false_accepts = sum(r.get("failure_type") is None and r.get("predicted_verdict") in {"accepted", "accepted_with_gap"} for r in invalid)
    unsupported_gold = [r for r in rows if r["gold_verdict"] in {"gap", "undetermined"}]
    unsupported = sum(
        r.get("failure_type") is None and (
            (r["gold_verdict"] == "gap" and r.get("predicted_verdict") == "accepted")
            or (r["gold_verdict"] == "undetermined"
                and r.get("predicted_verdict") in {"accepted", "accepted_with_gap"})
        )
        for r in unsupported_gold
    )
    counterexample_eligible = [r for r in rows if r.get("gold_counterexample_eligible") is True]
    false_claim_detected = sum(r.get("failure_type") is None and r.get("predicted_verdict") == "invalid" for r in counterexample_eligible)
    if any(
        not isinstance(r.get(field, 0), int) or isinstance(r.get(field, 0), bool) or r.get(field, 0) < 0
        for r in rows for field in ("counterexample_candidate_count", "valid_counterexample_count")
    ) or any(r.get("valid_counterexample_count", 0) > r.get("counterexample_candidate_count", 0) for r in rows):
        raise M6ExperimentError("counterexample counts are invalid")
    if any(r.get("valid_counterexample_count", 0) > 0 and r.get("predicted_verdict") != "invalid"
           for r in rows):
        raise M6ExperimentError("a valid counterexample requires an invalid mathematical verdict")
    counterexample_candidates = sum(r.get("counterexample_candidate_count", 0) for r in rows if r.get("failure_type") is None)
    valid_counterexamples = sum(r.get("valid_counterexample_count", 0) for r in rows if r.get("failure_type") is None)
    covered = sum(r.get("failure_type") is None and r.get("valid_counterexample_count", 0) > 0 for r in counterexample_eligible)
    repairable = [r for r in rows if r.get("gold_repairability") == "repairable"]
    verified = sum(r.get("failure_type") is None and r.get("verified_repair_success") is True for r in repairable)
    claimed = [r for r in rows if r.get("claimed_repair_success") is True and r.get("failure_type") is None]
    false_repairs = sum(r.get("verified_repair_success") is not True for r in claimed)
    applied = [r for r in rows if r.get("patch_applied") is True and r.get("failure_type") is None]
    new_errors = sum(r.get("new_error_introduced") is True for r in applied)
    new_error_total = sum(r.get("new_error_count", 1 if r.get("new_error_introduced") is True else 0) for r in applied)
    failures = sum(r.get("failure_type") is not None for r in rows)
    completed = [r for r in rows if r.get("failure_type") is None]
    abstentions = sum(r.get("predicted_verdict") == "undetermined" for r in completed)
    return {
        "sample_count_intention_to_treat": len(rows),
        "first_error_exact_accuracy": {"value": ratio(exact, len(evaluable)), "numerator": exact, "denominator": len(evaluable)},
        "first_error_false_positive_rate_when_absent": {
            "value": ratio(absent_fp, len(absent)), "numerator": absent_fp, "denominator": len(absent),
            "worst_case_upper": ratio(absent_fp + sum(r.get("failure_type") is not None for r in absent), len(absent)),
        },
        "false_accept_rate": {"value": ratio(false_accepts, len(invalid)), "numerator": false_accepts, "denominator": len(invalid),
                              "worst_case_upper": ratio(false_accepts + sum(r.get("failure_type") is not None for r in invalid), len(invalid))},
        "unsupported_resolution_rate": {"value": ratio(unsupported, len(unsupported_gold)), "numerator": unsupported,
                                        "denominator": len(unsupported_gold),
                                        "worst_case_upper": ratio(unsupported + sum(r.get("failure_type") is not None for r in unsupported_gold), len(unsupported_gold))},
        "false_claim_detection_rate": {"value": ratio(false_claim_detected, len(counterexample_eligible)),
                                       "numerator": false_claim_detected, "denominator": len(counterexample_eligible)},
        "valid_counterexample_coverage": {"value": ratio(covered, len(counterexample_eligible)),
                                          "numerator": covered, "denominator": len(counterexample_eligible)},
        "counterexample_candidate_precision": {"value": ratio(valid_counterexamples, counterexample_candidates),
                                               "numerator": valid_counterexamples, "denominator": counterexample_candidates},
        "proof_abstention_rate": {"value": ratio(abstentions, len(completed)), "numerator": abstentions,
                                  "denominator": len(completed), "infrastructure_failures_excluded": failures},
        "verified_repair_success_rate": {"value": ratio(verified, len(repairable)), "numerator": verified, "denominator": len(repairable)},
        "false_repair_rate": {"value": ratio(false_repairs, len(claimed)), "numerator": false_repairs,
                              "denominator": len(claimed),
                              "worst_case_upper": ratio(false_repairs + sum(r.get("failure_type") is not None for r in repairable),
                                                        len(claimed) + sum(r.get("failure_type") is not None for r in repairable))},
        "new_error_introduction_rate": {"value": ratio(new_errors, len(applied)), "numerator": new_errors,
                                        "denominator": len(applied), "introduced_error_total": new_error_total,
                                        "worst_case_upper": ratio(
                                            new_errors + sum(r.get("failure_type") is not None for r in repairable),
                                            len(applied) + sum(r.get("failure_type") is not None for r in repairable),
                                        )},
        "infrastructure_failure_rate": {"value": ratio(failures, len(rows)), "numerator": failures, "denominator": len(rows)},
    }


def apply_method_applicability(method_id: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Mark mechanism metrics unavailable when a method cannot emit that object."""
    if method_id not in METHOD_SPECS:
        raise M6ExperimentError(f"unknown method_id: {method_id!r}")
    result = dict(metrics)
    spec = METHOD_SPECS[method_id]
    not_applicable = {"value": "not_applicable", "numerator": None, "denominator": None}
    if not spec.counterexample_protocol:
        for key in ("valid_counterexample_coverage", "counterexample_candidate_precision"):
            result[key] = dict(not_applicable)
    if not spec.produces_patch:
        for key in ("verified_repair_success_rate", "false_repair_rate", "new_error_introduction_rate"):
            result[key] = dict(not_applicable)
    return result


def load_m5_gate(root: Path) -> dict[str, Any]:
    return json.loads((root / "data/benchmarks/m5/joint_acceptance_v0_1.json").read_text(encoding="utf-8"))
