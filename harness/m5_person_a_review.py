"""Fail-closed Person A mathematical review gate for M5 repair patches."""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "0.1"
SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
CHECKS = {"mathematically_valid", "resolves_failed_inference", "theorem_preserved",
          "assumptions_preserved", "domain_preserved", "unrelated_branches_preserved",
          "no_new_errors", "operationally_minimal"}
CODES = {"mathematical_error", "failed_inference_unresolved", "changes_problem",
         "hidden_assumption", "domain_changed", "target_changed", "unrelated_branch_changed",
         "new_error_introduced", "not_minimal", "insufficient_evidence", "stale_binding"}

class M5PersonAReviewError(ValueError):
    """Raised when an M5 mathematical review is malformed or unsafe."""

def canonical_digest(value: Any) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise M5PersonAReviewError("digest input must be canonical JSON") from exc
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise M5PersonAReviewError(f"{path}: nonempty string required")
    return value

def _texts(value: Any, path: str, *, unique: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise M5PersonAReviewError(f"{path}: array required")
    for index, item in enumerate(value):
        _text(item, f"{path}[{index}]")
    if unique and len(value) != len(set(value)):
        raise M5PersonAReviewError(f"{path}: duplicate values forbidden")
    return value

def _exact(value: Any, keys: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise M5PersonAReviewError(f"{path}: object required")
    missing, unknown = keys - set(value), set(value) - keys
    if missing or unknown:
        raise M5PersonAReviewError(f"{path}: missing={sorted(missing)} unknown={sorted(unknown)}")
    return value

def _node_ref(value: Any, path: str) -> dict[str, Any]:
    ref = _exact(value, {"proof_id", "node_id", "version"}, path)
    _text(ref["proof_id"], f"{path}.proof_id")
    node_id = ref["node_id"]
    invalid_id = (isinstance(node_id, bool) or not isinstance(node_id, (str, int))
                  or isinstance(node_id, str) and not node_id.strip()
                  or isinstance(node_id, int) and node_id < 1)
    if invalid_id:
        raise M5PersonAReviewError(f"{path}.node_id: positive integer or nonempty string required")
    version = ref["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise M5PersonAReviewError(f"{path}.version: positive integer required")
    return ref

def patch_edit_ids(patch_value: Any) -> list[str]:
    """Derive all atomic edits which require deletion trials."""
    if not isinstance(patch_value, dict):
        raise M5PersonAReviewError("expected_patch: object required")
    operation = _text(patch_value.get("operation"), "expected_patch.operation")
    target = _node_ref(patch_value.get("target"), "expected_patch.target")
    nodes = patch_value.get("replacement_nodes")
    if not isinstance(nodes, list):
        raise M5PersonAReviewError("expected_patch.replacement_nodes: array required")
    if operation in {"replace", "insert_before"}:
        if not nodes:
            raise M5PersonAReviewError(f"expected_patch.replacement_nodes: required for {operation}")
        result = []
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise M5PersonAReviewError(f"expected_patch.replacement_nodes[{index}]: object required")
            node_id = node.get("node_id")
            if isinstance(node_id, bool) or not isinstance(node_id, (str, int)):
                raise M5PersonAReviewError(f"expected_patch.replacement_nodes[{index}].node_id: invalid")
            result.append(f"{operation}:{node_id}")
    elif operation in {"delete", "mark_irreparable", "add_assumption"}:
        result = [f"{operation}:{target['node_id']}"]
    else:
        raise M5PersonAReviewError(f"expected_patch.operation: unsupported {operation!r}")
    if len(result) != len(set(result)):
        raise M5PersonAReviewError("expected_patch: duplicate atomic edit ids")
    return result

def validate_review_context(value: Any) -> dict[str, Any]:
    keys = {"schema_version", "context_id", "proof_id", "target", "theorem", "global_assumptions",
            "domain", "failed_inference", "allowed_evidence", "unrelated_branch_digests",
            "error_certificate_digest", "patch_digest"}
    context = _exact(value, keys, "context")
    if context["schema_version"] != SCHEMA_VERSION:
        raise M5PersonAReviewError("context.schema_version: must equal 0.1")
    for key in ("context_id", "proof_id", "theorem", "domain", "failed_inference"):
        _text(context[key], f"context.{key}")
    target = _node_ref(context["target"], "context.target")
    if target["proof_id"] != context["proof_id"]:
        raise M5PersonAReviewError("context.target: proof mismatch")
    _texts(context["global_assumptions"], "context.global_assumptions", unique=True)
    if not _texts(context["allowed_evidence"], "context.allowed_evidence", unique=True):
        raise M5PersonAReviewError("context.allowed_evidence: cannot be empty")
    branches = context["unrelated_branch_digests"]
    if not isinstance(branches, dict):
        raise M5PersonAReviewError("context.unrelated_branch_digests: object required")
    for branch_id, digest in branches.items():
        _text(branch_id, "context.unrelated_branch_digests key")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise M5PersonAReviewError(f"context.unrelated_branch_digests.{branch_id}: invalid digest")
    for key in ("error_certificate_digest", "patch_digest"):
        if not isinstance(context[key], str) or not SHA256_RE.fullmatch(context[key]):
            raise M5PersonAReviewError(f"context.{key}: invalid digest")
    return context

def _required_codes(checks: dict[str, bool], hidden: list[str], errors: list[str],
                    trials: list[dict[str, Any]], changes_problem: bool) -> set[str]:
    mapping = {"mathematically_valid": "mathematical_error",
               "resolves_failed_inference": "failed_inference_unresolved",
               "theorem_preserved": "target_changed", "domain_preserved": "domain_changed",
               "unrelated_branches_preserved": "unrelated_branch_changed",
               "no_new_errors": "new_error_introduced", "operationally_minimal": "not_minimal"}
    required = {code for check, code in mapping.items() if not checks[check]}
    if not checks["assumptions_preserved"] or hidden: required.add("hidden_assumption")
    if errors: required.add("new_error_introduced")
    if any(not trial["removal_breaks_repair"] for trial in trials): required.add("not_minimal")
    if changes_problem: required.add("changes_problem")
    return required

def review_patch_math(context_value: Any, review_value: Any, *, repair_generator_id: str,
                      expected_error_certificate: Any, expected_patch: Any) -> dict[str, Any]:
    """Derive acceptance from frozen inputs and explicit mathematical checks."""
    context = validate_review_context(context_value)
    if not isinstance(expected_error_certificate, dict) or not isinstance(expected_patch, dict):
        raise M5PersonAReviewError("expected certificate and patch must be objects")
    patch_target = _node_ref(expected_patch.get("target"), "expected_patch.target")
    cert_target = _node_ref(expected_error_certificate.get("target"), "expected_error_certificate.target")
    if context["target"] != patch_target or context["target"] != cert_target:
        raise M5PersonAReviewError("context.target: must equal certificate and patch targets")
    if expected_patch.get("error_certificate_id") != expected_error_certificate.get("certificate_id"):
        raise M5PersonAReviewError("expected_patch.error_certificate_id: certificate mismatch")
    if context["error_certificate_digest"] != canonical_digest(expected_error_certificate) or context["patch_digest"] != canonical_digest(expected_patch):
        raise M5PersonAReviewError("context: stale binding")

    keys = {"schema_version", "review_id", "context_id", "reviewer_id", "checks",
            "hidden_assumptions", "introduced_errors", "deletion_trials", "evidence_used",
            "accepted", "rejection_codes", "reason"}
    review = _exact(review_value, keys, "review")
    if review["schema_version"] != SCHEMA_VERSION:
        raise M5PersonAReviewError("review.schema_version: must equal 0.1")
    for key in ("review_id", "context_id", "reviewer_id", "reason"):
        _text(review[key], f"review.{key}")
    if review["context_id"] != context["context_id"]:
        raise M5PersonAReviewError("review.context_id: stale binding")
    if review["reviewer_id"] == _text(repair_generator_id, "repair_generator_id"):
        raise M5PersonAReviewError("Repair Generator cannot review its own patch")
    checks = _exact(review["checks"], CHECKS, "review.checks")
    if any(not isinstance(result, bool) for result in checks.values()):
        raise M5PersonAReviewError("review.checks: booleans required")
    hidden = _texts(review["hidden_assumptions"], "review.hidden_assumptions", unique=True)
    errors = _texts(review["introduced_errors"], "review.introduced_errors", unique=True)
    evidence = _texts(review["evidence_used"], "review.evidence_used", unique=True)
    if not evidence or not set(evidence) <= set(context["allowed_evidence"]):
        raise M5PersonAReviewError("review.evidence_used: must use allowed evidence")

    values = review["deletion_trials"]
    if not isinstance(values, list) or not values:
        raise M5PersonAReviewError("review.deletion_trials: cannot be empty")
    trials = []
    for index, value in enumerate(values):
        trial = _exact(value, {"edit_id", "removal_breaks_repair", "reason"}, f"review.deletion_trials[{index}]")
        _text(trial["edit_id"], f"review.deletion_trials[{index}].edit_id")
        _text(trial["reason"], f"review.deletion_trials[{index}].reason")
        if not isinstance(trial["removal_breaks_repair"], bool):
            raise M5PersonAReviewError(f"review.deletion_trials[{index}].removal_breaks_repair: boolean required")
        trials.append(trial)
    actual, expected = [trial["edit_id"] for trial in trials], patch_edit_ids(expected_patch)
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise M5PersonAReviewError(f"review.deletion_trials: must cover exactly {sorted(expected)}")

    codes = review["rejection_codes"]
    if not isinstance(codes, list) or len(codes) != len(set(codes)) or not set(codes) <= CODES:
        raise M5PersonAReviewError("review.rejection_codes: invalid")
    if not isinstance(review["accepted"], bool):
        raise M5PersonAReviewError("review.accepted: boolean required")
    changes_problem = expected_patch.get("changes_problem")
    if not isinstance(changes_problem, bool):
        raise M5PersonAReviewError("expected_patch.changes_problem: boolean required")
    required = _required_codes(checks, hidden, errors, trials, changes_problem)
    if not required <= set(codes):
        raise M5PersonAReviewError(f"review.rejection_codes: missing {sorted(required - set(codes))}")
    accepted = (all(checks.values()) and not hidden and not errors
                and all(trial["removal_breaks_repair"] for trial in trials)
                and not codes and not changes_problem)
    if review["accepted"] != accepted:
        raise M5PersonAReviewError(f"review.accepted: must equal derived result {accepted}")
    if not accepted and not codes:
        raise M5PersonAReviewError("review.rejection_codes: rejection requires a code")
    return review
