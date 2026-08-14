import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/benchmarks/m0_m4_completion_audit_v1.json"
SCHEMA = ROOT / "schemas/m0_m4_completion_audit_v1.schema.json"


class M0M4CompletionAuditTest(unittest.TestCase):
    def test_cross_milestone_status_semantics_and_hashes(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(audit))
        self.assertEqual("engineering_complete_with_declared_evidence_limitations", audit["status"])
        self.assertEqual({"M0", "M1", "M2", "M3", "M4"}, set(audit["milestones"]))
        self.assertTrue(all(item["engineering_complete"] for item in audit["milestones"].values()))
        self.assertFalse(audit["milestones"]["M0"]["controller"])
        self.assertIn("cannot be reconstructed", audit["milestones"]["M0"]["limitations"][0])
        self.assertIn("prediction error", audit["milestones"]["M3"]["limitations"][0])
        for relative, expected in audit["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)

        gold = {
            row["proof_id"]: row for row in (
                json.loads(line) for line in
                (ROOT / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl")
                .read_text(encoding="utf-8").splitlines()
            )
        }
        row = gold["m2-028"]
        self.assertEqual("invalid", row["gold_validity_status"])
        self.assertEqual("algebraic_invalidity", row["gold_error_type"])
        self.assertEqual(2, row["gold_first_invalid_step"])


if __name__ == "__main__":
    unittest.main()
