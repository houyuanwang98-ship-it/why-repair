"""Interrupted-run imports must preserve evidence and never regenerate completed assignments."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from harness.workflow_v2.contracts import ROOT, read, write_once, judge_input, ContractError
from harness.workflow_v2.experiment import prepare, validate_bundle, evidence_files, file_digest
from harness.workflow_v2.runtime import Calls
from harness.workflow_v2.engine import Workflow
from harness.workflow_v2.app_server import PersistentServer
from tests.test_workflow_v2 import judge

spec=importlib.util.spec_from_file_location("continuation_runner",ROOT/"scripts/continue_workflow_v2.py")
continuation=importlib.util.module_from_spec(spec);spec.loader.exec_module(continuation)


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/"source";self.output=Path(self.tmp.name)/"continued"
        prepare(self.source,case_ids=["m2-011"])
        _,cases,self.assignments=validate_bundle(self.source)
        mapping={a["task_id"]:"blind-test-"+a["method"] for a in self.assignments}
        write_once(self.source/"private_judge_mapping.json",mapping)
        (self.source/"console.log").write_text("interrupted fixture\n")
        for a in self.assignments:
            if a["method"]=="direct_rewrite":continue
            folder=self.source/"runtime"/a["task_id"]
            write_once(folder/"identity.json",a)
            calls=Calls(folder,fixture_adapter=lambda **kw:None)
            outcome=Workflow(cases[a["case_id"]],calls).run("original")
            write_once(folder/"result.json",{"assignment":a,"outcome":outcome,"evidence_files":evidence_files(folder)})
            if a["method"] in {"original","self_refine"}:
                jf=self.source/"judge"/mapping[a["task_id"]]
                payload=judge_input(cases[a["case_id"]],outcome["candidate_text"],mapping[a["task_id"]])
                write_once(jf/"result.json",{"status":"scored","judgment":judge(payload),
                    "calls":calls.summary(),"evidence_files":{}})

    def test_imports_only_verified_files_and_rejects_changed_evidence(self):
        p=continuation.prepare_continuation(self.source,self.output)
        self.assertEqual((len(p["runtime_imports"]),len(p["judge_imports"])),(5,2))
        task=next(iter(p["runtime_imports"]))
        (self.source/"runtime"/task/"identity.json").write_text("{}")
        with self.assertRaisesRegex(ContractError,"hash mismatch"):continuation.inspect_source(self.source)

    def test_missing_output_is_not_success_or_zero_cost_evidence(self):
        p=continuation.prepare_continuation(self.source,self.output)
        self.assertEqual((len(p["runtime_to_rerun"]),len(p["judgments_to_run"])),(1,4))
        self.assertIn("unknown never zero-filled",p["interruption_policy"])
        self.assertFalse((self.output/"candidate_freeze.json").exists())

    def test_pipeline_imports_byte_identically_and_runs_only_missing_tasks(self):
        continuation.prepare_continuation(self.source,self.output)
        before={str(f.relative_to(self.source)):file_digest(f) for f in self.source.rglob("*") if f.is_file()}
        instances=[]
        def factory(folder,role,lane):
            s=PersistentServer(folder,role,lane,command=[sys.executable,str(ROOT/"tests/fixtures/fake_codex_app_server.py"),"--with-validator"])
            instances.append(s);return s
        result=continuation.ContinuationScheduler(self.output,self.source,server_factory=factory).run()
        self.assertEqual(result["status"],"completed",result.get("stop_reason"))
        self.assertEqual((result["runtime_completed"],result["judge_completed"]),(6,6))
        self.assertEqual((result["inherited_runtime_results"],result["inherited_judgments"]),(5,2))
        self.assertEqual(result["new_experiment_model_calls"],1)
        self.assertEqual(result["new_judge_model_calls"],4)
        self.assertFalse(any(s["alive"] for s in result["slots"]))
        after={str(f.relative_to(self.source)):file_digest(f) for f in self.source.rglob("*") if f.is_file()}
        self.assertEqual(before,after)
        provenance=read(self.output/"continuation.json")
        for task,sha in provenance["runtime_imports"].items():self.assertEqual(file_digest(self.output/"runtime"/task/"result.json"),sha)
        for task,entry in provenance["judge_imports"].items():
            sample=read(self.output/"private_judge_mapping.json")[task]
            self.assertEqual(sample,entry["sample_id"])
            self.assertEqual(file_digest(self.output/"judge"/sample/"result.json"),entry["sha256"])


if __name__=="__main__":unittest.main()
