import unittest

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
            global_assumption_digest="sha256:ctx")
        return ctl

    def test_complete_a_b_a_handoff_accepts(self):
        ctl = self.local()
        result = ctl.process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["a == -1"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])
        self.assertEqual("person_b", result["review"]["verifier_id"])
        self.assertTrue(ctl.snapshot()["audit_chain_valid"])

    def test_failed_and_undetermined_never_accept(self):
        failed = self.local().process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["a > 0"], target_expression="a == 1")
        self.assertEqual("rejected", failed["state"])
        unknown = self.local().process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["is_real(a)"], target_expression="a == 1")
        self.assertEqual("undetermined", unknown["state"])

    def test_global_path_is_part_of_same_controller(self):
        ctl = M4CounterexampleController()
        value = certificate("global_theorem")
        ctl.register_context("global", scope="global_theorem", theorem_ref=value["theorem_ref"],
            premise_refs=[], premise_statements=["a is real"], global_assumption_digest="sha256:ctx")
        result = ctl.process("global", value, claimed_error_type="false_theorem",
            premise_expressions=["a == -1"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])

    def test_global_failure_rolls_back_registry_and_audit(self):
        ctl = M4CounterexampleController()
        value = certificate("global_theorem")
        ctl.register_context("global", scope="global_theorem", theorem_ref=value["theorem_ref"],
            premise_refs=[], premise_statements=["a is real"], global_assumption_digest="sha256:ctx")
        with self.assertRaises(ContractError):
            ctl.process("global", value, claimed_error_type="false_theorem",
                premise_expressions=[], target_expression="a == 1")
        self.assertEqual([], ctl.audit_records)
        result = ctl.process("global", value, claimed_error_type="false_theorem",
            premise_expressions=["a == -1"], target_expression="a == 1")
        self.assertEqual("accepted", result["state"])

    def test_identity_duplicate_and_stale_handoffs_fail_closed(self):
        with self.assertRaises(ContractError):
            M4CounterexampleController(reviewer_id="same", verifier_id="same")
        ctl = self.local()
        ctl.process("local", certificate(), claimed_error_type="false_local_claim",
            premise_expressions=["a == -1"], target_expression="a == 1")
        with self.assertRaises(ContractError):
            ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                premise_expressions=["a == -1"], target_expression="a == 1")
        stale = certificate(); stale["global_assumption_digest"] = "sha256:old"
        ctl2 = self.local()
        with self.assertRaises(StaleVersionError):
            ctl2.process("local", stale, claimed_error_type="false_local_claim",
                premise_expressions=["a == -1"], target_expression="a == 1")
        self.assertEqual([], ctl2.audit_records)


if __name__ == "__main__":
    unittest.main()
