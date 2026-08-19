import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness.provider_runner import (AppendOnlyEvidenceStore, ProviderRunConfig, ProviderRunner,
                                     ProviderRunnerError, build_openai_adapter)


PROMPT = "repair this proof"


def config(**changes):
    values = dict(provider="openai", model="fixture-model",
                  prompt_digest=hashlib.sha256(PROMPT.encode()).hexdigest(), sampling={"temperature": 0},
                  output_schema={"type": "object", "additionalProperties": True},
                  max_output_tokens=100, max_total_tokens=200, max_calls=2,
                  max_cost_usd=1.0, timeout_seconds=30, retry_limit=1)
    values.update(changes)
    return ProviderRunConfig(**values)


class ProviderRunnerTest(unittest.TestCase):
    def test_execution_fails_closed_without_flag_or_key(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AppendOnlyEvidenceStore(Path(directory))
            with self.assertRaisesRegex(ProviderRunnerError, "execution_enabled"):
                ProviderRunner(config(), store, lambda **_: {})
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ProviderRunnerError, "OPENAI_API_KEY"):
                    ProviderRunner(config(), store, lambda **_: {}, execution_enabled=True)

    def test_success_preserves_manifest_raw_response_and_ledger(self):
        raw = {"id": "resp_fixture", "usage": {"total_tokens": 12}, "cost_usd": 0.02,
               "output_text": "{\"patch\": \"fixture\"}",
               "output": {"patch": "fixture"}}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
            root = Path(directory)
            runner = ProviderRunner(config(), AppendOnlyEvidenceStore(root), lambda **_: raw,
                                    execution_enabled=True)
            row = runner.run(run_id="r1", sample_id="s1", method_id="full_system",
                             prompt=PROMPT, input_payload={"proof": "x=x"})
            self.assertEqual("success", row["status"])
            stored = json.loads((root / "raw_responses/r1-s1-full_system-a0.json").read_text())
            self.assertEqual(raw, {key: value for key, value in stored.items() if key != "parsed_output"})
            self.assertEqual({"patch": "fixture"}, stored["parsed_output"])
            self.assertEqual(1, len((root / "attempt_ledger.jsonl").read_text().splitlines()))
            self.assertNotIn("test-only", (root / "run_manifest.json").read_text())

    def test_failures_are_retained_and_retry_exhaustion_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
            runner = ProviderRunner(config(), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: (_ for _ in ()).throw(RuntimeError("offline")),
                                    execution_enabled=True)
            row = runner.run(run_id="r2", sample_id="s2", method_id="full_system",
                             prompt=PROMPT, input_payload={})
            lines = [json.loads(x) for x in (Path(directory) / "attempt_ledger.jsonl").read_text().splitlines()]
            self.assertEqual(["api_error", "retry_exhausted"], [x["status"] for x in lines])
            self.assertTrue(row["terminal"])

    def test_prompt_and_budget_are_bound(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}):
            runner = ProviderRunner(config(max_total_tokens=5), AppendOnlyEvidenceStore(Path(directory)),
                                    lambda **_: {"id": "x", "usage": {"total_tokens": 6}, "cost_usd": 0,
                                                  "output_text": "{}"},
                                    execution_enabled=True)
            with self.assertRaisesRegex(ProviderRunnerError, "prompt bytes"):
                runner.run(run_id="r", sample_id="s", method_id="m", prompt="changed", input_payload={})
            row = runner.run(run_id="r", sample_id="s", method_id="m", prompt=PROMPT, input_payload={})
            self.assertEqual("budget_exhausted", row["status"])

    def test_openai_adapter_records_exact_usage_and_frozen_price(self):
        class Response:
            output_text = "{}"
            def model_dump(self, **_):
                return {"id": "resp", "usage": {"input_tokens": 100, "output_tokens": 50}}
        class Responses:
            def create(self, **kwargs):
                self.kwargs = kwargs
                return Response()
        class Client:
            responses = Responses()
        adapter = build_openai_adapter(input_usd_per_million=2, output_usd_per_million=10,
                                       client=Client())
        raw = adapter(model="m", prompt="p", input_payload={"x": 1}, max_output_tokens=20,
                      sampling={"temperature": 0}, output_schema={"type": "object"})
        self.assertEqual(150, raw["usage"]["total_tokens"])
        self.assertAlmostEqual(0.0007, raw["cost_usd"])


if __name__ == "__main__":
    unittest.main()
