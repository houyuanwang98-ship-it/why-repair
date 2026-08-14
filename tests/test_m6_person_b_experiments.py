import unittest
from pathlib import Path

from harness.m6_experiments import (
    METHOD_IDS, M6ExperimentError, assert_execution_allowed,
    build_experiment_config, cache_fingerprint, load_m5_gate, score_records,
    validate_ablation_purity, validate_comparison, validate_experiment_config,
)


ROOT = Path(__file__).resolve().parents[1]


def config(method):
    return build_experiment_config(
        method, model_id="fixture-model", prompt_digest="p", dataset_digest="d",
        theorem_bank_digest="t", tool_digest="x", token_limit=4000,
        call_limit=4, timeout_seconds=60,
    )


class M6PersonBExperimentTest(unittest.TestCase):
    def test_all_locked_methods_have_unique_configs(self):
        configs = [config(method) for method in METHOD_IDS]
        validate_comparison(configs)
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
            "full_system", model_id="fixture-model", prompt_digest="p", dataset_digest="d",
            theorem_bank_digest="t", tool_digest="x", token_limit=4001,
            call_limit=4, timeout_seconds=60,
        )
        with self.assertRaisesRegex(M6ExperimentError, "budget"):
            validate_comparison([left, right])

    def test_config_rejects_content_tampering_and_binds_runtime_assets(self):
        item = config("full_system")
        self.assertEqual("fixture-scorer", validate_experiment_config(item)["scorer_digest"])
        item["method"]["sees_graph"] = False
        with self.assertRaisesRegex(M6ExperimentError, "method spec"):
            validate_experiment_config(item)

    def test_role_model_mode_is_enforced(self):
        with self.assertRaisesRegex(M6ExperimentError, "same_model"):
            build_experiment_config(
                "full_system", model_id={"generator": "a", "critic": "b"}, role_mode="same_model",
                prompt_digest="p", dataset_digest="d", theorem_bank_digest="t", tool_digest="x",
                token_limit=4000, call_limit=4, timeout_seconds=60,
            )
        different = build_experiment_config(
            "full_system", model_id={"generator": "a", "critic": "b"}, role_mode="different_models",
            prompt_digest="p", dataset_digest="d", theorem_bank_digest="t", tool_digest="x",
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

    def test_locked_metrics_and_intention_to_treat_failure(self):
        rows = [
            {"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "accepted", "gold_first_error_evaluable": True,
             "gold_first_error": 2, "predicted_first_error": 2, "gold_repairability": "repairable", "claimed_repair_success": True,
             "verified_repair_success": False, "false_repair": True, "patch_applied": True, "new_error_introduced": True, "failure_type": None},
            {"sample_id": "b", "gold_verdict": "accepted", "predicted_verdict": "accepted", "gold_first_error_evaluable": False,
             "gold_first_error_reason": "absent", "predicted_first_error": None, "gold_repairability": "irreparable", "failure_type": None},
            {"sample_id": "c", "gold_verdict": "invalid", "predicted_verdict": None, "gold_first_error_evaluable": True,
             "gold_first_error": 1, "predicted_first_error": None, "gold_repairability": "repairable", "failure_type": "timeout"},
            {"sample_id": "d", "gold_verdict": "gap", "predicted_verdict": "accepted_with_gap", "gold_first_error_evaluable": False,
             "gold_first_error_reason": "undetermined", "predicted_first_error": None, "gold_repairability": "undetermined",
             "gold_counterexample_eligible": True, "failure_type": None},
        ]
        metrics = score_records(rows)
        self.assertEqual(0.5, metrics["first_error_exact_accuracy"]["value"])
        self.assertEqual(0.5, metrics["false_accept_rate"]["value"])
        self.assertEqual(1.0, metrics["false_accept_rate"]["worst_case_upper"])
        self.assertEqual(0.0, metrics["verified_repair_success_rate"]["value"])
        self.assertEqual(1.0, metrics["false_repair_rate"]["value"])
        self.assertEqual(1.0, metrics["unsupported_resolution_rate"]["value"])
        self.assertEqual(0.0, metrics["false_claim_detection_rate"]["value"])
        self.assertEqual(0.0, metrics["valid_counterexample_coverage"]["value"])
        self.assertEqual("undefined (0/0)", metrics["counterexample_candidate_precision"]["value"])
        self.assertEqual(1, metrics["new_error_introduction_rate"]["introduced_error_total"])
        self.assertEqual(0.25, metrics["infrastructure_failure_rate"]["value"])

    def test_inconsistent_failure_and_repair_records_fail_closed(self):
        with self.assertRaisesRegex(M6ExperimentError, "cannot contain"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "accepted",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_repairability": "repairable", "failure_type": "timeout"}])
        with self.assertRaisesRegex(M6ExperimentError, "prerequisites"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_repairability": "repairable", "verified_repair_success": True,
                            "failure_type": None}])
        with self.assertRaisesRegex(M6ExperimentError, "counterexample counts"):
            score_records([{"sample_id": "a", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                            "gold_first_error_evaluable": True, "gold_first_error": 1,
                            "gold_repairability": "irreparable", "counterexample_candidate_count": "one",
                            "failure_type": None}])

    def test_zero_claimed_repairs_is_undefined(self):
        metrics = score_records([{"sample_id": "a", "gold_verdict": "accepted", "predicted_verdict": "accepted",
                                  "gold_first_error_evaluable": False, "gold_first_error_reason": "absent",
                                  "predicted_first_error": None, "gold_repairability": "irreparable", "failure_type": None}])
        self.assertEqual("undefined (0/0)", metrics["false_repair_rate"]["value"])


if __name__ == "__main__":
    unittest.main()
