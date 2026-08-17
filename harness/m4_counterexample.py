"""Person A's fail-closed mathematical gate for M4 counterexamples.

This module does not search for, or execute, a counterexample.  It turns the
M1 v0.3 certificate into a precise Person A review decision that Person B's
executable verifier can consume in M4.  Mathematical truth is never inferred
from the mere presence of prose evidence.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Iterable

from .contracts import (
    ContractError,
    validate_contract,
    validate_node_ref,
    validate_theorem_ref,
)


M4_PERSON_A_PROFILE = "m4-counterexample-person-a-v0.2"
SCOPE_ERROR_TYPE = {
    "local_claim": "false_local_claim",
    "global_theorem": "false_theorem",
}
VERIFICATION_STATUSES = {"verified", "failed", "undetermined"}
VERIFICATION_METHODS = {"manual_exact", "executable_exact", "hybrid_exact"}


def _canonical_refs(refs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for index, ref in enumerate(refs):
        validate_node_ref(ref, f"expected_premise_refs[{index}]")
        result.append(deepcopy(ref))
    return result


def _premise_statements(statements: Iterable[str]) -> list[str]:
    if isinstance(statements, (str, bytes)):
        raise ContractError("expected_premise_statements must be an array of strings")
    try:
        result = list(statements)
    except TypeError as exc:
        raise ContractError("expected_premise_statements must be an array of strings") from exc
    if not result:
        raise ContractError("expected_premise_statements must be nonempty")
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise ContractError("expected_premise_statements must contain nonempty strings")
    if len(set(result)) != len(result):
        raise ContractError("expected_premise_statements must not contain duplicates")
    return result


def expected_error_type(scope: str) -> str:
    """Return the only error category allowed for a certificate scope."""
    try:
        return SCOPE_ERROR_TYPE[scope]
    except KeyError as exc:
        raise ContractError(f"scope must be one of {sorted(SCOPE_ERROR_TYPE)}") from exc


def review_counterexample(
    certificate: dict[str, Any] | None,
    *,
    claimed_error_type: str | None,
    expected_premise_refs: Iterable[dict[str, Any]],
    expected_premise_statements: Iterable[str],
    expected_global_assumption_digest: str,
    expected_target: dict[str, Any] | None,
    expected_theorem_ref: dict[str, Any] | None,
    expected_target_statement: str,
    expected_structure: str,
    expected_interpretation_assumptions: Iterable[str],
    verification_status: str,
    verification_method: str,
    verification_notes: str,
    verifier_id: str,
    reviewer_id: str = "person_a",
) -> dict[str, Any]:
    """Apply Person A's M4 scope and mathematical acceptance policy.

    ``verification_status`` records an independent exact/manual or executable
    check.  ``undetermined`` is required when no counterexample was found or a
    premise/target could not be decided.  A certificate is accepted only when
    its v0.3 shape, scope, complete direct-premise frontier, proof assumptions,
    and independent verification all agree.
    """
    if verification_status not in VERIFICATION_STATUSES:
        raise ContractError(
            f"verification_status must be one of {sorted(VERIFICATION_STATUSES)}"
        )
    if verification_method not in VERIFICATION_METHODS:
        raise ContractError(
            f"verification_method must be one of {sorted(VERIFICATION_METHODS)}"
        )
    if not isinstance(verification_notes, str) or not verification_notes.strip():
        raise ContractError("verification_notes must be nonempty")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ContractError("reviewer_id must be nonempty")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise ContractError("verifier_id must be nonempty")
    if verifier_id == reviewer_id:
        raise ContractError("verifier_id must differ from reviewer_id")
    if not isinstance(expected_global_assumption_digest, str) or not expected_global_assumption_digest.strip():
        raise ContractError("expected_global_assumption_digest must be nonempty")
    if not isinstance(expected_target_statement, str) or not expected_target_statement.strip():
        raise ContractError("expected_target_statement must be nonempty")
    if not isinstance(expected_structure, str) or not expected_structure.strip():
        raise ContractError("expected_structure must be nonempty")
    if expected_target is not None:
        validate_node_ref(expected_target, "expected_target")
    if expected_theorem_ref is not None:
        validate_theorem_ref(expected_theorem_ref, "expected_theorem_ref")
    if (expected_target is None) == (expected_theorem_ref is None):
        raise ContractError("exactly one expected target or theorem ref is required")
    if isinstance(expected_interpretation_assumptions, (str, bytes)):
        raise ContractError("expected_interpretation_assumptions must be an array")
    try:
        expected_interpretations = list(expected_interpretation_assumptions)
    except TypeError as exc:
        raise ContractError("expected_interpretation_assumptions must be an array") from exc
    if any(not isinstance(item, str) or not item.strip() for item in expected_interpretations):
        raise ContractError("expected_interpretation_assumptions must contain nonempty strings")
    if len(set(expected_interpretations)) != len(expected_interpretations):
        raise ContractError("expected_interpretation_assumptions must not contain duplicates")

    expected_refs = _canonical_refs(expected_premise_refs)
    expected_statements = _premise_statements(expected_premise_statements)
    review_context = {
        "target": deepcopy(expected_target),
        "theorem_ref": deepcopy(expected_theorem_ref),
        "target_statement": expected_target_statement,
        "structure": expected_structure,
        "interpretation_assumptions": expected_interpretations,
        "premise_refs": expected_refs,
        "premise_statements": expected_statements,
        "global_assumption_digest": expected_global_assumption_digest,
    }
    review_context_digest = "sha256:" + hashlib.sha256(
        json.dumps(review_context, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    reasons: list[str] = []
    structural_error = False
    scope = None
    certificate_id = None

    if certificate is None:
        reasons.append("no counterexample certificate was produced")
    else:
        try:
            validate_contract("counterexample_certificate", certificate)
        except ContractError as exc:
            reasons.append(f"invalid shared certificate: {exc}")
            structural_error = True
        else:
            scope = certificate["scope"]
            certificate_id = certificate["certificate_id"]
            required_error_type = expected_error_type(scope)
            if claimed_error_type != required_error_type:
                reasons.append(
                    f"{scope} requires error type {required_error_type}, got {claimed_error_type}"
                )
                structural_error = True
            if certificate["target"] != expected_target or certificate["theorem_ref"] != expected_theorem_ref:
                reasons.append("certificate target binding does not match the reviewed target")
                structural_error = True
            if certificate["target_check"]["statement"] != expected_target_statement:
                reasons.append("target check statement does not match the reviewed target statement")
                structural_error = True
            if certificate["structure"] != expected_structure:
                reasons.append("certificate structure does not match the reviewed mathematical structure")
                structural_error = True
            if certificate.get("interpretation_assumptions", []) != expected_interpretations:
                reasons.append("certificate interpretation assumptions do not match the reviewed interpretation")
                structural_error = True
            if certificate["checked_premise_refs"] != expected_refs:
                reasons.append("checked premise refs do not equal the complete direct-premise frontier")
                structural_error = True
            checked_statements = [item["statement"] for item in certificate["premise_checks"]]
            if checked_statements != expected_statements:
                reasons.append("premise checks do not equal the complete reviewed premise statements")
                structural_error = True
            if certificate["global_assumption_digest"] != expected_global_assumption_digest:
                reasons.append("global assumption digest does not match the reviewed proof context")
                structural_error = True

    if verification_status == "failed":
        reasons.append("independent verification refuted a premise or did not refute the target")
    elif verification_status == "undetermined":
        reasons.append("independent verification remains undetermined")

    accepted = certificate is not None and verification_status == "verified" and not reasons
    decision = "accepted" if accepted else (
        "rejected" if verification_status == "failed" or structural_error else "undetermined"
    )
    return {
        "profile_version": M4_PERSON_A_PROFILE,
        "reviewer_id": reviewer_id,
        "verifier_id": verifier_id,
        "certificate_id": certificate_id,
        "scope": scope,
        "claimed_error_type": claimed_error_type,
        "verification_status": verification_status,
        "verification_method": verification_method,
        "accepted": accepted,
        "decision": decision,
        "reasons": reasons,
        "verification_notes": verification_notes,
        "review_context_digest": review_context_digest,
    }
