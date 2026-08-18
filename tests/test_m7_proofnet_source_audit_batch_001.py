import json
import unittest

from scripts.build_m7_proofnet_source_audit_batch_001 import OUT, build


class M7ProofNetSourceAuditBatch001Test(unittest.TestCase):
    def test_materialized_batch_rebuilds(self):
        packet, markdown = build()
        self.assertEqual(packet, json.loads((OUT / "source_audit_batch_001.json").read_text()))
        self.assertEqual(markdown + "\n", (OUT / "source_audit_batch_001.md").read_text())
        self.assertEqual(25, len(packet["rows"]))
        self.assertEqual(25, len({row["case_id"] for row in packet["rows"]}))

    def test_ai_first_pass_does_not_pretend_to_be_human_gold(self):
        packet, _ = build()
        self.assertEqual("ai_first_pass_complete_human_verification_pending", packet["status"])
        self.assertTrue(all(row["human_verification"] is None for row in packet["rows"]))
        self.assertTrue(all(row["ai_reason"] and row["proposed_use"] for row in packet["rows"]))


if __name__ == "__main__":
    unittest.main()
