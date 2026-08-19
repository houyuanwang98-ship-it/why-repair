"""Fail-closed, append-only Provider execution primitives for M5/M6 smoke runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Mapping


class ProviderRunnerError(RuntimeError):
    """Raised when execution or evidence preservation cannot be guaranteed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class ProviderRunConfig:
    provider: str
    model: str
    prompt_digest: str
    sampling: Mapping[str, Any]
    max_output_tokens: int
    max_total_tokens: int
    max_calls: int
    max_cost_usd: float
    timeout_seconds: float
    retry_limit: int = 1

    def validate(self) -> None:
        if self.provider != "openai":
            raise ProviderRunnerError("only the audited openai adapter is supported")
        if not self.model or len(self.prompt_digest) != 64:
            raise ProviderRunnerError("model and lowercase SHA-256 prompt_digest are required")
        if any(c not in "0123456789abcdef" for c in self.prompt_digest):
            raise ProviderRunnerError("prompt_digest must be lowercase SHA-256")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in
               (self.max_output_tokens, self.max_total_tokens, self.max_calls)):
            raise ProviderRunnerError("token and call budgets must be positive integers")
        if self.max_cost_usd < 0 or self.timeout_seconds <= 0 or self.retry_limit < 0:
            raise ProviderRunnerError("cost, timeout, and retry budgets are invalid")

    def frozen(self) -> dict[str, Any]:
        self.validate()
        return {
            "provider": self.provider, "model": self.model,
            "prompt_digest": self.prompt_digest, "sampling": dict(self.sampling),
            "max_output_tokens": self.max_output_tokens,
            "budgets": {"max_total_tokens": self.max_total_tokens,
                        "max_calls": self.max_calls, "max_cost_usd": self.max_cost_usd,
                        "timeout_seconds": self.timeout_seconds, "retry_limit": self.retry_limit},
        }


class AppendOnlyEvidenceStore:
    def __init__(self, root: Path):
        self.root = root
        self.raw_dir = root / "raw_responses"
        self.ledger_path = root / "attempt_ledger.jsonl"

    def initialize(self, run_manifest: Mapping[str, Any]) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.root / "run_manifest.json"
        payload = canonical_bytes(dict(run_manifest)) + b"\n"
        if manifest_path.exists() and manifest_path.read_bytes() != payload:
            raise ProviderRunnerError("run manifest is immutable and already differs")
        if not manifest_path.exists():
            manifest_path.write_bytes(payload)

    def append_attempt(self, row: Mapping[str, Any], raw: Mapping[str, Any] | None) -> None:
        attempt_id = row.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            raise ProviderRunnerError("attempt_id is required")
        if raw is not None:
            raw_path = self.raw_dir / f"{attempt_id}.json"
            if raw_path.exists():
                raise ProviderRunnerError("raw response already exists; evidence is append-only")
            raw_path.write_bytes(canonical_bytes(dict(raw)) + b"\n")
        with self.ledger_path.open("ab") as stream:
            stream.write(canonical_bytes(dict(row)) + b"\n")


class ProviderRunner:
    """Execute one assignment through an injected adapter while retaining every attempt."""

    def __init__(self, config: ProviderRunConfig, store: AppendOnlyEvidenceStore,
                 adapter: Callable[..., Mapping[str, Any]], *, execution_enabled: bool = False,
                 clock: Callable[[], float] = time.monotonic):
        config.validate()
        if not execution_enabled:
            raise ProviderRunnerError("real Provider execution requires explicit execution_enabled=True")
        if not os.environ.get("OPENAI_API_KEY"):
            raise ProviderRunnerError("OPENAI_API_KEY is not configured")
        self.config, self.store, self.adapter, self.clock = config, store, adapter, clock

    def run(self, *, run_id: str, sample_id: str, method_id: str, prompt: str,
            input_payload: Mapping[str, Any]) -> dict[str, Any]:
        if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != self.config.prompt_digest:
            raise ProviderRunnerError("prompt bytes do not match frozen prompt_digest")
        fingerprint = digest({"config": self.config.frozen(), "sample_id": sample_id,
                              "method_id": method_id, "input": input_payload})
        self.store.initialize({"schema_version": "provider-run-0.1", "run_id": run_id,
                               "config": self.config.frozen(), "config_digest": digest(self.config.frozen())})
        started = self.clock()
        used_tokens, used_cost = 0, 0.0
        for attempt in range(self.config.retry_limit + 1):
            if attempt >= self.config.max_calls or used_tokens >= self.config.max_total_tokens or used_cost >= self.config.max_cost_usd:
                raise ProviderRunnerError("frozen budget exhausted before next call")
            attempt_id = f"{run_id}-{sample_id}-{method_id}-a{attempt}"
            wall_before = self.clock()
            try:
                raw = dict(self.adapter(model=self.config.model, prompt=prompt,
                                        input_payload=dict(input_payload),
                                        max_output_tokens=self.config.max_output_tokens,
                                        sampling=dict(self.config.sampling)))
                tokens = int(raw["usage"]["total_tokens"])
                cost = float(raw["cost_usd"])
                used_tokens += tokens
                used_cost += cost
                elapsed = self.clock() - started
                if used_tokens > self.config.max_total_tokens or used_cost > self.config.max_cost_usd or elapsed > self.config.timeout_seconds:
                    status, terminal = "budget_exhausted", True
                else:
                    status, terminal = "success", True
                row = {"attempt_id": attempt_id, "run_id": run_id, "sample_id": sample_id,
                       "method_id": method_id, "attempt": attempt, "status": status,
                       "terminal": terminal, "provider_response_id": raw.get("id"),
                       "tokens": tokens, "cost_usd": cost, "latency_seconds": self.clock() - wall_before,
                       "cache_fingerprint": fingerprint, "raw_sha256": digest(raw),
                       "recorded_at": datetime.now(timezone.utc).isoformat()}
                self.store.append_attempt(row, raw)
                return row
            except Exception as exc:
                terminal = attempt == self.config.retry_limit
                row = {"attempt_id": attempt_id, "run_id": run_id, "sample_id": sample_id,
                       "method_id": method_id, "attempt": attempt,
                       "status": "retry_exhausted" if terminal else "api_error", "terminal": terminal,
                       "provider_response_id": None, "tokens": 0, "cost_usd": 0,
                       "latency_seconds": self.clock() - wall_before, "cache_fingerprint": fingerprint,
                       "raw_sha256": None, "error_type": type(exc).__name__,
                       "error_message": str(exc), "recorded_at": datetime.now(timezone.utc).isoformat()}
                self.store.append_attempt(row, None)
                if terminal:
                    return row
        raise AssertionError("unreachable")


def build_openai_adapter(*, input_usd_per_million: float, output_usd_per_million: float,
                         client: Any | None = None) -> Callable[..., Mapping[str, Any]]:
    """Create a Responses API adapter with an explicit, frozen price snapshot."""
    if input_usd_per_million < 0 or output_usd_per_million < 0:
        raise ProviderRunnerError("token prices must be nonnegative")
    if client is None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderRunnerError("openai dependency is not installed") from exc
        client = OpenAI()

    def call(*, model: str, prompt: str, input_payload: Mapping[str, Any],
             max_output_tokens: int, sampling: Mapping[str, Any]) -> Mapping[str, Any]:
        response = client.responses.create(
            model=model,
            input=[{"role": "system", "content": prompt},
                   {"role": "user", "content": json.dumps(input_payload, ensure_ascii=False)}],
            max_output_tokens=max_output_tokens, store=False, **dict(sampling),
        )
        raw = response.model_dump(mode="json")
        usage = raw.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        raw["usage"] = {**usage, "input_tokens": input_tokens, "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens}
        raw["cost_usd"] = (input_tokens * input_usd_per_million
                           + output_tokens * output_usd_per_million) / 1_000_000
        return raw

    return call
