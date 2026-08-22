import json
import hashlib
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

    def test_blind_packets_match_and_contain_no_gold(self):
        base = OUT.parent
        a_bytes = (base / "annotator_a_packet.json").read_bytes()
        b_bytes = (base / "annotator_b_packet.json").read_bytes()
        a = json.loads(a_bytes)
        b = json.loads(b_bytes)
        self.assertEqual(a["cases"], b["cases"])
        self.assertNotEqual(a["reviewer_slot"], b["reviewer_slot"])
        self.assertTrue(all(case["annotation"] is None for case in a["cases"]))
        self.assertFalse(any("gold" in key.lower() for case in a["cases"] for key in case))
        self.assertNotEqual(hashlib.sha256(a_bytes).hexdigest(), hashlib.sha256(b_bytes).hexdigest())

    def test_adjudication_is_fail_closed(self):
        item = json.loads((OUT.parent / "adjudication_template.json").read_text(encoding="utf-8"))
        self.assertIsNone(item["annotator_a_sha256"])
        self.assertIsNone(item["annotator_b_sha256"])
        self.assertEqual("blocked_until_two_locked_independent_packets", item["status"])


if __name__ == "__main__":
    unittest.main()
