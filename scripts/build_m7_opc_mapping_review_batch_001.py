"""Build a compact 25-case risk-calibration review for OPC node mappings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/opc_250_v0_1"
OUT = ROOT / "human_review/m7_opc_250_v0_1"


def ranked(rows: list[dict], label: str) -> list[dict]:
    return sorted(rows, key=lambda row: hashlib.sha256(
        f"m7-opc-mapping-review-001|{label}|{row['case_id']}".encode()).hexdigest())


def context(row: dict) -> list[dict]:
    if row["first_error_node"] is None:
        # The sole unmapped case must expose the complete proof; otherwise a
        # reviewer cannot identify the first erroneous node.
        return row["proof_nodes"]
    index = next(i for i, node in enumerate(row["proof_nodes"])
                 if node["node_id"] == row["first_error_node"])
    return row["proof_nodes"][max(0, index - 1):index + 2]


def build() -> tuple[dict, str]:
    item = json.loads((BASE / "node_annotations.json").read_text())
    rows = item["rows"]
    manual = [row for row in rows if row["case_id"] in item["manual_first_error_required"]]
    human = [row for row in rows if row["location_provenance"] == "human_selected_text"]
    ai = [row for row in rows if row["location_provenance"] == "opc_llm_judgment"
          and row["first_error_node"] is not None]
    selected = manual + ranked(human, "human")[:11] + ranked(ai, "ai")[:11]
    packet_rows = []
    lines = ["# M7 OPC-250 非几何节点映射校准：批次 001（25 条）", "",
             "每条只核对首错节点和错误类型。若同意写 `确认`；否则写 `纠正：首错=<节点>；类型=<类型>；理由=<理由>`。", ""]
    for row in selected:
        compact = {"case_id": row["case_id"], "proof_verdict": row["proof_verdict"],
                   "proposed_first_error_node": row["first_error_node"],
                   "proposed_error_type": row["error_type"],
                   "error_description": row["error_description"],
                   "location_provenance": row["location_provenance"],
                   "context_nodes": context(row), "human_verification": None}
        packet_rows.append(compact)
        lines += [f"## {row['case_id']}", "", f"- 位置来源：`{row['location_provenance']}`",
                  f"- 建议首错：`{row['first_error_node']}`", f"- 建议类型：`{row['error_type']}`",
                  f"- 原标注说明：{row['error_description']}", "", "### 节点上下文", ""]
        lines += [f"- **{node['node_id']}**：{node['text']}" for node in compact["context_nodes"]]
        lines += ["", "### 复核", "", "填写：`确认` 或 `纠正：首错=<节点>；类型=<类型>；理由=<理由>`", "", "---", ""]
    packet = {"schema_version": "m7-opc-mapping-review-batch-0.1", "batch_id": "001",
              "status": "pending_human_calibration", "row_count": len(packet_rows),
              "sampling": {"manual_location_required": len(manual), "human_location_mapping_sample": 11,
                           "ai_location_mapping_sample": 11}, "rows": packet_rows}
    return packet, "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    packet, markdown = build()
    (OUT / "mapping_review_batch_001.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    (OUT / "mapping_review_batch_001.md").write_text(markdown + "\n")


if __name__ == "__main__":
    main()
