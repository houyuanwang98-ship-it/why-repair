"""Validate the frozen 600-case Experiment 2 package without inventing results."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPECTED = {"M2 B50": 50, "M2 工程 Pilot": 50, "OPC-250 v0.2": 250, "ProofNet-250 v0.1": 250}
METHODS = {"no_agent", "single_agent", "single_agent_self_refine", "dual_agent", "dual_agent_controller"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    inputs = [json.loads(x) for x in (HERE / "inputs.jsonl").read_text(encoding="utf-8").splitlines()]
    audits = json.loads((HERE / "case_audit.json").read_text(encoding="utf-8"))
    assignments = json.loads((HERE / "assignments.json").read_text(encoding="utf-8"))
    progress = json.loads((HERE / "PROGRESS.json").read_text(encoding="utf-8"))
    manifest = json.loads((HERE / "source_manifest.json").read_text(encoding="utf-8"))
    ids = [x["case_id"] for x in inputs]
    assert len(ids) == len(set(ids)) == 600
    assert len(audits) == 600 and {x["case_id"] for x in audits} == set(ids)
    assert Counter(x["dataset"] for x in audits) == Counter(EXPECTED)
    assert len(assignments) == 3000
    assert {(x["case_id"], x["method"]) for x in assignments} == {(case_id, method) for case_id in ids for method in METHODS}
    assert progress["total_cases"] == 600 and progress["total_judgments_planned"] == 3000
    for relative, expected_digest in manifest.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected_digest, f"Source digest mismatch: {relative}"
    print(json.dumps({"status": "ok", "cases": 600, "assignments": 3000,
                      "judged_cases": progress["judgment_completed_cases"],
                      "remaining_cases": progress["judgment_remaining_cases"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
