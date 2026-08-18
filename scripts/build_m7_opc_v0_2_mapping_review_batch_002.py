"""Build mapping-review batch 002 for the remaining OPC-250 v0.2 incorrect proofs.

Batch 001 calibrated the node-mapping pipeline: 11/20 exact agreement, with the
reviewer correcting 16/25 cases and the pipeline overusing the ``other`` error
type (16 proposed vs 3 retained). Batch 002 therefore presents the full proof
context per case, reminds reviewers of the ``proof_end`` option for incomplete
proofs, and asks them to refine ``other`` where possible.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

V2 = ROOT / "data/benchmarks/m7/opc_250_v0_2"
H2 = ROOT / "human_review/m7_opc_250_v0_2"
INHERITED = V2 / "inherited_human_review.json"
SUPPLEMENTAL = H2 / "supplemental_review_batch_001_adjudicated.json"


def stable_rank(case_id: str) -> str:
    return hashlib.sha256(f"m7-opc-v0.2-mapping-review-002|{case_id}".encode()).hexdigest()


def reviewed_case_ids() -> set[str]:
    inherited = json.loads(INHERITED.read_text(encoding="utf-8"))
    ids = {row["new_case_id"] for row in inherited["rows"]}
    supplemental = json.loads(SUPPLEMENTAL.read_text(encoding="utf-8"))
    ids.update(row.get("case_id") for row in supplemental["rows"])
    return ids


def build() -> tuple[dict, str]:
    annotations = json.loads((V2 / "node_annotations.json").read_text(encoding="utf-8"))
    reviewed = reviewed_case_ids()
    pending = [row for row in annotations["rows"]
               if row["proof_verdict"] == "incorrect" and row["case_id"] not in reviewed]
    pending.sort(key=lambda row: stable_rank(row["case_id"]))
    selected = pending[:25]

    packet_rows = []
    lines = [
        "# M7 OPC-250 v0.2 节点映射复核：批次 002（25 条）", "",
        "每条核对：判错理由是否成立、首错节点是否准确、错误类型是否合理、修改方向。",
        "若证明不完整（没有给出所需构造/论证就结束），首错节点可填写 `proof_end`。",
        "若建议类型为 `other`，请尽量改写成具体类型（如 `proof_gap`、`invalid_inference`、`missing_proof`、`missing_bridge_lemma`、`unsupported_external_dependency`、`wrong_conclusion`、`false_generalization`、`missing_assumption`、`algebraic_invalidity`）。",
        "填写 `确认`，或填写 `纠正：首错节点……；错误类型……；修改方向……`。", "",
    ]
    for row in selected:
        compact = {
            "case_id": row["case_id"],
            "proof_verdict": row["proof_verdict"],
            "proposed_first_error_node": row["first_error_node"],
            "proposed_error_type": row["error_type"],
            "location_provenance": row["location_provenance"],
            "proof_nodes": row["proof_nodes"],
            "human_verification": None,
        }
        packet_rows.append(compact)
        lines += [
            f"## 第 {len(packet_rows)} 题｜{row['case_id']}", "",
            "### 审查摘要", "",
            "| 项目 | 内容 |",
            "|---|---|",
            f"| 建议首错节点 | **{row['first_error_node']}** |",
            f"| 建议错误类型 | {row['error_type']}（`{row['location_provenance']}`） |",
            "### 原题与完整原证明（已按节点编号）", "",
            "<details>",
            "<summary><strong>展开完整原证明</strong></summary>", "",
        ]
        for node in row["proof_nodes"]:
            lines += [f"> **{node['node_id']}**", ">", f"> {node['text']}", ""]
        lines += [
            "</details>", "",
            "### 复核", "",
            "填写：`确认` 或 `纠正：首错节点……；错误类型……；修改方向……`", "",
            "---", "",
        ]
    packet = {
        "schema_version": "m7-opc-v0.2-mapping-review-batch-0.2",
        "batch_id": "002",
        "status": "pending_human_review",
        "row_count": len(packet_rows),
        "sampling": "first 25 of remaining unreviewed incorrect cases by stable hash",
        "remaining_incorrect_cases_after_batch": len(pending) - len(packet_rows),
        "rows": packet_rows,
    }
    return packet, "\n".join(lines)


def main() -> None:
    H2.mkdir(parents=True, exist_ok=True)
    packet, markdown = build()
    (H2 / "mapping_review_batch_002.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    (H2 / "mapping_review_batch_002.md").write_text(markdown + "\n")
    print(f"wrote mapping_review_batch_002: {packet['row_count']} rows, "
          f"{packet['remaining_incorrect_cases_after_batch']} remaining after this batch")


if __name__ == "__main__":
    main()
