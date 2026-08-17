"""Fail-closed M8 publication and reproducibility Controller checks."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


M8_CONTROLLER_VERSION = "m8-controller-0.1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TERMINAL_STATUSES = {
    "succeeded", "api_failure", "timeout", "budget_exceeded",
    "schema_failure", "tool_failure", "retry_exhausted",
}
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
}


class M8ControllerError(ValueError):
    """Raised when publication evidence is incomplete or inconsistent."""


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def freeze_files(root: Path, paths: Iterable[str]) -> dict[str, str]:
    base = root.resolve()
    requested = list(paths)
    if not requested or any(not isinstance(path, str) or not path for path in requested):
        raise M8ControllerError("release files require nonempty repository-relative paths")
    result = {}
    for path in sorted(set(requested)):
        relative = Path(path)
        if (relative.is_absolute() or relative.drive or relative == Path(".")
                or ".." in relative.parts or relative.as_posix() != path):
            raise M8ControllerError("release file path is not normalized")
        target = (base / relative).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise M8ControllerError("release file escapes repository") from exc
        if not target.is_file():
            raise M8ControllerError(f"release file does not exist: {path}")
        result[path] = hashlib.sha256(target.read_bytes()).hexdigest()
    return result


def scan_release_text(root: Path, paths: Iterable[str]) -> list[dict[str, str]]:
    """Conservative byte scan; a clean result is not a full privacy audit."""
    normalized = freeze_files(root, paths)
    findings = []
    for path in normalized:
        target = root.resolve() / path
        try:
            text = target.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"path": path, "kind": kind})
    return findings


def rebuild_publication_table(ledger: Iterable[Mapping[str, Any]],
                              expected_assignments: Iterable[Mapping[str, str]]) -> list[dict[str, Any]]:
    """Aggregate a paper table from the exact frozen assignment/terminal-run set."""
    assignment_fields = {"case_id", "experiment_id"}
    run_fields = assignment_fields | {
        "run_id", "status", "tokens", "model_calls", "wall_ms", "cost_microunits",
        "raw_output_sha256", "scoring_input_sha256",
    }
    expected = [dict(row) for row in expected_assignments]
    runs = [dict(row) for row in ledger]
    if not expected or any(set(row) != assignment_fields for row in expected):
        raise M8ControllerError("expected assignments have an invalid shape")
    expected_keys = [(row["case_id"], row["experiment_id"]) for row in expected]
    if any(not all(isinstance(value, str) and value for value in key) for key in expected_keys):
        raise M8ControllerError("assignment identities must be nonempty strings")
    if len(expected_keys) != len(set(expected_keys)):
        raise M8ControllerError("expected assignments must be unique")
    if any(set(row) != run_fields for row in runs):
        raise M8ControllerError("terminal ledger rows have an invalid shape")
    run_keys = [(row["case_id"], row["experiment_id"]) for row in runs]
    if len(run_keys) != len(expected_keys) or set(run_keys) != set(expected_keys):
        raise M8ControllerError("terminal ledger must equal the exact assignment set")
    if len(run_keys) != len(set(run_keys)):
        raise M8ControllerError("terminal runs must be unique")
    run_ids = [row["run_id"] for row in runs]
    if any(not isinstance(run_id, str) or not run_id for run_id in run_ids):
        raise M8ControllerError("run_id must be a nonempty string")
    if len(run_ids) != len(set(run_ids)):
        raise M8ControllerError("run_id must be globally unique")
    if any(not isinstance(row[field], str) or not SHA256_RE.fullmatch(row[field]) for row in runs
           for field in ("raw_output_sha256", "scoring_input_sha256")):
        raise M8ControllerError("terminal runs require raw-output and scoring-input SHA-256")
    numeric = ("tokens", "model_calls", "wall_ms", "cost_microunits")
    if any(not isinstance(row[key], int) or isinstance(row[key], bool) or row[key] < 0
           for row in runs for key in numeric):
        raise M8ControllerError("terminal usage values must be nonnegative integers")
    if any(not isinstance(row["status"], str) or row["status"] not in TERMINAL_STATUSES
           for row in runs):
        raise M8ControllerError("terminal status is unknown")
    table = []
    for experiment_id in sorted({row["experiment_id"] for row in expected}):
        subset = [row for row in runs if row["experiment_id"] == experiment_id]
        successes = sum(row["status"] == "succeeded" for row in subset)
        table.append({"experiment_id": experiment_id, "sample_count": len(subset),
                      "success_count": successes, "failure_count": len(subset) - successes,
                      "tokens": sum(row["tokens"] for row in subset),
                      "model_calls": sum(row["model_calls"] for row in subset),
                      "wall_ms": sum(row["wall_ms"] for row in subset),
                      "cost_microunits": sum(row["cost_microunits"] for row in subset)})
    return table


def build_candidate(*, root: Path, artifacts: Iterable[str], upstream_sha256: Mapping[str, str],
                    gate_evidence_sha256: Mapping[str, Mapping[str, str]],
                    publication_ledger: Iterable[Mapping[str, Any]] | None = None,
                    expected_assignments: Iterable[Mapping[str, str]] | None = None,
                    formal_m7_complete: bool = False, external_reviews_complete: bool = False,
                    clean_reproduction_complete: bool = False,
                    license_privacy_complete: bool = False) -> dict[str, Any]:
    gates = {
        "formal_m7_complete": formal_m7_complete,
        "paper_outputs_rebuilt": publication_ledger is not None and expected_assignments is not None,
        "external_reviews_complete": external_reviews_complete,
        "clean_reproduction_complete": clean_reproduction_complete,
        "license_privacy_complete": license_privacy_complete,
        # v0.1 can bind bytes but cannot authenticate reviewers, reproduce an
        # external environment, or establish license/privacy clearance.  Keep
        # the release gate closed until a later protocol supplies and verifies
        # trusted attestations instead of accepting caller-provided booleans.
        "trusted_attestations_verified": False,
    }
    if any(not isinstance(value, bool) for value in gates.values()):
        raise M8ControllerError("M8 gates must be boolean")
    if set(gate_evidence_sha256) != set(gates):
        raise M8ControllerError("gate evidence must cover the exact M8 gate set")
    evidence = {}
    for gate, passed in gates.items():
        bindings = gate_evidence_sha256[gate]
        if not isinstance(bindings, Mapping):
            raise M8ControllerError("gate evidence must map paths to SHA-256")
        evidence[gate] = dict(sorted(bindings.items()))
        if passed and not evidence[gate]:
            raise M8ControllerError("a passed M8 gate requires bound evidence")
        if not passed and evidence[gate]:
            raise M8ControllerError("a failed M8 gate cannot claim completed evidence")
        if evidence[gate]:
            if any(not isinstance(path, str) or not SHA256_RE.fullmatch(value)
                   for path, value in evidence[gate].items()):
                raise M8ControllerError("gate evidence requires lowercase SHA-256")
            if freeze_files(root, evidence[gate]) != evidence[gate]:
                raise M8ControllerError("gate evidence bytes changed")
    frozen = freeze_files(root, artifacts)
    if not upstream_sha256 or any(not isinstance(path, str) or not SHA256_RE.fullmatch(value)
                                  for path, value in upstream_sha256.items()):
        raise M8ControllerError("upstream bindings require lowercase SHA-256")
    if freeze_files(root, upstream_sha256) != dict(sorted(upstream_sha256.items())):
        raise M8ControllerError("upstream bytes changed")
    if (publication_ledger is None) != (expected_assignments is None):
        raise M8ControllerError("publication ledger and assignments must be supplied together")
    ledger_rows = ([dict(row) for row in publication_ledger]
                   if publication_ledger is not None else [])
    assignment_rows = ([dict(row) for row in expected_assignments]
                       if expected_assignments is not None else [])
    table = (rebuild_publication_table(ledger_rows, assignment_rows)
             if publication_ledger is not None and expected_assignments is not None else [])
    findings = scan_release_text(root, frozen)
    # v0.1 is an engineering-audit candidate, not a release authorizer.
    # A later version may compute this from cryptographically or otherwise
    # trusted attestations; this version remains closed by construction.
    release_allowed = False
    body = {"schema_version": M8_CONTROLLER_VERSION,
            "status": "engineering_candidate_blocked",
            "gates": gates, "gate_evidence_sha256": evidence, "release_allowed": release_allowed,
            "artifact_sha256": frozen, "upstream_sha256": dict(sorted(upstream_sha256.items())),
            "expected_assignments": assignment_rows,
            "terminal_ledger": ledger_rows,
            "publication_table": table, "publication_table_sha256": _digest(table),
            "automated_secret_findings": findings,
            "scan_limitation": "pattern scan does not prove privacy or license clearance"}
    return {**body, "candidate_id": f"m8-controller-{_digest(body)[:16]}"}


def validate_candidate(candidate: Mapping[str, Any], *, root: Path) -> dict[str, Any]:
    row = dict(candidate)
    expected = {"schema_version", "status", "gates", "gate_evidence_sha256", "release_allowed", "artifact_sha256",
                "upstream_sha256", "expected_assignments", "terminal_ledger",
                "publication_table", "publication_table_sha256",
                "automated_secret_findings", "scan_limitation", "candidate_id"}
    if set(row) != expected or row.get("schema_version") != M8_CONTROLLER_VERSION:
        raise M8ControllerError("invalid M8 Controller candidate shape")
    rebuilt = build_candidate(root=root, artifacts=row["artifact_sha256"],
                              upstream_sha256=row["upstream_sha256"],
                              gate_evidence_sha256=row["gate_evidence_sha256"],
                              publication_ledger=(row["terminal_ledger"]
                                                  if row["gates"]["paper_outputs_rebuilt"] else None),
                              expected_assignments=(row["expected_assignments"]
                                                    if row["gates"]["paper_outputs_rebuilt"] else None),
                              formal_m7_complete=row["gates"]["formal_m7_complete"],
                              external_reviews_complete=row["gates"]["external_reviews_complete"],
                              clean_reproduction_complete=row["gates"]["clean_reproduction_complete"],
                              license_privacy_complete=row["gates"]["license_privacy_complete"])
    if rebuilt != row:
        raise M8ControllerError("M8 Controller candidate was mutated or is stale")
    return row
