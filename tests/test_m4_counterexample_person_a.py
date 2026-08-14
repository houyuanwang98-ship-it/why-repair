import hashlib
import json
import unittest
from pathlib import Path

from harness.contracts import ContractError
from harness.m4_counterexample import expected_error_type, review_counterexample


R1 = {"proof_id": "p1", "node_id": "n1", "version": 1}
R2 = {"proof_id": "p1", "node_id": "n2", "version": 1}
DIGEST = "sha256:assumptions-v1"
STATEMENTS = ["ax=ay"]
VERIFY = {
    "verification_method": "manual_exact",
    "verifier_id": "person_b_fixture",
}
LOCAL_BINDING = {
    "expected_target": R2,
    "expected_theorem_ref": None,
    "expected_target_statement": "x=y",
    "expected_structure": "real_numbers",
    "expected_interpretation_assumptions": [],
}


def local_certificate():
    return {
        "schema_version": "0.3", "certificate_id": "cex-local", "target": R2,
        "theorem_ref": None, "scope": "local_claim", "structure": "real_numbers",
        "assignment": {"a": 0, "x": 1, "y": 2},
        "premise_checks": [{"statement": "ax=ay", "holds": True, "evidence": "0=0"}],
        "checked_premise_refs": [R1], "global_assumption_digest": DIGEST,
        "target_check": {"statement": "x=y", "holds": False, "evidence": "1!=2"},
        "checker": "person_a_manual_exact",
    }


class M4PersonACounterexampleTest(unittest.TestCase):
    def test_scope_has_one_error_type(self):
        self.assertEqual("false_local_claim", expected_error_type("local_claim"))
        self.assertEqual("false_theorem", expected_error_type("global_theorem"))
        with self.assertRaises(ContractError):
            expected_error_type("proof")

    def test_accepts_independently_verified_local_certificate(self):
        result = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="verified", verification_notes="exact substitution checked",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual("accepted", result["decision"])

    def test_accepts_global_theorem_only_with_global_category(self):
        value = local_certificate()
        value.update({
            "certificate_id": "cex-global", "target": None, "scope": "global_theorem",
            "theorem_ref": {"proof_id": "p1", "theorem_version": 1,
                "theorem_digest": "sha256:" + "0" * 64},
            "checked_premise_refs": [],
        })
        result = review_counterexample(
            value, claimed_error_type="false_theorem", expected_premise_refs=[],
            expected_premise_statements=STATEMENTS,
            expected_global_assumption_digest=DIGEST, verification_status="verified",
            verification_notes="theorem assumptions and conclusion checked",
            expected_target=None, expected_theorem_ref=value["theorem_ref"],
            expected_target_statement="x=y", expected_structure="real_numbers",
            expected_interpretation_assumptions=[], **VERIFY,
        )
        self.assertTrue(result["accepted"])

    def test_rejects_scope_category_mismatch(self):
        result = review_counterexample(
            local_certificate(), claimed_error_type="false_theorem",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="verified", verification_notes="checked",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertFalse(result["accepted"])
        self.assertEqual("rejected", result["decision"])

    def test_rejects_incomplete_premise_frontier_and_stale_context(self):
        result = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1, {"proof_id": "p1", "node_id": "n0", "version": 1}],
            expected_premise_statements=STATEMENTS,
            expected_global_assumption_digest="sha256:new",
            verification_status="verified", verification_notes="checked",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("rejected", result["decision"])
        self.assertEqual(2, len(result["reasons"]))

    def test_failed_truth_check_rejects_and_absence_stays_undetermined(self):
        failed = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="failed", verification_notes="target evaluates true",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("rejected", failed["decision"])
        absent = review_counterexample(
            None, claimed_error_type=None, expected_premise_refs=[R1],
            expected_premise_statements=STATEMENTS,
            expected_global_assumption_digest=DIGEST, verification_status="undetermined",
            verification_notes="bounded search exhausted",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("undetermined", absent["decision"])
        self.assertFalse(absent["accepted"])

    def test_malformed_certificate_fails_closed(self):
        value = local_certificate()
        value["target_check"]["holds"] = True
        result = review_counterexample(
            value, claimed_error_type="false_local_claim", expected_premise_refs=[R1],
            expected_premise_statements=STATEMENTS,
            expected_global_assumption_digest=DIGEST, verification_status="verified",
            verification_notes="claimed checked",
            **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("rejected", result["decision"])

    def test_independent_verifier_is_mandatory(self):
        with self.assertRaisesRegex(ContractError, "must differ"):
            review_counterexample(
                local_certificate(), claimed_error_type="false_local_claim",
                expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
                expected_premise_statements=STATEMENTS,
                verification_status="verified", verification_method="manual_exact",
                verification_notes="self checked", verifier_id="person_a", **LOCAL_BINDING,
            )

    def test_frozen_gold_derived_scope_cases_are_accepted(self):
        root = Path(__file__).resolve().parents[1]
        fixture = json.loads(
            (root / "data/fixtures/m4/person_a_gold_scope_cases.json").read_text(encoding="utf-8")
        )
        gold = {
            item["proof_id"]: item
            for item in (
                json.loads(line)
                for line in (root / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl")
                .read_text(encoding="utf-8").splitlines()
            )
        }
        for case in fixture["cases"]:
            source = gold[case["source_sample_id"]]
            theorem_digest = "sha256:" + hashlib.sha256(source["theorem"].encode()).hexdigest()
            assumption_digest = "sha256:" + hashlib.sha256(source["assumptions"][0].encode()).hexdigest()
            self.assertEqual(case["expected_global_assumption_digest"], assumption_digest)
            theorem_ref = case["certificate"]["theorem_ref"]
            if theorem_ref is not None:
                self.assertEqual(theorem_ref["theorem_digest"], theorem_digest)
            result = review_counterexample(
                case["certificate"], claimed_error_type=case["claimed_error_type"],
                expected_premise_refs=case["expected_premise_refs"],
                expected_premise_statements=[
                    item["statement"] for item in case["certificate"]["premise_checks"]
                ],
                expected_global_assumption_digest=case["expected_global_assumption_digest"],
                verification_status="verified", verification_method="manual_exact",
                verification_notes="independent regression replay", verifier_id="person_b_fixture",
                expected_target=case["certificate"]["target"],
                expected_theorem_ref=case["certificate"]["theorem_ref"],
                expected_target_statement=case["certificate"]["target_check"]["statement"],
                expected_structure=case["certificate"]["structure"],
                expected_interpretation_assumptions=case["certificate"].get("interpretation_assumptions", []),
            )
            self.assertTrue(result["accepted"], case["source_sample_id"])

    def test_review_schema_covers_exact_runtime_output(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (root / "schemas/m4_person_a_counterexample_review_v0_2.schema.json")
            .read_text(encoding="utf-8")
        )
        result = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="verified", verification_notes="checked", **VERIFY,
            **LOCAL_BINDING,
        )
        self.assertEqual(set(schema["required"]), set(result))
        replay = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="verified", verification_notes="checked", **VERIFY,
            **LOCAL_BINDING,
        )
        self.assertEqual(result["review_context_digest"], replay["review_context_digest"])
        changed_binding = {**LOCAL_BINDING, "expected_structure": "integers"}
        changed = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1], expected_global_assumption_digest=DIGEST,
            expected_premise_statements=STATEMENTS,
            verification_status="verified", verification_notes="checked", **VERIFY,
            **changed_binding,
        )
        self.assertNotEqual(result["review_context_digest"], changed["review_context_digest"])

    def test_rejects_omitted_reviewed_assumption(self):
        result = review_counterexample(
            local_certificate(), claimed_error_type="false_local_claim",
            expected_premise_refs=[R1],
            expected_premise_statements=["a is real", "ax=ay"],
            expected_global_assumption_digest=DIGEST, verification_status="verified",
            verification_notes="only one premise was checked", **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("rejected", result["decision"])
        self.assertIn("complete reviewed premise statements", result["reasons"][0])

    def test_rejects_target_structure_and_interpretation_binding_mismatch(self):
        value = local_certificate()
        value["target_check"]["statement"] = "x=z"
        value["structure"] = "integers"
        value["interpretation_assumptions"] = ["equality is modulo 2"]
        result = review_counterexample(
            value, claimed_error_type="false_local_claim", expected_premise_refs=[R1],
            expected_premise_statements=STATEMENTS,
            expected_global_assumption_digest=DIGEST, verification_status="verified",
            verification_notes="checked", **VERIFY, **LOCAL_BINDING,
        )
        self.assertEqual("rejected", result["decision"])
        self.assertEqual(3, len(result["reasons"]))


if __name__ == "__main__":
    unittest.main()
