"""生成第二至第九步的双人中文人工检验工作包。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "manual_validation"
PEOPLE = (("person_a", "Person A"), ("person_b", "Person B"))
PERSON_B_STEP2_COMPLETION_DATE = "2026-08-28"
PERSON_B_STEP3_COMPLETION_DATE = "2026-08-29"


def jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(x) for x in (ROOT / path).read_text(encoding="utf-8").splitlines() if x.strip()]


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def text(value: Any) -> str:
    if value in (None, "", []):
        return "（未提供）"
    if isinstance(value, list):
        return "\n".join(f"- {x if not isinstance(x, dict) else json.dumps(x, ensure_ascii=False)}" for x in value)
    return str(value).replace("```", "``\\`")


def case_id(item: dict[str, Any]) -> str:
    return str(item.get("case_id") or item.get("proof_id") or item.get("id") or item.get("run_id") or "未命名对象")


def theorem(item: dict[str, Any]) -> str:
    return str(item.get("problem") or item.get("theorem") or item.get("goal") or "（未提供）")


def source_cases(include_samples: bool = True) -> list[dict[str, Any]]:
    specs = [
        ("M2 工程 Pilot", "data/benchmarks/m2/source/pilot_50.jsonl"),
        ("M2 B50", "data/benchmarks/m2/source/pilot_B50.jsonl"),
        ("OPC-250 v0.2", "data/benchmarks/m7/opc_250_v0_2/candidate.jsonl"),
        ("ProofNet-250 v0.1", "data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl"),
    ]
    if include_samples:
        specs += [
            ("代数诊断样例", "data/samples/algebra_diagnosis_cases.jsonl"),
            ("代数 Pilot 样例", "data/samples/algebra_pilot_3.jsonl"),
        ]
    out: list[dict[str, Any]] = []
    for group, path in specs:
        for row in jsonl(path):
            row = dict(row)
            row["_group"], row["_path"], row["_file_digest"] = group, path, digest(path)
            out.append(row)
    if include_samples:
        path = "data/samples/explicit_subquestion_demo.jsonl"
        for parent in jsonl(path):
            for part in parent.get("explicit_subquestions", []):
                out.append({"id": f"{parent['id']}-第{part['label']}问", "domain": parent.get("domain"), "assumptions": parent.get("assumptions", []), "theorem": part.get("theorem"), "proof_steps": part.get("proof_steps"), "_group": "显式分问样例", "_path": path, "_file_digest": digest(path)})
    return out


def weight(item: dict[str, Any]) -> int:
    proof = item.get("proof") or item.get("proof_steps") or item.get("flawed_proof_steps") or ""
    return max(1, len(str(proof)) // 800 + 1)


def balance(items: list[dict[str, Any]], weight_key: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bins: list[list[dict[str, Any]]] = [[], []]
    loads = [0, 0]
    for item in sorted(items, key=lambda x: (-int(x.get(weight_key, weight(x))) if weight_key else -weight(x), case_id(x))):
        target = 0 if loads[0] <= loads[1] else 1
        bins[target].append(item)
        loads[target] += int(item.get(weight_key, weight(item))) if weight_key else weight(item)
    for bucket in bins:
        bucket.sort(key=lambda x: (x.get("_group", ""), case_id(x), x.get("_path", "")))
    return bins[0], bins[1]


COMMON = """
## 公共记录

- 验证批次编号：________
- 分支：________
- 提交 SHA：________
- 对象摘要或范围清单：________
- 审核者：________
- 审核角色：________
- 审核时间：________
- 证据目录：________
- 已知限制：____________________________________________________________________

## 执行纪律

1. 逐项独立判断，不复制系统预测或另一审核者答案。
2. 机器结果只作定位线索，不构成数学、语义、权利或发布正确性证据。
3. 不确定时填写“不确定”或“需修订”，不得猜测通过。
4. 保留原始意见；复核与裁决不得覆盖初次记录。
5. 每个对象都必须填写结论、理由和证据路径，空白对象视为未审核。
"""


def header(step: int, title: str, person: str, intro: str, requirements: list[str], count: int, unit: str, *, batch_mode: bool = False) -> str:
    req = "\n".join(f"{i}. {x}" for i, x in enumerate(requirements, 1))
    discipline = COMMON if not batch_mode else COMMON.replace("5. 每个对象都必须填写结论、理由和证据路径，空白对象视为未审核。", "5. 每个抽样、异常或需要裁决的对象都必须填写结论、理由和证据路径；其余对象由批次决定覆盖。")
    section = "报告内容" if batch_mode else "逐项人工检验"
    return f"# 第{step}步：{title}——{person}工作包\n\n## 简介\n\n{intro}\n\n本工作包分配给 **{person}**，共 **{count} {unit}**。只完成本文件不足以关闭该步骤；必须与另一人的工作包合并、比较分歧并完成必要裁决。\n\n## 本步要求\n\n{req}\n{discipline}\n## {section}\n"


def finish(count: int, unit: str, requirements: list[str]) -> str:
    checklist = "\n".join(f"- [ ] {item}" for item in requirements)
    return f"""
## 批次级人工验证清单

本步骤不要求逐个对象重复填写审核表。审核者应通读本文件列出的全部对象，结合机器检查定位异常，抽查正常对象，并在发现问题时把对象编号、理由与证据集中登记在下方。

{checklist}

### 抽样与异常记录

- 抽样方法、覆盖范围与样本量：__________________________________________________
- 机器异常及人工复核结果：______________________________________________________
- 发现问题的对象编号、理由与证据路径：__________________________________________
- 需要另一审核者或第三方裁决的分歧：____________________________________________

### 工作包汇总与最终决定

- 分配总数：{count} {unit}
- 已完成：________
- 通过：________
- 不通过：________
- 需修订：________
- 不确定：________
- 排除／不适用：________
- 分类数量与分配总数一致：________（是／否）
- 阻塞问题：____________________________________________________________________
- 下一步行动：__________________________________________________________________
- 最终决定：________（通过／修订后通过／部分排除／不通过／不确定）
- 决定理由与证据路径：__________________________________________________________
- 本工作包状态：________（未开始／进行中／阻塞／完成）
"""


def source_boundary_finish(person: str, count: int) -> str:
    if person == "Person B":
        return f"""
## Person B 批次级人工审核

### 审核完成记录

- 人工审核覆盖：**{count}／{count} 道题**
- 完成状态：**已完成全部题目的人工审核**
- 完成确认日期：{PERSON_B_STEP2_COMPLETION_DATE}
- 确认来源：项目所有者在当前任务中确认
- 说明：当前任务只确认了全量人工审核已经完成，未提供逐项审核结论、异常统计、代表性结论或最终纳入决定。下列未知项据实标为“未提供”，不以完成状态推定全部题目通过。

### 一、机器检查覆盖确认

- 全量对象数与本工作包一致：是（304／304）
- 已运行的机器检查及版本／提交：未提供
- 机器异常总数及分类统计（来源／解析／许可／重复泄漏／语义差异／其他）：未提供
- 无法由当前机器检查覆盖的已知限制：未提供

### 二、分层代表性审核

| 分层维度 | 当前分布／证据 | 代表性判断 | 缺口、偏差或处置 |
|---|---|---|---|
| 数据组与来源族 | 本文件列出的 304 道分配题目 | 未提供 | 待补充审核结论 |
| 数学领域／主题 | 本文件各题原始记录 | 未提供 | 待补充审核结论 |
| 难度与证明长度／结构 | 本文件各题完整题面与证明 | 未提供 | 待补充审核结论 |
| 正确／错误证明及错误类型 | 本文件及对应 JSONL 源记录 | 未提供 | 待补充审核结论 |
| 训练、开发、Pilot、测试的边界 | 本文件列出的数据组与源路径 | 未提供 | 待补充审核结论 |

- 总体代表性结论：不确定（未提供审核结论）
- 代表性理由与证据路径：未提供

### 三、人工复核覆盖

- 人工复核范围：本工作包全部 304 道题
- 覆盖方式：全量人工审核（由项目所有者确认）
- 逐项观察与结论：当前任务未提供，未作推定

### 四、异常与边界项登记

- 异常或边界项清单：未提供
- 需要裁决的对象：未提供
- 说明：“未提供”不等同于“无异常”。

### 五、最终决定

- 最终决定：不确定（最终纳入结论未提供）
- 纳入范围／排除清单：未提供
- 决定理由：未提供
- 需要升级至另一审核者／第三方／许可审查的事项：未提供
- 审核者：Person B
- 审核时间：{PERSON_B_STEP2_COMPLETION_DATE}（完成确认日期）
- 证据路径：`docs/manual_validation/person_b/step02_source_and_boundary.md` 及文件内列出的 JSONL 原始记录
- 人工审核执行状态：完成（304／304）
- 结论汇总状态：待补充
"""
    return f"""
## {person} 批次级人工审核

本步骤不要求对 **{count} 道题**重复填写来源、题干、OCR、重复、权利等字段。机器检查负责全量发现；{person} 只对分布代表性、机器异常和最终纳入范围作人工判断。

### 一、机器检查覆盖确认

- 全量对象数与本工作包一致：________（是／否）
- 已运行的机器检查及版本／提交：________________________________________________
- 机器异常总数及分类统计（来源／解析／许可／重复泄漏／语义差异／其他）：____________
- 无法由当前机器检查覆盖的已知限制：____________________________________________

### 二、分层代表性审核

| 分层维度 | 当前分布／证据 | 代表性判断（合适／不合适／不确定） | 缺口、偏差或处置 |
|---|---|---|---|
| 数据组与来源族 | ________ | ________ | ________ |
| 数学领域／主题 | ________ | ________ | ________ |
| 难度与证明长度／结构 | ________ | ________ | ________ |
| 正确／错误证明及错误类型 | ________ | ________ | ________ |
| 训练、开发、Pilot、测试的边界 | ________ | ________ | ________ |

- 总体代表性结论：________（合适／不合适／不确定）
- 代表性理由与证据路径：________________________________________________________

### 三、抽样语义复核

抽样用于校验机器检查没有系统性漏报；不是把全量检查重新人工执行。每个数据组至少抽样 ________ 题，并覆盖机器异常、边界项及不同领域／难度。

| 样本／题号 | 抽样理由 | 人工观察（题意、来源、语义或权利） | 是否与机器结果一致 | 后续行动 |
|---|---|---|---|---|
| ________ | ________ | ________ | ________ | ________ |
| ________ | ________ | ________ | ________ | ________ |
| ________ | ________ | ________ | ________ | ________ |

### 四、异常与边界项登记表

仅登记机器标红、抽样不一致或需要裁决的对象；无异常时填写“无”。

| 题号／对象 | 触发原因 | 人工裁决 | 证据路径 | 处置 |
|---|---|---|---|---|
| ________ | ________ | ________ | ________ | ________ |
| ________ | ________ | ________ | ________ | ________ |
| ________ | ________ | ________ | ________ | ________ |

### 五、最终决定

- 最终决定：________（纳入／修订后纳入／部分排除／全部排除／不确定）
- 纳入范围／排除清单：__________________________________________________________
- 决定理由（结合代表性、机器异常与抽样结果）：__________________________________
- 需要升级至另一审核者／第三方／许可审查的事项：________________________________
- 审核者：________
- 审核时间：________
- 证据路径：____________________________________________________________________
- 本工作包状态：________（未开始／进行中／阻塞／完成）
"""


def independent_gold_finish(person: str, count: int, requirements: list[str]) -> str:
    if person != "Person B":
        return finish(count, "道正式样本", requirements)
    return f"""
## Person B 批次级人工审核

### 审核完成记录

- 人工审核覆盖：**{count}／{count} 道正式样本**
- 完成状态：**已完成 Person B 全部独立人工审核**
- 完成确认日期：{PERSON_B_STEP3_COMPLETION_DATE}
- 确认来源：项目所有者在当前任务中确认
- 审核范围：M2 工程 Pilot 50 道、M2 B50 50 道、OPC-250 v0.2 250 道、ProofNet-250 v0.1 250 道
- 结构化完成记录：`step03_completion_record.json`
- 说明：当前确认覆盖人工审核执行是否完成；未随任务提供逐题判定、分类统计、异常清单或 A/B 分歧裁决表。因此不从“已审核”推定“全部通过”，也不据此覆盖现有 Gold。

### 执行纪律确认

- [x] 已覆盖本工作包列出的 600 道正式样本。
- [x] 审核者身份按 Person B 登记。
- [x] 完成事实由项目所有者明确确认。
- [ ] 未查看系统预测或 Person A 答案：当前任务未提供可独立验证的锁定／隔离证据。
- [ ] 数学能力覆盖、超范围升级记录：当前任务未提供。
- [ ] 下游阻塞与新数学错误区分记录：当前任务未提供逐题结果，无法复核。
- [ ] A/B 分歧与第三方裁决：须待 Person A 结果合并后完成。

### 分组覆盖

| 数据组 | 已审核／分配 | 执行状态 | 逐题结论同步状态 |
|---|---:|---|---|
| M2 工程 Pilot | 50／50 | 完成 | 未随任务提供 |
| M2 B50 | 50／50 | 完成 | 未随任务提供 |
| OPC-250 v0.2 | 250／250 | 完成 | 未随任务提供 |
| ProofNet-250 v0.1 | 250／250 | 完成 | 未随任务提供 |
| **合计** | **600／600** | **完成** | **仅同步完成元数据** |

### 结果、异常与裁决登记

- 通过／不通过／需修订／不确定／排除分类：未提供，不能可靠汇总。
- 发现问题的对象编号、理由与证据路径：未提供。
- Person A / Person B 分歧：尚未比较；不得登记为“无分歧”。
- 第三方裁决：尚未提供。
- 数据同步处置：保存 600／600 完成状态、四个源数据文件 SHA-256 和边界说明；不修改逐题 Gold 字段。

### 工作包汇总与最终决定

- 分配总数：{count} 道正式样本
- 已完成：{count}
- 未完成：0
- 人工审核执行状态：**完成**
- 结论汇总状态：**待逐题结果导入**
- A/B 合并与裁决状态：**待 Person A 结果比较及必要的第三方裁决**
- 最终 Gold 冻结状态：**未关闭**
- 阻塞问题：缺少逐题 Person B 判定、分类统计、异常清单、独立性证据及 A/B 裁决结果。
- 下一步行动：导入 Person B 逐题结果；与 Person A 结果逐字段比较；保留双方原始意见；对未解决分歧执行第三方裁决后再冻结最终 Gold。
- 最终决定：**人工审核执行完成；Step 3 总体验收暂不关闭**
- 决定理由与证据路径：项目所有者确认 600／600 已审核；详细结果和联合裁决证据尚未进入仓库。证据见本文件与 `step03_completion_record.json`。
- 本工作包状态：**人工执行完成／结论合并待办**
"""


def source_boundary_overview(person: str, items: list[dict[str, Any]]) -> str:
    groups: dict[tuple[str, str], int] = {}
    for item in items:
        key = (str(item["_group"]), str(item["_path"]))
        groups[key] = groups.get(key, 0) + 1
    rows = "\n".join(
        f"| {group} | {count} | `{path}` | JSON 解析与文件摘要 |"
        for (group, path), count in groups.items()
    )
    return f"""
## 全量机器盘点（无需逐题人工填写）

本工作包覆盖 **{len(items)} 道题**。题干、证明、来源、许可证、近重复和数据边界的原始记录均保留在下列数据文件中；{person} 不需要逐题填写。实际运行的机器检查结果、异常数量和局限统一填写在文末人工审核表中。

| 数据组 | 对象数 | 原始记录路径 | 基础机器检查 |
|---|---:|---|---|
{rows}

## 全部原题与证明（保留 Markdown/LaTeX）

以下对象从 JSONL 源记录直接提取，并按 {person} 的原始分配顺序完整串联。题干、假设、证明和数学表达均不翻译、不改写；Markdown 与 LaTeX 保持原格式，以便在 VS Code 预览中渲染。各题不设置人工填空，审核者只在文件末尾填写汇总标准。
"""


def original_markdown(value: Any, *, proof: bool = False) -> str:
    if value in (None, "", []):
        return "（原始记录未提供）"
    if not isinstance(value, list):
        return str(value)
    blocks: list[str] = []
    for index, entry in enumerate(value, 1):
        if isinstance(entry, dict):
            label = entry.get("node_id") or entry.get("step_id") or entry.get("id") or index
            content = entry.get("text") or entry.get("content") or json.dumps(entry, ensure_ascii=False)
            blocks.append(f"{'#####' if proof else '-'} {'证明步骤 ' if proof else ''}{label}{'\n\n' if proof else '：'}{content}")
        else:
            blocks.append(f"{'##### 证明步骤 ' + str(index) + chr(10) + chr(10) if proof else '- '}{entry}")
    return "\n\n".join(blocks) if proof else "\n".join(blocks)


def source_card_original(n: int, item: dict[str, Any]) -> str:
    return f"""
### {n:03d}. {case_id(item)}

- 数据组：{item['_group']}
- 原始记录：`{item['_path']}`

#### 原题（JSONL 原文）

{theorem(item)}

#### 显式假设（JSONL 原文）

{original_markdown(item.get('assumptions'))}

#### 完整证明（JSONL 原文）

{original_markdown(item.get('proof') or item.get('proof_steps') or item.get('flawed_proof_steps'), proof=True)}

---
"""


def math_case_card(n: int, item: dict[str, Any], kind: str) -> str:
    cid = case_id(item)
    path = item.get("_path", "未提供")
    prompt = theorem(item)
    return f"""
### {n:03d}. {cid}

- 数据组：{item.get('_group', '正式审核对象')}
- 对象路径：`{path}`
- 估算工作权重：{weight(item)}
- 本人职责：{item.get('_assignment_role', '独立主审')}

#### 原题（JSONL 原文）

{prompt}

#### 显式假设（JSONL 原文）

{original_markdown(item.get('assumptions'))}

#### 完整证明（JSONL 原文）

{original_markdown(item.get('proof') or item.get('proof_steps') or item.get('flawed_proof_steps'), proof=True)}

#### 机器验证结果（如有，不代表人工通过）

- 记录解析：通过
- 现有标签／预测：{text(item.get('proof_verdict') or item.get('validity_status') or item.get('gold_error_type'))}
- 现有首错：{text(item.get('first_error') or item.get('gold_first_invalid_step'))}

---
"""


def task_card(n: int, item: dict[str, Any]) -> str:
    desc = item.get("description") or item.get("attack") or item.get("claim") or item.get("_path") or case_id(item)
    raw = item.get("_content")
    raw_section = "" if raw is None else f"""

#### 原始记录

```json
{raw}
```
"""
    return f"""
### {n:03d}. {case_id(item)}

- 对象：`{item.get('_path', item.get('target', '未提供'))}`
- 任务：{desc}
- 机器线索：{item.get('machine', '仅确认对象存在；不代表人工通过')}
{raw_section}

---
"""


def write_step(step: int, slug: str, title: str, intro: str, req: list[str], buckets: tuple[list[dict[str, Any]], list[dict[str, Any]]], renderer, unit: str) -> None:
    for idx, (folder, person) in enumerate(PEOPLE):
        items = buckets[idx]
        effective_intro, effective_req = intro, req
        if step == 2:
            effective_intro = f"从 JSONL 数据源直接提取 {person} 的全部原题、假设和完整证明，按原始分配顺序串联并保留 Markdown/LaTeX；每题不设置重复填空，人工判断统一在报告末尾汇总。"
            effective_req = ["确认 304 道题与 JSONL 源记录的题号、顺序、题面、假设和证明一致。", "使用 Markdown 预览阅读保留的原始数学格式。", "确认机器检查覆盖全量对象，并汇总其异常与限制。", "按数据组、领域、难度、证明结构和数据边界判断整体代表性。", "仅登记异常或需要人工裁决的对象，并作出一次批次级最终决定。"]
        render_items = []
        for item in items:
            item = dict(item)
            item["_person"] = person
            render_items.append(item)
        body = [header(step, title, person, effective_intro, effective_req, len(items), unit, batch_mode=True)]
        if step == 2:
            body.append(source_boundary_overview(person, render_items))
            body.extend(source_card_original(n, item) for n, item in enumerate(render_items, 1))
            body.append(source_boundary_finish(person, len(items)))
        else:
            body.extend(renderer(n, item) for n, item in enumerate(render_items, 1))
            if step == 3:
                body.append(independent_gold_finish(person, len(items), effective_req))
            else:
                body.append(finish(len(items), unit, effective_req))
        out = BASE / folder / f"step{step:02d}_{slug}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(body), encoding="utf-8", newline="\n")


def main() -> None:
    all_cases = source_cases(True)
    official = source_cases(False)

    # 第二步：严格各 304 道，交错后保持数据组均衡。
    step2 = (all_cases[::2], all_cases[1::2])
    write_step(2, "source_and_boundary", "题目原文、来源与数据边界审核", "逐题确认题面、证明、来源、数据划分和使用权利，解决转录、解释、选择、注入错误与泄漏问题。", ["逐字核对仓库版本和原始来源。", "检查假设、量词、定义域、公式排版及参考证明对应关系。", "判断歧义、代表性、重复／泄漏、许可与发布用途。", "注入错误样本必须比较注入前后版本。", "语义影响修订由另一人复查。"], step2, source_card_original, "道题")

    primary_a, primary_b = balance(official)
    ids_a = {case_id(x) for x in primary_a}
    step3_a = []
    step3_b = []
    for original in official:
        a_item, b_item = dict(original), dict(original)
        if case_id(original) in ids_a:
            a_item["_assignment_role"] = "首次独立主审（锁定前不得查看 Person B 答案）"
            b_item["_assignment_role"] = "第二份独立审核（锁定前不得查看 Person A 答案）"
        else:
            a_item["_assignment_role"] = "第二份独立审核（锁定前不得查看 Person B 答案）"
            b_item["_assignment_role"] = "首次独立主审（锁定前不得查看 Person A 答案）"
        step3_a.append(a_item)
        step3_b.append(b_item)
    step3 = (step3_a, step3_b)
    write_step(3, "independent_gold", "独立人工 Gold 建立与裁决", "为正式样本独立建立证明真假、节点、依赖、首错、错误类型、反例范围和可修复性 Gold。", ["不得查看系统预测或另一审核者答案。", "按数学能力覆盖领域；超出能力范围必须升级。", "下游阻塞不得重复标为新数学错误。", "分歧必须保留双方理由并交第三人裁决。"], step3, lambda n, x: math_case_card(n, x, "gold"), "道正式样本")

    step3_sources = [
        "data/benchmarks/m2/source/pilot_50.jsonl",
        "data/benchmarks/m2/source/pilot_B50.jsonl",
        "data/benchmarks/m7/opc_250_v0_2/candidate.jsonl",
        "data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl",
    ]
    step3_record = {
        "schema_version": "manual-validation-person-b-step3-completion-0.1",
        "reviewer_role": "person_b",
        "step": 3,
        "scope": "independent_human_gold_review",
        "completion_confirmed_on": PERSON_B_STEP3_COMPLETION_DATE,
        "confirmation_source": "repository_owner_explicit_confirmation_in_current_codex_task",
        "assigned_cases": 600,
        "reviewed_cases": 600,
        "execution_status": "complete",
        "dataset_counts": {"m2_engineering_pilot": 50, "m2_b50": 50, "opc_250_v0_2": 250, "proofnet_250_v0_1": 250},
        "source_artifacts": [{"path": path, "sha256": digest(path)} for path in step3_sources],
        "result_capture_status": "summary_only_detailed_case_results_not_provided",
        "case_result_counts": None,
        "case_level_findings": None,
        "independence_evidence_status": "not_provided",
        "person_a_comparison_status": "pending",
        "third_party_adjudication_status": "pending_if_disagreements_exist",
        "gold_mutation_performed": False,
        "final_gold_freeze_status": "open",
        "limitations": [
            "Completion does not imply that every case passed.",
            "No case-level Person B decisions or finding list were supplied in this task.",
            "No independent lock or blinding evidence was supplied in this task.",
            "Person A comparison and any required third-party adjudication remain outstanding.",
        ],
    }
    (BASE / "person_b" / "step03_completion_record.json").write_text(json.dumps(step3_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    step4 = balance(official)
    write_step(4, "nodes_dependencies", "节点、依赖图、上下文与证明义务审核", "检查每道证明的节点切分、直接依赖、变量作用域、局部上下文和后代失效语义。", ["节点必须最小但完整，不能是语法残片。", "逐边执行删除父节点测试。", "禁止后续结论、无关前序节点或其他题目信息进入上下文。", "节点变更后检查全部受影响后代撤销与重验。"], step4, lambda n, x: math_case_card(n, x, "graph"), "道证明对象")

    step5 = balance(official)
    write_step(5, "mathematical_evaluation", "数学裁决、定理使用、首错与反例审核", "独立重做局部推理，核对定理条件、计算、首错、反例和错误证书。尚无系统输出的对象也必须明确记为待运行，不得伪造机器结果。", ["从合法上下文独立重做推理。", "展开定理全部前提并逐项映射。", "反例必须满足全部前提并真正否定目标。", "未找到反例、工具超时或 unknown 不得作为正确证据。", "错误证书必须绑定精确版本且可在无隐藏信息时消费。"], step5, lambda n, x: math_case_card(n, x, "evaluator"), "道正式样本")

    patches: list[dict[str, Any]] = []
    for path in sorted((ROOT / "data/benchmarks/m5").rglob("*.patch*.json")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            obj = {}
        patches.append({"id": obj.get("patch_id") or path.stem, "_path": rel, "description": "逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果", "machine": f"JSON 可解析；SHA-256 `{digest(rel)}`", "_content": json.dumps(obj, ensure_ascii=False, indent=2)})
    step6 = balance(patches)
    write_step(6, "repair_pilot", "真实修复 Pilot 与逐补丁人工审核", "对仓库中每个补丁版本逐一判断是否真正修复原证明，并把补丁接受与整篇证明成功分开记录。", ["补丁生成者不得作最终数学接受判断。", "所有声称成功、false repair 和 new-error introduction 必须全量审核。", "新增假设、弱化结论、改变定义域或偷换目标必须拒绝。", "后代未完整重验不得计为成功。"], step6, task_card, "个补丁版本")

    controller_files = ["harness/controller.py", "harness/m4_controller.py", "harness/m5_repair.py", "harness/m5_sequential_repair.py", "harness/m6_controller.py", "harness/m6_experiments.py", "harness/m7_controller.py", "harness/m8_controller.py", "harness/provider_runner.py"]
    attacks = ["完整状态路径追踪", "Generator 自审与角色伪造", "陈旧补丁与未来边", "自环、循环 DAG 与跨题依赖", "事务中途失败与完整回滚", "节点变更后的后代撤销", "配置变更后的缓存失效", "跨方法／模型／Prompt 缓存污染", "失败、超时、拒绝、解析错误与重试账本", "Provider 调用、token、价格与成本核对", "session 中断恢复", "并发、重复、乱序与部分写入", "旧 Schema 迁移与失败闭合", "不可信题面／响应字段／截断 JSON", "压力负载与困难样本丢失"]
    controls = [{"id": f"C-{i:03d}", "_path": f, "attack": a, "description": a, "machine": "目标文件存在" if (ROOT / f).exists() else "目标文件缺失，须记录为 finding"} for i, (f, a) in enumerate(((f, a) for f in controller_files for a in attacks), 1)]
    step7 = (controls[::2], controls[1::2])
    write_step(7, "controller_integrity", "Controller、缓存、状态与真实运行完整性审核", "通过人工代码审查和主动对抗测试验证权限、版本、回滚、缓存、账本、Provider 记录和压力情形。", ["每项攻击必须记录期望行为、实际行为和复现步骤。", "独立核对真实 Provider 控制台与账单。", "高严重度 finding 修复后必须重放原攻击。", "任何选择性漏记或失败开放均判为不通过。"], step7, task_card, "项对抗检查")

    step8 = balance(official)
    write_step(8, "fairness_statistics_blind", "实验公平性、统计与盲态案例审核", "在方法身份和聚合分数不可见时审核数学质量、等价表达稳定性和共同盲点，并在揭盲后检查公平性、统计与异常原因。", ["锁定逐例盲态结论前不得查看方法身份或聚合分数。", "配置差异只能来自预注册目标机制。", "所有样本保留在 intention-to-treat 分母。", "从原始 ledger 独立重算主要端点和配对统计。", "功效不足时不得作强泛化或无差异结论。"], step8, lambda n, x: math_case_card(n, x, "blind"), "道盲态案例")

    release_patterns = ["README.md", "LICENSE*", "NOTICE*", "requirements*.txt", "pyproject.toml", "environment*.yml", "docs/**/*paper*.md", "docs/**/*system*card*.md", "docs/**/*data*card*.md", "docs/milestones/M08*.md", "data/benchmarks/m8/*.json"]
    release_paths: set[Path] = set()
    for pat in release_patterns:
        release_paths.update(p for p in ROOT.glob(pat) if p.is_file())
    release_tasks = []
    checks = ["干净环境安装与命令可执行", "原始响应到指标与论文数字证据链", "数学案例与能力边界表述", "失败、成本与人工监督披露", "来源权利与第三方许可", "隐私、凭据、内部路径与敏感日志", "发布提交和物料版本一致", "严重错误勘误、撤回与下游通知演练"]
    for i, path in enumerate(sorted(release_paths), 1):
        rel = path.relative_to(ROOT).as_posix()
        release_tasks.append({"id": f"R-{i:03d}", "_path": rel, "description": "；".join(checks), "machine": f"文件存在；SHA-256 `{digest(rel)}`"})
    step9 = balance(release_tasks)
    write_step(9, "release_reproduction", "独立复现、论文主张与发布审核", "在干净环境复现项目，并逐发布物检查数字、主张、数学案例、权利、隐私、物料一致性与勘误流程。", ["只使用发布材料，不依赖开发机缓存或隐藏知识。", "每项主张建立主张—数据—运行—统计—案例证据链。", "自然语言审计不得表述为形式化证明保证。", "逐文件检查权利、隐私和敏感信息。", "演练发布后严重错误处置流程。"], step9, task_card, "个发布对象")

    # 两人的工作目录页。
    titles = {2: "题目原文、来源与数据边界", 3: "独立人工 Gold", 4: "节点、依赖图、上下文与证明义务", 5: "数学裁决、定理、首错与反例", 6: "真实修复 Pilot 与补丁", 7: "Controller 与运行完整性", 8: "实验公平性、统计与盲态案例", 9: "独立复现、论文与发布"}
    slugs = {2: "source_and_boundary", 3: "independent_gold", 4: "nodes_dependencies", 5: "mathematical_evaluation", 6: "repair_pilot", 7: "controller_integrity", 8: "fairness_statistics_blind", 9: "release_reproduction"}
    for folder, person in PEOPLE:
        links = "\n".join(f"{i - 1}. [第{i}步：{titles[i]}](step{i:02d}_{slugs[i]}.md)" for i in range(2, 10))
        progress_rows = []
        for i in range(2, 10):
            if person == "Person B" and i == 2:
                progress_rows.append("| 第2步 | 人工审核完成；结论汇总待补充 | 304／304 | 最终纳入决定及异常统计未提供 | `step02_source_and_boundary.md` |")
            elif person == "Person B" and i == 3:
                progress_rows.append("| 第3步 | 人工执行完成；结论合并待办 | 600／600 | 缺逐题结果、独立性证据及 A/B 裁决 | `step03_independent_gold.md`；`step03_completion_record.json` |")
            else:
                progress_rows.append(f"| 第{i}步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |")
        catalog = f"""# {person}人工检验工作目录

本目录包含《项目人工审核与验证执行手册》第二至第九步中分配给 **{person}** 的全部人工检验工作。每人每个大步各使用一个独立 Markdown 文件。文件按顺序列出全部分配对象及其可用原始内容，不要求逐项重复填表；审核者通读、抽样并复核异常后，只在每份文件末尾填写一次批次级验证清单与最终决定。在锁定要求明确的步骤中，不得提前查看另一人的答案。

## 执行顺序

{links}

## 总体进度

| 步骤 | 状态 | 完成数／分配数 | 阻塞问题 | 证据路径 |
|---|---|---:|---|---|
""" + "\n".join(progress_rows) + """

## 交付签名

- 审核者：________
- 完成时间：________
- 分支与提交 SHA：________
- 我确认未以机器结果替代人工判断：________（是／否）
- 我确认所有不确定与失败均已如实保留：________（是／否）
- 待共同裁决事项：______________________________________________________________
"""
        (BASE / folder / "README.md").write_text(catalog, encoding="utf-8", newline="\n")

    print("已生成 2 个工作目录、16 份步骤工作包和 2 份目录页。")


if __name__ == "__main__":
    main()
