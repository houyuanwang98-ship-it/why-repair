import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness.m6_controller import aggregate_by_experiment, validate_controller_manifest, validate_run_ledger
import jsonschema


ROOT = Path(__file__).parents[1]
OUT = ROOT / "data/benchmarks/m6/engineering_fixture_v0_2"


class M6EngineeringFixtureV02Test(unittest.TestCase):
    def test_frozen_fixture_replays_complete_nine_method_pipeline(self):
        manifest = json.loads((OUT / "manifest.json").read_text())
        ledger = json.loads((OUT / "ledger.json").read_text())
        scoring = json.loads((OUT / "scoring.json").read_text())
        aggregate = json.loads((OUT / "aggregate.json").read_text())
        self.assertEqual(9, len(validate_controller_manifest(manifest)["configs"]))
        self.assertTrue(validate_run_ledger(manifest, ledger)["complete"])
        self.assertEqual(aggregate, aggregate_by_experiment(manifest, ledger, scoring))

    def test_fixture_is_provider_free_and_formal_gate_remains_closed(self):
        summary = json.loads((OUT / "summary.json").read_text())
        self.assertEqual(18, summary["assignment_count"])
        self.assertEqual(0, summary["provider_model_calls"])
        self.assertEqual(0, summary["provider_cost"])
        self.assertFalse(summary["formal_m6_execution_allowed"])

    def test_builder_is_deterministic(self):
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in OUT.glob("*.json")}
        subprocess.run([sys.executable, str(ROOT / "scripts/build_m6_engineering_fixture_v0_2.py")],
                       cwd=ROOT, check=True)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in OUT.glob("*.json")}
        self.assertEqual(before, after)

    def test_summary_schema_and_release_hashes(self):
        schema = json.loads((ROOT / "schemas/m6_engineering_fixture_summary_v0_2.schema.json").read_text())
        jsonschema.validate(json.loads((OUT / "summary.json").read_text()), schema)
        release = json.loads((ROOT / "data/benchmarks/m6/engineering_fixture_release_v0_2.json").read_text())
        self.assertFalse(release["formal_m6_execution_allowed"])
        for relative, expected in release["artifacts"].items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
