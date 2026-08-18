import json
import unittest
from pathlib import Path

from harness.m7_person_b import audit_near_duplicates, validate_candidate_records
from scripts.build_m7_proofnet_250_source_v0_1 import OUT, canonical_digest


class M7ProofNet250SourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in (OUT / "candidate.jsonl").read_text().splitlines()]
        cls.manifest = json.loads((OUT / "manifest.json").read_text())

    def test_candidate_passes_formal_record_schema_and_counts(self):
        report = validate_candidate_records(self.records)
        self.assertEqual(250, report["record_count"])
        self.assertEqual({"development": 50, "test": 150, "train": 50}, report["split_counts"])
        self.assertEqual(self.manifest["candidate_digest"], canonical_digest(self.records))

    def test_sources_are_unique_and_test_preserves_upstream_test_boundary(self):
        source = json.loads((OUT / "private_source_index.json").read_text())
        self.assertEqual(250, len({row["proofnet_id"] for row in source}))
        split_by_case = {row["case_id"]: row["split"] for row in self.records}
        self.assertTrue(all(row["proofnet_source_split"] == "test"
                            for row in source if split_by_case[row["case_id"]] == "test"))
        self.assertTrue(all(row["proofnet_source_split"] == "valid"
                            for row in source if split_by_case[row["case_id"]] != "test"))

    def test_no_cross_split_near_duplicate_at_frozen_threshold(self):
        findings = audit_near_duplicates(self.records, threshold=0.85)
        self.assertFalse([row for row in findings if row["cross_split"]])

    def test_private_formal_statement_is_not_in_public_candidate(self):
        public_text = (OUT / "candidate.jsonl").read_text()
        self.assertNotIn("formal_statement", public_text)
        self.assertTrue(all(row["license_status"] == "verified_redistributable" for row in self.records))


if __name__ == "__main__":
    unittest.main()
