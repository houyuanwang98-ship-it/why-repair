import unittest

from harness.contracts import ContractError, validate_contract


REF1 = {"proof_id": "p1", "node_id": 1, "version": 1}
REF2 = {"proof_id": "p1", "node_id": 2, "version": 1}


class DualAgentContractTest(unittest.TestCase):
    def test_valid_run_manifest(self):
        manifest = {
            "schema_version": "0.3", "run_id": "run-1",
            "created_at": "2026-08-11T00:00:00+08:00",
            "controller_version": "0.3", "contract_version": "0.3",
            "input_digest": "sha256:input", "theorem_bank_digest": None,
            "agents": {"evaluator": "fixture-evaluator", "repair_generator": "fixture-repair"},
            "prompt_versions": {"evaluator": "eval-v1", "repair_generator": "repair-v1"},
            "model_parameters": {"temperature": 0}, "events": [],
        }
        self.assertIs(manifest, validate_contract("run_manifest", manifest))

    def test_run_manifest_rejects_wrong_contract_version(self):
        manifest = {
            "schema_version": "0.3", "run_id": "run-1",
            "created_at": "2026-08-11T00:00:00+08:00",
            "controller_version": "0.3", "contract_version": "0.1",
            "input_digest": "sha256:input", "theorem_bank_digest": None,
            "agents": {"evaluator": "fixture-evaluator", "repair_generator": "fixture-repair"},
            "prompt_versions": {"evaluator": "eval-v1", "repair_generator": "repair-v1"},
            "model_parameters": {}, "events": [],
        }
        with self.assertRaises(ContractError):
            validate_contract("run_manifest", manifest)

    def test_valid_error_certificate(self):
        value = {
            "schema_version": "0.3", "certificate_id": "err-1", "target": REF2,
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
            "schema_version": "0.3", "certificate_id": "err-1", "target": REF2,
            "premises": [REF1], "error_type": "algebraic_mismatch",
            "failed_inference": "bad", "evidence": ["bad"],
            "repair_constraints": {
                "allowed_operations": ["replace"], "max_new_nodes": 1,
                "preserve_theorem": True, "preserve_assumptions": True,
            },
        }
        with self.assertRaises(ContractError):
            validate_contract("error_certificate", value)

    def test_dependency_blocking_is_not_a_mathematical_verdict(self):
        value = {
            "schema_version": "0.3", "evaluation_id": "eval-blocked", "target": REF2,
            "verdict": "blocked_by_invalid_dependency", "error_type": None,
            "reason": "parent is stale", "dependency_versions": {"1": 1},
            "evaluator_id": "eval",
        }
        with self.assertRaises(ContractError):
            validate_contract("evaluation_record", value)

    def test_counterexample_requires_true_premises_and_false_target(self):
        base = {
            "schema_version": "0.3", "certificate_id": "cex-1", "target": REF2,
            "theorem_ref": None,
            "scope": "local_claim", "structure": "real numbers",
            "assignment": {"a": 0, "x": 1, "y": 2},
            "premise_checks": [{"statement": "ax=ay", "holds": True, "evidence": "0=0"}],
            "checked_premise_refs": [REF1],
            "global_assumption_digest": "sha256:fixture",
            "target_check": {"statement": "x=y", "holds": False, "evidence": "1!=2"},
            "checker": "deterministic_fixture",
        }
        validate_contract("counterexample_certificate", base)
        invalid = {**base, "target_check": {"statement": "x=y", "holds": True, "evidence": "wrong"}}
        with self.assertRaises(ContractError):
            validate_contract("counterexample_certificate", invalid)

    def test_global_counterexample_binds_exact_theorem_version(self):
        value = {
            "schema_version": "0.3", "certificate_id": "cex-global",
            "target": None,
            "theorem_ref": {
                "proof_id": "p1", "theorem_version": 2,
                "theorem_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            },
            "scope": "global_theorem", "structure": "real numbers",
            "assignment": {"a": 0, "x": 1, "y": 2},
            "premise_checks": [{"statement": "ax=ay", "holds": True, "evidence": "0=0"}],
            "checked_premise_refs": [],
            "global_assumption_digest": "sha256:fixture",
            "target_check": {"statement": "x=y", "holds": False, "evidence": "1!=2"},
            "checker": "deterministic_fixture",
        }
        self.assertIs(value, validate_contract("counterexample_certificate", value))
        invalid = {**value, "theorem_ref": None}
        with self.assertRaisesRegex(ContractError, "requires theorem_ref"):
            validate_contract("counterexample_certificate", invalid)

    def test_blocked_dependency_is_not_a_mathematical_verdict(self):
        value = {
            "schema_version": "0.1", "evaluation_id": "eval-blocked", "target": REF2,
            "verdict": "blocked_by_invalid_dependency", "error_type": None,
            "reason": "parent failed", "dependency_versions": {"1": 1},
            "evaluator_id": "eval",
        }
        with self.assertRaises(ContractError):
            validate_contract("evaluation_record", value)

    def test_add_assumption_must_change_problem(self):
        patch = {
            "schema_version": "0.3", "patch_id": "patch-1", "error_certificate_id": "err-1",
            "target": REF2, "operation": "add_assumption", "replacement_nodes": [],
            "target_dependencies_after": [REF1],
            "used_dependencies": [REF1], "rationale": "Add a != 0", "changes_problem": False,
        }
        with self.assertRaises(ContractError):
            validate_contract("patch_proposal", patch)

    def test_replace_dependency_declarations_must_match(self):
        patch = {
            "schema_version": "0.3", "patch_id": "patch-1", "error_certificate_id": "err-1",
            "target": REF2, "operation": "replace",
            "replacement_nodes": [{
                "node_id": 2, "order_key": 2000, "claim": "Q", "self_contained_claim": "Q",
                "node_type": "claim", "depends_on": [],
            }],
            "target_dependencies_after": [REF1], "used_dependencies": [REF1],
            "rationale": "replace", "changes_problem": False,
        }
        with self.assertRaisesRegex(ContractError, "dependencies must equal"):
            validate_contract("patch_proposal", patch)

    def test_self_dependency_is_rejected(self):
        node = {
            "schema_version": "0.3", "proof_id": "p1", "node_id": 1, "version": 1,
            "order_key": 1000,
            "claim": "P", "self_contained_claim": "P", "node_type": "claim",
            "source_span": {"start": 0, "end": 1}, "source_span_source": "original",
            "depends_on": [{"proof_id": "p1", "node_id": 1, "version": 2}],
        }
        with self.assertRaises(ContractError):
            validate_contract("proof_node", node)

    def test_duplicate_dependency_is_rejected(self):
        node = {
            "schema_version": "0.3", "proof_id": "p1", "node_id": 2, "version": 1,
            "order_key": 2000,
            "claim": "Q", "self_contained_claim": "Q", "node_type": "claim",
            "source_span": {"start": 2, "end": 3}, "source_span_source": "original",
            "depends_on": [REF1, REF1],
        }
        with self.assertRaises(ContractError):
            validate_contract("proof_node", node)

    def test_ambiguity_outcome_cannot_cherry_pick_one_successful_interpretation(self):
        analysis = {
            "schema_version": "0.3", "analysis_id": "amb-1", "target": REF2,
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
            "schema_version": "0.3", "analysis_id": "amb-2", "target": REF2,
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
