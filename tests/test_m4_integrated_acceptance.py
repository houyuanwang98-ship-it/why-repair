import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/benchmarks/m4/integrated_acceptance_v1.json"
SCHEMA = ROOT / "schemas/m4_integrated_acceptance_v1.schema.json"


class M4IntegratedAcceptanceTest(unittest.TestCase):
    def test_release_identity_coverage_and_frozen_artifacts(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(manifest))
        self.assertEqual("m4-integrated-v1.0", manifest["release"])
        self.assertEqual("accepted_by_person_a", manifest["status"])
        self.assertNotEqual(manifest["reviewer_id"], manifest["verifier_id"])

        gold = [
            json.loads(line)
            for line in (ROOT / manifest["benchmark"]["source"])
            .read_text(encoding="utf-8").splitlines()
        ]
        expected = sorted(
            row["proof_id"] for row in gold if row["gold_counterexample_status"] == "valid"
        )
        self.assertEqual(expected, sorted(manifest["benchmark"]["sample_ids"]))
        self.assertEqual(len(expected), manifest["benchmark"]["valid_counterexample_count"])
        self.assertEqual(len(expected), manifest["benchmark"]["accepted_count"])

        for relative, expected_digest in manifest["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected_digest, relative)


if __name__ == "__main__":
    unittest.main()
