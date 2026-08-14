import hashlib
import json
import unittest
from pathlib import Path

from harness.contracts import ContractError
from harness.controller import StaleVersionError
from harness.m4_controller import M4CounterexampleController


TARGET = {"proof_id": "p", "node_id": "n", "version": 1}


def certificate(scope="local_claim"):
    global_scope = scope == "global_theorem"
    return {"schema_version": "0.3", "certificate_id": "c1",
        "target": None if global_scope else TARGET,
        "theorem_ref": {"proof_id": "p", "theorem_version": 1,
            "theorem_digest": "sha256:" + "0" * 64} if global_scope else None,
        "scope": scope, "structure": "rational_numbers", "assignment": {"a": -1},
        "premise_checks": [{"statement": "a is real", "holds": True, "evidence": "-1 is real"}],
        "checked_premise_refs": [], "global_assumption_digest": "sha256:ctx",
        "target_check": {"statement": "a=1", "holds": False, "evidence": "-1 != 1"},
        "checker": "person_a"}


class M4ControllerTest(unittest.TestCase):
    def local(self):
        ctl = M4CounterexampleController()
        ctl.register_context("local", scope="local_claim", target=TARGET,
            premise_refs=[], premise_statements=["a is real"],
            approved_premise_expressions=["is_real(a)"],
            approved_target_expression="a == 1",
            global_assumption_digest="sha256:ctx")
        return ctl

    def test_complete_a_b_a_handoff_accepts(self):
        ctl = self.local()
        result = ctl.process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])
        self.assertEqual("person_b", result["review"]["verifier_id"])
        self.assertTrue(ctl.snapshot()["audit_chain_valid"])

    def test_failed_and_undetermined_never_accept(self):
        false_witness = certificate()
        false_witness["assignment"] = {"a": 1}
        failed = self.local().process("local", false_witness, claimed_error_type="false_local_claim",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual("rejected", failed["state"])
        undecidable = M4CounterexampleController()
        undecidable.register_context("local", scope="local_claim", target=TARGET,
            premise_refs=[], premise_statements=["a is real"],
            approved_premise_expressions=["is_rational(a)"],
            approved_target_expression="a == 1", global_assumption_digest="sha256:ctx")
        unknown = undecidable.process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["is_rational(a)"], target_expression="a == 1")
        self.assertEqual("undetermined", unknown["state"])

    def test_global_path_is_part_of_same_controller(self):
        ctl = M4CounterexampleController()
        value = certificate("global_theorem")
        ctl.register_context("global", scope="global_theorem", theorem_ref=value["theorem_ref"],
            premise_refs=[], premise_statements=["a is real"],
            approved_premise_expressions=["is_real(a)"], approved_target_expression="a == 1",
            global_assumption_digest="sha256:ctx")
        result = ctl.process("global", value, claimed_error_type="false_theorem",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])

    def test_global_failure_rolls_back_registry_and_audit(self):
        ctl = M4CounterexampleController()
        value = certificate("global_theorem")
        ctl.register_context("global", scope="global_theorem", theorem_ref=value["theorem_ref"],
            premise_refs=[], premise_statements=["a is real"],
            approved_premise_expressions=["is_real(a)"], approved_target_expression="a == 1",
            global_assumption_digest="sha256:ctx")
        with self.assertRaises(ContractError):
            ctl.process("global", value, claimed_error_type="false_theorem",
                premise_expressions=[], target_expression="a == 1")
        self.assertEqual([], ctl.audit_records)
        result = ctl.process("global", value, claimed_error_type="false_theorem",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])

    def test_identity_duplicate_and_stale_handoffs_fail_closed(self):
        with self.assertRaises(ContractError):
            M4CounterexampleController(reviewer_id="same", verifier_id="same")
        ctl = self.local()
        ctl.process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        with self.assertRaises(ContractError):
            ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                premise_expressions=["is_real(a)"], target_expression="a == 1")
        stale = certificate(); stale["global_assumption_digest"] = "sha256:old"
        ctl2 = self.local()
        with self.assertRaises(StaleVersionError):
            ctl2.process("local", stale, claimed_error_type="false_local_claim",
                premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual([], ctl2.audit_records)

    def test_rejects_unapproved_semantic_surrogates(self):
        ctl = self.local()
        with self.assertRaisesRegex(ContractError, "frozen approval"):
            ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                premise_expressions=["a == -1"], target_expression="a == 1")
        with self.assertRaisesRegex(ContractError, "frozen approval"):
            ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                premise_expressions=["is_real(a)"], target_expression="a == 2")
        self.assertEqual([], ctl.audit_records)

    def test_person_a_rechecks_every_frozen_valid_gold_counterexample(self):
        root = Path(__file__).resolve().parents[1]
        review = json.loads(
            (root / "data/fixtures/m4/person_a_full_gold_review.json").read_text(encoding="utf-8")
        )
        gold = {
            row["proof_id"]: row
            for row in (
                json.loads(line)
                for line in (root / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl")
                .read_text(encoding="utf-8").splitlines()
            )
            if row["gold_counterexample_status"] == "valid"
        }
        self.assertEqual(set(gold), {case["source_sample_id"] for case in review["cases"]})
        accepted = []
        for case in review["cases"]:
            row = gold[case["source_sample_id"]]
            old = row["gold_counterexample"]
            theorem_digest = "sha256:" + hashlib.sha256(row["theorem"].encode()).hexdigest()
            assumption_digest = "sha256:" + hashlib.sha256(row["assumptions"][0].encode()).hexdigest()
            theorem_ref = {"proof_id": row["proof_id"], "theorem_version": row["theorem_version"],
                "theorem_digest": theorem_digest}
            value = {
                "schema_version": "0.3", "certificate_id": "m4-full-" + row["proof_id"],
                "target": None, "theorem_ref": theorem_ref, "scope": "global_theorem",
                "structure": row["domain"], "assignment": old["assignments"],
                "premise_checks": [{"statement": row["assumptions"][0], "holds": True,
                    "evidence": old["assumption_checks"][0]["evidence"]}],
                "checked_premise_refs": [], "global_assumption_digest": assumption_digest,
                "target_check": {"statement": row["theorem"], "holds": False,
                    "evidence": old["verification_notes"]},
                "checker": "m4_person_a_full_gold_review",
            }
            ctl = M4CounterexampleController()
            ctl.register_context(row["proof_id"], scope="global_theorem", theorem_ref=theorem_ref,
                premise_refs=[], premise_statements=row["assumptions"],
                approved_premise_expressions=[case["premise_expression"]],
                approved_target_expression=case["target_expression"],
                global_assumption_digest=assumption_digest)
            result = ctl.process(row["proof_id"], value, claimed_error_type="false_theorem",
                premise_expressions=[case["premise_expression"]],
                target_expression=case["target_expression"])
            self.assertEqual("accepted", result["state"], row["proof_id"])
            self.assertTrue(ctl.snapshot()["audit_chain_valid"])
            accepted.append(row["proof_id"])
        self.assertEqual(11, len(accepted))


if __name__ == "__main__":
    unittest.main()
