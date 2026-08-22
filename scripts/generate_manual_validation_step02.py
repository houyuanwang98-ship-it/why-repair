"""生成第二步题目原文、来源与数据边界人工审核表。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "manual_validation" / "step02_source_and_data_boundary_review.md"


def rows(path: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def block(value: object) -> str:
    if value in (None, "", []):
        return "（未提供）"
    if isinstance(value, list):
        value = "\n".join(f"- {item}" for item in value)
    return str(value).replace("```", "``\\`")


def manual_fields() -> str:
    return """
#### 人工检验（由审核者填写）

- 原始来源已打开并逐项对照：________（是／否／不确定）
- 来源定位与版本可靠：________（是／否／不确定）
- 题干忠实性：________（通过／需修订／不通过）
- 参考证明确实对应本题：________（是／否／不确定／不适用）
- 假设完整：________（是／否／不确定）
- 定义域、值域与量词正确：________（是／否／不确定）
- OCR、翻译、公式、Unicode、换行及规范化未改变数学意义：________（是／否／不确定）
- 歧义或自相矛盾：________（无／有／不确定）
- 歧义、缺失条件或文本差异说明：

  ________________________________________________________________________________

- 与开发集、Pilot、正式测试集或定理库的重复／近重复／泄漏风险：________（无／有／不确定）
- 重复或泄漏证据及关联题号：

  ________________________________________________________________________________

- 对目标领域与难度具有代表性：________（是／否／不确定）
- 代表性说明：

  ________________________________________________________________________________

- 注入错误忠实性：________（通过／不通过／不适用／不确定）
- 预期错误、实际错误及非预期变化：

  ________________________________________________________________________________

- 权利状态：________（可用／受限／不确定）
- 权利与用途限制说明：

  ________________________________________________________________________________

- 必要行动：________（无需行动／修订／补充来源／去重／重新划分／排除／升级复核）
- 最终决定：________（纳入／修订后纳入／排除／不确定）
- 判断依据与证据路径：

  ________________________________________________________________________________

- 审核者：________
- 审核时间：________
- 初次结果：________（通过／不通过／需修订／不确定）
- 复核者及复核结果：____________________________________________________________
"""


def card(index: int, group: str, item: dict, source_path: str, machine: list[str]) -> str:
    case_id = item.get("case_id") or item.get("proof_id") or item.get("id") or f"未命名-{index}"
    theorem = item.get("problem") or item.get("theorem") or "（未提供）"
    proof = item.get("proof") or item.get("proof_steps") or item.get("flawed_proof_steps") or "（未提供）"
    assumptions = item.get("assumptions", [])
    meta = []
    for key, label in (("domain", "领域"), ("topic", "主题"), ("difficulty", "难度"), ("language", "语言"), ("split", "数据划分"), ("source_uri", "来源地址"), ("license_status", "许可状态"), ("license_evidence", "许可证据")):
        if key in item:
            meta.append(f"- {label}：`{item[key]}`")
    return f"""
### 第 {index:03d} 题：{case_id}

- 数据组：{group}
- 对象路径：`{source_path}`
{chr(10).join(meta)}

#### 题干（仓库原文）

```text
{block(theorem)}
```

#### 显式假设（仓库原文）

{block(assumptions)}

#### 参考证明或证明步骤（仓库原文）

```text
{block(proof)}
```

#### 机器验证结果（仅作定位证据，不代表人工通过）

{chr(10).join(f'- {x}' for x in machine)}
{manual_fields()}
"""


def main() -> None:
    specs: list[tuple[str, str, list[dict], list[str]]] = []

    m2a = "data/benchmarks/m2/source/pilot_50.jsonl"
    specs.append(("M2 工程 Pilot（m2-001 至 m2-050）", m2a, rows(m2a), [
        "JSONL 可解析：是", f"文件行数：50", f"文件 SHA-256：`{sha256(m2a)}`", "Manifest 声明来源行数：50", "Manifest 严格接受状态：因缺少历史人工与来源证据而阻塞", "稳定外部来源定位：未随逐题记录提供，必须人工补充",
    ]))
    m2b = "data/benchmarks/m2/source/pilot_B50.jsonl"
    specs.append(("M2 B50 校准／补充 Pilot（B01 至 B50）", m2b, rows(m2b), [
        "JSONL 可解析：是", "文件行数：50", f"文件 SHA-256：`{sha256(m2b)}`", "逐题稳定外部来源定位：未提供，必须人工补充", "许可与用途字段：未在逐题记录中提供",
    ]))
    opc = "data/benchmarks/m7/opc_250_v0_2/candidate.jsonl"
    specs.append(("OPC-250 v0.2", opc, rows(opc), [
        "JSONL 可解析：是", "Manifest 声明记录数：250", f"当前文件 SHA-256：`{sha256(opc)}`", "Manifest 候选摘要：`1b7b0195fd00b522e1e51e061e2c42ff34c81d2022cc1ca03c346555503adce9`", "许可机器字段：Apache-2.0／verified_redistributable", "机器关键词规则已在抽样前排除 725 条几何候选；该规则不能替代人工边界判断", "现有人工覆盖：25 题；其中可用节点 Gold 23 题、未解决或排除 2 题；另有 141 条 AI 定位错误题仍待映射复核",
    ]))
    proofnet = "data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl"
    specs.append(("ProofNet-250 v0.1", proofnet, rows(proofnet), [
        "JSONL 可解析：是", "Manifest 声明记录数：250", f"当前文件 SHA-256：`{sha256(proofnet)}`", "Manifest 候选摘要：`670c4596a688c7ae345aadd6e4a1ab3576796bbbdf641181182d2afbf8573efa`", "许可机器字段：MIT／verified_redistributable", "机器近重复阈值：0.85；已排除 4 条跨划分近重复记录", "Manifest 状态：来源基线已冻结，错误派生与人工 Gold 待完成", "形式化陈述仅在私有来源索引中，按清单不得进入模型输入",
    ]))

    for path, name in (("data/samples/algebra_diagnosis_cases.jsonl", "代数诊断样例"), ("data/samples/algebra_pilot_3.jsonl", "代数三题 Pilot 样例")):
        specs.append((name, path, rows(path), ["JSONL 可解析：是", f"当前文件 SHA-256：`{sha256(path)}`", "逐题稳定外部来源、许可和用途字段：未提供", "样例可能是人工构造或注入错误；必须人工核对注入前后语义与非预期变化"]))

    explicit_path = "data/samples/explicit_subquestion_demo.jsonl"
    expanded = []
    for parent in rows(explicit_path):
        for part in parent.get("explicit_subquestions", []):
            expanded.append({"id": f"{parent['id']}-第{part['label']}问", "domain": parent.get("domain"), "topic": parent.get("topic"), "assumptions": parent.get("assumptions", []), "theorem": part.get("theorem"), "proof_steps": part.get("proof_steps")})
    specs.append(("显式分问演示样例", explicit_path, expanded, ["JSONL 可解析：是", f"当前文件 SHA-256：`{sha256(explicit_path)}`", "机器展开结果：1 条父记录展开为 2 道独立分问", "逐题稳定外部来源、许可和用途字段：未提供"]))

    total = sum(len(items) for _, _, items, _ in specs)
    intro = f"""# 第二步：题目原文、来源与数据边界人工审核表

## 简介

本表依据《项目人工审核与验证执行手册》第二步生成，用于逐题确认系统处理的是正确、完整、来源可靠且适合目标实验与发布用途的数学题目。机器解析、哈希、许可证字段、关键词过滤和相似度结果只用于定位与风险提示，不能替代人工阅读原始来源、核对数学语义和判断权利边界。

本轮按仓库中的唯一题目源对象列出，共 **{total} 道**。实验输入、预测、Gold、缓存和运行结果中的同题副本不重复建卡；审核时若发现同题不同版本或不同摘要，必须新增独立记录。英文来源题干和证明保留原文，因为本步骤要求逐字核对来源；表内全部审核说明、判断字段和填写提示均为中文。

## 审核要求

1. 为每道题同时打开本表所列仓库版本与原始来源，逐项核对题干、证明、公式、符号、假设、量词、定义域和值域。
2. 文本差异只能记为“无语义影响”“需要修订”“无法确定”或“必须排除”；不能仅凭哈希一致、OCR 成功或字符串相似度判定通过。
3. 必须判断歧义、自相矛盾、缺失条件、参考证明错配、样本代表性、跨数据集重复／泄漏以及目标研究和发布用途是否允许。
4. 对人工或模型注入错误的题，必须比较注入前后版本，确认错误只发生在预定位置、自然且未改变原定理或引入额外错误。
5. 具有语义影响的修订必须由另一名审核者复查；不确定时填写“不确定”，不得猜测通过。
6. 每题必须填写全部人工字段。仅有机器验证结果的题仍视为“未开始人工审核”。

## 本轮范围与机器盘点

| 数据组 | 题数 | 主要机器状态 |
|---|---:|---|
| M2 工程 Pilot | 50 | 可解析；严格接受因历史人工与来源证据缺失而阻塞 |
| M2 B50 | 50 | 可解析；逐题来源与许可字段缺失 |
| OPC-250 v0.2 | 250 | 可解析；许可字段已验证；人工映射覆盖尚不完整 |
| ProofNet-250 v0.1 | 250 | 可解析；来源基线冻结；错误派生与人工 Gold 待完成 |
| 三类仓库样例 | 8 | 可解析；来源、许可与注入前版本多未提供 |
| **合计** | **{total}** | **所有题均仍需本步骤人工审核** |

## 公共审核记录

- 验证批次编号：________
- 分支：________
- 提交 SHA：________
- 审核范围清单路径：________
- 审核负责人：________
- 证据目录：________
- 已知限制：____________________________________________________________________

## 逐题审核
"""
    parts = [intro]
    index = 0
    for group, path, items, shared_machine in specs:
        parts.append(f"\n## 数据组：{group}\n")
        for item in items:
            index += 1
            item_machine = list(shared_machine)
            if item.get("raw_bytes_sha256"):
                item_machine.append(f"记录携带原始字节 SHA-256：`{item['raw_bytes_sha256']}`；仓库中未含对应原始字节，当前无法独立重算")
            if item.get("source_record_digest"):
                item_machine.append(f"记录携带来源记录摘要：`{item['source_record_digest']}`")
            if item.get("gold_first_invalid_step") is not None:
                item_machine.append(f"已有机器／工程 Gold 首错步：`{item['gold_first_invalid_step']}`；本步骤不得据此推断题面忠实")
            if item.get("gold_error_type"):
                item_machine.append(f"已有机器／工程 Gold 错误类型：`{item['gold_error_type']}`；仅作注入错误核对线索")
            parts.append(card(index, group, item, path, item_machine))

    parts.append("""
## 批次汇总与关闭检查

- 对象总数：608
- 已人工通过：________
- 不通过：________
- 需修订：________
- 不确定：________
- 排除：________
- 各分类数量之和等于对象总数：________（是／否）
- 所有纳入样本均可回溯至可靠来源：________（是／否）
- 所有语义影响修订均已由另一人复查：________（是／否／不适用）
- 数据集边界明确且无未处理实质泄漏：________（是／否）
- 来源或使用条件不确定的样本均未进入正式结果：________（是／否）
- 阻塞问题：____________________________________________________________________
- 下一步行动：__________________________________________________________________
- 任务状态：________（未开始／进行中／阻塞／通过）
""")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(parts), encoding="utf-8", newline="\n")
    print(f"已生成 {OUT}，共 {index} 道。")


if __name__ == "__main__":
    main()
