"""Observed quotation and review-scope failures from iteration two."""
from pathlib import Path
import tempfile
import unittest

from harness.workflow_v2.contracts import digest, ContractError
from harness.workflow_v2.controller import ProofState, confirmed_certificate
from harness.workflow_v2.engine import Workflow
from harness.workflow_v2.runtime import Calls, RunStop
from tests.test_workflow_v2 import (PROBLEM, graph, evaluation, diagnosis, replacement,
                                  review, Scripted, AUDIT, CANDIDATE)


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)

    def test_noncontiguous_diagnosis_cannot_bind_and_gets_one_counted_correction(self):
        state=ProofState(PROBLEM,graph());node=state.nodes[0]
        payload={"target":state.ref(node),"target_node":node}
        correct=diagnosis(payload);bad={**correct,"quote":"\"A.\" and \"B.\""}
        before=state.snapshot()
        calls=Calls(self.path,fixture_adapter=Scripted([("diagnose",bad),("diagnose",correct)]),max_output_retries=1)
        result=calls.call("diagnose",payload,validator=lambda v:state.check_diagnosis(node,v))
        self.assertEqual(state.snapshot(),before)
        self.assertEqual((calls.count,calls.tokens,calls.output_corrections),(2,60,1))
        self.assertFalse((self.path/"call-001-diagnose/validated.json").exists())
        self.assertEqual(confirmed_certificate(state,node,result)["quote"],"A.")

    def test_newline_normalization_is_rejected_without_changing_source(self):
        problem={**PROBLEM,"proof_text":"A\nB."}
        g={"ambiguities":[],"nodes":[{"node_id":"n1","text":"A\nB.","claim":"A B.","scope":[],"depends_on":[],"goal_refs":["main"]}]}
        state=ProofState(problem,g);node=state.nodes[0]
        value=diagnosis({"target":state.ref(node),"target_node":node})
        with self.assertRaises(ContractError):state.check_diagnosis(node,{**value,"quote":"A B."})
        state.check_diagnosis(node,value)
        self.assertEqual(state.render(),"A\nB.")

    def closed_state(self):
        state=ProofState(PROBLEM,graph())
        for n in state.nodes:state.record(n,evaluation()({"target":state.ref(n),"target_node":n}),0)
        return state

    def patch_for(self,state):
        n=state.find("n2");p={"target":state.ref(n),"target_node":n}
        cert=confirmed_certificate(state,n,diagnosis(p))
        return replacement({**p,"certificate":cert,"base_state_digest":digest(state.snapshot())}),cert

    def test_review_edits_exclude_invalidated_only_nodes_but_include_rewired_nodes(self):
        state=self.closed_state();p,c=self.patch_for(state)
        draft=state.draft_patch(p,c)
        self.assertEqual(state.direct_edits(draft),["n2"])
        self.assertGreater(draft.find("n4")["version"],state.find("n4")["version"])
        deleted=state.draft_patch({**p,"operation":"delete","nodes":[]},c)
        self.assertEqual(state.direct_edits(deleted),["n2","n4"])

    def test_reviewer_receives_before_after_and_direct_edit_scope(self):
        adapter=Scripted([("graph",graph()),("evaluate",evaluation()),("evaluate",evaluation("gap")),
            ("diagnose",diagnosis),("generate_patch",replacement),("review_patch",review),
            ("evaluate",evaluation()),("evaluate",evaluation()),("evaluate",evaluation()),("audit",AUDIT)])
        result=Workflow(PROBLEM,Calls(self.path,fixture_adapter=adapter)).run("full_system")
        self.assertEqual(result["terminal_status"],"proof_ready",result["stop_reason"])
        request=next(kw["input_payload"] for phase,kw in adapter.inputs if phase=="review_patch")
        self.assertEqual(request["base_proof"],PROBLEM["proof_text"])
        self.assertEqual(request["direct_edit_node_ids"],["n2"])
        self.assertIn("Repaired B.",request["proposed_proof"])

    def test_correction_count_excludes_attempt_blocked_before_invocation(self):
        calls=Calls(self.path,fixture_adapter=Scripted([("candidate",{**CANDIDATE,"reason":""})]),
            max_output_retries=1,max_calls=1)
        with self.assertRaises(RunStop):calls.call("candidate",{})
        self.assertEqual(calls.output_corrections,0)
        self.assertEqual(calls.count,1)


if __name__=="__main__":unittest.main()
