"""Build a low-human-labor 250-proof candidate from Open Proof Corpus labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/m7/opc_250_v0_1"
COMMIT = "e92a6ca848e50f5d3f9c2a1393da72720760d931"
REPOSITORY = "https://github.com/insait-institute/open-proof-corpus"
CATEGORY_MAP = {
    "Overgeneralization": "false_generalization",
    "Oversimplification": "proof_gap",
    "Skipping Computation Steps": "proof_gap",
    "Missing Computation Steps": "proof_gap",
    "Missing Proof Steps": "proof_gap",
    "Missing Explanation": "proof_gap",
    "Missing justification": "proof_gap",
    "Missing reasoning": "proof_gap",
    "Missing Edge Cases": "missing_assumption",
    "Citing Non-Standard Works or Theorems": "unsupported_external_dependency",
    "Wrong Final Answer": "wrong_conclusion",
    "Missing Final Answer": "wrong_conclusion",
    "Wrong reasoning": "invalid_inference",
    "Other": "other",
}
QUOTAS = {
    "human_localized_incorrect": {"train": 8, "development": 8, "test": 25},
    "human_incorrect_ai_localized": {"train": 32, "development": 32, "test": 95},
    "human_correct": {"train": 10, "development": 10, "test": 30},
}
QUALITY_QUOTAS = {
    "human_localized_incorrect": {"train": 7, "development": 7, "test": 21},
    "human_incorrect_ai_localized": {"train": 31, "development": 31, "test": 93},
    "human_correct": {"train": 12, "development": 12, "test": 36},
}
GEOMETRY_PATTERN = re.compile(
    r"\b(?:triangle|circle|circumcircle|circumcenter|orthocenter|incenter|incircle|"
    r"angle|perpendicular|parallel|collinear|midpoint|polygon|polyhedron|quadrilateral|"
    r"parallelogram|trapezoid|rectangle|square|pentagon|hexagon|octagon|tangent|chord|"
    r"altitude|bisector|centroid|semicircle|parabola|geometric|geometry|plane)\b",
    re.IGNORECASE,
)


def is_geometry_problem(problem: str) -> bool:
    """Conservatively reject prompts that depend on geometric objects/relations."""
    return bool(GEOMETRY_PATTERN.search(problem))


def proof_quality(text: str) -> dict[str, int]:
    boundaries = {0, len(text)}
    for match in re.finditer(r"\n\s*\n+|(?<=[.!?])\s+(?=[A-Z])", text):
        boundaries.update((match.start(), match.end()))
    points = sorted(boundaries)
    parts = [text[left:right].strip() for left, right in zip(points, points[1:])
             if text[left:right].strip()]
    return {"node_count": len(parts), "max_node_chars": max(map(len, parts), default=0),
            "proof_chars": len(text)}


def passes_quality_gate(proof: str) -> bool:
    item = proof_quality(proof)
    return item["node_count"] <= 100 and item["max_node_chars"] <= 700 and item["proof_chars"] <= 12000


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> str:
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode())


def extract_prompt(text: str) -> tuple[str, str] | None:
    match = re.search(r"### Problem Statement:\s*\n(.*?)\n\n### Model Solution:\s*\n(.*)", text, re.S)
    return (match.group(1).strip(), match.group(2).strip()) if match else None


def export_rows(source_root: Path, duckdb: Path, destination: Path) -> None:
    parquet = (source_root / "data/train/discrete/long/*.parquet").as_posix().replace("'", "''")
    output = destination.as_posix().replace("'", "''")
    sql = f"""COPY (SELECT problem_id, metadata, model_id,
      reward_model.ground_truth AS ground_truth, extra_info.split AS source_split,
      extra_info.index AS source_index, prompt[1].content AS prompt_content,
      annotations, llm_judgment.result.issues AS llm_issues
      FROM read_parquet('{parquet}')) TO '{output}' (FORMAT JSON, ARRAY true);"""
    subprocess.run([str(duckdb), "-c", sql], check=True, capture_output=True, text=True)


def rank(rows: list[dict], group: str) -> list[dict]:
    return sorted(rows, key=lambda row: sha(
        f"m7-opc-250-v0.1|{COMMIT}|{group}|{row['problem_id']}|{row['model_id']}|{row['source_index']}".encode()))


def one_per_problem(rows: list[dict], *, prefer_annotations: bool = False) -> list[dict]:
    chosen = {}
    for row in rows:
        key = row["problem_id"]
        score = (len(row.get("annotations") or []) if prefer_annotations else 0,
                 canonical(row))
        if key not in chosen or score > chosen[key][0]:
            chosen[key] = (score, row)
    return [value[1] for value in chosen.values()]


def mapped_issue(row: dict, *, human_localized: bool) -> dict | None:
    issues = [issue for issue in row.get("llm_issues") or [] if issue.get("description")]
    annotations = [item for item in row.get("annotations") or [] if item.get("comment")]
    if human_localized and annotations:
        annotation = min(annotations, key=lambda item: (item.get("original_text_indices") or [10**12])[0])
        offset = (annotation.get("original_text_indices") or [None])[0]
        nearest = min(issues, key=lambda issue: abs((issue.get("start_index") or 0) - (offset or 0))) if issues else None
        category = CATEGORY_MAP.get((nearest or {}).get("category"), "other")
        return {"location_provenance": "human_selected_text", "category_provenance": "opc_llm_judgment",
                "first_error_char": offset, "selected_text": annotation.get("original_text"),
                "error_description": annotation["comment"], "error_type": category,
                "opc_category": (nearest or {}).get("category")}
    if issues:
        issue = min(issues, key=lambda item: item.get("start_index") if item.get("start_index") is not None else 10**12)
        offset = issue.get("start_index")
        if offset is None and issue.get("text"):
            found = row["proof"].find(issue["text"])
            offset = found if found >= 0 else None
        return {"location_provenance": "opc_llm_judgment", "category_provenance": "opc_llm_judgment",
                "first_error_char": offset, "selected_text": issue.get("text"),
                "error_description": issue["description"],
                "error_type": CATEGORY_MAP.get(issue.get("category"), "other"),
                "opc_category": issue.get("category")}
    return None


def build(source_root: Path, duckdb: Path, *, quality_filtered: bool = False) -> tuple[list[dict], list[dict], dict, str]:
    with tempfile.TemporaryDirectory() as tmp:
        exported = Path(tmp) / "opc.jsonl"
        export_rows(source_root, duckdb, exported)
        raw = json.loads(exported.read_text())
    eligible = []
    geometry_excluded = 0
    for row in raw:
        parsed = extract_prompt(row.get("prompt_content") or "")
        if parsed:
            row["problem"], row["proof"] = parsed
            if is_geometry_problem(row["problem"]):
                geometry_excluded += 1
            elif quality_filtered and not passes_quality_gate(row["proof"]):
                continue
            else:
                eligible.append(row)
    quotas = QUALITY_QUOTAS if quality_filtered else QUOTAS
    targets = {group: sum(split.values()) for group, split in quotas.items()}
    high = one_per_problem([row for row in eligible if row["ground_truth"] == "incorrect"
                            and row.get("annotations")], prefer_annotations=True)
    high = rank(high, "human_localized_incorrect")[:targets["human_localized_incorrect"]]
    used = {row["problem_id"] for row in high}
    low = one_per_problem([row for row in eligible if row["ground_truth"] == "incorrect"
                           and row["problem_id"] not in used and row.get("llm_issues")])
    low = rank(low, "human_incorrect_ai_localized")[:targets["human_incorrect_ai_localized"]]
    used |= {row["problem_id"] for row in low}
    correct = one_per_problem([row for row in eligible if row["ground_truth"] == "correct"
                               and row["problem_id"] not in used])
    correct = rank(correct, "human_correct")[:targets["human_correct"]]
    groups = {"human_localized_incorrect": high,
              "human_incorrect_ai_localized": low, "human_correct": correct}
    if {key: len(value) for key, value in groups.items()} != targets:
        raise RuntimeError("OPC does not contain enough eligible unique-problem records")
    selected = []
    for group, rows in groups.items():
        cursor = 0
        for split, count in quotas[group].items():
            selected += [(row, group, split) for row in rows[cursor:cursor + count]]
            cursor += count
    selected.sort(key=lambda item: sha(f"m7-opc-output|{item[0]['problem_id']}".encode()))
    license_path = source_root / "LICENSE.md"
    license_digest = sha(license_path.read_bytes())
    records, seed = [], []
    for number, (row, group, split) in enumerate(selected, 1):
        case_id = f"opc250-{number:03d}"
        payload = {key: row[key] for key in ("problem_id", "model_id", "source_index", "problem", "proof")}
        raw_digest = canonical(payload)
        metadata = row.get("metadata") or {}
        domain = ((metadata.get("category") or [None])[0] or metadata.get("competition") or "mathematics")
        records.append({
            "case_id": case_id, "source_uri": f"{REPOSITORY}/tree/{COMMIT}/data/train/discrete/long",
            "source_record_digest": canonical(row), "license_status": "verified_redistributable",
            "license_evidence": f"OPC Apache-2.0 LICENSE.md sha256:{license_digest}",
            "raw_bytes_sha256": raw_digest, "problem": row["problem"], "proof": row["proof"],
            "language": "en", "domain": str(domain),
            "difficulty": str(metadata.get("difficulty") or "unrated"), "split": split,
        })
        issue = (mapped_issue(row, human_localized=group == "human_localized_incorrect")
                 if row["ground_truth"] == "incorrect" else None)
        seed.append({"case_id": case_id, "opc_problem_id": row["problem_id"],
                     "opc_model_id": row["model_id"], "label_group": group,
                     "human_proof_verdict": row["ground_truth"], "prefilled_first_issue": issue,
                     "human_mapping_verification": None})
    manifest = {
        "schema_version": "m7-opc-250-source-0.2" if quality_filtered else "m7-opc-250-source-0.1",
        "status": "candidate_frozen_existing_human_verdicts_mapping_review_pending",
        "repository": REPOSITORY, "commit": COMMIT, "license": "Apache-2.0",
        "license_sha256": license_digest, "record_count": 250,
        "geometry_policy": "exclude prompts containing geometric objects or planar/spatial relations",
        "geometry_records_excluded_before_sampling": geometry_excluded,
        "proof_quality_gate": ({"max_nodes": 100, "max_node_chars": 700, "max_proof_chars": 12000}
                               if quality_filtered else None),
        "label_group_counts": {key: len(value) for key, value in groups.items()},
        "split_counts": {"train": 50, "development": 50, "test": 150},
        "candidate_digest": canonical(records), "seed_annotation_digest": canonical(seed),
        "manual_labor_reduction": "all 250 proof verdicts reuse OPC human labels; 41 non-geometry error locations reuse human spans",
        "limitations": [
            "The remaining 159 incorrect cases use OPC LLM-localized issue positions and categories pending mapping review.",
            "OPC labels are proof judgments, not this project's dependency-graph Gold.",
            "Public benchmark contamination remains possible because OPC is already released.",
            "Geometry exclusion is conservative and keyword-based; borderline shape-based combinatorics is also excluded.",
        ],
    }
    return records, seed, manifest, license_path.read_text()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--duckdb", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--quality-filtered", action="store_true")
    args = parser.parse_args()
    records, seed, manifest, license_text = build(args.source_root, args.duckdb,
                                                   quality_filtered=args.quality_filtered)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "candidate.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records))
    (args.output / "seed_annotations.json").write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n")
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.output / "LICENSE.OpenProofCorpus").write_text(license_text)


if __name__ == "__main__":
    main()
