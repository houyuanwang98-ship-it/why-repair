import json
import unittest
from pathlib import Path

import jsonschema

from harness.m7_controller import validate_aggregate_table, validate_run_integrity
from harness.m7_person_b import M7PersonBError
from scripts.build_m7_interactive_engineering_v0_2 import build


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/m7/interactive_engineering_v0_2"


class M7InteractiveEngineeringV02Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disk = {path.stem: json.loads(path.read_text(encoding="utf-8"))
                    for path in OUT.glob("*.json")}

    def test_rebuild_is_exact_and_complete(self):
        self.assertEqual(build(), self.disk)
        self.assertEqual(900, len(self.disk["ledger"]))
        self.assertEqual(900, len(self.disk["results"]))
        self.assertEqual(900, len(self.disk["scoring"]))
        self.assertEqual(18, len(self.disk["aggregate"]))
        self.assertEqual(20, len(self.disk["replay_sample"]))
        self.assertTrue(self.disk["blind_review_plan"]["review_rows"])
        self.assertTrue(self.disk["blind_review_payloads"])

    def test_integrity_and_aggregate_rebuild(self):
        report = validate_run_integrity(self.disk["manifest"], self.disk["ledger"],
                                        self.disk["results"], root=ROOT)
        self.assertTrue(report["complete"])
        self.assertEqual(900, report["assignment_count"])
        self.assertEqual(self.disk["aggregate"], validate_aggregate_table(
            self.disk["manifest"], self.disk["ledger"], self.disk["aggregate"], root=ROOT))

    def test_analysis_schema_and_fail_closed_boundary(self):
        schema = json.loads((ROOT / "schemas/m7_interactive_analysis_v0_2.schema.json").read_text())
        jsonschema.validate(self.disk["analysis"], schema)
        analysis = self.disk["analysis"]
        self.assertFalse(analysis["scientific_claim_allowed"])
        self.assertFalse(analysis["formal_m7_experiment_allowed"])
        self.assertEqual(0, analysis["provider_model_calls"])
        self.assertFalse(analysis["blind_review_completed"])

    def test_blind_packet_hides_method_identity_and_binds_payloads(self):
        public = json.dumps(self.disk["blind_review_plan"], sort_keys=True)
        self.assertNotIn("interactive_same_model_projection", public)
        self.assertNotIn("interactive_different_models_label_projection", public)
        self.assertNotIn("direct_judgment", public)
        payloads = self.disk["blind_review_payloads"]
        for row in self.disk["blind_review_plan"]["review_rows"]:
            self.assertIn(row["review_payload_sha256"], payloads)
        for payload in payloads.values():
            text = json.dumps(payload)
            self.assertNotIn("gold_", text)
            self.assertNotIn("experiment_id", text)
            self.assertNotIn("verified_repair_success", text)
            self.assertNotIn("independent_review_accepted", text)

    def test_replay_report_is_deterministic_and_does_not_claim_provider_replay(self):
        report = self.disk["replay_verification"]
        self.assertEqual(self.disk["replay_sample"], report["selected_run_ids"])
        self.assertTrue(report["all_selected_terminal_success"])
        self.assertFalse(report["provider_replay_performed"])

    def test_joint_acceptance_is_schema_valid_and_byte_bound(self):
        acceptance_path = ROOT / "data/benchmarks/m7/interactive_joint_acceptance_v0_2.json"
        acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas/m7_interactive_joint_acceptance_v0_2.schema.json").read_text())
        jsonschema.validate(acceptance, schema)
        import hashlib
        for relative, expected in acceptance["artifacts"].items():
            self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        upstream = ROOT / acceptance["upstream"]["m6_interactive_acceptance_path"]
        self.assertEqual(acceptance["upstream"]["m6_interactive_acceptance_sha256"],
                         hashlib.sha256(upstream.read_bytes()).hexdigest())

    def test_missing_or_tampered_terminal_fails(self):
        with self.assertRaisesRegex(M7PersonBError, "exact frozen assignment"):
            validate_run_integrity(self.disk["manifest"], self.disk["ledger"][:-1],
                                   self.disk["results"], root=ROOT)
        ledger = [dict(row) for row in self.disk["ledger"]]
        ledger[0]["tokens"] = 8001
        with self.assertRaisesRegex(M7PersonBError, "budget"):
            validate_run_integrity(self.disk["manifest"], ledger, self.disk["results"], root=ROOT)


if __name__ == "__main__":
    unittest.main()
