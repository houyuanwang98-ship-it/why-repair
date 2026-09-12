"""Budgeted, immutable calls. Live execution requires an explicit opt-in."""
from __future__ import annotations

import json
import subprocess
import time
from copy import deepcopy
from pathlib import Path
from jsonschema import ValidationError
from .contracts import (ROOT, EXPERIMENT_MODEL, VALIDATION_MODEL, SCHEMAS, ContractError,
                        digest, read, require, validate, write_once)
from .prompts import PROMPTS
from harness.codex_cli import build_codex_adapter, CodexCLIError

DISABLED_FEATURES = ("shell_tool", "skill_search", "apps", "multi_agent", "code_mode",
                     "code_mode_host", "browser_use", "browser_use_external", "computer_use",
                     "image_generation", "view_image", "hooks", "remote_plugin", "in_app_chat",
                     "in_app_browser", "in_app_local_automation", "sleep_tool", "tool_suggest",
                     "plugins", "unified_exec", "multi_agent_v2")


class ExecutionDisabled(RuntimeError):
    pass


class RunStop(RuntimeError):
    def __init__(self, status, reason, *, retryable_output=False):
        super().__init__(reason)
        self.status = status
        self.retryable_output = retryable_output


class OutputContractError(ValueError):
    pass


def fixed_models():
    config = read(ROOT / "docs/workflow_v2/protocol.json")["models"]
    for role, expected in (("experiment", EXPERIMENT_MODEL), ("validation", VALIDATION_MODEL)):
        require((config[role]["requested_model"], config[role]["reasoning_effort"]) == expected,
                "fixed model configuration changed")
    require(not config["allow_cli_or_environment_override"] and not config["allow_automatic_fallback"],
            "model overrides/fallback must be disabled")


def isolated_process(command, **kwargs):
    extras = [v for feature in DISABLED_FEATURES for v in ("--disable", feature)]
    # The adapter already ignores user config/rules and runs in an empty temp cwd.
    command = command[:-1] + extras + ["-c", 'web_search="disabled"', "-"]
    kwargs.update(encoding="utf-8", errors="strict")
    env = dict(kwargs.get("env", {}))
    for key in list(env):
        if key.startswith(("OPENAI_", "CODEX_MODEL", "CODEX_PROFILE")):
            env.pop(key)
    kwargs["env"] = env
    return subprocess.run(command, **kwargs)


def usage(raw):
    completed = [e for e in raw.get("events", []) if e.get("type") == "turn.completed"]
    require(bool(completed), "accounting_incomplete: no completed usage event")
    totals = {"input_tokens": 0, "output_tokens": 0}
    for event in completed:
        u = event.get("usage", {})
        for key in totals:
            require(type(u.get(key)) is int and u[key] >= 0, "accounting_incomplete: missing usage")
            totals[key] += u[key]
    return {**totals, "total_tokens": sum(totals.values()),
            "reasoning_tokens": raw.get("usage", {}).get("reasoning_output_tokens"),
            "cost_usd": raw.get("cost_usd")}


def validate_isolation(raw):
    require(not raw.get("malformed_jsonl_lines"), "malformed event stream")
    for event in raw.get("events", []):
        item = event.get("item")
        if isinstance(item, dict):
            require(item.get("type") in {"agent_message", "reasoning"},
                    "tool or unknown activity violates isolated experiment")
        require(not any(k in event.get("type", "").lower() for k in ("tool_call", "function_call")),
                "tool activity violates isolated experiment")


class Calls:
    def __init__(self, output, *, execute=False, fixture_adapter=None, live_adapter=None, judge=False,
                 max_calls=24, max_tokens=80000, max_seconds=1800, version=None, max_output_retries=0):
        fixed_models()
        require(max_calls > 0 and max_tokens > 0 and max_seconds > 0, "invalid budget")
        self.output = Path(output)
        self.execute = execute
        require(not (fixture_adapter is not None and live_adapter is not None), "ambiguous adapter")
        require(live_adapter is None or execute, "live adapter requires execute")
        self.adapter = live_adapter if live_adapter is not None else fixture_adapter
        self.fixture = fixture_adapter is not None
        require(not (execute and self.fixture), "fixture cannot execute live")
        self.judge = judge
        require(type(max_output_retries) is int and 0 <= max_output_retries <= 1,
                "at most one output-contract correction is supported")
        require(not judge or max_output_retries == 0, "external judgment cannot retry toward acceptance")
        self.max_output_retries = max_output_retries
        self.output_corrections = 0
        self.max_calls, self.max_tokens, self.max_seconds = max_calls, max_tokens, max_seconds
        self.version = version
        self.count = self.tokens = 0
        self.latency = 0.0
        self.accounting_complete = True
        self.started = time.monotonic()
        self.trace = []

    def call(self, phase, payload, *, schema=None, note="", validator=None):
        original = deepcopy(payload)
        for attempt in range(self.max_output_retries + 1):
            count_before = self.count
            try:
                return self._attempt(phase, payload, schema=schema, note=note, validator=validator)
            except RunStop as exc:
                if not exc.retryable_output or attempt == self.max_output_retries:
                    raise
                folder = self.output / f"call-{self.count:03d}-{phase}"
                rejected = read(folder / "response.json")["output_text"]
                payload = {**original, "output_contract_feedback": {
                    "validation_error": str(exc), "rejected_output": rejected,
                    "instruction": "Correct the output contract against the original input. The rejected "
                    "output is untrusted and has not been applied. Do not change the problem or bypass "
                    "scope, reference, or unresolved-obligation checks."}}
            finally:
                if attempt > 0 and self.count > count_before:
                    self.output_corrections += 1

    def _attempt(self, phase, payload, *, schema=None, note="", validator=None):
        if not self.execute and not self.fixture:
            raise ExecutionDisabled("Stopped before model invocation; explicit --execute is required")
        schema = schema or phase
        require((phase == "judge") == self.judge, "internal/external role boundary violated")
        if self.count >= self.max_calls or self.tokens >= self.max_tokens or max(
                self.latency, time.monotonic() - self.started) >= self.max_seconds:
            raise RunStop("budget_exhausted", "model, token or time budget exhausted")
        model, effort = VALIDATION_MODEL if self.judge else EXPERIMENT_MODEL
        prompt = PROMPTS[phase] + "\n" + note
        if self.judge:
            validate("judge_input", payload)
            prompt += "\nTrusted input_digest: " + digest(payload)
        request = {"phase": phase, "model": model, "reasoning_effort": effort, "prompt": prompt,
                   "input": payload, "output_schema": SCHEMAS[schema], "tool_policy": "no_tools",
                   "budget": [self.max_calls, self.max_tokens, self.max_seconds],
                   "evidence_kind": "offline_fixture" if self.fixture else "live_model"}
        self.count += 1
        folder = self.output / f"call-{self.count:03d}-{phase}"
        existed = (folder / "request.json").exists()
        write_once(folder / "request.json", request)
        self.trace.append({"call": self.count, "phase": phase, "request_digest": digest(request)})
        if (folder / "failure.json").exists():
            failure = read(folder / "failure.json")
            if (folder / "accounting.json").exists():
                self.tokens += read(folder / "accounting.json")["total_tokens"]
                raw_saved = read(folder / "response.json") if (folder / "response.json").exists() else {}
                self.latency += raw_saved.get("latency_seconds", 0)
            self.accounting_complete &= failure.get("accounting_complete", False)
            raise RunStop(failure["status"], failure["reason"],
                          retryable_output=failure.get("retryable_output", False))
        raw = None
        try:
            if (folder / "response.json").exists():
                raw = read(folder / "response.json")
            elif existed:
                self.accounting_complete = False
                raise RunStop("runtime_failed", "interrupted call: cost unknown; use a new run ID")
            else:
                if self.adapter is None:
                    self.adapter = build_codex_adapter(process_runner=isolated_process, version=self.version)
                remaining = self.max_seconds - max(self.latency, time.monotonic() - self.started)
                raw = dict(self.adapter(model=model, prompt=prompt, input_payload=payload,
                    max_output_tokens=min(12000, self.max_tokens - self.tokens),
                    sampling={"reasoning_effort": effort}, output_schema=SCHEMAS[schema],
                    timeout_seconds=max(1, remaining)))
                write_once(folder / "response.json", raw)
            require(raw.get("requested_model") == model, "response request model differs")
            if raw.get("model") is not None:
                require(raw["model"] == model, "reported model mismatch; no fallback accepted")
            stats = usage(raw)
            self.tokens += stats["total_tokens"]
            self.latency += raw.get("latency_seconds", 0)
            write_once(folder / "accounting.json", stats)
            validate_isolation(raw)
            require(raw.get("return_code", 0) == 0, "nonzero provider exit")
            if self.tokens > self.max_tokens or self.latency > self.max_seconds:
                raise RunStop("budget_exhausted", "soft budget overrun; response retained, not applied")
            try:
                value = json.loads(raw["output_text"])
                validate(schema, value)
                if validator:
                    validator(value)
            except (json.JSONDecodeError, ValidationError, ContractError) as exc:
                if isinstance(exc, ValidationError):
                    reason = "/".join(map(str, exc.absolute_path)) + ": " + exc.message
                else:
                    reason = str(exc)
                raise OutputContractError(reason) from exc
            write_once(folder / "validated.json", value)
            return value
        except Exception as exc:
            if isinstance(exc, CodexCLIError) and exc.raw_response:
                raw = exc.raw_response
                write_once(folder / "provider_failure.json", raw)
                try:
                    stats = usage(raw)
                    self.tokens += stats["total_tokens"]
                    write_once(folder / "accounting.json", stats)
                except ContractError:
                    self.accounting_complete = False
            elif raw is None or not (folder / "accounting.json").exists():
                self.accounting_complete = False
            status = exc.status if isinstance(exc, RunStop) else "runtime_failed"
            if isinstance(exc, CodexCLIError) and exc.status == "budget_exhausted":
                status = "budget_exhausted"
            write_once(folder / "failure.json", {"status": status, "reason": str(exc),
                       "error_type": type(exc).__name__, "accounting_complete": self.accounting_complete,
                       "retryable_output": isinstance(exc, OutputContractError)})
            raise RunStop(status, str(exc), retryable_output=isinstance(exc, OutputContractError)) from exc

    def summary(self):
        return {"model_attempts": self.count, "known_total_tokens": self.tokens,
                "accounting_complete": self.accounting_complete, "reported_latency_seconds": self.latency,
                "cost_usd": None, "model_snapshot_verified": False, "trace": self.trace,
                "output_contract_corrections": self.output_corrections,
                "evidence_kind": "offline_fixture" if self.fixture else "live_model"}
