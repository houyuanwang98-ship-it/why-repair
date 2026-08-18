import json
import unittest

from scripts.import_m7_opc_mapping_review_batch_001 import OUT, build


class M7OPCMappingReviewImportTest(unittest.TestCase):
    def test_completed_review_is_bound_and_rebuilds(self):
        result = build()
        self.assertEqual(result, json.loads(OUT.read_text()))
        self.assertEqual(25, result["row_count"])
        self.assertEqual(23, result["usable_node_gold_count"])
        self.assertEqual(2, result["excluded_or_unresolved_count"])
        self.assertEqual("human_calibration_complete_quality_remediation_required", result["status"])

    def test_disputed_and_unresolved_cases_fail_closed(self):
        rows = {row["case_id"]: row for row in build()["rows"]}
        self.assertEqual("source_verdict_disputed", rows["opc250-243"]["review_status"])
        self.assertEqual("first_error_rejected_unresolved", rows["opc250-235"]["review_status"])
        self.assertFalse(rows["opc250-243"]["usable_as_node_gold"])
        self.assertFalse(rows["opc250-235"]["usable_as_node_gold"])
        self.assertEqual("proof_end", rows["opc250-077"]["reviewed_first_error_node"])


if __name__ == "__main__":
    unittest.main()
