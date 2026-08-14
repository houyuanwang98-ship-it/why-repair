import json
import unittest
from pathlib import Path

from harness.controller import DualAgentController, InvalidTransitionError, StaleVersionError
from harness.contracts import ContractError, validate_contract


def ref(node_id, version=1):
    return {"proof_id": "p1", "node_id": node_id, "version": version}


def node_record(node_id, claim, depends_on=(), state="pending_evaluation", verdict=None):
    return {
        "schema_version": "0.3",
        "node": {
            "schema_version": "0.3", "proof_id": "p1", "node_id": node_id,
            "version": 1, "order_key": node_id * 1000,
            "claim": claim, "self_contained_claim": claim,
            "node_type": "conclusion", "source_span": {"start": node_id * 10, "end": node_id * 10 + 5},
            "source_span_source": "original",
            "depends_on": list(depends_on),
        },
        "lifecycle_state": state, "current_verdict": verdict,
        "created_by": "original", "supersedes": None,
    }


def evaluation(node_id, verdict, dependencies, evaluation_id="eval-1", error_type=None, target_version=1):
    value = {
        "schema_version": "0.3", "evaluation_id": evaluation_id, "target": ref(node_id, target_version),
        "verdict": verdict, "error_type": error_type, "reason": "fixture result",
        "dependency_versions": {str(i): 1 for i in dependencies}, "evaluator_id": "fixture-evaluator",
    }
    return value


def patch(target_version=1):
    return {
        "schema_version": "0.3", "patch_id": "patch-1", "error_certificate_id": "err-1",
        "target": ref(2, target_version), "operation": "replace",
        "replacement_nodes": [{
            "node_id": 2, "order_key": 2000, "claim": "n^2 = 4k^2.",
            "self_contained_claim": "n^2 = 4k^2.", "node_type": "calculation",
            "depends_on": [ref(1)],
        }],
        "target_dependencies_after": [ref(1)], "used_dependencies": [ref(1)],
        "rationale": "Correct the expansion.", "changes_problem": False,
    }


def review(accepted=True):
    return {
        "schema_version": "0.3", "review_id": "review-1", "patch_id": "patch-1",
        "target": ref(2), "accepted": accepted,
        "verdict": "accepted" if accepted else "unsupported",
        "reason": "fixture review", "reviewer_id": "fixture-evaluator",
        **({} if accepted else {"rejection_code": "mathematical_error"}),
    }


def submit_registered_patch(controller, proposal):
    controller.submit_patch(proposal)


def record_repair_evaluation(controller, node_id=2, dependencies=(1,), *, target_version=1):
    target = ref(node_id, target_version)
    target_record = controller.node_version(target)
    certificate = {
        "schema_version": "0.3", "certificate_id": "err-1",
        "target": target,
        "premises": target_record["node"]["depends_on"],
        "error_type": "algebraic_invalidity", "failed_inference": "fixture failure",
        "evidence": ["fixture evidence"],
        "repair_constraints": {
            "allowed_operations": ["replace", "insert_before"],
            "max_new_nodes": 3,
            "preserve_theorem": True, "preserve_assumptions": True,
        },
    }
    controller.record_error_certificate(certificate)
    value = evaluation(
        node_id, "unsupported", list(dependencies), error_type="algebraic_invalidity",
        target_version=target_version,
    )
    value["error_certificate_id"] = "err-1"
    controller.record_evaluation(value)


def insertion_patch():
    inserted_ref = {"proof_id": "p1", "node_id": "bridge-1", "version": 1}
    return {
        "schema_version": "0.3", "patch_id": "patch-1", "error_certificate_id": "err-1",
        "target": ref(2), "operation": "insert_before",
        "replacement_nodes": [{
            "node_id": "bridge-1", "order_key": 1500,
            "claim": "From n=2k, n^2=4k^2.",
            "self_contained_claim": "From n=2k, n^2=4k^2.",
            "node_type": "calculation", "depends_on": [ref(1)],
        }],
        "target_dependencies_after": [inserted_ref],
        "used_dependencies": [ref(1)], "rationale": "Insert the missing bridge.",
        "changes_problem": False,
    }


def ambiguity_analysis(outcome="requires_clarification", meaning_relation="distinct"):
    return {
        "schema_version": "0.3", "analysis_id": "amb-1", "target": ref(2),
        "ambiguous_span": "it is zero", "ambiguity_type": "unclear_reference",
        "declared_scope": "reasonable antecedents in the local obligation",
        "coverage_status": "exhaustive_within_declared_scope",
        "meaning_relation": meaning_relation, "dependency_versions": {"1": 1},
        "interpretations": [
            {"interpretation_id": "i1", "normalized_claim": "a=0", "plausibility": "reasonable", "verdict": "accepted", "reason": "the inference works"},
            {"interpretation_id": "i2", "normalized_claim": "x-y=0", "plausibility": "reasonable", "verdict": "unsupported", "reason": "the inference does not follow"},
        ],
        "outcome": outcome, "evaluator_id": "fixture-evaluator",
    }


class DualAgentControllerTest(unittest.TestCase):
    def controller_with_three_nodes(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "n=2k", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "n^2=2k^2", [ref(1)]))
        controller.register_node(node_record(3, "n^2 is even", [ref(2)], state="active", verdict="accepted"))
        controller.validate_graph("p1")
        return controller

    def test_accepted_patch_creates_version_and_invalidates_descendant(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        new_ref = controller.review_patch(review(True))
        self.assertEqual(ref(2, 2), new_ref)
        self.assertEqual("pending_evaluation", controller.lifecycle(ref(2, 2)))
        self.assertEqual("stale", controller.lifecycle(ref(3)))
        self.assertIsNone(controller.node_version(ref(3))["current_verdict"])
        self.assertEqual(1, len(controller.invalidation_records))
        invalidation = controller.invalidation_records[0]
        self.assertEqual(ref(2), invalidation["trigger_old"])
        self.assertEqual(ref(2, 2), invalidation["trigger_new"])
        self.assertEqual([ref(3)], invalidation["invalidated"])
        controller.transition(new_ref, "evaluating", reason="evaluate exact replacement version")
        controller.record_evaluation(evaluation(2, "accepted", [1], evaluation_id="eval-v2", target_version=2))
        self.assertEqual("active", controller.lifecycle(new_ref))

    def test_invalidation_record_is_topological_complete_isolated_and_read_only(self):
        controller = self.controller_with_three_nodes()
        controller.register_node(node_record(4, "final", [ref(3)], state="active", verdict="accepted"))
        controller.register_node(node_record(5, "independent", [ref(1)], state="active", verdict="accepted"))
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        controller.review_patch(review(True))
        record = controller.invalidation_records[0]
        self.assertEqual([ref(3), ref(4)], record["invalidated"])
        self.assertEqual("stale", controller.lifecycle(ref(3)))
        self.assertEqual("stale", controller.lifecycle(ref(4)))
        self.assertEqual("active", controller.lifecycle(ref(5)))
        record["invalidated"].append(ref(5))
        self.assertEqual([ref(3), ref(4)], controller.invalidation_records[0]["invalidated"])

    def test_invalid_parent_blocks_descendants_without_math_verdict(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        descendant = controller.node_version(ref(3))
        self.assertEqual("blocked_by_invalid_dependency", descendant["lifecycle_state"])
        self.assertIsNone(descendant["current_verdict"])

    def test_patch_against_superseded_version_is_rejected(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        controller.review_patch(review(True))
        with self.assertRaises(StaleVersionError):
            controller.submit_patch({**patch(), "patch_id": "late-patch"})

    def test_patch_with_stale_dependency_version_is_rejected(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        proposal = patch()
        proposal["used_dependencies"] = [ref(1, 2)]
        with self.assertRaises(StaleVersionError):
            submit_registered_patch(controller, proposal)

    def test_initial_node_version_must_start_at_one(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        record = node_record(1, "P")
        record["node"]["version"] = 2
        with self.assertRaisesRegex(ValueError, "initial node version must be 1"):
            controller.register_node(record)

    def test_new_node_version_cannot_skip_versions(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "P", state="active", verdict="accepted"))
        record = node_record(1, "P revised", state="active", verdict="accepted")
        record["node"]["version"] = 3
        record["supersedes"] = ref(1)
        record["created_by"] = "repair_generator"
        with self.assertRaisesRegex(ValueError, "increment the current version by one"):
            controller.register_node(record)

    def test_invalid_replace_graph_rolls_back_new_version(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        proposal = patch()
        proposal["target_dependencies_after"] = [ref(3)]
        proposal["replacement_nodes"][0]["depends_on"] = [ref(3)]
        proposal["used_dependencies"] = [ref(3)]
        submit_registered_patch(controller, proposal)
        controller.begin_patch_review(proposal["patch_id"])
        with self.assertRaisesRegex(ValueError, "earlier order_key"):
            controller.review_patch(review(True))
        self.assertEqual(ref(2), controller.current_ref("p1", 2))
        self.assertEqual("pending_recheck", controller.lifecycle(ref(2)))
        with self.assertRaises(KeyError):
            controller.node_version(ref(2, 2))
        self.assertEqual([], controller.invalidation_records)

    def test_rejected_patch_returns_to_pending_repair(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        self.assertIsNone(controller.review_patch(review(False)))
        self.assertEqual("pending_repair", controller.lifecycle(ref(2)))

    def test_repair_generator_cannot_review_own_patch(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        own_review = review(True)
        own_review["reviewer_id"] = "repair_generator"
        with self.assertRaisesRegex(ValueError, "configured evaluator"):
            controller.review_patch(own_review)
        self.assertEqual("pending_recheck", controller.lifecycle(ref(2)))

    def test_dependency_blocking_is_lifecycle_only(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "invalid parent", state="stale", verdict=None))
        controller.register_node(node_record(2, "child", [ref(1)]))
        controller.mark_blocked_by_invalid_dependency(ref(2), reason="node 1 is stale")
        record = controller.node_version(ref(2))
        self.assertEqual("blocked_by_invalid_dependency", record["lifecycle_state"])
        self.assertIsNone(record["current_verdict"])

    def test_non_active_descendant_invalidation_is_recorded(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "n=2k", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "n^2=2k^2", [ref(1)]))
        controller.register_node(node_record(3, "n^2 is even", [ref(2)]))
        controller.validate_graph("p1")
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        controller.begin_patch_review("patch-1")
        controller.review_patch(review(True))
        transitions = [
            event for event in controller.events
            if event.get("event") == "lifecycle_transition"
            and event.get("target") == ref(3)
            and event.get("to") == "stale"
        ]
        self.assertEqual(1, len(transitions))

    def test_invalid_transition_is_rejected(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "P"))
        with self.assertRaises(InvalidTransitionError):
            controller.transition(ref(1), "active", reason="skip evaluator")

    def test_evaluation_rejects_active_but_superseded_dependency(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "old premise", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "dependent claim", [ref(1)]))
        replacement = node_record(1, "new premise")
        replacement["node"]["version"] = 2
        replacement["supersedes"] = ref(1)
        controller.register_node(replacement)
        with self.assertRaisesRegex(InvalidTransitionError, "active and current"):
            controller.transition(ref(2), "evaluating", reason="stale dependency")
        ready = controller.proof_snapshot("p1")["ready_for_evaluation"]
        self.assertNotIn(ref(2), ready)
        self.assertIn(ref(1, 2), ready)

    def test_blocked_descendant_is_not_released_by_active_superseded_dependency(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "old premise", state="active", verdict="accepted"))
        controller.register_node(node_record(
            2, "dependent claim", [ref(1)],
            state="blocked_by_invalid_dependency", verdict=None,
        ))
        replacement = node_record(1, "new premise")
        replacement["node"]["version"] = 2
        replacement["supersedes"] = ref(1)
        controller.register_node(replacement)
        controller.transition(ref(1, 2), "evaluating", reason="evaluate replacement")
        controller.record_evaluation(evaluation(
            1, "accepted", [], evaluation_id="replacement-eval", target_version=2
        ))
        self.assertEqual("blocked_by_invalid_dependency", controller.lifecycle(ref(2)))

    def test_repair_queue_fails_closed_until_certificate_is_bound(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1]))
        queue = controller.repair_queue(["p1"])
        self.assertEqual(1, len(queue))
        self.assertEqual("awaiting_error_certificate", queue[0]["status"])
        self.assertIsNone(queue[0]["error_certificate"])
        controller.assert_consistent("p1")

    def test_evaluation_with_wrong_dependency_version_is_stale(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        value = evaluation(2, "unsupported", [1], error_type="algebraic_invalidity")
        value["dependency_versions"] = {"1": 2}
        with self.assertRaises(StaleVersionError):
            controller.record_evaluation(value)

    def test_evaluation_cannot_reference_unregistered_error_certificate(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        value = evaluation(2, "unsupported", [1], error_type="algebraic_invalidity")
        value["error_certificate_id"] = "missing-error-certificate"
        with self.assertRaisesRegex(ValueError, "registered error certificate"):
            controller.record_evaluation(value)

    def test_counterexample_verdict_requires_registered_certificate(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        value = evaluation(2, "counterexample_found", [1], error_type="false_local_claim")
        value["counterexample_certificate_id"] = "missing-counterexample"
        with self.assertRaisesRegex(ValueError, "registered certificate"):
            controller.record_evaluation(value)

    def test_graph_with_missing_dependency_version_is_rejected(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "P", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "Q", [ref(1, 2)]))
        with self.assertRaisesRegex(ValueError, "missing dependency version"):
            controller.validate_graph("p1")

    def test_graph_rejects_dependency_with_later_order_key(self):
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "P", [ref(2)]))
        controller.register_node(node_record(2, "Q", state="active", verdict="accepted"))
        with self.assertRaisesRegex(ValueError, "earlier order_key"):
            controller.validate_graph("p1")

    def test_insert_before_creates_pending_node_and_requeues_target(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        record_repair_evaluation(controller)
        proposal = insertion_patch()
        submit_registered_patch(controller, proposal)
        controller.begin_patch_review(proposal["patch_id"])
        result = controller.review_patch(review(True))
        inserted_ref = result["inserted_refs"][0]
        target_ref = result["target_ref"]
        self.assertEqual("pending_evaluation", controller.lifecycle(inserted_ref))
        self.assertEqual("pending_evaluation", controller.lifecycle(target_ref))
        self.assertEqual("stale", controller.lifecycle(ref(3)))
        with self.assertRaisesRegex(InvalidTransitionError, "dependency is active"):
            controller.transition(target_ref, "evaluating", reason="too early")
        controller.transition(inserted_ref, "evaluating", reason="evaluate inserted bridge")
        controller.record_evaluation(evaluation("bridge-1", "accepted", [1], evaluation_id="eval-bridge"))
        self.assertEqual("active", controller.lifecycle(inserted_ref))
        self.assertEqual("pending_evaluation", controller.lifecycle(target_ref))
        controller.transition(target_ref, "evaluating", reason="re-evaluate original target")
        controller.record_evaluation(evaluation(2, "accepted", ["bridge-1"], evaluation_id="eval-target", target_version=2))
        self.assertEqual("active", controller.lifecycle(target_ref))

    def test_ambiguous_verdict_runs_interpretation_branches_then_requests_rewrite(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "ambiguous", [1]))
        self.assertEqual("resolving_ambiguity", controller.lifecycle(ref(2)))
        controller.record_ambiguity_analysis(ambiguity_analysis())
        self.assertEqual("pending_repair", controller.lifecycle(ref(2)))
        self.assertEqual("ambiguous", controller.node_version(ref(2))["current_verdict"])
        queue = controller.repair_queue(["p1"])
        self.assertEqual(1, len(queue))
        self.assertEqual("ready", queue[0]["status"])
        self.assertEqual(["replace"], queue[0]["executable_operations"])
        self.assertEqual("interpretation_ambiguity", queue[0]["error_certificate"]["error_type"])
        self.assertTrue(any(
            event.get("event") == "evaluation_recorded"
            and event.get("source") == "ambiguity_analysis"
            for event in controller.events
        ))

        proposal = patch()
        proposal["error_certificate_id"] = queue[0]["error_certificate"]["certificate_id"]
        proposal["rationale"] = "Rewrite the ambiguous reference explicitly."
        controller.submit_patch(proposal)
        controller.begin_patch_review(proposal["patch_id"])
        new_ref = controller.review_patch(review(True))
        self.assertEqual(ref(2, 2), new_ref)

    def test_non_executable_certificate_is_not_reported_ready(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        certificate = {
            "schema_version": "0.3", "certificate_id": "needs-assumption",
            "target": ref(2), "premises": [ref(1)],
            "error_type": "missing_assumption", "failed_inference": "c may be zero",
            "evidence": ["division requires c != 0"],
            "repair_constraints": {
                "allowed_operations": ["add_assumption"], "max_new_nodes": 1,
                "preserve_theorem": False, "preserve_assumptions": False,
            },
        }
        controller.record_error_certificate(certificate)
        value = evaluation(2, "unsupported", [1], error_type="missing_assumption")
        value["error_certificate_id"] = certificate["certificate_id"]
        controller.record_evaluation(value)
        queue = controller.repair_queue(["p1"])
        self.assertEqual("requires_problem_revision", queue[0]["status"])
        self.assertEqual([], queue[0]["executable_operations"])

        proposal = patch()
        proposal.update({
            "error_certificate_id": certificate["certificate_id"],
            "operation": "add_assumption", "replacement_nodes": [],
            "changes_problem": True,
        })
        with self.assertRaisesRegex(ContractError, "not executable"):
            controller.submit_patch(proposal)
        self.assertEqual("pending_repair", controller.lifecycle(ref(2)))

    def test_equivalent_exhaustive_interpretations_can_be_robustly_accepted(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "ambiguous", [1]))
        analysis = ambiguity_analysis("robustly_accepted", "equivalent")
        for branch in analysis["interpretations"]:
            branch["verdict"] = "accepted"
            branch["normalized_claim"] = "a=0"
        controller.record_ambiguity_analysis(analysis)
        self.assertEqual("active", controller.lifecycle(ref(2)))
        self.assertEqual("accepted", controller.node_version(ref(2))["current_verdict"])


class M1FixtureReplayTest(unittest.TestCase):
    fixture_dir = Path(__file__).parents[1] / "data" / "fixtures" / "m1"

    def load_fixture(self, name):
        return json.loads((self.fixture_dir / name).read_text(encoding="utf-8"))

    def test_illegal_transition_fixture_fails_closed(self):
        fixture = self.load_fixture("illegal_transition.json")
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "P"))
        with self.assertRaises(InvalidTransitionError):
            controller.transition(fixture["target"], fixture["attempted_to"], reason="fixture illegal jump")

    def test_missing_patch_review_fixture_cannot_apply_patch(self):
        fixture = self.load_fixture("missing_patch_review.json")
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "n=2k", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "bad", [ref(1)]))
        controller.transition(ref(2), "evaluating", reason="fixture")
        record_repair_evaluation(controller)
        submit_registered_patch(controller, patch())
        self.assertEqual(fixture["expected_current"], controller.current_ref("p1", 2))
        self.assertEqual(fixture["expected_lifecycle"], controller.lifecycle(ref(2)))
        with self.assertRaises(KeyError):
            controller.node_version(ref(2, 2))

    def test_rollback_failure_fixture_is_atomic(self):
        fixture = self.load_fixture("rollback_failure.json")
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "n=2k", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "bad", [ref(1)]))
        controller.register_node(node_record(3, "goal", [ref(2)], state="active", verdict="accepted"))
        controller.transition(ref(2), "evaluating", reason="fixture")
        record_repair_evaluation(controller)
        proposal = patch()
        proposal["target_dependencies_after"] = [fixture["illegal_dependency"]]
        proposal["replacement_nodes"][0]["depends_on"] = [fixture["illegal_dependency"]]
        proposal["used_dependencies"] = [fixture["illegal_dependency"]]
        submit_registered_patch(controller, proposal)
        controller.begin_patch_review(proposal["patch_id"])
        event_count = len(controller.events)
        with self.assertRaisesRegex(ValueError, fixture["expected_error_contains"]):
            controller.review_patch(review(True))
        self.assertEqual(fixture["expected_current"], controller.current_ref("p1", 2))
        self.assertEqual(event_count, len(controller.events))
        self.assertEqual([], controller.invalidation_records)

    def test_missing_version_fixture_is_rejected(self):
        fixture = self.load_fixture("missing_version.json")
        record = node_record(1, "P")
        record["node"]["depends_on"] = [fixture["invalid_ref"]]
        with self.assertRaises(ContractError):
            validate_contract(fixture["kind"], record["node"])

    def replay_accepted_repair(self):
        fixture = self.load_fixture("accepted_repair.json")
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        for item in fixture["initial_nodes"]:
            dependencies = [ref(node_id) for node_id in item["depends_on"]]
            controller.register_node(node_record(
                item["node_id"], item["claim"], dependencies,
                state=item["state"], verdict=item["verdict"],
            ))
        controller.validate_graph("p1")
        spec = fixture["evaluation"]
        controller.transition(ref(spec["target_node_id"]), "evaluating", reason="fixture replay")
        record_repair_evaluation(
            controller, spec["target_node_id"], spec["dependencies"]
        )
        patch_spec = fixture["patch"]
        proposal = patch(patch_spec["target_version"])
        proposal["replacement_nodes"][0]["claim"] = patch_spec["replacement"]
        proposal["replacement_nodes"][0]["self_contained_claim"] = patch_spec["replacement"]
        submit_registered_patch(controller, proposal)
        controller.begin_patch_review(proposal["patch_id"])
        new_ref = controller.review_patch(review(fixture["review"]["accepted"]))
        controller.transition(new_ref, "evaluating", reason="fixture replacement recheck")
        controller.record_evaluation(evaluation(2, "accepted", [1], evaluation_id="fixture-v2", target_version=2))
        return fixture, controller, new_ref

    def test_accepted_repair_fixture_replays_completely(self):
        fixture, controller, new_ref = self.replay_accepted_repair()
        expected = fixture["expected"]
        self.assertEqual(expected["current_node_2"], new_ref)
        self.assertEqual(expected["node_2_lifecycle"], controller.lifecycle(new_ref))
        self.assertEqual(expected["node_3_lifecycle"], controller.lifecycle(ref(3)))

    def test_rejected_stale_patch_fixture_replays_completely(self):
        fixture = self.load_fixture("rejected_stale_patch.json")
        _, controller, _ = self.replay_accepted_repair()
        late_spec = fixture["late_patch"]
        late_patch = patch(late_spec["target_version"])
        late_patch["patch_id"] = late_spec["patch_id"]
        late_patch["replacement_nodes"][0]["claim"] = late_spec["replacement"]
        late_patch["replacement_nodes"][0]["self_contained_claim"] = late_spec["replacement"]
        self.assertEqual("StaleVersionError", fixture["expected_error"])
        with self.assertRaises(StaleVersionError):
            controller.submit_patch(late_patch)

    def test_ambiguity_branching_fixture_replays_completely(self):
        fixture = self.load_fixture("ambiguity_branching.json")
        controller = DualAgentController(evaluator_ids={"fixture-evaluator", "eval"})
        controller.register_node(node_record(1, "a=0", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "It is zero, so the sides are equal.", [ref(1)]))
        controller.transition(fixture["target"], "evaluating", reason="fixture replay")
        controller.record_evaluation(evaluation(2, fixture["initial_verdict"], [1]))
        controller.record_ambiguity_analysis(fixture["analysis"])
        record = controller.node_version(fixture["target"])
        self.assertEqual(fixture["expected"]["lifecycle_state"], record["lifecycle_state"])
        self.assertEqual(fixture["expected"]["current_verdict"], record["current_verdict"])

    def test_insert_bridge_fixture_replays_completely(self):
        fixture = self.load_fixture("insert_bridge_and_reevaluate.json")
        controller = DualAgentControllerTest().controller_with_three_nodes()
        controller.transition(fixture["target"], "evaluating", reason="fixture start")
        record_repair_evaluation(controller)
        proposal = insertion_patch()
        submit_registered_patch(controller, proposal)
        controller.begin_patch_review(proposal["patch_id"])
        result = controller.review_patch(review(True))
        inserted_ref, target_ref = result["inserted_refs"][0], result["target_ref"]
        expected = fixture["expected_after_patch"]
        self.assertEqual(expected["inserted_lifecycle"], controller.lifecycle(inserted_ref))
        self.assertEqual(expected["target_version"], target_ref["version"])
        self.assertEqual(expected["target_lifecycle"], controller.lifecycle(target_ref))
        self.assertEqual(expected["descendant_lifecycle"], controller.lifecycle(ref(3)))
        controller.transition(inserted_ref, "evaluating", reason="fixture bridge check")
        controller.record_evaluation(evaluation("bridge-1", "accepted", [1], evaluation_id="fixture-bridge"))
        controller.transition(target_ref, "evaluating", reason="fixture target recheck")
        controller.record_evaluation(evaluation(2, "accepted", ["bridge-1"], evaluation_id="fixture-target", target_version=2))
        expected = fixture["expected_after_recheck"]
        self.assertEqual(expected["inserted_lifecycle"], controller.lifecycle(inserted_ref))
        self.assertEqual(expected["target_lifecycle"], controller.lifecycle(target_ref))


if __name__ == "__main__":
    unittest.main()
