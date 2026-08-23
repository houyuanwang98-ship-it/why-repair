"""生成第二至第九步的双人中文人工检验工作包。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "manual_validation"
PEOPLE = (("person_a", "Person A"), ("person_b", "Person B"))


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


def header(step: int, title: str, person: str, intro: str, requirements: list[str], count: int, unit: str) -> str:
    req = "\n".join(f"{i}. {x}" for i, x in enumerate(requirements, 1))
    return f"# 第{step}步：{title}——{person}工作包\n\n## 简介\n\n{intro}\n\n本工作包分配给 **{person}**，共 **{count} {unit}**。只完成本文件不足以关闭该步骤；必须与另一人的工作包合并、比较分歧并完成必要裁决。\n\n## 本步要求\n\n{req}\n{COMMON}\n## 逐项人工检验\n"


def finish(count: int, unit: str) -> str:
    return f"""
## 工作包汇总

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
- 本工作包状态：________（未开始／进行中／阻塞／完成）
"""


def source_card(n: int, item: dict[str, Any]) -> str:
    machine = ["JSON 记录已成功解析", f"源文件 SHA-256：`{item['_file_digest']}`"]
    for k, label in (("raw_bytes_sha256", "原始字节摘要"), ("source_record_digest", "来源记录摘要"), ("license_status", "机器许可状态"), ("split", "数据划分")):
        if item.get(k) is not None:
            machine.append(f"{label}：`{item[k]}`")
    if not item.get("source_uri"):
        machine.append("逐题稳定外部来源地址：未提供")
    return f"""
<!-- 人工检验对象 -->
### {n}. {case_id(item)}

- 数据组：{item['_group']}
- 对象路径：`{item['_path']}`
- 领域：`{item.get('domain', '未提供')}`
- 来源地址：{item.get('source_uri', '未提供')}

#### 题干（仓库原文）

```text
{text(theorem(item))}
```

#### 假设与证明（仓库原文）

```text
假设：{text(item.get('assumptions'))}

证明：{text(item.get('proof') or item.get('proof_steps') or item.get('flawed_proof_steps'))}
```

#### 机器验证结果（不代表人工通过）

{chr(10).join(f'- {x}' for x in machine)}

#### 人工检验（填空）

- 已打开原始来源并逐项对照：________（是／否／不确定）
- 来源可靠且定位准确：________（是／否／不确定）
- 题干忠实性：________（通过／需修订／不通过）
- 假设、量词、定义域和值域完整正确：________（是／否／不确定）
- 参考证明对应原题：________（是／否／不确定／不适用）
- OCR、翻译、公式、Unicode 或规范化改变数学意义：________（无／有／不确定）
- 歧义、自相矛盾或缺失条件：________（无／有／不确定）
- 重复、近重复或泄漏风险：________（无／有／不确定）
- 代表性：________（合适／不合适／不确定）
- 注入错误忠实性：________（通过／不通过／不适用／不确定）
- 权利状态：________（可用／受限／不确定）
- 差异、风险与理由：____________________________________________________________
- 证据路径：____________________________________________________________________
- 必要行动：________（无／修订／补来源／去重／重新划分／排除／升级复核）
- 最终决定：________（纳入／修订后纳入／排除／不确定）
"""


def math_case_card(n: int, item: dict[str, Any], kind: str) -> str:
    cid = case_id(item)
    path = item.get("_path", "未提供")
    prompt = theorem(item)
    fields = {
        "gold": ["原定理真假", "证明整体裁决", "节点切分", "直接依赖", "逐节点裁决", "第一处真实错误", "错误类型", "下游阻塞", "反例范围", "可修复性"],
        "graph": ["节点最小且完整", "源文本对齐", "自包含改写等价", "节点类型", "直接依赖", "缺失依赖", "无关依赖", "作用域或上下文泄漏", "局部证明义务", "后代撤销与重验"],
        "evaluator": ["人工数学裁决", "系统裁决", "定理适用性", "缺失条件", "计算有效性", "首错位置", "反例有效性与范围", "自然语言到程序表达式忠实性", "错误证书目标绑定", "证书上下文完整且无需隐藏信息"],
        "blind": ["盲态数学质量", "方法身份是否泄漏", "题面与上下文公平", "等价改写稳定性", "符号替换稳定性", "首错稳定性", "证书稳定性", "补丁稳定性", "共享盲点", "异常原因（揭盲后填写）"],
    }[kind]
    blanks = "\n".join(f"- {x}：________" for x in fields)
    return f"""
<!-- 人工检验对象 -->
### {n}. {cid}

- 数据组：{item.get('_group', '正式审核对象')}
- 对象路径：`{path}`
- 估算工作权重：{weight(item)}
- 本人职责：{item.get('_assignment_role', '独立主审')}

#### 题干（仓库原文）

```text
{text(prompt)}
```

#### 机器验证结果（如有，不代表人工通过）

- 记录解析：通过
- 现有标签／预测：{text(item.get('proof_verdict') or item.get('validity_status') or item.get('gold_error_type'))}
- 现有首错：{text(item.get('first_error') or item.get('gold_first_invalid_step'))}

#### 人工检验（填空）

{blanks}
- 详细理由：____________________________________________________________________
- 证据路径：____________________________________________________________________
- 初次结果：________（通过／不通过／需修订／不确定）
- 必要修订：____________________________________________________________________
"""


def task_card(n: int, item: dict[str, Any], labels: list[str]) -> str:
    desc = item.get("description") or item.get("attack") or item.get("claim") or item.get("_path") or case_id(item)
    return f"""
<!-- 人工检验对象 -->
### {n}. {case_id(item)}

- 对象：`{item.get('_path', item.get('target', '未提供'))}`
- 任务：{desc}
- 机器线索：{item.get('machine', '仅确认对象存在；不代表人工通过')}

#### 人工检验（填空）

{chr(10).join(f'- {x}：________' for x in labels)}
- 实际观察／数学理由：____________________________________________________________
- 复现或执行步骤：________________________________________________________________
- 证据路径：______________________________________________________________________
- 必要修订：______________________________________________________________________
- 初次结果：________（通过／不通过／需修订／不确定／不适用）
"""


def write_step(step: int, slug: str, title: str, intro: str, req: list[str], buckets: tuple[list[dict[str, Any]], list[dict[str, Any]]], renderer, unit: str) -> None:
    for idx, (folder, person) in enumerate(PEOPLE):
        items = buckets[idx]
        body = [header(step, title, person, intro, req, len(items), unit)]
        body.extend(renderer(n, item) for n, item in enumerate(items, 1))
        body.append(finish(len(items), unit))
        out = BASE / folder / f"step{step:02d}_{slug}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(body), encoding="utf-8", newline="\n")


def main() -> None:
    all_cases = source_cases(True)
    official = source_cases(False)

    # 第二步：严格各 304 道，交错后保持数据组均衡。
    step2 = (all_cases[::2], all_cases[1::2])
    write_step(2, "source_and_boundary", "题目原文、来源与数据边界审核", "逐题确认题面、证明、来源、数据划分和使用权利，解决转录、解释、选择、注入错误与泄漏问题。", ["逐字核对仓库版本和原始来源。", "检查假设、量词、定义域、公式排版及参考证明对应关系。", "判断歧义、代表性、重复／泄漏、许可与发布用途。", "注入错误样本必须比较注入前后版本。", "语义影响修订由另一人复查。"], step2, source_card, "道题")

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
        patches.append({"id": obj.get("patch_id") or path.stem, "_path": rel, "description": "逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果", "machine": f"JSON 可解析；SHA-256 `{digest(rel)}`"})
    step6 = balance(patches)
    write_step(6, "repair_pilot", "真实修复 Pilot 与逐补丁人工审核", "对仓库中每个补丁版本逐一判断是否真正修复原证明，并把补丁接受与整篇证明成功分开记录。", ["补丁生成者不得作最终数学接受判断。", "所有声称成功、false repair 和 new-error introduction 必须全量审核。", "新增假设、弱化结论、改变定义域或偷换目标必须拒绝。", "后代未完整重验不得计为成功。"], step6, lambda n, x: task_card(n, x, ["输入隔离", "保持原问题", "数学有效", "最小且局部", "引入新错误", "后代已重验", "补丁评审结果", "整篇证明结果", "失败原因"]), "个补丁版本")

    controller_files = ["harness/controller.py", "harness/m4_controller.py", "harness/m5_repair.py", "harness/m5_sequential_repair.py", "harness/m6_controller.py", "harness/m6_experiments.py", "harness/m7_controller.py", "harness/m8_controller.py", "harness/provider_runner.py"]
    attacks = ["完整状态路径追踪", "Generator 自审与角色伪造", "陈旧补丁与未来边", "自环、循环 DAG 与跨题依赖", "事务中途失败与完整回滚", "节点变更后的后代撤销", "配置变更后的缓存失效", "跨方法／模型／Prompt 缓存污染", "失败、超时、拒绝、解析错误与重试账本", "Provider 调用、token、价格与成本核对", "session 中断恢复", "并发、重复、乱序与部分写入", "旧 Schema 迁移与失败闭合", "不可信题面／响应字段／截断 JSON", "压力负载与困难样本丢失"]
    controls = [{"id": f"C-{i:03d}", "_path": f, "attack": a, "description": a, "machine": "目标文件存在" if (ROOT / f).exists() else "目标文件缺失，须记录为 finding"} for i, (f, a) in enumerate(((f, a) for f in controller_files for a in attacks), 1)]
    step7 = (controls[::2], controls[1::2])
    write_step(7, "controller_integrity", "Controller、缓存、状态与真实运行完整性审核", "通过人工代码审查和主动对抗测试验证权限、版本、回滚、缓存、账本、Provider 记录和压力情形。", ["每项攻击必须记录期望行为、实际行为和复现步骤。", "独立核对真实 Provider 控制台与账单。", "高严重度 finding 修复后必须重放原攻击。", "任何选择性漏记或失败开放均判为不通过。"], step7, lambda n, x: task_card(n, x, ["期望行为", "实际行为", "结果", "严重度", "复测结果", "中断恢复结果", "并发与顺序结果", "迁移结果", "不可信输入结果", "压力与部分响应结果"]), "项对抗检查")

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
    write_step(9, "release_reproduction", "独立复现、论文主张与发布审核", "在干净环境复现项目，并逐发布物检查数字、主张、数学案例、权利、隐私、物料一致性与勘误流程。", ["只使用发布材料，不依赖开发机缓存或隐藏知识。", "每项主张建立主张—数据—运行—统计—案例证据链。", "自然语言审计不得表述为形式化证明保证。", "逐文件检查权利、隐私和敏感信息。", "演练发布后严重错误处置流程。"], step9, lambda n, x: task_card(n, x, ["干净安装", "测试", "数据构建", "结果回放", "指标复现", "论文数字", "主张支持", "数学案例", "权利审核", "隐私审核", "文档完整", "勘误流程", "发布决定"]), "个发布对象")

    # 两人的工作目录页。
    titles = {2: "题目原文、来源与数据边界", 3: "独立人工 Gold", 4: "节点、依赖图、上下文与证明义务", 5: "数学裁决、定理、首错与反例", 6: "真实修复 Pilot 与补丁", 7: "Controller 与运行完整性", 8: "实验公平性、统计与盲态案例", 9: "独立复现、论文与发布"}
    slugs = {2: "source_and_boundary", 3: "independent_gold", 4: "nodes_dependencies", 5: "mathematical_evaluation", 6: "repair_pilot", 7: "controller_integrity", 8: "fairness_statistics_blind", 9: "release_reproduction"}
    for folder, person in PEOPLE:
        links = "\n".join(f"{i - 1}. [第{i}步：{titles[i]}](step{i:02d}_{slugs[i]}.md)" for i in range(2, 10))
        catalog = f"""# {person}人工检验工作目录

本目录包含《项目人工审核与验证执行手册》第二至第九步中分配给 **{person}** 的全部填空式人工检验工作。每一步必须独立完成；在锁定要求明确的步骤中，不得提前查看另一人的答案。

## 执行顺序

{links}

## 总体进度

| 步骤 | 状态 | 完成数／分配数 | 阻塞问题 | 证据路径 |
|---|---|---:|---|---|
""" + "\n".join(f"| 第{i}步 | 未开始／进行中／阻塞／完成 | ________ | ________ | ________ |" for i in range(2, 10)) + """

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
