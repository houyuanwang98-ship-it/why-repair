"""Import the completed 600-case common-run evidence and rebuild Experiment 2.

The source run evaluates the original proof and four anonymized repair outputs in
one independent judgment call per case.  This importer retains the case-level
judgments and method mapping, but not bulky model event logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
METHOD_MAP = {
    "original": "no_agent",
    "direct_rewrite": "single_agent",
    "self_refine": "single_agent_self_refine",
    "generator_critic": "dual_agent",
    "full_system": "dual_agent_controller",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def accepted(judgment: dict) -> bool:
    return (
        judgment["verdict"] == "valid"
        and judgment["problem_preserved"] is True
        and judgment["rigorous"] is True
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_run", type=Path)
    args = parser.parse_args()
    source = args.source_run.resolve()
    inputs = [json.loads(line) for line in (HERE / "inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = [row["case_id"] for row in inputs]
    if len(ids) != 600 or len(set(ids)) != 600:
        raise SystemExit("Experiment 2 inputs must contain exactly 600 unique cases")

    rows = []
    for case_id in ids:
        judgment_path = source / case_id / "judgment.json"
        mapping_path = source / case_id / "mapping.json"
        if not judgment_path.exists() or not mapping_path.exists():
            raise SystemExit(f"Incomplete common run: {case_id}")
        judgment = load_json(judgment_path)
        mapping = load_json(mapping_path)
        if judgment["case_id"] != case_id or set(mapping.values()) != set(METHOD_MAP) - {"original"}:
            raise SystemExit(f"Identity mismatch: {case_id}")
        by_candidate = {item["candidate_id"]: item["judgment"] for item in judgment["candidates"]}
        per_method = {"no_agent": judgment["original"]}
        for candidate_id, source_method in mapping.items():
            per_method[METHOD_MAP[source_method]] = by_candidate[candidate_id]
        for method, value in per_method.items():
            rows.append({"case_id": case_id, "method": method, "accepted": accepted(value), **value})

    evidence = HERE / "full600_case_judgments.jsonl"
    evidence.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    summary = {}
    for method in METHOD_MAP.values():
        subset = [row for row in rows if row["method"] == method]
        counts = Counter(row["verdict"] for row in subset)
        passed = sum(row["accepted"] for row in subset)
        summary[method] = {
            "n": len(subset),
            "accepted": passed,
            "acceptance_rate": passed / len(subset),
            "verdicts": dict(sorted(counts.items())),
            "problem_preserved": sum(row["problem_preserved"] for row in subset),
            "rigorous": sum(row["rigorous"] for row in subset),
            "mean_error_count": sum(row["error_count"] for row in subset) / len(subset),
        }
    result = {
        "schema_version": "experiment-2-full600-ablation-1.0",
        "status": "completed",
        "case_count": 600,
        "judgments": 3000,
        "metric": "independent_blind_model_acceptance",
        "acceptance_definition": "verdict=valid AND problem_preserved=true AND rigorous=true",
        "human_verified": False,
        "case_evidence": evidence.name,
        "case_evidence_sha256": digest,
        "methods": summary,
    }
    (HERE / "full600_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
