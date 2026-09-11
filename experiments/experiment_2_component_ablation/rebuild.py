"""Freeze the original 300-case roster and audit experiment readiness. No model calls."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROSTER = "data/manual_validation/person_b_step05_case_results.jsonl"
METHODS = ["no_agent", "single_agent_repair", "dual_agent", "dual_agent_controller",
           "no_structured_certificate", "no_graph", "no_counterexample",
           "no_descendant_invalidation", "single_round"]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"

def build():
    sources = {}
    def read(path):
        raw = (ROOT / path).read_bytes()
        sources[path] = digest(raw)
        text = raw.decode("utf-8-sig")
        return [json.loads(x) for x in text.splitlines() if x.strip()] if path.endswith(".jsonl") else json.loads(text)
    roster = read(ROSTER)
    completion = read("data/manual_validation/person_b_step05_completion_record.json")
    read("data/benchmarks/m7/proofnet_250_v0_1/manifest.json")
    read("data/benchmarks/m7/proofnet_250_v0_1/derivation_plan.json")
    read("data/benchmarks/m7/opc_250_v0_2/manifest.json")
    for license_path in ("data/benchmarks/m7/opc_250_v0_2/LICENSE.OpenProofCorpus",
                         "data/benchmarks/m7/proofnet_250_v0_1/LICENSE.ProofNet"):
        sources[license_path] = digest((ROOT / license_path).read_bytes())
    source_indexes = {}
    for path in sorted({r["source_path"] for r in roster}):
        items = read(path)
        keys = [r.get("case_id", r.get("proof_id")) for r in items]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate source IDs: " + path)
        source_indexes[path] = dict(zip(keys, items))
    counts = Counter(r["dataset_group"] for r in roster)
    if len(roster) != 300 or dict(counts) != completion["dataset_counts"]:
        raise ValueError("Original roster count mismatch")
    if len({r["case_id"] for r in roster}) != 300:
        raise ValueError("Duplicate roster ID")
    inputs, audit = [], []
    duplicate_index = defaultdict(list)
    for r in roster:
        row = source_indexes[r["source_path"]][r["case_id"]]
        if "proof_steps" in row:
            problem, assumptions = row["theorem"], row.get("assumptions", [])
            proof = "\n".join(s["text"] for s in row["proof_steps"])
        else:
            problem, assumptions, proof = row["problem"], [], row["proof"]
        if not problem.strip() or not proof.strip():
            raise ValueError("Empty original proof: " + r["case_id"])
        payload = {"case_id": r["case_id"], "problem": problem,
                   "assumptions": assumptions, "proof": proof}
        content_hash = digest(dumps(payload).encode("utf-8"))
        duplicate_index[digest(dumps([problem, assumptions, proof]).encode("utf-8"))].append(r["case_id"])
        inputs.append(payload)
        ref = r["node_agent_result_reference"]
        available = bool(ref["path"]) and (ROOT / ref["path"]).is_file()
        if available:
            sources[ref["path"]] = digest((ROOT / ref["path"]).read_bytes())
        audit.append({"case_id": r["case_id"], "dataset": r["dataset_group"],
                      "source_path": r["source_path"], "input_sha256": content_hash,
                      "source_split": row.get("split", "pilot"),
                      "input_available": True, "historical_agent_file_available": available,
                      "historical_agent_reference": ref["path"] or None,
                      "historical_confirmation": r["overall_result"],
                      "new_method_outputs": {m: None for m in METHODS},
                      "independent_final_proof_score": None})
    result = {
        "schema_version": "experiment-2-original-roster-2.0",
        "status": "original_300_inputs_frozen_execution_and_scoring_pending",
        "experiment_completed": False,
        "new_model_calls": 0,
        "cohort_size": len(inputs),
        "dataset_counts": dict(counts),
        "inputs_available": len(inputs),
        "historical_agent_files_available": sum(c["historical_agent_file_available"] for c in audit),
        "exact_duplicate_content_groups": [v for v in duplicate_index.values() if len(v) > 1],
        "split_counts": dict(Counter(c["source_split"] for c in audit)),
        "methods": [{"method": m, "planned_cases": 300, "completed_cases": 0,
                     "scored_cases": 0, "successes": None, "accuracy": None,
                     "status": "not_run"} for m in METHODS],
        "retired_claim": "The previous 21-case 0/0/8/14 ladder is not an agent/controller ablation.",
        "blocking_evidence": [
            "No full-roster independent repair outputs for the requested methods.",
            "Historical review agreement is not a per-method final-proof correctness label.",
            "ProofNet source manifest marks mathematical Gold and error derivations pending."
        ]
    }
    case_md = ["# 实验2逐题状态（原项目300题）", "",
               "所有300题保留原证明。以下是输入与运行状态，不是预测正确率。",
               "", "| ID | 数据集 | 原输入 | 历史Agent文件 | 新消融结果 |",
               "|---|---|---|---|---|"]
    for c in audit:
        link = "../../" + c["source_path"]
        case_md.append(f"| {c['case_id']} | {c['dataset']} | [来源]({link}) | "
                       + ("可访问" if c["historical_agent_file_available"] else "未单独归档")
                       + " | 尚未运行/评分 |")
    summary = ["# 实验2结果：300题版本", "",
               "**状态：原始300题输入已冻结，方法运行和评分尚未完成。**",
               "本页没有300题正确率结果；null表示未测，不能解释为0%。", "",
               "| 原数据集 | 纳入题数 |", "|---|---:|"]
    summary += [f"| {k} | {v} |" for k,v in counts.items()]
    summary += ["", f"输入覆盖：{len(inputs)}/300；历史Agent文件可访问：{result['historical_agent_files_available']}/300。",
                f"分割分布：{result['split_counts']}。原清单含训练/开发数据，因此不是密封测试集。",
                "", "| 方法 | 计划题数 | 已运行 | 已评分 | 正确率 |",
                "|---|---:|---:|---:|---|"]
    summary += [f"| {m} | 300 | 0 | 0 | 未测 |" for m in METHODS]
    summary += ["", "撤回旧版21题阶梯中的38.1%、66.7%及28.6个百分点组件增益解释。"
                "旧内容可在Git提交ced4603查阅，仅属历史记录，不能用于本实验结论。", ""]
    return {
        "inputs.jsonl": "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in inputs),
        "case_audit.json": dumps(audit), "results.json": dumps(result),
        "source_manifest.json": dumps(dict(sorted(sources.items()))),
        "CASE_RESULTS.md": "\n".join(case_md) + "\n",
        "RESULTS.md": "\n".join(summary),
        "assignments.json": dumps([{"case_id": c["case_id"], "method": m,
                                   "input_sha256": c["input_sha256"], "status": "pending"}
                                  for c in audit for m in METHODS])
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    for name, text in outputs.items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit("Stale output: " + name)
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    print("PASS: original 300 cases; 2700 planned assignments; no fabricated results")

if __name__ == "__main__":
    main()
