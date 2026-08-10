import json
import unittest
from pathlib import Path

from harness.controller import DualAgentController, InvalidTransitionError, StaleVersionError


def ref(node_id, version=1):
    return {"proof_id": "p1", "node_id": node_id, "version": version}


def node_record(node_id, claim, depends_on=(), state="pending_evaluation", verdict=None):
    return {
        "schema_version": "0.1",
        "node": {
            "schema_version": "0.1", "proof_id": "p1", "node_id": node_id,
            "version": 1, "order_key": node_id * 1000,
            "claim": claim, "self_contained_claim": claim,
            "node_type": "conclusion", "source_span": {"start": node_id * 10, "end": node_id * 10 + 5},
            "depends_on": list(depends_on),
        },
        "lifecycle_state": state, "current_verdict": verdict,
        "created_by": "original", "supersedes": None,
    }


def evaluation(node_id, verdict, dependencies, evaluation_id="eval-1", error_type=None, target_version=1):
    value = {
        "schema_version": "0.1", "evaluation_id": evaluation_id, "target": ref(node_id, target_version),
        "verdict": verdict, "error_type": error_type, "reason": "fixture result",
        "dependency_versions": {str(i): 1 for i in dependencies}, "evaluator_id": "fixture-evaluator",
    }
    return value


def patch(target_version=1):
    return {
        "schema_version": "0.1", "patch_id": "patch-1", "error_certificate_id": "err-1",
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
        "schema_version": "0.1", "review_id": "review-1", "patch_id": "patch-1",
        "target": ref(2), "accepted": accepted,
        "verdict": "accepted" if accepted else "unsupported",
        "reason": "fixture review", "reviewer_id": "fixture-evaluator",
        **({} if accepted else {"rejection_code": "mathematical_error"}),
    }


def insertion_patch():
    inserted_ref = {"proof_id": "p1", "node_id": "bridge-1", "version": 1}
    return {
        "schema_version": "0.1", "patch_id": "patch-1", "error_certificate_id": "err-1",
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
        "schema_version": "0.1", "analysis_id": "amb-1", "target": ref(2),
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
        controller = DualAgentController()
        controller.register_node(node_record(1, "n=2k", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "n^2=2k^2", [ref(1)]))
        controller.register_node(node_record(3, "n^2 is even", [ref(2)], state="active", verdict="accepted"))
        controller.validate_graph("p1")
        return controller

    def test_accepted_patch_creates_version_and_invalidates_descendant(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        controller.submit_patch(patch())
        controller.begin_patch_review("patch-1")
        new_ref = controller.review_patch(review(True))
        self.assertEqual(ref(2, 2), new_ref)
        self.assertEqual("active", controller.lifecycle(ref(2, 2)))
        self.assertEqual("stale", controller.lifecycle(ref(3)))
        self.assertIsNone(controller.node_version(ref(3))["current_verdict"])

    def test_patch_against_superseded_version_is_rejected(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        controller.submit_patch(patch())
        controller.begin_patch_review("patch-1")
        controller.review_patch(review(True))
        with self.assertRaises(StaleVersionError):
            controller.submit_patch({**patch(), "patch_id": "late-patch"})

    def test_rejected_patch_returns_to_pending_repair(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        controller.submit_patch(patch())
        controller.begin_patch_review("patch-1")
        self.assertIsNone(controller.review_patch(review(False)))
        self.assertEqual("pending_repair", controller.lifecycle(ref(2)))

    def test_invalid_transition_is_rejected(self):
        controller = DualAgentController()
        controller.register_node(node_record(1, "P"))
        with self.assertRaises(InvalidTransitionError):
            controller.transition(ref(1), "active", reason="skip evaluator")

    def test_evaluation_with_wrong_dependency_version_is_stale(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        value = evaluation(2, "unsupported", [1], error_type="algebraic_invalidity")
        value["dependency_versions"] = {"1": 2}
        with self.assertRaises(StaleVersionError):
            controller.record_evaluation(value)

    def test_graph_with_missing_dependency_version_is_rejected(self):
        controller = DualAgentController()
        controller.register_node(node_record(1, "P", state="active", verdict="accepted"))
        controller.register_node(node_record(2, "Q", [ref(1, 2)]))
        with self.assertRaisesRegex(ValueError, "missing dependency version"):
            controller.validate_graph("p1")

    def test_graph_rejects_dependency_with_later_order_key(self):
        controller = DualAgentController()
        controller.register_node(node_record(1, "P", [ref(2)]))
        controller.register_node(node_record(2, "Q", state="active", verdict="accepted"))
        with self.assertRaisesRegex(ValueError, "earlier order_key"):
            controller.validate_graph("p1")

    def test_insert_before_creates_pending_node_and_requeues_target(self):
        controller = self.controller_with_three_nodes()
        controller.transition(ref(2), "evaluating", reason="start")
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        proposal = insertion_patch()
        controller.submit_patch(proposal)
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

    def replay_accepted_repair(self):
        fixture = self.load_fixture("accepted_repair.json")
        controller = DualAgentController()
        for item in fixture["initial_nodes"]:
            dependencies = [ref(node_id) for node_id in item["depends_on"]]
            controller.register_node(node_record(
                item["node_id"], item["claim"], dependencies,
                state=item["state"], verdict=item["verdict"],
            ))
        controller.validate_graph("p1")
        spec = fixture["evaluation"]
        controller.transition(ref(spec["target_node_id"]), "evaluating", reason="fixture replay")
        controller.record_evaluation(evaluation(
            spec["target_node_id"], spec["verdict"], spec["dependencies"],
            error_type=spec["error_type"],
        ))
        patch_spec = fixture["patch"]
        proposal = patch(patch_spec["target_version"])
        proposal["replacement_nodes"][0]["claim"] = patch_spec["replacement"]
        proposal["replacement_nodes"][0]["self_contained_claim"] = patch_spec["replacement"]
        controller.submit_patch(proposal)
        controller.begin_patch_review(proposal["patch_id"])
        new_ref = controller.review_patch(review(fixture["review"]["accepted"]))
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
        controller = DualAgentController()
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
        controller.record_evaluation(evaluation(2, "unsupported", [1], error_type="algebraic_invalidity"))
        proposal = insertion_patch()
        controller.submit_patch(proposal)
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
