import json
import unittest

from scripts.import_m7_opc_v0_2_supplemental_review import OUT, SUMMARY, build


class M7OPCV02SupplementalReviewImportTest(unittest.TestCase):
    def test_completed_review_is_bound_and_rebuilds(self):
        adjudication, summary = build()
        self.assertEqual(adjudication, json.loads(OUT.read_text()))
        self.assertEqual(summary, json.loads(SUMMARY.read_text()))
        self.assertEqual("six_changed_proofs_human_review_complete", adjudication["status"])
        self.assertEqual(6, adjudication["row_count"])
        self.assertEqual(6, adjudication["usable_node_gold_count"])
        # Segmentation cleanup re-mapped one proposed node onto its reviewed
        # node (opc250-214: n11 -> n10), so exact agreement rose from 0 to 1.
        self.assertEqual(1, adjudication["exact_first_error_agreement"])
        self.assertEqual(5, adjudication["proof_verdict_agreement"])

    def test_primary_human_corrections_are_normalized(self):
        adjudication, summary = build()
        rows = {row["case_id"]: row for row in adjudication["rows"]}
        self.assertEqual(("n10", "algebraic_invalidity"),
                         (rows["opc250-214"]["reviewed_first_error_node"],
                          rows["opc250-214"]["reviewed_error_type"]))
        self.assertEqual("n24", rows["opc250-039"]["reviewed_first_error_node"])
        self.assertEqual(25, summary["total_human_reviewed_cases"])
        self.assertEqual(23, summary["usable_node_gold_count"])
        self.assertEqual(134, summary["remaining_incorrect_cases_pending_mapping_review"])


if __name__ == "__main__":
    unittest.main()
