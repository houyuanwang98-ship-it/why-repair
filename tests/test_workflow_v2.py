"""Semantic acceptance tests. All responses are scripted, never model evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from harness.workflow_v2.contracts import (ROOT, SCHEMAS, EXPERIMENT_MODEL, VALIDATION_MODEL,
    ContractError, digest, judge_input, public_problem, validate_judgment, strict_accept, write_once)
from harness.workflow_v2.controller import ProofState, confirmed_certificate, review_pass
from harness.workflow_v2.engine import Workflow
from harness.workflow_v2.runtime import Calls, ExecutionDisabled, RunStop, isolated_process
from harness.workflow_v2.experiment import prepare, validate_bundle, preflight, aggregate
from harness.workflow_v2.evidence import exact_numeric_relation, rule_candidates


PROBLEM = {"theorem": "D.", "assumptions": ["A."], "domain": "real algebra",
           "proof_text": "A.\nB.\nC.\nD.", "explicit_subgoals": []}


def graph():
    return {"nodes": [{"node_id": f"n{i+1}", "text": t, "claim": t,
             "depends_on": deps, "scope": [], "goal_refs": ["main"] if i == 3 else []}
            for i, (t, deps) in enumerate(zip(["A.", "B.", "C.", "D."],
                                            [[], ["n1"], ["n1"], ["n2", "n3"]]))], "ambiguities": []}


def evaluation(status="closed", counterexample=None):
    def make(p):
        return {"target": p["target"], "status": status, "checked_obligation": p["target_node"]["claim"],
                "reason": "Scripted test, not mathematical evidence", "counterexample": counterexample,
                "unresolved_conditions": ["unknown assumption"] if status == "undetermined" else []}
    return make


def diagnosis(p):
    return {"target": p["target"], "confirmation": "confirmed", "kind": "gap",
            "failed_edge": "Missing implication", "quote": p["target_node"]["text"], "reason": "test defect"}


def replacement(p):
    cert = p.get("certificate", p.get("routing"))
    target = p["target"]
    return {"base_state_digest": p["base_state_digest"], "certificate_id": cert["certificate_id"],
            "target": target, "operation": "replace", "nodes": [{"node_id": target["node_id"],
            "text": "Repaired " + p["target_node"]["text"], "claim": p["target_node"]["claim"],
            "depends_on": p["target_node"]["depends_on"], "scope": [],
            "goal_refs": ["main"] if target["node_id"] == "n4" else []}],
            "target_dependencies_after": [], "counterexample": None, "reason": "test patch"}


def review(p):
    return {"patch_digest": p["patch_digest"], "resolved": "pass", "problem_preserved": "pass",
            "scope_valid": "pass", "dependencies_valid": "pass", "introduced_errors": [],
            "unresolved_conditions": [], "reason": "scripted review"}


AUDIT = {"validity": "pass", "rigor": "pass", "problem_preserved": "pass", "goal_coverage": "pass",
         "issues": [], "unresolved_conditions": [], "reason": "scripted full audit"}
CANDIDATE = {"kind": "proof", "text": "Scripted final proof.", "reason": "fixture only"}


def judge(p):
    return {"sample_id": p["sample_id"], "input_digest": digest(p), "candidate_kind": "proof",
            "validity": "valid", "rigor": "pass", "problem_preservation": "pass", "goal_coverage": "pass",
            "counterexample_validity": "not_applicable", "findings": [], "unresolved_obligations": [],
            "evidence_scope": "model_only", "reason": "scripted judgment"}


class Scripted:
    def __init__(self, steps, transform=None):
        self.steps = list(steps)
        self.inputs = []
        self.transform = transform

    def __call__(self, **kwargs):
        name, response = self.steps.pop(0)
        if kwargs["output_schema"] != SCHEMAS[name]:
            raise AssertionError(f"unexpected schema, wanted {name}")
        self.inputs.append((name, deepcopy(kwargs)))
        value = response(kwargs["input_payload"]) if callable(response) else deepcopy(response)
        raw = {"requested_model": kwargs["model"], "model": None, "output_text": json.dumps(value),
               "return_code": 0, "latency_seconds": 0.01,
               "events": [{"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 20}}],
               "usage": {"reasoning_output_tokens": None}}
        return self.transform(raw) if self.transform else raw


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)

    def run_workflow(self, steps, method="full_system", **kwargs):
        adapter = Scripted(steps)
        calls = Calls(self.path / "calls", fixture_adapter=adapter)
        result = Workflow(PROBLEM, calls, **kwargs).run(method)
        self.assertNotEqual("runtime_failed", result["terminal_status"], result["stop_reason"])
        self.assertFalse(adapter.steps, f"unused scripted phases: {adapter.steps}")
        return result, adapter

    def test_full_loop_repairs_and_revalidates(self):
        result, adapter = self.run_workflow([("graph", graph()), ("evaluate", evaluation()),
            ("evaluate", evaluation("gap")), ("diagnose", diagnosis), ("generate_patch", replacement),
            ("review_patch", review), ("evaluate", evaluation()), ("evaluate", evaluation()),
            ("evaluate", evaluation()), ("audit", AUDIT)])
        self.assertEqual(result["terminal_status"], "proof_ready")
        self.assertIn("patch_review", result["internal_checks"])
        self.assertIn("internal_final_audit", result["internal_checks"])
        event = next(e for e in result["events"] if e["event"] == "patch_applied")
        self.assertIn("n4", event["invalidated"])
        self.assertNotIn("n3", event["invalidated"])
        self.assertEqual(result["evidence_kind"], "offline_fixture")
        self.assertTrue(all(k["model"] == EXPERIMENT_MODEL[0] and k["sampling"]["reasoning_effort"] == "xhigh"
                            for _, k in adapter.inputs))

    def test_internal_final_failure_cannot_be_local_success(self):
        audit = {**AUDIT, "validity": "fail", "issues": [{"node_id": "n4", "kind": "invalid", "quote": "D.", "reason": "gap"}]}
        result, _ = self.run_workflow([("graph", graph())] + [("evaluate", evaluation())] * 4 +
            [("audit", audit), ("diagnose", diagnosis), ("generate_patch", replacement), ("review_patch", review),
             ("evaluate", evaluation()), ("audit", AUDIT)])
        self.assertEqual(result["terminal_status"], "proof_ready")
        self.assertEqual(result["internal_checks"].count("internal_final_audit"), 2)

    def test_uncertainty_does_not_become_certificate(self):
        result, _ = self.run_workflow([("graph", graph()), ("evaluate", evaluation("undetermined")),
                                      ("evaluate", evaluation("undetermined"))])
        self.assertEqual(result["terminal_status"], "undetermined")
        self.assertFalse(list(self.path.rglob("certificate-*.json")))

    def test_rejected_patch_does_not_change_proof(self):
        def reject(p):
            return {**review(p), "resolved": "fail", "introduced_errors": ["new error"]}
        result, _ = self.run_workflow([("graph", graph()), ("evaluate", evaluation()),
            ("evaluate", evaluation("gap")), ("diagnose", diagnosis), ("generate_patch", replacement),
            ("review_patch", reject), ("generate_patch", replacement)])
        self.assertEqual(result["terminal_status"], "repair_not_found")
        self.assertEqual(result["candidate_text"], PROBLEM["proof_text"])

    def test_verified_counterexample_is_not_proof(self):
        counter = {"scope": "theorem", "target": PROBLEM["theorem"], "witness": "test witness"}
        def check(p):
            return {"counterexample_digest": p["counterexample_digest"], "scope": "theorem",
                    "assumptions": "pass", "domain": "pass", "target_refuted": "pass",
                    "unresolved_conditions": [], "reason": "test only"}
        result, _ = self.run_workflow([("graph", graph()), ("evaluate", evaluation("invalid", counter)),
                                      ("counterexample_review", check)])
        self.assertEqual(result["terminal_status"], "counterexample_ready")
        self.assertEqual(result["system_claim"], "theorem_false")

    def test_original_and_independent_baselines_have_real_call_counts(self):
        feedback = {"issues": ["check assumptions"], "reason": "test"}
        for method, steps, expected in [
            ("original", [], 0), ("direct_rewrite", [("candidate", CANDIDATE)], 1),
            ("self_refine", [("candidate", CANDIDATE), ("feedback", feedback), ("candidate", CANDIDATE)], 3),
            ("generator_critic", [("candidate", CANDIDATE), ("feedback", feedback), ("candidate", CANDIDATE)], 3),
            ("best_of_n", [("candidate", CANDIDATE)] * 3 + [("select", {"selected_id": "choice-2", "reason": "test"})], 4)]:
            with self.subTest(method=method):
                scripted = Scripted(steps)
                calls = Calls(self.path / method, fixture_adapter=scripted)
                result = Workflow(PROBLEM, calls).run(method)
                self.assertEqual(result["terminal_status"], "proof_ready", result["stop_reason"])
                self.assertEqual(calls.count, expected)

    def closed_state(self):
        state = ProofState(PROBLEM, graph())
        for n in state.nodes:
            state.record(n, evaluation()({"target": state.ref(n), "target_node": n}), "fixture")
        return state

    def make_patch(self, state, target_id="n2"):
        n = state.find(target_id)
        cert = confirmed_certificate(state, n, diagnosis({"target": state.ref(n), "target_node": n}))
        p = replacement({"target": state.ref(n), "target_node": n, "certificate": cert,
                         "base_state_digest": digest(state.snapshot())})
        return cert, p

    def test_patch_transaction_retains_unaffected_branch(self):
        s = self.closed_state()
        old = s.snapshot()
        cert, p = self.make_patch(s)
        draft = s.draft_patch(p, cert)
        self.assertEqual(s.snapshot(), old)
        s.commit(draft)
        self.assertEqual(s.find("n2")["status"], "pending")
        self.assertEqual(s.find("n4")["status"], "pending")
        self.assertEqual(s.find("n3")["status"], "closed")
        self.assertEqual(s.frontier()["node_id"], "n2")

    def test_removed_edge_keeps_old_descendants_invalid(self):
        s = self.closed_state()
        cert, p = self.make_patch(s, "n4")
        p.update(operation="set_dependencies", nodes=[], target_dependencies_after=["n3"])
        draft = s.draft_patch(p, cert)
        self.assertEqual(draft.find("n4")["status"], "pending")
        # Deleting n2 rewires n4, but n4 must still be invalidated from the old graph.
        cert, p = self.make_patch(s)
        p.update(operation="delete", nodes=[])
        draft = s.draft_patch(p, cert)
        self.assertIn("n4", draft.events[-1]["invalidated"])
        self.assertEqual(draft.find("n4")["status"], "pending")

    def test_cyclic_patch_rolls_back_all_state(self):
        s = self.closed_state()
        cert, p = self.make_patch(s)
        old = deepcopy(s.__dict__)
        p["nodes"][0]["depends_on"] = ["n4"]
        with self.assertRaises(ContractError):
            s.draft_patch(p, cert)
        self.assertEqual(s.__dict__, old)

    def test_cannot_delete_goal_or_reuse_old_version(self):
        s = self.closed_state()
        cert, p = self.make_patch(s, "n4")
        p.update(operation="delete", nodes=[])
        with self.assertRaises(ContractError): s.draft_patch(p, cert)
        cert, p = self.make_patch(s)
        p["target"]["version"] = 999
        with self.assertRaises(ContractError): s.draft_patch(p, cert)

    def test_gap_is_not_a_trusted_premise(self):
        s = self.closed_state()
        s.find("n2")["status"] = "gap"
        with self.assertRaises(ContractError): s.context(s.find("n4"))

    def test_graph_cannot_omit_source_or_escape_scope(self):
        g = graph()
        g["nodes"].pop(1)
        with self.assertRaises(ContractError): ProofState(PROBLEM, g)
        g = graph()
        g["nodes"][1]["scope"] = ["n1"]
        with self.assertRaises(ContractError): ProofState(PROBLEM, g)

    def test_review_is_bound_to_patch_and_unknown_rejects(self):
        r = review({"patch_digest": digest({"x": 1})})
        r["resolved"] = "unknown"
        self.assertFalse(review_pass(r, {"x": 1}))
        with self.assertRaises(ContractError): review_pass(r, {"x": 2})

    def test_blind_payload_keeps_domain_and_strips_gold(self):
        source = {**PROBLEM, "gold": "invalid", "method": "full_system", "claimed_outcome": "success"}
        p = judge_input(source, "test candidate", "blind-example")
        self.assertEqual(p["domain"], PROBLEM["domain"])
        self.assertEqual(set(p), set(SCHEMAS["judge_input"]["properties"]))
        self.assertFalse({"gold", "method", "claimed_outcome", "proof_text"}.intersection(p))

    def test_judge_identity_unknown_counterexample_and_evidence(self):
        p = judge_input(PROBLEM, "candidate", "blind-example")
        j = judge(p)
        self.assertTrue(strict_accept(validate_judgment(j, p)))
        j["rigor"] = "unknown"
        self.assertFalse(strict_accept(j))
        j["sample_id"] = "wrong"
        with self.assertRaises(ContractError): validate_judgment(j, p)
        j = judge(p)
        j["findings"] = [{"quote": "not in candidate", "reason": "test"}]
        with self.assertRaises(ContractError): validate_judgment(j, p)
        j = {**judge(p), "candidate_kind": "counterexample", "validity": "not_applicable", "counterexample_validity": "valid"}
        self.assertFalse(strict_accept(validate_judgment(j, p)))

    def test_live_calls_disabled_before_adapter_creation(self):
        with patch("harness.workflow_v2.runtime.build_codex_adapter") as build:
            calls = Calls(self.path)
            with self.assertRaises(ExecutionDisabled): calls.call("candidate", {})
            build.assert_not_called()

    def test_final_judge_uses_fixed_gpt6_high(self):
        scripted = Scripted([("judge", judge)])
        calls = Calls(self.path, fixture_adapter=scripted, judge=True)
        p = judge_input(PROBLEM, "candidate", "blind-example")
        calls.call("judge", p)
        kwargs = scripted.inputs[0][1]
        self.assertEqual(kwargs["model"], VALIDATION_MODEL[0])
        self.assertEqual(kwargs["sampling"], {"reasoning_effort": "high"})
        with self.assertRaises(ContractError): calls.call("candidate", {})

    def test_budget_overrun_and_missing_usage_never_accept(self):
        calls = Calls(self.path / "overrun", fixture_adapter=Scripted([("candidate", CANDIDATE)]), max_tokens=25)
        with self.assertRaises(RunStop) as e: calls.call("candidate", {})
        self.assertEqual(e.exception.status, "budget_exhausted")
        self.assertEqual(calls.tokens, 30)
        scripted = Scripted([("candidate", CANDIDATE)], lambda r: {**r, "events": []})
        calls = Calls(self.path / "unknown", fixture_adapter=scripted)
        with self.assertRaises(RunStop): calls.call("candidate", {})
        self.assertFalse(calls.accounting_complete)

    def test_tool_output_cannot_enter_proof(self):
        def tool(r):
            r["events"].append({"type": "item.completed", "item": {"type": "command_execution"}})
            return r
        calls = Calls(self.path, fixture_adapter=Scripted([("candidate", CANDIDATE)], tool))
        with self.assertRaises(RunStop): calls.call("candidate", {})
        self.assertFalse(list(self.path.rglob("validated.json")))

    def test_resume_reuses_only_exact_request_and_restores_cost(self):
        first = Calls(self.path, fixture_adapter=Scripted([("candidate", CANDIDATE)]))
        first.call("candidate", {"value": 1})
        second_adapter = Scripted([])
        second = Calls(self.path, fixture_adapter=second_adapter)
        second.call("candidate", {"value": 1})
        self.assertEqual(second.tokens, 30)
        self.assertFalse(second_adapter.inputs)
        changed = Calls(self.path, fixture_adapter=Scripted([]))
        with self.assertRaises(ContractError): changed.call("candidate", {"value": 2})

    def test_process_disables_tools_and_preserves_fixed_request(self):
        with patch("harness.workflow_v2.runtime.subprocess.run") as run:
            isolated_process(["codex", "exec", "--model", "gpt-5.6-sol", "-"], env={"OPENAI_MODEL": "wrong", "PATH": "/bin"})
            command = run.call_args.args[0]
            self.assertIn("shell_tool", command)
            self.assertIn("apps", command)
            self.assertIn('web_search="disabled"', command)
            self.assertNotIn("OPENAI_MODEL", run.call_args.kwargs["env"])

    def test_cli_rejects_execution_and_model_override(self):
        for args in [("runtime",), ("runtime", "--model", "wrong", "--execute")]:
            p = subprocess.run([sys.executable, "scripts/run_workflow_v2.py", *args, "--bundle", str(self.path)],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)

    def test_prepare_has_600_inputs_and_72_unrun_assignments(self):
        with patch("harness.workflow_v2.runtime.build_codex_adapter") as build:
            m = prepare(self.path)
            self.assertEqual((m["corpus_cases"], m["pilot_cases"], m["assignment_count"]), (600, 12, 72))
            report = preflight(self.path, inspect_environment=False)
            self.assertFalse(report["experiment_started"])
            self.assertFalse(list(self.path.rglob("call-*")))
            self.assertTrue(all(v["counts"]["not_run"] == 12 for v in aggregate(self.path)["methods"].values()))
            build.assert_not_called()
        manifest = json.loads((self.path / "manifest.json").read_text())
        manifest["implementation_digest"] = "changed"
        (self.path / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ContractError): validate_bundle(self.path)

    def test_exact_arithmetic_rejects_symbols_undefined_and_partial_matches(self):
        self.assertTrue(exact_numeric_relation("0.1+0.2=0.3"))
        self.assertFalse(exact_numeric_relation("1/3 > 1/2"))
        for text in ("x/x=1", "1/0=2", "because 2+2=4", "2**1000000=1", "2+2=4 therefore T"):
            self.assertIsNone(exact_numeric_relation(text), text)

    def test_rule_retrieval_is_unverified_and_does_not_close_a_node(self):
        rows = rule_candidates("normal subgroup quotient group")
        self.assertTrue(rows)
        self.assertTrue(all(r["applicability"] == "unchecked" and r["conditions"] for r in rows))

    def test_local_counterexample_does_not_claim_false_theorem(self):
        counter = {"scope": "local", "target": "A.", "witness": "test witness"}
        def review_counter(p):
            return {"counterexample_digest": p["counterexample_digest"], "scope": "local",
                    "assumptions": "pass", "domain": "pass", "target_refuted": "pass",
                    "unresolved_conditions": [], "reason": "local only"}
        def uncertain(p):
            return {**diagnosis(p), "confirmation": "uncertain", "kind": "undetermined"}
        result, _ = self.run_workflow([("graph", graph()), ("evaluate", evaluation("invalid", counter)),
                                      ("counterexample_review", review_counter), ("diagnose", uncertain)])
        self.assertEqual(result["terminal_status"], "undetermined")
        self.assertNotEqual(result["system_claim"], "theorem_false")

    def test_missing_goal_cannot_pass_with_closed_nodes(self):
        missing = {**AUDIT, "goal_coverage": "fail", "issues": [
            {"node_id": "__goal__", "kind": "gap", "quote": "D.", "reason": "Goal missing"}]}
        def abstain(p):
            r = replacement(p)
            return {**r, "operation": "abstain", "nodes": []}
        result, _ = self.run_workflow([("graph", graph())] + [("evaluate", evaluation())] * 4 +
                                     [("audit", missing), ("diagnose", diagnosis), ("generate_patch", abstain)])
        self.assertEqual(result["terminal_status"], "repair_not_found")
        self.assertTrue(any(n["synthetic"] for n in result["snapshot"]["nodes"]))

    def test_ablations_change_actual_revalidation_and_audit(self):
        s = self.closed_state()
        s.revalidation = "retain_stale_for_experiment"
        cert, p = self.make_patch(s)
        draft = s.draft_patch(p, cert)
        self.assertEqual(draft.find("n4")["status"], "closed")
        self.assertTrue(draft.events[-1]["stale_reused_for_ablation"])
        s.revalidation = "all_nodes"
        cert, p = self.make_patch(s)
        draft = s.draft_patch(p, cert)
        self.assertTrue(all(n["status"] == "pending" for n in draft.nodes))
        result, _ = self.run_workflow([("graph", graph())] + [("evaluate", evaluation())] * 4,
                                     options={"internal_final_audit": False})
        self.assertEqual(result["terminal_status"], "proof_ready")
        self.assertNotIn("internal_final_audit", result["internal_checks"])

    def test_single_round_stops_after_one_rejected_patch(self):
        def reject(p): return {**review(p), "resolved": "fail"}
        result, _ = self.run_workflow([("graph", graph()), ("evaluate", evaluation()),
            ("evaluate", evaluation("gap")), ("diagnose", diagnosis), ("generate_patch", replacement),
            ("review_patch", reject)], options={"max_patch_attempts": 1})
        self.assertEqual(result["terminal_status"], "budget_exhausted")

    def test_plain_certificate_and_disabled_search_affect_payloads(self):
        result, adapter = self.run_workflow([("graph", graph()), ("evaluate", evaluation()),
            ("evaluate", evaluation("gap")), ("diagnose", diagnosis), ("generate_patch", replacement),
            ("review_patch", review), ("evaluate", evaluation()), ("evaluate", evaluation()),
            ("evaluate", evaluation()), ("audit", AUDIT)],
            options={"certificate_format": "plain_same_information", "counterexample_search": False})
        inputs = [p[1]["input_payload"] for p in adapter.inputs if p[0] == "generate_patch"]
        self.assertNotIn("certificate", inputs[0])
        self.assertIn("diagnosis_text", inputs[0])
        self.assertTrue(all(not k["input_payload"]["counterexample_search"] for phase, k in adapter.inputs if phase == "evaluate"))

    def test_interrupted_request_does_not_get_free_retry(self):
        c = Calls(self.path, fixture_adapter=Scripted([("candidate", CANDIDATE)]))
        c.call("candidate", {})
        for name in ("response.json", "validated.json", "accounting.json"):
            (self.path / "call-001-candidate" / name).unlink()
        adapter = Scripted([])
        c = Calls(self.path, fixture_adapter=adapter)
        with self.assertRaises(RunStop): c.call("candidate", {})
        self.assertFalse(c.accounting_complete)
        self.assertFalse(adapter.inputs)


if __name__ == "__main__":
    unittest.main()
