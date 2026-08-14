import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_m2_dataset.py"
SPEC = importlib.util.spec_from_file_location("audit_m2_dataset", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class M2RevalidationTests(unittest.TestCase):
    def test_automated_acceptance_checks_pass(self):
        report = MODULE.audit()
        self.assertTrue(all(report["automated_checks"].values()), report)

    def test_strict_mode_honestly_blocks_missing_human_evidence(self):
        completed = subprocess.run([sys.executable, str(SCRIPT), "--strict"], capture_output=True, text=True)
        self.assertEqual(1, completed.returncode)
        report = json.loads(completed.stdout)
        self.assertEqual("engineering_pass_strict_acceptance_blocked", report["result"])

    def test_historical_pilot_is_not_misrepresented_as_held_out(self):
        registry = json.loads((ROOT / "data/benchmarks/m2/audit/sample_registry_v1.json").read_text(encoding="utf-8"))
        self.assertFalse(registry["defaults"]["held_out"])
        self.assertNotEqual("pass", registry["evidence_status"]["held_out_test"])

    def test_missing_graph_gold_is_an_explicit_strict_gate(self):
        report = MODULE.audit()
        self.assertTrue(report["representation_gates"]["source_spans_node_coverage_edges_and_dag"].startswith("fail_"))
        self.assertTrue(report["automated_checks"]["posthoc_m3_node_coverage_edges_and_dag_valid"])

    def test_counterexample_second_review_is_derived_not_trusted(self):
        report = MODULE.audit()
        self.assertTrue(report["automated_checks"]["all_global_counterexamples_have_distinct_m4_reviewer_and_verifier"])
        self.assertEqual("pass", report["human_evidence_gates"]["global_counterexamples_second_reviewed"])

    def test_registry_covers_exactly_the_50_source_ids(self):
        registry = json.loads((ROOT / "data/benchmarks/m2/audit/sample_registry_v1.json").read_text(encoding="utf-8"))
        registered = [item for group in registry["theorem_families"] for item in group["sample_ids"]]
        self.assertEqual(50, len(registered))
        self.assertEqual(50, len(set(registered)))


if __name__ == "__main__":
    unittest.main()
