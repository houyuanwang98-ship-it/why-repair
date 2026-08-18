import json
import unittest
from pathlib import Path

from harness.m6_experiments import (
    COMPARISON_FAMILIES, FIXTURE_DIGEST, METHOD_IDS, M6ExperimentError, assert_execution_allowed,
    apply_method_applicability, build_experiment_config, cache_fingerprint, load_m5_gate, score_records,
    validate_ablation_purity, validate_comparison, validate_experiment_config,
    validate_experiment_suite,
)


ROOT = Path(__file__).resolve().parents[1]


def config(method):
    return build_experiment_config(
        method, model_id="fixture-model", prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
        theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST, token_limit=4000,
        call_limit=4, timeout_seconds=60,
    )


class M6PersonBExperimentTest(unittest.TestCase):
    def test_all_locked_methods_have_unique_configs(self):
        configs = [config(method) for method in METHOD_IDS]
        validate_experiment_suite(configs)
        for methods in COMPARISON_FAMILIES.values():
            validate_comparison([config(method) for method in methods])
        self.assertEqual(9, len({item["experiment_id"] for item in configs}))
        self.assertEqual(1, configs[METHOD_IDS.index("single_round_repair")]["method"]["max_patch_rounds"])

    def test_ablation_changes_are_explicit(self):
        validate_ablation_purity()
        full = config("full_system")["method"]
        self.assertFalse(config("no_graph")["method"]["sees_graph"])
        self.assertFalse(config("no_structured_certificate")["method"]["structured_certificate"])
        self.assertFalse(config("no_counterexample_protocol")["method"]["counterexample_protocol"])
        self.assertFalse(config("no_descendant_invalidation")["method"]["descendant_invalidation"])
        self.assertTrue(full["sees_graph"] and full["structured_certificate"] and full["counterexample_protocol"])

    def test_comparison_rejects_budget_drift(self):
        left = config("direct_judgment")
        right = build_experiment_config(
            "full_system", model_id="fixture-model", prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
            theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST, token_limit=4001,
            call_limit=4, timeout_seconds=60,
        )
        with self.assertRaisesRegex(M6ExperimentError, "budget"):
            validate_comparison([left, right])

    def test_config_rejects_content_tampering_and_binds_runtime_assets(self):
        item = config("full_system")
        self.assertEqual(FIXTURE_DIGEST, validate_experiment_config(item)["scorer_digest"])
        item["method"]["sees_graph"] = False
        with self.assertRaisesRegex(M6ExperimentError, "method spec"):
            validate_experiment_config(item)

    def test_role_model_mode_is_enforced(self):
        with self.assertRaisesRegex(M6ExperimentError, "same_model"):
            build_experiment_config(
                "full_system", model_id={"generator": "a", "critic": "b"}, role_mode="same_model",
                prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
                theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST,
                token_limit=4000, call_limit=4, timeout_seconds=60,
            )
        different = build_experiment_config(
            "full_system", model_id={"generator": "a", "critic": "b"}, role_mode="different_models",
            prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
            theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST,
            token_limit=4000, call_limit=4, timeout_seconds=60,
        )
        self.assertNotEqual(different["models"]["generator"], different["models"]["critic"])

    def test_cache_is_method_and_exact_input_isolated(self):
        direct, full = config("direct_judgment"), config("full_system")
        self.assertNotEqual(cache_fingerprint(direct, "c1", {"x": 1}), cache_fingerprint(full, "c1", {"x": 1}))
        self.assertNotEqual(cache_fingerprint(full, "c1", {"x": 1}), cache_fingerprint(full, "c1", {"x": 2}))

    def test_real_execution_fails_closed_but_fixture_is_allowed(self):
        gate = load_m5_gate(ROOT)
        pending = {"person_a": "pending", "person_b_cross_review": "pending", "controller_manifest": "pending"}
        with self.assertRaisesRegex(M6ExperimentError, "M5"):
            assert_execution_allowed(gate, pending, fixture_only=False)
        assert_execution_allowed(gate, pending, fixture_only=True)
        with self.assertRaisesRegex(M6ExperimentError, "detached-signature"):
            assert_execution_allowed(
                {"m6_entry_allowed": True},
                {"person_a": "signed", "person_b_cross_review": "signed",
                 "controller_manifest": "frozen"},
                fixture_only=False,
            )

    def test_repository_owner_release_allows_execution_but_not_tampering(self):
        release = json.loads(
            (ROOT / "data/governance/m6_m7_user_execution_release_v0_1.json").read_text(encoding="utf-8")
        )
        assert_execution_allowed({}, {}, fixture_only=False, user_release=release)
        tampered = dict(release, scientific_claim_allowed=True)
        with self.assertRaisesRegex(M6ExperimentError, "M5"):
            assert_execution_allowed({}, {}, fixture_only=False, user_release=tampered)

    def test_locked_metrics_and_intention_to_treat_failure(self):
        rows = [
            {"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "accepted", "gold_first_error_evaluable": True,
             "gold_first_error": 2, "gold_first_error_reason": "evaluable", "predicted_first_error": 2,
             "gold_repairability": "repairable", "gold_counterexample_eligible": False, "claimed_repair_success": True,
             "verified_repair_success": False, "false_repair": True, "patch_applied": True,
             "new_error_introduced": True, "new_error_count": 1,
             "independent_review_accepted": False, "problem_preserved": False,
             "failed_edge_resolved": False, "no_new_errors": False,
             "operationally_minimal": False, "descendants_revalidated": False,
             "final_path_clear": False, "failure_type": None},
            {"sample_id": "b", "gold_verdict": "accepted", "predicted_verdict": "accepted", "gold_first_error_evaluable": False,
             "gold_first_error_reason": "absent", "predicted_first_error": None, "gold_repairability": "irreparable",
             "gold_counterexample_eligible": False, "failure_type": None},
            {"sample_id": "c", "gold_verdict": "invalid", "predicted_verdict": None, "gold_first_error_evaluable": True,
             "gold_first_error": 1, "gold_first_error_reason": "evaluable", "predicted_first_error": None,
             "gold_repairability": "repairable", "gold_counterexample_eligible": False, "failure_type": "timeout"},
            {"sample_id": "d", "gold_verdict": "gap", "predicted_verdict": "accepted_with_gap", "gold_first_error_evaluable": False,
             "gold_first_error_reason": "undetermined", "predicted_first_error": None, "gold_repairability": "undetermined",
             "gold_counterexample_eligible": False, "failure_type": None},
        ]
        metrics = score_records(rows)
        self.assertEqual(0.5, metrics["first_error_exact_accuracy"]["value"])
        self.assertEqual(0.5, metrics["false_accept_rate"]["value"])
        self.assertEqual(1.0, metrics["false_accept_rate"]["worst_case_upper"])
        self.assertEqual(0.0, metrics["verified_repair_success_rate"]["value"])
        self.assertEqual(1.0, metrics["false_repair_rate"]["value"])
        self.assertEqual(0.0, metrics["unsupported_resolution_rate"]["value"])
        self.assertEqual("undefined (0/0)", metrics["false_claim_detection_rate"]["value"])
        self.assertEqual("undefined (0/0)", metrics["valid_counterexample_coverage"]["value"])
        self.assertEqual("undefined (0/0)", metrics["counterexample_candidate_precision"]["value"])
        self.assertEqual(1, metrics["new_error_introduction_rate"]["introduced_error_total"])
        self.assertEqual(0.25, metrics["infrastructure_failure_rate"]["value"])

    def test_inconsistent_failure_and_repair_records_fail_closed(self):
        with self.assertRaisesRegex(M6ExperimentError, "cannot contain"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "accepted",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_first_error_reason": "evaluable", "gold_repairability": "repairable",
                            "gold_counterexample_eligible": False, "failure_type": "timeout"}])
        with self.assertRaisesRegex(M6ExperimentError, "prerequisites"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_first_error_reason": "evaluable", "gold_repairability": "repairable",
                            "gold_counterexample_eligible": False, "verified_repair_success": True,
                            "failure_type": None}])
        with self.assertRaisesRegex(M6ExperimentError, "counterexample counts"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_first_error_reason": "evaluable", "gold_repairability": "irreparable",
                            "gold_counterexample_eligible": False, "counterexample_candidate_count": "one",
                            "failure_type": None}])

    def test_zero_claimed_repairs_is_undefined(self):
        metrics = score_records([{"sample_id": "a", "gold_verdict": "accepted", "predicted_verdict": "accepted",
                                  "gold_first_error_evaluable": False, "gold_first_error_reason": "absent",
                                  "predicted_first_error": None, "gold_repairability": "irreparable",
                                  "gold_counterexample_eligible": False, "failure_type": None}])
        self.assertEqual("undefined (0/0)", metrics["false_repair_rate"]["value"])

    def test_method_mechanism_metrics_are_not_applicable(self):
        base = score_records([{"sample_id": "a", "gold_verdict": "accepted", "predicted_verdict": "accepted",
                              "gold_first_error_evaluable": False, "gold_first_error_reason": "absent",
                              "predicted_first_error": None, "gold_repairability": "irreparable",
                              "gold_counterexample_eligible": False, "failure_type": None}])
        direct = apply_method_applicability("direct_judgment", base)
        self.assertEqual("not_applicable", direct["verified_repair_success_rate"]["value"])
        self.assertEqual("not_applicable", direct["valid_counterexample_coverage"]["value"])
        full = apply_method_applicability("full_system", base)
        self.assertEqual("undefined (0/0)", full["verified_repair_success_rate"]["value"])

    def test_abstention_excludes_infrastructure_failures(self):
        rows = [
            {"sample_id": "a", "gold_verdict": "undetermined", "predicted_verdict": "undetermined",
             "gold_first_error_evaluable": False, "gold_first_error_reason": "undetermined",
             "gold_repairability": "undetermined", "gold_counterexample_eligible": False, "failure_type": None},
            {"sample_id": "b", "gold_verdict": "undetermined", "predicted_verdict": None,
             "gold_first_error_evaluable": False, "gold_first_error_reason": "undetermined",
             "gold_repairability": "undetermined", "gold_counterexample_eligible": False, "failure_type": "timeout"},
        ]
        metric = score_records(rows)["proof_abstention_rate"]
        self.assertEqual(1.0, metric["value"])
        self.assertEqual(1, metric["infrastructure_failures_excluded"])

    def test_false_repair_is_derived_and_success_requires_all_math_gates(self):
        base = {"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                "gold_first_error_evaluable": True, "gold_first_error": 1,
                "gold_first_error_reason": "evaluable", "gold_repairability": "repairable",
                "gold_counterexample_eligible": False, "claimed_repair_success": True,
                "patch_applied": True, "new_error_introduced": False, "new_error_count": 0,
                "independent_review_accepted": False, "problem_preserved": False,
                "failed_edge_resolved": False, "no_new_errors": False,
                "operationally_minimal": False, "descendants_revalidated": False,
                "final_path_clear": False, "failure_type": None}
        with self.assertRaisesRegex(M6ExperimentError, "false repair"):
            score_records([{**base, "verified_repair_success": False, "false_repair": False}])
        gates = {field: True for field in (
            "independent_review_accepted", "problem_preserved", "failed_edge_resolved",
            "no_new_errors", "operationally_minimal", "descendants_revalidated", "final_path_clear",
        )}
        metrics = score_records([{**base, **gates, "verified_repair_success": True,
                                  "false_repair": False}])
        self.assertEqual(1.0, metrics["verified_repair_success_rate"]["value"])

    def test_applied_patch_requires_complete_review_fields(self):
        row = {"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
               "gold_first_error_evaluable": True, "gold_first_error": 1,
               "gold_first_error_reason": "evaluable", "gold_repairability": "repairable",
               "gold_counterexample_eligible": False, "patch_applied": True,
               "claimed_repair_success": False, "failure_type": None}
        with self.assertRaisesRegex(M6ExperimentError, "complete mathematical review"):
            score_records([row])

    def test_only_preregistered_comparison_families_are_allowed(self):
        with self.assertRaisesRegex(M6ExperimentError, "preregistered"):
            validate_comparison([config("direct_judgment"), config("no_graph"), config("full_system")])
        with self.assertRaisesRegex(M6ExperimentError, "complete preregistered"):
            validate_comparison([config("direct_judgment"), config("full_system")])
        with self.assertRaisesRegex(M6ExperimentError, "every preregistered method"):
            validate_experiment_suite([config(method) for method in METHOD_IDS[:-1]])

    def test_gold_denominators_and_counterexample_semantics_fail_closed(self):
        incomplete = {"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                      "gold_first_error_evaluable": True, "gold_first_error": 1,
                      "gold_first_error_reason": "evaluable", "gold_repairability": "irreparable",
                      "failure_type": None}
        with self.assertRaisesRegex(M6ExperimentError, "missing required"):
            score_records([incomplete])
        with self.assertRaisesRegex(M6ExperimentError, "valid counterexample"):
            score_records([{**incomplete, "gold_counterexample_eligible": True,
                            "predicted_verdict": "accepted", "counterexample_candidate_count": 1,
                            "valid_counterexample_count": 1}])

    def test_digest_fields_require_real_sha256_shape(self):
        with self.assertRaisesRegex(M6ExperimentError, "SHA-256"):
            build_experiment_config(
                "full_system", model_id="fixture-model", prompt_digest="p",
                dataset_digest=FIXTURE_DIGEST, theorem_bank_digest=FIXTURE_DIGEST,
                tool_digest=FIXTURE_DIGEST, token_limit=4000, call_limit=4,
                timeout_seconds=60,
            )


if __name__ == "__main__":
    unittest.main()
