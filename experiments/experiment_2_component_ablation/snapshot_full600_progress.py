"""Publish a deterministic, non-final snapshot of the shared full-600 run."""
import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
METHODS = ["no_agent", "single_agent", "single_agent_self_refine", "dual_agent", "dual_agent_controller"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_run", type=Path)
    args = parser.parse_args()
    source = args.source_run.resolve()
    inputs = [json.loads(x) for x in (HERE / "inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = [x["case_id"] for x in inputs]
    if len(ids) != 600 or len(set(ids)) != 600:
        raise SystemExit("Expected 600 unique experiment inputs")

    generated = [case_id for case_id in ids if (source / case_id / "generation.json").exists()]
    judged = [case_id for case_id in ids if (source / case_id / "judgment.json").exists()]
    mapped = [case_id for case_id in ids if (source / case_id / "mapping.json").exists()]
    missing_generation = [case_id for case_id in ids if case_id not in set(generated)]
    missing_judgment = [case_id for case_id in ids if case_id not in set(judged)]
    if set(judged) != set(mapped):
        raise SystemExit("Judgment/mapping checkpoint sets differ")

    assignments = []
    for case in inputs:
        for method in METHODS:
            done = case["case_id"] in set(judged)
            assignments.append({
                "case_id": case["case_id"], "method": method,
                "status": "judged" if done else ("generated_pending_judgment" if case["case_id"] in set(generated) else "pending_generation"),
            })
    (HERE / "assignments.json").write_text(json.dumps(assignments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")
    snapshot = {
        "schema_version": "experiment-2-progress-1.0", "snapshot_time": now,
        "total_cases": 600, "method_count": 5, "total_judgments_planned": 3000,
        "generation_completed_cases": len(generated), "generation_remaining_cases": 600 - len(generated),
        "judgment_completed_cases": len(judged), "judgment_remaining_cases": 600 - len(judged),
        "completed_method_case_judgments": len(judged) * 5,
        "remaining_method_case_judgments": (600 - len(judged)) * 5,
        "missing_generation_case_ids": missing_generation,
        "missing_judgment_case_ids": missing_judgment,
        "status": "completed" if len(judged) == 600 else "in_progress",
        "metric": "independent_blind_model_acceptance", "human_verified": False,
    }
    (HERE / "PROGRESS.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    groups = Counter(x["case_id"].split("-")[0] if "-" in x["case_id"] else "M2" for x in inputs if x["case_id"] in set(judged))
    lines = [
        "# 实验2运行进度", "", f"> 快照时间：{now}（UTC+08:00）。实验仍在进行，以下不是最终正确率。", "",
        "| 阶段 | 已完成 | 剩余 |", "|---|---:|---:|",
        f"| 600题四候选生成 | {len(generated)}/600 | {600-len(generated)} |",
        f"| 统一独立盲审（按题） | {len(judged)}/600 | {600-len(judged)} |",
        f"| 配置×题判断 | {len(judged)*5}/3000 | {(600-len(judged))*5} |", "",
        "剩余待盲审题号：" + ("、".join(missing_judgment) if missing_judgment else "无"), "",
        "当前仅发布完成度，不提前发布596题阶段性通过率，以免被误读为600题最终结果。所有已完成判断均有匿名方法映射检查点；待600/600后生成逐题证据、正式结果与报告。", "",
        "进度口径：每题一次生成得到4种修复候选；一次独立盲审同时判断原证明（无Agent）与4种候选，因此每道完成题对应5个配置判断。", "",
    ]
    (HERE / "PROGRESS.md").write_text("\n".join(lines), encoding="utf-8")
    audits = {x["case_id"]: x for x in json.loads((HERE / "case_audit.json").read_text(encoding="utf-8"))}
    case_lines = [
        "# 实验2逐题运行状态（600题）", "",
        f"> 状态快照：{now}。逐题数学判定将在600/600后随正式结果发布。", "",
        "| ID | 数据集 | 输入SHA-256 | 生成 | 独立盲审 |", "|---|---|---|---|---|",
    ]
    generated_set, judged_set = set(generated), set(judged)
    for case_id in ids:
        audit = audits[case_id]
        case_lines.append(
            f'| {case_id} | {audit["dataset"]} | `{audit["input_sha256"]}` | '
            f'{"完成" if case_id in generated_set else "待运行"} | {"完成" if case_id in judged_set else "待运行"} |'
        )
    (HERE / "CASE_RESULTS.md").write_text("\n".join(case_lines) + "\n", encoding="utf-8")
    audit_fields = ("case_id", "dataset", "source_path", "input_sha256", "source_split", "input_available",
                    "historical_agent_file_available", "historical_agent_reference", "historical_confirmation")
    clean_audits = [{key: audits[case_id].get(key) for key in audit_fields} for case_id in ids]
    (HERE / "case_audit.json").write_text(json.dumps(clean_audits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
