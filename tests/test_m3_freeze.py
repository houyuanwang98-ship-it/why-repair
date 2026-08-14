import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1"
MANIFEST = EXPERIMENT / "freeze_manifest.json"
SPEC = importlib.util.spec_from_file_location("m3_evaluator_freeze", ROOT / "scripts/m3_evaluator.py")
M3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M3)


class M3FreezeTests(unittest.TestCase):
    def test_frozen_artifact_hashes_match_manifest(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for relative, expected in manifest["artifacts"].items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_frozen_run_is_complete_and_report_provenance_is_current(self):
        config = json.loads((EXPERIMENT / "config.json").read_text(encoding="utf-8"))
        report = json.loads((EXPERIMENT / "report.json").read_text(encoding="utf-8"))
        gold = ROOT / "data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl"
        predictions = EXPERIMENT / "session/results"
        self.assertEqual(config["status"], "frozen")
        self.assertEqual(config["version"], "m3-evaluator-v1.0")
        self.assertEqual(report["sample_count"], 50)
        self.assertEqual(report["prediction_coverage"], 1.0)
        self.assertEqual(len(list(predictions.glob("*.json"))), 50)
        self.assertEqual(report["inputs"]["gold_sha256"], M3.sha256_path(gold))
        self.assertEqual(report["inputs"]["predictions_sha256"], M3.sha256_path(predictions))


if __name__ == "__main__":
    unittest.main()
