import json
import unittest
from pathlib import Path

from scripts.build_m7_human_readable_case_reviews_v0_2 import build, render_person_b_execution_review


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "human_review/m7_human_readable_v0_2"


def without_human_answers(text):
    return [line for line in text.splitlines()
            if line and line != "确认" and not line.startswith("纠正：")]


class M7HumanReadableCaseReviewTest(unittest.TestCase):
    def test_all_cards_have_original_and_prefilled_decision(self):
        cards, _, _ = build()
        self.assertEqual(50, len(cards))
        self.assertEqual([f"m2-{i:03d}" for i in range(1, 51)], [row["proof_id"] for row in cards])
        for row in cards:
            self.assertTrue(row["theorem"])
            self.assertTrue(row["original_proof"])
            self.assertTrue(row["ai_diagnosis"])
            self.assertTrue(row["ai_proposed_review"])
            if row["disposition"] == "irreparable":
                self.assertIsNone(row["corrected_proof"])
            else:
                self.assertTrue(row["corrected_proof"])

    def test_materialized_files_rebuild_exactly(self):
        cards, user_doc, person_b_doc = build()
        self.assertEqual(cards, json.loads((OUT / "all_50_prefilled_cards.json").read_text()))
        self.assertEqual(without_human_answers(user_doc), without_human_answers(
            (OUT / "user_cases_001_025.md").read_text()))
        self.assertEqual(without_human_answers(person_b_doc), without_human_answers(
            (OUT / "person_b_cases_026_050.md").read_text()))
        self.assertEqual(25, user_doc.count("\n## m2-"))
        self.assertEqual(25, person_b_doc.count("\n## m2-"))
        self.assertEqual(render_person_b_execution_review() + "\n",
                         (OUT / "person_b_execution_review.md").read_text())

    def test_repaired_cards_include_patch_rationale_and_full_proof(self):
        cards, _, _ = build()
        repaired = [row for row in cards if row["disposition"] == "repaired"]
        self.assertEqual(26, len(repaired))
        self.assertTrue(all(row["patch_rationales"] and row["corrected_proof"] for row in repaired))


if __name__ == "__main__":
    unittest.main()
