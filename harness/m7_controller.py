"""Deterministic, fixture-only M7 Controller governance machinery."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from harness.m6_experiments import M6ExperimentError, validate_experiment_suite
from harness.m7_person_b import M7PersonBError, build_run_matrix, validate_terminal_ledger


M7_CONTROLLER_VERSION = "m7-controller-0.1"
SHA256 = set("0123456789abcdef")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= SHA256


def freeze_artifacts(root: Path, paths: Iterable[str]) -> dict[str, str]:
    base = root.resolve()
    requested = list(paths)
    if not requested or any(not isinstance(item, str) for item in requested):
        raise M7PersonBError("artifacts require nonempty normalized repository-relative paths")
    frozen: dict[str, str] = {}
    for item in sorted(set(requested)):
        candidate = Path(item)
        if (not item or candidate.is_absolute() or candidate.drive or ".." in candidate.parts
                or candidate == Path(".") or candidate.as_posix() != item):
            raise M7PersonBError("artifacts require nonempty normalized repository-relative paths")
        target = (base / candidate).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise M7PersonBError("artifact escapes repository root") from exc
        if not target.is_file():
            raise M7PersonBError(f"artifact is not a file: {item}")
        frozen[item] = hashlib.sha256(target.read_bytes()).hexdigest()
    return frozen


def build_controller_manifest(*, config_families: Mapping[str, Sequence[Mapping[str, Any]]],
                              case_ids: Sequence[str], candidate_digest: str,
                              gold_digest: str, artifacts: Mapping[str, str],
                              person_a_manifest_digest: str, person_b_manifest_digest: str,
                              replay_seed: int, fixture_only: bool = True,
                              m7_entry_allowed: bool = False) -> dict[str, Any]:
    if not isinstance(fixture_only, bool) or not isinstance(m7_entry_allowed, bool):
        raise M7PersonBError("Controller gate fields must be boolean")
    if not fixture_only:
        raise M7PersonBError("formal M7 Controller blocked: live gates and detached signatures are not verified")
    if m7_entry_allowed:
        raise M7PersonBError("fixture Controller must preserve the closed M7 entry gate")
    if not config_families or any(not isinstance(name, str) or not name for name in config_families):
        raise M7PersonBError("config_families must have nonempty names")
    families = {}
    experiment_ids: set[str] = set()
    for name, configs in sorted(config_families.items()):
        rows = [dict(row) for row in configs]
        try:
            validate_experiment_suite(rows)
        except M6ExperimentError as exc:
            raise M7PersonBError(f"invalid M7 config family: {exc}") from exc
        ids = {row["experiment_id"] for row in rows}
        if experiment_ids & ids:
            raise M7PersonBError("experiment_id cannot be reused across model families")
        experiment_ids |= ids
        families[name] = rows
    if not case_ids or any(not isinstance(case, str) or not case for case in case_ids) or len(set(case_ids)) != len(case_ids):
        raise M7PersonBError("case_ids must be nonempty and unique")
    if any(not _sha(value) for value in (candidate_digest, gold_digest,
                                         person_a_manifest_digest, person_b_manifest_digest)):
        raise M7PersonBError("Controller digest fields must be lowercase SHA-256")
    if not artifacts or any(not isinstance(path, str) or not path or not _sha(value)
                            for path, value in artifacts.items()):
        raise M7PersonBError("artifacts must map paths to lowercase SHA-256")
    for path in artifacts:
        candidate = Path(path)
        if (candidate.is_absolute() or candidate.drive or candidate == Path(".")
                or ".." in candidate.parts or candidate.as_posix() != path):
            raise M7PersonBError("artifact keys must be normalized repository-relative paths")
    if not isinstance(replay_seed, int) or isinstance(replay_seed, bool):
        raise M7PersonBError("replay_seed must be an integer")
    body = {
        "schema_version": M7_CONTROLLER_VERSION,
        "status": "fixture_candidate_upstream_gates_blocked",
        "fixture_only": True,
        "m7_entry_allowed": False,
        "case_ids": list(case_ids),
        "case_set_digest": _digest(list(case_ids)),
        "candidate_digest": candidate_digest,
        "gold_digest": gold_digest,
        "config_families": families,
        "artifacts": dict(sorted(artifacts.items())),
        "upstream": {"person_a_manifest_digest": person_a_manifest_digest,
                     "person_b_manifest_digest": person_b_manifest_digest},
        "replay_seed": replay_seed,
    }
    return {**body, "manifest_id": f"m7-controller-{_digest(body)[:16]}"}


def validate_controller_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(manifest)
    expected = {"schema_version", "status", "fixture_only", "m7_entry_allowed", "case_ids",
                "case_set_digest", "candidate_digest", "gold_digest", "config_families",
                "artifacts", "upstream", "replay_seed", "manifest_id"}
    if set(row) != expected or row.get("schema_version") != M7_CONTROLLER_VERSION:
        raise M7PersonBError("M7 Controller Manifest has an invalid shape or version")
    if (not isinstance(row.get("upstream"), Mapping)
            or set(row["upstream"]) != {"person_a_manifest_digest", "person_b_manifest_digest"}):
        raise M7PersonBError("M7 Controller upstream binding has an invalid shape")
    rebuilt = build_controller_manifest(
        config_families=row["config_families"], case_ids=row["case_ids"],
        candidate_digest=row["candidate_digest"], gold_digest=row["gold_digest"],
        artifacts=row["artifacts"], person_a_manifest_digest=row["upstream"]["person_a_manifest_digest"],
        person_b_manifest_digest=row["upstream"]["person_b_manifest_digest"],
        replay_seed=row["replay_seed"], fixture_only=row["fixture_only"],
        m7_entry_allowed=row["m7_entry_allowed"])
    if rebuilt != row:
        raise M7PersonBError("M7 Controller Manifest content or ID was mutated")
    return row


def build_assignments(manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    frozen = validate_controller_manifest(manifest)
    assignments = []
    for family, configs in frozen["config_families"].items():
        for row in build_run_matrix(configs, frozen["case_ids"]):
            assignments.append({"family_id": family, **row})
    return assignments


def validate_run_integrity(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]],
                           results: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    assignments = build_assignments(manifest)
    ledger_rows = [dict(row) for row in ledger]
    result_rows = [dict(row) for row in results]
    terminal_fields = {"case_id", "experiment_id", "run_id", "status", "terminal", "tokens",
                       "model_calls", "wall_ms", "raw_output_sha256"}
    by_family = {}
    for assignment in assignments:
        by_family.setdefault(assignment["family_id"], []).append(
            {key: assignment[key] for key in ("case_id", "experiment_id", "method_id")})
    experiment_family = {row["experiment_id"]: row["family_id"] for row in assignments}
    expected_keys = {(row["case_id"], row["experiment_id"]) for row in assignments}
    ledger_keys = [(row.get("case_id"), row.get("experiment_id")) for row in ledger_rows]
    if len(ledger_keys) != len(expected_keys) or set(ledger_keys) != expected_keys:
        raise M7PersonBError("Controller ledger must equal the exact frozen assignment set")
    reports = {}
    for family, family_assignments in by_family.items():
        family_ledger = [row for row in ledger_rows if experiment_family.get(row.get("experiment_id")) == family]
        reports[family] = validate_terminal_ledger(family_assignments, family_ledger)
    if any(set(row) != terminal_fields for row in ledger_rows):
        raise M7PersonBError("Controller ledger contains extra or missing fields")
    terminal = {(row["case_id"], row["experiment_id"]): row for row in ledger_rows}
    required = {"case_id", "experiment_id", "run_id", "status", "raw_output_sha256", "score_input_sha256"}
    seen = set()
    for row in result_rows:
        if set(row) != required:
            raise M7PersonBError("result binding has an invalid field set")
        key = (row["case_id"], row["experiment_id"])
        if key not in terminal or key in seen:
            raise M7PersonBError("result binding is unknown or duplicated")
        run = terminal[key]
        if (row["run_id"] != run["run_id"] or row["status"] != run["status"]
                or row["raw_output_sha256"] != run["raw_output_sha256"] or not _sha(row["score_input_sha256"])):
            raise M7PersonBError("result binding disagrees with terminal ledger bytes or status")
        seen.add(key)
    if seen != set(terminal):
        raise M7PersonBError("every terminal run requires one result binding")
    return {"complete": True, "family_reports": reports, "assignment_count": len(assignments),
            "result_digest": _digest(result_rows)}


def validate_aggregate_table(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]],
                             table: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    frozen = validate_controller_manifest(manifest)
    rows = [dict(row) for row in ledger]
    assignments = build_assignments(frozen)
    expected_keys = {(row["case_id"], row["experiment_id"]) for row in assignments}
    ledger_keys = [(row.get("case_id"), row.get("experiment_id")) for row in rows]
    if len(ledger_keys) != len(expected_keys) or set(ledger_keys) != expected_keys:
        raise M7PersonBError("aggregate ledger must equal the exact frozen assignment set")
    for family in frozen["config_families"]:
        family_assignments = [{key: row[key] for key in ("case_id", "experiment_id", "method_id")}
                              for row in assignments if row["family_id"] == family]
        family_ids = {row["experiment_id"] for row in family_assignments}
        validate_terminal_ledger(family_assignments,
                                 [row for row in rows if row.get("experiment_id") in family_ids])
    expected = []
    for family, configs in frozen["config_families"].items():
        for config in configs:
            subset = [row for row in rows if row.get("experiment_id") == config["experiment_id"]]
            counts = Counter(row.get("status") for row in subset)
            expected.append({"family_id": family, "experiment_id": config["experiment_id"],
                             "sample_count": len(subset), "success_count": counts["succeeded"],
                             "failure_count": len(subset) - counts["succeeded"],
                             "tokens": sum(row.get("tokens", 0) for row in subset),
                             "model_calls": sum(row.get("model_calls", 0) for row in subset),
                             "wall_ms": sum(row.get("wall_ms", 0) for row in subset)})
    supplied = [dict(row) for row in table]
    if supplied != expected:
        raise M7PersonBError("aggregate table does not reproduce the complete terminal ledger")
    return supplied


def select_replay_sample(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]], count: int) -> list[str]:
    frozen = validate_controller_manifest(manifest)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise M7PersonBError("replay count must be a positive integer")
    rows = [dict(row) for row in ledger]
    assignments = build_assignments(frozen)
    expected_keys = {(row["case_id"], row["experiment_id"]) for row in assignments}
    ledger_keys = [(row.get("case_id"), row.get("experiment_id")) for row in rows]
    if len(ledger_keys) != len(expected_keys) or set(ledger_keys) != expected_keys:
        raise M7PersonBError("replay ledger must equal the exact frozen assignment set")
    for family in frozen["config_families"]:
        family_assignments = [{key: row[key] for key in ("case_id", "experiment_id", "method_id")}
                              for row in assignments if row["family_id"] == family]
        family_ids = {row["experiment_id"] for row in family_assignments}
        validate_terminal_ledger(family_assignments,
                                 [row for row in rows if row.get("experiment_id") in family_ids])
    eligible = sorted(row["run_id"] for row in rows if row["status"] == "succeeded")
    if count > len(eligible):
        raise M7PersonBError("replay count exceeds successful terminal runs")
    return sorted(random.Random(frozen["replay_seed"]).sample(eligible, count))
