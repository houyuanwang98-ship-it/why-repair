import copy
import json
import unittest
from unittest.mock import patch as mock_patch
from pathlib import Path

from harness.m5_repair import M5RepairController, M5RepairError, RepairBudget
from harness.m5_person_a_review import canonical_digest


FIXTURE = Path(__file__).parents[1] / "data" / "fixtures" / "m5" / "person_b_gold_repair.json"


class M5PersonBRepairTest(unittest.TestCase):
    def case(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def controller(self, **kwargs):
        case = self.case()
        return M5RepairController(proof_id=case["proof_id"], nodes=case["nodes"],
                                  error_certificate=case["error_certificate"], **kwargs)

    def review_pair(self, controller, patch, *, accepted=True, reviewer="person-a"):
        context = {"schema_version": "0.1", "context_id": "ctx-" + patch["patch_id"],
                   "proof_id": controller.proof_id, "target": copy.deepcopy(patch["target"]),
                   "theorem": "If n is even, n squared is even.", "global_assumptions": ["n is even"],
                   "domain": "integers", "failed_inference": controller._certificate["failed_inference"],
                   "allowed_evidence": ["certificate:" + controller._certificate["certificate_id"]],
                   "unrelated_branch_digests": {},
                   "error_certificate_digest": canonical_digest(controller._certificate),
                   "patch_digest": canonical_digest(patch)}
        checks = {key: accepted for key in ("mathematically_valid", "resolves_failed_inference",
                  "theorem_preserved", "assumptions_preserved", "domain_preserved",
                  "unrelated_branches_preserved", "no_new_errors", "operationally_minimal")}
        if accepted:
            codes = []
        else:
            # Every failed check has a deterministic rejection code.
            codes = ["mathematical_error", "failed_inference_unresolved", "target_changed",
                     "hidden_assumption", "domain_changed", "unrelated_branch_changed",
                     "new_error_introduced", "not_minimal"]
        if patch["operation"] in {"replace", "insert_before"}:
            edit_ids = [f"{patch['operation']}:{node['node_id']}" for node in patch["replacement_nodes"]]
        else:
            edit_ids = [f"{patch['operation']}:{patch['target']['node_id']}"]
        review = {"schema_version": "0.1", "review_id": "review-" + patch["patch_id"],
                  "context_id": context["context_id"], "reviewer_id": reviewer, "checks": checks,
                  "hidden_assumptions": [], "introduced_errors": [],
                  "deletion_trials": [{"edit_id": edit_id, "removal_breaks_repair": accepted,
                                       "reason": "required" if accepted else "invalid edit"} for edit_id in edit_ids],
                  "evidence_used": context["allowed_evidence"], "accepted": accepted,
                  "rejection_codes": codes, "reason": "accepted" if accepted else "rejected"}
        return context, review

    def revalidation(self, target, *, verdict="accepted", evaluator="person-a", suffix="1"):
        return {"schema_version": "0.1", "evaluation_id": "recheck-" + suffix,
                "evaluator_id": evaluator, "target": copy.deepcopy(target),
                "verdict": verdict, "reason": "independent node recheck"}

    def test_gold_replace_invalidates_full_descendant_closure(self):
        case = self.case(); controller = self.controller()
        controller.submit(case["patch"])
        result = controller.review_and_apply(case["review_context"], case["review"])
        self.assertIsNone(result["stop_reason"])
        self.assertEqual(controller._find_current(2)["version"], 2)
        self.assertEqual([node["node_id"] for node in result["stale"]], [3])
        self.assertEqual([item["target"]["node_id"] for item in result["revalidation_queue"]], [2, 3])
        self.assertEqual(result["revalidation_queue"][1]["status"], "blocked_by_stale_dependency")
        self.assertTrue(any(event["event"] == "cache_cleared" for event in controller.events))
        result = controller.record_revalidation(self.revalidation(result["revalidation_queue"][0]["target"]))
        self.assertEqual(result["revalidation_queue"][1]["target"]["version"], 2)
        result = controller.record_revalidation(self.revalidation(
            result["revalidation_queue"][1]["target"], suffix="2"))
        self.assertEqual(result["stop_reason"], "accepted")
        self.assertEqual(controller.audit_manifest("gold-run")["release"], "m5-person-b-v0.1")

    def test_generator_cannot_accept_own_patch(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        with self.assertRaisesRegex(ValueError, "cannot review"):
            controller.review_and_apply(*self.review_pair(controller, case["patch"], reviewer="person-b"))

    def test_stale_target_and_unknown_dependency_are_rejected(self):
        case = self.case()
        for mutation in ("target", "dependency"):
            controller = self.controller(); patch = copy.deepcopy(case["patch"])
            if mutation == "target": patch["target"]["version"] = 2
            else: patch["used_dependencies"][0]["node_id"] = 99
            with self.subTest(mutation=mutation), self.assertRaises(M5RepairError): controller.submit(patch)

    def test_equivalent_patch_terminates_even_when_id_and_rationale_change(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        controller.review_and_apply(*self.review_pair(controller, case["patch"], accepted=False))
        duplicate = copy.deepcopy(case["patch"]); duplicate["patch_id"] = "another"; duplicate["rationale"] = "different prose"
        with self.assertRaisesRegex(M5RepairError, "equivalent patch"): controller.submit(duplicate)
        self.assertEqual(controller.snapshot()["stop_reason"], "equivalent_patch")

    def test_patch_requires_one_review_and_review_cannot_be_replayed(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        changed = copy.deepcopy(case["patch"]); changed["patch_id"] = "too-soon"
        changed["replacement_nodes"][0]["claim"] += " "
        with self.assertRaisesRegex(M5RepairError, "awaiting review"):
            controller.submit(changed)
        controller.review_and_apply(*self.review_pair(controller, case["patch"], accepted=False))
        with self.assertRaisesRegex(M5RepairError, "no patch awaiting review"):
            controller.review_and_apply(*self.review_pair(controller, case["patch"], accepted=False))

    def test_retries_end_at_max_rounds(self):
        case = self.case(); controller = self.controller(budget=RepairBudget(max_rounds=1))
        controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"], accepted=False))
        self.assertEqual(result["stop_reason"], "max_rounds")

    def test_insert_delete_and_irreparable(self):
        case = self.case()
        insert = copy.deepcopy(case["patch"]); insert.update({"patch_id": "insert", "operation": "insert_before"})
        bridge = {"node_id": "bridge", "order_key": 15, "claim": "(2k)^2=4k^2", "self_contained_claim": "Squaring 2k gives 4k^2.", "node_type": "calculation", "depends_on": insert["used_dependencies"]}
        insert["replacement_nodes"] = [bridge]
        insert["target_dependencies_after"] = [{"proof_id": case["proof_id"], "node_id": "bridge", "version": 1}]
        controller = self.controller(); controller.submit(insert)
        result = controller.review_and_apply(*self.review_pair(controller, insert))
        self.assertIsNotNone(controller._find_current("bridge")); self.assertIsNone(result["stop_reason"])

        delete = copy.deepcopy(case["patch"]); delete.update({"patch_id": "delete", "operation": "delete", "replacement_nodes": [], "target_dependencies_after": [], "used_dependencies": []})
        controller = self.controller(); controller.submit(delete)
        result = controller.review_and_apply(*self.review_pair(controller, delete))
        self.assertIsNone(controller._find_current(2)); self.assertEqual(len(result["stale"]), 1)

        irreparable = copy.deepcopy(case["patch"]); irreparable.update({"patch_id": "stop", "operation": "mark_irreparable", "replacement_nodes": [], "target_dependencies_after": [], "used_dependencies": []})
        controller = self.controller(); controller.submit(irreparable)
        result = controller.review_and_apply(*self.review_pair(controller, irreparable))
        self.assertEqual(result["stop_reason"], "irreparable")

    def test_transaction_rolls_back_dangling_replace(self):
        case = self.case(); controller = self.controller(); before = controller.snapshot()
        patch = copy.deepcopy(case["patch"])
        patch["target_dependencies_after"] = [{"proof_id": case["proof_id"], "node_id": 3, "version": 1}]
        patch["replacement_nodes"][0]["depends_on"] = copy.deepcopy(patch["target_dependencies_after"])
        patch["used_dependencies"] = copy.deepcopy(patch["target_dependencies_after"])
        controller.submit(patch)
        with self.assertRaisesRegex(M5RepairError, "dangling"):
            controller.review_and_apply(*self.review_pair(controller, patch))
        after = controller.snapshot()
        self.assertEqual(after["nodes"], before["nodes"])
        self.assertEqual(after["stale"], before["stale"])

    def test_m4_input_is_accepted_v1_1_and_digest_bound(self):
        accepted = [json.loads((Path(__file__).parents[1] / "data" / "benchmarks" / "m4" /
                                "integrated_acceptance_v1_1.json").read_text(encoding="utf-8"))]
        controller = self.controller(m4_accepted_certificates=accepted)
        self.assertTrue(controller.generator_input()["m4_input_digest"].startswith("sha256:"))
        with self.assertRaisesRegex(M5RepairError, "v1.1 contract"):
            self.controller(m4_accepted_certificates=[{"release": "m4-integrated-v1.0",
                                                       "status": "accepted_by_person_a_and_person_b"}])

    def test_current_graph_has_one_version_and_history_preserves_old_target(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"]))
        current = [node for node in result["nodes"] if node["node_id"] == 2]
        self.assertEqual([node["version"] for node in current], [2])
        self.assertEqual(result["version_history"][0]["version"], 1)
        self.assertEqual(result["version_history"][0]["lifecycle_state"], "superseded")

    def test_patch_review_alone_cannot_claim_success(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"]))
        self.assertIsNone(result["stop_reason"])
        self.assertEqual(result["revalidation_queue"][0]["status"], "pending_evaluation")

    def test_revalidation_is_trusted_topological_and_fail_closed(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"]))
        with self.assertRaisesRegex(M5RepairError, "topological order"):
            controller.record_revalidation(self.revalidation(result["revalidation_queue"][1]["target"]))
        with self.assertRaisesRegex(M5RepairError, "untrusted"):
            controller.record_revalidation(self.revalidation(
                result["revalidation_queue"][0]["target"], evaluator="outsider"))
        result = controller.record_revalidation(self.revalidation(
            result["revalidation_queue"][0]["target"], verdict="rejected"))
        self.assertEqual(result["stop_reason"], "revalidation_failed")

    def test_unaffected_dependency_does_not_deadlock_stale_descendant(self):
        case = self.case()
        case["nodes"].insert(1, {"proof_id": case["proof_id"], "node_id": 4, "version": 1,
            "order_key": 15, "claim": "k is an integer.",
            "self_contained_claim": "The witness k is an integer.",
            "node_type": "premise", "depends_on": []})
        case["nodes"][-1]["depends_on"].append(
            {"proof_id": case["proof_id"], "node_id": 4, "version": 1})
        controller = M5RepairController(proof_id=case["proof_id"], nodes=case["nodes"],
                                        error_certificate=case["error_certificate"])
        controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"]))
        result = controller.record_revalidation(self.revalidation(
            result["revalidation_queue"][0]["target"]))
        self.assertEqual(result["revalidation_queue"][1]["status"], "pending_evaluation")
        self.assertEqual({ref["node_id"] for ref in controller._find_current(3)["depends_on"]}, {2, 4})

    def test_delete_splices_dependencies_and_revalidates_descendant(self):
        case = self.case(); delete = copy.deepcopy(case["patch"])
        delete.update({"patch_id": "delete-redundant", "operation": "delete",
                       "replacement_nodes": [], "target_dependencies_after": [],
                       "used_dependencies": []})
        controller = self.controller(); controller.submit(delete)
        result = controller.review_and_apply(*self.review_pair(controller, delete))
        self.assertEqual(result["revalidation_queue"][0]["status"], "pending_evaluation")
        self.assertEqual(result["revalidation_queue"][0]["target"]["node_id"], 3)
        self.assertEqual([ref["node_id"] for ref in controller._find_current(3)["depends_on"]], [1])
        result = controller.record_revalidation(self.revalidation(
            result["revalidation_queue"][0]["target"]))
        self.assertEqual(result["stop_reason"], "accepted")

    def test_revalidation_exception_rolls_back_atomically(self):
        case = self.case(); controller = self.controller(); controller.submit(case["patch"])
        result = controller.review_and_apply(*self.review_pair(controller, case["patch"]))
        result = controller.record_revalidation(self.revalidation(
            result["revalidation_queue"][0]["target"]))
        before = controller.snapshot()
        final = self.revalidation(result["revalidation_queue"][1]["target"], suffix="2")
        with mock_patch.object(controller, "_assert_final_target_path",
                               side_effect=M5RepairError("forced final gate failure")):
            with self.assertRaisesRegex(M5RepairError, "forced final gate failure"):
                controller.record_revalidation(final)
        self.assertEqual(controller.snapshot(), before)

    def test_generator_context_only_exposes_certificate_operations(self):
        controller = self.controller()
        self.assertEqual(controller.generator_input()["allowed_operations"],
                         ["delete", "insert_before", "mark_irreparable", "replace"])
        case = self.case()
        case["error_certificate"]["repair_constraints"]["allowed_operations"] = ["replace"]
        controller = M5RepairController(proof_id=case["proof_id"], nodes=case["nodes"],
                                        error_certificate=case["error_certificate"])
        self.assertEqual(controller.generator_input()["allowed_operations"], ["mark_irreparable", "replace"])

    def test_model_adapter_success_and_failure_are_audited(self):
        case = self.case(); controller = self.controller()
        proposal = controller.generate(
            lambda context: {"proposal": copy.deepcopy(case["patch"]),
                             "token_usage": {"input": 120, "output": 45}},
            model="fixture-model", prompt_version="m5-person-b-v0.1")
        self.assertEqual(proposal["patch_id"], case["patch"]["patch_id"])
        manifest = controller.audit_manifest("adapter-success")
        self.assertEqual(manifest["metrics"]["model_calls"], 1)
        self.assertEqual(manifest["metrics"]["failed_model_calls"], 0)
        self.assertEqual(manifest["metrics"]["token_usage"], {"input": 120, "output": 45})

        failed = self.controller()
        def broken_adapter(context):
            raise RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            failed.generate(broken_adapter, model="fixture-model",
                            prompt_version="m5-person-b-v0.1")
        failure_manifest = failed.audit_manifest("adapter-failure")
        self.assertEqual(failure_manifest["metrics"]["failed_model_calls"], 1)
        self.assertEqual(failure_manifest["model_invocations"][0]["error_type"], "RuntimeError")
        self.assertEqual(failure_manifest["attempt_fingerprints"], [])

    def test_frozen_certificate_mutation_is_detected(self):
        controller = self.controller()
        controller._certificate["failed_inference"] = "tampered"
        with self.assertRaisesRegex(M5RepairError, "frozen ErrorCertificate"):
            controller.generator_input()


if __name__ == "__main__": unittest.main()
