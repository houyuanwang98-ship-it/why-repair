import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import m3_audited_evaluator as M3  # noqa: E402


class M3AuditedEvaluatorTests(unittest.TestCase):
    def test_false_theorem_can_be_excluded_from_localization(self):
        gold = [{
            "proof_id": "p1", "gold_validity_status": "invalid", "gold_error_type": "false_generalization",
            "gold_first_gap_step": None, "gold_first_invalid_step": 1,
            "gold_first_invalid_applicable": False, "gold_nodes": [],
        }]
        prediction = [{
            "id": "p1", "validity_status": "invalid", "error_type": "false_generalization",
            "first_gap_step": None, "first_invalid_step": 1, "proof_graph": [],
        }]
        report, details = M3.evaluate(gold, prediction)
        self.assertEqual(report["first_invalid_localization"]["applicable_count"], 0)
        self.assertFalse(details[0]["first_invalid_applicable"])


if __name__ == "__main__":
    unittest.main()
