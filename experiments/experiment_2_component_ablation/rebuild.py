#!/usr/bin/env python3
"""Rebuild Experiment 2 from frozen, repository-local evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXP1 = ROOT / "experiments/experiment_1_final_repair_accuracy/results.json"
GOLD = ROOT / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl"
M3 = ROOT / "data/benchmarks/m3/revalidation/full50_report_v0_2.json"
STEP6 = ROOT / "data/manual_validation/person_a_step06_completion_record.json"
M5 = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else 0.0


def condition(condition_id: str, label: str, successes: int, total: int, evidence: str) -> dict:
    return {
        "condition_id": condition_id,
        "label": label,
        "successes": successes,
        "total": total,
        "verified_final_acceptance_rate": successes / total if total else 0.0,
        "percentage": pct(successes, total),
        "wilson95": wilson(successes, total),
        "evidence_basis": evidence,
    }


def render_case_table(cases: list[dict]) -> str:
    rows = [
        "# 实验2逐题结果",
        "",
        "`双 Agent 单轮`一列是将已保存完整轨迹截断在第一轮后的回顾性重构；它不是一次新的独立模型调用。",
        "",
        "| 证明 | Gold状态 | 无Agent | 单诊断Agent | 双Agent单轮 | 双Agent+Controller | 轮数 | 最终操作 | 人工审核 |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for case in cases:
        yn = lambda value: "1" if value else "0"
        rows.append(
            f"| {case['proof_id']} | `{case['gold_status']}` | {yn(case['no_agent_success'])} | "
            f"{yn(case['single_diagnostic_agent_success'])} | {yn(case['dual_agents_one_pass_success'])} | "
            f"{yn(case['full_system_success'])} | {case['repair_rounds']} | `{case['final_operation']}` | "
            f"`{case['review_status']}` |"
        )
    rows.extend([
        "",
        "说明：1表示该条件下最终整篇证明被记录为严格通过，0表示没有。仅诊断Agent不生成补丁，因此其最终修复成功状态与原证明相同。",
        "",
    ])
    return "\n".join(rows)


def render_results(result: dict) -> str:
    conditions = result["primary_ablation"]
    rows = [
        "# 实验2结果",
        "",
        "## 主结果：组件能力阶梯",
        "",
        "| 条件 | 成功/总数 | 最终严格通过率 | 相对上一档 | 证据类型 |",
        "|---|---:|---:|---:|---|",
    ]
    previous = None
    for item in conditions:
        delta = "—" if previous is None else f"{item['percentage'] - previous:+.1f} pp"
        rows.append(
            f"| {item['label']} | {item['successes']}/{item['total']} | {item['percentage']:.1f}% | "
            f"{delta} | {item['evidence_basis']} |"
        )
        previous = item["percentage"]
    safety = result["safety_and_design_signals"]
    diag = result["single_agent_diagnostic_benchmark"]
    rows.extend([
        "",
        "完整系统相对双 Agent 单轮截断增加 **6/21** 个最终成功，提升 **28.6个百分点**。这6题均来自需要第二轮修复的历史轨迹；该结果说明迭代控制与拒绝后重试在这批轨迹中有贡献，但不等价于随机化因果估计。",
        "",
        "## 单 Agent 的独立诊断能力",
        "",
        f"M3冻结50题诊断集上，单 Evaluator Agent 的证明有效性准确率为 **{diag['proof_validity_accuracy'] * 100:.1f}%（{diag['proof_validity_correct']}/{diag['sample_count']}）**，错误类型准确率为 **{diag['error_type_accuracy'] * 100:.1f}%**，首错整体定位准确率为 **{diag['first_error_overall_accuracy'] * 100:.1f}%**，依赖边 F1 为 **{diag['dependency_edge_f1']:.4f}**。这些是诊断指标，不是修复成功率。",
        "",
        "## 项目独特改善点",
        "",
        f"- 迭代控制挽回：{safety['controller_rescued_cases']}/{safety['full_successes']} 个最终成功依赖第二轮，占成功案例的 {safety['controller_rescue_share_of_successes'] * 100:.1f}%。",
        f"- 保守退出：{safety['irreparable_safe_exits']}/{safety['cohort_size']} 个案例被标记为不可局部修复，没有被包装成成功修复。",
        f"- 人工确认的问题保持：{safety['problem_preserved']}/{safety['full_successes']}。",
        f"- 人工确认的无新增错误：{safety['no_new_errors']}/{safety['full_successes']}。",
        f"- 人工确认的操作最小性：{safety['operationally_minimal']}/{safety['full_successes']}。",
        f"- 局部补丁覆盖：{safety['local_patch_operations']}/{safety['full_successes']}，操作分布为 {safety['operation_counts']}。",
        "",
        "## 结论边界",
        "",
        "本实验完成的是保存轨迹上的回顾性组件消融。无Agent与仅诊断Agent的0%来自两者都不改写原证明；双Agent单轮结果来自截断完整轨迹；完整系统结果来自实验1已审核终态。除单Agent诊断指标外，本轮没有新provider模型调用，也没有四套系统的独立、等预算随机重跑。因此主表可用于项目内部论证和下一轮实验设计，不应直接写成投稿级因果结论。",
        "",
    ])
    return "\n".join(rows)


def build() -> tuple[dict, dict, str, str]:
    exp1 = load_json(EXP1)
    gold_by_id = {row["proof_id"]: row for row in load_jsonl(GOLD)}
    m3 = load_json(M3)
    step6 = load_json(STEP6)
    source_paths = {EXP1, GOLD, M3, STEP6}
    cases = []
    operation_counts: Counter[str] = Counter()
    review_counts = Counter()

    assert step6["assigned_patches"] == 21
    assert step6["whole_proof_result_counts"] == {"not_repaired_irreparable": 7, "repaired": 14}

    for source_case in exp1["cases"]:
        proof_id = source_case["proof_id"]
        gold = gold_by_id[proof_id]
        assert gold["gold_validity_status"] == source_case["gold_status"]
        completion_path = M5 / f"{proof_id}.completion.json"
        patch_path = ROOT / source_case["evidence_paths"][0]
        if source_case["repair_rounds"] > 1 and (M5 / f"{proof_id}.patch.r2.json").exists():
            patch_path = M5 / f"{proof_id}.patch.r2.json"
        review_path = M5 / f"{proof_id}.person_a_review.json"
        if source_case["repair_rounds"] > 1 and (M5 / f"{proof_id}.person_a_review.r2.json").exists():
            review_path = M5 / f"{proof_id}.person_a_review.r2.json"
        completion = load_json(completion_path)
        patch = load_json(patch_path)
        review = load_json(review_path)
        source_paths.update({completion_path, patch_path, review_path})

        repaired = source_case["outcome"] == "repaired"
        rounds = int(completion["repair_rounds"])
        assert rounds == source_case["repair_rounds"]
        assert (completion["controller_stop_reason"] == "accepted") == repaired
        one_pass = repaired and rounds == 1
        operation = patch["operation"]
        operation_counts[operation] += int(repaired)
        review_ok = bool(review.get("accepted"))
        review_counts["accepted"] += int(repaired and review_ok)

        cases.append({
            "proof_id": proof_id,
            "gold_status": source_case["gold_status"],
            "no_agent_success": source_case["gold_status"] == "valid",
            "single_diagnostic_agent_success": source_case["gold_status"] == "valid",
            "dual_agents_one_pass_success": one_pass,
            "full_system_success": repaired,
            "controller_rescued": repaired and rounds > 1,
            "repair_rounds": rounds,
            "final_operation": operation,
            "review_status": "accepted" if review_ok else "not_accepted",
            "evidence_paths": [
                str(completion_path.relative_to(ROOT)).replace("\\", "/"),
                str(patch_path.relative_to(ROOT)).replace("\\", "/"),
                str(review_path.relative_to(ROOT)).replace("\\", "/"),
            ],
        })

    total = len(cases)
    no_agent = sum(case["no_agent_success"] for case in cases)
    single = sum(case["single_diagnostic_agent_success"] for case in cases)
    one_pass = sum(case["dual_agents_one_pass_success"] for case in cases)
    full = sum(case["full_system_success"] for case in cases)
    rescued = sum(case["controller_rescued"] for case in cases)
    accepted_reviews = [
        load_json(ROOT / case["evidence_paths"][2]) for case in cases if case["full_system_success"]
    ]
    assert (no_agent, single, one_pass, full, rescued) == (0, 0, 8, 14, 6)
    assert review_counts["accepted"] == full

    result = {
        "schema_version": "experiment-2-component-ablation-1.0",
        "experiment_name": "retrospective_component_capability_ladder",
        "evidence_level": "retrospective_trace_ablation_not_independent_equal_budget_rerun",
        "new_provider_model_calls": 0,
        "cohort": {
            "n": total,
            "source": "experiment_1_final_repair_accuracy",
            "selection": "all 21 cases with synchronized Person A Step 6 terminal outcomes",
        },
        "primary_ablation": [
            condition("no_agent", "无Agent（原证明）", no_agent, total, "observed original Gold state"),
            condition("single_diagnostic_agent", "仅单个诊断Agent", single, total, "deterministic no-edit capability condition"),
            condition("dual_agents_one_pass", "双Agent（单轮截断）", one_pass, total, "retrospective trace truncation"),
            condition("dual_agents_controller", "双Agent + Controller", full, total, "observed reviewed terminal state"),
        ],
        "contrasts": {
            "dual_agents_vs_no_agent_pp": pct(one_pass - no_agent, total),
            "controller_increment_pp": pct(full - one_pass, total),
            "full_vs_no_agent_pp": pct(full - no_agent, total),
            "controller_rescued_cases": rescued,
        },
        "single_agent_diagnostic_benchmark": {
            "sample_count": m3["sample_count"],
            "proof_validity_accuracy": m3["proof_validity"]["accuracy"],
            "proof_validity_correct": round(m3["proof_validity"]["accuracy"] * m3["sample_count"]),
            "error_type_accuracy": m3["error_type"]["accuracy"],
            "first_error_overall_accuracy": m3["first_error_localization"]["overall_accuracy"],
            "dependency_edge_f1": m3["dependency_edges"]["f1"],
            "warning": "Different 50-case diagnostic benchmark; not a repair-rate row.",
        },
        "safety_and_design_signals": {
            "cohort_size": total,
            "full_successes": full,
            "controller_rescued_cases": rescued,
            "controller_rescue_share_of_successes": rescued / full,
            "irreparable_safe_exits": total - full,
            "problem_preserved": sum(bool(r["checks"].get("theorem_preserved") and r["checks"].get("assumptions_preserved") and r["checks"].get("domain_preserved")) for r in accepted_reviews),
            "no_new_errors": sum(bool(r["checks"].get("no_new_errors")) for r in accepted_reviews),
            "operationally_minimal": sum(bool(r["checks"].get("operationally_minimal")) for r in accepted_reviews),
            "local_patch_operations": sum(operation_counts.values()),
            "operation_counts": {key: value for key, value in sorted(operation_counts.items()) if value},
            "review_basis": "owner-confirmed synchronized review; not independent blind review",
        },
        "cases": cases,
        "limitations": [
            "The four primary rows are not independent equal-budget model reruns.",
            "The one-pass row is reconstructed by truncating saved successful traces after round one.",
            "The single-agent repair baseline is unavailable; the single-agent row is diagnosis-only and cannot modify proofs.",
            "Human review is owner-confirmed synchronized review rather than independent blinded adjudication.",
            "The cohort is retrospective and selected from cases entering the repair workflow.",
        ],
    }
    manifest = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in sorted(source_paths, key=lambda p: str(p))
    }
    return result, manifest, render_case_table(cases), render_results(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if committed outputs differ from a fresh rebuild.")
    args = parser.parse_args()
    result, manifest, cases_md, results_md = build()
    outputs = {
        OUT / "results.json": json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        OUT / "source_manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        OUT / "CASE_RESULTS.md": cases_md,
        OUT / "RESULTS.md": results_md,
    }
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            raise SystemExit("stale generated outputs: " + ", ".join(stale))
        print(f"Experiment 2 check passed: {len(result['cases'])} cases, {len(manifest)} source files.")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Experiment 2 rebuilt: {len(result['cases'])} cases, {len(manifest)} source files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
