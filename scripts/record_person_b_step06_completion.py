"""Materialize the user-confirmed Person B Step 6 review results."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKPACK = ROOT / "docs/manual_validation/person_b/step06_repair_pilot.md"
OUT_DIR = ROOT / "data/manual_validation"
RESULTS = OUT_DIR / "person_b_step06_patch_results.jsonl"
COMPLETION = OUT_DIR / "person_b_step06_completion_record.json"
PILOT_DIR = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"

CRITERIA = {
    "input_isolation": "confirmed_matches_machine_agent_result",
    "problem_preservation": "confirmed_matches_machine_agent_result",
    "mathematical_and_edit_quality": "confirmed_matches_machine_agent_result",
    "descendants_revalidated": "confirmed_matches_machine_agent_result",
    "patch_and_whole_proof_separated": "confirmed_matches_machine_agent_result",
}


def main() -> None:
    text = WORKPACK.read_text(encoding="utf-8")
    patch_paths = re.findall(r"^- 对象：`([^`]+\.patch(?:\.r\d+)?\.json)`", text, re.MULTILINE)
    if len(patch_paths) != 21 or len(set(patch_paths)) != 21:
        raise ValueError(f"expected 21 unique patch paths, found {len(patch_paths)}")

    rows = []
    for index, relative_patch in enumerate(patch_paths, 1):
        patch_path = ROOT / relative_patch
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
        proof_id = patch["target"]["proof_id"]
        completion_path = PILOT_DIR / f"{proof_id}.completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        stop_reason = completion["controller_stop_reason"]
        if stop_reason == "accepted":
            patch_disposition = "accepted"
            whole_proof_result = "repaired"
        elif stop_reason == "irreparable":
            patch_disposition = "accepted_irreparable_disposition"
            whole_proof_result = "not_repaired_irreparable"
        else:
            patch_disposition = "uncertain"
            whole_proof_result = "undetermined"

        evidence_paths = [relative_patch, completion_path.relative_to(ROOT).as_posix()]
        review_suffix = ".r2" if ".r2.json" in relative_patch else ""
        for suffix in (f".review_context{review_suffix}.json", f".person_a_review{review_suffix}.json"):
            evidence = PILOT_DIR / f"{proof_id}{suffix}"
            if evidence.exists():
                evidence_paths.append(evidence.relative_to(ROOT).as_posix())

        rows.append(
            {
                "sequence": index,
                "patch_id": patch["patch_id"],
                "proof_id": proof_id,
                "operation": patch["operation"],
                "criteria": CRITERIA,
                "human_sync_status": "completed_matches_machine_agent_results",
                "machine_agent_patch_disposition": patch_disposition,
                "machine_agent_whole_proof_result": whole_proof_result,
                "controller_stop_reason": stop_reason,
                "evidence_paths": evidence_paths,
                "basis": "project_owner_confirmation_2026-09-09",
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    RESULTS.write_text(payload, encoding="utf-8", newline="\n")

    patch_counts = Counter(row["machine_agent_patch_disposition"] for row in rows)
    proof_counts = Counter(row["machine_agent_whole_proof_result"] for row in rows)
    record = {
        "schema_version": "person-b-step06-completion-v0.1",
        "person": "Person B",
        "step": 6,
        "status": "human_review_results_synchronized",
        "recorded_on": "2026-09-09",
        "assigned_patches": len(rows),
        "completed_patches": len(rows),
        "criteria_per_patch": len(CRITERIA),
        "completed_criteria": len(rows) * len(CRITERIA),
        "patch_disposition_counts": dict(sorted(patch_counts.items())),
        "whole_proof_result_counts": dict(sorted(proof_counts.items())),
        "result_basis": "The project owner confirmed all five human-review criteria match the machine/node-agent results.",
        "formal_real_pilot_gate": "blocked_missing_api_provenance_and_provider_records",
        "limitations": [
            "The synchronized result records the owner's completed human review; it is not an independent identity or signature attestation.",
            "Provider response IDs, exact production model snapshot, token usage, latency, retries, and billing evidence remain unavailable.",
            "Five accepted irreparable dispositions are not counted as repaired proofs.",
        ],
        "case_results_path": RESULTS.relative_to(ROOT).as_posix(),
        "case_results_sha256": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
    }
    COMPLETION.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
