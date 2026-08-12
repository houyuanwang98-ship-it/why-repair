import hashlib
import json
import unittest

from harness.m3_alpha import (
    AdapterResponse,
    M3AlphaError,
    dependency_edge_metrics,
    evaluate_dataset,
    evaluate_module,
    false_acceptance_rate,
    macro_f1,
    run_module,
    segmentation_metrics,
    validate_module_output,
)


def run_manifest(samples, *, adapter="fixture-adapter", prompt="classification-v0"):
    payload = json.dumps(samples, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "0.3", "run_id": "m3-alpha-test",
        "created_at": "2026-08-11T00:00:00+08:00",
        "controller_version": "0.3", "contract_version": "0.3",
        "input_digest": "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "theorem_bank_digest": None,
        "agents": {"evaluator": adapter, "repair_generator": "not-invoked"},
        "prompt_versions": {"evaluator": prompt, "repair_generator": "not-invoked"},
        "model_parameters": {"model": "fixture-model", "temperature": 0}, "events": [],
    }


class M3AlphaMetricTest(unittest.TestCase):
    def test_segmentation_boundary_f1(self):
        result = segmentation_metrics([[0, 5], [5, 10], [10, 20]], [[0, 5], [5, 20]])
        self.assertEqual(1.0, result["recall"])
        self.assertEqual(0.5, result["precision"])

    def test_segmentation_rejects_gap(self):
        with self.assertRaisesRegex(M3AlphaError, "contiguous"):
            segmentation_metrics([[0, 5], [6, 10]], [[0, 10]])

    def test_macro_f1_includes_missed_and_extra_classes(self):
        result = macro_f1(["claim", "claim", "calculation"], ["claim", "conclusion", "calculation"])
        self.assertEqual({"calculation", "claim", "conclusion"}, set(result["labels"]))
        self.assertLess(result["macro_f1"], 1.0)

    def test_dependency_edges_are_directional(self):
        result = dependency_edge_metrics([[1, 3]], [[2, 3]])
        self.assertEqual(0, result["tp"])
        self.assertEqual(1, result["fp"])

    def test_dependency_metrics_reject_backward_edge(self):
        with self.assertRaisesRegex(M3AlphaError, "earlier"):
            dependency_edge_metrics([[2, 1]], [])

    def test_false_acceptance_uses_only_gold_invalid_denominator(self):
        result = false_acceptance_rate(
            ["accepted", "invalid", "accepted_with_gap"],
            ["invalid", "invalid", "accepted_with_gap"],
        )
        self.assertEqual(0.5, result["false_acceptance_rate"])

    def test_verdict_report_keeps_isolation_mode(self):
        result = evaluate_module(
            "verdict",
            {"verdicts": ["accepted", "invalid"]},
            {"verdicts": ["accepted", "invalid"]},
            upstream_mode="gold_upstream",
        )
        self.assertEqual("gold_upstream", result["upstream_mode"])
        self.assertIn("false_acceptance_rate", result["metrics"])

    def test_dataset_alignment_rejects_missing_prediction(self):
        with self.assertRaisesRegex(M3AlphaError, "missing"):
            evaluate_dataset(
                "localization", [],
                [{"sample_id": "p1", "output": {"first_error_step": 1}}],
                upstream_mode="gold_upstream",
            )

    def test_dataset_edges_do_not_collide_across_samples(self):
        rows = [
            {"sample_id": "p1", "output": {"edges": [[1, 2]]}},
            {"sample_id": "p2", "output": {"edges": [[1, 2]]}},
        ]
        result = evaluate_dataset("dependency", rows, rows, upstream_mode="gold_upstream")
        self.assertEqual(2, result["metrics"]["tp"])


class M3AlphaRunnerTest(unittest.TestCase):
    def test_runner_records_reproducibility_and_usage(self):
        samples = [{"sample_id": "p1", "node_count": 1}]
        result = run_module(
            module="classification", samples=samples,
            adapter=lambda *_: AdapterResponse({"labels": ["claim"]}, input_tokens=3, output_tokens=2, estimated_cost=0.01),
            adapter_id="fixture-adapter", model="fixture-model",
            prompt_version="classification-v0", upstream_mode="gold_upstream",
            run_manifest=run_manifest(samples),
        )
        manifest = result["manifest"]
        self.assertTrue(manifest["input_digest"].startswith("sha256:"))
        self.assertEqual(1, manifest["model_call_count"])
        self.assertEqual(3, manifest["input_tokens"])
        self.assertEqual(2, manifest["output_tokens"])
        self.assertEqual(0.01, manifest["estimated_cost"])
        self.assertEqual("completed", manifest["status"])
        self.assertEqual("0.3", result["run_manifest"]["contract_version"])

    def test_failed_adapter_call_is_preserved(self):
        samples = [{"sample_id": "p1", "node_count": 1}, {"sample_id": "p2", "node_count": 1}]
        def adapter(module, sample):
            if sample["sample_id"] == "p1":
                return AdapterResponse({"labels": ["claim"]}, input_tokens=1)
            raise RuntimeError("provider unavailable")
        result = run_module(
            module="classification", samples=samples, adapter=adapter,
            adapter_id="fixture-adapter", model="fixture-model",
            prompt_version="classification-v0", upstream_mode="gold_upstream",
            run_manifest=run_manifest(samples),
        )
        self.assertEqual("partial", result["manifest"]["status"])
        self.assertEqual(1, result["manifest"]["failed_call_count"])
        self.assertEqual("RuntimeError", result["manifest"]["calls"][1]["error_type"])

    def test_malformed_adapter_output_fails_closed(self):
        samples = [{"sample_id": "p1", "node_count": 1}]
        result = run_module(
            module="classification", samples=samples,
            adapter=lambda *_: AdapterResponse({"labels": ["invented"]}),
            adapter_id="fixture-adapter", model="fixture-model",
            prompt_version="classification-v0", upstream_mode="gold_upstream",
            run_manifest=run_manifest(samples),
        )
        self.assertEqual("failed", result["manifest"]["status"])
        self.assertEqual([], result["predictions"])

    def test_run_manifest_must_bind_exact_input(self):
        samples = [{"sample_id": "p1", "node_count": 1}]
        manifest = run_manifest([{"sample_id": "different", "node_count": 1}])
        with self.assertRaisesRegex(M3AlphaError, "exact module inputs"):
            run_module(
                module="classification", samples=samples,
                adapter=lambda *_: AdapterResponse({"labels": ["claim"]}),
                adapter_id="fixture-adapter", model="fixture-model",
                prompt_version="classification-v0", upstream_mode="gold_upstream",
                run_manifest=manifest,
            )

    def test_run_manifest_must_bind_model(self):
        samples = [{"sample_id": "p1", "node_count": 1}]
        manifest = run_manifest(samples)
        manifest["model_parameters"]["model"] = "other-model"
        with self.assertRaisesRegex(M3AlphaError, "does not match model"):
            run_module(
                module="classification", samples=samples,
                adapter=lambda *_: AdapterResponse({"labels": ["claim"]}),
                adapter_id="fixture-adapter", model="fixture-model",
                prompt_version="classification-v0", upstream_mode="gold_upstream",
                run_manifest=manifest,
            )

    def test_module_contracts_reject_gapped_segmentation(self):
        with self.assertRaisesRegex(M3AlphaError, "contiguous"):
            validate_module_output("segmentation", {"source_length": 10}, {"spans": [[0, 4], [5, 10]]})

    def test_runner_rejects_duplicate_samples(self):
        with self.assertRaisesRegex(M3AlphaError, "unique"):
            run_module(
                module="segmentation", samples=[{"sample_id": "p1"}, {"sample_id": "p1"}],
                adapter=lambda *_: AdapterResponse({}), adapter_id="a", model="m",
                prompt_version="p", upstream_mode="predicted_upstream", run_manifest={},
            )

    def test_unknown_isolation_mode_is_rejected(self):
        with self.assertRaisesRegex(M3AlphaError, "upstream"):
            evaluate_module("classification", {"labels": []}, {"labels": []}, upstream_mode="silent")


if __name__ == "__main__":
    unittest.main()
