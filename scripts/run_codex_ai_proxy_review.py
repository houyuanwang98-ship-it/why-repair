#!/usr/bin/env python3
"""Run auditable Codex CLI batches that proxy, but never impersonate, human review."""

from __future__ import annotations

import argparse
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


def extract_event_metadata(stdout: str) -> dict[str, Any]:
    thread_ids: list[str] = []
    usages: list[dict[str, Any]] = []
    event_types: list[str] = []
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
    }


def run_attempt(*, task: str, batch_id: str, rows: list[dict[str, Any]],
                output_dir: Path, model: str, reasoning_effort: str,
                timeout_seconds: int, attempt: int) -> dict[str, Any]:
    schema_path = ROOT / f"schemas/{task}_ai_proxy_batch_review_v0_1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    instructions = M5_INSTRUCTIONS if task == "m5" else M7_INSTRUCTIONS
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
        "repository_commit": git_value("rev-parse", "HEAD"),
        "repository_dirty_at_run_start": bool(git_value("status", "--porcelain")),
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
    command = [
        "codex", "exec", "--ephemeral", "--skip-git-repo-check",
        "-C", str(ROOT), "-s", "read-only", "-m", model,
        "-c", f'model_reasoning_effort="{reasoning_effort}"',
        "--output-schema", str(schema_path), "--json",
        "-o", str(last_message_path), "-",
    ]
    started = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command, input=prompt, text=True, capture_output=True,
            timeout=timeout_seconds, check=False,
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
        "schema_version": "codex-ai-proxy-attempt-0.1",
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
    parser.add_argument("--task", choices=("m5", "m7"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--retry-limit", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Codex proxy calls are disabled; pass --execute explicitly")
    if args.batch_size < 1 or args.timeout_seconds < 1 or args.retry_limit < 0:
        raise SystemExit("batch size/timeout must be positive and retry limit nonnegative")
    rows = m5_rows() if args.task == "m5" else m7_rows()
    if args.limit is not None:
        rows = rows[:args.limit]
    cli_version = subprocess.check_output(["codex", "--version"], text=True).strip()
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
        "repository_commit": git_value("rev-parse", "HEAD"),
        "case_count": len(rows),
        "case_ids": [row.get("case_id", row.get("proof_id")) for row in rows],
        "batch_size": args.batch_size,
        "timeout_seconds": args.timeout_seconds,
        "retry_limit": args.retry_limit,
        "response_id_available": False,
        "per_call_cost_available": False,
    }
    write_once(args.output_dir / "run_manifest.json", canonical_bytes(run_manifest))
    results = []
    for offset in range(0, len(rows), args.batch_size):
        batch_rows = rows[offset:offset + args.batch_size]
        batch_id = f"{args.task}-proxy-{offset // args.batch_size + 1:03d}"
        result = None
        for attempt in range(1, args.retry_limit + 2):
            result = run_attempt(
                task=args.task, batch_id=batch_id, rows=batch_rows,
                output_dir=args.output_dir, model=args.model,
                reasoning_effort=args.reasoning_effort,
                timeout_seconds=args.timeout_seconds, attempt=attempt,
            )
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if result["status"] == "completed":
                break
        if result is None or result["status"] != "completed":
            print(f"batch {batch_id} exhausted retries; continuing with preserved failure", file=sys.stderr)
    summary = {
        "schema_version": "codex-ai-proxy-run-summary-0.1",
        "task": args.task,
        "attempt_count": len(results),
        "completed_batches": sum(row["status"] == "completed" for row in results),
        "failed_attempts": sum(row["status"] == "failed" for row in results),
        "timed_out_attempts": sum(row["status"] == "timeout" for row in results),
        "response_ids": [],
        "cost_usd": None,
        "token_usage_events": [usage for row in results for usage in row["token_usage_events"]],
    }
    write_once(args.output_dir / "run_summary.json", canonical_bytes(summary))
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
