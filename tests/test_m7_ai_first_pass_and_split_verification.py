import json
import unittest
from pathlib import Path

from harness.m7_interactive_review import M7InteractiveReviewError
from harness.m7_interactive_verification import validate_human_verification, verify_partition
from scripts.build_m7_ai_first_pass_and_split_verification_v0_2 import build


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "human_review/m7_ai_first_pass_v0_2"


class M7AIFirstPassSplitVerificationTest(unittest.TestCase):
    def test_materialized_bundle_rebuilds_exactly(self):
        disk = {path.stem: json.loads(path.read_text()) for path in OUT.glob("*.json")}
        self.assertEqual(build(), disk)
        self.assertEqual(900, len(disk["ai_first_pass"]["rows"]))
        self.assertEqual(450, len(disk["user_cases_001_025"]["rows"]))
        self.assertEqual(450, len(disk["person_b_cases_026_050"]["rows"]))
        verify_partition(disk["ai_first_pass"], disk["user_cases_001_025"], disk["person_b_cases_026_050"])

    def test_human_forms_are_pending_and_cannot_pass(self):
        bundle = build()
        for name in ("user_cases_001_025", "person_b_cases_026_050"):
            form = bundle[name]
            with self.assertRaisesRegex(M7InteractiveReviewError, "not complete"):
                validate_human_verification(form, form, require_complete=True)

    def test_partition_overlap_fails(self):
        bundle = build()
        right = dict(bundle["person_b_cases_026_050"])
        right["assigned_case_ids"] = list(bundle["user_cases_001_025"]["assigned_case_ids"])
        with self.assertRaisesRegex(M7InteractiveReviewError, "disjoint"):
            verify_partition(bundle["ai_first_pass"], bundle["user_cases_001_025"], right)


if __name__ == "__main__":
    unittest.main()
