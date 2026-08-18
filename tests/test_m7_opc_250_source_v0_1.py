import json
import unittest

from harness.m7_person_b import audit_near_duplicates, validate_candidate_records
from scripts.build_m7_opc_250_source_v0_1 import OUT, canonical, is_geometry_problem


class M7OPC250SourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in (OUT / "candidate.jsonl").read_text().splitlines()]
        cls.seed = json.loads((OUT / "seed_annotations.json").read_text())
        cls.manifest = json.loads((OUT / "manifest.json").read_text())

    def test_candidate_schema_counts_and_digest(self):
        report = validate_candidate_records(self.records)
        self.assertEqual(250, report["record_count"])
        self.assertEqual({"development": 50, "test": 150, "train": 50}, report["split_counts"])
        self.assertEqual(self.manifest["candidate_digest"], canonical(self.records))

    def test_existing_human_verdict_composition_and_unique_problems(self):
        self.assertEqual(250, len({row["opc_problem_id"] for row in self.seed}))
        groups = {}
        for row in self.seed:
            groups[row["label_group"]] = groups.get(row["label_group"], 0) + 1
        self.assertEqual({"human_localized_incorrect": 41,
                          "human_incorrect_ai_localized": 159, "human_correct": 50}, groups)
        self.assertEqual(200, sum(row["human_proof_verdict"] == "incorrect" for row in self.seed))

    def test_human_locations_and_mapping_review_boundary(self):
        high = [row for row in self.seed if row["label_group"] == "human_localized_incorrect"]
        self.assertTrue(all(row["prefilled_first_issue"]["location_provenance"] == "human_selected_text"
                            for row in high))
        self.assertTrue(all(row["human_mapping_verification"] is None for row in self.seed))

    def test_geometry_is_excluded(self):
        self.assertTrue(self.manifest["geometry_records_excluded_before_sampling"] > 0)
        self.assertFalse(any(is_geometry_problem(row["problem"]) for row in self.records))


if __name__ == "__main__":
    unittest.main()
