#!/usr/bin/env python3
"""Run the five-method M6 Controller-connected engineering acceptance batch.

This runner starts with an independent diagnosis call, then executes generated
patches, independent reviews, Controller application, descendant handling and
node revalidation. It is AI-assisted engineering evidence, never formal Gold.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.m5_sequential_repair import M5SequentialRepairController  # noqa: E402
from harness.m6_experiments import METHOD_SPECS  # noqa: E402
from scripts.build_m5_runtime_controller_replay import _nodes  # noqa: E402
from scripts.run_live_repair_pilot import Calls, PROMPTS, read, run_case, write_once  # noqa: E402


METHODS = (
    "no_structured_certificate",
    "no_counterexample_protocol",
    "no_descendant_invalidation",
    "single_round_repair",
    "full_system",
)
CASES = ("m2-011", "m2-018", "m2-034")


def _ref(node):
    return {key: node[key] for key in ("proof_id", "node_id", "version")}


class NoDescendantInvalidationController(M5SequentialRepairController):
    """Intentional M6 ablation: retain and do not revalidate descendants."""

    def _apply(self, patch):
        target = deepcopy(patch["target"])
        descendants = self._descendants(target) if patch["operation"] != "mark_irreparable" else []
        stale_before = len(self._stale)
        queue_before = len(self._revalidation_queue)
        event_before = len(self._events)
        super()._apply(patch)
        if not descendants:
            return

        newly_stale = self._stale[stale_before:]
        del self._stale[stale_before:]
        descendant_keys = {
            (item["proof_id"], item["node_id"], item["version"])
            for item in newly_stale
        }
        retained_queue = self._revalidation_queue[:queue_before]
        retained_queue.extend(
            item for item in self._revalidation_queue[queue_before:]
            if (item["target"]["proof_id"], item["target"]["node_id"],
                item["target"]["version"]) not in descendant_keys
        )
        self._revalidation_queue = retained_queue

        current_target = self._find_current(target["node_id"])
        replacement_refs = (
            [_ref(current_target)] if current_target is not None
            else deepcopy(self._dependency_redirects.get(
                (target["proof_id"], target["node_id"], target["version"]), []))
        )
        for node in newly_stale:
            node.pop("stale_reason", None)
            rewritten = []
            for dependency in node.get("depends_on", []):
                if dependency == target:
                    rewritten.extend(deepcopy(replacement_refs))
                else:
                    rewritten.append(deepcopy(dependency))
            node["depends_on"] = rewritten
            self._nodes.append(node)

        del self._events[event_before:]
        self._events.append({
            "event": "patch_applied_without_descendant_invalidation",
            "operation": patch["operation"],
            "patch_id": patch["patch_id"],
            "descendants_reused_without_revalidation": len(newly_stale),
            "ablation": True,
        })


def _diagnosis_prompt(method_id: str) -> str:
    prompt = PROMPTS["diagnose"]
    if method_id == "no_counterexample_protocol":
        return prompt + " This ablation disables counterexample search: set counterexample to null and decide from direct obligation checking."
    return prompt + " Actively search for a concrete counterexample when the claim may be false."


def _certificate(case_id: str, nodes: list[dict], diagnosis: dict) -> dict:
    if diagnosis["verdict"] != "invalid":
        raise ValueError("only an invalid diagnosis can initialize repair")
    target = diagnosis["first_error_target"]
    if target is None or target not in [_ref(node) for node in nodes]:
        raise ValueError("diagnosis target is not an exact current node reference")
    allowed = ["insert_before", "replace", "delete"]
    return {
        "certificate_id": f"{case_id}-m6-live-diagnosis",
        "target": target,
        "failed_inference": diagnosis["failed_inference"],
        "repair_constraints": {
            "allowed_operations": allowed,
            "max_new_nodes": 2,
            "preserve_theorem": True,
            "preserve_assumptions": True,
        },
    }


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        stream.write((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))


def run_assignment(*, case_id: str, method_id: str, output: Path, model: str,
                   codex_command: str, execute: bool, max_calls: int,
                   max_tokens: int) -> dict:
    source, nodes = _nodes(case_id)
    calls = Calls(output, model, codex_command, execute,
                  max_calls=max_calls, max_tokens=max_tokens)
    problem = {key: source[key] for key in ("theorem", "assumptions", "domain")}
    diagnosis_input = {
        "problem": problem,
        "proof_id": case_id,
        "ordered_nodes": nodes,
        "method_id": method_id,
        "gold_visible": False,
    }
    diagnosis = calls.call("diagnose", diagnosis_input,
                           prompt_override=_diagnosis_prompt(method_id))
    write_once(output / "diagnosis.json", diagnosis)
    if diagnosis["verdict"] != "invalid":
        result = {
            "status": f'diagnosis_{diagnosis["verdict"]}',
            "method_id": method_id,
            "case_id": case_id,
            "calls": calls.count,
            "reported_tokens": calls.tokens,
            "controller_started": False,
            "human_verified": False,
            "scientific_claim_allowed": False,
        }
        write_once(output / "result.json", result)
        return result

    certificate = _certificate(case_id, nodes, diagnosis)
    spec = METHOD_SPECS[method_id]
    controller_class = (NoDescendantInvalidationController
                        if method_id == "no_descendant_invalidation"
                        else M5SequentialRepairController)
    run_case(case_id, output, calls, spec.max_patch_rounds,
             certificate_override=certificate, method_id=method_id,
             controller_class=controller_class, diagnosis_record=diagnosis)
    result = read(output / "result.json")
    result["case_id"] = case_id
    result["controller_started"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--max-calls", type=int, default=12)
    parser.add_argument("--max-tokens", type=int, default=60000)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.max_calls < 1 or args.max_tokens < 1:
        parser.error("budgets must be positive")

    assignments = [{"method_id": method, "case_id": case}
                   for method in METHODS for case in CASES]
    manifest = {
        "schema_version": "m6-end-to-end-engineering-0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "three_case_five_method_controller_connected_engineering_acceptance",
        "methods": list(METHODS),
        "cases": list(CASES),
        "assignments": assignments,
        "model": args.model,
        "credential_mode": "saved_codex_cli_auth",
        "per_assignment_budget": {"max_calls": args.max_calls, "max_tokens": args.max_tokens},
        "independent_session_per_assignment": True,
        "checkpoint_interval": 10,
        "human_review": False,
        "scientific_claim_allowed": False,
        "formal_budget_modified": False,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    write_once(args.output_dir / "run_manifest.json", manifest)
    ledger = args.output_dir / "ledger.jsonl"
    completed = set()
    if ledger.exists():
        completed = {(row["method_id"], row["case_id"])
                     for row in map(json.loads, ledger.read_text(encoding="utf-8").splitlines())}

    for index, assignment in enumerate(assignments, 1):
        key = (assignment["method_id"], assignment["case_id"])
        if key in completed:
            continue
        folder = args.output_dir / "assignments" / assignment["method_id"] / assignment["case_id"]
        try:
            result = run_assignment(output=folder, model=args.model,
                                    codex_command=args.codex_command, execute=args.execute,
                                    max_calls=args.max_calls, max_tokens=args.max_tokens, **assignment)
            row = {**assignment, "terminal": True, "result_status": result["status"],
                   "calls": result["calls"], "reported_tokens": result["reported_tokens"],
                   "failure_type": None}
        except Exception as exc:
            interruption = read(folder / "interruption.json") if (folder / "interruption.json").exists() else {}
            row = {**assignment, "terminal": True, "result_status": "failed",
                   "calls": interruption.get("calls", 0),
                   "reported_tokens": interruption.get("reported_tokens", 0),
                   "failure_type": type(exc).__name__, "error": str(exc)}
        _append_jsonl(ledger, row)
        if index % 10 == 0:
            write_once(args.output_dir / f"checkpoint-{index:03d}.json",
                       {"completed_assignments": index, "last_assignment": assignment})

    rows = list(map(json.loads, ledger.read_text(encoding="utf-8").splitlines()))
    summary = {
        "schema_version": "m6-end-to-end-engineering-summary-0.1",
        "assignment_count": len(assignments),
        "terminal_count": len(rows),
        "status_counts": {status: sum(row["result_status"] == status for row in rows)
                          for status in sorted({row["result_status"] for row in rows})},
        "total_calls": sum(row["calls"] for row in rows),
        "total_reported_tokens": sum(row["reported_tokens"] for row in rows),
        "failures_retained": sum(row["failure_type"] is not None for row in rows),
        "human_review": False,
        "scientific_claim_allowed": False,
    }
    write_once(args.output_dir / "run_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if len(rows) == len(assignments) else 1


if __name__ == "__main__":
    raise SystemExit(main())
