"""Freeze the per-case validity/error derivation assignment for ProofNet-250."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/proofnet_250_v0_1"
OUT = BASE / "derivation_plan.json"
RATIOS = (
    ("unchanged_valid", 10),
    ("proof_gap", 12),
    ("invalid_inference", 12),
    ("algebraic_or_symbolic_error", 6),
    ("missing_assumption_or_domain", 5),
    ("false_or_undefined_theorem", 5),
)
SPLIT_SCALE = {"train": 1, "development": 1, "test": 3}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def build() -> dict:
    records = [json.loads(line) for line in (BASE / "candidate.jsonl").read_text().splitlines()]
    source = {row["case_id"]: row for row in json.loads(
        (BASE / "private_source_index.json").read_text())}
    assignments = []
    for split, scale in SPLIT_SCALE.items():
        rows = [row for row in records if row["split"] == split]
        rows.sort(key=lambda row: hashlib.sha256(
            f"proofnet-250-derivation-v0.1|{split}|{row['case_id']}".encode()).hexdigest())
        categories = [category for category, count in RATIOS for _ in range(count * scale)]
        if len(rows) != len(categories):
            raise RuntimeError(f"unexpected {split} size")
        for row, category in zip(rows, categories):
            assignments.append({
                "case_id": row["case_id"], "proofnet_id": source[row["case_id"]]["proofnet_id"],
                "split": split, "domain": row["domain"], "derivation_category": category,
                "source_record_digest": row["source_record_digest"],
                "derivation_status": "ready_unchanged" if category == "unchanged_valid" else "pending_ai_derivation",
                "human_gold_status": "pending",
            })
    assignments.sort(key=lambda row: row["case_id"])
    return {
        "schema_version": "m7-proofnet-250-derivation-plan-0.1",
        "status": "frozen_assignment_pending_ai_derivation_and_human_gold",
        "assignment_seed": "proofnet-250-derivation-v0.1",
        "source_candidate_digest": digest(records),
        "counts": dict(sorted(Counter(row["derivation_category"] for row in assignments).items())),
        "split_counts": {split: dict(sorted(Counter(
            row["derivation_category"] for row in assignments if row["split"] == split).items()))
                         for split in SPLIT_SCALE},
        "assignments": assignments,
        "rules": [
            "Each source theorem appears exactly once and remains in its frozen split.",
            "Unchanged-valid cases preserve source statement and proof bytes semantically.",
            "Derived cases must have one intended earliest defect and may not expose the private formal statement.",
            "AI derivations are candidates only; human Gold must confirm theorem status, first error, and repairability.",
        ],
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
