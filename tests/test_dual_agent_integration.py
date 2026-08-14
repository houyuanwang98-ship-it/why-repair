import unittest
from copy import deepcopy
import hashlib
import json

from harness import (
    CheckerIntegrationError,
    ContractError,
    DualAgentController,
    ingest_m3_run,
    ingest_person_a_result,
)


def person_a_result():
    return {
        "id": "integration-proof",
        "domain": "algebra",
        "topic": "parity",
        "theorem": "If n is even, n^2 is even.",
        "assumptions": ["n is an even integer"],
        "proof_graph": [
            {
                "node_id": 1, "claim": "Let n=2k.",
                "self_contained_claim": "There is an integer k with n=2k.",
                "node_type": "introduction", "depends_on": [], "status": "closed",
                "diagnosis": "Definition of evenness.", "repair_action": None,
            },
            {
                "node_id": 2, "claim": "Then n^2=2k^2.",
                "self_contained_claim": "From n=2k, n^2=2k^2.",
                "node_type": "calculation_step", "depends_on": [1],
                "status": "algebraic_invalidity",
                "diagnosis": "Squaring n=2k gives 4k^2, not 2k^2.",
                "operation_check": "(2k)^2=4k^2", "minimal_repair": "Replace by n^2=4k^2.",
                "repair_action": "replace_step", "missing_conditions": [],
            },
            {
                "node_id": 3, "claim": "Therefore n^2 is even.",
                "self_contained_claim": "Therefore n^2 is even.",
                "node_type": "conclusion", "depends_on": [2],
                "status": "downstream_invalid", "diagnosis": "Parent node is invalid.",
                "repair_action": None,
            },
        ],
    }


def replacement_patch(certificate_id):
    dependency = {"proof_id": "integration-proof", "node_id": 1, "version": 1}
    return {
        "schema_version": "0.3", "patch_id": "person-b-patch-1",
        "error_certificate_id": certificate_id,
        "target": {"proof_id": "integration-proof", "node_id": 2, "version": 1},
        "operation": "replace",
        "replacement_nodes": [{
            "node_id": 2, "order_key": 2000, "claim": "Then n^2=4k^2.",
            "self_contained_claim": "From n=2k, n^2=4k^2.",
            "node_type": "calculation", "depends_on": [dependency],
        }],
        "target_dependencies_after": [dependency], "used_dependencies": [dependency],
        "rationale": "Correct the squaring step.", "changes_problem": False,
    }


def person_a_review():
    return {
        "schema_version": "0.3", "review_id": "person-a-review-1",
        "patch_id": "person-b-patch-1",
        "target": {"proof_id": "integration-proof", "node_id": 2, "version": 1},
        "accepted": True, "verdict": "accepted",
        "reason": "The replacement follows by direct calculation.",
        "reviewer_id": "person_a_evaluator",
    }


class PersonAControllerIntegrationTest(unittest.TestCase):
    def test_m3_run_is_digest_bound_and_exposes_controller_handoff(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        second = person_a_result()
        second["id"] = "integration-proof-2"
        summary = ingest_m3_run(
            controller, [person_a_result(), second], run_id="m3-controller-smoke"
        )
        self.assertEqual(2, summary["proof_count"])
        self.assertEqual(6, summary["node_count"])
        self.assertEqual(4, summary["evaluation_count"])
        self.assertEqual(2, summary["error_certificate_count"])
        self.assertTrue(summary["input_digest"].startswith("sha256:"))
        self.assertEqual({"active": 2, "pending_repair": 2,
                          "blocked_by_invalid_dependency": 2}, summary["lifecycle_counts"])
        self.assertEqual([], summary["ready_for_evaluation"])
        self.assertEqual(2, len(summary["repair_queue"]))
        self.assertTrue(all(item["status"] == "ready" for item in summary["repair_queue"]))
        controller.assert_consistent("integration-proof")

    def test_m3_run_rolls_back_every_proof_when_late_result_fails(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        invalid = person_a_result()
        invalid["id"] = "integration-proof-2"
        invalid["proof_graph"][1]["status"] = "unknown_status"
        with self.assertRaisesRegex(CheckerIntegrationError, "unsupported Person A"):
            ingest_m3_run(
                controller, [person_a_result(), invalid], run_id="failed-run"
            )
        with self.assertRaises(KeyError):
            controller.current_ref("integration-proof", 1)
        self.assertEqual([], controller.events)

    def test_m3_run_rejects_duplicate_proof_ids_before_mutation(self):
        controller = DualAgentController(evaluator_ids={"person_a_evaluator"})
        with self.assertRaisesRegex(CheckerIntegrationError, "duplicate proof ids"):
            ingest_m3_run(
                controller,
                [person_a_result(), person_a_result()],
                run_id="duplicate-run",
            )
        self.assertEqual([], controller.events)

    def test_person_a_result_enters_controller_with_separated_states(self):
        controller = DualAgentController(repair_generator_id="person_b_repair_generator", evaluator_ids={"person_a_evaluator"})
        artifacts = ingest_person_a_result(controller, person_a_result())
        self.assertEqual("0.3", artifacts["schema_version"])
        self.assertEqual("active", controller.lifecycle({"proof_id": "integration-proof", "node_id": 1, "version": 1}))
        self.assertEqual("pending_repair", controller.lifecycle({"proof_id": "integration-proof", "node_id": 2, "version": 1}))
        blocked_ref = {"proof_id": "integration-proof", "node_id": 3, "version": 1}
        blocked = controller.node_version(blocked_ref)
        self.assertEqual("blocked_by_invalid_dependency", blocked["lifecycle_state"])
        self.assertIsNone(blocked["current_verdict"])
        self.assertEqual(1, len(artifacts["error_certificates"]))
        self.assertTrue(all(
            node["node"]["source_span_source"] == "synthetic_compatibility"
            for node in artifacts["node_versions"]
        ))

    def test_person_b_patch_is_bound_to_person_a_certificate_and_review(self):
        controller = DualAgentController(repair_generator_id="person_b_repair_generator", evaluator_ids={"person_a_evaluator"})
        artifacts = ingest_person_a_result(controller, person_a_result())
        certificate_id = artifacts["error_certificates"][0]["certificate_id"]
        patch = replacement_patch(certificate_id)
        controller.submit_patch(patch)
        controller.begin_patch_review(patch["patch_id"])
        new_ref = controller.review_patch(person_a_review())
        self.assertEqual(2, new_ref["version"])
        self.assertEqual("pending_evaluation", controller.lifecycle(new_ref))
        self.assertEqual(
            "stale",
            controller.lifecycle({"proof_id": "integration-proof", "node_id": 3, "version": 1}),
        )

    def test_patch_cannot_reference_unknown_certificate(self):
        controller = DualAgentController(repair_generator_id="person_b_repair_generator", evaluator_ids={"person_a_evaluator"})
        ingest_person_a_result(controller, person_a_result())
        with self.assertRaisesRegex(ContractError, "registered error certificate"):
            controller.submit_patch(replacement_patch("unknown-certificate"))

    def test_patch_operation_must_obey_person_a_constraints(self):
        controller = DualAgentController(repair_generator_id="person_b_repair_generator", evaluator_ids={"person_a_evaluator"})
        artifacts = ingest_person_a_result(controller, person_a_result())
        patch = replacement_patch(artifacts["error_certificates"][0]["certificate_id"])
        patch["operation"] = "delete"
        patch["replacement_nodes"] = []
        with self.assertRaisesRegex(ContractError, "not allowed"):
            controller.submit_patch(patch)

    def test_patch_must_use_certificate_bound_to_current_evaluation(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        artifacts = ingest_person_a_result(controller, person_a_result())
        alternate = deepcopy(artifacts["error_certificates"][0])
        alternate["certificate_id"] = "alternate-error-certificate"
        controller.record_error_certificate(alternate)
        patch = replacement_patch(alternate["certificate_id"])
        with self.assertRaisesRegex(ContractError, "bound to the current evaluation"):
            controller.submit_patch(patch)

    def test_failed_ingest_rolls_back_all_controller_state(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        invalid = person_a_result()
        invalid["proof_graph"][1]["status"] = "unknown_status"
        with self.assertRaises(ValueError):
            ingest_person_a_result(controller, invalid)
        with self.assertRaises(KeyError):
            controller.current_ref("integration-proof", 1)
        artifacts = ingest_person_a_result(controller, person_a_result())
        self.assertEqual(3, len(artifacts["node_versions"]))

    def test_legacy_false_label_is_not_preserved_as_verified_error_type(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        legacy = person_a_result()
        legacy["proof_graph"][1]["status"] = "false_theorem"
        artifacts = ingest_person_a_result(controller, legacy)
        certificate = artifacts["error_certificates"][0]
        self.assertEqual("unverified_counterexample", certificate["error_type"])
        evaluation = next(item for item in artifacts["evaluations"] if item["target"]["node_id"] == 2)
        self.assertEqual("unsupported", evaluation["verdict"])
        self.assertEqual("unverified_counterexample", evaluation["error_type"])

    def test_counterexample_must_cover_exact_dependencies_and_assumption_digest(self):
        controller = DualAgentController(
            repair_generator_id="person_b_repair_generator",
            evaluator_ids={"person_a_evaluator"},
        )
        ingest_person_a_result(controller, person_a_result())
        digest_payload = json.dumps(
            ["n is an even integer"], ensure_ascii=False, separators=(",", ":")
        )
        digest = "sha256:" + hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        certificate = {
            "schema_version": "0.3", "certificate_id": "cex-incomplete",
            "target": {"proof_id": "integration-proof", "node_id": 2, "version": 1},
            "theorem_ref": None,
            "scope": "local_claim", "structure": "integers", "assignment": {"k": 1},
            "premise_checks": [{"statement": "n=2k", "holds": True, "evidence": "n=2"}],
            "checked_premise_refs": [], "global_assumption_digest": digest,
            "target_check": {"statement": "n^2=2k^2", "holds": False, "evidence": "4!=2"},
            "checker": "fixture",
        }
        with self.assertRaisesRegex(RuntimeError, "checked premises"):
            controller.record_counterexample_certificate(certificate)



if __name__ == "__main__":
    unittest.main()
