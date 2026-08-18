"""Import and normalize the completed human review of OPC mapping batch 001."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/opc_250_v0_1"
REVIEW_DIR = ROOT / "human_review/m7_opc_250_v0_1"
SOURCE = REVIEW_DIR / "mapping_review_batch_001_zh.md"
OUT = REVIEW_DIR / "mapping_review_batch_001_adjudicated.json"

# Human decisions normalized from the free-form completed review. `proof_end`
# represents a missing continuation after the final source node.
DECISIONS = {
    "opc250-077": ("accepted_with_normalization", "proof_end", "missing_proof"),
    "opc250-083": ("accepted_with_normalization", "n1", "missing_proof"),
    "opc250-180": ("accepted_with_normalization", "n23", "wrong_conclusion"),
    "opc250-123": ("corrected", "n62", "proof_gap"),
    "opc250-249": ("confirmed", "n23", "other"),
    "opc250-176": ("confirmed", "n27", "other"),
    "opc250-085": ("confirmed", "n12", "other"),
    "opc250-213": ("corrected", "n21", "proof_gap"),
    "opc250-154": ("corrected", "n9", "other"),
    "opc250-243": ("source_verdict_disputed", None, None),
    "opc250-235": ("first_error_rejected_unresolved", None, None),
    "opc250-168": ("confirmed_with_segmentation_warning", "n12", "other"),
    "opc250-076": ("corrected", "n39", "proof_gap"),
    "opc250-153": ("corrected", "n10", "unsupported_inference"),
    "opc250-110": ("corrected", "n9", "invalid_inference"),
    "opc250-038": ("corrected", "n14", "invalid_inference"),
    "opc250-179": ("corrected", "n12", "proof_gap"),
    "opc250-199": ("corrected", "n1", "missing_proof"),
    "opc250-075": ("corrected", "n35", "invalid_inference"),
    "opc250-181": ("corrected", "n4", "missing_bridge_lemma"),
    "opc250-071": ("corrected", "n110", "unsupported_inference"),
    "opc250-158": ("corrected", "n60", "unsupported_inference"),
    "opc250-238": ("corrected", "n8", "proof_gap"),
    "opc250-094": ("corrected", "n1", "missing_proof"),
    "opc250-055": ("corrected", "n47", "algebraic_invalidity"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def responses(markdown: str) -> dict[str, str]:
    parts = re.split(r"^## 第 \d+ 题｜(opc250-\d+)\s*$", markdown, flags=re.MULTILINE)
    result = {}
    for index in range(1, len(parts), 2):
        case_id, body = parts[index:index + 2]
        match = re.search(r"### 你的复核\s*\n(.*?)(?=\n---\s*(?:\n|$))", body, re.DOTALL)
        if not match:
            raise ValueError(f"missing review section: {case_id}")
        text = match.group(1).strip()
        text = re.sub(r"^- 同意上述判断：`确认`\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^- 不同意：`纠正：首错节点……；错误类型……；修改方向……`\s*$", "", text,
                      flags=re.MULTILINE).strip()
        if not text:
            raise ValueError(f"empty human response: {case_id}")
        result[case_id] = text
    return result


def build() -> dict:
    source_bytes = SOURCE.read_bytes()
    raw = responses(source_bytes.decode())
    packet = json.loads((REVIEW_DIR / "mapping_review_batch_001.json").read_text())
    proposed = {row["case_id"]: row for row in packet["rows"]}
    annotations = {row["case_id"]: row for row in json.loads(
        (BASE / "node_annotations.json").read_text())["rows"]}
    if set(raw) != set(DECISIONS) or set(raw) != set(proposed):
        raise ValueError("review cases do not match normalized decisions")
    rows = []
    for case_id in raw:
        status, node, error_type = DECISIONS[case_id]
        valid_nodes = {item["node_id"] for item in annotations[case_id]["proof_nodes"]}
        if node not in valid_nodes | {None, "proof_end"}:
            raise ValueError(f"invalid reviewed node {case_id}: {node}")
        prior = proposed[case_id]
        rows.append({
            "case_id": case_id,
            "review_status": status,
            "proposed_first_error_node": prior["proposed_first_error_node"],
            "proposed_error_type": prior["proposed_error_type"],
            "reviewed_first_error_node": node,
            "reviewed_error_type": error_type,
            "raw_human_response": raw[case_id],
            "usable_as_node_gold": node is not None and error_type is not None,
        })
    usable = [row for row in rows if row["usable_as_node_gold"]]
    proposed_mapped = [row for row in usable if row["proposed_first_error_node"] is not None]
    return {
        "schema_version": "m7-opc-mapping-review-adjudicated-0.1",
        "status": "human_calibration_complete_quality_remediation_required",
        "source_review_sha256": digest(source_bytes),
        "row_count": len(rows),
        "usable_node_gold_count": len(usable),
        "excluded_or_unresolved_count": len(rows) - len(usable),
        "exact_first_error_agreement": sum(
            row["proposed_first_error_node"] == row["reviewed_first_error_node"] for row in proposed_mapped),
        "proposed_mapped_evaluable_count": len(proposed_mapped),
        "segmentation_quality_warning": True,
        "rows": rows,
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
