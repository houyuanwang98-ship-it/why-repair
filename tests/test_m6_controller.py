import unittest
from pathlib import Path

from harness.m6_controller import (
    aggregate_by_experiment, build_controller_manifest, field_completeness_report, freeze_artifacts,
    CONFIRMATORY_FAMILIES, holm_adjust, holm_adjust_preregistered, paired_bootstrap_difference,
    paired_randomization_p_value, validate_controller_manifest,
    validate_run_ledger,
)
from harness.m6_experiments import FIXTURE_DIGEST, METHOD_IDS, M6ExperimentError, build_experiment_config


ROOT = Path(__file__).resolve().parents[1]


def config(method):
    return build_experiment_config(
        method, model_id="fixture-model", prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
        theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST, token_limit=8000,
        call_limit=4, timeout_seconds=180,
    )


def manifest():
    return build_controller_manifest(
        configs=[config(method) for method in METHOD_IDS],
        sample_ids=["s1", "s2"], artifacts={"fixture": "a" * 64},
        metric_digest="b" * 64, statistics_digest="c" * 64, bootstrap_seeds=[1, 2, 3],
        randomization_seeds=[4, 5, 6],
        m5_gate_digest="d" * 64, signatures={"person_a": "pending_human_signature",
        "person_b_cross_review": "pending_cross_review", "controller": "candidate_unsigned"},
    )


def complete_ledger(item):
    rows = []
    for configuration in item["configs"]:
        experiment_id = configuration["experiment_id"]
        for sample_id in item["sample_ids"]:
            failed = sample_id == "s2"
            rows.append({
                "run_id": f"{experiment_id}:{sample_id}", "experiment_id": experiment_id,
                "sample_id": sample_id, "attempt": 0,
                "status": "timeout" if failed else "success", "terminal": True,
                "tokens": 1, "model_calls": 1, "cost": 0, "latency_seconds": 1,
            })
    return rows


class M6ControllerTest(unittest.TestCase):
    def test_freeze_artifacts_hashes_explicit_files(self):
        frozen = freeze_artifacts(ROOT, ["docs/milestones/M06_person_a_preregistered_protocol.md"])
        self.assertEqual(64, len(next(iter(frozen.values()))))
        with self.assertRaisesRegex(M6ExperimentError, "repository-relative"):
            freeze_artifacts(ROOT, ["../outside"])
        with self.assertRaisesRegex(M6ExperimentError, "repository-relative"):
            freeze_artifacts(ROOT, ["docs/../README.md"])
        with self.assertRaisesRegex(M6ExperimentError, "repository-relative"):
            freeze_artifacts(ROOT, [Path("README.md")])

    def test_manifest_binds_samples_configs_and_statistics(self):
        item = manifest()
        self.assertTrue(item["fixture_only"])
        self.assertEqual(9, len(item["configs"]))
        self.assertTrue(item["manifest_id"].startswith("m6-controller-"))
        self.assertEqual(item, validate_controller_manifest(item))
        item["sample_ids"].append("tampered")
        with self.assertRaisesRegex(M6ExperimentError, "mutated"):
            validate_controller_manifest(item)

    def test_fixture_manifest_cannot_overclaim_open_gate_or_signatures(self):
        kwargs = dict(
            configs=[config(method) for method in METHOD_IDS], sample_ids=["s1"],
            artifacts={"fixture": "a" * 64}, metric_digest="b" * 64,
            statistics_digest="c" * 64, bootstrap_seeds=[1], randomization_seeds=[2],
            m5_gate_digest="d" * 64,
            signatures={"person_a": "signed", "person_b_cross_review": "signed",
                        "controller": "signed"},
        )
        with self.assertRaisesRegex(M6ExperimentError, "pending signatures"):
            build_controller_manifest(**kwargs)
        kwargs.update(signatures={"person_a": "pending_human_signature",
                                  "person_b_cross_review": "pending_cross_review",
                                  "controller": "candidate_unsigned"}, fixture_only="yes")
        with self.assertRaisesRegex(M6ExperimentError, "fixture_only must be boolean"):
            build_controller_manifest(**kwargs)
        kwargs.update(fixture_only=True, artifacts={"../outside": "a" * 64})
        with self.assertRaisesRegex(M6ExperimentError, "repository-relative"):
            build_controller_manifest(**kwargs)
        kwargs["artifacts"] = {".": "a" * 64}
        with self.assertRaisesRegex(M6ExperimentError, "repository-relative"):
            build_controller_manifest(**kwargs)

    def test_formal_manifest_cannot_bypass_closed_gates(self):
        kwargs = dict(
            configs=[config(method) for method in METHOD_IDS], sample_ids=["s1"], artifacts={"fixture": "a" * 64},
            metric_digest="b" * 64, statistics_digest="c" * 64,
            bootstrap_seeds=list(range(10_000)), m5_gate_digest="d" * 64,
            randomization_seeds=list(range(10_000, 20_000)),
            signatures={"person_a": "signed", "person_b_cross_review": "signed", "controller": "signed"},
            fixture_only=False,
        )
        with self.assertRaisesRegex(M6ExperimentError, "authentic M5"):
            build_controller_manifest(**kwargs)
        kwargs["m5_entry_allowed"] = True
        with self.assertRaisesRegex(M6ExperimentError, "detached-signature"):
            build_controller_manifest(**kwargs)

    def test_ledger_preserves_failures_retries_cost_and_missing_rows(self):
        item = manifest()
        left, right = item["configs"][0]["experiment_id"], item["configs"][-1]["experiment_id"]
        rows = [
            {"run_id": "a0", "experiment_id": left, "sample_id": "s1", "attempt": 0, "status": "api_error", "terminal": False, "tokens": 10, "model_calls": 1, "cost": 0.1, "latency_seconds": 1},
            {"run_id": "a1", "experiment_id": left, "sample_id": "s1", "attempt": 1, "status": "success", "terminal": True, "tokens": 20, "model_calls": 1, "cost": 0.2, "latency_seconds": 2},
            {"run_id": "b", "experiment_id": left, "sample_id": "s2", "attempt": 0, "status": "timeout", "terminal": True, "tokens": 30, "model_calls": 1, "cost": 0.3, "latency_seconds": 180},
            {"run_id": "c", "experiment_id": right, "sample_id": "s1", "attempt": 0, "status": "success", "terminal": True, "tokens": 40, "model_calls": 1, "cost": 0.4, "latency_seconds": 4},
        ]
        report = validate_run_ledger(item, rows)
        self.assertFalse(report["complete"])
        self.assertEqual(15, len(report["missing_assignments"]))
        self.assertEqual(100, report["total_tokens"])
        self.assertEqual(4, report["total_model_calls"])
        self.assertEqual(1, report["failure_counts"]["timeout"])

    def test_ledger_rejects_deleted_attempt_history(self):
        item = manifest()
        row = {"run_id": "x", "experiment_id": item["configs"][0]["experiment_id"], "sample_id": "s1",
               "attempt": 1, "status": "success", "terminal": True, "tokens": 1, "model_calls": 1, "cost": 0, "latency_seconds": 1}
        with self.assertRaisesRegex(M6ExperimentError, "contiguous"):
            validate_run_ledger(item, [row])

    def test_ledger_rejects_nonterminal_success(self):
        item = manifest()
        row = {"run_id": "x", "experiment_id": item["configs"][0]["experiment_id"], "sample_id": "s1",
               "attempt": 0, "status": "success", "terminal": False, "tokens": 1, "model_calls": 1, "cost": 0, "latency_seconds": 1}
        with self.assertRaisesRegex(M6ExperimentError, "successful"):
            validate_run_ledger(item, [row])

    def test_ledger_rejects_nonterminal_retry_exhaustion(self):
        item = manifest()
        row = {"run_id": "x", "experiment_id": item["configs"][0]["experiment_id"], "sample_id": "s1",
               "attempt": 0, "status": "retry_exhausted", "terminal": False,
               "tokens": 1, "model_calls": 1, "cost": 0, "latency_seconds": 1}
        with self.assertRaisesRegex(M6ExperimentError, "retry_exhausted must be terminal"):
            validate_run_ledger(item, [row])

    def test_ledger_enforces_frozen_hard_budgets(self):
        item = manifest()
        row = {"run_id": "x", "experiment_id": item["configs"][0]["experiment_id"], "sample_id": "s1",
               "attempt": 0, "status": "budget_exhausted", "terminal": True, "tokens": 8001,
               "model_calls": 1, "cost": 0, "latency_seconds": 1}
        with self.assertRaisesRegex(M6ExperimentError, "token limit"):
            validate_run_ledger(item, [row])
        row.update(tokens=1, cost=float("nan"))
        with self.assertRaisesRegex(M6ExperimentError, "cost"):
            validate_run_ledger(item, [row])

    def test_wall_clock_limit_is_per_sample_across_retries(self):
        item = manifest()
        experiment_id = item["configs"][0]["experiment_id"]
        rows = [
            {"run_id": "x0", "experiment_id": experiment_id, "sample_id": "s1", "attempt": 0,
             "status": "api_error", "terminal": False, "tokens": 1, "model_calls": 1,
             "cost": 0, "latency_seconds": 100},
            {"run_id": "x1", "experiment_id": experiment_id, "sample_id": "s1", "attempt": 1,
             "status": "timeout", "terminal": True, "tokens": 1, "model_calls": 1,
             "cost": 0, "latency_seconds": 100},
        ]
        with self.assertRaisesRegex(M6ExperimentError, "per-sample wall-clock"):
            validate_run_ledger(item, rows)

    def test_field_completeness_reports_rows_without_dropping_false_values(self):
        report = field_completeness_report(
            [{"run_id": "a", "verdict": False, "cost": 0}, {"run_id": "b", "verdict": None, "cost": 1}],
            ["verdict", "cost"],
        )
        self.assertFalse(report["complete"])
        self.assertEqual(1, report["fields"]["verdict"]["missing_count"])
        self.assertEqual(2, report["fields"]["cost"]["present_count"])

    def test_bootstrap_and_holm_are_deterministic(self):
        result = paired_bootstrap_difference([1, 1, 0, 1], [0, 0, 0, 0], seeds=list(range(100)))
        self.assertEqual(0.75, result["absolute_difference"])
        self.assertEqual(100, result["bootstrap_replicates"])
        self.assertNotIn("p_value_unadjusted", result)
        p_value = paired_randomization_p_value([1, 1, 0, 1], [0, 0, 0, 0], seeds=list(range(100)))
        self.assertGreater(p_value, 0)
        adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertEqual({"a": 0.03, "c": 0.06, "b": 0.06}, adjusted)
        with self.assertRaisesRegex(M6ExperimentError, "finite"):
            paired_bootstrap_difference([float("nan")], [0], seeds=[1])
        complete = {key: 0.05 for key in CONFIRMATORY_FAMILIES["H1"]}
        self.assertEqual(set(complete), set(holm_adjust_preregistered("H1", complete)))
        with self.assertRaisesRegex(M6ExperimentError, "complete preregistered"):
            holm_adjust_preregistered("H1", {next(iter(complete)): 0.05})

    def test_aggregate_keeps_infrastructure_failure_in_denominator(self):
        item = manifest()
        ledger = complete_ledger(item)
        rows = []
        for configuration in item["configs"]:
            experiment_id = configuration["experiment_id"]
            rows.extend([
                {"experiment_id": experiment_id, "sample_id": "s1", "gold_verdict": "invalid", "predicted_verdict": "invalid",
                 "terminal_run_id": f"{experiment_id}:s1",
                 "gold_first_error_evaluable": True, "gold_first_error": 1, "gold_first_error_reason": "evaluable",
                 "predicted_first_error": 1, "gold_repairability": "irreparable",
                 "gold_counterexample_eligible": False, "failure_type": None},
                {"experiment_id": experiment_id, "sample_id": "s2", "gold_verdict": "invalid", "predicted_verdict": None,
                 "terminal_run_id": f"{experiment_id}:s2",
                 "gold_first_error_evaluable": True, "gold_first_error": 1, "gold_first_error_reason": "evaluable",
                 "predicted_first_error": None, "gold_repairability": "irreparable",
                 "gold_counterexample_eligible": False, "failure_type": "timeout"},
            ])
        target = item["configs"][-1]["experiment_id"]
        metrics = aggregate_by_experiment(item, ledger, rows)[target]
        self.assertEqual(0.5, metrics["first_error_exact_accuracy"]["value"])
        self.assertEqual(0.5, metrics["infrastructure_failure_rate"]["value"])

    def test_aggregate_rejects_unbound_or_incomplete_scoring_rows(self):
        item = manifest()
        ledger = complete_ledger(item)
        row = {"experiment_id": "unbound", "sample_id": "s1"}
        with self.assertRaisesRegex(M6ExperimentError, "not assigned"):
            aggregate_by_experiment(item, ledger, [row])
        with self.assertRaisesRegex(M6ExperimentError, "cover every"):
            aggregate_by_experiment(item, ledger, [])

    def test_aggregate_binds_terminal_run_and_failure_status(self):
        item = manifest()
        ledger = complete_ledger(item)
        scoring = []
        for configuration in item["configs"]:
            experiment_id = configuration["experiment_id"]
            scoring.extend([
                {"experiment_id": experiment_id, "sample_id": "s1", "terminal_run_id": f"{experiment_id}:s1",
                 "gold_verdict": "accepted", "predicted_verdict": "accepted", "gold_first_error_evaluable": False,
                 "gold_first_error_reason": "absent", "gold_repairability": "irreparable",
                 "gold_counterexample_eligible": False, "failure_type": None},
                {"experiment_id": experiment_id, "sample_id": "s2", "terminal_run_id": f"{experiment_id}:s2",
                 "gold_verdict": "accepted", "predicted_verdict": None, "gold_first_error_evaluable": False,
                 "gold_first_error_reason": "absent", "gold_repairability": "irreparable",
                 "gold_counterexample_eligible": False, "failure_type": "timeout"},
            ])
        scoring[0]["terminal_run_id"] = "forged"
        with self.assertRaisesRegex(M6ExperimentError, "terminal ledger run_id"):
            aggregate_by_experiment(item, ledger, scoring)
        scoring[0]["terminal_run_id"] = ledger[0]["run_id"]
        scoring[1]["failure_type"] = "api_error"
        with self.assertRaisesRegex(M6ExperimentError, "ledger status"):
            aggregate_by_experiment(item, ledger, scoring)


if __name__ == "__main__":
    unittest.main()
