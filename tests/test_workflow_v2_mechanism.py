"""Semantic controls for the constructed local-edit study."""
import importlib.util
from pathlib import Path
import tempfile
import json
import os
import threading
import unittest
from unittest.mock import patch

from harness.workflow_v2.contracts import ROOT, SCHEMAS, digest, read
from harness.workflow_v2.runtime import Calls
from tests.test_workflow_v2 import Scripted, evaluation, AUDIT, judge

spec = importlib.util.spec_from_file_location("mechanism_study", ROOT / "scripts/run_workflow_v2_mechanism.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class MechanismTests(unittest.TestCase):
    def test_paired_pool_finishes_all_tasks_and_releases_every_context(self):
        instances=[]
        test_case=self
        class FakeServer:
            def __init__(self,folder,role,lane):
                test_case.assertTrue(folder.is_absolute(), "Codex sqlite_home requires an absolute path")
                self.role,self.lane=role,lane
                self.abort=threading.Event()
                self.call_count=self.contexts_released=0
                self.process=None
                self.closed=False
                instances.append(self)
            def start(self):
                self.process=self
                self.pid=100+self.lane+(24 if self.role=="validation" else 0)
            def poll(self): return 0 if self.closed else None
            def check_ready(self):
                self.contexts_released+=1
                return {"catalog_available":True,"context_unload_verified":True}
            def close(self): self.closed=True
            def __call__(self,**kwargs):
                self.call_count+=1
                self.contexts_released+=1
                payload=kwargs["input_payload"]
                schema=kwargs["output_schema"]
                if schema==SCHEMAS["evaluate"]: value=evaluation()(payload)
                elif schema==SCHEMAS["audit"]: value=AUDIT
                elif schema==SCHEMAS["judge"]: value=judge(payload)
                else: raise AssertionError("unexpected phase")
                return {"requested_model":kwargs["model"],"model":None,"output_text":json.dumps(value),
                    "return_code":0,"latency_seconds":0.01,
                    "events":[{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":20}}]}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            m,c,a=study.prepare(path)
            relative=Path(os.path.relpath(path,Path.cwd()))
            with patch.object(study,"PersistentServer",FakeServer): result=study.run(relative,m,c,a)
            self.assertEqual(result,"completed")
            final=read(path/"final.json")
            self.assertEqual((final["runtime_completed"],final["judge_completed"]),(18,18))
            self.assertEqual(len(final["slots"]),48)
            self.assertFalse(any(s["alive"] for s in final["slots"]))
            self.assertEqual(sum(s.call_count for s in instances),84)
            self.assertTrue(all(s.contexts_released==s.call_count+1 for s in instances))
            self.assertEqual(len(read(path/"aggregate.json")["summaries"]),3)

    def test_identical_patch_and_text_with_different_invalidated_sets(self):
        for case in study.fixtures():
            values = [study.edited_state(case,s) for s in study.STRATEGIES]
            self.assertEqual(len({digest(patch) for state,patch in values}),1)
            self.assertEqual(len({state.render() for state,patch in values}),1)
            pending = [{n["node_id"] for n in state.nodes if n["status"]=="pending"} for state,p in values]
            self.assertEqual(pending,[{"n1","n2"},{"n1","n2","n3","n4","n5"},{"n1"}])
            stale = values[-1][0].find("n2")
            self.assertNotEqual(stale["evaluation"]["context_fingerprint"],values[-1][0].fingerprint(stale))

    def test_exact_oracle_has_balanced_positive_negative_controls(self):
        cases=study.fixtures()
        self.assertEqual(sum(c["oracle"]["submitted_text_strictly_valid_after_edit"] for c in cases),3)
        for c in cases:
            self.assertTrue(c["oracle"]["initial_all_nodes_locally_valid"])
            false_ids=[n for n,v in c["oracle"]["after_edit_valid"].items() if not v]
            self.assertEqual(false_ids,[] if c["control"]=="semantics_preserving" else ["n2"])

    def test_pre_audit_measurement_exposes_stale_success_without_repair(self):
        for case in study.fixtures():
            for strategy in study.STRATEGIES:
                state,_=study.edited_state(case,strategy)
                pending=[n["node_id"] for n in state.nodes if n["status"]=="pending"]
                oracle=case["oracle"]["after_edit_valid"]
                checks=[("evaluate",evaluation("closed" if oracle[n] else "invalid")) for n in pending]
                audit=dict(AUDIT)
                if not all(oracle.values()): audit["rigor"]="fail"
                adapter=Scripted(checks+[("audit",audit)])
                with tempfile.TemporaryDirectory() as temp:
                    calls=Calls(Path(temp),fixture_adapter=adapter)
                    r=study.generate(case,{"case_id":case["case_id"],"strategy":strategy},calls)
                self.assertIsNone(r["failure"])
                expected=all(oracle.values()) or strategy=="retain_stale_for_experiment"
                self.assertEqual(r["local_success_before_audit"],expected)
                self.assertEqual(r["success_after_audit"],all(oracle.values()))
                self.assertEqual(r["evaluated_nodes"],pending)
                self.assertEqual(r["candidate_text"],state.render())
                for phase,kwargs in adapter.inputs:
                    self.assertNotIn("oracle",kwargs["input_payload"])
                    self.assertNotIn("strategy",kwargs["input_payload"])
                    self.assertNotIn("case_id",kwargs["input_payload"])


if __name__=="__main__": unittest.main()
