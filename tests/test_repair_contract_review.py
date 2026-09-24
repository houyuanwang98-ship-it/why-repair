import copy
import unittest

from harness.iterative_localization import IterativeRepairSession, IterativeLocalizationError
from harness.local_inference_v2 import ref
from harness.repair_contract import build_contract, RepairContractError
from harness.repair_contract_review import review_request, validate_review, reviewed_generator_input


def node(i, claim, parents=()):
    return {"proof_id": "review", "node_id": i, "version": 1, "order_key": i,
            "claim": claim, "self_contained_claim": claim, "node_type": "calculation",
            "depends_on": [{"proof_id": "review", "node_id": p, "version": 1} for p in parents]}


def fixture(request):
    sources = {s["source_id"]: s["digest"] for s in request["input"]["sources"]}
    return {"schema_version": "repair-contract-review-v1", "input_digest": request["input_digest"],
            "reviewer_id": "person-a", "checks": [
                {"check_id": c["check_id"], "status": "accepted",
                 "reason": "Disclosed fixture judgment; not real mathematical review.",
                 "source_refs": [{"source_id": s, "digest": sources[s]} for s in c["required_sources"]]}
                for c in request["input"]["checks"]]}


class ContractReviewTest(unittest.TestCase):
    def setUp(self):
        self.session = IterativeRepairSession(proof_id="review", theorem="4 == 4", assumptions=[],
            domain="reals", nodes=[node(1, "1 == 1"), node(2, "2 == 3", [1]),
                                   node(3, "4 == 4", [2]), node(4, "5 == 5", [2])])
        self.snapshot = self.session.snapshot()
        self.contract = build_contract(self.snapshot, [ref(self.snapshot["nodes"][1])])
        self.request = review_request(self.contract, self.snapshot)
        self.response = fixture(self.request)

    def validate(self, response=None):
        return validate_review(self.response if response is None else response, self.contract,
                               self.snapshot, evaluator_ids={"person-a"}, generator_id="person-b")

    def test_all_consumers_and_upstream_have_checks(self):
        self.assertEqual(6, len(self.response["checks"]))
        self.assertEqual("accepted", self.validate())

    def test_revision_or_unknown_blocks_release(self):
        for status in ("needs_revision", "undetermined"):
            self.response["checks"][-1]["status"] = status
            self.assertEqual(status, self.validate())
            self.session.evaluate()
            with self.assertRaises(RepairContractError):
                reviewed_generator_input(self.session, self.contract, self.response)

    def test_missing_duplicate_extra_checks_rejected(self):
        for rows in (self.response["checks"][:-1], self.response["checks"] + self.response["checks"][:1],
                     self.response["checks"][:-1] + self.response["checks"][:1]):
            r = copy.deepcopy(self.response)
            r["checks"] = rows
            with self.assertRaises(RepairContractError):
                self.validate(r)

    def test_forged_source_and_digest_rejected(self):
        for field, value in (("source_id", "invented"), ("digest", "sha256:" + "0" * 64)):
            r = copy.deepcopy(self.response)
            r["checks"][0]["source_refs"][0][field] = value
            with self.assertRaises(RepairContractError):
                self.validate(r)

    def test_no_citations_no_reason_or_invented_status(self):
        for field, value in (("source_refs", []), ("reason", "  "), ("status", "valid")):
            r = copy.deepcopy(self.response)
            r["checks"][0][field] = value
            with self.assertRaises(RepairContractError):
                self.validate(r)

    def test_untrusted_and_generator_identity_rejected(self):
        for reviewer in ("person-b", "unknown", None):
            self.response["reviewer_id"] = reviewer
            with self.assertRaises(RepairContractError):
                self.validate()

    def test_stale_request_rejected(self):
        self.response["input_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(RepairContractError):
            self.validate()

    def test_accepted_review_cannot_replace_localization(self):
        with self.assertRaises(IterativeLocalizationError):
            reviewed_generator_input(self.session, self.contract, self.response)

    def test_confirmed_target_releases_only_output_obligations(self):
        self.session.evaluate()
        before = self.session.snapshot()
        data = reviewed_generator_input(self.session, self.contract, self.response)
        self.assertEqual([1], [n["node_id"] for n in data["premise_nodes"]])
        self.assertEqual(2, len(data["repair_contract"]["downstream_targets_only"]))
        self.assertEqual(before, self.session.snapshot())
        self.assertFalse(self.contract["repair_authorized"])

    def test_other_target_or_expanded_region_not_authorized(self):
        self.session.evaluate()
        for ids in ((0,), (1, 2)):
            contract = build_contract(self.snapshot, [ref(self.snapshot["nodes"][i]) for i in ids])
            response = fixture(review_request(contract, self.snapshot))
            with self.assertRaises(RepairContractError):
                reviewed_generator_input(self.session, contract, response)

    def test_unresolved_prefix_still_blocks(self):
        session = IterativeRepairSession(proof_id="review", theorem="4 == 4", assumptions=[], domain="reals",
            nodes=[node(1, "uncertain assertion"), node(2, "2 == 3")])
        session.evaluate()
        snap = session.snapshot()
        contract = build_contract(snap, [ref(snap["nodes"][1])])
        response = fixture(review_request(contract, snap))
        with self.assertRaises(IterativeLocalizationError):
            reviewed_generator_input(session, contract, response)

    def test_review_has_no_interface_rewrite_field(self):
        self.response["weakened_targets"] = []
        with self.assertRaises(RepairContractError):
            self.validate()

    def test_every_semantic_obligation_can_block(self):
        self.session.evaluate()
        for i in range(len(self.response["checks"])):
            response = copy.deepcopy(self.response)
            response["checks"][i]["status"] = "needs_revision"
            with self.subTest(check=response["checks"][i]["check_id"]), self.assertRaises(RepairContractError):
                reviewed_generator_input(self.session, self.contract, response)

    def test_changed_current_state_rejects_previous_review(self):
        from harness.m5_person_a_review import canonical_digest
        snap = copy.deepcopy(self.snapshot)
        snap["nodes"][-1]["claim"] = "different retained branch"
        snap["proof_digest"] = canonical_digest({k: snap[k] for k in ("proof", "nodes", "revision")})
        with self.assertRaises(RepairContractError):
            validate_review(self.response, self.contract, snap,
                            evaluator_ids={"person-a"}, generator_id="person-b")

    def test_schema(self):
        from jsonschema import Draft202012Validator
        validator = Draft202012Validator(self.request["response_schema"])
        validator.check_schema(self.request["response_schema"])
        validator.validate(self.response)
        self.response["checks"][0]["reason"] = " "
        self.assertFalse(validator.is_valid(self.response))


if __name__ == "__main__":
    unittest.main()
