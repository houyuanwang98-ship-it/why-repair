import json
import unittest

from scripts.build_m5_codex_ai_proxy_review_v0_1 import IRREPARABLE, build


class M5CodexAIProxyReviewTest(unittest.TestCase):
    def test_complete_proxy_scope_is_nonhuman(self):
        result = build()
        self.assertEqual(36, result["scope"]["case_count"])
        self.assertEqual(24, result["scope"]["repairable_count"])
        self.assertEqual(12, result["scope"]["irreparable_count"])
        self.assertFalse(result["human_review"])
        self.assertFalse(result["eligible_as_human_evidence"])
        self.assertFalse(result["eligible_for_scientific_gold"])
        self.assertEqual(IRREPARABLE, {
            row["proof_id"] for row in result["rows"] if row["disposition"] == "irreparable"
        })

    def test_every_proxy_decision_is_bound_to_inputs_and_patches(self):
        result = build()
        self.assertEqual(36, len({row["proof_id"] for row in result["rows"]}))
        for row in result["rows"]:
            self.assertEqual(64, len(row["input_sha256"]))
            self.assertTrue(row["patch_sha256"])
            self.assertTrue(all(len(value) == 64 for value in row["patch_sha256"]))
            self.assertTrue(row["failed_edge_and_resolution"])


if __name__ == "__main__":
    unittest.main()
