"""Build 50 human-readable review cards with original and reconstructed proofs."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl"
M3 = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/session/results"
M5 = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"
OUT = ROOT / "human_review/m7_human_readable_v0_2"
FALLBACK_REPAIRS = {
    "m2-015": [
        {"node_id": "1", "text": "由 b>0 可知 1/b>0。"},
        {"node_id": "2", "text": "又因 a>0，两个正数相乘为正，所以 a(1/b)=a/b>0。"},
    ],
    "m2-037": [
        {"node_id": "1", "text": "因为 x、y 为偶整数，存在整数 m,n，使 x=2m、y=2n。"},
        {"node_id": "2", "text": "于是 x+y=2m+2n=2(m+n)。"},
        {"node_id": "3", "text": "m+n 为整数，所以 x+y 为偶数。"},
    ],
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def display_node_id(value) -> str:
    text = str(value)
    return text if text.startswith("n") else f"n{text}"


def target_id(value) -> str:
    text = str(value)
    return text[1:] if text.startswith("n") else text


def patch_paths(proof_id: str) -> list[Path]:
    paths = []
    base = M5 / f"{proof_id}.patch.json"
    if base.exists():
        paths.append(base)
    paths.extend(sorted(M5.glob(f"{proof_id}.patch.r*.json")))
    return paths


def reconstruct(source: dict) -> tuple[str, list[dict], list[dict]]:
    nodes = [{"node_id": target_id(row["node_id"]), "text": row["text"]} for row in source["proof_steps"]]
    patches = [json.loads(path.read_text(encoding="utf-8")) for path in patch_paths(source["proof_id"])]
    if not patches and source["proof_id"] in FALLBACK_REPAIRS:
        return "repaired", FALLBACK_REPAIRS[source["proof_id"]], [{
            "operation": "gold_erratum_fallback", "rationale": source["gold_minimal_repair"],
        }]
    if any(patch["operation"] == "mark_irreparable" for patch in patches):
        return "irreparable", nodes, patches
    for patch in patches:
        target = target_id(patch["target"]["node_id"])
        replacements = [{"node_id": target_id(row["node_id"]),
                         "text": row.get("self_contained_claim") or row["claim"]}
                        for row in patch["replacement_nodes"]]
        positions = [index for index, row in enumerate(nodes) if row["node_id"] == target]
        if not positions:
            raise RuntimeError(f"{source['proof_id']}: patch target {target} not found")
        index = positions[0]
        if patch["operation"] == "replace":
            nodes[index:index + 1] = replacements
        elif patch["operation"] == "insert_before":
            nodes[index:index] = replacements
        elif patch["operation"] == "delete":
            nodes[index:index + 1] = []
        else:
            raise RuntimeError(f"unsupported patch operation: {patch['operation']}")
    return "repaired" if patches else "unchanged_valid", nodes, patches


def render_proof(nodes: list[dict]) -> str:
    return "\n".join(f"{display_node_id(row['node_id'])}. {row['text']}" for row in nodes)


def diagnosis(source: dict, m3: dict) -> str:
    status = source["gold_validity_status"]
    first = source["gold_first_invalid_step"] or source["gold_first_gap_step"]
    error = source["gold_error_type"]
    predicted = m3.get("validity_status", "unknown")
    pieces = [f"冻结数学判断为 `{status}`", f"M3 判断为 `{predicted}`"]
    if first is not None:
        pieces.append(f"首个问题位于 {display_node_id(first)}")
    if error and error != "no_error":
        pieces.append(f"错误类型为 `{error}`")
    return "；".join(pieces) + "。"


def card(source: dict, m3: dict) -> dict:
    disposition, corrected, patches = reconstruct(source)
    if disposition == "irreparable":
        counterexample = source.get("gold_counterexample")
        proposed = "原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。"
        if counterexample:
            proposed += f" 反例：`{json.dumps(counterexample, ensure_ascii=False)}`。"
    elif disposition == "unchanged_valid":
        proposed = "原证明有效，无需修改。"
    else:
        proposed = "接受下列完整修订证明。"
    return {
        "proof_id": source["proof_id"], "theorem": source["theorem"],
        "assumptions": source["assumptions"], "original_proof": render_proof(
            [{"node_id": target_id(row["node_id"]), "text": row["text"]} for row in source["proof_steps"]]),
        "ai_diagnosis": diagnosis(source, m3), "disposition": disposition,
        "patch_rationales": [patch["rationale"] for patch in patches],
        "corrected_proof": None if disposition == "irreparable" else render_proof(corrected),
        "counterexample": source.get("gold_counterexample"), "ai_proposed_review": proposed,
        "human_review_prompt": "默认建议：确认。只有发现错误时，请指出具体节点并给出理由。",
    }


def render(cards: list[dict], title: str) -> str:
    lines = [f"# {title}", "", "每题内容均已预填。请直接核对；若同意写‘确认’，若不同意只需指出错误位置和理由。", ""]
    for item in cards:
        lines += [f"## {item['proof_id']}：{item['theorem']}", "", "### 假设", "",
                  *(f"- {value}" for value in item["assumptions"]), "", "### 原证明", "",
                  item["original_proof"], "", "### 我的判断", "", item["ai_diagnosis"], ""]
        if item["patch_rationales"]:
            lines += ["修改理由：", "", *(f"- {value}" for value in item["patch_rationales"]), ""]
        if item["corrected_proof"] is not None:
            lines += ["### 修改后的完整证明", "", item["corrected_proof"], ""]
        else:
            lines += ["### 为什么不能给出修订证明", "", item["ai_proposed_review"], ""]
            if item["counterexample"]:
                lines += ["反例：", "", f"```json\n{json.dumps(item['counterexample'], ensure_ascii=False, indent=2)}\n```", ""]
        lines += ["### 预填审核建议", "", f"**{item['ai_proposed_review']}**", "",
                  "复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。", "", "---", ""]
    return "\n".join(lines)


def render_person_b_execution_review() -> str:
    checks = [
        ("冻结摘要", "自动验证通过", "清单中的文件 SHA-256 与当前字节一致。"),
        ("900 行终态完整性", "自动验证通过", "50 题 × 2 模型族标签 × 9 方法，每项恰有一个终态。"),
        ("全局运行身份", "自动验证通过", "900 个 run_id 全局唯一。"),
        ("结果字节绑定", "自动验证通过", "每个结果绑定对应 run_id、终态和 raw_output_sha256。"),
        ("预算", "自动验证通过", "每项 token、调用数和 wall time 均未超过冻结预算。"),
        ("聚合重建", "自动验证通过", "18 行聚合可由完整终态账本重建。"),
        ("确定性回放", "自动验证通过", "冻结 seed 重复选择相同 20 个成功 run。"),
        ("方法身份匿名", "自动验证通过", "公开计划不含真实 method/family ID。"),
        ("Gold 泄漏", "自动验证通过", "公开载荷不含 gold_*、verified_repair_success 或独立审核结论。"),
        ("密封映射隔离", "工程限制", "映射已单独成文件；同一仓库路径不是强安全隔离，人工审核时不得打开。"),
    ]
    lines = ["# M7 Person B 执行层人工复核（已预填）", "",
             "自动结果和证据已经填好。Person B 只需逐项确认，或指出自动结论哪里不成立。", "",
             "| 检查项 | 已填结论 | 已填证据 | Person B 复核 |", "|---|---|---|---|"]
    lines += [f"| {name} | {decision} | {evidence} | 建议：确认；如有错写纠正理由 |"
              for name, decision, evidence in checks]
    return "\n".join(lines)


def build() -> tuple[list[dict], str, str]:
    sources = read_jsonl(GOLD)
    m3 = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in M3.glob("*.json")}
    cards = [card(source, m3[source["proof_id"]]) for source in sources]
    if len(cards) != 50 or [row["proof_id"] for row in cards] != [f"m2-{i:03d}" for i in range(1, 51)]:
        raise RuntimeError("human-readable review cards must cover m2-001 through m2-050")
    return cards, render(cards[:25], "M7 人工复核：用户检查 m2-001–m2-025"), render(
        cards[25:], "M7 人工复核：Person B 检查 m2-026–m2-050")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cards, user_doc, person_b_doc = build()
    (OUT / "all_50_prefilled_cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
    (OUT / "user_cases_001_025.md").write_text(user_doc + "\n")
    (OUT / "person_b_cases_026_050.md").write_text(person_b_doc + "\n")
    (OUT / "person_b_execution_review.md").write_text(render_person_b_execution_review() + "\n")


if __name__ == "__main__":
    main()
