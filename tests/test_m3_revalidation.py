import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_m3_evaluator.py"
SPEC = importlib.util.spec_from_file_location("audit_m3_evaluator", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(AUDIT)


class M3RevalidationTests(unittest.TestCase):
    def test_all_reconstructable_automated_checks_pass(self):
        report = AUDIT.audit()
        self.assertTrue(all(report["automated_checks"].values()), report)

    def test_strict_mode_blocks_unrecoverable_evidence(self):
        completed = subprocess.run([sys.executable, str(SCRIPT), "--strict"], capture_output=True, text=True)
        self.assertEqual(1, completed.returncode)
        self.assertEqual("engineering_pass_strict_acceptance_blocked", json.loads(completed.stdout)["result"])

    def test_frozen_v1_evaluator_was_not_modified(self):
        manifest = json.loads((ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/freeze_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("d17d176f9efd8cef46fec985b780d943623651293456d65366f2dacb771836df", manifest["artifacts"]["scripts/m3_evaluator.py"])
        self.assertTrue(AUDIT.manifest_valid(ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/freeze_manifest.json"))

    def test_non_blind_run_is_not_relabelled_publication_result(self):
        report = AUDIT.audit()
        self.assertTrue(report["automated_checks"]["frozen_run_declares_non_publication_and_non_blind"])
        self.assertTrue(report["strict_evidence_gates"]["held_out_test_isolation"].startswith("fail_"))

    def test_revalidation_manifest_binds_every_declared_artifact(self):
        manifest = json.loads((ROOT / "data/benchmarks/m3/revalidation/manifest_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(AUDIT.digest(ROOT / manifest["base_freeze_manifest"]), manifest["base_freeze_manifest_sha256"])
        for name, expected in manifest["artifacts"].items():
            self.assertEqual(expected, AUDIT.digest(ROOT / name), name)


if __name__ == "__main__":
    unittest.main()
