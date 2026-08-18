"""Render the six changed v0.2 proofs as a Chinese, LaTeX-preserving review."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_m7_opc_v0_2_review_transfer import H2
from scripts.materialize_m7_opc_mapping_review_zh import (
    ERROR_TYPE_ZH, CACHE, quoted_node, translate, translated_long,
)


def main() -> None:
    packet = json.loads((H2 / "supplemental_review_batch_001.json").read_text())
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    lines = ["# M7 OPC-250 v0.2 补充人工复核（6 题）", "",
             "> 这 6 题在质量过滤后更换了模型证明，旧审核不可迁移。自然语言为中文机器翻译，数学公式保留 LaTeX。", "",
             "请检查证明是否错误、首错节点、错误类型和修改方向。", ""]
    for number, row in enumerate(packet["rows"], 1):
        print(f"[{number}/6] translating {row['new_case_id']}", flush=True)
        problem = translated_long(row["problem"], cache)
        is_correct = row["proposed_proof_verdict"] == "correct"
        reason = ("OPC 人工标签认为该证明正确。" if is_correct
                  else translate(row["error_description"], cache).strip())
        node = row["proposed_first_error_node"] or ("无（建议判为正确）" if is_correct else "尚未自动定位")
        error_type = row["proposed_error_type"]
        lines += [f"## 第 {number} 题｜{row['new_case_id']}", "", "### 审查摘要", "",
                  "| 项目 | 内容 |", "|---|---|", f"| 建议首错节点 | **{node}** |",
                  f"| 建议证明结论 | **{'正确' if is_correct else '错误'}** |",
                  f"| 建议错误类型 | {'无' if is_correct else ERROR_TYPE_ZH.get(error_type, error_type) + f'（`{error_type}`）'} |",
                  f"| 判错理由 | {reason} |",
                  f"| 修改方向 | 从节点 {node} 开始修正上述问题，并复查依赖它的后续结论。 |", "",
                  "### 原题（中文释义）", "", f"> {problem.replace(chr(10), chr(10) + '> ')}", "",
                  "<details>", "<summary><strong>展开完整原证明（已按节点编号）</strong></summary>", ""]
        for proof_node in row["proof_nodes"]:
            text = translated_long(proof_node["text"], cache)
            lines += quoted_node(proof_node["node_id"], text,
                                 highlighted=proof_node["node_id"] == row["proposed_first_error_node"]) + [""]
        lines += ["</details>", "", "### 你的复核", "",
                  "填写 `确认`，或填写：", "",
                  "`纠正：证明结论……；首错节点……；错误类型……；修改方向……`", "", "---", ""]
    (H2 / "supplemental_review_batch_001_zh.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
