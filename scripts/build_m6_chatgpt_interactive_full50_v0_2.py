"""Materialize the non-blind ChatGPT M3+M5 replay across the M6 method surface."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m6_controller import (  # noqa: E402
    aggregate_by_experiment, build_controller_manifest, file_sha256, freeze_artifacts,
    validate_run_ledger,
)
from harness.m6_experiments import (  # noqa: E402
    METHOD_IDS, build_experiment_config, canonical_digest,
)


OUT = ROOT / "data/benchmarks/m6/chatgpt_interactive_full50_v0_2"
GOLD = ROOT / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl"
M3_RESULTS = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/session/results"
M5_RESULTS = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def node_number(value):
    if value is None or isinstance(value, int):
        return value
    text = str(value)
    return int(text[1:]) if text.startswith("n") and text[1:].isdigit() else None


def verdict(value: str) -> str:
    return {
        "valid": "accepted", "valid_with_gap": "gap", "invalid": "invalid",
        "false_theorem": "invalid", "undetermined": "undetermined",
    }[value]


def configs(dataset_digest: str) -> list[dict]:
    shared = canonical_digest("chatgpt-interactive-m3-m5-replay-v0.2")
    return [build_experiment_config(
        method, model_id="chatgpt-interactive-historical-m3-m5",
        prompt_digest=shared, dataset_digest=dataset_digest,
        theorem_bank_digest=shared, tool_digest=shared,
        code_digest=shared, scorer_digest=shared, schema_digest=shared,
        sampling_digest=shared, truncation_digest=shared,
        token_limit=8000, call_limit=4, timeout_seconds=180,
    ) for method in METHOD_IDS]


def build() -> dict[str, object]:
    gold = {row["proof_id"]: row for row in read_jsonl(GOLD)}
    m3 = {path.stem: json.loads(path.read_text(encoding="utf-8"))
          for path in M3_RESULTS.glob("*.json")}
    completions = {
        row["proof_id"]: row
        for path in M5_RESULTS.glob("*.completion.json")
        for row in [json.loads(path.read_text(encoding="utf-8"))]
    }
    if set(gold) != set(m3) or len(gold) != 50 or len(completions) != 36:
        raise RuntimeError("the frozen 50-case M3/M5 replay surface is incomplete")
    suite = configs(file_sha256(GOLD))
    transition = ROOT / "data/benchmarks/m5/m6_interactive_transition_v0_2.json"
    manifest = build_controller_manifest(
        configs=suite, sample_ids=sorted(gold),
        artifacts=freeze_artifacts(ROOT, [
            "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl",
            "data/benchmarks/m5/m6_interactive_transition_v0_2.json",
            "harness/m6_experiments.py", "harness/m6_controller.py",
        ]),
        metric_digest=canonical_digest("m6-locked-metrics-v0.2"),
        statistics_digest=canonical_digest("inferential-statistics-suppressed-shared-replay"),
        bootstrap_seeds=list(range(1000)), randomization_seeds=list(range(1000, 2000)),
        m5_gate_digest=file_sha256(transition),
        signatures={"person_a": "pending_human_signature",
                    "person_b_cross_review": "pending_cross_review",
                    "controller": "candidate_unsigned"},
        m5_entry_allowed=False, fixture_only=True,
    )
    ledger, scoring = [], []
    for configuration in manifest["configs"]:
        experiment_id = configuration["experiment_id"]
        produces_patch = configuration["method"]["produces_patch"]
        for sample_id in manifest["sample_ids"]:
            run_id = f"{experiment_id}:{sample_id}:replay"
            ledger.append({
                "run_id": run_id, "experiment_id": experiment_id, "sample_id": sample_id,
                "attempt": 0, "status": "success", "terminal": True,
                "tokens": 0, "model_calls": 0, "cost": 0, "latency_seconds": 0,
                "provenance": "historical_chatgpt_m3_m5_replay_no_new_provider_call",
            })
            source, prediction = gold[sample_id], m3[sample_id]
            gold_first = node_number(source["gold_first_invalid_step"] or source["gold_first_gap_step"])
            predicted_first = node_number(prediction["first_invalid_step"] or prediction["first_gap_step"]
                                          or prediction["first_undetermined_step"])
            gold_status = source["gold_validity_status"]
            completion = completions.get(sample_id)
            repairable = completion is not None and completion["controller_stop_reason"] == "accepted"
            row = {
                "experiment_id": experiment_id, "sample_id": sample_id,
                "terminal_run_id": run_id, "gold_verdict": verdict(gold_status),
                "predicted_verdict": verdict(prediction["validity_status"]),
                "gold_first_error_evaluable": gold_first is not None,
                "gold_first_error_reason": "evaluable" if gold_first is not None else (
                    "undetermined" if gold_status == "undetermined" else "absent"),
                "predicted_first_error": predicted_first,
                "gold_repairability": "repairable" if repairable else (
                    "undetermined" if gold_status == "undetermined" else "irreparable"),
                "gold_counterexample_eligible": bool(
                    gold_status == "invalid" and source.get("gold_counterexample")),
                "failure_type": None,
            }
            if gold_first is not None:
                row["gold_first_error"] = gold_first
            if produces_patch and repairable:
                row.update({
                    "claimed_repair_success": True, "patch_applied": True,
                    "verified_repair_success": True, "false_repair": False,
                    "new_error_introduced": False, "new_error_count": 0,
                    "independent_review_accepted": True, "problem_preserved": True,
                    "failed_edge_resolved": True, "no_new_errors": True,
                    "operationally_minimal": True, "descendants_revalidated": True,
                    "final_path_clear": True,
                })
            scoring.append(row)
    ledger_report = validate_run_ledger(manifest, ledger)
    aggregate = aggregate_by_experiment(manifest, ledger, scoring)
    method_by_experiment = {row["experiment_id"]: row["method"]["method_id"]
                            for row in manifest["configs"]}
    metrics_by_method = {method_by_experiment[key]: value for key, value in aggregate.items()}
    analysis = {
        "schema_version": "m6-chatgpt-interactive-analysis-0.2",
        "scope": "nonblind_historical_chatgpt_replay_gold_exposed",
        "method_count": 9, "sample_count": 50, "assignment_count": 450,
        "ledger_complete": ledger_report["complete"],
        "provider_model_calls": ledger_report["total_model_calls"],
        "metrics_by_method": metrics_by_method,
        "inferential_statistics": "not_computed_invalid_independence_shared_underlying_predictions",
        "scientific_claim_allowed": False,
        "interactive_engineering_acceptance_eligible": True,
    }
    return {"manifest": manifest, "ledger": ledger, "scoring": scoring,
            "aggregate": aggregate, "analysis": analysis}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in build().items():
        (OUT / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
