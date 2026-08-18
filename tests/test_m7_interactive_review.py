import json
import unittest
from pathlib import Path

from harness.m7_interactive_review import (
    M7InteractiveReviewError, authorize_unblinding, build_template, disputes,
    validate_review, verify_independent_pair,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_plan.json").read_text())
MAPPING = json.loads((ROOT / "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_sealed_mapping.json").read_text())


def completed(slot, reviewer, decision="accepted"):
    row = build_template(PLAN, reviewer_slot=slot)
    row.update(status="complete", reviewer_id=reviewer, independence_statement="independent review",
               started_at="2026-08-17T10:00:00+08:00", finished_at="2026-08-17T11:00:00+08:00")
    for item in row["rows"]:
        item.update(decision=decision, mathematically_valid=decision == "accepted",
                    problem_preserved=True, no_new_error=True, minimal=True,
                    finding=None if decision == "accepted" else "review finding")
    return row


class M7InteractiveReviewTest(unittest.TestCase):
    def test_repository_templates_are_exact_and_pending(self):
        for slot in ("person_a", "person_b"):
            path = ROOT / f"human_review/m7_interactive_v0_2/{slot}_blind_review.json"
            self.assertEqual(build_template(PLAN, reviewer_slot=slot), json.loads(path.read_text()))
            validate_review(PLAN, json.loads(path.read_text()), require_complete=False)
            with self.assertRaisesRegex(M7InteractiveReviewError, "not complete"):
                validate_review(PLAN, json.loads(path.read_text()), require_complete=True)

    def test_complete_pair_requires_distinct_reviewers(self):
        a, b = completed("person_a", "alice"), completed("person_b", "bob")
        verify_independent_pair(PLAN, a, b)
        b["reviewer_id"] = "alice"
        with self.assertRaisesRegex(M7InteractiveReviewError, "distinct identities"):
            verify_independent_pair(PLAN, a, b)

    def test_missing_decision_and_false_accept_fail_closed(self):
        review = completed("person_a", "alice")
        review["rows"][0]["decision"] = None
        with self.assertRaisesRegex(M7InteractiveReviewError, "every decision"):
            validate_review(PLAN, review, require_complete=True)
        review = completed("person_a", "alice")
        review["rows"][0]["mathematically_valid"] = False
        with self.assertRaisesRegex(M7InteractiveReviewError, "all mathematical checks"):
            validate_review(PLAN, review, require_complete=True)

    def test_disputes_block_unblinding_until_third_review(self):
        a, b = completed("person_a", "alice"), completed("person_b", "bob")
        b["rows"][0].update(decision="rejected", mathematically_valid=False, finding="incorrect step")
        pending = disputes(PLAN, a, b)
        self.assertEqual(1, len(pending))
        with self.assertRaisesRegex(M7InteractiveReviewError, "third-person"):
            authorize_unblinding(PLAN, a, b, MAPPING, [])
        item = pending[0]
        adjudication = {key: item[key] for key in ("case_id", "anonymized_config_id", "review_payload_sha256")}
        adjudication.update(third_reviewer_id="carol", decision="rejected", finding="confirmed")
        self.assertEqual(MAPPING, authorize_unblinding(PLAN, a, b, MAPPING, [adjudication]))

    def test_agreement_allows_unblinding_only_after_complete_pair(self):
        a, b = completed("person_a", "alice"), completed("person_b", "bob")
        self.assertEqual([], disputes(PLAN, a, b))
        self.assertEqual(MAPPING, authorize_unblinding(PLAN, a, b, MAPPING, []))


if __name__ == "__main__":
    unittest.main()
