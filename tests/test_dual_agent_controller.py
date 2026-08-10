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
            "version": 1, "claim": claim, "self_contained_claim": claim,
            "node_type": "conclusion", "source_span": {"start": node_id * 10, "end": node_id * 10 + 5},
            "depends_on": list(depends_on),
        },
        "lifecycle_state": state, "current_verdict": verdict,
        "created_by": "original", "supersedes": None,
    }


def evaluation(node_id, verdict, dependencies, evaluation_id="eval-1", error_type=None):
    value = {
        "schema_version": "0.1", "evaluation_id": evaluation_id, "target": ref(node_id),
        "verdict": verdict, "error_type": error_type, "reason": "fixture result",
        "dependency_versions": {str(i): 1 for i in dependencies}, "evaluator_id": "fixture-evaluator",
    }
    return value


def patch(target_version=1):
    return {
        "schema_version": "0.1", "patch_id": "patch-1", "error_certificate_id": "err-1",
        "target": ref(2, target_version), "operation": "replace",
        "replacement_nodes": ["n^2 = 4k^2."], "used_dependencies": [ref(1)],
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
        proposal["replacement_nodes"] = [patch_spec["replacement"]]
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
        late_patch["replacement_nodes"] = [late_spec["replacement"]]
        self.assertEqual("StaleVersionError", fixture["expected_error"])
        with self.assertRaises(StaleVersionError):
            controller.submit_patch(late_patch)


if __name__ == "__main__":
    unittest.main()
