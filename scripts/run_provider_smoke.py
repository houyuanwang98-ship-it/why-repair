#!/usr/bin/env python3
"""Run explicit M5/M6 Codex CLI smoke assignments with append-only evidence.

The historical filename remains as a compatibility entrypoint. No API key is
read or accepted; ``codex exec`` reuses the authenticated Codex CLI session.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from harness.codex_cli import build_codex_adapter, codex_cli_version
from harness.provider_runner import AppendOnlyEvidenceStore, ProviderRunConfig, ProviderRunner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Frozen JSON configuration")
    parser.add_argument("--assignments", required=True, help="JSONL: sample_id, method_id, input_payload")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--execute", action="store_true", help="Required for any Codex call")
    args = parser.parse_args()

    if not args.execute:
        raise SystemExit("Codex calls are disabled; review frozen inputs, then pass --execute explicitly")

    raw_config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    config = ProviderRunConfig(**raw_config)
    actual_commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit != config.repository_commit:
        raise SystemExit("current repository commit does not match frozen Codex config")
    dirty = subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    )
    if dirty:
        raise SystemExit("Codex execution requires a clean worktree")
    actual_cli_version = codex_cli_version()
    if actual_cli_version != config.sdk_version:
        raise SystemExit("installed Codex CLI does not match frozen Codex config")
    prompt = Path(args.prompt).read_text(encoding="utf-8")
    assignments = [json.loads(line) for line in Path(args.assignments).read_text(encoding="utf-8").splitlines() if line.strip()]
    adapter = build_codex_adapter(version=actual_cli_version)
    runner = ProviderRunner(config, AppendOnlyEvidenceStore(Path(args.output_dir)), adapter,
                            execution_enabled=args.execute)
    for row in runner.run_batch(run_id=args.run_id, prompt=prompt, assignments=assignments):
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
