"""Fail-closed, append-only Codex CLI execution primitives for M5/M6 runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import time
from typing import Any, Callable, Mapping, Sequence

import jsonschema

from harness.codex_cli import CodexCLIError, project_codex_output_schema


class ProviderRunnerError(RuntimeError):
    """Raised when execution or evidence preservation cannot be guaranteed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def make_provider_output_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Project the authoritative schema to Codex structured-output keywords.

    The projected schema constrains generation only. Every parsed response is
    still validated locally against the complete authoritative schema.
    """

    try:
        result = project_codex_output_schema(schema)
    except CodexCLIError as exc:
        raise ProviderRunnerError(str(exc)) from exc
    if result.get("type") != "object":
        raise ProviderRunnerError("provider output schema must remain a top-level object")
    return result


def _nonnegative_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ProviderRunnerError(f"{name} must be a nonnegative number")
    return float(value)


def _safe_identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
        raise ProviderRunnerError(f"{name} must be a path-safe identifier")
    return value


@dataclass(frozen=True)
class ProviderRunConfig:
    provider: str
    model: str
    prompt_digest: str
    sampling: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    provider_output_schema: Mapping[str, Any]
    max_output_tokens: int
    max_total_tokens: int
    max_calls: int
    max_cost_usd: float
    timeout_seconds: float
    prices_usd_per_million: Mapping[str, float]
    repository_commit: str
    sdk_version: str
    run_kind: str
    retry_limit: int = 1

    def validate(self) -> None:
        if self.provider != "codex_cli":
            raise ProviderRunnerError("only the audited codex_cli adapter is supported")
        if not self.model or len(self.prompt_digest) != 64:
            raise ProviderRunnerError("model and lowercase SHA-256 prompt_digest are required")
        if any(c not in "0123456789abcdef" for c in self.prompt_digest):
            raise ProviderRunnerError("prompt_digest must be lowercase SHA-256")
        if self.output_schema.get("type") != "object" or self.provider_output_schema.get("type") != "object":
            raise ProviderRunnerError("top-level object output schemas are required")
        try:
            jsonschema.Draft202012Validator.check_schema(dict(self.output_schema))
            jsonschema.Draft202012Validator.check_schema(dict(self.provider_output_schema))
        except jsonschema.SchemaError as exc:
            raise ProviderRunnerError("output schema is invalid") from exc
        if make_provider_output_schema(self.output_schema) != dict(self.provider_output_schema):
            raise ProviderRunnerError("provider_output_schema is not the audited projection")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in
               (self.max_output_tokens, self.max_total_tokens, self.max_calls)):
            raise ProviderRunnerError("token and call budgets must be positive integers")
        _nonnegative_number(self.max_cost_usd, "max_cost_usd")
        if self.timeout_seconds <= 0 or self.retry_limit < 0:
            raise ProviderRunnerError("cost, timeout, and retry budgets are invalid")
        expected_prices = {"input", "cached_input", "output"}
        if set(self.prices_usd_per_million) != expected_prices:
            raise ProviderRunnerError("price snapshot must contain input, cached_input, and output")
        for key, value in self.prices_usd_per_million.items():
            _nonnegative_number(value, f"price {key}")
        if any(float(value) != 0 for value in self.prices_usd_per_million.values()):
            raise ProviderRunnerError("codex_cli price fields must be zero because per-call USD cost is unavailable")
        if len(self.repository_commit) != 40 or any(c not in "0123456789abcdef" for c in self.repository_commit):
            raise ProviderRunnerError("repository_commit must be a full lowercase Git SHA")
        if not self.sdk_version or not self.run_kind:
            raise ProviderRunnerError("sdk_version and run_kind are required")

    def frozen(self) -> dict[str, Any]:
        self.validate()
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_digest": self.prompt_digest,
            "sampling": dict(self.sampling),
            "output_schema": dict(self.output_schema),
            "output_schema_digest": digest(self.output_schema),
            "provider_output_schema": dict(self.provider_output_schema),
            "provider_output_schema_digest": digest(self.provider_output_schema),
            "max_output_tokens": self.max_output_tokens,
            "budgets": {
                "max_total_tokens": self.max_total_tokens,
                "max_calls": self.max_calls,
                "max_cost_usd": self.max_cost_usd,
                "cost_budget_applicable": False,
                "timeout_seconds": self.timeout_seconds,
                "retry_limit_per_assignment": self.retry_limit,
            },
            "prices_usd_per_million": dict(self.prices_usd_per_million),
            "repository_commit": self.repository_commit,
            "sdk_version": self.sdk_version,
            "run_kind": self.run_kind,
        }


class AppendOnlyEvidenceStore:
    def __init__(self, root: Path):
        self.root = root
        self.request_dir = root / "raw_requests"
        self.response_dir = root / "raw_responses"
        self.input_dir = root / "frozen_inputs"
        self.ledger_path = root / "attempt_ledger.jsonl"

    @staticmethod
    def _write_immutable(path: Path, payload: bytes) -> None:
        if path.exists() and path.read_bytes() != payload:
            raise ProviderRunnerError(f"immutable evidence already differs: {path}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def initialize(self, run_manifest: Mapping[str, Any], *, prompt: str,
                   assignments: Sequence[Mapping[str, Any]]) -> None:
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self._write_immutable(self.root / "run_manifest.json", canonical_bytes(dict(run_manifest)) + b"\n")
        self._write_immutable(self.input_dir / "prompt.txt", prompt.encode("utf-8"))
        assignment_payload = b"".join(canonical_bytes(dict(row)) + b"\n" for row in assignments)
        self._write_immutable(self.input_dir / "assignments.jsonl", assignment_payload)

    def attempt_ids(self) -> set[str]:
        if not self.ledger_path.exists():
            return set()
        rows = []
        for line_number, line in enumerate(self.ledger_path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ProviderRunnerError(f"ledger line {line_number} is invalid JSON") from exc
            attempt_id = row.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise ProviderRunnerError(f"ledger line {line_number} has no attempt_id")
            rows.append(attempt_id)
        if len(rows) != len(set(rows)):
            raise ProviderRunnerError("attempt ledger contains duplicate attempt IDs")
        return set(rows)

    def reserve_request(self, attempt_id: str, request: Mapping[str, Any]) -> str:
        if attempt_id in self.attempt_ids():
            raise ProviderRunnerError(f"attempt already exists in ledger: {attempt_id}")
        path = self.request_dir / f"{attempt_id}.json"
        if path.exists():
            raise ProviderRunnerError(f"attempt request already exists: {attempt_id}")
        payload = canonical_bytes(dict(request)) + b"\n"
        path.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def append_attempt(self, row: Mapping[str, Any], raw: Mapping[str, Any] | None) -> None:
        attempt_id = row.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            raise ProviderRunnerError("attempt_id is required")
        if attempt_id in self.attempt_ids():
            raise ProviderRunnerError(f"attempt already exists in ledger: {attempt_id}")
        if not (self.request_dir / f"{attempt_id}.json").is_file():
            raise ProviderRunnerError("raw request must be reserved before recording an attempt")
        if raw is not None:
            raw_path = self.response_dir / f"{attempt_id}.json"
            if raw_path.exists():
                raise ProviderRunnerError("raw response already exists; evidence is append-only")
            raw_path.write_bytes(canonical_bytes(dict(raw)) + b"\n")
        with self.ledger_path.open("ab") as stream:
            stream.write(canonical_bytes(dict(row)) + b"\n")

    def finalize(self, summary: Mapping[str, Any]) -> None:
        self._write_immutable(self.root / "run_summary.json", canonical_bytes(dict(summary)) + b"\n")


class ProviderRunner:
    """Execute a batch while retaining every request, response, failure and retry."""

    def __init__(self, config: ProviderRunConfig, store: AppendOnlyEvidenceStore,
                 adapter: Callable[..., Mapping[str, Any]], *, execution_enabled: bool = False,
                 clock: Callable[[], float] = time.monotonic):
        config.validate()
        if not execution_enabled:
            raise ProviderRunnerError("real Codex execution requires explicit execution_enabled=True")
        self.config, self.store, self.adapter, self.clock = config, store, adapter, clock
        self.batch_started = self.clock()
        self.used_input_tokens = 0
        self.used_cached_input_tokens = 0
        self.used_output_tokens = 0
        self.used_total_tokens = 0
        self.used_cost = 0.0
        self.cost_tracking_available = True
        self.used_calls = 0
        self.active_run_id: str | None = None

    @staticmethod
    def _validate_assignments(assignments: Sequence[Mapping[str, Any]]) -> None:
        if not assignments:
            raise ProviderRunnerError("at least one assignment is required")
        identities = []
        for row in assignments:
            if set(row) != {"sample_id", "method_id", "input_payload"}:
                raise ProviderRunnerError("assignment must contain sample_id, method_id, and input_payload")
            _safe_identifier(row["sample_id"], "sample_id")
            _safe_identifier(row["method_id"], "method_id")
            if not isinstance(row["input_payload"], Mapping):
                raise ProviderRunnerError("assignment input_payload must be an object")
            identities.append((row["sample_id"], row["method_id"]))
        if len(identities) != len(set(identities)):
            raise ProviderRunnerError("duplicate sample/method assignments are forbidden")

    def _manifest(self, run_id: str, prompt: str,
                  assignments: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": "provider-run-0.2",
            "run_id": run_id,
            "config": self.config.frozen(),
            "config_digest": digest(self.config.frozen()),
            "inputs": {
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "assignments_digest": digest([dict(row) for row in assignments]),
                "assignment_count": len(assignments),
            },
            "environment": {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
            },
        }

    def _budget_exceeded_after_response(self) -> str | None:
        if self.used_total_tokens > self.config.max_total_tokens:
            return "max_total_tokens"
        if (self.cost_tracking_available and self.config.max_cost_usd > 0
                and self.used_cost > self.config.max_cost_usd):
            return "max_cost_usd"
        if self.clock() - self.batch_started > self.config.timeout_seconds:
            return "timeout_seconds"
        return None

    def _budget_exhausted(self) -> str | None:
        if self.used_calls >= self.config.max_calls:
            return "max_calls"
        if self.used_total_tokens >= self.config.max_total_tokens:
            return "max_total_tokens"
        if (self.cost_tracking_available and self.config.max_cost_usd > 0
                and self.used_cost >= self.config.max_cost_usd):
            return "max_cost_usd"
        if self.clock() - self.batch_started >= self.config.timeout_seconds:
            return "timeout_seconds"
        return None

    @staticmethod
    def _usage(raw: Mapping[str, Any]) -> tuple[int, int, int, int]:
        usage = raw.get("usage")
        if not isinstance(usage, Mapping):
            raise ValueError("response usage is missing")
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        details = usage.get("input_tokens_details") or {}
        cached_tokens = int(details.get("cached_tokens") or 0) if isinstance(details, Mapping) else 0
        total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
        if min(input_tokens, output_tokens, cached_tokens, total_tokens) < 0 or cached_tokens > input_tokens:
            raise ValueError("response token usage is invalid")
        return input_tokens, cached_tokens, output_tokens, total_tokens

    def _consume(self, raw: Mapping[str, Any]) -> tuple[int, int, int, int, float | None]:
        input_tokens, cached_tokens, output_tokens, total_tokens = self._usage(raw)
        raw_cost = raw.get("cost_usd")
        cost = None if raw_cost is None else _nonnegative_number(raw_cost, "response cost_usd")
        self.used_input_tokens += input_tokens
        self.used_cached_input_tokens += cached_tokens
        self.used_output_tokens += output_tokens
        self.used_total_tokens += total_tokens
        if cost is None:
            self.cost_tracking_available = False
        else:
            self.used_cost += cost
        return input_tokens, cached_tokens, output_tokens, total_tokens, cost

    def _request(self, *, attempt_id: str, run_id: str, sample_id: str,
                 method_id: str, prompt: str, input_payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "attempt_id": attempt_id,
            "run_id": run_id,
            "sample_id": sample_id,
            "method_id": method_id,
            "provider": self.config.provider,
            "model": self.config.model,
            "runtime": "codex_cli",
            "credential_mode": "saved_codex_cli_auth",
            "prompt": prompt,
            "input_payload": dict(input_payload),
            "output_schema": dict(self.config.provider_output_schema),
            "max_output_tokens": self.config.max_output_tokens,
            "sampling": dict(self.config.sampling),
            "ephemeral": True,
            "sandbox": "read-only",
            "timeout_seconds": self.config.timeout_seconds,
        }

    def _row(self, *, attempt_id: str, run_id: str, sample_id: str, method_id: str,
             attempt: int, status: str, terminal: bool, retry_of: str | None,
             request_sha256: str, started_at: str, wall_before: float,
             raw: Mapping[str, Any] | None = None,
             usage: tuple[int, int, int, int, float | None] | None = None,
             error: Exception | None = None, budget_reason: str | None = None,
             failure_stage: str | None = None) -> dict[str, Any]:
        input_tokens, cached_tokens, output_tokens, total_tokens, cost = usage or (0, 0, 0, 0, None)
        ended_at = datetime.now(timezone.utc).isoformat()
        fingerprint = digest({"config": self.config.frozen(), "sample_id": sample_id,
                              "method_id": method_id, "request_sha256": request_sha256})
        return {
            "attempt_id": attempt_id,
            "run_id": run_id,
            "sample_id": sample_id,
            "method_id": method_id,
            "attempt": attempt,
            "retry_of": retry_of,
            "status": status,
            "terminal": terminal,
            "provider": self.config.provider,
            "requested_model": self.config.model,
            "returned_model": raw.get("model") if raw else None,
            "provider_response_id": raw.get("id") if raw else None,
            "codex_thread_id": raw.get("codex_thread_id") if raw else None,
            "codex_cli_version": raw.get("codex_cli_version") if raw else None,
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost,
            "started_at": started_at,
            "ended_at": ended_at,
            "latency_seconds": self.clock() - wall_before,
            "cache_fingerprint": fingerprint,
            "request_sha256": request_sha256,
            "raw_response_sha256": digest(raw) if raw else None,
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None,
            "failure_stage": failure_stage,
            "budget_reason": budget_reason,
            "recorded_at": ended_at,
        }

    def _run_one(self, *, run_id: str, sample_id: str, method_id: str, prompt: str,
                 input_payload: Mapping[str, Any]) -> dict[str, Any]:
        previous_attempt: str | None = None
        for attempt in range(self.config.retry_limit + 1):
            attempt_id = f"{run_id}-{sample_id}-{method_id}-a{attempt}"
            request = self._request(attempt_id=attempt_id, run_id=run_id, sample_id=sample_id,
                                    method_id=method_id, prompt=prompt, input_payload=input_payload)
            request_sha256 = self.store.reserve_request(attempt_id, request)
            started_at = datetime.now(timezone.utc).isoformat()
            wall_before = self.clock()
            budget_reason = self._budget_exhausted()
            if budget_reason:
                row = self._row(attempt_id=attempt_id, run_id=run_id, sample_id=sample_id,
                                method_id=method_id, attempt=attempt, status="budget_exhausted",
                                terminal=True, retry_of=previous_attempt, request_sha256=request_sha256,
                                started_at=started_at, wall_before=wall_before, budget_reason=budget_reason)
                self.store.append_attempt(row, None)
                return row
            self.used_calls += 1
            try:
                raw = dict(self.adapter(model=self.config.model, prompt=prompt,
                                        input_payload=dict(input_payload),
                                        max_output_tokens=self.config.max_output_tokens,
                                        sampling=dict(self.config.sampling),
                                        output_schema=dict(self.config.provider_output_schema),
                                        timeout_seconds=self.config.timeout_seconds))
            except Exception as exc:
                raw_error = getattr(exc, "raw_response", None)
                usage = None
                if isinstance(raw_error, Mapping):
                    try:
                        usage = self._consume(raw_error)
                    except (TypeError, ValueError, ProviderRunnerError):
                        usage = None
                is_timeout = getattr(exc, "status", None) == "timeout" or "timeout" in type(exc).__name__.lower()
                retryable = getattr(exc, "retryable", True)
                terminal = (not retryable or attempt == self.config.retry_limit
                            or self._budget_exhausted() is not None)
                requested_status = getattr(exc, "status", None)
                status = (
                    requested_status
                    if terminal and not retryable and isinstance(requested_status, str)
                    else "retry_exhausted" if terminal
                    else "timeout" if is_timeout
                    else "api_error"
                )
                row = self._row(attempt_id=attempt_id, run_id=run_id, sample_id=sample_id,
                                method_id=method_id, attempt=attempt, status=status, terminal=terminal,
                                retry_of=previous_attempt, request_sha256=request_sha256,
                                started_at=started_at, wall_before=wall_before,
                                raw=raw_error if isinstance(raw_error, Mapping) else None,
                                usage=usage, error=exc,
                                budget_reason=self._budget_exhausted(),
                                failure_stage=getattr(
                                    exc, "failure_stage", "timeout" if is_timeout else "codex_cli"))
                self.store.append_attempt(
                    row, raw_error if isinstance(raw_error, Mapping) else None)
                if terminal:
                    return row
                previous_attempt = attempt_id
                continue
            usage: tuple[int, int, int, int, float | None] | None = None
            try:
                usage = self._consume(raw)
                parsed = json.loads(raw["output_text"])
                if not isinstance(parsed, dict):
                    raise ValueError("structured output is not a JSON object")
                jsonschema.validate(parsed, self.config.output_schema)
                raw["parsed_output"] = parsed
                budget_reason = self._budget_exceeded_after_response()
                status = "budget_exhausted" if budget_reason else "success"
                row = self._row(attempt_id=attempt_id, run_id=run_id, sample_id=sample_id,
                                method_id=method_id, attempt=attempt, status=status, terminal=True,
                                retry_of=previous_attempt, request_sha256=request_sha256,
                                started_at=started_at, wall_before=wall_before, raw=raw, usage=usage,
                                budget_reason=budget_reason)
                self.store.append_attempt(row, raw)
                return row
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
                if usage is None:
                    try:
                        usage = self._consume(raw)
                    except (TypeError, ValueError, ProviderRunnerError):
                        usage = (0, 0, 0, 0, None)
                terminal = attempt == self.config.retry_limit or self._budget_exhausted() is not None
                row = self._row(attempt_id=attempt_id, run_id=run_id, sample_id=sample_id,
                                method_id=method_id, attempt=attempt,
                                status="retry_exhausted" if terminal else "schema_invalid",
                                terminal=terminal, retry_of=previous_attempt,
                                request_sha256=request_sha256, started_at=started_at,
                                wall_before=wall_before, raw=raw, usage=usage, error=exc,
                                budget_reason=self._budget_exhausted(), failure_stage="schema_invalid")
                self.store.append_attempt(row, raw)
                if terminal:
                    return row
                previous_attempt = attempt_id
        raise AssertionError("unreachable")

    def run_batch(self, *, run_id: str, prompt: str,
                  assignments: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        self._validate_assignments(assignments)
        _safe_identifier(run_id, "run_id")
        if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != self.config.prompt_digest:
            raise ProviderRunnerError("prompt bytes do not match frozen prompt_digest")
        if self.active_run_id is not None:
            raise ProviderRunnerError("ProviderRunner instances execute exactly one frozen batch")
        self.active_run_id = run_id
        manifest = self._manifest(run_id, prompt, assignments)
        self.store.initialize(manifest, prompt=prompt, assignments=assignments)
        rows = [self._run_one(run_id=run_id, sample_id=row["sample_id"],
                              method_id=row["method_id"], prompt=prompt,
                              input_payload=row["input_payload"])
                for row in assignments]
        summary = {
            "schema_version": "provider-run-summary-0.2",
            "run_id": run_id,
            "assignment_count": len(assignments),
            "terminal_assignment_count": sum(row["terminal"] for row in rows),
            "status_counts": {status: sum(row["status"] == status for row in rows)
                              for status in sorted({row["status"] for row in rows})},
            "attempt_count": len(self.store.attempt_ids()),
            "input_tokens": self.used_input_tokens,
            "cached_input_tokens": self.used_cached_input_tokens,
            "output_tokens": self.used_output_tokens,
            "total_tokens": self.used_total_tokens,
            "cost_usd": self.used_cost if self.cost_tracking_available else None,
            "cost_tracking_available": self.cost_tracking_available,
            "billing_mode": "saved_codex_cli_auth_per_call_cost_unavailable",
            "model_calls": self.used_calls,
            "elapsed_seconds": self.clock() - self.batch_started,
            "scientific_claim_allowed": False,
        }
        self.store.finalize(summary)
        return rows

    def run(self, *, run_id: str, sample_id: str, method_id: str, prompt: str,
            input_payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.run_batch(run_id=run_id, prompt=prompt, assignments=[{
            "sample_id": sample_id, "method_id": method_id, "input_payload": dict(input_payload),
        }])[0]
