import json
import unittest
from pathlib import Path

from harness.m7_person_b import audit_near_duplicates, validate_candidate_records
from scripts.build_m7_opc_250_source_v0_1 import canonical, is_geometry_problem, passes_quality_gate


BASE = Path(__file__).parents[1] / "data/benchmarks/m7/opc_250_v0_2"


class M7OPC250SourceV02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in (BASE / "candidate.jsonl").read_text().splitlines()]
        cls.seed = json.loads((BASE / "seed_annotations.json").read_text())
        cls.manifest = json.loads((BASE / "manifest.json").read_text())
        cls.nodes = json.loads((BASE / "node_annotations.json").read_text())

    def test_schema_distribution_and_digest(self):
        report = validate_candidate_records(self.records)
        self.assertEqual(250, report["record_count"])
        self.assertEqual({"development": 50, "test": 150, "train": 50}, report["split_counts"])
        self.assertEqual(self.manifest["candidate_digest"], canonical(self.records))
        groups = {name: sum(row["label_group"] == name for row in self.seed)
                  for name in self.manifest["label_group_counts"]}
        self.assertEqual({"human_localized_incorrect": 35,
                          "human_incorrect_ai_localized": 155, "human_correct": 60}, groups)

    def test_geometry_and_pathological_proofs_are_excluded(self):
        self.assertFalse(any(is_geometry_problem(row["problem"]) for row in self.records))
        self.assertTrue(all(passes_quality_gate(row["proof"]) for row in self.records))
        self.assertLessEqual(max(len(row["proof_nodes"]) for row in self.nodes["rows"]), 100)
        self.assertLessEqual(max(len(node["text"]) for row in self.nodes["rows"]
                                 for node in row["proof_nodes"]), 700)

    def test_no_near_duplicate_or_cross_split_leak(self):
        self.assertEqual([], audit_near_duplicates(self.records, threshold=0.85))

    def test_node_mapping_is_fail_closed(self):
        self.assertEqual(187, self.nodes["automatic_first_error_mapped"])
        self.assertEqual(3, len(self.nodes["manual_first_error_required"]))

    def test_human_review_coverage_is_explicit(self):
        coverage = json.loads((BASE / "human_review_coverage.json").read_text())
        self.assertEqual(coverage["status"], "review_transfer_and_supplemental_review_complete")
        self.assertEqual(25, coverage["total_human_reviewed_cases"])
        self.assertEqual(23, coverage["usable_node_gold_count"])
        self.assertEqual(134, coverage["remaining_incorrect_cases_pending_mapping_review"])
        self.assertEqual(coverage["total_human_reviewed_cases"],
                         self.manifest["human_review_coverage"]["total_human_reviewed_cases"])


if __name__ == "__main__":
    unittest.main()
