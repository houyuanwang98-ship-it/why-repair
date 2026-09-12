from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

from harness.workflow_v2.app_server import PersistentServer
from harness.workflow_v2.contracts import ROOT, ContractError, read, write_once
from harness.workflow_v2.engine import Workflow
from harness.workflow_v2.experiment import prepare, validate_bundle, evidence_files, file_digest, aggregate
from harness.workflow_v2.judging import prepare_judging, validate_frozen_source, validate_judge_bundle
from harness.workflow_v2.runtime import Calls
from harness.workflow_v2.scheduler import Scheduler


class DeferredJudgingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "generation"
        self.output = Path(self.temp.name) / "judging"
        prepare(self.source)
        _, cases, assignments = validate_bundle(self.source)
        self.assignments = assignments
        freezes = {}
        for i, a in enumerate(assignments):
            folder = self.source / "runtime" / a["task_id"]
            write_once(folder / "identity.json", a)
            calls = Calls(folder, fixture_adapter=lambda **kw: None)
            outcome = Workflow(cases[a["case_id"]], calls).run("original")
            write_once(folder / "result.json", {"assignment": a, "outcome": outcome, "evidence_files": evidence_files(folder)})
            freezes[a["task_id"]] = file_digest(folder / "result.json")
            write_once(self.source / "candidate_freezes" / (a["task_id"] + ".json"),
                       {"task_id": a["task_id"], "lane": i % 24, "result_sha256": freezes[a["task_id"]]})
        write_once(self.source / "candidate_freeze.json", freezes)
        write_once(self.source / "scheduler/final.json", {"runtime_completed": len(assignments),
                   "status": "completed", "slots": []})
        write_once(self.source / "scheduler/judge_handoff.json", {"pending_task_ids": list(freezes),
                   "candidate_freeze_sha256": file_digest(self.source / "candidate_freeze.json")})

    def test_historical_source_uses_its_archive_not_the_new_judge_code_identity(self):
        before = file_digest(self.source / "manifest.json")
        with patch("harness.workflow_v2.experiment.implementation_digest", return_value="new-review-version"):
            with self.assertRaisesRegex(ContractError, "implementation drift"):
                validate_bundle(self.source)
            validate_frozen_source(self.source)
        prepare_judging(self.source, self.output)
        manifest, _, tasks = validate_judge_bundle(self.output)
        self.assertEqual(tasks, self.assignments)
        self.assertEqual(manifest["models"]["validation"]["requested_model"], "gpt-6-astra")
        self.assertEqual(before, file_digest(self.source / "manifest.json"))
        self.assertFalse((self.output / "runtime").exists())

    def test_tampered_frozen_output_and_call_evidence_are_rejected(self):
        prepare_judging(self.source, self.output)
        task = self.assignments[0]["task_id"]
        identity = self.source / "runtime" / task / "identity.json"
        identity.write_text("{}")
        with self.assertRaisesRegex(ContractError, "call evidence changed"):
            validate_judge_bundle(self.output)

    def test_changed_archive_and_overlapping_output_are_rejected(self):
        with self.assertRaisesRegex(ContractError, "separate bundle"):
            prepare_judging(self.source, self.source / "judge-batch")
        prepare_judging(self.source, self.output)
        with (self.source / "implementation_snapshot.zip").open("ab") as f:
            f.write(b"unexpected archive mutation")
        with self.assertRaisesRegex(ContractError, "anchors changed"):
            validate_judge_bundle(self.output)

    def test_judge_only_scores_all_candidates_on_24_servers_without_generation(self):
        prepare_judging(self.source, self.output)
        before = {str(f.relative_to(self.source)): file_digest(f) for f in self.source.rglob("*") if f.is_file()}
        servers = []

        def factory(folder, role, lane):
            self.assertEqual(role, "validation")
            server = PersistentServer(folder, role, lane, command=[sys.executable,
                str(ROOT / "tests/fixtures/fake_codex_app_server.py"), "--with-validator"])
            servers.append(server)
            return server

        scheduler = Scheduler(self.output, server_factory=factory, mode="judge_only")
        result = scheduler.run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["judge_scored"], 72)
        self.assertEqual(result["new_experiment_model_calls"], 0)
        self.assertEqual(result["inherited_runtime_results"], 72)
        self.assertEqual(len(servers), 24)
        self.assertFalse((self.output / "runtime").exists())
        after = {str(f.relative_to(self.source)): file_digest(f) for f in self.source.rglob("*") if f.is_file()}
        self.assertEqual(before, after)
        for event in scheduler.events:
            if event["event"] == "judge_started":
                self.assertEqual(event["lane"], read(self.source / "candidate_freezes" / (event["task_id"] + ".json"))["lane"])
        groups = aggregate(self.output)["methods"]
        self.assertTrue(all(g["counts"]["strict_accepted_texts"] == 12 for g in groups.values()))


if __name__ == "__main__":
    unittest.main()
