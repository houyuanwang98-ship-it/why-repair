import json
import unittest

from scripts.build_m7_proofnet_pilot30_v0_1 import OUT, build


class M7ProofNetPilot30V01Test(unittest.TestCase):
    def test_selection_is_deterministic_and_nonconfirmatory(self):
        item = build()
        self.assertEqual(item, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual(30, item["record_count"])
        self.assertEqual({"development": 10, "test": 10, "train": 10}, item["split_counts"])
        self.assertEqual(30, len({row["case_id"] for row in item["records"]}))
        self.assertEqual("pending_independent_annotation", item["gold_status"])
        self.assertFalse(item["formal_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
