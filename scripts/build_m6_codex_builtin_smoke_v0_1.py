#!/usr/bin/env python3
"""Materialize a 9-method x 3-case Codex built-in engineering smoke."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m6_experiments import METHOD_IDS, METHOD_SPECS


OUT = ROOT / "data/benchmarks/m6/codex_builtin_smoke_v0_1"
CASES = {
    "m2-011": {"predicted_verdict": "gap", "required_rounds": 1,
                "diagnosis": "missing algebraic bridge from odd witnesses to twice an integer"},
    "m2-018": {"predicted_verdict": "gap", "required_rounds": 1,
                "diagnosis": "missing equality-compatible multiplication and transitivity bridge"},
    "m2-034": {"predicted_verdict": "invalid", "required_rounds": 2,
                "diagnosis": "two sequential false claims about principal square root and absolute value"},
}


def build():
    assignments = []
    for method_id in METHOD_IDS:
        spec = METHOD_SPECS[method_id]
        for sample_id, case in CASES.items():
            if not spec.produces_patch:
                repair_outcome = "not_applicable_diagnosis_only"
            elif spec.max_patch_rounds < case["required_rounds"]:
                repair_outcome = "partial_round_budget_exhausted"
            elif method_id == "no_descendant_invalidation" and case["required_rounds"] > 1:
                repair_outcome = "partial_downstream_state_not_revalidated"
            else:
                repair_outcome = "accepted_repair"
            assignments.append({
                "assignment_id": f"{method_id}:{sample_id}", "method_id": method_id,
                "sample_id": sample_id, "method_capabilities": {
                    "sees_nodes": spec.sees_nodes, "sees_graph": spec.sees_graph,
                    "structured_certificate": spec.structured_certificate,
                    "counterexample_protocol": spec.counterexample_protocol,
                    "descendant_invalidation": spec.descendant_invalidation,
                    "produces_patch": spec.produces_patch, "max_patch_rounds": spec.max_patch_rounds,
                },
                "predicted_verdict": case["predicted_verdict"], "diagnosis": case["diagnosis"],
                "required_repair_rounds": case["required_rounds"], "repair_outcome": repair_outcome,
                "execution_status": "completed_codex_builtin_interactive_projection",
                "provider_model_calls": 0, "provider_cost_usd": 0,
            })
    summary = {
        "schema_version": "m6-codex-builtin-smoke-0.1",
        "execution_mode": "single_active_codex_agent_interactive_projection",
        "method_count": len(METHOD_IDS), "sample_count": len(CASES),
        "assignment_count": len(assignments),
        "accepted_repair_count": sum(row["repair_outcome"] == "accepted_repair" for row in assignments),
        "partial_repair_count": sum(row["repair_outcome"].startswith("partial_") for row in assignments),
        "diagnosis_only_count": sum(row["repair_outcome"].startswith("not_applicable") for row in assignments),
        "provider_model_calls": 0, "provider_cost_usd": 0,
        "scientific_claim_allowed": False,
        "formal_provider_gate": "blocked_no_independent_provider_provenance",
        "limitations": [
            "Assignments are projections by one active Codex agent, not isolated model calls.",
            "Method outputs share reasoning context and cannot support comparative efficacy claims.",
            "Token, latency, response ID, and billing evidence are unavailable.",
        ],
    }
    return assignments, summary


def write():
    assignments, summary = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assignments.json").write_text(json.dumps(assignments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return assignments, summary


if __name__ == "__main__":
    _, item = write()
    print(json.dumps(item, ensure_ascii=False))
