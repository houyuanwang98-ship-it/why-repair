#!/usr/bin/env python3
"""Run auditable Codex CLI batches that proxy, but never impersonate, human review."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"
M7 = ROOT / "data/benchmarks/m7/opc_250_v0_2"
M7_HUMAN = ROOT / "human_review/m7_opc_250_v0_2"
M7_PROXY_PARTIAL = ROOT / "data/benchmarks/m7/codex_ai_proxy_partial_20260820"
M7_PROXY_CHECKPOINTS = ROOT / "data/benchmarks/m7/codex_ai_proxy_checkpoints_20260820"
M7_BLIND_FULL = ROOT / "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_full_20260821"
M7_BLIND_TOOL_FREE_RERUN = (
    ROOT / "data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_rerun_20260821"
)
M7_THEOREM_AUDIT = ROOT / "data/benchmarks/m7/audits/m7_theorem_verification_20260821.json"
M5_RUNTIME = ROOT / "data/benchmarks/m5/codex_cli_runtime_smoke_v0_1/successful_and_budget_bound"
ISOLATED_TASKS = {"m5_runtime_review", "m7_blind", "m7_adjudication"}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError(f"refusing to overwrite differing evidence: {path}")
        return
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o644), "wb") as handle:
        handle.write(data)


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def m5_rows() -> list[dict[str, Any]]:
    source = {}
    for line in (ROOT / "data/benchmarks/m2/pilot_50.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        source[row["proof_id"]] = row
    rows = []
    for completion_path in sorted(M5.glob("*.completion.json")):
        proof_id = completion_path.name.removesuffix(".completion.json")
        patches = []
        for patch_path in (M5 / f"{proof_id}.patch.json", M5 / f"{proof_id}.patch.r2.json"):
            if patch_path.exists():
                patches.append({
                    "path": str(patch_path.relative_to(ROOT)),
                    "sha256": sha256_bytes(patch_path.read_bytes()),
                    "patch": json.loads(patch_path.read_text(encoding="utf-8")),
                })
        input_path = M5 / f"{proof_id}.input.json"
        rows.append({
            "proof_id": proof_id,
            "frozen_source": source[proof_id],
            "repair_input": json.loads(input_path.read_text(encoding="utf-8")),
            "patch_sequence": patches,
            "completion": json.loads(completion_path.read_text(encoding="utf-8")),
        })
    if len(rows) != 36:
        raise RuntimeError(f"expected 36 M5 cases, found {len(rows)}")
    return rows


def m5_runtime_review_rows() -> list[dict[str, Any]]:
    """Build a no-Gold review packet for the three real Codex generator outputs."""
    source = {}
    for line in (ROOT / "data/benchmarks/m2/pilot_50.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        source[row["proof_id"]] = row
    generated_paths = {
        "m2-011": M5_RUNTIME / "evidence/raw_responses/m5-codex-smoke-20260820-v4-m2-011-full_system-a0.json",
        "m2-018": M5_RUNTIME / "evidence/raw_responses/m5-codex-smoke-20260820-v4-m2-018-full_system-a0.json",
        "m2-034": M5_RUNTIME / "evidence-m2-034-only/raw_responses/m5-codex-smoke-20260820-v4-m2-034-m2-034-full_system-a0.json",
    }
    ledger_rows: dict[str, dict[str, Any]] = {}
    for ledger_path in (
        M5_RUNTIME / "evidence/attempt_ledger.jsonl",
        M5_RUNTIME / "evidence-m2-034-only/attempt_ledger.jsonl",
    ):
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ledger_rows[row["sample_id"]] = row
    rows = []
    for proof_id in ("m2-011", "m2-018", "m2-034"):
        raw_path = generated_paths[proof_id]
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        input_path = M5 / f"{proof_id}.input.json"
        rows.append({
            "proof_id": proof_id,
            "original_problem": source[proof_id],
            "frozen_generator_input": json.loads(input_path.read_text(encoding="utf-8")),
            "generated_patch": raw["parsed_output"],
            "generator_evidence": {
                "raw_response_path": str(raw_path.relative_to(ROOT)),
                "raw_response_sha256": sha256_bytes(raw_path.read_bytes()),
                "codex_thread_id": raw["codex_thread_id"],
                "usage": raw["usage"],
                "terminal_status": ledger_rows[proof_id]["status"],
                "budget_reason": ledger_rows[proof_id]["budget_reason"],
            },
        })
    return rows


def m7_rows() -> list[dict[str, Any]]:
    candidates = {}
    for line in (M7 / "candidate.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        candidates[row["case_id"]] = row
    annotations_doc = json.loads((M7 / "node_annotations.json").read_text(encoding="utf-8"))
    annotations = {row["case_id"]: row for row in annotations_doc["rows"]}
    inherited = json.loads((M7 / "inherited_human_review.json").read_text(encoding="utf-8"))
    reviewed = {row["new_case_id"] for row in inherited["rows"]}
    supplemental = json.loads(
        (M7_HUMAN / "supplemental_review_batch_001_adjudicated.json").read_text(encoding="utf-8"))
    reviewed.update(row["case_id"] for row in supplemental["rows"])
    provisional_doc = json.loads((M7 / "codex_provisional_manual_mappings.json").read_text(encoding="utf-8"))
    provisional = {row["case_id"] for row in provisional_doc["rows"]}
    pending = {
        row["case_id"] for row in annotations_doc["rows"]
        if row["proof_verdict"] == "incorrect"
        and row["location_provenance"] == "opc_llm_judgment"
        and row["case_id"] not in reviewed
    }
    selected = sorted(pending | provisional)
    if len(pending) != 141 or len(provisional) != 3 or len(selected) != 144:
        raise RuntimeError(
            f"unexpected M7 scope: pending={len(pending)}, provisional={len(provisional)}, total={len(selected)}")
    rows = []
    for case_id in selected:
        annotation = annotations[case_id]
        candidate = candidates[case_id]
        rows.append({
            "case_id": case_id,
            "problem": candidate["problem"],
            "frozen_human_proof_verdict": annotation["proof_verdict"],
            "proof_nodes": annotation["proof_nodes"],
            "candidate_mapping": {
                "first_error_node": annotation["first_error_node"],
                "error_type": annotation["error_type"],
                "error_description": annotation.get("error_description"),
                "location_provenance": annotation["location_provenance"],
                "category_provenance": annotation["category_provenance"],
            },
            "scope": "codex_provisional_confirmation" if case_id in provisional else "pending_ai_localized_mapping",
        })
    return rows


def m7_blind_rows() -> list[dict[str, Any]]:
    """Project corrected/undetermined first-pass cases without leaking their mappings."""
    first_pass: dict[str, dict[str, Any]] = {}
    for evidence_dir in (M7_PROXY_PARTIAL, M7_PROXY_CHECKPOINTS):
        for path in sorted(evidence_dir.rglob("last_message.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            for row in document["rows"]:
                case_id = row["case_id"]
                if case_id in first_pass:
                    raise RuntimeError(f"duplicate completed first-pass case: {case_id}")
                first_pass[case_id] = row
    selected = {
        case_id for case_id, row in first_pass.items()
        if row["review_status"] in {"corrected", "undetermined"}
    }
    rows = [
        {
            "case_id": row["case_id"],
            "problem": row["problem"],
            "proof_nodes": row["proof_nodes"],
        }
        for row in m7_rows()
        if row["case_id"] in selected
    ]
    if len(first_pass) != 144 or len(selected) != 124 or len(rows) != 124:
        raise RuntimeError(
            f"unexpected M7 blind scope: first_pass={len(first_pass)}, "
            f"selected={len(selected)}, projected={len(rows)}"
        )
    return rows


def _completed_output_rows(*evidence_dirs: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for evidence_dir in evidence_dirs:
        for path in sorted(evidence_dir.rglob("last_message.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            for row in document["rows"]:
                case_id = row["case_id"]
                if case_id in rows:
                    raise RuntimeError(f"duplicate completed evidence case: {case_id}")
                rows[case_id] = row
    return rows


def _first_pass_assessment(row: dict[str, Any]) -> str:
    if row["review_status"] == "undetermined":
        return "undetermined"
    if row["first_error_node"] in {"none", "no_error"} or row["error_type"] == "no_error":
        return "valid_no_error"
    return "invalid_localized"


def m7_adjudication_rows() -> list[dict[str, Any]]:
    """Build a no-Gold packet for conflicts between the two AI mapping passes."""
    first = _completed_output_rows(M7_PROXY_PARTIAL, M7_PROXY_CHECKPOINTS)
    second = _completed_output_rows(M7_BLIND_FULL)
    tool_free_rerun = _completed_output_rows(M7_BLIND_TOOL_FREE_RERUN)
    second.update(tool_free_rerun)
    theorem_rows = {
        row["case_id"]: row
        for row in json.loads(M7_THEOREM_AUDIT.read_text(encoding="utf-8"))["rows"]
    }
    rows = []
    for source in m7_blind_rows():
        case_id = source["case_id"]
        first_row = first[case_id]
        second_row = second[case_id]
        first_assessment = _first_pass_assessment(first_row)
        second_assessment = second_row["proof_assessment"]
        reasons = []
        if first_assessment != second_assessment:
            reasons.append("assessment_disagreement")
        if (first_assessment == second_assessment == "invalid_localized"
                and first_row["first_error_node"] != second_row["first_error_node"]):
            reasons.append("first_error_node_disagreement")
        if "undetermined" in {first_assessment, second_assessment}:
            reasons.append("undetermined_in_one_or_more_passes")
        if not reasons:
            continue
        rows.append({
            "case_id": case_id,
            "problem": source["problem"],
            "proof_nodes": source["proof_nodes"],
            "adjudication_reasons": reasons,
            "first_pass_proposal": first_row,
            "second_pass_proposal": second_row,
            "second_pass_source": (
                "tool_free_eight_case_rerun"
                if case_id in tool_free_rerun
                else "full_blind_second_pass"
            ),
            "verified_theorem_evidence": theorem_rows.get(case_id),
        })
    if len(rows) != 49:
        raise RuntimeError(f"expected 49 M7 adjudication cases, found {len(rows)}")
    return rows


M5_INSTRUCTIONS = """You are a Codex AI proxy reviewer, not a human reviewer and not a Gold authority.
Independently audit each supplied natural-language algebra proof and its complete patch sequence.
Use a dependency-guided obligation check: identify the exact failed edge; distinguish a locally
repairable gap from a false theorem; verify every replacement calculation; reject theorem or
assumption changes; check descendants after every edit; and require operational minimality.
For a false theorem, accept only mark_irreparable unless a theorem change was authorized (none is).
Do not defer to any historical human decision and do not invent evidence. Return exactly one row
per supplied proof_id, in input order, conforming to the output schema. Chinese or English is fine.
"""


M7_INSTRUCTIONS = """You are a Codex AI proxy mapping reviewer, not a human reviewer and not a Gold authority.
The frozen human proof verdict is incorrect; your task is to locate the earliest genuinely failed
dependency edge in the supplied proof. Read the full proof, not only the proposed node. A terse but
standard algebraic step is not a proof gap merely because it lacks expanded arithmetic. Confirm the
candidate only if every earlier node is valid and sufficiently justified. Otherwise correct it.
Use proof_end when the proof simply stops before supplying the required construction or argument.
Use a specific error type instead of other when possible. The reason must identify the local
premises, claimed conclusion, and why the inference fails. Give a minimal repair direction, not a
rewritten theorem. If the first error cannot be responsibly located, use review_status=undetermined,
first_error_node=proof_end, error_type=undetermined, and explain why. Return exactly one row per
supplied case_id, in input order, conforming to the output schema. Chinese or English is fine.
"""


M7_BLIND_INSTRUCTIONS = """You are an isolated second-pass Codex AI proof auditor, not a human
reviewer and not a Gold authority. You receive only the problem and ordered proof nodes. You do not
receive any earlier verdict, candidate mapping, first-pass output, or frozen Gold. Do not inspect
the repository, local files, tools, or the web; decide only from the supplied mathematical text and
standard mathematical knowledge.

For each case, build the direct dependency route to the target and check nodes in order. Locate the
earliest genuinely failed inference edge, not the first terse sentence. Standard one-step algebra
is directly justified when its premises suffice. Distinguish a repairable omitted bridge, a missing
premise, theorem misuse, an invalid transformation, a false local claim, a false theorem, a target
mismatch, and a proof that simply ends without the required argument. Failure to find a
counterexample is not proof. Do not add assumptions or change the theorem.

Use proof_assessment=invalid_localized only when the exact first failure is supported. Use
valid_no_error with first_error_node=no_error and error_type=no_error when the proof is valid and
complete. Use undetermined with both fields set to undetermined when the supplied text cannot
responsibly decide the obligation. If resolving the case genuinely depends on verifying a named
theorem, set theorem_dependency_required=true and identify its statement and conditions; do not use
that flag for direct calculations or target comparisons. Return exactly one row per supplied
case_id, in input order, conforming to the output schema. Chinese or English is fine.
"""


M7_ADJUDICATION_INSTRUCTIONS = """You are a third-pass Codex AI adjudicator, not a human reviewer
and not a Gold authority. Each case contains the original problem, every ordered proof node, two
untrusted AI proposals, and sometimes host-verified theorem evidence. The proposals are evidence,
not constraints. Independently reconstruct the dependency route and decide the earliest genuinely
failed edge. Keep the theorem and assumptions fixed. A terse standard inference is not a gap by
length alone; a correct route with a missing atomic bridge is a gap, while an invalid operation or
false claim is not. Failure to find a counterexample is not proof.

Check every mathematical assertion in the submitted proof, including examples or postscripts after
the main conclusion. If verified theorem evidence is supplied, use its exact premise and status
effect, but still check all later nodes. Prefer an earlier node only if it is itself unsupported or
false under its direct dependencies. Use proof_end only when the proof stops before the required
argument. If neither proposal is correct, synthesize the supported result. If the evidence cannot
decide, use adjudication_status=unresolved, proof_assessment=undetermined,
first_error_node=undetermined, and error_type=undetermined. Return exactly one row per case_id in
input order, conforming to the output schema. Chinese or English is fine.
"""


M5_RUNTIME_REVIEW_INSTRUCTIONS = """You are an isolated independent Codex AI patch reviewer, not
a human reviewer, not the Repair Generator, and not a Gold authority. Each case contains the
original problem and proof, the frozen local generator input, one actual generated PatchProposal,
and non-mathematical execution metadata. Do not inspect the repository, files, tools, or web.

Reconstruct the exact failed dependency edge. Decide whether the patch is mathematically valid,
actually closes that edge, preserves the theorem, assumptions and domain, introduces no new error,
and is operationally minimal. Then check the full original proof after applying the patch: later
claims remain obligations even if the target itself was repaired. A replacement may not merely
assert the theorem it is supposed to prove. Execution success, schema validity, model confidence,
or a budget terminal status is not mathematical acceptance. For the deletion trial, state whether
removing every proposed edit restores the certified failure. The generator has no self-acceptance
authority. If accepted, choose apply_and_revalidate; if any check fails, choose reject_patch; use
manual_review only when the supplied text is genuinely insufficient. Return exactly one row per
proof_id in input order and conform to the output schema. Chinese or English is fine.
"""


def extract_event_metadata(stdout: str) -> dict[str, Any]:
    thread_ids: list[str] = []
    usages: list[dict[str, Any]] = []
    event_types: list[str] = []
    transport_error_categories: Counter[str] = Counter()
    fallback_error_item_categories: Counter[str] = Counter()
    malformed = 0
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        event_type = event.get("type")
        if isinstance(event_type, str):
            event_types.append(event_type)
        if event_type == "error":
            transport_error_categories[classify_transport_error(event.get("message"))] += 1
        item = event.get("item")
        if (event_type == "item.completed" and isinstance(item, dict)
                and item.get("type") == "error"):
            fallback_error_item_categories[classify_transport_error(item.get("message"))] += 1
        thread_id = event.get("thread_id")
        if isinstance(thread_id, str) and thread_id not in thread_ids:
            thread_ids.append(thread_id)
        usage = event.get("usage")
        if isinstance(usage, dict):
            usages.append(usage)
    return {
        "thread_ids": thread_ids,
        "usage_events": usages,
        "event_types": event_types,
        "malformed_jsonl_lines": malformed,
        "transport_error_event_count": sum(transport_error_categories.values()),
        "transport_error_event_categories": dict(sorted(transport_error_categories.items())),
        "fallback_error_item_count": sum(fallback_error_item_categories.values()),
        "fallback_error_item_categories": dict(sorted(fallback_error_item_categories.items())),
    }


def classify_transport_error(message: Any) -> str:
    text = message.lower() if isinstance(message, str) else ""
    if "403 forbidden" in text and ("websocket" in text or "wss://" in text):
        return "websocket_403_reconnect"
    if "request timed out" in text:
        return "request_timeout_reconnect"
    return "other"


def run_attempt(*, task: str, batch_id: str, rows: list[dict[str, Any]],
                output_dir: Path, model: str, reasoning_effort: str,
                timeout_seconds: int, attempt: int,
                codex_command: str = "codex",
                isolated_working_dir: Path | None = None,
                repository_commit: str | None = None,
                repository_dirty_at_run_start: bool | None = None,
                disabled_skill_paths: list[Path] | None = None) -> dict[str, Any]:
    schema_path = ROOT / f"schemas/{task}_ai_proxy_batch_review_v0_1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    instructions = {
        "m5": M5_INSTRUCTIONS,
        "m5_runtime_review": M5_RUNTIME_REVIEW_INSTRUCTIONS,
        "m7": M7_INSTRUCTIONS,
        "m7_blind": M7_BLIND_INSTRUCTIONS,
        "m7_adjudication": M7_ADJUDICATION_INSTRUCTIONS,
    }[task]
    disabled_skill_paths = disabled_skill_paths or []
    payload = {"batch_id": batch_id, "rows": rows}
    prompt = instructions + "\nINPUT JSON:\n" + json.dumps(payload, ensure_ascii=False)
    attempt_dir = output_dir / "batches" / batch_id / f"attempt-{attempt:02d}"
    request = {
        "schema_version": "codex-ai-proxy-request-0.1",
        "task": task,
        "batch_id": batch_id,
        "attempt": attempt,
        "reviewer_kind": "codex_ai_proxy",
        "model_requested": model,
        "exact_model_snapshot": None,
        "reasoning_effort": reasoning_effort,
        "sandbox": "read-only",
        "ephemeral_session": True,
        "ignore_user_config": task in ISOLATED_TASKS,
        "ignore_rules": task in ISOLATED_TASKS,
        "working_directory": str(isolated_working_dir if task in ISOLATED_TASKS else ROOT),
        "disabled_features": ["shell_tool", "skill_search"] if task in ISOLATED_TASKS else [],
        "disabled_skill_paths": [str(path) for path in disabled_skill_paths],
        "repository_commit": repository_commit or git_value("rev-parse", "HEAD"),
        "repository_dirty_at_run_start": (
            bool(git_value("status", "--porcelain"))
            if repository_dirty_at_run_start is None
            else repository_dirty_at_run_start
        ),
        "schema_path": str(schema_path.relative_to(ROOT)),
        "schema_sha256": sha256_bytes(schema_path.read_bytes()),
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "case_ids": [row.get("case_id", row.get("proof_id")) for row in rows],
        "timeout_seconds": timeout_seconds,
        "response_id": None,
        "response_id_note": "Codex CLI is not the Responses API and exposes no Provider response ID here.",
        "cost_usd": None,
        "cost_note": "Codex subscription execution exposes no per-call billing amount.",
    }
    write_once(attempt_dir / "request.json", canonical_bytes(request))
    write_once(attempt_dir / "stdin_prompt.txt", prompt.encode("utf-8"))
    last_message_path = attempt_dir / "last_message.json"
    command = [codex_command, "exec", "--ephemeral", "--skip-git-repo-check"]
    if task in ISOLATED_TASKS:
        if isolated_working_dir is None:
            raise RuntimeError(f"{task} requires an isolated working directory")
        command.extend([
            "--ignore-user-config", "--ignore-rules",
            "--disable", "shell_tool", "--disable", "skill_search",
        ])
        if disabled_skill_paths:
            skills_config = "[" + ",".join(
                "{path=" + json.dumps(str(path)) + ",enabled=false}"
                for path in disabled_skill_paths
            ) + "]"
            command.extend(["-c", f"skills.config={skills_config}"])
    command.extend([
        "-C", str(isolated_working_dir if task in ISOLATED_TASKS else ROOT),
        "-s", "read-only", "-m", model,
        "-c", f'model_reasoning_effort="{reasoning_effort}"',
        "--output-schema", str(schema_path), "--json",
        "-o", str(last_message_path), "-",
    ])
    started = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    timed_out = False
    child_env = dict(os.environ)
    child_env.pop("OPENAI_API_KEY", None)
    child_env.pop("CODEX_API_KEY", None)
    try:
        completed = subprocess.run(
            command, input=prompt, text=True, capture_output=True,
            encoding="utf-8", errors="strict",
            timeout=timeout_seconds, check=False, env=child_env,
        )
        return_code = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    ended = datetime.now(timezone.utc)
    latency_ms = round((time.monotonic() - monotonic_start) * 1000)
    write_once(attempt_dir / "stdout.jsonl", stdout.encode("utf-8"))
    write_once(attempt_dir / "stderr.txt", stderr.encode("utf-8"))
    metadata = extract_event_metadata(stdout)
    parsed = None
    parse_error = None
    if last_message_path.exists():
        try:
            parsed = json.loads(last_message_path.read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(parsed)
            expected = request["case_ids"]
            actual = [row.get("case_id", row.get("proof_id")) for row in parsed["rows"]]
            if actual != expected:
                raise ValueError(f"output identifiers/order differ: expected {expected}, got {actual}")
        except Exception as exc:  # Evidence must preserve the exact parse failure.
            parse_error = f"{type(exc).__name__}: {exc}"
    else:
        parse_error = "last_message.json was not produced"
    status = "completed" if return_code == 0 and parse_error is None else (
        "timeout" if timed_out else "failed")
    result = {
        "schema_version": "codex-ai-proxy-attempt-0.2",
        "task": task,
        "batch_id": batch_id,
        "attempt": attempt,
        "status": status,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "latency_ms": latency_ms,
        "return_code": return_code,
        "timed_out": timed_out,
        "parse_error": parse_error,
        "codex_thread_ids": metadata["thread_ids"],
        "token_usage_events": metadata["usage_events"],
        "event_types": metadata["event_types"],
        "malformed_jsonl_lines": metadata["malformed_jsonl_lines"],
        "transport_error_event_count": metadata["transport_error_event_count"],
        "transport_error_event_categories": metadata["transport_error_event_categories"],
        "fallback_error_item_count": metadata["fallback_error_item_count"],
        "fallback_error_item_categories": metadata["fallback_error_item_categories"],
        "response_id": None,
        "cost_usd": None,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        "parsed_output_sha256": sha256_bytes(canonical_bytes(parsed)) if parsed is not None else None,
    }
    write_once(attempt_dir / "attempt_result.json", canonical_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task", choices=("m5", "m5_runtime_review", "m7", "m7_blind", "m7_adjudication"),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument(
        "--isolated-working-dir", type=Path,
        default=Path("/tmp/why-repair-m7-blind-runtime-20260821"),
    )
    parser.add_argument("--disable-skill-path", action="append", type=Path, default=[])
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--retry-limit", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Codex proxy calls are disabled; pass --execute explicitly")
    if args.batch_size < 1 or args.timeout_seconds < 1 or args.retry_limit < 0 or args.offset < 0:
        raise SystemExit("batch size/timeout must be positive; offset/retry limit must be nonnegative")
    rows = {
        "m5": m5_rows,
        "m5_runtime_review": m5_runtime_review_rows,
        "m7": m7_rows,
        "m7_blind": m7_blind_rows,
        "m7_adjudication": m7_adjudication_rows,
    }[args.task]()
    if args.case_id:
        requested = set(args.case_id)
        known = {row.get("case_id", row.get("proof_id")) for row in rows}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"unknown case ids for {args.task}: {unknown}")
        rows = [
            row for row in rows
            if row.get("case_id", row.get("proof_id")) in requested
        ]
    rows = rows[args.offset:]
    if args.limit is not None:
        rows = rows[:args.limit]
    cli_version = subprocess.check_output(
        [args.codex_command, "--version"], text=True, encoding="utf-8"
    ).strip()
    if args.task in ISOLATED_TASKS:
        args.isolated_working_dir.mkdir(parents=True, exist_ok=True)
        if any(args.isolated_working_dir.iterdir()):
            raise SystemExit(
                f"isolated working directory must be empty: {args.isolated_working_dir}"
            )
    repository_commit = git_value("rev-parse", "HEAD")
    repository_dirty_at_run_start = bool(git_value("status", "--porcelain"))
    run_manifest = {
        "schema_version": "codex-ai-proxy-run-0.1",
        "task": args.task,
        "reviewer_kind": "codex_ai_proxy",
        "human_review": False,
        "eligible_as_human_evidence": False,
        "eligible_for_scientific_gold": False,
        "model_requested": args.model,
        "exact_model_snapshot": None,
        "codex_cli_version": cli_version,
        "python_version": platform.python_version(),
        "repository_commit": repository_commit,
        "repository_dirty_at_run_start": repository_dirty_at_run_start,
        "case_count": len(rows),
        "case_ids": [row.get("case_id", row.get("proof_id")) for row in rows],
        "source_offset": args.offset,
        "requested_case_ids": args.case_id,
        "batch_size": args.batch_size,
        "timeout_seconds": args.timeout_seconds,
        "retry_limit": args.retry_limit,
        "response_id_available": False,
        "per_call_cost_available": False,
    }
    if args.task == "m5_runtime_review":
        run_manifest["review_input_projection"] = {
            "included_fields": [
                "proof_id", "original_problem", "frozen_generator_input",
                "generated_patch", "generator_evidence",
            ],
            "excluded_fields": [
                "gold", "historical_patch", "person_a_review", "human_attestation",
            ],
            "generator_output_authority": "untrusted_proposal",
        }
        run_manifest["execution_isolation"] = {
            "ephemeral_session": True,
            "sandbox": "read-only",
            "ignore_user_config": True,
            "ignore_rules": True,
            "isolated_working_directory": str(args.isolated_working_dir),
            "isolated_working_directory_empty_at_start": True,
            "output_directory": str(args.output_dir),
            "disabled_features": ["shell_tool", "skill_search"],
            "disabled_skill_paths": [str(path) for path in args.disable_skill_path],
        }
    elif args.task == "m7_blind":
        run_manifest["blind_input_projection"] = {
            "included_fields": ["case_id", "problem", "proof_nodes"],
            "excluded_fields": [
                "frozen_human_proof_verdict", "candidate_mapping", "scope",
                "first_pass_output", "gold",
            ],
            "selection_rule": "first-pass corrected or undetermined; selection hidden from model",
        }
        run_manifest["execution_isolation"] = {
            "ephemeral_session": True,
            "sandbox": "read-only",
            "ignore_user_config": True,
            "ignore_rules": True,
            "isolated_working_directory": str(args.isolated_working_dir),
            "isolated_working_directory_empty_at_start": True,
            "output_directory": str(args.output_dir),
            "disabled_features": ["shell_tool", "skill_search"],
            "disabled_skill_paths": [str(path) for path in args.disable_skill_path],
        }
    elif args.task == "m7_adjudication":
        run_manifest["adjudication_input_projection"] = {
            "included_fields": [
                "case_id", "problem", "proof_nodes", "adjudication_reasons",
                "first_pass_proposal", "second_pass_proposal", "second_pass_source",
                "verified_theorem_evidence",
            ],
            "excluded_fields": ["frozen_human_proof_verdict", "candidate_mapping", "gold"],
            "proposal_authority": "untrusted_ai_evidence",
        }
        run_manifest["execution_isolation"] = {
            "ephemeral_session": True,
            "sandbox": "read-only",
            "ignore_user_config": True,
            "ignore_rules": True,
            "isolated_working_directory": str(args.isolated_working_dir),
            "isolated_working_directory_empty_at_start": True,
            "output_directory": str(args.output_dir),
            "disabled_features": ["shell_tool", "skill_search"],
            "disabled_skill_paths": [str(path) for path in args.disable_skill_path],
        }
    write_once(args.output_dir / "run_manifest.json", canonical_bytes(run_manifest))
    results = []
    for offset in range(0, len(rows), args.batch_size):
        batch_rows = rows[offset:offset + args.batch_size]
        batch_id = f"{args.task}-proxy-{(args.offset + offset) // args.batch_size + 1:03d}"
        result = None
        for attempt in range(1, args.retry_limit + 2):
            result = run_attempt(
                task=args.task, batch_id=batch_id, rows=batch_rows,
                output_dir=args.output_dir, model=args.model,
                reasoning_effort=args.reasoning_effort,
                timeout_seconds=args.timeout_seconds, attempt=attempt,
                codex_command=args.codex_command,
                isolated_working_dir=args.isolated_working_dir,
                repository_commit=repository_commit,
                repository_dirty_at_run_start=repository_dirty_at_run_start,
                disabled_skill_paths=args.disable_skill_path,
            )
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if result["status"] == "completed":
                break
        if result is None or result["status"] != "completed":
            print(f"batch {batch_id} exhausted retries; continuing with preserved failure", file=sys.stderr)
    summary = {
        "schema_version": "codex-ai-proxy-run-summary-0.2",
        "task": args.task,
        "attempt_count": len(results),
        "completed_batches": sum(row["status"] == "completed" for row in results),
        "failed_attempts": sum(row["status"] == "failed" for row in results),
        "timed_out_attempts": sum(row["status"] == "timeout" for row in results),
        "completed_attempts_with_transport_errors": sum(
            row["status"] == "completed" and row["transport_error_event_count"] > 0
            for row in results
        ),
        "transport_error_event_count": sum(
            row["transport_error_event_count"] for row in results
        ),
        "transport_error_event_categories": dict(sorted(sum(
            (Counter(row["transport_error_event_categories"]) for row in results),
            Counter(),
        ).items())),
        "fallback_error_item_count": sum(row["fallback_error_item_count"] for row in results),
        "response_ids": [],
        "cost_usd": None,
        "token_usage_events": [usage for row in results for usage in row["token_usage_events"]],
    }
    write_once(args.output_dir / "run_summary.json", canonical_bytes(summary))
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
