import json
import unittest
from pathlib import Path

from harness.m7_mapping import clean_nodes
from scripts.rebuild_m7_opc_v0_2_node_annotations import V2, canonical_json_sha


class M7OPCV02RebuildIdempotencyTest(unittest.TestCase):
    def test_current_annotations_are_already_clean(self):
        candidates = {row["case_id"]: row for row in map(
            json.loads, (V2 / "candidate.jsonl").read_text(encoding="utf-8").splitlines())}
        annotations = json.loads((V2 / "node_annotations.json").read_text(encoding="utf-8"))
        for row in annotations["rows"]:
            self.assertEqual(clean_nodes(candidates[row["case_id"]]["proof"]), row["proof_nodes"])

    def test_coverage_uses_cross_platform_canonical_json_hashes(self):
        coverage = json.loads((V2 / "human_review_coverage.json").read_text(encoding="utf-8"))
        inherited = json.loads((V2 / "inherited_human_review.json").read_text(encoding="utf-8"))
        review = Path(__file__).resolve().parents[1] / "human_review/m7_opc_250_v0_2/supplemental_review_batch_001_adjudicated.json"
        supplemental = json.loads(review.read_text(encoding="utf-8"))
        self.assertEqual("canonical_json_utf8_v1", coverage["digest_mode"])
        self.assertEqual(canonical_json_sha(inherited), coverage["inherited_review_sha256"])
        self.assertEqual(canonical_json_sha(supplemental), coverage["supplemental_adjudication_sha256"])

    def test_provisional_mappings_reference_real_nodes_and_remain_non_gold(self):
        packet = json.loads((V2 / "codex_provisional_manual_mappings.json").read_text(encoding="utf-8"))
        annotations = {row["case_id"]: row for row in json.loads(
            (V2 / "node_annotations.json").read_text(encoding="utf-8"))["rows"]}
        self.assertFalse(packet["scientific_gold_allowed"])
        self.assertTrue(all(row["human_confirmation"] is None for row in packet["rows"]))
        for row in packet["rows"]:
            valid = {node["node_id"] for node in annotations[row["case_id"]]["proof_nodes"]}
            self.assertIn(row["first_error_node"], valid)


if __name__ == "__main__":
    unittest.main()
