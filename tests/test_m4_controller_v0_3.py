import unittest

from harness.contracts import ContractError
from harness.m4_controller_v0_3 import M4CounterexampleControllerV03


TARGET = {"proof_id": "p", "node_id": "n", "version": 1}


def certificate():
    return {
        "schema_version": "0.3", "certificate_id": "c-v03", "target": TARGET,
        "theorem_ref": None, "scope": "local_claim", "structure": "rational_numbers",
        "assignment": {"a": -1},
        "premise_checks": [{"statement": "a is real", "holds": True, "evidence": "-1 is real"}],
        "checked_premise_refs": [], "global_assumption_digest": "sha256:ctx",
        "target_check": {"statement": "a=1", "holds": False, "evidence": "-1 != 1"},
        "checker": "person_a",
    }


class M4ControllerV03Tests(unittest.TestCase):
    def controller(self):
        ctl = M4CounterexampleControllerV03()
        ctl.register_context(
            "local", scope="local_claim", target=TARGET, premise_refs=[],
            premise_statements=["a is real"], approved_premise_expressions=["is_real(a)"],
            approved_target_expression="a == 1", target_statement="a=1",
            structure="rational_numbers", global_assumption_digest="sha256:ctx",
        )
        return ctl

    def test_pending_precedes_verification_and_terminal_state(self):
        ctl = self.controller()
        result = ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                             premise_expressions=["is_real(a)"], target_expression="a == 1")
        events = ctl.events
        pending = next(i for i, event in enumerate(events) if event["event"] == "m4_pending_verification")
        terminal = next(i for i, event in enumerate(events) if event["event"] == "m4_counterexample_processed")
        self.assertLess(pending, terminal)
        self.assertEqual("accepted", result["state"])
        self.assertEqual("m4-counterexample-controller-v0.3", result["profile_version"])
        self.assertIn("timeout_policy", result["verification_environment"])

    def test_failed_candidate_preserves_pending_and_rejection_event(self):
        ctl = self.controller()
        with self.assertRaises(ContractError):
            ctl.process("local", certificate(), claimed_error_type="false_local_claim",
                        premise_expressions=[], target_expression="a == 1")
        self.assertEqual(
            ["m4_context_registered", "m4_pending_verification", "m4_candidate_rejected_before_terminal_result"],
            [event["event"] for event in ctl.events],
        )
        self.assertEqual([], ctl.audit_records)


if __name__ == "__main__":
    unittest.main()
