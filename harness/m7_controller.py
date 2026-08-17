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
PERSON_A_MANIFEST_PATH = "data/benchmarks/m7/person_a_protocol_candidate_v0_1.json"
PERSON_B_MANIFEST_PATH = "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json"


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


def verify_frozen_artifacts(root: Path, artifacts: Mapping[str, str]) -> None:
    """Re-read every frozen file; a digest map alone is never execution evidence."""
    if not artifacts:
        raise M7PersonBError("at least one frozen artifact is required")
    actual = freeze_artifacts(root, artifacts)
    if actual != dict(artifacts):
        raise M7PersonBError("frozen artifact bytes disagree with the Controller Manifest")


def build_controller_manifest(*, config_families: Mapping[str, Sequence[Mapping[str, Any]]],
                              case_ids: Sequence[str], candidate_digest: str,
                              gold_digest: str, artifacts: Mapping[str, str],
                              person_a_manifest_digest: str, person_b_manifest_digest: str,
                              replay_seed: int, root: Path, fixture_only: bool = True,
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
    role_modes = {rows[0]["role_mode"] for rows in families.values()}
    if role_modes != {"same_model", "different_models"}:
        raise M7PersonBError(
            "M7 config families must include at least one same_model and one different_models family"
        )
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
    verify_frozen_artifacts(root, artifacts)
    upstream_files = {
        PERSON_A_MANIFEST_PATH: person_a_manifest_digest,
        PERSON_B_MANIFEST_PATH: person_b_manifest_digest,
    }
    verify_frozen_artifacts(root, upstream_files)
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


def validate_controller_manifest(manifest: Mapping[str, Any], *, root: Path) -> dict[str, Any]:
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
        replay_seed=row["replay_seed"], root=root, fixture_only=row["fixture_only"],
        m7_entry_allowed=row["m7_entry_allowed"])
    if rebuilt != row:
        raise M7PersonBError("M7 Controller Manifest content or ID was mutated")
    return row


def build_assignments(manifest: Mapping[str, Any], *, root: Path) -> list[dict[str, str]]:
    frozen = validate_controller_manifest(manifest, root=root)
    assignments = []
    for family, configs in frozen["config_families"].items():
        for row in build_run_matrix(configs, frozen["case_ids"]):
            assignments.append({"family_id": family, **row})
    return assignments


def validate_run_integrity(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]],
                           results: Iterable[Mapping[str, Any]], *, root: Path) -> dict[str, Any]:
    assignments = build_assignments(manifest, root=root)
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
    run_ids = [row["run_id"] for row in ledger_rows]
    if len(set(run_ids)) != len(run_ids):
        raise M7PersonBError("run_id values must be globally unique across model families")
    terminal = {(row["case_id"], row["experiment_id"]): row for row in ledger_rows}
    configs = {config["experiment_id"]: config
               for family in manifest["config_families"].values() for config in family}
    for row in ledger_rows:
        budget = configs[row["experiment_id"]]["budget"]
        if (row["tokens"] > budget["total_tokens"]
                or row["model_calls"] > budget["model_calls"]
                or row["wall_ms"] > budget["timeout_seconds"] * 1000):
            raise M7PersonBError("terminal ledger exceeds the frozen per-sample budget")
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
    canonical_results = sorted(result_rows, key=lambda row: (row["case_id"], row["experiment_id"]))
    return {"complete": True, "family_reports": reports, "assignment_count": len(assignments),
            "result_digest": _digest(canonical_results)}


def validate_aggregate_table(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]],
                             table: Iterable[Mapping[str, Any]], *, root: Path) -> list[dict[str, Any]]:
    frozen = validate_controller_manifest(manifest, root=root)
    rows = [dict(row) for row in ledger]
    assignments = build_assignments(frozen, root=root)
    expected_keys = {(row["case_id"], row["experiment_id"]) for row in assignments}
    ledger_keys = [(row.get("case_id"), row.get("experiment_id")) for row in rows]
    if len(ledger_keys) != len(expected_keys) or set(ledger_keys) != expected_keys:
        raise M7PersonBError("aggregate ledger must equal the exact frozen assignment set")
    run_ids = [row.get("run_id") for row in rows]
    if len(set(run_ids)) != len(run_ids):
        raise M7PersonBError("run_id values must be globally unique across model families")
    for family in frozen["config_families"]:
        family_assignments = [{key: row[key] for key in ("case_id", "experiment_id", "method_id")}
                              for row in assignments if row["family_id"] == family]
        family_ids = {row["experiment_id"] for row in family_assignments}
        validate_terminal_ledger(family_assignments,
                                 [row for row in rows if row.get("experiment_id") in family_ids])
    configs_by_id = {config["experiment_id"]: config
                     for family in frozen["config_families"].values() for config in family}
    for row in rows:
        budget = configs_by_id[row["experiment_id"]]["budget"]
        if (row["tokens"] > budget["total_tokens"]
                or row["model_calls"] > budget["model_calls"]
                or row["wall_ms"] > budget["timeout_seconds"] * 1000):
            raise M7PersonBError("aggregate ledger exceeds the frozen per-sample budget")
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


def select_replay_sample(manifest: Mapping[str, Any], ledger: Iterable[Mapping[str, Any]], count: int,
                         *, root: Path) -> list[str]:
    frozen = validate_controller_manifest(manifest, root=root)
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise M7PersonBError("replay count must be a positive integer")
    rows = [dict(row) for row in ledger]
    assignments = build_assignments(frozen, root=root)
    expected_keys = {(row["case_id"], row["experiment_id"]) for row in assignments}
    ledger_keys = [(row.get("case_id"), row.get("experiment_id")) for row in rows]
    if len(ledger_keys) != len(expected_keys) or set(ledger_keys) != expected_keys:
        raise M7PersonBError("replay ledger must equal the exact frozen assignment set")
    run_ids = [row.get("run_id") for row in rows]
    if len(set(run_ids)) != len(run_ids):
        raise M7PersonBError("run_id values must be globally unique across model families")
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


def build_blind_review_plan(records: Iterable[Mapping[str, Any]], *, seed: int,
                            max_controls: int = 20) -> dict[str, Any]:
    """Freeze the M7 blind-error-analysis frame without exposing config identities."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise M7PersonBError("blind review seed must be an integer")
    if not isinstance(max_controls, int) or isinstance(max_controls, bool) or max_controls < 1:
        raise M7PersonBError("max_controls must be a positive integer")
    rows = [dict(row) for row in records]
    required = {"case_id", "experiment_id", "false_accept", "invalid_global_counterexample",
                "false_repair", "correct_verdict", "verified_repair_success", "undetermined",
                "infrastructure_failure", "review_payload_sha256"}
    bool_fields = required - {"case_id", "experiment_id", "review_payload_sha256"}
    if not rows or any(set(row) != required for row in rows):
        raise M7PersonBError("blind review record has an invalid field set")
    if any(not isinstance(row[field], str) or not row[field] for row in rows
           for field in ("case_id", "experiment_id")):
        raise M7PersonBError("blind review identities must be nonempty")
    if any(not _sha(row["review_payload_sha256"]) for row in rows):
        raise M7PersonBError("blind review payload digest must be a lowercase SHA-256")
    if any(not isinstance(row[field], bool) for row in rows for field in bool_fields):
        raise M7PersonBError("blind review classification fields must be boolean")
    keys = [(row["case_id"], row["experiment_id"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise M7PersonBError("blind review case/config pairs must be unique")

    rng = random.Random(seed)
    critical_fields = ("false_accept", "invalid_global_counterexample", "false_repair")
    control_fields = ("correct_verdict", "verified_repair_success", "undetermined",
                      "infrastructure_failure")
    selected_keys = {key for key, row in zip(keys, rows)
                     if any(row[field] for field in critical_fields)}
    frames = []
    experiments = sorted({row["experiment_id"] for row in rows})
    shuffled = list(experiments)
    rng.shuffle(shuffled)
    sealed_mapping = {experiment_id: f"anon-config-{index + 1:03d}"
                      for index, experiment_id in enumerate(shuffled)}
    for experiment_id in experiments:
        for category in control_fields:
            eligible = sorted(row["case_id"] for row in rows
                              if row["experiment_id"] == experiment_id and row[category])
            chosen = sorted(rng.sample(eligible, min(max_controls, len(eligible))))
            selected_keys.update((case_id, experiment_id) for case_id in chosen)
            frames.append({"anonymized_config_id": sealed_mapping[experiment_id], "category": category,
                           "eligible": eligible, "selected": chosen,
                           "not_selected": sorted(set(eligible) - set(chosen))})

    # When one case is selected, include every available anonymous configuration side by side.
    selected_cases = {case_id for case_id, _ in selected_keys}
    expanded = sorted(key for key in keys if key[0] in selected_cases)
    by_key = {(row["case_id"], row["experiment_id"]): row for row in rows}
    public_rows = [{"case_id": case_id,
                    "anonymized_config_id": sealed_mapping[experiment_id],
                    "review_payload_sha256": by_key[(case_id, experiment_id)]["review_payload_sha256"]}
                   for case_id, experiment_id in expanded]
    public_plan = {"seed": seed, "max_controls": max_controls, "frames": frames,
                   "review_rows": public_rows, "sealed_mapping_sha256": _digest(sealed_mapping)}
    return {"public_plan": public_plan, "public_plan_sha256": _digest(public_plan),
            "sealed_mapping": sealed_mapping}
