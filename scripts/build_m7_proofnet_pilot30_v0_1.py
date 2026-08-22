"""Freeze a deterministic 30-case ProofNet process pilot selection."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/benchmarks/m7/proofnet_250_v0_1"
OUT = ROOT / "data/benchmarks/m7/proofnet_pilot30_v0_1/manifest.json"
SEED = "proofnet-pilot30-v0.1|process-only|2026-08-22"


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build() -> dict:
    source_manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (SOURCE / "candidate.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = []
    for split in ("train", "development", "test"):
        pool = [row for row in rows if row["split"] == split]
        ranked = sorted(pool, key=lambda row: hashlib.sha256(
            f"{SEED}|{row['case_id']}".encode("utf-8")
        ).hexdigest())
        selected.extend(ranked[:10])
    records = [{
        "case_id": row["case_id"],
        "source_split": row["split"],
        "domain": row["domain"],
        "source_record_digest": row["source_record_digest"],
    } for row in sorted(selected, key=lambda row: row["case_id"])]
    return {
        "schema_version": "m7-proofnet-pilot30-0.1",
        "status": "selection_frozen_annotation_pending",
        "purpose": "process_pilot_not_confirmatory_evidence",
        "source_manifest_digest": canonical_sha256(source_manifest),
        "selection_seed": SEED,
        "selection_method": "sha256_rank_first_10_per_source_split",
        "record_count": len(records),
        "split_counts": dict(sorted(Counter(row["source_split"] for row in records).items())),
        "records": records,
        "exclusion_policy": "all selected case_ids are permanently excluded from future formal test sets",
        "gold_status": "pending_independent_annotation",
        "formal_claim_allowed": False,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = build()
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    source_rows = {
        row["case_id"]: row for row in (
            json.loads(line) for line in (SOURCE / "candidate.jsonl").read_text(encoding="utf-8").splitlines()
        )
    }
    cases = [{
        "case_id": item["case_id"],
        "domain": item["domain"],
        "problem": source_rows[item["case_id"]]["problem"],
        "proof": source_rows[item["case_id"]]["proof"],
        "annotation": None,
    } for item in manifest["records"]]
    for slot in ("annotator_a", "annotator_b"):
        packet = {
            "schema_version": "m7-pilot-annotation-packet-0.1",
            "reviewer_slot": slot,
            "independence_rule": "complete_and_hash_lock_before_viewing_other_packet",
            "required_fields": [
                "proof_verdict", "first_error", "error_type", "counterexample_scope",
                "repairability", "evidence", "notes",
            ],
            "cases": cases,
        }
        (OUT.parent / f"{slot}_packet.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    adjudication = {
        "schema_version": "m7-pilot-adjudication-0.1",
        "status": "blocked_until_two_locked_independent_packets",
        "third_expert_identity": None,
        "annotator_a_sha256": None,
        "annotator_b_sha256": None,
        "disagreements": [],
    }
    (OUT.parent / "adjudication_template.json").write_text(
        json.dumps(adjudication, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
