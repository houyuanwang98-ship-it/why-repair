"""Run reproducible structural checks for manual-validation Step 4.

This audit deliberately does not claim semantic equivalence or mathematical
correctness.  Those remain the small human-review surface in the workpacks.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "manual_validation" / "step04_machine_report.json"
SOURCES = (
    ("M2 工程 Pilot", "data/benchmarks/m2/source/pilot_50.jsonl"),
    ("M2 B50", "data/benchmarks/m2/source/pilot_B50.jsonl"),
    ("OPC-250 v0.2", "data/benchmarks/m7/opc_250_v0_2/candidate.jsonl"),
    ("ProofNet-250 v0.1", "data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def case_id(row: dict[str, Any]) -> str:
    return str(row.get("case_id") or row.get("proof_id") or row.get("id") or "")


def proof_parts(row: dict[str, Any]) -> list[dict[str, str]]:
    raw = row.get("proof_steps") or row.get("flawed_proof_steps")
    if isinstance(raw, list):
        parts = []
        for index, value in enumerate(raw, 1):
            if isinstance(value, dict):
                parts.append({"node_id": str(value.get("node_id") or value.get("id") or index), "text": str(value.get("text") or value.get("content") or "")})
            else:
                parts.append({"node_id": str(index), "text": str(value)})
        return parts
    proof = row.get("proof")
    return [{"node_id": "document", "text": str(proof)}] if proof not in (None, "") else []


def load_opc_annotations() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = ROOT / "data/benchmarks/m7/opc_250_v0_2/node_annotations.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(row["case_id"]): row for row in payload["rows"]}, {
        "path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path),
        "declared_rows": payload.get("row_count"), "status": payload.get("status"),
    }


def regression_tests() -> dict[str, Any]:
    modules = [
        "tests.test_graph_and_subquestions",
        "tests.test_dual_agent_controller",
        "tests.test_session_cache_and_io",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "tests"), str(ROOT)))
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "unittest", *modules],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return {
        "command": f"{Path(sys.executable).name} -X utf8 -m unittest {' '.join(modules)}",
        "modules": modules,
        "return_code": completed.returncode,
        "status": "pass" if completed.returncode == 0 else "fail",
        "output_tail": "\n".join(output.splitlines()[-8:]),
    }


def audit() -> dict[str, Any]:
    annotations, annotation_source = load_opc_annotations()
    findings: list[dict[str, Any]] = []
    source_records = []
    seen: set[str] = set()
    duplicate_ids: list[str] = []
    for group, relative in SOURCES:
        path = ROOT / relative
        group_rows = rows(path)
        source_records.append({"group": group, "path": relative, "sha256": sha256(path), "rows": len(group_rows)})
        for row in group_rows:
            cid = case_id(row)
            if cid in seen:
                duplicate_ids.append(cid)
            seen.add(cid)
            parts = proof_parts(row)
            node_ids = [part["node_id"] for part in parts]
            issues = []
            if not cid:
                issues.append("missing_case_id")
            if not (row.get("problem") or row.get("theorem") or row.get("goal")):
                issues.append("missing_theorem")
            if not parts:
                issues.append("missing_proof")
            if any(not part["text"].strip() for part in parts):
                issues.append("empty_proof_part")
            if len(node_ids) != len(set(node_ids)):
                issues.append("duplicate_node_id")

            annotation = annotations.get(cid)
            annotation_issues: list[str] = []
            annotation_nodes = 0
            if annotation is not None:
                proof_text = str(row.get("proof") or "")
                nodes = annotation.get("proof_nodes") or []
                annotation_nodes = len(nodes)
                ids = [str(node.get("node_id")) for node in nodes]
                if len(ids) != len(set(ids)):
                    annotation_issues.append("annotation_duplicate_node_id")
                previous_end = -1
                for node in nodes:
                    start, end = node.get("start_char"), node.get("end_char")
                    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > len(proof_text):
                        annotation_issues.append("annotation_invalid_span")
                        continue
                    if start < previous_end:
                        annotation_issues.append("annotation_overlapping_or_unsorted_span")
                    if proof_text[start:end] != node.get("text"):
                        annotation_issues.append("annotation_text_span_mismatch")
                    previous_end = end
                if not nodes:
                    annotation_issues.append("annotation_missing_nodes")
            issues.extend(sorted(set(annotation_issues)))
            findings.append({
                "case_id": cid, "group": group, "source_path": relative,
                "source_parts": len(parts), "annotation_nodes": annotation_nodes,
                "annotation_available": annotation is not None,
                "structural_status": "pass" if not issues else "flagged",
                "issues": sorted(set(issues)),
                "semantic_status": "human_review_required",
            })

    issue_counts = Counter(issue for item in findings for issue in item["issues"])
    status_counts = Counter(item["structural_status"] for item in findings)
    tests = regression_tests()
    return {
        "schema_version": "manual-validation-step4-machine-report-0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "structural_only_no_semantic_or_mathematical_claim",
        "sources": source_records,
        "annotation_source": annotation_source,
        "regression_tests": tests,
        "summary": {
            "cases": len(findings), "unique_case_ids": len(seen),
            "duplicate_case_ids": sorted(set(duplicate_ids)),
            "structural_status_counts": dict(sorted(status_counts.items())),
            "issue_counts": dict(sorted(issue_counts.items())),
            "cases_with_node_annotations": sum(item["annotation_available"] for item in findings),
            "cases_without_node_annotations": sum(not item["annotation_available"] for item in findings),
        },
        "machine_checks": [
            "JSONL parsing and source digests", "case-id uniqueness",
            "theorem/proof presence", "proof-part node-id uniqueness and non-empty text",
            "available annotation node-id uniqueness", "available annotation span bounds/order/text round-trip",
        ],
        "not_machine_decidable": [
            "node semantic minimality and completeness", "self-contained rewrite equivalence",
            "true necessary direct dependencies", "mathematical correctness and natural-language accuracy",
        ],
        "cases": findings,
    }


def main() -> None:
    report = audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    print(json.dumps(report["regression_tests"], ensure_ascii=False, sort_keys=True))
    print(OUT.relative_to(ROOT).as_posix())
    if report["regression_tests"]["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
