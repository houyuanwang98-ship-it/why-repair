"""Revalidate M3 without rewriting its frozen v1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data" / "benchmarks" / "m3" / "experiments" / "full50_codex_v1"
REVALIDATION = ROOT / "data" / "benchmarks" / "m3" / "revalidation"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def manifest_valid(path: Path) -> bool:
    manifest = load(path)
    return all((ROOT / name).is_file() and digest(ROOT / name) == expected for name, expected in manifest["artifacts"].items())


def audit() -> dict:
    freeze_path = RUN / "freeze_manifest.json"
    integrated_path = RUN / "integrated_freeze_manifest.json"
    config = load(RUN / "config.json")
    session = load(RUN / "session" / "session.json")
    responses = load_jsonl(RUN / "session" / "responses.jsonl")
    results = [load(path) for path in sorted((RUN / "session" / "results").glob("*.json"))]
    source = load_jsonl(ROOT / "data" / "benchmarks" / "m2" / "source" / "pilot_50.jsonl")
    m3_input = load_jsonl(ROOT / "data" / "benchmarks" / "m3" / "input" / "evaluator_pilot_v1.jsonl")
    gold = load_jsonl(ROOT / "data" / "benchmarks" / "m3" / "gold" / "evaluator_pilot_v1.jsonl")
    report_v2 = load(REVALIDATION / "full50_report_v0_2.json")

    source_map = {row["proof_id"]: row for row in source}
    input_map = {row["id"]: row for row in m3_input}
    gold_map = {row["proof_id"]: row for row in gold}
    results_map = {row["id"]: row for row in results}
    ids = set(source_map)
    content_aligned = ids == set(input_map) == set(gold_map) == set(results_map) and all(
        input_map[item]["theorem"] == source_map[item]["theorem"]
        and input_map[item]["assumptions"] == source_map[item]["assumptions"]
        and input_map[item]["flawed_proof_steps"] == [step["text"] for step in source_map[item]["proof_steps"]]
        for item in ids
    )
    accepted_evidence = all(
        node.get("verification_source") and node.get("diagnosis")
        for row in results for node in row.get("proof_graph", []) if node.get("status") == "closed"
    )
    nonclosed_fail_closed = all(
        node.get("diagnosis") or node.get("status") == "undetermined"
        for row in results for node in row.get("proof_graph", []) if node.get("status") != "closed"
    )
    response_kinds = {row.get("kind") for row in responses}
    response_shape_valid = all(
        set(row) == {"result_id", "node_id", "kind", "response"}
        and row["kind"] in {"ambient", "graph", "proof", "calculation", "diagnosis"}
        and isinstance(row["response"], dict)
        for row in responses
    )
    extended_metrics_present = (
        report_v2["schema_version"] == "m3-evaluator-report-0.2"
        and report_v2["sample_count"] == 50
        and report_v2["prediction_coverage"] == 1.0
        and "first_error_localization" in report_v2
        and "critical_dependency_omission_rate" in report_v2["dependency_edges"]
        and {"node_false_acceptance_rate", "proof_false_acceptance_rate", "proof_abstention_rate", "node_abstention_rate"} <= set(report_v2["safety_rates"])
        and {"overall_count", "overall_correct", "overall_accuracy"} <= set(report_v2["first_error_localization"])
    )
    automated = {
        "base_freeze_artifact_hashes_match": manifest_valid(freeze_path),
        "integrated_freeze_artifact_hashes_match": manifest_valid(integrated_path),
        "integrated_manifest_binds_base_manifest": load(integrated_path)["base_manifest_sha256"] == digest(freeze_path),
        "m2_source_m3_input_gold_and_results_align": content_aligned,
        "all_accepted_nodes_have_evidence": accepted_evidence,
        "all_nonclosed_nodes_have_diagnosis_or_undetermined": nonclosed_fail_closed,
        "response_ledger_shapes_and_stage_kinds_valid": response_shape_valid and response_kinds == {"ambient", "graph", "proof", "calculation", "diagnosis"},
        "v0_2_required_metrics_present": extended_metrics_present,
        "frozen_run_declares_non_publication_and_non_blind": config["publication_result"] is False and config["blind_to_gold"] is False,
    }
    gates = {
        "segmentation_f1": "fail_gold_has_no_character_spans",
        "gold_upstream_isolated_module_runs": "fail_no_complete_per_module_gold_upstream_run_artifacts",
        "held_out_test_isolation": "fail_frozen_pilot_was_non_blind_and_gold_exposed",
        "prompt_registry_version_and_hash": "fail_full50_session_does_not_record_prompt_hashes",
        "model_identity_consistency": "fail_config_and_session_record_different_model_identifiers" if config["model"] != session["model"] else "pass",
        "retry_timeout_token_and_cost_ledger": "fail_legacy_response_ledger_omits_call_attempt_token_cost_and_timeout_metadata",
        "contemporaneous_blind_person_a_review": "fail_joint_review_is_explicitly_post_freeze_non_blind",
        "m2_028_gold_issue_resolved": "fail_known_gold_issue_preserved_in_v1",
    }
    strict_pass = all(automated.values()) and all(value == "pass" for value in gates.values())
    return {
        "schema_version": "m3-revalidation-1.0",
        "release": "m3-evaluator-v1.0+metrics-v0.2",
        "result": "pass" if strict_pass else "engineering_pass_strict_acceptance_blocked",
        "automated_checks": automated,
        "strict_evidence_gates": gates,
        "statistics": {
            "samples": len(results),
            "response_records": len(responses),
            "response_kinds": {kind: sum(row["kind"] == kind for row in responses) for kind in sorted(response_kinds)},
            "accepted_nodes": sum(node.get("status") == "closed" for row in results for node in row.get("proof_graph", [])),
            "nonclosed_nodes": sum(node.get("status") != "closed" for row in results for node in row.get("proof_graph", [])),
            "v0_2_metrics": {
                "first_error_applicable_accuracy": report_v2["first_error_localization"]["exact_accuracy"],
                "first_error_overall_accuracy": report_v2["first_error_localization"]["overall_accuracy"],
                "critical_dependency_omission_rate": report_v2["dependency_edges"]["critical_dependency_omission_rate"],
                **report_v2["safety_rates"],
            },
        },
        "immutable_hashes": {
            "base_freeze_manifest_sha256": digest(freeze_path),
            "integrated_freeze_manifest_sha256": digest(integrated_path),
            "report_v0_2_sha256": digest(REVALIDATION / "full50_report_v0_2.json"),
            "evaluator_v0_2_sha256": digest(ROOT / "scripts" / "m3_evaluator_v0_2.py"),
            "report_schema_v0_2_sha256": digest(ROOT / "schemas" / "m3_evaluator_report_v0_2.schema.json"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 1 if args.strict and report["result"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
