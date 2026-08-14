import hashlib
import json
import unittest
from pathlib import Path

from harness.contracts import ContractError
from harness.controller import StaleVersionError
from harness.m4_verifier import CounterexampleAuditLog, TheoremCounterexampleRegistry, UndeterminedExpression, evaluate_exact, run_counterexample_cases, verify_audit_records, verify_counterexample


def certificate(scope="local_claim"):
    global_scope = scope == "global_theorem"
    target_statement = "sqrt(a^2)=a"
    return {
        "schema_version": "0.3", "certificate_id": "cex-1",
        "target": None if global_scope else {"proof_id": "p", "node_id": "n", "version": 1},
        "theorem_ref": {"proof_id": "p", "theorem_version": 1, "theorem_digest": "sha256:" + hashlib.sha256(target_statement.encode()).hexdigest()} if global_scope else None,
        "scope": scope, "structure": "rational_numbers", "assignment": {"a": -1},
        "premise_checks": [{"statement": "a is real", "holds": True, "evidence": "-1 is real"}],
        "checked_premise_refs": [], "global_assumption_digest": "sha256:context",
        "target_check": {"statement": target_statement, "holds": False, "evidence": "1 != -1"},
        "checker": "person_a_manual_exact",
    }


class M4PersonBTest(unittest.TestCase):
    def test_exact_safe_subset(self):
        self.assertTrue(evaluate_exact("sqrt(a ** 2) != a", {"a": -1}))
        self.assertTrue(evaluate_exact("1 / 10 + 2 / 10 == 3 / 10", {}))
        self.assertTrue(evaluate_exact("(a + b) % 2 == 0", {"a": 1, "b": 1}))
        self.assertTrue(evaluate_exact("is_integer(a) and is_real(a)", {"a": -1}))
        self.assertFalse(evaluate_exact("is_integer(a)", {"a": 0.5}))
        self.assertTrue(evaluate_exact("is_prime(p)", {"p": 2}))
        self.assertFalse(evaluate_exact("is_prime(p)", {"p": 9}))

    def test_verifies_and_hash_chains_without_trusting_prose(self):
        log = CounterexampleAuditLog()
        first = verify_counterexample(certificate(), premise_expressions=["a == -1"],
            target_expression="sqrt(a ** 2) == a", audit_log=log)
        second = verify_counterexample({**certificate(), "certificate_id": "cex-2"},
            premise_expressions=["a == -1"], target_expression="sqrt(a ** 2) == a", audit_log=log)
        self.assertEqual("verified", first["status"])
        self.assertEqual(first["record_digest"], second["previous_digest"])
        self.assertTrue(log.verify_chain())
        self.assertTrue(verify_audit_records(log.records))
        self.assertIn("certificate_digest", first)
        self.assertEqual("a is real", first["premise_bindings"][0]["statement"])
        self.assertEqual("sqrt(a ** 2) == a", first["target_binding"]["expression"])
        exported = log.records
        exported[0]["status"] = "failed"
        self.assertFalse(verify_audit_records(exported))
        forged = log.records
        forged[0]["status"] = "verified"
        forged[0]["target_binding"]["holds"] = True
        self.assertFalse(verify_audit_records(forged))
        self.assertEqual("verified", log.records[0]["status"])

    def test_false_premise_fails_and_unsupported_syntax_is_undetermined(self):
        failed = verify_counterexample(certificate(), premise_expressions=["a > 0"], target_expression="a == 1")
        unknown = verify_counterexample(certificate(), premise_expressions=["is_rational(a)"], target_expression="a == 1")
        self.assertEqual("failed", failed["status"])
        self.assertEqual("undetermined", unknown["status"])
        self.assertIsNone(unknown["premise_bindings"][0]["holds"])

    def test_requires_complete_premise_expression_coverage(self):
        with self.assertRaises(ContractError):
            verify_counterexample(certificate(), premise_expressions=[], target_expression="a == 1")
        with self.assertRaises(ContractError):
            verify_counterexample(certificate(), premise_expressions="a", target_expression="a == 1")
        with self.assertRaises(ContractError):
            verify_counterexample(certificate(), premise_expressions=["a == -1"], target_expression="a == 1", verifier_id=" ")

    def test_resource_bounds_fail_closed(self):
        with self.assertRaises(UndeterminedExpression):
            evaluate_exact(" + ".join(["a"] * 200), {"a": 1})
        with self.assertRaises(UndeterminedExpression):
            evaluate_exact("a == 1", {"not a name": 1})
        invalid = certificate()
        invalid["assignment"] = {"a": float("nan")}
        with self.assertRaisesRegex(ContractError, "portable JSON"):
            verify_counterexample(invalid, premise_expressions=["a == a"], target_expression="a == 1")
        with self.assertRaises(UndeterminedExpression):
            evaluate_exact("a ** 64", {"a": 2 ** 100})
        with self.assertRaises(UndeterminedExpression):
            evaluate_exact("(a == 1) + 1 == 2", {"a": 1})
        with self.assertRaises(UndeterminedExpression):
            evaluate_exact("is_prime(a)", {"a": 2 ** 40 + 15})

    def test_batch_runner_has_one_valid_chain(self):
        report = run_counterexample_cases([{"certificate": certificate(), "premise_expressions": ["a == -1"], "target_expression": "a == 1"}])
        self.assertTrue(report["chain_valid"])
        self.assertEqual(report["head_digest"], report["records"][0]["record_digest"])

    def test_controller_has_explicit_theorem_level_path(self):
        controller = TheoremCounterexampleRegistry()
        value = certificate("global_theorem")
        controller.register_context(value["theorem_ref"], global_assumption_digest="sha256:context",
            premise_statements=["a is real"], theorem_statement="sqrt(a^2)=a",
            target_statement="sqrt(a^2)=a", structure="rational_numbers")
        controller.record(value)
        self.assertEqual("theorem_counterexample_certificate_recorded", controller.events[-1]["event"])
        with self.assertRaises(ContractError):
            controller.record({**certificate(), "certificate_id": "other"})

    def test_theorem_level_path_rejects_stale_context(self):
        controller = TheoremCounterexampleRegistry()
        value = certificate("global_theorem")
        controller.register_context(value["theorem_ref"], global_assumption_digest="sha256:other",
            premise_statements=["a is real"], theorem_statement="sqrt(a^2)=a",
            target_statement="sqrt(a^2)=a", structure="rational_numbers")
        with self.assertRaises(StaleVersionError):
            controller.record(value)
        duplicate_context = TheoremCounterexampleRegistry()
        with self.assertRaisesRegex(ContractError, "duplicates"):
            duplicate_context.register_context(value["theorem_ref"], global_assumption_digest="sha256:context",
                premise_statements=["P", "P"], theorem_statement="sqrt(a^2)=a",
                target_statement="sqrt(a^2)=a", structure="rational_numbers")
        with self.assertRaisesRegex(ContractError, "requires a theorem registry"):
            verify_counterexample(value, premise_expressions=["a == -1"], target_expression="a == 1")

    def test_replays_both_frozen_person_a_scope_cases(self):
        root = Path(__file__).resolve().parents[1]
        person_a = json.loads((root / "data/fixtures/m4/person_a_gold_scope_cases.json").read_text(encoding="utf-8"))
        person_b = json.loads((root / "data/fixtures/m4/person_b_executable_cases.json").read_text(encoding="utf-8"))
        certificates = {item["source_sample_id"]: item["certificate"] for item in person_a["cases"]}
        cases = [{**item, "certificate": certificates[item["source_sample_id"]]} for item in person_b["cases"]]
        report = run_counterexample_cases(cases)
        self.assertTrue(report["chain_valid"])
        self.assertEqual(["verified", "verified"], [item["status"] for item in report["records"]])

    def test_schema_required_fields_match_runtime_record(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas/m4_person_b_verification_v0_1.schema.json").read_text(encoding="utf-8"))
        record = verify_counterexample(certificate(), premise_expressions=["a == -1"], target_expression="a == 1")
        self.assertEqual(set(schema["required"]), set(record))


if __name__ == "__main__":
    unittest.main()
