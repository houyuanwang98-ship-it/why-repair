import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("m3_evaluator_v0_2", ROOT / "scripts/m3_evaluator_v0_2.py")
M3 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(M3)


class M3EvaluatorV02Tests(unittest.TestCase):
    def test_required_safety_and_localization_metrics(self):
        gold = [{
            "proof_id": "p1", "gold_validity_status": "invalid", "gold_error_type": "algebraic_invalidity",
            "gold_first_gap_step": None, "gold_first_invalid_step": 2,
            "gold_nodes": [
                {"node_id": "n1", "node_type": "introduction", "depends_on": [], "verdict_group": "accepted"},
                {"node_id": "n2", "node_type": "calculation", "depends_on": ["n1"], "verdict_group": "invalid"},
            ],
        }]
        prediction = [{
            "id": "p1", "validity_status": "undetermined", "error_type": "undetermined",
            "first_gap_step": None, "first_invalid_step": 2,
            "proof_graph": [
                {"node_id": 1, "node_type": "introduction", "depends_on": [], "status": "closed"},
                {"node_id": 2, "node_type": "calculation_step", "depends_on": [1], "status": "closed"},
            ],
        }]
        report, _ = M3.evaluate(gold, prediction)
        self.assertEqual("m3-evaluator-report-0.2", report["schema_version"])
        self.assertEqual(1.0, report["first_error_localization"]["exact_accuracy"])
        self.assertEqual(1.0, report["first_error_localization"]["overall_accuracy"])
        self.assertEqual(0.0, report["dependency_edges"]["critical_dependency_omission_rate"])
        self.assertEqual(1.0, report["safety_rates"]["node_false_acceptance_rate"])
        self.assertEqual(0.0, report["safety_rates"]["proof_false_acceptance_rate"])
        self.assertEqual(1.0, report["safety_rates"]["proof_abstention_rate"])
        self.assertEqual("not_evaluable", report["segmentation"]["status"])


if __name__ == "__main__":
    unittest.main()
