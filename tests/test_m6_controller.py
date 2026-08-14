import unittest
from pathlib import Path

from harness.m6_controller import (
    aggregate_by_experiment, build_controller_manifest, field_completeness_report, freeze_artifacts,
    holm_adjust, paired_bootstrap_difference, validate_controller_manifest,
    validate_run_ledger,
)
from harness.m6_experiments import M6ExperimentError, build_experiment_config


ROOT = Path(__file__).resolve().parents[1]


def config(method):
    return build_experiment_config(
        method, model_id="fixture-model", prompt_digest="p", dataset_digest="d",
        theorem_bank_digest="t", tool_digest="x", token_limit=8000,
        call_limit=4, timeout_seconds=180,
    )


def manifest():
    return build_controller_manifest(
        configs=[config("direct_judgment"), config("full_system")],
        sample_ids=["s1", "s2"], artifacts={"fixture": "a" * 64},
        metric_digest="b" * 64, statistics_digest="c" * 64, bootstrap_seeds=[1, 2, 3],
        m5_gate_digest="d" * 64, signatures={"person_a": "pending_human_signature",
        "person_b_cross_review": "pending_cross_review", "controller": "candidate_unsigned"},
    )


class M6ControllerTest(unittest.TestCase):
    def test_freeze_artifacts_hashes_explicit_files(self):
        frozen = freeze_artifacts(ROOT, ["docs/milestones/M06_person_a_preregistered_protocol.md"])
        self.assertEqual(64, len(next(iter(frozen.values()))))
        with self.assertRaisesRegex(M6ExperimentError, "escapes"):
            freeze_artifacts(ROOT, ["../outside"])

    def test_manifest_binds_samples_configs_and_statistics(self):
        item = manifest()
        self.assertTrue(item["fixture_only"])
        self.assertEqual(2, len(item["configs"]))
        self.assertTrue(item["manifest_id"].startswith("m6-controller-"))
        self.assertEqual(item, validate_controller_manifest(item))
        item["sample_ids"].append("tampered")
        with self.assertRaisesRegex(M6ExperimentError, "mutated"):
            validate_controller_manifest(item)

    def test_formal_manifest_cannot_bypass_closed_gates(self):
        kwargs = dict(
            configs=[config("full_system")], sample_ids=["s1"], artifacts={"fixture": "a" * 64},
            metric_digest="b" * 64, statistics_digest="c" * 64,
            bootstrap_seeds=list(range(10_000)), m5_gate_digest="d" * 64,
            signatures={"person_a": "signed", "person_b_cross_review": "signed", "controller": "signed"},
            fixture_only=False,
        )
        with self.assertRaisesRegex(M6ExperimentError, "M5"):
            build_controller_manifest(**kwargs)
        kwargs["m5_entry_allowed"] = True
        self.assertFalse(build_controller_manifest(**kwargs)["fixture_only"])

    def test_ledger_preserves_failures_retries_cost_and_missing_rows(self):
        item = manifest()
        left, right = [row["experiment_id"] for row in item["configs"]]
        rows = [
            {"run_id": "a0", "experiment_id": left, "sample_id": "s1", "attempt": 0, "status": "api_error", "terminal": False, "tokens": 10, "model_calls": 1, "cost": 0.1, "latency_seconds": 1},
            {"run_id": "a1", "experiment_id": left, "sample_id": "s1", "attempt": 1, "status": "success", "terminal": True, "tokens": 20, "model_calls": 1, "cost": 0.2, "latency_seconds": 2},
            {"run_id": "b", "experiment_id": left, "sample_id": "s2", "attempt": 0, "status": "timeout", "terminal": True, "tokens": 30, "model_calls": 1, "cost": 0.3, "latency_seconds": 180},
            {"run_id": "c", "experiment_id": right, "sample_id": "s1", "attempt": 0, "status": "success", "terminal": True, "tokens": 40, "model_calls": 1, "cost": 0.4, "latency_seconds": 4},
        ]
        report = validate_run_ledger(item, rows)
        self.assertFalse(report["complete"])
        self.assertEqual(1, len(report["missing_assignments"]))
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
        adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertEqual({"a": 0.03, "c": 0.06, "b": 0.06}, adjusted)
        with self.assertRaisesRegex(M6ExperimentError, "finite"):
            paired_bootstrap_difference([float("nan")], [0], seeds=[1])

    def test_aggregate_keeps_infrastructure_failure_in_denominator(self):
        rows = [
            {"experiment_id": "e", "sample_id": "s1", "gold_verdict": "invalid", "predicted_verdict": "invalid",
             "gold_first_error_evaluable": True, "gold_first_error": 1, "predicted_first_error": 1,
             "gold_repairability": "irreparable", "failure_type": None},
            {"experiment_id": "e", "sample_id": "s2", "gold_verdict": "invalid", "predicted_verdict": None,
             "gold_first_error_evaluable": True, "gold_first_error": 1, "predicted_first_error": None,
             "gold_repairability": "irreparable", "failure_type": "timeout"},
        ]
        metrics = aggregate_by_experiment(rows)["e"]
        self.assertEqual(0.5, metrics["first_error_exact_accuracy"]["value"])
        self.assertEqual(0.5, metrics["infrastructure_failure_rate"]["value"])


if __name__ == "__main__":
    unittest.main()
