"""Build the M7 non-blind interactive engineering replay from frozen M6 bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m6_experiments import METHOD_IDS, build_experiment_config, canonical_digest  # noqa: E402
from harness.m7_controller import (  # noqa: E402
    build_assignments, build_blind_review_plan, build_controller_manifest, select_replay_sample,
    validate_aggregate_table, validate_run_integrity,
)


OUT = ROOT / "data/benchmarks/m7/interactive_engineering_v0_2"
M6 = ROOT / "data/benchmarks/m6/chatgpt_interactive_full50_v0_2"
M6_ACCEPTANCE = ROOT / "data/benchmarks/m6/interactive_joint_acceptance_v0_2.json"
PERSON_A = ROOT / "data/benchmarks/m7/person_a_protocol_candidate_v0_1.json"
PERSON_B = ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json"
GOLD = ROOT / "data/benchmarks/m2/gold/algebra_pilot_v1.jsonl"


def digest_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_value(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def read(name: str) -> object:
    return json.loads((M6 / name).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def config_family(*, role_mode: str, dataset_digest: str) -> list[dict]:
    shared = canonical_digest("m7-interactive-historical-m6-projection-v0.2")
    models = ("chatgpt-interactive-historical-m3-m5" if role_mode == "same_model" else
              {"generator": "chatgpt-interactive-historical-generator",
               "critic": "chatgpt-interactive-historical-critic-label"})
    return [build_experiment_config(
        method, model_id=models, role_mode=role_mode, prompt_digest=shared,
        dataset_digest=dataset_digest, theorem_bank_digest=shared, tool_digest=shared,
        code_digest=shared, scorer_digest=shared, schema_digest=shared,
        sampling_digest=shared, truncation_digest=shared, token_limit=8000,
        call_limit=4, timeout_seconds=180,
    ) for method in METHOD_IDS]


def build() -> dict[str, object]:
    acceptance = json.loads(M6_ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("interactive_m7_engineering_allowed") is not True:
        raise RuntimeError("M6 does not permit M7 interactive engineering")
    if acceptance.get("formal_m7_experiment_allowed") is not False:
        raise RuntimeError("interactive builder requires the formal M7 gate to remain closed")
    m6_manifest = read("manifest.json")
    m6_ledger = read("ledger.json")
    m6_scoring = read("scoring.json")
    if not isinstance(m6_manifest, dict) or not isinstance(m6_ledger, list) or not isinstance(m6_scoring, list):
        raise RuntimeError("M6 replay artifacts have invalid top-level shapes")
    case_ids = list(m6_manifest["sample_ids"])
    if len(case_ids) != 50 or len(m6_ledger) != 450 or len(m6_scoring) != 450:
        raise RuntimeError("M6 replay is incomplete")
    m6_config_by_id = {row["experiment_id"]: row for row in m6_manifest["configs"]}
    source_score = {(row["sample_id"], m6_config_by_id[row["experiment_id"]]["method"]["method_id"]): row
                    for row in m6_scoring}
    source_run = {(row["sample_id"], m6_config_by_id[row["experiment_id"]]["method"]["method_id"]): row
                  for row in m6_ledger}
    dataset_digest = m6_manifest["configs"][0]["dataset_digest"]
    artifacts = {
        path: digest_bytes(ROOT / path) for path in (
            "data/benchmarks/m6/interactive_joint_acceptance_v0_2.json",
            "data/benchmarks/m6/chatgpt_interactive_full50_v0_2/manifest.json",
            "data/benchmarks/m6/chatgpt_interactive_full50_v0_2/ledger.json",
            "data/benchmarks/m6/chatgpt_interactive_full50_v0_2/scoring.json",
            "harness/m7_controller.py", "harness/m7_person_b.py",
        )
    }
    manifest = build_controller_manifest(
        config_families={
            "interactive_same_model_projection": config_family(role_mode="same_model", dataset_digest=dataset_digest),
            "interactive_different_models_label_projection": config_family(role_mode="different_models", dataset_digest=dataset_digest),
        },
        case_ids=case_ids, candidate_digest=digest_bytes(M6 / "manifest.json"),
        gold_digest=dataset_digest, artifacts=artifacts,
        person_a_manifest_digest=digest_bytes(PERSON_A),
        person_b_manifest_digest=digest_bytes(PERSON_B), replay_seed=20260817,
        root=ROOT, fixture_only=True, m7_entry_allowed=False,
    )
    assignments = build_assignments(manifest, root=ROOT)
    cases = {row["proof_id"]: row for row in read_jsonl(GOLD)}
    ledger, results, scoring, blind_records, review_payloads = [], [], [], [], {}
    for assignment in assignments:
        key = (assignment["case_id"], assignment["method_id"])
        old_run, old_score = source_run[key], source_score[key]
        run_id = f"m7-interactive:{assignment['family_id']}:{assignment['experiment_id']}:{assignment['case_id']}"
        raw_digest = digest_value({"source_run": old_run, "family": assignment["family_id"]})
        score_digest = digest_value({"source_score": old_score, "family": assignment["family_id"]})
        ledger.append({
            "case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
            "run_id": run_id, "status": "succeeded", "terminal": True, "tokens": 0,
            "model_calls": 0, "wall_ms": 0, "raw_output_sha256": raw_digest,
        })
        results.append({
            "case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
            "run_id": run_id, "status": "succeeded", "raw_output_sha256": raw_digest,
            "score_input_sha256": score_digest,
        })
        scoring.append({"family_id": assignment["family_id"], "method_id": assignment["method_id"],
                        "case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
                        "source_m6_score_sha256": digest_value(old_score), "score": old_score})
        public_case = {key: cases[assignment["case_id"]][key]
                       for key in ("proof_id", "theorem", "theorem_version", "assumptions", "domain", "proof_steps")}
        candidate = {key: value for key, value in old_score.items()
                     if key not in {"experiment_id", "terminal_run_id", "sample_id"}
                     and not key.startswith("gold_")
                     and key not in {"independent_review_accepted", "verified_repair_success"}}
        payload = {"case": public_case, "candidate_output": candidate,
                   "notice": "method identity and Gold decision intentionally withheld"}
        payload_digest = digest_value(payload)
        review_payloads[payload_digest] = payload
        blind_records.append({
            "case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
            "false_accept": (old_score["predicted_verdict"] == "accepted"
                             and old_score["gold_verdict"] != "accepted"),
            "invalid_global_counterexample": False,
            "false_repair": bool(old_score.get("false_repair", False)),
            "correct_verdict": old_score["predicted_verdict"] == old_score["gold_verdict"],
            "verified_repair_success": bool(old_score.get("verified_repair_success", False)),
            "undetermined": old_score["predicted_verdict"] == "undetermined",
            "infrastructure_failure": False, "review_payload_sha256": payload_digest,
        })
    integrity = validate_run_integrity(manifest, ledger, results, root=ROOT)
    aggregate = []
    for family, configs in manifest["config_families"].items():
        for config in configs:
            subset = [row for row in ledger if row["experiment_id"] == config["experiment_id"]]
            aggregate.append({"family_id": family, "experiment_id": config["experiment_id"],
                              "sample_count": len(subset), "success_count": len(subset),
                              "failure_count": 0, "tokens": 0, "model_calls": 0, "wall_ms": 0})
    validate_aggregate_table(manifest, ledger, aggregate, root=ROOT)
    replay = select_replay_sample(manifest, ledger, 20, root=ROOT)
    blind = build_blind_review_plan(blind_records, seed=20260817, max_controls=20)
    public_review_plan = blind["public_plan"]
    selected_payloads = sorted({row["review_payload_sha256"] for row in public_review_plan["review_rows"]})
    public_payloads = {key: review_payloads[key] for key in selected_payloads}
    replay_verification = {
        "schema_version": "m7-interactive-replay-verification-0.2",
        "selection_seed": manifest["replay_seed"], "selected_run_ids": replay,
        "selected_run_ids_sha256": digest_value(replay), "selected_count": len(replay),
        "all_selected_terminal_success": all(
            row["status"] == "succeeded" for row in ledger if row["run_id"] in set(replay)),
        "full_rebuild_result_digest": integrity["result_digest"],
        "provider_replay_performed": False,
        "boundary": "deterministic artifact reconstruction only; no provider was called",
    }
    analysis = {
        "schema_version": "m7-interactive-analysis-0.2",
        "status": "interactive_engineering_complete_formal_experiment_blocked",
        "scope": "nonblind_historical_m6_projection_gold_exposed",
        "case_count": 50, "family_count": 2, "method_count_per_family": 9,
        "assignment_count": len(assignments), "ledger_complete": integrity["complete"],
        "provider_model_calls": 0, "provider_cost": 0,
        "result_digest": integrity["result_digest"], "replay_sample_count": len(replay),
        "blind_review_row_count": len(public_review_plan["review_rows"]),
        "blind_review_payload_count": len(public_payloads),
        "blind_review_completed": False,
        "inferential_statistics": "not_computed_invalid_shared_historical_predictions",
        "scientific_claim_allowed": False, "formal_m7_experiment_allowed": False,
        "interactive_m7_engineering_complete": True,
        "limitations": [
            "The benchmark contains the existing 50 exposed-Gold Pilot cases, not a formal 200-500-case M7 benchmark.",
            "Both model-family labels project the same historical M6 predictions and are not independent provider runs.",
            "No new provider call, response ID, token, latency, billing, blind review, or third-expert evidence exists.",
        ],
    }
    return {"manifest": manifest, "ledger": ledger, "results": results, "scoring": scoring,
            "aggregate": aggregate, "replay_sample": replay,
            "replay_verification": replay_verification,
            "blind_review_plan": public_review_plan,
            "blind_review_payloads": public_payloads,
            "blind_review_sealed_mapping": blind["sealed_mapping"], "analysis": analysis}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in build().items():
        (OUT / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
