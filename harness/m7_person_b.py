"""M7 Person B benchmark and experiment-integrity fixture machinery.

This module deliberately does not run models or certify mathematical Gold.  It
mechanises the engineering checks assigned to Person B while the M5/M6 gates
remain closed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from harness.m6_experiments import (
    METHOD_IDS, M6ExperimentError, validate_experiment_config, validate_experiment_suite,
)
from harness.execution_release import release_allows


M7_PERSON_B_VERSION = "m7-person-b-0.1"
SPLITS = {"train", "development", "test"}
LICENSE_STATUSES = {"verified_redistributable", "permission_documented", "restricted_excluded"}
TERMINAL_STATUSES = {"succeeded", "api_failure", "timeout", "budget_exceeded", "schema_failure", "tool_failure", "retry_exhausted"}
FINDING_SEVERITIES = {"critical", "major", "minor"}
FINDING_STATUSES = {"open", "resolved", "accepted_risk"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class M7PersonBError(ValueError):
    """Raised when an M7 engineering invariant is violated."""


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE))


def validate_candidate_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate provenance/schema and report distribution without judging Gold."""
    rows = [dict(row) for row in records]
    if not 200 <= len(rows) <= 500:
        raise M7PersonBError("formal M7 candidate must contain 200-500 records")
    required = {
        "case_id", "source_uri", "source_record_digest", "license_status", "license_evidence",
        "raw_bytes_sha256", "problem", "proof", "language", "domain", "difficulty", "split",
    }
    ids: list[str] = []
    raw_digests: list[str] = []
    for row in rows:
        if set(row) != required:
            raise M7PersonBError("candidate record has an invalid field set")
        if any(not isinstance(row[field], str) or not row[field].strip() for field in required):
            raise M7PersonBError("candidate string fields must be nonempty")
        if row["license_status"] not in LICENSE_STATUSES:
            raise M7PersonBError("unknown license status")
        if row["license_status"] == "restricted_excluded":
            raise M7PersonBError("restricted source cannot enter the formal candidate")
        if row["split"] not in SPLITS:
            raise M7PersonBError("unknown split")
        for field in ("source_record_digest", "raw_bytes_sha256"):
            if not SHA256_RE.fullmatch(row[field]):
                raise M7PersonBError(f"{field} must be a lowercase SHA-256")
        ids.append(row["case_id"])
        raw_digests.append(row["raw_bytes_sha256"])
    if len(set(ids)) != len(ids):
        raise M7PersonBError("case_id values must be unique")
    if len(set(raw_digests)) != len(raw_digests):
        raise M7PersonBError("exact duplicate raw records are forbidden")
    return {
        "record_count": len(rows),
        "split_counts": dict(sorted(Counter(r["split"] for r in rows).items())),
        "domain_counts": dict(sorted(Counter(r["domain"] for r in rows).items())),
        "language_counts": dict(sorted(Counter(r["language"] for r in rows).items())),
        "difficulty_counts": dict(sorted(Counter(r["difficulty"] for r in rows).items())),
        "candidate_digest": canonical_digest(rows),
    }


def audit_near_duplicates(records: Iterable[Mapping[str, Any]], *, threshold: float = 0.85) -> list[dict[str, Any]]:
    """Return all token-Jaccard pairs at/above a frozen threshold, including split leaks."""
    if not 0 < threshold <= 1:
        raise M7PersonBError("near-duplicate threshold must be within (0, 1]")
    rows = [dict(row) for row in records]
    if any(not isinstance(r.get("case_id"), str) or not r["case_id"].strip() for r in rows):
        raise M7PersonBError("near-duplicate audit requires nonempty case_id values")
    if len({r["case_id"] for r in rows}) != len(rows):
        raise M7PersonBError("near-duplicate audit requires unique case_id values")
    if any(r.get("split") not in SPLITS for r in rows):
        raise M7PersonBError("near-duplicate audit requires a valid split")
    if any(not isinstance(r.get(field), str) or not r[field].strip()
           for r in rows for field in ("problem", "proof")):
        raise M7PersonBError("near-duplicate audit requires nonempty problem and proof text")
    findings = []
    token_sets = [_tokens(f"{r.get('problem', '')} {r.get('proof', '')}") for r in rows]
    for i, left in enumerate(rows):
        if not token_sets[i]:
            raise M7PersonBError("near-duplicate text cannot be empty")
        for j in range(i + 1, len(rows)):
            union = token_sets[i] | token_sets[j]
            score = len(token_sets[i] & token_sets[j]) / len(union)
            if score >= threshold:
                findings.append({
                    "left_case_id": left["case_id"], "right_case_id": rows[j]["case_id"],
                    "similarity": score, "cross_split": left.get("split") != rows[j].get("split"),
                })
    return findings


def assert_no_unresolved_critical(findings: Iterable[Mapping[str, Any]]) -> None:
    for finding in findings:
        if set(finding) != {"finding_id", "severity", "status", "evidence_digest"}:
            raise M7PersonBError("finding has an invalid field set")
        if not isinstance(finding["finding_id"], str) or not finding["finding_id"].strip():
            raise M7PersonBError("finding_id must be nonempty")
        if finding["severity"] not in FINDING_SEVERITIES or finding["status"] not in FINDING_STATUSES:
            raise M7PersonBError("finding has an unknown severity or status")
        if not isinstance(finding["evidence_digest"], str) or not SHA256_RE.fullmatch(finding["evidence_digest"]):
            raise M7PersonBError("finding evidence_digest must be a lowercase SHA-256")
        if finding.get("severity") == "critical" and finding.get("status") != "resolved":
            raise M7PersonBError("unresolved critical provenance/dedup/leakage finding")


def build_run_matrix(configs: Iterable[Mapping[str, Any]], case_ids: Iterable[str]) -> list[dict[str, str]]:
    """Build the complete case x method assignment matrix for one frozen config family."""
    materialized = list(configs)
    try:
        validate_experiment_suite(materialized)
        rows = [validate_experiment_config(config) for config in materialized]
    except M6ExperimentError as exc:
        raise M7PersonBError(f"invalid M7 experiment family: {exc}") from exc
    ids = list(case_ids)
    if not ids or any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise M7PersonBError("case_ids must be nonempty and unique")
    return [{"case_id": case_id, "experiment_id": row["experiment_id"], "method_id": row["method"]["method_id"]}
            for case_id in ids for row in rows]


def validate_terminal_ledger(assignments: Iterable[Mapping[str, Any]], ledger: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Require exactly one terminal record for every assignment and retain failures."""
    assignment_rows = [dict(row) for row in assignments]
    assignment_fields = {"case_id", "experiment_id", "method_id"}
    if not assignment_rows or any(set(row) != assignment_fields for row in assignment_rows):
        raise M7PersonBError("assignments are invalid")
    if any(row["method_id"] not in METHOD_IDS for row in assignment_rows):
        raise M7PersonBError("assignments contain an unknown method_id")
    keys = [(row["case_id"], row["experiment_id"]) for row in assignment_rows]
    if any(not isinstance(value, str) or not value for pair in keys for value in pair):
        raise M7PersonBError("assignments are invalid")
    if len(set(keys)) != len(keys):
        raise M7PersonBError("assignments contain duplicate case/config pairs")
    method_to_experiment: dict[str, str] = {}
    experiment_to_method: dict[str, str] = {}
    case_methods: dict[str, set[str]] = {}
    for row in assignment_rows:
        method_id, experiment_id = row["method_id"], row["experiment_id"]
        if method_id in method_to_experiment and method_to_experiment[method_id] != experiment_id:
            raise M7PersonBError("one method_id maps to multiple experiment_id values")
        if experiment_id in experiment_to_method and experiment_to_method[experiment_id] != method_id:
            raise M7PersonBError("one experiment_id maps to multiple method_id values")
        method_to_experiment[method_id] = experiment_id
        experiment_to_method[experiment_id] = method_id
        case_methods.setdefault(row["case_id"], set()).add(method_id)
    if set(method_to_experiment) != set(METHOD_IDS) or any(methods != set(METHOD_IDS) for methods in case_methods.values()):
        raise M7PersonBError("assignments do not contain the complete method family for every case")
    expected = set(keys)
    rows = [dict(row) for row in ledger]
    required = {"case_id", "experiment_id", "run_id", "status", "terminal", "tokens", "model_calls", "wall_ms", "raw_output_sha256"}
    seen = set()
    run_ids = set()
    for row in rows:
        if set(row) != required or row["terminal"] is not True or row["status"] not in TERMINAL_STATUSES:
            raise M7PersonBError("ledger row is not a valid terminal record")
        key = (row["case_id"], row["experiment_id"])
        if key not in expected or key in seen:
            raise M7PersonBError("ledger has an unknown or duplicate assignment")
        if not isinstance(row["run_id"], str) or not row["run_id"] or not SHA256_RE.fullmatch(row["raw_output_sha256"]):
            raise M7PersonBError("ledger identity/digest is invalid")
        if row["run_id"] in run_ids:
            raise M7PersonBError("run_id values must be unique")
        if any(not isinstance(row[f], int) or isinstance(row[f], bool) or row[f] < 0 for f in ("tokens", "model_calls", "wall_ms")):
            raise M7PersonBError("ledger costs must be nonnegative integers")
        seen.add(key)
        run_ids.add(row["run_id"])
    if seen != expected:
        raise M7PersonBError("ledger is incomplete; failed assignments cannot be deleted")
    status_counts = dict(sorted(Counter(row["status"] for row in rows).items()))
    failures = len(rows) - status_counts.get("succeeded", 0)
    return {"assignment_count": len(expected), "failure_count": failures,
            "status_counts": status_counts, "complete": True}


def assert_execution_allowed(m7_gate: Mapping[str, Any], *, fixture_only: bool,
                             user_release: Mapping[str, Any] | None = None) -> None:
    if fixture_only:
        return
    if release_allows(user_release, "m7"):
        return
    if m7_gate.get("m7_entry_allowed") is not True:
        raise M7PersonBError("M7 execution blocked: verified M6 exit does not allow entry")
    raise M7PersonBError("M7 execution blocked: detached-signature and live-manifest verification are not implemented")
