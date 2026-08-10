#!/usr/bin/env python3
"""Synchronize theorem-rule JSONL files from Theorem_grabbing."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT.parent / "Theorem_grabbing"
DEFAULT_DESTINATION = PROJECT_ROOT / "data" / "theorem_bank"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict) or not row.get("id"):
            raise ValueError(f"Missing rule id in {path}:{line_number}")
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    source_files = sorted(args.source.glob("*/*.jsonl"))
    if not source_files:
        raise SystemExit(f"No JSONL files found under {args.source}")

    args.destination.mkdir(parents=True, exist_ok=True)
    seen_ids: dict[str, Path] = {}
    for source in source_files:
        for row in read_jsonl(source):
            rule_id = row["id"]
            if rule_id in seen_ids:
                raise ValueError(
                    f"Duplicate rule id {rule_id!r} in {seen_ids[rule_id]} and {source}"
                )
            seen_ids[rule_id] = source

    imported_paths = []
    for source in source_files:
        destination = args.destination / source.name
        shutil.copyfile(source, destination)
        imported_paths.append(destination)

    artin_path = args.destination / "artin_clean_seed_rules.jsonl"
    merged_paths = [artin_path, *imported_paths]
    merged_rows = []
    merged_ids: dict[str, Path] = {}
    for path in merged_paths:
        for row in read_jsonl(path):
            rule_id = row["id"]
            if rule_id in merged_ids:
                raise ValueError(
                    f"Duplicate merged rule id {rule_id!r} in {merged_ids[rule_id]} and {path}"
                )
            merged_ids[rule_id] = path
            merged_rows.append(row)

    merged_path = args.destination / "all_clean_seed_rules.jsonl"
    with merged_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in merged_rows:
            handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")

    print(
        f"Imported {len(imported_paths)} files with {len(seen_ids)} source rules; "
        f"merged {len(merged_rows)} rules into {merged_path}"
    )


if __name__ == "__main__":
    main()
