"""Recompute the historical baseline without changing predictions or Gold."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def first(gap, invalid):
    return min((v for v in (gap, invalid) if v is not None), default=None)


def audit():
    path = ROOT / "data/benchmarks/m3/revalidation/full50_details_v0_2.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mismatches, correct, applicable, localized = [], 0, 0, 0
    for row in rows:
        gold = first(row["gold_first_gap_step"], row["gold_first_invalid_step"])
        pred = first(row["predicted_first_gap_step"], row["predicted_first_invalid_step"])
        correct += gold == pred
        applicable += gold is not None
        localized += gold is not None and gold == pred
        if gold != pred:
            mismatches.append({"id": row["sample_id"], "gold_first": gold, "predicted_first": pred})
    candidates = json.loads((ROOT / "data/benchmarks/m3/localization_v1/review_candidates.json").read_text(encoding="utf-8"))
    if {r["id"] for r in mismatches} != {r["id"] for r in candidates["cases"]}:
        raise ValueError("Audit packet no longer covers the exact mismatch set")
    return {"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "overall": {"correct": correct, "count": len(rows), "accuracy": correct / len(rows)},
            "applicable": {"correct": localized, "count": applicable, "accuracy": localized / applicable},
            "mismatches": mismatches, "candidate_status": candidates["status"],
            "gold_modified": False, "new_model_accuracy": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "applicable": report["applicable"]}))
