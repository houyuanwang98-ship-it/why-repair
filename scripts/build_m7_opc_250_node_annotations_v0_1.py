"""Map OPC character-level issue locations into reviewable proof nodes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/opc_250_v0_1"
OUT = BASE / "node_annotations.json"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def nodes(text: str) -> list[dict]:
    boundaries = {0, len(text)}
    for match in re.finditer(r"\n\s*\n+|(?<=[.!?])\s+(?=[A-Z])", text):
        boundaries.add(match.start())
        boundaries.add(match.end())
    points = sorted(boundaries)
    result = []
    for left, right in zip(points, points[1:]):
        raw = text[left:right]
        stripped = raw.strip()
        if not stripped:
            continue
        start = left + len(raw) - len(raw.lstrip())
        end = right - (len(raw) - len(raw.rstrip()))
        result.append({"node_id": f"n{len(result) + 1}", "start_char": start,
                       "end_char": end, "text": text[start:end]})
    return result


def locate(items: list[dict], offset: int | None) -> str | None:
    if offset is None:
        return None
    for item in items:
        if item["start_char"] <= offset < item["end_char"]:
            return item["node_id"]
    following = [item for item in items if item["start_char"] > offset]
    return following[0]["node_id"] if following else items[-1]["node_id"]


def build(base: Path = BASE) -> dict:
    records = {row["case_id"]: row for row in map(json.loads, (base / "candidate.jsonl").read_text().splitlines())}
    seeds = json.loads((base / "seed_annotations.json").read_text())
    rows = []
    for seed in seeds:
        proof_nodes = nodes(records[seed["case_id"]]["proof"])
        issue = seed["prefilled_first_issue"]
        first = locate(proof_nodes, issue["first_error_char"]) if issue else None
        rows.append({
            "case_id": seed["case_id"], "proof_verdict": seed["human_proof_verdict"],
            "proof_nodes": proof_nodes, "first_error_node": first,
            "error_type": issue["error_type"] if issue else None,
            "error_description": issue["error_description"] if issue else None,
            "location_provenance": issue["location_provenance"] if issue else "not_applicable_correct",
            "category_provenance": issue["category_provenance"] if issue else "not_applicable_correct",
            "human_mapping_verification": None,
        })
    return {
        "schema_version": "m7-opc-250-node-annotations-0.1",
        "status": "prefilled_from_existing_labels_human_mapping_verification_pending",
        "source_candidate_digest": digest(list(records.values())),
        "row_count": len(rows),
        "automatic_first_error_mapped": sum(row["proof_verdict"] == "incorrect" and row["first_error_node"] is not None for row in rows),
        "manual_first_error_required": [row["case_id"] for row in rows
                                        if row["proof_verdict"] == "incorrect" and row["first_error_node"] is None],
        "rows": rows,
        "review_scope": "verify node segmentation, first-error mapping, and mapped error type; do not re-grade from scratch",
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=BASE)
    args = parser.parse_args()
    (args.base / "node_annotations.json").write_text(
        json.dumps(build(args.base), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
