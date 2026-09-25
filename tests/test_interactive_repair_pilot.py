"""Transport tests use explicit synthetic fixtures; no mathematical result is accepted here."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_interactive_repair_pilot import run_case


def fixture_case(*, arithmetic_error=False):
    first = "2 == 3" if arithmetic_error else "Synthetic inference requiring review"
    nodes = [{
        "proof_id": "fixture_case", "node_id": 1, "version": 1, "order_key": 10,
        "claim": first, "self_contained_claim": first, "node_type": "fixture", "depends_on": [],
    }]
    if arithmetic_error:
        nodes.append({
            "proof_id": "fixture_case", "node_id": 2, "version": 1, "order_key": 20,
            "claim": "Synthetic consumer", "self_contained_claim": "Synthetic consumer",
            "node_type": "fixture",
            "depends_on": [{"proof_id": "fixture_case", "node_id": 1, "version": 1}],
        })
    return {"proof_id": "fixture_case", "theorem": "Synthetic theorem", "assumptions": [],
            "domain": "reals" if arithmetic_error else "synthetic domain", "nodes": nodes}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture_accepted_local_review(request):
    """Schema-valid transport fixture, not a claimed mathematical judgment."""
    source = request["input"]["sources"][0]
    citation = {"source_id": source["source_id"], "digest": source["digest"]}
    return {
        "input_digest": request["input_digest"], "evaluator_id": "person-a",
        "decision": "accepted", "error_type": None, "rule": "fixture rule",
        "conditions": [{"condition": "fixture condition", "status": "supported",
                        "source_refs": [citation], "justification": "fixture only"}],
        "circularity": {"status": "clear", "source_refs": [], "justification": "fixture only"},
        "conclusion": {"statement": request["input"]["claim"], "source_refs": [citation],
                       "justification": "fixture only"},
        "bridge_steps": [], "reason": "fixture only",
    }


class InteractiveRepairPilotTransportTest(unittest.TestCase):
    def make_paths(self, directory, case):
        root = Path(directory)
        case_path = root / "case.json"
        run_dir = root / "run"
        write_json(case_path, case)
        return case_path, run_dir

    def pending(self, run_dir):
        return json.loads((run_dir / "pending.json").read_text(encoding="utf-8"))["requests"][0]

    def test_missing_response_is_pending_not_callback_failure_and_replay_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            case_path, run_dir = self.make_paths(directory, fixture_case())
            self.assertEqual(3, run_case(case_path, run_dir))
            first_checkpoint = (run_dir / "checkpoint.json").read_bytes()
            self.assertEqual(3, run_case(case_path, run_dir))
            self.assertEqual(first_checkpoint, (run_dir / "checkpoint.json").read_bytes())
            checkpoint = json.loads(first_checkpoint)
            costs = checkpoint["controller_snapshot"]["cost_events"]
            self.assertEqual("awaiting_external_response", costs[-1]["status"])
            self.assertNotIn("error_type", costs[-1])
            self.assertEqual(0, checkpoint["transport_accounting"]["fresh_model_calls_by_controller"])
            self.assertIsNone(checkpoint["transport_accounting"]["external_usage_and_cost"])

    def test_supplied_response_replays_then_emits_next_exact_request(self):
        with tempfile.TemporaryDirectory() as directory:
            case_path, run_dir = self.make_paths(directory, fixture_case())
            run_case(case_path, run_dir)
            first = self.pending(run_dir)
            response_path = run_dir / first["response_filename"]
            write_json(response_path, fixture_accepted_local_review(first["request"]))
            self.assertEqual(3, run_case(case_path, run_dir))
            second = self.pending(run_dir)
            self.assertEqual("final_review", second["phase"])
            self.assertEqual("online_reviewer", second["agent"]["role"])
            checkpoint = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
            statuses = [e["status"] for e in checkpoint["transport_accounting"]["events"]]
            self.assertEqual(["supplied_external_response_replayed", "awaiting_external_response"], statuses)
            self.assertTrue(all(e["usage"] is None and e["cost"] is None
                                for e in checkpoint["transport_accounting"]["events"]))

    def test_malformed_supplied_local_review_is_terminal_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            case_path, run_dir = self.make_paths(directory, fixture_case())
            run_case(case_path, run_dir)
            packet = self.pending(run_dir)
            write_json(run_dir / packet["response_filename"], {})
            self.assertEqual(2, run_case(case_path, run_dir))
            terminal = json.loads((run_dir / "terminal.json").read_text(encoding="utf-8"))
            self.assertEqual("failed", terminal["status"])
            self.assertEqual("malformed_or_rejected_response", terminal["stop_reason"])
            self.assertIn("review_rejected", terminal["failure"]["reason"])

    def test_interface_proposal_is_separate_phase_before_contract_review(self):
        with tempfile.TemporaryDirectory() as directory:
            case_path, run_dir = self.make_paths(directory, fixture_case(arithmetic_error=True))
            self.assertEqual(3, run_case(case_path, run_dir))
            proposal = self.pending(run_dir)
            self.assertEqual("interface_proposal", proposal["phase"])
            self.assertEqual("generator", proposal["agent"]["role"])
            self.assertEqual(1, proposal["response_schema"]["properties"]["statements"]["minItems"])
            write_json(run_dir / proposal["response_filename"], {"statements": ["Synthetic boundary"]})
            self.assertEqual(3, run_case(case_path, run_dir))
            review = self.pending(run_dir)
            self.assertEqual("contract_review", review["phase"])
            self.assertEqual("online_reviewer", review["agent"]["role"])
            self.assertIsInstance(review["response_schema"], dict)
            self.assertEqual("repair-interface-review-v1", review["request"]["input"]["policy"])

    def test_gold_bearing_case_is_rejected_before_controller_work(self):
        with tempfile.TemporaryDirectory() as directory:
            case = fixture_case()
            case["Gold"] = "forbidden"
            case_path, run_dir = self.make_paths(directory, case)
            with self.assertRaisesRegex(ValueError, "Gold-bearing"):
                run_case(case_path, run_dir)
            self.assertFalse(run_dir.exists())


if __name__ == "__main__":
    unittest.main()
