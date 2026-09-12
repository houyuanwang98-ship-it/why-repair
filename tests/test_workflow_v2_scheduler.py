import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from harness.codex_cli import CodexCLIError
from harness.workflow_v2.app_server import PersistentServer
from harness.workflow_v2.contracts import ROOT, SCHEMAS, ContractError, read, digest, write_once
from harness.workflow_v2.runtime import Calls, RunStop
from harness.workflow_v2.scheduler import Scheduler, LANES


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.server = PersistentServer(self.path / "server", "experiment", 0,
            command=[sys.executable, str(ROOT / "tests/fixtures/fake_codex_app_server.py")])
        self.addCleanup(self.server.close)
        self.server.start()

    def call(self, payload=None):
        return self.server(model="gpt-5.6-sol", prompt="fixture", input_payload=payload or {},
            max_output_tokens=100, sampling={"reasoning_effort": "xhigh"},
            output_schema=SCHEMAS["candidate"], timeout_seconds=5)

    def test_process_reuse_fresh_threads_and_observed_unload(self):
        first, second = self.call(), self.call()
        self.assertEqual(first["server_pid"], second["server_pid"])
        self.assertNotEqual(first["codex_thread_id"], second["codex_thread_id"])
        self.assertEqual(self.server.contexts_released, 2)
        self.assertTrue(first["context_released"] and second["context_released"])
        self.assertEqual(second["usage"]["input_tokens"], 31)
        self.assertEqual(second["output_text"], first["output_text"])
        with self.assertRaisesRegex(ContractError, "restart"):
            self.server.start()

    def test_model_effort_lock(self):
        with self.assertRaisesRegex(ContractError, "model mismatch"):
            self.server(model="gpt-6-astra", prompt="", input_payload={}, max_output_tokens=100,
                sampling={"reasoning_effort": "high"}, output_schema={}, timeout_seconds=1)

    def test_startup_checks_catalog_and_unloads_without_model_calls(self):
        result = self.server.check_ready()
        self.assertTrue(result["catalog_available"] and result["context_unload_verified"])
        self.assertEqual(self.server.call_count, 0)
        validator = PersistentServer(self.path / "validator", "validation", 0,
            command=[sys.executable, str(ROOT / "tests/fixtures/fake_codex_app_server.py")])
        self.addCleanup(validator.close)
        validator.start()
        result = validator.check_ready()
        self.assertFalse(result["catalog_available"])
        self.assertEqual(validator.call_count, 0)
        process = read(self.path / "server/process.json")
        # The fake executable ignores CLI arguments; the real command construction is retained in source.
        self.assertEqual(process["server_starts"], 1)

    def test_process_death_is_retained_without_restart(self):
        pid = self.server.process.pid
        with self.assertRaises(CodexCLIError) as error:
            self.call({"crash": True})
        self.assertEqual(error.exception.raw_response["server_pid"], pid)
        self.assertFalse(self.server.healthy)
        with self.assertRaises(ContractError):
            self.call()

    def test_forbidden_tool_activity_is_failure(self):
        with self.assertRaisesRegex(CodexCLIError, "tool or unknown"):
            self.call({"tool": True})

    def test_live_injection_preserves_accounting_and_evidence_kind(self):
        calls = Calls(self.path / "calls", execute=True, live_adapter=self.server)
        calls.call("candidate", {})
        self.assertEqual(calls.summary()["evidence_kind"], "live_model")
        self.assertEqual(calls.tokens, 48)

    def test_missing_usage_never_becomes_zero(self):
        calls = Calls(self.path / "calls", execute=True, live_adapter=self.server)
        with self.assertRaisesRegex(RunStop, "accounting_incomplete"):
            calls.call("candidate", {"missing_usage": True})
        self.assertFalse(calls.accounting_complete)


class PipelineTests(unittest.TestCase):
    def test_experiment_only_starts_24_sol_servers_and_freezes_without_judging(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            instances = []
            problem = {"theorem": "A", "assumptions": [], "domain": "algebra",
                       "proof_text": "A", "explicit_subgoals": []}
            assignments = [{"task_id": "a", "case_id": "c", "method": "original"},
                           {"task_id": "b", "case_id": "c", "method": "direct_rewrite"}]
            manifest = {"budget": {"max_model_attempts_per_task": 24, "max_total_tokens_per_task": 80000,
                                   "max_wall_seconds_per_task": 30}}

            def factory(folder, role, lane):
                self.assertEqual(role, "experiment")
                server = PersistentServer(folder, role, lane,
                    command=[sys.executable, str(ROOT / "tests/fixtures/fake_codex_app_server.py")])
                instances.append(server)
                return server

            with patch("harness.workflow_v2.scheduler.validate_bundle", return_value=(manifest, {"c": problem}, assignments)), \
                 patch("harness.workflow_v2.scheduler.aggregate", return_value={"evidence": "offline_fixture"}):
                scheduler = Scheduler(path, server_factory=factory, mode="experiment_only")
                result = scheduler.run()
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["expected_servers"], 24)
            self.assertEqual(result["runtime_completed"], 2)
            self.assertEqual(result["judge_completed"], 0)
            self.assertEqual(result["judge_stage"], "deferred")
            self.assertEqual(len(instances), 24)
            self.assertFalse((path / "judge").exists())
            self.assertFalse((path / "private_judge_mapping.json").exists())
            self.assertEqual(set(read(path / "candidate_freeze.json")), {"a", "b"})
            self.assertEqual(read(path / "scheduler/judge_handoff.json")["pending_task_ids"], ["a", "b"])
            self.assertFalse(any(e["event"] == "judge_started" for e in scheduler.events))
            with self.assertRaisesRegex(ContractError, "deferred"):
                scheduler.judge_assignment(assignments[0], instances[0])

    def test_missing_fixed_model_stops_before_generation(self):
        instances = []

        class MissingModelServer:
            def __init__(self, folder, role, lane):
                self.role, self.lane = role, lane
                self.model = "gpt-6-astra" if role == "validation" else "gpt-5.6-sol"
                self.abort = threading.Event()
                self.healthy = True
                self.call_count = self.contexts_released = 0
                self.process = None
                self.starts = 0
                instances.append(self)

            def start(self):
                self.starts += 1
                self.process = self
                self.pid = self.lane + 100

            def poll(self):
                return 0 if self.abort.is_set() else None

            def check_ready(self):
                return {"model": self.model, "catalog_available": self.role == "experiment",
                        "context_unload_verified": True}

            def close(self):
                self.abort.set()

            def __call__(self, **kwargs):
                raise AssertionError("unavailable model gate must prevent every generation call")

        with tempfile.TemporaryDirectory() as temp, \
             patch("harness.workflow_v2.scheduler.validate_bundle", return_value=({}, {}, [])):
            result = Scheduler(temp, server_factory=MissingModelServer).run()
            self.assertEqual(result["status"], "failed")
            self.assertIn("gpt-6-astra", result["stop_reason"])
            self.assertFalse((Path(temp) / "runtime").exists())
        self.assertEqual(len(instances), 48)
        self.assertTrue(all(s.starts == 1 and s.call_count == 0 for s in instances))

    def test_24_pairs_stream_frozen_outputs_before_all_generation_finishes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            judged = threading.Event()
            instances = []
            problem = {"theorem": "A", "assumptions": [], "domain": "algebra",
                       "proof_text": "A", "explicit_subgoals": []}
            assignments = [{"task_id": "a", "case_id": "c", "method": "original"},
                           {"task_id": "b", "case_id": "c", "method": "direct_rewrite"}]
            manifest = {"budget": {"max_model_attempts_per_task": 24, "max_total_tokens_per_task": 80000,
                        "max_wall_seconds_per_task": 30},
                        "external_judge_budget": {"max_calls": 1, "max_tokens": 24000, "max_seconds": 30}}

            class Fake:
                def __init__(self, folder, role, lane):
                    self.role, self.lane = role, lane
                    self.model = "gpt-6-astra" if role == "validation" else "gpt-5.6-sol"
                    self.effort = "high" if role == "validation" else "xhigh"
                    self.abort = threading.Event()
                    self.healthy = True
                    self.call_count = self.contexts_released = 0
                    self.starts = 0
                    self.process = None
                    instances.append(self)

                def start(self):
                    self.starts += 1
                    self.pid = 1000 + len(instances) + self.lane
                    self.process = self

                def poll(self):
                    return 0 if self.abort.is_set() else None

                def check_ready(self):
                    return {"model": self.model, "catalog_available": True, "context_unload_verified": True}

                def close(self):
                    self.abort.set()

                def __call__(self, **kwargs):
                    self.call_count += 1
                    self.contexts_released += 1
                    p = kwargs["input_payload"]
                    if self.role == "validation":
                        self.assert_blind(p)
                        value = {"sample_id": p["sample_id"], "input_digest": digest(p), "candidate_kind": "proof",
                            "validity": "valid", "rigor": "pass", "problem_preservation": "pass", "goal_coverage": "pass",
                            "counterexample_validity": "not_applicable", "findings": [], "unresolved_obligations": [],
                            "evidence_scope": "model_only", "reason": "fixture"}
                        judged.set()
                    else:
                        if not judged.wait(10):
                            raise RuntimeError("judge waited for global freeze: pipeline deadlock")
                        value = {"kind": "proof", "text": "A", "reason": "fixture"}
                    return {"requested_model": self.model, "model": None, "output_text": json.dumps(value),
                        "events": [{"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2}}],
                        "return_code": 0, "context_released": True, "codex_thread_id": str(self.call_count)}

                @staticmethod
                def assert_blind(p):
                    assert set(p) == {"sample_id", "theorem", "assumptions", "domain", "explicit_subgoals", "candidate_text"}

            with patch("harness.workflow_v2.scheduler.validate_bundle", return_value=(manifest, {"c": problem}, assignments)), \
                 patch("harness.workflow_v2.scheduler.aggregate", return_value={"evidence": "offline_fixture"}):
                scheduler = Scheduler(path, server_factory=Fake)
                result = scheduler.run()
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["runtime_completed"], 2)
            self.assertEqual(result["judge_scored"], 2)
            self.assertEqual(len(instances), 48)
            self.assertTrue(all(s.starts == 1 for s in instances))
            self.assertEqual(LANES, 24)
            events = scheduler.events
            first_judge = next(i for i, e in enumerate(events) if e["event"] == "judge_started")
            last_freeze = max(i for i, e in enumerate(events) if e["event"] == "candidate_frozen")
            self.assertLess(first_judge, last_freeze)
            for e in events:
                if e["event"] == "judge_started":
                    frozen = read(path / "candidate_freezes" / (e["task_id"] + ".json"))
                    self.assertEqual(e["lane"], frozen["lane"])


if __name__ == "__main__":
    unittest.main()
