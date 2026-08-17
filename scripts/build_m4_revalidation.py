"""Deterministically archive the complete M4 replay of frozen global counterexamples."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m4_controller_v0_3 import M4CounterexampleControllerV03


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def build() -> dict:
    gold_path = ROOT / "data" / "benchmarks" / "m2" / "gold" / "algebra_pilot_v1.jsonl"
    mapping_path = ROOT / "data" / "fixtures" / "m4" / "person_a_full_gold_review.json"
    response_path = ROOT / "data" / "benchmarks" / "m3" / "experiments" / "full50_codex_v1" / "session" / "responses.jsonl"
    gold = {
        row["proof_id"]: row for row in load_jsonl(gold_path)
        if row["gold_counterexample_status"] == "valid"
    }
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapped = {case["source_sample_id"]: case for case in mapping["cases"]}
    if set(gold) != set(mapped):
        raise ValueError("full-gold mapping must cover exactly every valid M2 counterexample")
    discovered = {
        row["result_id"] for row in load_jsonl(response_path)
        if row.get("kind") == "diagnosis"
        and row.get("result_id") in gold
        and row.get("response", {}).get("error_scope") == "original_theorem"
        and isinstance(row.get("response", {}).get("counterexample_or_witness"), str)
        and row["response"]["counterexample_or_witness"].strip()
    }

    controller = M4CounterexampleControllerV03()
    results = []
    for proof_id in sorted(gold):
        row = gold[proof_id]
        old = row["gold_counterexample"]
        case = mapped[proof_id]
        theorem_digest = "sha256:" + hashlib.sha256(row["theorem"].encode("utf-8")).hexdigest()
        assumption_digest = "sha256:" + hashlib.sha256("\n".join(row["assumptions"]).encode("utf-8")).hexdigest()
        theorem_ref = {
            "proof_id": proof_id,
            "theorem_version": row["theorem_version"],
            "theorem_digest": theorem_digest,
        }
        checks = old["assumption_checks"]
        if len(checks) != len(row["assumptions"]):
            raise ValueError(f"{proof_id}: Gold counterexample does not cover every assumption")
        certificate = {
            "schema_version": "0.3",
            "certificate_id": "m4-revalidation-" + proof_id,
            "target": None,
            "theorem_ref": theorem_ref,
            "scope": "global_theorem",
            "structure": row["domain"],
            "assignment": old["assignments"],
            "premise_checks": [
                {"statement": statement, "holds": True, "evidence": check["evidence"]}
                for statement, check in zip(row["assumptions"], checks)
            ],
            "checked_premise_refs": [],
            "global_assumption_digest": assumption_digest,
            "target_check": {
                "statement": row["theorem"],
                "holds": False,
                "evidence": old["verification_notes"],
            },
            "checker": "m4_person_a_contract_gate_revalidation",
        }
        controller.register_context(
            proof_id, scope="global_theorem", theorem_ref=theorem_ref,
            premise_refs=[], premise_statements=row["assumptions"],
            approved_premise_expressions=[case["premise_expression"]],
            approved_target_expression=case["target_expression"],
            target_statement=row["theorem"], structure=row["domain"],
            theorem_statement=row["theorem"], global_assumption_digest=assumption_digest,
        )
        results.append(controller.process(
            proof_id, certificate, claimed_error_type="false_theorem",
            premise_expressions=[case["premise_expression"]],
            target_expression=case["target_expression"],
        ))
    snapshot = controller.snapshot()
    negative_controls = []
    for name, assignment, premise_expression, expected_state in (
        ("target_true", {"a": 1}, "is_real(a)", "rejected"),
        ("unsupported_expression", {"a": -1}, "is_rational(a)", "undetermined"),
    ):
        negative = M4CounterexampleControllerV03()
        target = {"proof_id": "m4-negative-" + name, "node_id": "n1", "version": 1}
        certificate = {
            "schema_version": "0.3", "certificate_id": "m4-negative-" + name,
            "target": target, "theorem_ref": None, "scope": "local_claim",
            "structure": "rational_numbers", "assignment": assignment,
            "premise_checks": [{"statement": "a is real", "holds": True, "evidence": "numeric witness"}],
            "checked_premise_refs": [], "global_assumption_digest": "sha256:negative-control",
            "target_check": {"statement": "a=1", "holds": False, "evidence": "candidate claim"},
            "checker": "m4_negative_control",
        }
        negative.register_context(
            name, scope="local_claim", target=target, premise_refs=[],
            premise_statements=["a is real"], approved_premise_expressions=[premise_expression],
            approved_target_expression="a == 1", target_statement="a=1",
            structure="rational_numbers", global_assumption_digest="sha256:negative-control",
        )
        result = negative.process(
            name, certificate, claimed_error_type="false_local_claim",
            premise_expressions=[premise_expression], target_expression="a == 1",
        )
        if result["state"] != expected_state:
            raise ValueError(f"negative control {name} expected {expected_state}, got {result['state']}")
        negative_controls.append({"control_id": name, "expected_state": expected_state,
                                  "result": result, "snapshot": negative.snapshot()})
    accepted = sum(result["state"] == "accepted" for result in results)
    verified = sum(result["verification"]["status"] == "verified" for result in results)
    accepted_false = sum(
        result["state"] == "accepted"
        and (
            result["verification"]["status"] != "verified"
            or result["review"]["accepted"] is not True
        )
        for result in results
    )
    premise_bindings = [binding for record in snapshot["audit_records"] for binding in record["premise_bindings"]]
    return {
        "schema_version": "m4-revalidation-1.0",
        "source": {
            "gold_file": gold_path.relative_to(ROOT).as_posix(),
            "gold_sha256": sha256(gold_path),
            "mapping_file": mapping_path.relative_to(ROOT).as_posix(),
            "mapping_sha256": sha256(mapping_path),
            "nonblind_response_ledger": response_path.relative_to(ROOT).as_posix(),
            "nonblind_response_ledger_sha256": sha256(response_path),
        },
        "reviewer_id": snapshot["reviewer_id"],
        "verifier_id": snapshot["verifier_id"],
        "results": results,
        "audit_records": snapshot["audit_records"],
        "events": snapshot["events"],
        "negative_controls": negative_controls,
        "audit_chain_valid": snapshot["audit_chain_valid"],
        "verification_environment": snapshot["verification_environment"],
        "verification_cost": {
            "global_verifier_calls": len(results),
            "negative_control_verifier_calls": len(negative_controls),
            "total_verifier_calls": len(results) + len(negative_controls),
            "external_tool_calls": 0,
            "external_cost_usd": 0.0,
            "latency_status": "not_recorded_to_keep_deterministic_replay_byte_stable",
        },
        "metrics": {
            "candidate_count": len(results),
            "accepted_count": accepted,
            "verified_count": verified,
            "verification_validity_rate": verified / len(results) if results else None,
            "accepted_false_counterexample_count": accepted_false,
            "accepted_false_counterexample_rate": accepted_false / accepted if accepted else None,
            "premise_satisfaction_rate": sum(item["holds"] is True for item in premise_bindings) / len(premise_bindings) if premise_bindings else None,
            "global_scope_accuracy": sum(result["review"]["scope"] == "global_theorem" for result in results) / len(results) if results else None,
            "engineering_nonblind_discovered_count": len(discovered),
            "engineering_nonblind_discovery_denominator": len(gold),
            "engineering_nonblind_discovery_rate": len(discovered) / len(gold) if gold else None,
            "publication_blind_discovery_rate": None,
            "discovery_scope_note": "derived from a Gold-exposed non-publication M3 response ledger",
            "negative_control_count": len(negative_controls),
            "negative_control_accepted_count": sum(item["result"]["state"] == "accepted" for item in negative_controls),
            "unsupported_controls_kept_undetermined": sum(
                item["control_id"] == "unsupported_expression" and item["result"]["state"] == "undetermined"
                for item in negative_controls
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"Archived {result['metrics']['accepted_count']} accepted global counterexamples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
