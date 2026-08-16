import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness.m6_controller import aggregate_by_experiment, validate_controller_manifest, validate_run_ledger
import jsonschema


ROOT = Path(__file__).parents[1]
OUT = ROOT / "data/benchmarks/m6/chatgpt_interactive_full50_v0_2"


class M6ChatGPTInteractiveFull50V02Test(unittest.TestCase):
    def test_complete_450_assignment_replay(self):
        manifest = json.loads((OUT / "manifest.json").read_text())
        ledger = json.loads((OUT / "ledger.json").read_text())
        scoring = json.loads((OUT / "scoring.json").read_text())
        self.assertEqual(9, len(validate_controller_manifest(manifest)["configs"]))
        self.assertEqual(50, len(manifest["sample_ids"]))
        self.assertEqual(450, len(ledger))
        self.assertEqual(450, len(scoring))
        report = validate_run_ledger(manifest, ledger)
        self.assertTrue(report["complete"])
        self.assertEqual(0, report["total_model_calls"])

    def test_aggregate_replays_and_scope_cannot_be_overclaimed(self):
        manifest = json.loads((OUT / "manifest.json").read_text())
        ledger = json.loads((OUT / "ledger.json").read_text())
        scoring = json.loads((OUT / "scoring.json").read_text())
        aggregate = json.loads((OUT / "aggregate.json").read_text())
        analysis = json.loads((OUT / "analysis.json").read_text())
        self.assertEqual(aggregate, aggregate_by_experiment(manifest, ledger, scoring))
        self.assertFalse(analysis["scientific_claim_allowed"])
        self.assertEqual("not_computed_invalid_independence_shared_underlying_predictions",
                         analysis["inferential_statistics"])
        self.assertTrue(analysis["interactive_engineering_acceptance_eligible"])

    def test_full_system_consumes_m5_reviewed_repairs_without_false_repairs(self):
        analysis = json.loads((OUT / "analysis.json").read_text())
        full = analysis["metrics_by_method"]["full_system"]
        direct = analysis["metrics_by_method"]["direct_judgment"]
        self.assertEqual(1.0, full["verified_repair_success_rate"]["value"])
        self.assertEqual(0.0, full["false_repair_rate"]["value"])
        self.assertEqual(0.0, full["new_error_introduction_rate"]["value"])
        self.assertEqual("not_applicable", direct["verified_repair_success_rate"]["value"])

    def test_builder_is_deterministic(self):
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in OUT.glob("*.json")}
        subprocess.run([sys.executable, str(ROOT / "scripts/build_m6_chatgpt_interactive_full50_v0_2.py")],
                       cwd=ROOT, check=True)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in OUT.glob("*.json")}
        self.assertEqual(before, after)

    def test_analysis_and_joint_acceptance_schemas(self):
        analysis_schema = json.loads((ROOT / "schemas/m6_chatgpt_interactive_analysis_v0_2.schema.json").read_text())
        acceptance_schema = json.loads((ROOT / "schemas/m6_interactive_joint_acceptance_v0_2.schema.json").read_text())
        jsonschema.validate(json.loads((OUT / "analysis.json").read_text()), analysis_schema)
        acceptance_path = ROOT / "data/benchmarks/m6/interactive_joint_acceptance_v0_2.json"
        acceptance = json.loads(acceptance_path.read_text())
        jsonschema.validate(acceptance, acceptance_schema)
        for relative, expected in acceptance["artifacts"].items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
