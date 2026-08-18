import json
import unittest

from scripts.import_m7_case_level_human_reviews_v0_2 import OUT, build
from scripts.finalize_m7_interactive_50_case_v0_2 import OUT as ACCEPTANCE_OUT, build as build_acceptance


class M7CaseLevelHumanReviewTest(unittest.TestCase):
    def test_materialized_result_rebuilds_exactly(self):
        result = build()
        self.assertEqual(result, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual({"cases": 50, "confirmed": 45, "corrected": 5}, result["summary"])
        self.assertEqual([f"m2-{number:03d}" for number in range(1, 51)],
                         [row["case_id"] for row in result["rows"]])

    def test_corrections_are_the_five_human_selected_cases(self):
        result = build()
        corrected = {row["case_id"] for row in result["rows"]
                     if row["verification"] == "corrected"}
        self.assertEqual({"m2-028", "m2-032", "m2-038", "m2-042", "m2-044"}, corrected)

    def test_scope_does_not_overclaim_blind_row_review(self):
        result = build()
        self.assertIn("not_900_row_blind_review", result["scope"])
        self.assertTrue(any("does not complete Person B" in item for item in result["limitations"]))

    def test_final_acceptance_uses_the_authorized_50_case_scope(self):
        acceptance = build_acceptance()
        self.assertEqual(acceptance, json.loads(ACCEPTANCE_OUT.read_text(encoding="utf-8")))
        self.assertTrue(acceptance["interactive_m7_50_case_review_complete"])
        self.assertEqual("not_required_by_user_scope",
                         acceptance["human_review"]["person_b_execution_verification"])
        self.assertFalse(acceptance["formal_m7_experiment_allowed"])


if __name__ == "__main__":
    unittest.main()
