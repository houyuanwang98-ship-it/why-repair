#!/usr/bin/env python3
"""Run fixed experiment and/or validation pools, optionally judging a completed frozen source."""
import argparse
import fcntl
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.workflow_v2.experiment import preflight
from harness.workflow_v2.scheduler import Scheduler
from harness.workflow_v2.judging import prepare_judging


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--experiment-only", action="store_true",
                        help="Start only 24 gpt-5.6-sol servers; freeze every candidate and defer judging")
    mode.add_argument("--judge-only", action="store_true",
                      help="Start only 24 gpt-6-astra/high servers to judge a completed frozen source")
    parser.add_argument("--source-bundle", type=Path, help="Completed generation bundle; required with --judge-only")
    args = parser.parse_args()
    if args.judge_only != bool(args.source_bundle):
        parser.error("--judge-only requires --source-bundle, and only that mode accepts a source")
    args.bundle.mkdir(parents=True, exist_ok=True)
    with (args.bundle / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.judge_only:
            prepare_judging(args.source_bundle, args.bundle)
        checked = preflight(args.bundle)
        if not args.execute:
            print(json.dumps({"preflight": checked, "servers": {"gpt-5.6-sol/xhigh": 0 if args.judge_only else 24,
                "gpt-6-astra/high": 0 if args.experiment_only else 24},
                "new_model_calls": 0, "start_requires": "--execute"}, ensure_ascii=False, indent=2))
            return
        result = Scheduler(args.bundle, mode="experiment_only" if args.experiment_only else
                           "judge_only" if args.judge_only else "pipeline").run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["status"] not in {"completed", "completed_with_failures"}:
            sys.exit(1)


if __name__ == "__main__":
    main()
