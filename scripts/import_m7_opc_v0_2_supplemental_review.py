"""Import the completed human review for the six changed OPC v0.2 proofs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/opc_250_v0_2"
REVIEW_DIR = ROOT / "human_review/m7_opc_250_v0_2"
SOURCE = REVIEW_DIR / "supplemental_review_batch_001_zh.md"
OUT = REVIEW_DIR / "supplemental_review_batch_001_adjudicated.json"
SUMMARY = BASE / "human_review_coverage.json"

# Normalize the primary (earliest) defect identified by the completed review.
# Secondary defects remain verbatim in raw_human_response.
DECISIONS = {
    "opc250-214": ("corrected", "incorrect", "n10", "algebraic_invalidity"),
    "opc250-153": ("corrected", "incorrect", "n15", "algebraic_invalidity"),
    "opc250-167": ("corrected", "incorrect", "n47", "algebraic_invalidity"),
    "opc250-039": ("corrected", "incorrect", "n24", "missing_bridge_lemma"),
    "opc250-072": ("corrected", "incorrect", "n4", "wrong_conclusion"),
    "opc250-157": ("corrected", "incorrect", "n9", "missing_assumption"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return digest(payload.encode("utf-8"))


def responses(markdown: str) -> dict[str, str]:
    parts = re.split(r"^## 第 \d+ 题｜(opc250-\d+)\s*$", markdown, flags=re.MULTILINE)
    result = {}
    for index in range(1, len(parts), 2):
        case_id, body = parts[index:index + 2]
        match = re.search(r"### 你的复核\s*\n(.*?)(?=\n---\s*(?:\n|$))", body, re.DOTALL)
        if not match:
            raise ValueError(f"missing review section: {case_id}")
        text = match.group(1).strip()
        if not text or "填写 `确认`" in text:
            raise ValueError(f"empty human response: {case_id}")
        result[case_id] = text
    return result


def build() -> tuple[dict, dict]:
    source_bytes = SOURCE.read_bytes()
    raw = responses(source_bytes.decode())
    packet = json.loads((REVIEW_DIR / "supplemental_review_batch_001.json").read_text())
    proposed = {row["new_case_id"]: row for row in packet["rows"]}
    if set(raw) != set(DECISIONS) or set(raw) != set(proposed):
        raise ValueError("review cases do not match normalized decisions")

    rows = []
    for case_id, response in raw.items():
        status, verdict, node, error_type = DECISIONS[case_id]
        prior = proposed[case_id]
        valid_nodes = {item["node_id"] for item in prior["proof_nodes"]}
        if node not in valid_nodes:
            raise ValueError(f"invalid reviewed node {case_id}: {node}")
        rows.append({
            "case_id": case_id,
            "review_status": status,
            "reviewed_proof_verdict": verdict,
            "proposed_proof_verdict": prior["proposed_proof_verdict"],
            "proposed_first_error_node": prior["proposed_first_error_node"],
            "proposed_error_type": prior["proposed_error_type"],
            "reviewed_first_error_node": node,
            "reviewed_error_type": error_type,
            "raw_human_response": response,
            "usable_as_node_gold": True,
        })

    adjudication = {
        "schema_version": "m7-opc-v0.2-supplemental-review-adjudicated-0.1",
        "status": "six_changed_proofs_human_review_complete",
        "source_review_sha256": digest(source_bytes),
        "row_count": len(rows),
        "usable_node_gold_count": sum(row["usable_as_node_gold"] for row in rows),
        "exact_first_error_agreement": sum(
            row["proposed_first_error_node"] == row["reviewed_first_error_node"] for row in rows
        ),
        "proof_verdict_agreement": sum(
            row["proposed_proof_verdict"] == row["reviewed_proof_verdict"] for row in rows
        ),
        "rows": rows,
    }

    inherited_path = BASE / "inherited_human_review.json"
    inherited = json.loads(inherited_path.read_text())
    seeds = {row["case_id"]: row for row in json.loads(
        (BASE / "seed_annotations.json").read_text(encoding="utf-8"))}
    reviewed_ids = ({row["new_case_id"] for row in inherited["rows"]}
                    | {row["case_id"] for row in adjudication["rows"]})
    ai_localized_ids = {
        case_id for case_id, row in seeds.items()
        if row["label_group"] == "human_incorrect_ai_localized"
    }
    summary = {
        "schema_version": "m7-opc-v0.2-human-review-coverage-0.1",
        "status": "review_transfer_and_supplemental_review_complete",
        "digest_mode": "canonical_json_utf8_v1",
        "inherited_review_sha256": canonical_json_digest(inherited),
        "supplemental_adjudication_sha256": canonical_json_digest(adjudication),
        "exact_proof_reviews_transferred": inherited["exact_proof_review_count"],
        "changed_proofs_newly_reviewed": adjudication["row_count"],
        "total_human_reviewed_cases": inherited["exact_proof_review_count"] + adjudication["row_count"],
        "usable_node_gold_count": (
            inherited["inherited_usable_node_gold_count"] + adjudication["usable_node_gold_count"]
        ),
        "unresolved_or_excluded_count": (
            inherited["exact_proof_review_count"] - inherited["inherited_usable_node_gold_count"]
        ),
        "ai_localized_incorrect_total": len(ai_localized_ids),
        "ai_localized_incorrect_human_reviewed": len(ai_localized_ids & reviewed_ids),
        "remaining_ai_localized_incorrect_cases_pending_mapping_review": len(ai_localized_ids - reviewed_ids),
    }
    return adjudication, summary


def main() -> None:
    adjudication, summary = build()
    OUT.write_text(json.dumps(adjudication, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
