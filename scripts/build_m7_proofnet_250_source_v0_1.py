"""Build the pinned, provenance-complete ProofNet-250 source baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/m7/proofnet_250_v0_1"
PINNED_COMMIT = "509ad79710ed4f46ff5c282ed5640c1aa9ac3f30"
REPOSITORY = "https://github.com/zhangir-azerbayev/ProofNet"
DOMAIN = {
    "Artin": "abstract_algebra", "Axler": "linear_algebra",
    "Dummit-Foote": "abstract_algebra", "Herstein": "abstract_algebra",
    "Ireland-Rosen": "number_theory", "Munkres": "topology",
    "Pugh": "real_analysis", "Putnam": "mixed_undergraduate",
    "Rudin": "real_analysis", "Shakarchi": "complex_analysis",
}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: object) -> str:
    return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")).encode("utf-8"))


def read_rows(path: Path) -> list[tuple[bytes, dict]]:
    return [(line, json.loads(line)) for line in path.read_bytes().splitlines() if line.strip()]


def ranked(rows: list[tuple[bytes, dict]], source_split: str) -> list[tuple[bytes, dict]]:
    return sorted(rows, key=lambda item: hashlib.sha256(
        f"proofnet-250-v0.1|{PINNED_COMMIT}|{source_split}|{item[1]['id']}".encode()).hexdigest())


def tokens(row: dict) -> set[str]:
    return set(re.findall(r"[\w]+", f"{row['nl_statement']} {row['nl_proof']}".casefold(), re.UNICODE))


def similarity(left: dict, right: dict) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / len(a | b)


def build(source_root: Path) -> tuple[list[dict], dict, list[dict], str]:
    license_path = source_root / "LICENSE"
    valid_path = source_root / "benchmark/valid.jsonl"
    test_path = source_root / "benchmark/test.jsonl"
    if not all(path.is_file() for path in (license_path, valid_path, test_path)):
        raise RuntimeError("ProofNet checkout is missing LICENSE or benchmark JSONL files")
    valid_all, test_all = read_rows(valid_path), read_rows(test_path)
    if len(valid_all) != 185 or len(test_all) != 186:
        raise RuntimeError("pinned ProofNet is expected to contain 185 valid and 186 test records")
    excluded = [row["id"] for _, row in valid_all + test_all
                if not row.get("nl_statement", "").strip() or not row.get("nl_proof", "").strip()]
    valid = [(raw, row) for raw, row in valid_all
             if row.get("nl_statement", "").strip() and row.get("nl_proof", "").strip()]
    test = [(raw, row) for raw, row in test_all
            if row.get("nl_statement", "").strip() and row.get("nl_proof", "").strip()]
    chosen_valid = ranked(valid, "valid")[:100]
    chosen_test = []
    excluded_cross_split = []
    for candidate in ranked(test, "test"):
        matches = [(row["id"], similarity(candidate[1], row)) for _, row in chosen_valid]
        matches = [(proofnet_id, score) for proofnet_id, score in matches if score >= 0.85]
        if matches:
            excluded_cross_split.append({"proofnet_id": candidate[1]["id"], "matches": matches})
            continue
        chosen_test.append(candidate)
        if len(chosen_test) == 150:
            break
    if len(chosen_test) != 150:
        raise RuntimeError("not enough non-leaking ProofNet test records for the frozen sample")
    assignments = [(raw, row, "train" if index < 50 else "development", "valid")
                   for index, (raw, row) in enumerate(chosen_valid)]
    assignments += [(raw, row, "test", "test") for raw, row in chosen_test]
    license_digest = digest_bytes(license_path.read_bytes())
    records = []
    source_index = []
    for number, (raw, row, split, source_split) in enumerate(assignments, 1):
        source = row["id"].split("|", 1)[0]
        source_digest = canonical_digest(row)
        raw_digest = digest_bytes(raw)
        case_id = f"proofnet250-{number:03d}"
        uri = f"{REPOSITORY}/blob/{PINNED_COMMIT}/benchmark/{source_split}.jsonl"
        records.append({
            "case_id": case_id, "source_uri": uri,
            "source_record_digest": source_digest,
            "license_status": "verified_redistributable",
            "license_evidence": f"ProofNet MIT LICENSE sha256:{license_digest}",
            "raw_bytes_sha256": raw_digest, "problem": row["nl_statement"],
            "proof": row["nl_proof"], "language": "en",
            "domain": DOMAIN[source], "difficulty": "unrated_pending_annotation", "split": split,
        })
        source_index.append({
            "case_id": case_id, "proofnet_id": row["id"], "proofnet_source_split": source_split,
            "formal_statement": row["formal_statement"], "source_record_digest": source_digest,
            "raw_bytes_sha256": raw_digest,
        })
    manifest = {
        "schema_version": "m7-proofnet-250-source-0.1",
        "status": "source_baseline_frozen_pending_error_derivation_and_human_gold",
        "repository": REPOSITORY, "commit": PINNED_COMMIT,
        "license": "MIT", "license_sha256": license_digest,
        "upstream_counts": {"valid": len(valid_all), "test": len(test_all)},
        "eligible_counts": {"valid": len(valid), "test": len(test)},
        "excluded_incomplete_proofnet_ids": sorted(excluded),
        "near_duplicate_threshold": 0.85,
        "excluded_cross_split_near_duplicates": excluded_cross_split,
        "selection": "sha256_ranked_without_replacement",
        "selection_seed": f"proofnet-250-v0.1|{PINNED_COMMIT}",
        "record_count": len(records),
        "split_counts": {"train": 50, "development": 50, "test": 150},
        "candidate_digest": canonical_digest(records),
        "source_index_digest": canonical_digest(source_index),
        "limitations": [
            "These are original correct-proof source records, not yet the final diagnostic/repair cases.",
            "Difficulty and mathematical Gold remain pending annotation.",
            "The formal statement is retained only in the private source index and must not enter model input.",
        ],
    }
    return records, manifest, source_index, license_path.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    records, manifest, source_index, license_text = build(args.source_root)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "candidate.jsonl").write_text("".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "private_source_index.json").write_text(
        json.dumps(source_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "LICENSE.ProofNet").write_text(license_text, encoding="utf-8")


if __name__ == "__main__":
    main()
