"""AI-first, split-human verification workflow for interactive M7 only."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from harness.m7_interactive_review import CHECKS, DECISIONS, M7InteractiveReviewError


def build_human_verification(ai_review: Mapping[str, Any], *, reviewer_slot: str,
                             case_ids: Sequence[str]) -> dict[str, Any]:
    if reviewer_slot not in {"user_person_a", "person_b"}:
        raise M7InteractiveReviewError("unknown verification slot")
    selected = set(case_ids)
    if not selected or len(selected) != len(case_ids):
        raise M7InteractiveReviewError("verification case partition must be nonempty and unique")
    source = [row for row in ai_review["rows"] if row["case_id"] in selected]
    if {row["case_id"] for row in source} != selected:
        raise M7InteractiveReviewError("AI review does not cover the requested case partition")
    return {
        "schema_version": "m7-interactive-human-verification-0.2",
        "reviewer_slot": reviewer_slot, "status": "pending", "reviewer_id": None,
        "independence_statement": None, "started_at": None, "finished_at": None,
        "assigned_case_ids": list(case_ids),
        "rows": [{"case_id": row["case_id"], "anonymized_config_id": row["anonymized_config_id"],
                  "review_payload_sha256": row["review_payload_sha256"],
                  "ai_decision": row["decision"], "ai_finding": row["finding"],
                  "verification": None, "corrected_decision": None,
                  **{f"corrected_{check}": None for check in CHECKS}, "finding": None}
                 for row in source],
    }


def validate_human_verification(template: Mapping[str, Any], submission: Mapping[str, Any],
                                *, require_complete: bool = True) -> dict[str, Any]:
    row = dict(submission)
    if set(row) != set(template) or row["schema_version"] != template["schema_version"]:
        raise M7InteractiveReviewError("human verification has an invalid shape")
    immutable = {"reviewer_slot", "assigned_case_ids"}
    if any(row[key] != template[key] for key in immutable):
        raise M7InteractiveReviewError("human verification changed its frozen assignment")
    if len(row["rows"]) != len(template["rows"]):
        raise M7InteractiveReviewError("human verification is incomplete")
    identity_fields = ("case_id", "anonymized_config_id", "review_payload_sha256", "ai_decision", "ai_finding")
    for actual, expected in zip(row["rows"], template["rows"]):
        if set(actual) != set(expected) or any(actual[key] != expected[key] for key in identity_fields):
            raise M7InteractiveReviewError("human verification rows changed the AI or payload binding")
    if require_complete:
        if row["status"] != "complete":
            raise M7InteractiveReviewError("human verification is not complete")
        for key in ("reviewer_id", "independence_statement", "started_at", "finished_at"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise M7InteractiveReviewError(f"complete human verification requires {key}")
        for item in row["rows"]:
            if item["verification"] not in {"confirmed", "corrected", "undetermined"}:
                raise M7InteractiveReviewError("every row requires a human verification")
            if item["verification"] == "confirmed":
                if item["corrected_decision"] is not None or any(item[f"corrected_{c}"] is not None for c in CHECKS):
                    raise M7InteractiveReviewError("confirmed AI label cannot contain a correction")
            else:
                if item["corrected_decision"] not in DECISIONS or any(
                        not isinstance(item[f"corrected_{c}"], bool) for c in CHECKS):
                    raise M7InteractiveReviewError("corrected/undetermined row requires a complete replacement")
                if not isinstance(item["finding"], str) or not item["finding"].strip():
                    raise M7InteractiveReviewError("corrected/undetermined row requires a finding")
    return row


def verify_partition(ai_review: Mapping[str, Any], left_template: Mapping[str, Any],
                     right_template: Mapping[str, Any]) -> None:
    left, right = set(left_template["assigned_case_ids"]), set(right_template["assigned_case_ids"])
    expected = {row["case_id"] for row in ai_review["rows"]}
    if left & right or left | right != expected:
        raise M7InteractiveReviewError("human partitions must be disjoint and cover every AI-reviewed case")


PERSON_B_EXECUTION_CHECKS = (
    "frozen_artifact_hashes", "complete_900_assignment_ledger", "globally_unique_run_ids",
    "terminal_result_byte_binding", "per_sample_budget_enforcement", "aggregate_reconstruction",
    "deterministic_replay_selection", "anonymous_plan_has_no_method_identity",
    "review_payload_has_no_gold_fields", "sealed_mapping_access_separation",
)


def build_person_b_execution_template() -> dict[str, Any]:
    return {"schema_version": "m7-person-b-execution-verification-0.2", "status": "pending",
            "reviewer_id": None, "started_at": None, "finished_at": None,
            "checks": [{"check_id": check, "decision": None, "evidence": None, "finding": None}
                       for check in PERSON_B_EXECUTION_CHECKS]}
