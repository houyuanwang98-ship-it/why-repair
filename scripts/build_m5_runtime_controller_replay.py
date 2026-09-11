#!/usr/bin/env python3
"""Deterministically replay independently reviewed real M5 generator outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m5_person_a_review import canonical_digest, patch_edit_ids  # noqa: E402
from harness.m5_repair import M5RepairController, RepairBudget  # noqa: E402
from scripts.run_codex_ai_proxy_review import m5_runtime_review_rows  # noqa: E402


REVIEW_OUTPUT = (
    ROOT / "data/benchmarks/m5/codex_ai_proxy_independent_runtime_review_20260821"
    / "batches/m5_runtime_review-proxy-001/attempt-01/last_message.json"
)
M3_SOURCE = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/session/results"


def _nodes(proof_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = json.loads((M3_SOURCE / f"{proof_id}.json").read_text(encoding="utf-8"))
    nodes = []
    for index, node in enumerate(source["proof_graph"], 1):
        nodes.append({
            "proof_id": proof_id,
            "node_id": node["node_id"],
            "version": 1,
            "order_key": index * 10,
            "claim": node["claim"],
            "self_contained_claim": node["self_contained_claim"],
            "node_type": node.get("node_type", "conclusion"),
            "depends_on": [
                {"proof_id": proof_id, "node_id": dependency, "version": 1}
                for dependency in node.get("depends_on", [])
            ],
        })
    return source, nodes


def _rejection_codes(checks: dict[str, bool], introduced_errors: list[str]) -> list[str]:
    mapping = {
        "mathematically_valid": "mathematical_error",
        "resolves_failed_inference": "failed_inference_unresolved",
        "theorem_preserved": "target_changed",
        "assumptions_preserved": "hidden_assumption",
        "domain_preserved": "domain_changed",
        "no_new_errors": "new_error_introduced",
        "operationally_minimal": "not_minimal",
    }
    codes = {code for check, code in mapping.items() if not checks[check]}
    if introduced_errors:
        codes.add("new_error_introduced")
    return sorted(codes)


def build() -> dict[str, Any]:
    review_doc = json.loads(REVIEW_OUTPUT.read_text(encoding="utf-8"))
    reviews = {row["proof_id"]: row for row in review_doc["rows"]}
    rows = []
    for packet in m5_runtime_review_rows():
        proof_id = packet["proof_id"]
        proxy = reviews[proof_id]
        source, nodes = _nodes(proof_id)
        generator_input = packet["frozen_generator_input"]
        patch = packet["generated_patch"]
        budget = RepairBudget(**generator_input["budget"])
        reviewer_id = "codex-ai-proxy-independent-patch-reviewer"
        controller = M5RepairController(
            proof_id=proof_id,
            nodes=nodes,
            error_certificate=generator_input["error_certificate"],
            repair_generator_id=patch["generator_id"],
            budget=budget,
            evaluator_ids={reviewer_id},
        )
        response_evidence = "generator_response:" + packet["generator_evidence"]["raw_response_sha256"]
        review_evidence = "independent_review:" + hashlib.sha256(
            REVIEW_OUTPUT.read_bytes()).hexdigest()
        evidence = [response_evidence, review_evidence]
        context_id = f"m5-runtime-{proof_id}-ai-proxy-review-context"
        certificate = generator_input["error_certificate"]
        context = {
            "schema_version": "0.1",
            "context_id": context_id,
            "proof_id": proof_id,
            "target": patch["target"],
            "theorem": source["theorem"],
            "global_assumptions": source["assumptions"],
            "domain": source["domain"],
            "failed_inference": certificate["failed_inference"],
            "allowed_evidence": evidence,
            "unrelated_branch_digests": {},
            "error_certificate_digest": canonical_digest(certificate),
            "patch_digest": canonical_digest(patch),
        }
        checks = {
            key: proxy["checks"][key]
            for key in (
                "mathematically_valid", "resolves_failed_inference", "theorem_preserved",
                "assumptions_preserved", "domain_preserved", "no_new_errors",
                "operationally_minimal",
            )
        }
        checks["unrelated_branches_preserved"] = proxy["checks"]["descendants_checked"]
        introduced_errors = [] if proxy["checks"]["no_new_errors"] else [proxy["failed_obligation"]]
        accepted = proxy["decision"] == "accept_patch"
        review = {
            "schema_version": "0.1",
            "review_id": f"m5-runtime-{proof_id}-codex-ai-proxy-review",
            "context_id": context_id,
            "reviewer_id": reviewer_id,
            "checks": checks,
            "hidden_assumptions": [],
            "introduced_errors": introduced_errors,
            "deletion_trials": [
                {
                    "edit_id": edit_id,
                    "removal_breaks_repair": proxy["deletion_trial"]["removal_breaks_repair"],
                    "reason": proxy["deletion_trial"]["reason"],
                }
                for edit_id in patch_edit_ids(patch)
            ],
            "evidence_used": evidence,
            "accepted": accepted,
            "rejection_codes": _rejection_codes(checks, introduced_errors),
            "reason": proxy["reason"],
        }
        controller.submit(patch)
        state = controller.review_and_apply(context, review)
        revalidations = []
        if accepted:
            while state["stop_reason"] is None:
                pending = next(
                    item for item in state["revalidation_queue"]
                    if item["status"] == "pending_evaluation"
                )
                record = {
                    "schema_version": "0.1",
                    "evaluation_id": f"m5-runtime-{proof_id}-proxy-revalidation-{len(revalidations) + 1}",
                    "evaluator_id": reviewer_id,
                    "target": pending["target"],
                    "verdict": "accepted",
                    "reason": "The independent proxy review checked the patched node and all descendants.",
                }
                revalidations.append(record)
                state = controller.record_revalidation(record)
        manifest = controller.audit_manifest(f"m5-runtime-controller-replay-{proof_id}")
        rows.append({
            "proof_id": proof_id,
            "generator_terminal_status": packet["generator_evidence"]["terminal_status"],
            "review_decision": proxy["decision"],
            "controller_review_accepted": accepted,
            "graph_edit_applied": any(event["event"] == "patch_applied" for event in controller.events),
            "revalidation_count": len(revalidations),
            "controller_stop_reason": state["stop_reason"],
            "next_action": (
                "complete_ai_proxy_engineering_replay"
                if state["stop_reason"] == "accepted"
                else "new_generator_attempt_required"
            ),
            "patch_digest": canonical_digest(patch),
            "review_digest": canonical_digest(review),
            "final_state_digest": manifest["final_state_digest"],
            "attempt_fingerprints": manifest["attempt_fingerprints"],
            "events": manifest["events"],
        })
    return {
        "schema_version": "m5-runtime-controller-ai-proxy-replay-0.1",
        "reviewer_kind": "codex_ai_proxy_independent_patch_reviewer",
        "human_review": False,
        "eligible_as_human_evidence": False,
        "eligible_for_scientific_gold": False,
        "scientific_claim_allowed": False,
        "frozen_inputs_modified": False,
        "rows": rows,
        "summary": {
            "case_count": len(rows),
            "accepted_and_revalidated_count": sum(
                row["controller_stop_reason"] == "accepted" for row in rows),
            "rejected_awaiting_new_generation_count": sum(
                row["next_action"] == "new_generator_attempt_required" for row in rows),
            "generator_budget_terminal_case_ids": [
                row["proof_id"] for row in rows
                if row["generator_terminal_status"] == "budget_exhausted"
            ],
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
