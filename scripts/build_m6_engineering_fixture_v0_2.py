"""Build the deterministic, provider-free M6 nine-method engineering fixture."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m6_controller import (
    aggregate_by_experiment, build_controller_manifest, file_sha256, freeze_artifacts,
    validate_run_ledger,
)
from harness.m6_experiments import (
    FIXTURE_DIGEST, METHOD_IDS, build_experiment_config, canonical_digest,
)


OUT = ROOT / "data/benchmarks/m6/engineering_fixture_v0_2"


def config(method_id: str) -> dict:
    return build_experiment_config(
        method_id, model_id="fixture-model-no-provider-call",
        prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
        theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST,
        token_limit=8000, call_limit=4, timeout_seconds=180,
    )


def build() -> dict[str, dict | list]:
    configs = [config(method) for method in METHOD_IDS]
    artifacts = freeze_artifacts(ROOT, [
        "harness/m6_experiments.py", "harness/m6_controller.py",
        "docs/milestones/M06_person_a_preregistered_protocol.md",
    ])
    m5_gate = ROOT / "data/benchmarks/m5/m6_interactive_transition_v0_2.json"
    manifest = build_controller_manifest(
        configs=configs, sample_ids=["fixture-valid", "fixture-invalid"],
        artifacts=artifacts, metric_digest=canonical_digest("m6-locked-metrics-v0.2"),
        statistics_digest=canonical_digest("m6-locked-statistics-v0.2"),
        bootstrap_seeds=list(range(100)), randomization_seeds=list(range(100, 200)),
        m5_gate_digest=file_sha256(m5_gate),
        signatures={"person_a": "pending_human_signature",
                    "person_b_cross_review": "pending_cross_review",
                    "controller": "candidate_unsigned"},
        m5_entry_allowed=False, fixture_only=True,
    )
    ledger = []
    scoring = []
    for configuration in manifest["configs"]:
        experiment_id = configuration["experiment_id"]
        for sample_id in manifest["sample_ids"]:
            run_id = f"{experiment_id}:{sample_id}:0"
            ledger.append({
                "run_id": run_id, "experiment_id": experiment_id,
                "sample_id": sample_id, "attempt": 0, "status": "success",
                "terminal": True, "tokens": 0, "model_calls": 0,
                "cost": 0, "latency_seconds": 0,
            })
            if sample_id == "fixture-valid":
                scoring.append({
                    "experiment_id": experiment_id, "sample_id": sample_id,
                    "terminal_run_id": run_id, "gold_verdict": "accepted",
                    "predicted_verdict": "accepted", "gold_first_error_evaluable": False,
                    "gold_first_error_reason": "absent", "predicted_first_error": None,
                    "gold_repairability": "irreparable", "gold_counterexample_eligible": False,
                    "failure_type": None,
                })
            else:
                scoring.append({
                    "experiment_id": experiment_id, "sample_id": sample_id,
                    "terminal_run_id": run_id, "gold_verdict": "invalid",
                    "predicted_verdict": "invalid", "gold_first_error_evaluable": True,
                    "gold_first_error": 1, "gold_first_error_reason": "evaluable",
                    "predicted_first_error": 1, "gold_repairability": "repairable",
                    "gold_counterexample_eligible": False, "failure_type": None,
                })
    ledger_report = validate_run_ledger(manifest, ledger)
    aggregate = aggregate_by_experiment(manifest, ledger, scoring)
    summary = {
        "schema_version": "m6-engineering-fixture-summary-0.2",
        "scope": "deterministic_provider_free_fixture_only",
        "method_count": len(configs), "sample_count": len(manifest["sample_ids"]),
        "assignment_count": len(ledger), "ledger_complete": ledger_report["complete"],
        "provider_model_calls": ledger_report["total_model_calls"],
        "provider_cost": ledger_report["total_cost"],
        "interactive_person_a_acceptance_consumed": True,
        "formal_m6_execution_allowed": False,
    }
    return {"manifest": manifest, "ledger": ledger, "scoring": scoring,
            "aggregate": aggregate, "summary": summary}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in build().items():
        (OUT / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
