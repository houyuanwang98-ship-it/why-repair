"""Fail-closed live audit of the remaining formal-M7 entry evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/benchmarks/m7/formal_readiness_audit_v0_2.json"


def load(relative: str) -> dict:
    path = ROOT / relative
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def formal_candidate_ready() -> bool:
    """Verify the frozen OPC candidate from repository bytes, not a status claim."""
    base = ROOT / "data/benchmarks/m7/opc_250_v0_2"
    required = (base / "manifest.json", base / "candidate.jsonl",
                base / "seed_annotations.json", base / "LICENSE.OpenProofCorpus")
    if not all(path.is_file() for path in required):
        return False
    manifest = json.loads(required[0].read_text(encoding="utf-8"))
    records = [json.loads(line) for line in required[1].read_text(encoding="utf-8").splitlines()]
    seeds = json.loads(required[2].read_text(encoding="utf-8"))
    split_counts = {name: sum(row.get("split") == name for row in records)
                    for name in ("train", "development", "test")}
    return (
        200 <= len(records) <= 500
        and len(records) == manifest.get("record_count")
        and len({row.get("case_id") for row in records}) == len(records)
        and split_counts == manifest.get("split_counts")
        and canonical(records) == manifest.get("candidate_digest")
        and canonical(seeds) == manifest.get("seed_annotation_digest")
        and hashlib.sha256(required[3].read_bytes()).hexdigest() == manifest.get("license_sha256")
        and bool(manifest.get("repository"))
        and bool(manifest.get("commit"))
        and bool(manifest.get("license"))
    )


def build() -> dict:
    m5 = load("data/benchmarks/m5/joint_acceptance_v0_1.json")
    m6 = load("data/benchmarks/m6/interactive_joint_acceptance_v0_2.json")
    release = load("data/governance/m6_m7_user_execution_release_v0_1.json")
    signature_waived = (
        release.get("status") == "active"
        and release.get("cryptographic_signature_policy") == "waived_for_current_project_scope"
    )
    user_execution_allowed = (
        signature_waived
        and release.get("m6_execution_allowed") is True
        and release.get("m7_execution_allowed") is True
    )
    checks = [
        ("m5_formal_m6_entry", "entry", m5.get("m6_entry_allowed") is True,
         "M5 live acceptance must set m6_entry_allowed=true from verified external evidence."),
        ("m6_formal_m7_entry", "entry", m6.get("formal_m7_experiment_allowed") is True,
         "M6 formal exit must authorize M7; interactive engineering permission is insufficient."),
        ("m6_three_party_detached_signatures", "entry", signature_waived,
         "Provide independently controlled detached signatures, or an explicit repository-owner scope waiver."),
        ("formal_candidate_200_to_500", "entry", formal_candidate_ready(),
         "Provide a new 200-500-case candidate with source, license, split, and raw-byte evidence."),
        ("independent_gold_and_adjudication", "entry", False,
         "Provide locked independent A/B annotations and third-expert adjudication where required."),
        ("provider_run_evidence", "completion", False,
         "Provide frozen provider/model configuration and raw attempt, retry, usage, latency, and billing records."),
    ]
    rows = [{"check_id": check_id, "phase": phase, "passed": passed, "required_evidence": evidence}
            for check_id, phase, passed, evidence in checks]
    entry_allowed = all(row["passed"] for row in rows if row["phase"] == "entry")
    complete = all(row["passed"] for row in rows)
    return {
        "schema_version": "m7-formal-readiness-audit-0.2",
        "status": "complete" if complete else (
            "ready_for_provider_execution" if entry_allowed else "blocked_requires_human_and_external_evidence"
        ),
        "interactive_50_case_m7_complete": True,
        "formal_m7_execution_allowed": entry_allowed,
        "formal_m7_complete": complete,
        "user_authorized_execution": {
            "release_record": "data/governance/m6_m7_user_execution_release_v0_1.json",
            "signature_requirement_waived": signature_waived,
            "m6_execution_allowed": user_execution_allowed,
            "m7_execution_allowed": user_execution_allowed,
            "scientific_claim_allowed": False,
        },
        "checks": rows,
        "next_human_action": (
            "Supply independently verifiable M5/M6 sign-off and locked independent A/B Gold; provider "
            "execution remains later and must not begin before those entry gates pass."
        ),
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
