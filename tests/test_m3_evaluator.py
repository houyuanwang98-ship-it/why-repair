import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m3_evaluator", ROOT / "scripts/m3_evaluator.py")
M3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M3)
INPUT_SPEC = importlib.util.spec_from_file_location("prepare_m3", ROOT / "scripts/prepare_m3_checker_input.py")
PREPARE = importlib.util.module_from_spec(INPUT_SPEC)
INPUT_SPEC.loader.exec_module(PREPARE)


class M3EvaluatorTests(unittest.TestCase):
    def gold(self):
        return [{
            "proof_id": "p1", "gold_validity_status": "invalid", "gold_error_type": "algebraic_invalidity",
            "gold_first_gap_step": None, "gold_first_invalid_step": 2,
            "gold_nodes": [
                {"node_id": "n1", "node_type": "introduction", "depends_on": [], "verdict_group": "accepted"},
                {"node_id": "n2", "node_type": "calculation", "depends_on": ["n1"], "verdict_group": "invalid"},
            ],
        }]

    def prediction(self):
        return [{
            "id": "p1", "validity_status": "invalid", "error_type": "algebraic_invalidity",
            "first_gap_step": None, "first_invalid_step": 2,
            "proof_graph": [
                {"node_id": 1, "node_type": "introduction", "depends_on": [], "status": "closed"},
                {"node_id": 2, "node_type": "calculation_step", "depends_on": [1], "status": "algebraic_invalidity"},
            ],
        }]

    def test_oracle_scores_are_perfect(self):
        report, _ = M3.evaluate(self.gold(), self.prediction())
        self.assertEqual(report["proof_validity"]["accuracy"], 1.0)
        self.assertEqual(report["node_type"]["macro_f1"], 1.0)
        self.assertEqual(report["node_verdict_group"]["accuracy"], 1.0)
        self.assertEqual(report["dependency_edges"]["f1"], 1.0)
        self.assertEqual(report["first_invalid_localization"]["exact_accuracy"], 1.0)

    def test_missing_prediction_is_counted_and_coverage_reported(self):
        report, details = M3.evaluate(self.gold(), [])
        self.assertEqual(report["prediction_coverage"], 0.0)
        self.assertEqual(report["proof_validity"]["accuracy"], 0.0)
        self.assertEqual(report["node_type"]["accuracy"], 0.0)
        self.assertFalse(details[0]["prediction_present"])

    def test_false_positive_location_is_reported(self):
        gold = self.gold()
        gold[0]["gold_first_invalid_step"] = None
        pred = self.prediction()
        report, _ = M3.evaluate(gold, pred)
        self.assertEqual(report["first_invalid_localization"]["false_positive_rate_when_absent"], 1.0)

    def test_m2_source_is_converted_to_checker_contract(self):
        converted = PREPARE.convert({
            "proof_id": "m2-001", "domain": "elementary_algebra", "theorem": "T",
            "assumptions": ["A"], "proof_steps": [{"node_id": "n1", "text": "S"}],
        })
        self.assertEqual(converted["id"], "m2-001")
        self.assertEqual(converted["flawed_proof_steps"], ["S"])

    def test_proof_status_supplies_non_error_categories(self):
        self.assertEqual(M3.prediction_error_type({"validity_status": "valid"}), "no_error")
        self.assertEqual(M3.prediction_error_type({"validity_status": "valid_with_gap"}), "proof_gap")
        self.assertEqual(M3.prediction_error_type({"validity_status": "undetermined"}), "undetermined")


if __name__ == "__main__":
    unittest.main()
