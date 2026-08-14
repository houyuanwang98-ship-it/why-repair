import json
import unittest
from pathlib import Path

from harness import DualAgentController, ingest_m3_run


ROOT = Path(__file__).parents[1]
RESULTS = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/session/results"


class M3ControllerHandoffTest(unittest.TestCase):
    def test_frozen_full50_run_enters_controller_without_semantic_rewrite(self):
        rows = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(RESULTS.glob("*.json"))
        ]
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        summary = ingest_m3_run(
            controller, rows, run_id="m3-full50-controller-compat"
        )
        self.assertEqual(50, summary["proof_count"])
        self.assertEqual(122, summary["node_count"])
        self.assertEqual(101, summary["evaluation_count"])
        self.assertEqual(25, summary["error_certificate_count"])
        self.assertEqual(
            {
                "active": 75,
                "blocked_by_invalid_dependency": 21,
                "pending_repair": 25,
                "undetermined": 1,
            },
            summary["lifecycle_counts"],
        )
        self.assertEqual([], summary["ready_for_evaluation"])
        self.assertEqual(25, len(summary["repair_queue"]))
        self.assertTrue(all(item["status"] == "ready" for item in summary["repair_queue"]))


if __name__ == "__main__":
    unittest.main()
