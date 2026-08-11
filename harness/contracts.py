"""Strict standard-library validators for shared dual-agent contracts v0.1.

The JSON Schema in ``schemas/dual_agent_harness_v0_1.schema.json`` is the
portable interchange definition. These validators enforce the same critical
invariants at runtime without adding a jsonschema dependency.
"""

from __future__ import annotations

import re
from typing import Any, Callable


SCHEMA_VERSION = "0.1"

NODE_TYPES = {
    "definition", "assumption", "introduction", "claim", "calculation",
    "conclusion", "citation",
}

MATHEMATICAL_VERDICTS = {
    "accepted", "accepted_with_gap", "unsupported", "counterexample_found",
    "ambiguous", "undetermined",
}

ERROR_TYPES = {
    "missing_assumption", "theorem_misuse", "algebraic_invalidity",
    "target_mismatch", "dependency_error", "false_local_claim",
    "false_theorem", "segmentation_error", "interpretation_ambiguity",
}

LIFECYCLE_STATES = {
    "pending_evaluation", "evaluating", "pending_repair", "patch_submitted",
    "pending_recheck", "active", "stale", "irreparable", "undetermined",
    "resolving_ambiguity", "blocked_by_invalid_dependency", "terminated",
}

INTERPRETATION_COVERAGE = {
    "exhaustive_within_declared_scope", "best_effort", "non_exhaustive",
}

AMBIGUITY_OUTCOMES = {
    "robustly_accepted", "requires_clarification",
    "unsupported_under_all_checked", "undetermined",
}

PATCH_OPERATIONS = {"insert_before", "replace", "delete", "add_assumption"}


class ContractError(ValueError):
    """Raised when a shared object violates contract v0.1."""


def _fail(path: str, message: str) -> None:
    raise ContractError(f"{path}: {message}")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    return value


def _exact_keys(
    value: dict[str, Any], required: set[str], optional: set[str], path: str
) -> None:
    missing = required - set(value)
    extra = set(value) - required - optional
    if missing:
        _fail(path, f"missing fields: {sorted(missing)}")
    if extra:
        _fail(path, f"unknown fields: {sorted(extra)}")


def _string(value: Any, path: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        _fail(path, "must be a string")
    if nonempty and not value.strip():
        _fail(path, "must be nonempty")
    return value


def _integer(value: Any, path: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(path, f"must be an integer >= {minimum}")
    return value


def _node_id(value: Any, path: str) -> int | str:
    if isinstance(value, bool):
        _fail(path, "must be a positive integer or nonempty string")
    if isinstance(value, int):
        return _integer(value, path)
    if isinstance(value, str):
        return _string(value, path)
    _fail(path, "must be a positive integer or nonempty string")


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        _fail(path, "must be a boolean")
    return value


def _enum(value: Any, allowed: set[str], path: str) -> str:
    result = _string(value, path)
    if result not in allowed:
        _fail(path, f"must be one of {sorted(allowed)}")
    return result


def _string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        _fail(path, "must be a nonempty array" if nonempty else "must be an array")
    for index, item in enumerate(value):
        _string(item, f"{path}[{index}]")
    return value


def _schema_header(value: dict[str, Any], path: str) -> None:
    if value.get("schema_version") != SCHEMA_VERSION:
        _fail(f"{path}.schema_version", f"must equal {SCHEMA_VERSION!r}")


def validate_node_ref(value: Any, path: str = "node_ref") -> dict[str, Any]:
    obj = _object(value, path)
    _exact_keys(obj, {"proof_id", "node_id", "version"}, set(), path)
    _string(obj["proof_id"], f"{path}.proof_id")
    _node_id(obj["node_id"], f"{path}.node_id")
    _integer(obj["version"], f"{path}.version")
    return obj


def validate_theorem_ref(value: Any, path: str = "theorem_ref") -> dict[str, Any]:
    obj = _object(value, path)
    _exact_keys(obj, {"proof_id", "theorem_version", "theorem_digest"}, set(), path)
    _string(obj["proof_id"], f"{path}.proof_id")
    _integer(obj["theorem_version"], f"{path}.theorem_version")
    _string(obj["theorem_digest"], f"{path}.theorem_digest")
    return obj


def validate_dependency_edge(value: Any, path: str = "dependency_edge") -> dict[str, Any]:
    obj = _object(value, path)
    _exact_keys(
        obj, {"schema_version", "source", "target", "relation", "reason"}, set(), path
    )
    _schema_header(obj, path)
    source = validate_node_ref(obj["source"], f"{path}.source")
    target = validate_node_ref(obj["target"], f"{path}.target")
    if source["proof_id"] != target["proof_id"]:
        _fail(path, "source and target must belong to the same proof")
    _enum(obj["relation"], {"used_as_premise", "applies_definition", "case_scope"}, f"{path}.relation")
    _string(obj["reason"], f"{path}.reason")
    return obj


def validate_proof_node(value: Any, path: str = "proof_node") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "proof_id", "node_id", "version", "order_key", "claim",
        "self_contained_claim", "node_type", "source_span", "depends_on",
    }
    _exact_keys(obj, required, set(), path)
    _schema_header(obj, path)
    _string(obj["proof_id"], f"{path}.proof_id")
    _node_id(obj["node_id"], f"{path}.node_id")
    _integer(obj["version"], f"{path}.version")
    _integer(obj["order_key"], f"{path}.order_key")
    _string(obj["claim"], f"{path}.claim")
    _string(obj["self_contained_claim"], f"{path}.self_contained_claim")
    _enum(obj["node_type"], NODE_TYPES, f"{path}.node_type")
    span = _object(obj["source_span"], f"{path}.source_span")
    _exact_keys(span, {"start", "end"}, set(), f"{path}.source_span")
    start = _integer(span["start"], f"{path}.source_span.start", minimum=0)
    end = _integer(span["end"], f"{path}.source_span.end", minimum=0)
    if end <= start:
        _fail(f"{path}.source_span", "end must be greater than start")
    if not isinstance(obj["depends_on"], list):
        _fail(f"{path}.depends_on", "must be an array")
    seen: set[tuple[str, int, int]] = set()
    for index, ref_value in enumerate(obj["depends_on"]):
        ref = validate_node_ref(ref_value, f"{path}.depends_on[{index}]")
        key = (ref["proof_id"], ref["node_id"], ref["version"])
        if key in seen:
            _fail(f"{path}.depends_on", "contains duplicate node references")
        seen.add(key)
        if ref["proof_id"] != obj["proof_id"] or ref["node_id"] == obj["node_id"]:
            _fail(f"{path}.depends_on[{index}]", "must reference another node in the same proof")
    return obj


def validate_evaluation_record(value: Any, path: str = "evaluation_record") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "evaluation_id", "target", "verdict", "error_type",
        "reason", "dependency_versions", "evaluator_id",
    }
    _exact_keys(
        obj, required,
        {"error_certificate_id", "counterexample_certificate_id", "ambiguity_analysis_id"},
        path,
    )
    _schema_header(obj, path)
    _string(obj["evaluation_id"], f"{path}.evaluation_id")
    target = validate_node_ref(obj["target"], f"{path}.target")
    verdict = _enum(obj["verdict"], MATHEMATICAL_VERDICTS, f"{path}.verdict")
    if obj["error_type"] is not None:
        _enum(obj["error_type"], ERROR_TYPES, f"{path}.error_type")
    if verdict in {"accepted", "accepted_with_gap"} and obj["error_type"] is not None:
        _fail(path, "accepted verdicts cannot carry an error_type")
    if verdict == "counterexample_found" and not obj.get("counterexample_certificate_id"):
        _fail(path, "counterexample_found requires counterexample_certificate_id")
    _string(obj["reason"], f"{path}.reason")
    _string(obj["evaluator_id"], f"{path}.evaluator_id")
    versions = _object(obj["dependency_versions"], f"{path}.dependency_versions")
    for node_id, version in versions.items():
        if not str(node_id).strip():
            _fail(f"{path}.dependency_versions", "keys must be nonempty node ids")
        _integer(version, f"{path}.dependency_versions.{node_id}")
    if str(target["node_id"]) in versions:
        _fail(f"{path}.dependency_versions", "must not include the target itself")
    for optional in ("error_certificate_id", "counterexample_certificate_id", "ambiguity_analysis_id"):
        if obj.get(optional) is not None:
            _string(obj[optional], f"{path}.{optional}")
    return obj


def ambiguity_outcome(value: dict[str, Any]) -> str:
    """Compute the only permitted aggregate outcome for an ambiguity analysis."""
    interpretations = [
        item for item in value["interpretations"] if item["plausibility"] == "reasonable"
    ]
    verdicts = [item["verdict"] for item in interpretations]
    accepted = [verdict in {"accepted", "accepted_with_gap"} for verdict in verdicts]
    if any(verdict in {"ambiguous", "undetermined"} for verdict in verdicts):
        return "undetermined"
    if any(accepted) and not all(accepted):
        return "requires_clarification"
    if all(accepted):
        if value["meaning_relation"] == "equivalent" and value["coverage_status"] == "exhaustive_within_declared_scope":
            return "robustly_accepted"
        if value["meaning_relation"] == "distinct":
            return "requires_clarification"
        return "undetermined"
    if value["coverage_status"] == "exhaustive_within_declared_scope":
        return "unsupported_under_all_checked"
    return "undetermined"


def validate_ambiguity_analysis(value: Any, path: str = "ambiguity_analysis") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "analysis_id", "target", "ambiguous_span",
        "ambiguity_type", "declared_scope", "coverage_status",
        "meaning_relation", "interpretations", "dependency_versions",
        "outcome", "evaluator_id",
    }
    _exact_keys(obj, required, set(), path)
    _schema_header(obj, path)
    _string(obj["analysis_id"], f"{path}.analysis_id")
    target = validate_node_ref(obj["target"], f"{path}.target")
    _string(obj["ambiguous_span"], f"{path}.ambiguous_span")
    _enum(
        obj["ambiguity_type"],
        {"unclear_reference", "scope_ambiguity", "notation_ambiguity", "syntactic_ambiguity", "other"},
        f"{path}.ambiguity_type",
    )
    _string(obj["declared_scope"], f"{path}.declared_scope")
    _enum(obj["coverage_status"], INTERPRETATION_COVERAGE, f"{path}.coverage_status")
    _enum(obj["meaning_relation"], {"equivalent", "distinct", "undetermined"}, f"{path}.meaning_relation")
    interpretations = obj["interpretations"]
    if not isinstance(interpretations, list) or len(interpretations) < 2:
        _fail(f"{path}.interpretations", "must contain at least two candidates")
    seen_ids: set[str] = set()
    reasonable_count = 0
    for index, item_value in enumerate(interpretations):
        item_path = f"{path}.interpretations[{index}]"
        item = _object(item_value, item_path)
        _exact_keys(
            item,
            {"interpretation_id", "normalized_claim", "plausibility", "verdict", "reason"},
            set(), item_path,
        )
        interpretation_id = _string(item["interpretation_id"], f"{item_path}.interpretation_id")
        if interpretation_id in seen_ids:
            _fail(f"{path}.interpretations", "contains duplicate interpretation ids")
        seen_ids.add(interpretation_id)
        _string(item["normalized_claim"], f"{item_path}.normalized_claim")
        plausibility = _enum(item["plausibility"], {"reasonable", "remote"}, f"{item_path}.plausibility")
        if plausibility == "reasonable":
            reasonable_count += 1
        _enum(item["verdict"], MATHEMATICAL_VERDICTS - {"counterexample_found"}, f"{item_path}.verdict")
        _string(item["reason"], f"{item_path}.reason")
    if reasonable_count < 2:
        _fail(f"{path}.interpretations", "must contain at least two reasonable candidates")
    versions = _object(obj["dependency_versions"], f"{path}.dependency_versions")
    for node_id, version in versions.items():
        if not str(node_id).strip() or str(node_id) == str(target["node_id"]):
            _fail(f"{path}.dependency_versions", "keys must be nonempty dependency node ids")
        _integer(version, f"{path}.dependency_versions.{node_id}")
    _enum(obj["outcome"], AMBIGUITY_OUTCOMES, f"{path}.outcome")
    expected = ambiguity_outcome(obj)
    if obj["outcome"] != expected:
        _fail(f"{path}.outcome", f"must equal deterministic outcome {expected!r}")
    _string(obj["evaluator_id"], f"{path}.evaluator_id")
    return obj


def validate_error_certificate(value: Any, path: str = "error_certificate") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "certificate_id", "target", "premises", "error_type",
        "failed_inference", "evidence", "repair_constraints",
    }
    _exact_keys(obj, required, {"missing_condition", "counterexample_certificate_id"}, path)
    _schema_header(obj, path)
    _string(obj["certificate_id"], f"{path}.certificate_id")
    target = validate_node_ref(obj["target"], f"{path}.target")
    if not isinstance(obj["premises"], list):
        _fail(f"{path}.premises", "must be an array")
    for index, premise in enumerate(obj["premises"]):
        ref = validate_node_ref(premise, f"{path}.premises[{index}]")
        if ref["proof_id"] != target["proof_id"] or ref["node_id"] == target["node_id"]:
            _fail(f"{path}.premises[{index}]", "must reference another node in the same proof")
    _enum(obj["error_type"], ERROR_TYPES, f"{path}.error_type")
    _string(obj["failed_inference"], f"{path}.failed_inference")
    _string_list(obj["evidence"], f"{path}.evidence", nonempty=True)
    constraints = _object(obj["repair_constraints"], f"{path}.repair_constraints")
    _exact_keys(
        constraints,
        {"allowed_operations", "max_new_nodes", "preserve_theorem", "preserve_assumptions"},
        set(), f"{path}.repair_constraints",
    )
    operations = constraints["allowed_operations"]
    if not isinstance(operations, list) or not operations:
        _fail(f"{path}.repair_constraints.allowed_operations", "must be a nonempty array")
    for index, operation in enumerate(operations):
        _enum(operation, PATCH_OPERATIONS, f"{path}.repair_constraints.allowed_operations[{index}]")
    _integer(constraints["max_new_nodes"], f"{path}.repair_constraints.max_new_nodes", minimum=0)
    _boolean(constraints["preserve_theorem"], f"{path}.repair_constraints.preserve_theorem")
    _boolean(constraints["preserve_assumptions"], f"{path}.repair_constraints.preserve_assumptions")
    for optional in ("missing_condition", "counterexample_certificate_id"):
        if obj.get(optional) is not None:
            _string(obj[optional], f"{path}.{optional}")
    return obj


def validate_counterexample_certificate(value: Any, path: str = "counterexample_certificate") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "certificate_id", "target", "theorem_ref", "scope", "structure",
        "assignment", "premise_checks", "target_check", "checker",
    }
    _exact_keys(obj, required, {"tool_trace", "interpretation_assumptions"}, path)
    _schema_header(obj, path)
    _string(obj["certificate_id"], f"{path}.certificate_id")
    scope = _enum(obj["scope"], {"local_claim", "global_theorem"}, f"{path}.scope")
    if scope == "local_claim":
        if obj["target"] is None or obj["theorem_ref"] is not None:
            _fail(path, "local_claim requires target and forbids theorem_ref")
        validate_node_ref(obj["target"], f"{path}.target")
    else:
        if obj["target"] is not None or obj["theorem_ref"] is None:
            _fail(path, "global_theorem requires theorem_ref and forbids target")
        theorem_ref = validate_theorem_ref(obj["theorem_ref"], f"{path}.theorem_ref")
        if re.fullmatch(r"sha256:[0-9a-f]{64}", theorem_ref["theorem_digest"]) is None:
            _fail(f"{path}.theorem_ref.theorem_digest", "must be a lowercase SHA-256 digest")
    _string(obj["structure"], f"{path}.structure")
    _object(obj["assignment"], f"{path}.assignment")
    if not isinstance(obj["premise_checks"], list) or not obj["premise_checks"]:
        _fail(f"{path}.premise_checks", "must be a nonempty array")
    for index, check in enumerate(obj["premise_checks"]):
        check = _object(check, f"{path}.premise_checks[{index}]")
        _exact_keys(check, {"statement", "holds", "evidence"}, set(), f"{path}.premise_checks[{index}]")
        _string(check["statement"], f"{path}.premise_checks[{index}].statement")
        if not _boolean(check["holds"], f"{path}.premise_checks[{index}].holds"):
            _fail(f"{path}.premise_checks[{index}].holds", "must be true for a valid certificate")
        _string(check["evidence"], f"{path}.premise_checks[{index}].evidence")
    target_check = _object(obj["target_check"], f"{path}.target_check")
    _exact_keys(target_check, {"statement", "holds", "evidence"}, set(), f"{path}.target_check")
    _string(target_check["statement"], f"{path}.target_check.statement")
    if _boolean(target_check["holds"], f"{path}.target_check.holds"):
        _fail(f"{path}.target_check.holds", "must be false for a counterexample")
    _string(target_check["evidence"], f"{path}.target_check.evidence")
    _string(obj["checker"], f"{path}.checker")
    if obj.get("tool_trace") is not None:
        _string_list(obj["tool_trace"], f"{path}.tool_trace")
    if obj.get("interpretation_assumptions") is not None:
        _string_list(obj["interpretation_assumptions"], f"{path}.interpretation_assumptions")
    return obj


def validate_patch_proposal(value: Any, path: str = "patch_proposal") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "patch_id", "error_certificate_id", "target",
        "operation", "replacement_nodes", "target_dependencies_after",
        "used_dependencies", "rationale", "changes_problem",
    }
    _exact_keys(obj, required, set(), path)
    _schema_header(obj, path)
    _string(obj["patch_id"], f"{path}.patch_id")
    _string(obj["error_certificate_id"], f"{path}.error_certificate_id")
    target = validate_node_ref(obj["target"], f"{path}.target")
    operation = _enum(obj["operation"], PATCH_OPERATIONS, f"{path}.operation")
    if not isinstance(obj["replacement_nodes"], list):
        _fail(f"{path}.replacement_nodes", "must be an array")
    if operation in {"replace", "insert_before"} and not obj["replacement_nodes"]:
        _fail(f"{path}.replacement_nodes", f"must be nonempty for {operation}")
    seen_node_ids: set[int | str] = set()
    seen_order_keys: set[int] = set()
    for index, node_value in enumerate(obj["replacement_nodes"]):
        node_path = f"{path}.replacement_nodes[{index}]"
        node = _object(node_value, node_path)
        _exact_keys(
            node,
            {"node_id", "order_key", "claim", "self_contained_claim", "node_type", "depends_on"},
            set(), node_path,
        )
        node_id = _node_id(node["node_id"], f"{node_path}.node_id")
        order_key = _integer(node["order_key"], f"{node_path}.order_key")
        if node_id in seen_node_ids or order_key in seen_order_keys:
            _fail(f"{path}.replacement_nodes", "contains duplicate node ids or order keys")
        seen_node_ids.add(node_id)
        seen_order_keys.add(order_key)
        _string(node["claim"], f"{node_path}.claim")
        _string(node["self_contained_claim"], f"{node_path}.self_contained_claim")
        _enum(node["node_type"], NODE_TYPES, f"{node_path}.node_type")
        if not isinstance(node["depends_on"], list):
            _fail(f"{node_path}.depends_on", "must be an array")
        for dep_index, dep in enumerate(node["depends_on"]):
            validate_node_ref(dep, f"{node_path}.depends_on[{dep_index}]")
    if operation == "insert_before" and len(obj["replacement_nodes"]) > 3:
        _fail(f"{path}.replacement_nodes", "M1 permits at most three inserted nodes")
    if not isinstance(obj["target_dependencies_after"], list):
        _fail(f"{path}.target_dependencies_after", "must be an array")
    for index, dep in enumerate(obj["target_dependencies_after"]):
        validate_node_ref(dep, f"{path}.target_dependencies_after[{index}]")
    if not isinstance(obj["used_dependencies"], list):
        _fail(f"{path}.used_dependencies", "must be an array")
    for index, dep in enumerate(obj["used_dependencies"]):
        ref = validate_node_ref(dep, f"{path}.used_dependencies[{index}]")
        if ref["proof_id"] != target["proof_id"] or ref["node_id"] == target["node_id"]:
            _fail(f"{path}.used_dependencies[{index}]", "must reference another node in the same proof")
    _string(obj["rationale"], f"{path}.rationale")
    changes_problem = _boolean(obj["changes_problem"], f"{path}.changes_problem")
    if operation == "add_assumption" and not changes_problem:
        _fail(path, "add_assumption must set changes_problem to true")
    return obj


def validate_patch_review(value: Any, path: str = "patch_review") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "review_id", "patch_id", "target", "accepted",
        "verdict", "reason", "reviewer_id",
    }
    _exact_keys(obj, required, {"rejection_code"}, path)
    _schema_header(obj, path)
    _string(obj["review_id"], f"{path}.review_id")
    _string(obj["patch_id"], f"{path}.patch_id")
    validate_node_ref(obj["target"], f"{path}.target")
    accepted = _boolean(obj["accepted"], f"{path}.accepted")
    verdict = _enum(obj["verdict"], MATHEMATICAL_VERDICTS, f"{path}.verdict")
    if accepted and verdict not in {"accepted", "accepted_with_gap"}:
        _fail(path, "accepted patch review requires an accepted verdict")
    if not accepted and verdict in {"accepted", "accepted_with_gap"}:
        _fail(path, "rejected patch review cannot carry an accepted verdict")
    _string(obj["reason"], f"{path}.reason")
    _string(obj["reviewer_id"], f"{path}.reviewer_id")
    if obj.get("rejection_code") is not None:
        _enum(obj["rejection_code"], {"mathematical_error", "changes_problem", "not_minimal", "stale_target", "malformed"}, f"{path}.rejection_code")
    return obj


def validate_node_version(value: Any, path: str = "node_version") -> dict[str, Any]:
    obj = _object(value, path)
    required = {"schema_version", "node", "lifecycle_state", "current_verdict", "created_by", "supersedes"}
    _exact_keys(obj, required, {"stale_reason"}, path)
    _schema_header(obj, path)
    validate_proof_node(obj["node"], f"{path}.node")
    _enum(obj["lifecycle_state"], LIFECYCLE_STATES, f"{path}.lifecycle_state")
    if obj["current_verdict"] is not None:
        _enum(obj["current_verdict"], MATHEMATICAL_VERDICTS, f"{path}.current_verdict")
    _enum(obj["created_by"], {"original", "repair_generator", "human"}, f"{path}.created_by")
    if obj["supersedes"] is not None:
        old = validate_node_ref(obj["supersedes"], f"{path}.supersedes")
        node = obj["node"]
        if old["proof_id"] != node["proof_id"] or old["node_id"] != node["node_id"] or old["version"] >= node["version"]:
            _fail(f"{path}.supersedes", "must reference an earlier version of the same node")
    if obj.get("stale_reason") is not None:
        _string(obj["stale_reason"], f"{path}.stale_reason")
    return obj


def validate_run_manifest(value: Any, path: str = "run_manifest") -> dict[str, Any]:
    obj = _object(value, path)
    required = {
        "schema_version", "run_id", "created_at", "controller_version",
        "contract_version", "input_digest", "theorem_bank_digest", "agents",
        "prompt_versions", "model_parameters", "events",
    }
    _exact_keys(obj, required, set(), path)
    _schema_header(obj, path)
    for field in ("run_id", "created_at", "controller_version", "contract_version", "input_digest"):
        _string(obj[field], f"{path}.{field}")
    if obj["contract_version"] != SCHEMA_VERSION:
        _fail(f"{path}.contract_version", f"must equal {SCHEMA_VERSION!r}")
    if obj["theorem_bank_digest"] is not None:
        _string(obj["theorem_bank_digest"], f"{path}.theorem_bank_digest")
    agents = _object(obj["agents"], f"{path}.agents")
    _exact_keys(agents, {"evaluator", "repair_generator"}, set(), f"{path}.agents")
    _string(agents["evaluator"], f"{path}.agents.evaluator")
    _string(agents["repair_generator"], f"{path}.agents.repair_generator")
    prompts = _object(obj["prompt_versions"], f"{path}.prompt_versions")
    _exact_keys(prompts, {"evaluator", "repair_generator"}, set(), f"{path}.prompt_versions")
    _string(prompts["evaluator"], f"{path}.prompt_versions.evaluator")
    _string(prompts["repair_generator"], f"{path}.prompt_versions.repair_generator")
    _object(obj["model_parameters"], f"{path}.model_parameters")
    if not isinstance(obj["events"], list):
        _fail(f"{path}.events", "must be an array")
    return obj


VALIDATORS: dict[str, Callable[[Any, str], dict[str, Any]]] = {
    "dependency_edge": validate_dependency_edge,
    "proof_node": validate_proof_node,
    "evaluation_record": validate_evaluation_record,
    "ambiguity_analysis": validate_ambiguity_analysis,
    "error_certificate": validate_error_certificate,
    "counterexample_certificate": validate_counterexample_certificate,
    "patch_proposal": validate_patch_proposal,
    "patch_review": validate_patch_review,
    "node_version": validate_node_version,
    "run_manifest": validate_run_manifest,
}


def validate_contract(kind: str, value: Any) -> dict[str, Any]:
    """Validate one v0.1 contract object and return it unchanged."""
    try:
        validator = VALIDATORS[kind]
    except KeyError as exc:
        raise ContractError(f"unknown contract kind: {kind!r}") from exc
    return validator(value, kind)
