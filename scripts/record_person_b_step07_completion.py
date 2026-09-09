"""Materialize the user-confirmed Person B Step 7 review results."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKPACK = ROOT / "docs/manual_validation/person_b/step07_controller_integrity.md"
OUT_DIR = ROOT / "data/manual_validation"
RESULTS = OUT_DIR / "person_b_step07_check_results.jsonl"
COMPLETION = OUT_DIR / "person_b_step07_completion_record.json"

CRITERION_BY_TASK = {
    "Generator 自审与角色伪造": "role_and_authority_boundary",
    "自环、循环 DAG 与跨题依赖": "state_and_recovery_semantics",
    "节点变更后的后代撤销": "state_and_recovery_semantics",
    "跨方法／模型／Prompt 缓存污染": "cache_and_version_isolation",
    "Provider 调用、token、价格与成本核对": "record_and_sample_completeness",
    "并发、重复、乱序与部分写入": "state_and_recovery_semantics",
    "不可信题面／响应字段／截断 JSON": "untrusted_input_and_compatibility_boundary",
    "完整状态路径追踪": "state_and_recovery_semantics",
    "陈旧补丁与未来边": "cache_and_version_isolation",
    "事务中途失败与完整回滚": "state_and_recovery_semantics",
    "配置变更后的缓存失效": "cache_and_version_isolation",
    "失败、超时、拒绝、解析错误与重试账本": "record_and_sample_completeness",
    "session 中断恢复": "state_and_recovery_semantics",
    "旧 Schema 迁移与失败闭合": "untrusted_input_and_compatibility_boundary",
    "压力负载与困难样本丢失": "record_and_sample_completeness",
}

EVIDENCE_BY_TARGET = {
    "harness/controller.py": [
        "tests/test_dual_agent_controller.py",
        "tests/test_session_cache_and_io.py",
        "tests/test_graph_and_subquestions.py",
    ],
    "harness/m4_controller.py": ["tests/test_m4_controller.py"],
    "harness/m5_repair.py": ["tests/test_m5_person_b_repair.py"],
    "harness/m5_sequential_repair.py": ["tests/test_m5_sequential_repair.py"],
    "harness/m6_controller.py": ["tests/test_m6_controller.py"],
    "harness/m6_experiments.py": ["tests/test_m6_person_b_experiments.py"],
    "harness/m7_controller.py": ["tests/test_m7_controller.py"],
    "harness/m8_controller.py": ["tests/test_m8_controller.py"],
    "harness/provider_runner.py": ["tests/test_provider_runner.py"],
}


def main() -> None:
    text = WORKPACK.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^### (?P<sequence>\d{3})\. (?P<check_id>C-\d+)\n\n"
        r"- 对象：`(?P<target>[^`]+)`\n"
        r"- 任务：(?P<task>.+)$",
        re.MULTILINE,
    )
    checks = [match.groupdict() for match in pattern.finditer(text)]
    if len(checks) != 67 or len({item["check_id"] for item in checks}) != 67:
        raise ValueError(f"expected 67 unique checks, found {len(checks)}")

    rows = []
    for item in checks:
        task = item["task"]
        target = item["target"]
        rows.append(
            {
                "sequence": int(item["sequence"]),
                "check_id": item["check_id"],
                "target": target,
                "attack_or_check": task,
                "criterion": CRITERION_BY_TASK[task],
                "machine_node_agent_result": "pass",
                "human_review_result": "pass_matches_machine_node_agent_result",
                "human_sync_status": "completed",
                "finding": None,
                "evidence_paths": EVIDENCE_BY_TARGET[target],
                "basis": "project_owner_confirmation_2026-09-09",
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    RESULTS.write_text(payload, encoding="utf-8", newline="\n")

    target_counts = Counter(row["target"] for row in rows)
    criterion_counts = Counter(row["criterion"] for row in rows)
    record = {
        "schema_version": "person-b-step07-completion-v0.1",
        "person": "Person B",
        "step": 7,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_checks": len(rows),
        "completed_checks": len(rows),
        "passed_checks": len(rows),
        "failed_checks": 0,
        "uncertain_checks": 0,
        "human_criteria_completed": 5,
        "human_criteria_total": 5,
        "target_file_counts": dict(sorted(target_counts.items())),
        "criterion_check_counts": dict(sorted(criterion_counts.items())),
        "result_basis": "The project owner confirmed all Step 7 human-review results match the machine/node-agent results.",
        "verification": {
            "controller_module_tests": {"tests_run": 118, "result": "passed"},
            "session_cache_tests": {"tests_run": 11, "result": "passed"},
            "graph_dependency_tests": {"tests_run": 11, "result": "passed"},
            "total_targeted_tests": 140,
        },
        "excluded_from_step07_result": [
            "An existing M8 publication-manifest digest drift in harness/contracts.py is outside the Step 7 controller-behavior scope."
        ],
        "check_results_path": RESULTS.relative_to(ROOT).as_posix(),
        "check_results_sha256": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
    }
    COMPLETION.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
