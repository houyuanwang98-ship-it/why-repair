"""Fail-closed human-review handoff for the M7 interactive blind packet."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


DECISIONS = {"accepted", "rejected", "undetermined"}
CHECKS = ("mathematically_valid", "problem_preserved", "no_new_error", "minimal")


class M7InteractiveReviewError(ValueError):
    pass


def expected_rows(public_plan: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    rows = public_plan.get("review_rows")
    if not isinstance(rows, list) or not rows:
        raise M7InteractiveReviewError("public review plan has no rows")
    triples = []
    for row in rows:
        if set(row) != {"case_id", "anonymized_config_id", "review_payload_sha256"}:
            raise M7InteractiveReviewError("public review row has an invalid shape")
        triple = (row["case_id"], row["anonymized_config_id"], row["review_payload_sha256"])
        if any(not isinstance(value, str) or not value for value in triple):
            raise M7InteractiveReviewError("public review row identities must be nonempty")
        triples.append(triple)
    if len(set(triples)) != len(triples):
        raise M7InteractiveReviewError("public review rows must be unique")
    return triples


def build_template(public_plan: Mapping[str, Any], *, reviewer_slot: str) -> dict[str, Any]:
    if reviewer_slot not in {"person_a", "person_b"}:
        raise M7InteractiveReviewError("reviewer slot must be person_a or person_b")
    return {
        "schema_version": "m7-interactive-blind-review-0.2",
        "reviewer_slot": reviewer_slot, "status": "pending", "reviewer_id": None,
        "independence_statement": None, "started_at": None, "finished_at": None,
        "rows": [{"case_id": case_id, "anonymized_config_id": config_id,
                  "review_payload_sha256": payload, "decision": None,
                  **{check: None for check in CHECKS}, "finding": None}
                 for case_id, config_id, payload in expected_rows(public_plan)],
    }


def validate_review(public_plan: Mapping[str, Any], review: Mapping[str, Any], *, require_complete: bool) -> dict[str, Any]:
    row = dict(review)
    required = {"schema_version", "reviewer_slot", "status", "reviewer_id",
                "independence_statement", "started_at", "finished_at", "rows"}
    if set(row) != required or row.get("schema_version") != "m7-interactive-blind-review-0.2":
        raise M7InteractiveReviewError("blind review has an invalid shape or version")
    if row.get("reviewer_slot") not in {"person_a", "person_b"}:
        raise M7InteractiveReviewError("blind review has an invalid reviewer slot")
    if row.get("status") not in {"pending", "complete"}:
        raise M7InteractiveReviewError("blind review has an invalid status")
    expected = expected_rows(public_plan)
    supplied = row.get("rows")
    if not isinstance(supplied, list) or len(supplied) != len(expected):
        raise M7InteractiveReviewError("blind review must cover every planned row")
    review_fields = {"case_id", "anonymized_config_id", "review_payload_sha256", "decision",
                     *CHECKS, "finding"}
    identities = []
    for item in supplied:
        if not isinstance(item, Mapping) or set(item) != review_fields:
            raise M7InteractiveReviewError("blind review decision row has an invalid shape")
        identities.append((item["case_id"], item["anonymized_config_id"], item["review_payload_sha256"]))
    if identities != expected:
        raise M7InteractiveReviewError("blind review rows differ from the frozen plan")
    complete = row["status"] == "complete"
    if require_complete and not complete:
        raise M7InteractiveReviewError("blind review is not complete")
    if complete:
        for field in ("reviewer_id", "independence_statement", "started_at", "finished_at"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise M7InteractiveReviewError(f"complete blind review requires {field}")
        for item in supplied:
            if item["decision"] not in DECISIONS:
                raise M7InteractiveReviewError("complete blind review requires every decision")
            if any(not isinstance(item[check], bool) for check in CHECKS):
                raise M7InteractiveReviewError("complete blind review requires every mathematical check")
            if item["decision"] != "accepted" and (not isinstance(item["finding"], str) or not item["finding"].strip()):
                raise M7InteractiveReviewError("non-accepted decision requires a finding")
            if item["decision"] == "accepted" and not all(item[check] for check in CHECKS):
                raise M7InteractiveReviewError("accepted decision requires all mathematical checks")
    return row


def verify_independent_pair(public_plan: Mapping[str, Any], left: Mapping[str, Any],
                            right: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    a = validate_review(public_plan, left, require_complete=True)
    b = validate_review(public_plan, right, require_complete=True)
    if {a["reviewer_slot"], b["reviewer_slot"]} != {"person_a", "person_b"}:
        raise M7InteractiveReviewError("review pair must fill distinct A/B slots")
    if a["reviewer_id"] == b["reviewer_id"]:
        raise M7InteractiveReviewError("independent reviewers must have distinct identities")
    return a, b


def disputes(public_plan: Mapping[str, Any], left: Mapping[str, Any], right: Mapping[str, Any]) -> list[dict[str, Any]]:
    a, b = verify_independent_pair(public_plan, left, right)
    result = []
    for first, second in zip(a["rows"], b["rows"]):
        if first["decision"] != second["decision"] or any(first[key] != second[key] for key in CHECKS):
            result.append({"case_id": first["case_id"],
                           "anonymized_config_id": first["anonymized_config_id"],
                           "review_payload_sha256": first["review_payload_sha256"],
                           "person_a_decision": first["decision"],
                           "person_b_decision": second["decision"]})
    return result


def authorize_unblinding(public_plan: Mapping[str, Any], left: Mapping[str, Any], right: Mapping[str, Any],
                         sealed_mapping: Mapping[str, str], adjudications: list[Mapping[str, Any]]) -> dict[str, str]:
    pending = disputes(public_plan, left, right)
    expected = {(row["case_id"], row["anonymized_config_id"], row["review_payload_sha256"]) for row in pending}
    resolved = set()
    for item in adjudications:
        if set(item) != {"case_id", "anonymized_config_id", "review_payload_sha256",
                         "third_reviewer_id", "decision", "finding"}:
            raise M7InteractiveReviewError("adjudication has an invalid shape")
        key = (item["case_id"], item["anonymized_config_id"], item["review_payload_sha256"])
        if (key not in expected or key in resolved or item["decision"] not in DECISIONS
                or not isinstance(item["third_reviewer_id"], str) or not item["third_reviewer_id"].strip()
                or not isinstance(item["finding"], str) or not item["finding"].strip()):
            raise M7InteractiveReviewError("adjudication does not resolve an exact dispute")
        resolved.add(key)
    if resolved != expected:
        raise M7InteractiveReviewError("all review disputes require third-person adjudication before unblinding")
    anonymous_ids = {row[1] for row in expected_rows(public_plan)}
    if set(sealed_mapping.values()) != anonymous_ids or len(set(sealed_mapping.values())) != len(sealed_mapping):
        raise M7InteractiveReviewError("sealed mapping does not cover the exact anonymous configs")
    return dict(sealed_mapping)
