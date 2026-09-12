"""Regression tests for observed pilot contract failures, never mathematical gold."""
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest

from harness.workflow_v2.contracts import ContractError, read, judge_input, validate_judgment
from harness.workflow_v2.controller import ProofState
from harness.workflow_v2.engine import Workflow
from harness.workflow_v2.runtime import Calls, RunStop
from tests.test_workflow_v2 import Scripted, CANDIDATE, PROBLEM, graph, evaluation, judge, AUDIT


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)

    def test_empty_reason_corrected_once_and_failed_cost_retained_on_replay(self):
        adapter = Scripted([("candidate", {**CANDIDATE, "reason": ""}), ("candidate", CANDIDATE)])
        calls = Calls(self.path, fixture_adapter=adapter, max_output_retries=1)
        self.assertEqual(calls.call("candidate", {"problem": PROBLEM}), CANDIDATE)
        self.assertEqual((calls.count, calls.tokens, calls.output_corrections), (2, 60, 1))
        self.assertFalse((self.path / "call-001-candidate/validated.json").exists())
        self.assertIn("reason", adapter.inputs[1][1]["input_payload"]["output_contract_feedback"]["validation_error"])
        replay = Calls(self.path, fixture_adapter=Scripted([]), max_output_retries=1)
        self.assertEqual(replay.call("candidate", {"problem": PROBLEM}), CANDIDATE)
        self.assertEqual((replay.count, replay.tokens), (2, 60))
        self.assertTrue(replay.accounting_complete)

    def test_whitespace_and_second_invalid_output_cannot_pass(self):
        calls = Calls(self.path, fixture_adapter=Scripted([
            ("candidate", {**CANDIDATE, "reason": " "}), ("candidate", {**CANDIDATE, "reason": ""})]),
            max_output_retries=1)
        with self.assertRaises(RunStop): calls.call("candidate", {})
        self.assertEqual(calls.count, 2)
        self.assertFalse(list(self.path.rglob("validated.json")))

    def test_correction_cannot_bypass_attempt_or_token_budget(self):
        for name, limits in [("attempt", {"max_calls": 1}), ("token", {"max_tokens": 30})]:
            calls = Calls(self.path / name, fixture_adapter=Scripted([("candidate", {**CANDIDATE, "reason": ""})]),
                          max_output_retries=1, **limits)
            with self.assertRaises(RunStop) as caught: calls.call("candidate", {})
            self.assertEqual(caught.exception.status, "budget_exhausted")
            self.assertEqual((calls.count, calls.tokens), (1, 30))

    def test_security_and_accounting_failures_are_not_retried(self):
        for name, transform in [("model", lambda r: {**r, "model": "other"}),
                                ("usage", lambda r: {**r, "events": []})]:
            calls = Calls(self.path / name, fixture_adapter=Scripted([("candidate", CANDIDATE)], transform),
                          max_output_retries=1)
            with self.assertRaises(RunStop): calls.call("candidate", {})
            self.assertEqual(calls.count, 1)
        with self.assertRaises(ContractError):
            Calls(self.path / "judge", judge=True, max_output_retries=1)

    def test_bad_graph_is_not_applied_before_corrected_graph_passes(self):
        bad = graph()
        bad["nodes"][0]["goal_refs"] = ["subgoal-1"]
        adapter = Scripted([("graph", bad), ("graph", graph()),
            *[("evaluate", evaluation()) for _ in range(4)], ("audit", AUDIT)])
        calls = Calls(self.path, fixture_adapter=adapter, max_output_retries=1)
        result = Workflow(PROBLEM, calls).run("full_system")
        self.assertEqual(result["terminal_status"], "proof_ready", result["stop_reason"])
        self.assertEqual(adapter.inputs[0][1]["input_payload"]["allowed_goal_refs"], ["main"])
        self.assertEqual(result["output_contract_corrections"], 1)
        self.assertFalse((self.path / "call-001-graph/validated.json").exists())

    def test_closed_with_conditions_is_rejected_without_mutating_state(self):
        state = ProofState(PROBLEM, graph())
        node = state.nodes[0]
        payload = {"target": state.ref(node), "target_node": node}
        bad = {**evaluation()(payload), "unresolved_conditions": ["unsupported assumption"]}
        calls = Calls(self.path, fixture_adapter=Scripted([("evaluate", bad),
            ("evaluate", {**bad, "status": "undetermined"})]), max_output_retries=1)
        result = calls.call("evaluate", payload, validator=lambda r: state.check_evaluation(node, r))
        self.assertEqual(node["status"], "pending")
        state.record(node, result, calls.count)
        self.assertEqual(node["status"], "undetermined")

    def test_patch_generator_receives_goal_preservation_metadata(self):
        state = ProofState(PROBLEM, graph())
        calls = Calls(self.path, fixture_adapter=Scripted([]))
        workflow = Workflow(PROBLEM, calls)
        workflow.state = state
        for node in state.nodes[:-1]:
            state.record(node, evaluation()({"target": state.ref(node), "target_node": node}), 0)
        captured = []
        def call(phase, payload, **kwargs):
            captured.append(payload)
            raise RunStop("budget_exhausted", "test capture")
        calls.call = call
        with self.assertRaises(RunStop): workflow.repair(state.nodes[-1], {"kind": "gap"})
        self.assertEqual(captured[0]["target_node"]["goal_refs"], ["main"])

    def test_redundant_error_cannot_be_strict_accepted(self):
        payload = judge_input(PROBLEM, "A.\nB.", "blind-test")
        judgment = judge(payload)
        judgment["findings"] = [{"quote": "B.", "reason": "explicit invalid redundant inference"}]
        with self.assertRaises(ContractError): validate_judgment(judgment, payload)
        judgment["rigor"] = "fail"
        self.assertEqual(validate_judgment(judgment, payload)["validity"], "valid")


if __name__ == "__main__":
    unittest.main()
