import unittest

from harness.contracts import ContractError, validate_contract


REF1 = {"proof_id": "p1", "node_id": 1, "version": 1}
REF2 = {"proof_id": "p1", "node_id": 2, "version": 1}


class DualAgentContractTest(unittest.TestCase):
    def test_valid_error_certificate(self):
        value = {
            "schema_version": "0.1", "certificate_id": "err-1", "target": REF2,
            "premises": [REF1], "error_type": "algebraic_invalidity",
            "failed_inference": "n^2 = 4k^2 was changed to n^2 = 2k^2.",
            "evidence": ["Substitution n=2k gives n^2=4k^2."],
            "repair_constraints": {
                "allowed_operations": ["replace"], "max_new_nodes": 1,
                "preserve_theorem": True, "preserve_assumptions": True,
            },
        }
        self.assertIs(value, validate_contract("error_certificate", value))

    def test_unknown_error_enum_is_rejected(self):
        value = {
            "schema_version": "0.1", "certificate_id": "err-1", "target": REF2,
            "premises": [REF1], "error_type": "algebraic_mismatch",
            "failed_inference": "bad", "evidence": ["bad"],
            "repair_constraints": {
                "allowed_operations": ["replace"], "max_new_nodes": 1,
                "preserve_theorem": True, "preserve_assumptions": True,
            },
        }
        with self.assertRaises(ContractError):
            validate_contract("error_certificate", value)

    def test_counterexample_requires_true_premises_and_false_target(self):
        base = {
            "schema_version": "0.1", "certificate_id": "cex-1", "target": REF2,
            "scope": "local_claim", "structure": "real numbers",
            "assignment": {"a": 0, "x": 1, "y": 2},
            "premise_checks": [{"statement": "ax=ay", "holds": True, "evidence": "0=0"}],
            "target_check": {"statement": "x=y", "holds": False, "evidence": "1!=2"},
            "checker": "deterministic_fixture",
        }
        validate_contract("counterexample_certificate", base)
        invalid = {**base, "target_check": {"statement": "x=y", "holds": True, "evidence": "wrong"}}
        with self.assertRaises(ContractError):
            validate_contract("counterexample_certificate", invalid)

    def test_add_assumption_must_change_problem(self):
        patch = {
            "schema_version": "0.1", "patch_id": "patch-1", "error_certificate_id": "err-1",
            "target": REF2, "operation": "add_assumption", "replacement_nodes": [],
            "used_dependencies": [REF1], "rationale": "Add a != 0", "changes_problem": False,
        }
        with self.assertRaises(ContractError):
            validate_contract("patch_proposal", patch)

    def test_forward_dependency_is_rejected(self):
        node = {
            "schema_version": "0.1", "proof_id": "p1", "node_id": 1, "version": 1,
            "claim": "P", "self_contained_claim": "P", "node_type": "claim",
            "source_span": {"start": 0, "end": 1}, "depends_on": [REF2],
        }
        with self.assertRaises(ContractError):
            validate_contract("proof_node", node)

    def test_duplicate_dependency_is_rejected(self):
        node = {
            "schema_version": "0.1", "proof_id": "p1", "node_id": 2, "version": 1,
            "claim": "Q", "self_contained_claim": "Q", "node_type": "claim",
            "source_span": {"start": 2, "end": 3}, "depends_on": [REF1, REF1],
        }
        with self.assertRaises(ContractError):
            validate_contract("proof_node", node)

    def test_ambiguity_outcome_cannot_cherry_pick_one_successful_interpretation(self):
        analysis = {
            "schema_version": "0.1", "analysis_id": "amb-1", "target": REF2,
            "ambiguous_span": "it is zero", "ambiguity_type": "unclear_reference",
            "declared_scope": "pronoun antecedents in nodes 1-2",
            "coverage_status": "exhaustive_within_declared_scope",
            "meaning_relation": "distinct", "dependency_versions": {"1": 1},
            "interpretations": [
                {"interpretation_id": "i1", "normalized_claim": "a=0", "plausibility": "reasonable", "verdict": "accepted", "reason": "works"},
                {"interpretation_id": "i2", "normalized_claim": "x-y=0", "plausibility": "reasonable", "verdict": "unsupported", "reason": "does not follow"},
            ],
            "outcome": "robustly_accepted", "evaluator_id": "eval",
        }
        with self.assertRaisesRegex(ContractError, "requires_clarification"):
            validate_contract("ambiguity_analysis", analysis)

    def test_non_exhaustive_equivalent_successes_remain_undetermined(self):
        analysis = {
            "schema_version": "0.1", "analysis_id": "amb-2", "target": REF2,
            "ambiguous_span": "it", "ambiguity_type": "unclear_reference",
            "declared_scope": "best effort antecedents", "coverage_status": "non_exhaustive",
            "meaning_relation": "equivalent", "dependency_versions": {"1": 1},
            "interpretations": [
                {"interpretation_id": "i1", "normalized_claim": "P", "plausibility": "reasonable", "verdict": "accepted", "reason": "works"},
                {"interpretation_id": "i2", "normalized_claim": "P", "plausibility": "reasonable", "verdict": "accepted", "reason": "works"},
            ],
            "outcome": "undetermined", "evaluator_id": "eval",
        }
        self.assertIs(analysis, validate_contract("ambiguity_analysis", analysis))


if __name__ == "__main__":
    unittest.main()
