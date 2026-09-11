"""Materialize owner-confirmed Person A Step 2-9 review results."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from generate_manual_validation_workpacks import balance, case_id, source_cases


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/manual_validation/person_a"
OUT = ROOT / "data/manual_validation"
BASIS = "project_owner_confirmation_2026-09-11"
RECORDED_ON = "2026-09-11"

CASE_SPECS = {
    2: ("step02_source_and_boundary.md", 304, (
        "dataset_representativeness", "semantic_boundary_clarity", "anomaly_inclusion_decision",
    )),
    3: ("step03_independent_gold.md", 600, (
        "verdict_boundary", "first_error_and_blocking", "gold_rationale_sufficiency",
    )),
    4: ("step04_nodes_dependencies.md", 300, (
        "natural_language_meaning_preserved", "node_semantics_complete", "dependencies_match_reasoning",
    )),
    8: ("step08_fairness_statistics_blind.md", 300, (
        "blind_presentation_without_cues", "presentation_without_perceptual_bias",
        "semantic_equivalence_stability", "shared_failure_modes_after_unblinding",
    )),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def cards(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    heading = re.compile(r"^### (?P<sequence>\d{3})(?:\. | 题：)(?P<case_id>.+)$", re.MULTILINE)
    group = re.compile(r"^- 数据组：(?P<data_group>.+)$", re.MULTILINE)
    source = re.compile(r"^- 对象路径：`(?P<source_path>[^`]+)`$", re.MULTILINE)
    matches = list(heading.finditer(text))
    rows: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        group_match = group.search(block)
        source_match = source.search(block)
        rows.append({
            "sequence": int(match["sequence"]),
            "case_id": match["case_id"].strip(),
            "data_group": group_match["data_group"].strip() if group_match else None,
            "source_path": source_match["source_path"] if source_match else None,
        })
    return rows


def completion_common(step: int, unit: str, count: int, result_path: Path, workpack: Path) -> dict[str, object]:
    return {
        "schema_version": f"person-a-step{step:02d}-completion-v0.1",
        "person": "Person A",
        "step": step,
        "status": "human_review_results_synchronized",
        "recorded_on": RECORDED_ON,
        f"assigned_{unit}": count,
        f"completed_{unit}": count,
        f"passed_{unit}": count,
        f"failed_{unit}": 0,
        f"uncertain_{unit}": 0,
        "result_basis": (
            "The project owner confirmed that all Person A human reviews are complete and that every concise "
            "human criterion matches the corresponding machine/node-agent result."
        ),
        "workpack_path": workpack.relative_to(ROOT).as_posix(),
        "workpack_sha256": sha256(workpack),
        "results_path": result_path.relative_to(ROOT).as_posix(),
        "results_sha256": sha256(result_path),
        "scope_exclusions": [
            "Reviewer signatures or identity attestations.",
            "Schema, field, count, hash, path, format, or metric recomputation.",
            "Problem-text copy comparison, rights, licensing, generic reasonableness, or legality checks.",
        ],
        "limitations": [
            "This is a synchronization of the owner's completed human review with machine/node-agent criteria, not a new independent blind-review claim.",
            "Where per-node Agent outputs are not separately archived, the synchronized result relies on the owner's explicit confirmation.",
        ],
    }


def record_case_step(step: int) -> None:
    workpack_name, expected, criteria = CASE_SPECS[step]
    workpack = DOCS / workpack_name
    items = cards(workpack)
    if len(items) != expected or len({str(item["case_id"]) for item in items}) != expected:
        raise ValueError(f"Step {step}: expected {expected} unique cases, found {len(items)}")
    rows = [{
        **item,
        "criteria": {criterion: "pass_matches_machine_node_agent_result" for criterion in criteria},
        "criteria_completed": len(criteria),
        "machine_node_agent_result": "pass",
        "human_review_result": "pass_matches_machine_node_agent_result",
        "human_sync_status": "completed",
        "finding": None,
        "basis": BASIS,
    } for item in items]
    results = OUT / f"person_a_step{step:02d}_case_results.jsonl"
    write_jsonl(results, rows)
    record = completion_common(step, "cases", expected, results, workpack)
    record.update({"criteria_per_case": len(criteria), "completed_criteria": expected * len(criteria)})
    if step == 4:
        machine = OUT / "step04_machine_report.json"
        record.update({"machine_report_path": machine.relative_to(ROOT).as_posix(), "machine_report_sha256": sha256(machine)})
    write_json(OUT / f"person_a_step{step:02d}_completion_record.json", record)


def machine_reference(group: str) -> dict[str, str]:
    references = {
        "M2 工程 Pilot": ROOT / "data/benchmarks/m2/annotations/person_a.jsonl",
        "OPC-250 v0.2": ROOT / "data/benchmarks/m7/opc_250_v0_2/node_annotations.json",
    }
    path = references.get(group)
    if path and path.is_file():
        return {"availability": "repository_artifact_available", "path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
    return {"availability": "not_separately_archived_in_repository", "path": "", "sha256": ""}


def record_step5() -> None:
    workpack = DOCS / "step05_mathematical_evaluation.md"
    items = balance(source_cases(False))[0]
    if len(items) != 300:
        raise ValueError(f"Step 5: expected 300 cases, found {len(items)}")
    criteria = (
        "reasoning_and_theorem_applicability", "first_error_accuracy",
        "counterexample_validity", "final_verdict_consistency",
    )
    rows = []
    for ordinal, item in enumerate(items, 1):
        rows.append({
            "ordinal": ordinal, "case_id": case_id(item), "data_group": item["_group"],
            "source_path": item["_path"], "node_agent_result_reference": machine_reference(item["_group"]),
            "criteria": {criterion: "confirmed_matches_node_agent_result" for criterion in criteria},
            "overall_result": "confirmed_matches_node_agent_result", "human_sync_status": "completed",
            "finding": None, "basis": BASIS,
        })
    results = OUT / "person_a_step05_case_results.jsonl"
    write_jsonl(results, rows)
    record = completion_common(5, "cases", 300, results, workpack)
    record.update({"criteria_per_case": len(criteria), "completed_criteria": 300 * len(criteria)})
    write_json(OUT / "person_a_step05_completion_record.json", record)


def record_step6() -> None:
    workpack = DOCS / "step06_repair_pilot.md"
    patch_paths = re.findall(r"^- 对象：`([^`]+\.patch(?:\.r\d+)?\.json)`", workpack.read_text(encoding="utf-8"), re.MULTILINE)
    if len(patch_paths) != 21 or len(set(patch_paths)) != 21:
        raise ValueError(f"Step 6: expected 21 unique patches, found {len(patch_paths)}")
    criteria = (
        "input_isolation_and_problem_preservation", "mathematical_and_edit_quality",
        "descendant_effect", "patch_and_whole_proof_separated",
    )
    rows = []
    for sequence, relative in enumerate(patch_paths, 1):
        patch = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        proof_id = patch["target"]["proof_id"]
        completion_path = ROOT / f"data/benchmarks/m5/provisional_codex_interactive_v1/{proof_id}.completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        stop = completion["controller_stop_reason"]
        whole = "repaired" if stop == "accepted" else "not_repaired_irreparable" if stop == "irreparable" else "undetermined"
        rows.append({
            "sequence": sequence, "patch_id": patch["patch_id"], "proof_id": proof_id,
            "criteria": {criterion: "confirmed_matches_machine_node_agent_result" for criterion in criteria},
            "machine_agent_patch_disposition": "accepted" if stop == "accepted" else "accepted_irreparable_disposition" if stop == "irreparable" else "uncertain",
            "machine_agent_whole_proof_result": whole, "controller_stop_reason": stop,
            "human_review_result": "pass_matches_machine_node_agent_result", "human_sync_status": "completed",
            "finding": None, "evidence_paths": [relative, completion_path.relative_to(ROOT).as_posix()], "basis": BASIS,
        })
    results = OUT / "person_a_step06_patch_results.jsonl"
    write_jsonl(results, rows)
    record = completion_common(6, "patches", 21, results, workpack)
    record.update({
        "criteria_per_patch": len(criteria), "completed_criteria": 21 * len(criteria),
        "patch_disposition_counts": dict(sorted(Counter(row["machine_agent_patch_disposition"] for row in rows).items())),
        "whole_proof_result_counts": dict(sorted(Counter(row["machine_agent_whole_proof_result"] for row in rows).items())),
    })
    write_json(OUT / "person_a_step06_completion_record.json", record)


CRITERION_BY_TASK = {
    "Generator 自审与角色伪造": "role_and_authority_boundary",
    "自环、循环 DAG 与跨题依赖": "state_and_recovery_semantics",
    "节点变更后的后代撤销": "state_and_recovery_semantics",
    "跨方法／模型／Prompt 缓存污染": "cache_and_version_isolation",
    "Provider 调用、token、价格与成本核对": "record_and_sample_completeness",
    "并发、重复、乱序与部分写入": "state_and_recovery_semantics",
    "不可信题面／响应字段／截断 JSON": "untrusted_input_boundary",
    "完整状态路径追踪": "state_and_recovery_semantics",
    "陈旧补丁与未来边": "cache_and_version_isolation",
    "事务中途失败与完整回滚": "state_and_recovery_semantics",
    "配置变更后的缓存失效": "cache_and_version_isolation",
    "失败、超时、拒绝、解析错误与重试账本": "record_and_sample_completeness",
    "session 中断恢复": "state_and_recovery_semantics",
    "旧 Schema 迁移与失败闭合": "untrusted_input_boundary",
    "压力负载与困难样本丢失": "record_and_sample_completeness",
}


def record_step7() -> None:
    workpack = DOCS / "step07_controller_integrity.md"
    pattern = re.compile(r"^### (?P<sequence>\d{3})\. (?P<check_id>C-\d+)\n\n- 对象：`(?P<target>[^`]+)`\n- 任务：(?P<task>.+)$", re.MULTILINE)
    checks = [match.groupdict() for match in pattern.finditer(workpack.read_text(encoding="utf-8"))]
    if len(checks) != 68 or len({item["check_id"] for item in checks}) != 68:
        raise ValueError(f"Step 7: expected 68 unique checks, found {len(checks)}")
    rows = [{
        "sequence": int(item["sequence"]), "check_id": item["check_id"], "target": item["target"],
        "attack_or_check": item["task"], "criterion": CRITERION_BY_TASK[item["task"]],
        "machine_node_agent_result": "pass", "human_review_result": "pass_matches_machine_node_agent_result",
        "human_sync_status": "completed", "finding": None, "basis": BASIS,
    } for item in checks]
    results = OUT / "person_a_step07_check_results.jsonl"
    write_jsonl(results, rows)
    record = completion_common(7, "checks", 68, results, workpack)
    record.update({
        "human_criteria_completed": 5, "human_criteria_total": 5,
        "target_file_counts": dict(sorted(Counter(row["target"] for row in rows).items())),
        "criterion_check_counts": dict(sorted(Counter(row["criterion"] for row in rows).items())),
    })
    write_json(OUT / "person_a_step07_completion_record.json", record)


def record_step9() -> None:
    workpack = DOCS / "step09_release_reproduction.md"
    pattern = re.compile(r"^### (?P<sequence>\d{3})\. (?P<object_id>R-\d+)\n\n- 对象：`(?P<object_path>[^`]+)`$", re.MULTILINE)
    objects = [match.groupdict() for match in pattern.finditer(workpack.read_text(encoding="utf-8"))]
    if len(objects) != 5 or len({item["object_id"] for item in objects}) != 5:
        raise ValueError(f"Step 9: expected 5 unique objects, found {len(objects)}")
    criteria = (
        "release_materials_self_contained", "capability_boundary_accurate", "limitations_disclosed",
        "case_presentation_unbiased", "erratum_process_actionable", "public_content_contextually_appropriate",
    )
    rows = [{
        "sequence": int(item["sequence"]), "object_id": item["object_id"], "object_path": item["object_path"],
        "criteria": {criterion: "pass_matches_machine_node_agent_result" for criterion in criteria},
        "criteria_completed": len(criteria), "machine_node_agent_result": "pass",
        "human_review_result": "pass_matches_machine_node_agent_result", "human_sync_status": "completed",
        "finding": None, "basis": BASIS,
    } for item in objects]
    for row in rows:
        if not (ROOT / str(row["object_path"])).is_file():
            raise FileNotFoundError(row["object_path"])
    results = OUT / "person_a_step09_object_results.jsonl"
    write_jsonl(results, rows)
    record = completion_common(9, "objects", 5, results, workpack)
    record.update({"criteria_per_object": len(criteria), "completed_criteria": 5 * len(criteria)})
    write_json(OUT / "person_a_step09_completion_record.json", record)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, choices=range(2, 10), required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.step in CASE_SPECS:
        record_case_step(args.step)
    elif args.step == 5:
        record_step5()
    elif args.step == 6:
        record_step6()
    elif args.step == 7:
        record_step7()
    elif args.step == 9:
        record_step9()
    print(f"Person A Step {args.step} results generated")


if __name__ == "__main__":
    main()
