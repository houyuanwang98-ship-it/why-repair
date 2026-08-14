"""Audit the M4 release and its v0.3 compatibility replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from scripts.verify_m4_external_evidence import verify_blind_run, verify_signoffs
except ModuleNotFoundError:  # Direct execution places scripts/ rather than repository root on sys.path.
    from verify_m4_external_evidence import verify_blind_run, verify_signoffs


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m4_verifier import verify_audit_records


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def audit() -> dict:
    integrated_path = ROOT / "data" / "benchmarks" / "m4" / "integrated_acceptance_v1_1.json"
    archive_path = ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "global_counterexample_replay_v1.json"
    latency_path = ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "latency_benchmark_v1.json"
    signoff_path = ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "external_human_signoff_packet_v1.json"
    gold_path = ROOT / "data" / "benchmarks" / "m2" / "gold" / "algebra_pilot_v1.jsonl"
    local_path = ROOT / "data" / "fixtures" / "m4" / "person_a_gold_scope_cases.json"
    integrated = load(integrated_path)
    archive = load(archive_path)
    latency = load(latency_path)
    signoff = load(signoff_path)
    local_cases = load(local_path)["cases"]
    gold_ids = {
        row["proof_id"] for row in load_jsonl(gold_path)
        if row["gold_counterexample_status"] == "valid"
    }
    result_ids = {result["context_id"] for result in archive["results"]}
    artifact_hashes_valid = all(
        (ROOT / name).is_file() and digest(ROOT / name) == expected
        for name, expected in integrated["artifacts"].items()
    )
    pending_positions = {
        event["certificate_id"]: index for index, event in enumerate(archive["events"])
        if event["event"] == "m4_pending_verification"
    }
    terminal_positions = {
        event["certificate_id"]: index for index, event in enumerate(archive["events"])
        if event["event"] == "m4_counterexample_processed"
    }
    pending_order_valid = (
        set(pending_positions) == set(terminal_positions) == {result["certificate_id"] for result in archive["results"]}
        and all(pending_positions[item] < terminal_positions[item] for item in pending_positions)
    )
    every_verified = all(
        result["state"] == "accepted"
        and result["verification"]["status"] == "verified"
        and result["review"]["accepted"] is True
        and result["review"]["scope"] == "global_theorem"
        for result in archive["results"]
    )
    exact_truth_bindings = all(
        all(binding["holds"] is True for binding in record["premise_bindings"])
        and record["target_binding"]["holds"] is False
        for record in archive["audit_records"]
    )
    local_global_fixture_separated = (
        {case["source_sample_id"]: case["certificate"]["scope"] for case in local_cases}
        == {"m2-021": "global_theorem", "m2-034": "local_claim"}
    )
    negative_controls_valid = (
        {item["control_id"]: item["result"]["state"] for item in archive["negative_controls"]}
        == {"target_true": "rejected", "unsupported_expression": "undetermined"}
        and all(item["result"]["state"] != "accepted" for item in archive["negative_controls"])
        and all(item["snapshot"]["audit_chain_valid"] for item in archive["negative_controls"])
    )
    unsupported_disposition_valid = any(
        item["control_id"] == "unsupported_expression"
        and item["expected_state"] == "undetermined"
        and item["result"]["state"] == "undetermined"
        for item in archive["negative_controls"]
    )
    cost_record_valid = archive["verification_cost"] == {
        "global_verifier_calls": 11,
        "negative_control_verifier_calls": 2,
        "total_verifier_calls": 13,
        "external_tool_calls": 0,
        "external_cost_usd": 0.0,
        "latency_status": "not_recorded_to_keep_deterministic_replay_byte_stable",
    }
    engineering_discovery_valid = (
        archive["metrics"]["engineering_nonblind_discovered_count"] == 11
        and archive["metrics"]["engineering_nonblind_discovery_denominator"] == 11
        and archive["metrics"]["engineering_nonblind_discovery_rate"] == 1.0
        and archive["metrics"]["publication_blind_discovery_rate"] is None
        and archive["source"]["nonblind_response_ledger_sha256"]
        == digest(ROOT / archive["source"]["nonblind_response_ledger"])
    )
    latency_valid = (
        latency["scope"] == "current_machine_non_publication_operational_measurement"
        and latency["rounds"] >= 20
        and all(isinstance(latency["latency_ms"][key], (int, float)) and latency["latency_ms"][key] > 0
                for key in ("min", "median", "mean", "p95", "max"))
        and latency["external_tool_calls_per_round"] == 0
        and latency["external_cost_usd_per_round"] == 0.0
    )
    signoff_packet_ready = (
        signoff["schema_version"] == "m4-external-human-signoff-1.0"
        and len(signoff["signoffs"]) == 2
        and len({item["slot"] for item in signoff["signoffs"]}) == 2
        and all(signoff["review_protocol"].values())
        and signoff["review_target"]["archive_sha256"]
        == digest(ROOT / signoff["review_target"]["archive_file"])
    )
    signoffs_complete = verify_signoffs(signoff)
    blind_path = ROOT / "data" / "benchmarks" / "m4" / "revalidation" / "prospective_blind_run_v1.json"
    blind_complete = blind_path.is_file() and verify_blind_run(load(blind_path))
    automated = {
        "integrated_v1_1_artifact_hashes_match": artifact_hashes_valid,
        "archive_source_hashes_match": archive["source"]["gold_sha256"] == digest(gold_path),
        "archive_covers_exactly_all_11_valid_gold_counterexamples": result_ids == gold_ids and len(result_ids) == 11,
        "pending_precedes_every_terminal_verification": pending_order_valid,
        "all_archived_candidates_program_verified_and_person_a_contract_gate_accepted": every_verified,
        "all_premises_true_and_all_targets_false": exact_truth_bindings,
        "audit_hash_chain_valid": archive["audit_chain_valid"] is True and verify_audit_records(archive["audit_records"]),
        "reviewer_and_verifier_roles_are_distinct": archive["reviewer_id"] != archive["verifier_id"],
        "local_and_global_regression_scopes_are_separate": local_global_fixture_separated,
        "tool_profile_and_resource_bounds_archived": set(archive["verification_environment"]) == {
            "engine", "engine_profile", "max_ast_nodes", "max_expression_length",
            "max_integer_bits", "max_abs_exponent", "timeout_policy",
        },
        "frozen_negative_controls_fail_closed": negative_controls_valid,
        "unsupported_expression_is_archived_as_undetermined": unsupported_disposition_valid,
        "deterministic_verification_call_and_external_cost_recorded": cost_record_valid,
        "nonblind_engineering_discovery_rate_is_source_bound": engineering_discovery_valid,
        "current_operational_latency_is_archived": latency_valid,
        "external_human_signoff_packet_is_ready": signoff_packet_ready,
    }
    gates = {
        "engineering_counterexample_discovery_rate": "pass" if engineering_discovery_valid else "fail_engineering_discovery_evidence_invalid",
        "publication_blind_counterexample_discovery_rate": "pass" if blind_complete else "fail_no_verified_prospective_blind_candidate_generation_run",
        "invalid_candidate_failure_distribution": "pass" if negative_controls_valid else "fail_negative_control_archive_invalid",
        "unsupported_expression_human_disposition_archive": "pass" if unsupported_disposition_valid else "fail_unsupported_disposition_missing",
        "human_identity_authentication": "pass" if signoffs_complete else "fail_external_cryptographic_signatures_pending",
        "new_human_revalidation": "pass" if signoffs_complete else "fail_two_external_independent_reviews_pending",
        "historical_blind_independence": "superseded_by_verified_prospective_run" if blind_complete else "fail_not_reconstructable_use_prospective_protocol",
        "verification_compute_cost": "pass" if cost_record_valid else "fail_verification_cost_missing",
        "verification_latency": "pass" if latency_valid else "fail_latency_report_invalid",
    }
    strict_pass = all(automated.values()) and all(
        value == "pass" or (key == "historical_blind_independence" and value == "superseded_by_verified_prospective_run")
        for key, value in gates.items()
    )
    return {
        "schema_version": "m4-revalidation-audit-1.0",
        "release": "m4-integrated-v1.1+controller-v0.3-replay",
        "result": "pass" if strict_pass else "engineering_pass_strict_acceptance_blocked",
        "automated_checks": automated,
        "strict_evidence_gates": gates,
        "metrics": archive["metrics"],
        "immutable_hashes": {
            "integrated_acceptance_v1_1_sha256": digest(integrated_path),
            "global_counterexample_replay_sha256": digest(archive_path),
            "controller_v0_3_sha256": digest(ROOT / "harness" / "m4_controller_v0_3.py"),
            "replay_builder_sha256": digest(ROOT / "scripts" / "build_m4_revalidation.py"),
            "latency_benchmark_sha256": digest(latency_path),
            "external_signoff_packet_sha256": digest(signoff_path),
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
