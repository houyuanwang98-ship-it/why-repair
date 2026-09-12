#!/usr/bin/env python3
"""Prepare/preflight by default; model execution is an explicit separate action."""
import argparse
import fcntl
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.workflow_v2.experiment import prepare, preflight, execute_assignments, score_assignments, aggregate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "preflight", "runtime", "judge", "aggregate"))
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--execute", action="store_true", help="Opt in to real model calls, only for runtime/judge")
    p.add_argument("--case-ids", nargs="+", help="Development case IDs; prepare only")
    p.add_argument("--selection-note", help="Selection rationale frozen in manifest; prepare only")
    a = p.parse_args()
    if (a.case_ids or a.selection_note) and a.action != "prepare":
        p.error("selection options apply only to prepare")
    if a.action in {"runtime", "judge"} and not a.execute:
        p.error("Stopped before experiment: runtime/judge requires --execute")
    if a.execute and a.action not in {"runtime", "judge"}:
        p.error("--execute only applies to runtime/judge")
    a.bundle.mkdir(parents=True, exist_ok=True)
    with (a.bundle / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if a.action == "prepare":
            m = prepare(a.bundle, case_ids=a.case_ids, selection_note=a.selection_note)
            result = {"status": m["status"], "corpus_cases": m["corpus_cases"],
                      "pilot_cases": m["pilot_cases"], "assignments": m["assignment_count"], "new_model_calls": 0}
        elif a.action == "preflight":
            result = preflight(a.bundle)
        elif a.action == "runtime":
            execute_assignments(a.bundle, execute=True)
            result = {"runtime": "complete", "judge": "not_started_by_this_command"}
        elif a.action == "judge":
            score_assignments(a.bundle, execute=True)
            result = aggregate(a.bundle)
        else:
            result = aggregate(a.bundle)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
