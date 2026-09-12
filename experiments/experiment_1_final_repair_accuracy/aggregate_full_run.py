"""Aggregate the completed full600_v1 blind-judge run into publication-ready artifacts."""
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs" / "full600_v1"
METHODS = ["original", "direct_rewrite", "self_refine", "generator_critic", "full_system"]

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def strict(j):
    return j["verdict"] == "valid" and j["rigorous"] and j["problem_preserved"]

data = {x["case_id"]: x for x in read_jsonl(HERE / "dataset.jsonl")}
gold = {x["case_id"]: x for x in read_jsonl(HERE / "gold_index.jsonl")}
rows, missing = [], []
for case_id, case in data.items():
    d = RUNS / case_id
    needed = [d / "generation.json", d / "judgment.json", d / "mapping.json"]
    if not all(p.exists() for p in needed):
        missing.append(case_id); continue
    judgment = json.loads((d / "judgment.json").read_text(encoding="utf-8"))
    mapping = json.loads((d / "mapping.json").read_text(encoding="utf-8"))
    base = {"case_id": case_id, "group": case["group"], "gold_original_verdict": gold[case_id]["original_verdict"]}
    oj = judgment["original"]
    rows.append({**base, "method": "original", **oj, "strict_success": strict(oj)})
    for item in judgment["candidates"]:
        j = item["judgment"]
        rows.append({**base, "method": mapping[item["candidate_id"]], **j, "strict_success": strict(j)})

summary = {}
for method in METHODS:
    rr = [r for r in rows if r["method"] == method]
    summary[method] = {
        "n": len(rr),
        "strict_success": sum(r["strict_success"] for r in rr),
        "strict_success_rate": round(sum(r["strict_success"] for r in rr) / len(rr), 6) if rr else None,
        "verdict_counts": dict(Counter(r["verdict"] for r in rr)),
        "rigorous": sum(r["rigorous"] for r in rr),
        "problem_preserved": sum(r["problem_preserved"] for r in rr),
    }
    for label in ("invalid", "valid", "valid_with_gap", "undetermined"):
        subset = [r for r in rr if r["gold_original_verdict"] == label]
        summary[method][f"gold_{label}_n"] = len(subset)
        summary[method][f"gold_{label}_strict_success"] = sum(r["strict_success"] for r in subset)

artifact = {
    "run_id": "full600_v1", "evaluation": "independent_blind_ai_judge",
    "strict_success_definition": "verdict=valid AND rigorous=true AND problem_preserved=true",
    "dataset_cases": len(data), "completed_cases": len(data) - len(missing), "missing_cases": missing,
    "structured_original_gold_cases": sum(gold[x]["original_verdict"] != "not_structured" for x in gold),
    "summary": summary,
}
(HERE / "aggregate_results.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with (HERE / "comparison_results.jsonl").open("w", encoding="utf-8") as f:
    for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")

lines = ["# Experiment 1: full 600-case results", "", "Strict success means the blind judge marked the output valid, rigorous, and problem-preserving.", "",
         "| Method | Strict success | Rate | Valid | Rigorous | Preserved |", "|---|---:|---:|---:|---:|---:|"]
for method in METHODS:
    s = summary[method]
    lines.append(f"| {method} | {s['strict_success']}/{s['n']} | {100*s['strict_success_rate']:.1f}% | {s['verdict_counts'].get('valid',0)} | {s['rigorous']} | {s['problem_preserved']} |")
lines += ["", "## Structured-gold invalid subset", "", "This subset contains the 216 inputs whose original project gold label is `invalid`.", "", "| Method | Strictly valid output | Rate |", "|---|---:|---:|"]
for method in METHODS:
    s=summary[method]; n=s['gold_invalid_n']; k=s['gold_invalid_strict_success']
    lines.append(f"| {method} | {k}/{n} | {100*k/n:.1f}% |")
lines += ["", "## Interpretation boundary", "", "These are AI-judged experimental measurements, not human gold labels for the newly generated repairs. The four repair workflows were produced together in one schema-constrained generator call per problem, so this run is an exploratory controlled prompted comparison; it is not yet an isolated compute-matched ablation. Human adjudication of a stratified output sample is required before using the numbers as a paper's headline claim.", ""]
(HERE / "FULL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"completed": artifact["completed_cases"], "missing": len(missing), "summary": summary}, ensure_ascii=False))
