#!/usr/bin/env python3
"""Reconstruct frozen pilot results and prepare anonymous human review materials."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness.workflow_v2.reporting import make_report

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--judge", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    summary = make_report(a.source, a.judge, a.output)
    print(json.dumps({"totals": summary["totals"], "failures": summary["failure_categories"],
                     "disputes": len(summary["disputes"]), "human_verified": False}, indent=2))
