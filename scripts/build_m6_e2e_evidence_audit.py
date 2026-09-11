#!/usr/bin/env python3
"""Build a reproducible call inventory for an existing M6 E2E run directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, payload: bytes) -> None:
    if path.exists() and path.read_bytes() != payload:
        raise RuntimeError(f"refusing to overwrite differing audit: {path}")
    if not path.exists():
        path.write_bytes(payload)


def build(root: Path) -> tuple[list[dict], dict]:
    rows = []
    for folder in sorted((root / "assignments").glob("*/*/call-*")):
        request_path = folder / "request.json"
        response_path = folder / "response.json"
        failure_path = folder / "failure.json"
        if not request_path.exists():
            continue
        request = json.loads(request_path.read_text(encoding="utf-8"))
        container = None
        raw = None
        raw_path = None
        if response_path.exists():
            raw_path = response_path
            raw = json.loads(response_path.read_text(encoding="utf-8"))
        elif failure_path.exists():
            raw_path = failure_path
            container = json.loads(failure_path.read_text(encoding="utf-8"))
            raw = container.get("raw")
        raw = raw if isinstance(raw, dict) else {}
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        relative = folder.relative_to(root).parts
        validated = (folder / "validated.json").exists()
        rows.append({
            "method_id": relative[1],
            "case_id": relative[2],
            "call_folder": folder.relative_to(root).as_posix(),
            "phase": request["phase"],
            "attempt": 1,
            "retry_count": 0,
            "status": ("validated" if validated else "codex_failure" if failure_path.exists()
                       else "response_retained_not_applied"),
            "requested_model": request["model"],
            "returned_model": raw.get("model"),
            "codex_cli_version": raw.get("codex_cli_version"),
            "provider_response_id": raw.get("provider_response_id", raw.get("id")),
            "codex_thread_id": raw.get("codex_thread_id"),
            "input_tokens": usage.get("input_tokens"),
            "cached_input_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "latency_seconds": (raw.get("latency_seconds") if raw.get("latency_seconds") is not None
                                else max(0.0, raw_path.stat().st_mtime - request_path.stat().st_mtime)
                                if raw_path else None),
            "latency_source": ("monotonic_clock" if raw.get("latency_seconds") is not None
                               else "filesystem_mtime_approximation" if raw_path else "unavailable"),
            "cost_usd": raw.get("cost_usd"),
            "cost_tracking_available": raw.get("cost_tracking_available", False),
            "request_sha256": sha(request_path),
            "raw_response_sha256": sha(raw_path) if raw_path else None,
        })
    audit = {
        "schema_version": "m6-e2e-evidence-audit-0.1",
        "run_dir": root.as_posix(),
        "call_count": len(rows),
        "request_count": sum(row["request_sha256"] is not None for row in rows),
        "raw_response_count": sum(row["raw_response_sha256"] is not None for row in rows),
        "validated_count": sum(row["status"] == "validated" for row in rows),
        "retained_not_applied_count": sum(row["status"] == "response_retained_not_applied" for row in rows),
        "latency_present_count": sum(row["latency_seconds"] is not None for row in rows),
        "latency_precision": "filesystem_mtime_approximation_for_runs_created_before_adapter_timing_patch",
        "provider_response_id_available_count": sum(row["provider_response_id"] is not None for row in rows),
        "cost_available_count": sum(row["cost_usd"] is not None for row in rows),
        "billing_note": "Saved ChatGPT Codex CLI auth exposes no per-call USD amount; null is retained.",
        "complete": all(row["request_sha256"] and row["raw_response_sha256"]
                        and row["latency_seconds"] is not None for row in rows),
    }
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows, audit = build(args.run_dir)
    ledger = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                      for row in rows)
    payload = (json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    write_once(args.run_dir / "call_ledger.jsonl", ledger)
    write_once(args.run_dir / "evidence_audit.json", payload)
    print(payload.decode("utf-8"), end="")


if __name__ == "__main__":
    main()
