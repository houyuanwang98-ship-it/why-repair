"""Deterministic M6 Controller freeze, ledger, and statistics machinery.

The module prepares and validates pre-results experiment candidates.  It does
not call a model provider; non-fixture execution remains guarded by the M5 and
human-signature gates in :mod:`harness.m6_experiments`.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from harness.m6_experiments import (
    FAILURE_TYPES, M6ExperimentError, apply_method_applicability, canonical_digest, score_records,
    validate_experiment_config, validate_experiment_suite,
)


M6_CONTROLLER_VERSION = "m6-controller-0.1"
RUN_STATUSES = {"success", *FAILURE_TYPES}
CONFIRMATORY_FAMILIES = {
    "H1": {
        f"{method}:{endpoint}"
        for method in ("direct_judgment", "self_reflection", "generator_critic")
        for endpoint in ("first_error_exact_accuracy",
                         "first_error_false_positive_rate_when_absent", "false_accept_rate")
    },
    "H2": {
        f"{method}:{endpoint}"
        for method in ("no_structured_certificate", "no_counterexample_protocol")
        for endpoint in ("false_accept_rate", "false_claim_detection_rate",
                         "valid_counterexample_coverage")
    },
    "H3": {
        f"{method}:{endpoint}"
        for method in ("no_graph", "no_descendant_invalidation", "single_round_repair")
        for endpoint in ("verified_repair_success_rate", "false_repair_rate",
                         "new_error_introduction_rate")
    },
}


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_artifacts(root: Path, paths: Iterable[str]) -> dict[str, str]:
    """Hash an explicit, repository-relative artifact set, rejecting escapes."""
    base = root.resolve()
    frozen: dict[str, str] = {}
    for relative in sorted(set(paths)):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise M6ExperimentError("artifact paths must be nonempty repository-relative strings")
        target = (base / relative).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise M6ExperimentError("artifact path escapes repository root") from exc
        if not target.is_file():
            raise M6ExperimentError(f"artifact is not a file: {relative}")
        frozen[Path(relative).as_posix()] = file_sha256(target)
    if not frozen:
        raise M6ExperimentError("at least one artifact must be frozen")
    return frozen


def build_controller_manifest(
    *, configs: Sequence[Mapping[str, Any]], sample_ids: Sequence[str],
    artifacts: Mapping[str, str], metric_digest: str, statistics_digest: str,
    bootstrap_seeds: Sequence[int], randomization_seeds: Sequence[int], m5_gate_digest: str,
    signatures: Mapping[str, str], m5_entry_allowed: bool = False,
    fixture_only: bool = True,
) -> dict[str, Any]:
    """Build an immutable pre-results Controller manifest candidate."""
    validate_experiment_suite(configs)
    if not sample_ids or any(not isinstance(item, str) or not item for item in sample_ids):
        raise M6ExperimentError("sample_ids must be nonempty strings")
    if len(set(sample_ids)) != len(sample_ids):
        raise M6ExperimentError("sample_ids must be unique")
    if not artifacts or any(not isinstance(path, str) or not path or not _is_sha256(digest)
                            for path, digest in artifacts.items()):
        raise M6ExperimentError("artifacts must map paths to SHA-256 digests")
    for path in artifacts:
        candidate = Path(path)
        if (candidate.is_absolute() or candidate.drive or not candidate.parts
                or candidate == Path(".") or ".." in candidate.parts
                or candidate.as_posix() != path):
            raise M6ExperimentError("artifact manifest keys must be normalized repository-relative paths")
    for name, seeds in (("bootstrap_seeds", bootstrap_seeds),
                        ("randomization_seeds", randomization_seeds)):
        if any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds) or not seeds:
            raise M6ExperimentError(f"{name} must be a nonempty integer list")
        if len(set(seeds)) != len(seeds):
            raise M6ExperimentError(f"{name} must be unique")
    if any(not _is_sha256(value) for value in (metric_digest, statistics_digest, m5_gate_digest)):
        raise M6ExperimentError("manifest digest fields must be SHA-256 digests")
    required_signatures = {"person_a", "person_b_cross_review", "controller"}
    if set(signatures) != required_signatures:
        raise M6ExperimentError("manifest requires exact Person A, Person B, and Controller signature slots")
    if not isinstance(fixture_only, bool):
        raise M6ExperimentError("fixture_only must be boolean")
    if not isinstance(m5_entry_allowed, bool):
        raise M6ExperimentError("m5_entry_allowed must be boolean")
    pending_signatures = {"person_a": "pending_human_signature",
                          "person_b_cross_review": "pending_cross_review",
                          "controller": "candidate_unsigned"}
    if fixture_only and (m5_entry_allowed or dict(signatures) != pending_signatures):
        raise M6ExperimentError("fixture manifest must preserve the closed M5 gate and pending signatures")
    if not fixture_only:
        # v0.1 has no trusted signature verifier and receives the M5 flag/digest from
        # its caller.  Accepting strings such as "signed" here would turn assertions
        # into authority.  A later formal version must verify the live M5 artifact and
        # detached signatures before this branch can construct an executable manifest.
        raise M6ExperimentError(
            "formal M6 manifest blocked: authentic M5 gate and detached-signature verification are not implemented"
        )
    body = {
        "schema_version": M6_CONTROLLER_VERSION,
        "status": "fixture_candidate_m5_entry_blocked" if fixture_only else "frozen_for_execution",
        "fixture_only": fixture_only,
        "result_exposure": {"status": "no_m6_results_viewed",
                            "evidence_strength": "self_attested_unverified"},
        "configs": [validate_experiment_config(row) for row in configs],
        "sample_ids": list(sample_ids),
        "sample_set_digest": canonical_digest(list(sample_ids)),
        "artifacts": dict(sorted(artifacts.items())),
        "metric_digest": metric_digest,
        "statistics_digest": statistics_digest,
        "bootstrap_seeds": list(bootstrap_seeds),
        "randomization_seeds": list(randomization_seeds),
        "m5_gate_digest": m5_gate_digest,
        "m5_entry_allowed": m5_entry_allowed,
        "signatures": dict(signatures),
    }
    return {**body, "manifest_id": f"m6-controller-{canonical_digest(body)[:16]}"}


def validate_run_ledger(
    manifest: Mapping[str, Any], records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require one terminal row per configured method/sample and preserve attempts."""
    rows = [dict(row) for row in records]
    validated = validate_controller_manifest(manifest)
    configs_by_id = {row["experiment_id"]: row for row in validated["configs"]}
    expected = {(eid, sid) for eid in configs_by_id for sid in validated["sample_ids"]}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen_run_ids: set[str] = set()
    for row in rows:
        required = {"run_id", "experiment_id", "sample_id", "attempt", "status", "terminal", "tokens", "model_calls", "cost", "latency_seconds"}
        if not required.issubset(row):
            raise M6ExperimentError("run ledger row is missing required fields")
        if not isinstance(row["run_id"], str) or not row["run_id"]:
            raise M6ExperimentError("run_id must be a nonempty string")
        if row["run_id"] in seen_run_ids:
            raise M6ExperimentError("run_id values must be unique")
        seen_run_ids.add(row["run_id"])
        key = (row["experiment_id"], row["sample_id"])
        if key not in expected:
            raise M6ExperimentError("run ledger contains an unassigned experiment/sample")
        if row["status"] not in RUN_STATUSES:
            raise M6ExperimentError("run ledger contains an unknown status")
        if not isinstance(row["terminal"], bool):
            raise M6ExperimentError("terminal must be boolean")
        if row["status"] == "success" and not row["terminal"]:
            raise M6ExperimentError("a successful attempt must be terminal")
        if not isinstance(row["attempt"], int) or isinstance(row["attempt"], bool) or row["attempt"] < 0:
            raise M6ExperimentError("attempt must be a nonnegative integer")
        for field in ("tokens", "model_calls", "cost", "latency_seconds"):
            if (not isinstance(row[field], (int, float)) or isinstance(row[field], bool)
                    or not math.isfinite(row[field]) or row[field] < 0):
                raise M6ExperimentError(f"{field} must be nonnegative")
        if not isinstance(row["tokens"], int) or not isinstance(row["model_calls"], int):
            raise M6ExperimentError("tokens and model_calls must be integers")
        grouped.setdefault(key, []).append(row)
    missing = sorted(expected - set(grouped))
    duplicate_attempts = []
    nonterminal = []
    for key, attempts in grouped.items():
        numbers = sorted(row["attempt"] for row in attempts)
        if numbers != list(range(len(numbers))):
            duplicate_attempts.append(key)
        terminal = [row for row in attempts if row.get("terminal") is True]
        if len(terminal) != 1 or terminal[0]["attempt"] != max(numbers):
            nonterminal.append(key)
        budget = configs_by_id[key[0]]["budget"]
        if len(attempts) > budget["retry_limit"] + 1:
            raise M6ExperimentError("run ledger exceeds the frozen retry limit")
        if sum(row["tokens"] for row in attempts) > budget["total_tokens"]:
            raise M6ExperimentError("run ledger exceeds the per-sample token limit")
        if sum(row["model_calls"] for row in attempts) > budget["model_calls"]:
            raise M6ExperimentError("run ledger exceeds the per-sample model-call limit")
        if sum(row["latency_seconds"] for row in attempts) > budget["timeout_seconds"]:
            raise M6ExperimentError("run ledger exceeds the frozen per-sample wall-clock limit")
    if duplicate_attempts:
        raise M6ExperimentError("attempts must be contiguous from zero")
    if nonterminal:
        raise M6ExperimentError("each assignment requires exactly one final terminal attempt")
    terminal_rows = [next(row for row in grouped[key] if row.get("terminal") is True) for key in sorted(grouped)]
    return {
        "expected_assignment_count": len(expected),
        "observed_assignment_count": len(grouped),
        "missing_assignments": [{"experiment_id": e, "sample_id": s} for e, s in missing],
        "complete": not missing,
        "attempt_count": len(rows),
        "success_count": sum(row["status"] == "success" for row in terminal_rows),
        "failure_counts": {kind: sum(row["status"] == kind for row in terminal_rows) for kind in sorted(FAILURE_TYPES)},
        "total_tokens": sum(row["tokens"] for row in rows),
        "total_model_calls": sum(row["model_calls"] for row in rows),
        "total_cost": sum(row["cost"] for row in rows),
        "total_latency_seconds": sum(row["latency_seconds"] for row in rows),
    }


def field_completeness_report(
    records: Iterable[Mapping[str, Any]], required_fields: Sequence[str],
) -> dict[str, Any]:
    """Report field presence without deleting incomplete rows or treating false/zero as missing."""
    if not required_fields or any(not isinstance(field, str) or not field for field in required_fields):
        raise M6ExperimentError("required_fields must be nonempty field names")
    if len(set(required_fields)) != len(required_fields):
        raise M6ExperimentError("required_fields must be unique")
    rows = [dict(row) for row in records]
    missing_by_field = {
        field: [row.get("run_id", f"row:{index}") for index, row in enumerate(rows)
                if field not in row or row[field] is None]
        for field in required_fields
    }
    complete_rows = sum(all(field in row and row[field] is not None for field in required_fields) for row in rows)
    return {
        "row_count": len(rows),
        "complete_row_count": complete_rows,
        "complete": complete_rows == len(rows),
        "fields": {
            field: {"present_count": len(rows) - len(missing), "missing_count": len(missing),
                    "missing_run_ids": missing}
            for field, missing in missing_by_field.items()
        },
    }


def validate_controller_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate shape, gates, embedded configs, and the content-bound ID."""
    row = dict(manifest)
    expected_fields = {
        "schema_version", "status", "fixture_only", "result_exposure", "configs",
        "sample_ids", "sample_set_digest", "artifacts", "metric_digest",
        "statistics_digest", "bootstrap_seeds", "randomization_seeds", "m5_gate_digest", "m5_entry_allowed",
        "signatures", "manifest_id",
    }
    if set(row) != expected_fields or row["schema_version"] != M6_CONTROLLER_VERSION:
        raise M6ExperimentError("Controller manifest has an invalid shape or version")
    rebuilt = build_controller_manifest(
        configs=row["configs"], sample_ids=row["sample_ids"], artifacts=row["artifacts"],
        metric_digest=row["metric_digest"], statistics_digest=row["statistics_digest"],
        bootstrap_seeds=row["bootstrap_seeds"], randomization_seeds=row["randomization_seeds"],
        m5_gate_digest=row["m5_gate_digest"],
        signatures=row["signatures"], m5_entry_allowed=row["m5_entry_allowed"],
        fixture_only=row["fixture_only"],
    )
    if row != rebuilt:
        raise M6ExperimentError("Controller manifest content or manifest_id was mutated")
    return row


def paired_bootstrap_difference(
    left: Sequence[float], right: Sequence[float], *, seeds: Sequence[int], alpha: float = 0.05,
) -> dict[str, Any]:
    """Deterministic paired bootstrap confidence interval for a mean difference.

    This function intentionally does not manufacture a hypothesis-test p-value
    from bootstrap sign tails.  Confirmatory Holm input must come from the paired
    randomization test below (or another preregistered valid test).
    """
    if len(left) != len(right) or not left:
        raise M6ExperimentError("paired bootstrap requires equal nonempty samples")
    if (not 0 < alpha < 1 or not seeds
            or any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds)
            or len(set(seeds)) != len(seeds)):
        raise M6ExperimentError("invalid bootstrap alpha or seeds")
    try:
        diffs = [float(a) - float(b) for a, b in zip(left, right)]
    except (TypeError, ValueError) as exc:
        raise M6ExperimentError("paired bootstrap values must be finite numbers") from exc
    if any(not math.isfinite(value) for value in diffs):
        raise M6ExperimentError("paired bootstrap values must be finite numbers")
    estimates = []
    n = len(diffs)
    for seed in seeds:
        rng = random.Random(seed)
        estimates.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    estimates.sort()

    def quantile(p: float) -> float:
        position = p * (len(estimates) - 1)
        low, high = math.floor(position), math.ceil(position)
        return estimates[low] if low == high else estimates[low] + (estimates[high] - estimates[low]) * (position - low)

    return {
        "paired_count": n,
        "absolute_difference": sum(diffs) / n,
        "ci": [quantile(alpha / 2), quantile(1 - alpha / 2)],
        "bootstrap_replicates": len(seeds),
    }


def paired_randomization_p_value(
    left: Sequence[float], right: Sequence[float], *, seeds: Sequence[int],
) -> float:
    """Two-sided paired sign-flip randomization p-value with +1 correction."""
    if len(left) != len(right) or not left:
        raise M6ExperimentError("paired randomization requires equal nonempty samples")
    if (not seeds or any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds)
            or len(set(seeds)) != len(seeds)):
        raise M6ExperimentError("paired randomization requires unique integer seeds")
    try:
        diffs = [float(a) - float(b) for a, b in zip(left, right)]
    except (TypeError, ValueError) as exc:
        raise M6ExperimentError("paired randomization values must be finite numbers") from exc
    if any(not math.isfinite(value) for value in diffs):
        raise M6ExperimentError("paired randomization values must be finite numbers")
    observed = abs(sum(diffs) / len(diffs))
    extreme = 0
    for seed in seeds:
        rng = random.Random(seed)
        permuted = abs(sum(value if rng.randrange(2) else -value for value in diffs) / len(diffs))
        extreme += permuted >= observed
    return (extreme + 1) / (len(seeds) + 1)


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    """Return monotone Holm-adjusted p-values for one preregistered family."""
    if not p_values or any(not isinstance(value, (int, float)) or isinstance(value, bool)
                           or not math.isfinite(value) or not 0 <= value <= 1
                           for value in p_values.values()):
        raise M6ExperimentError("Holm p-values must be within [0, 1]")
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    size = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (size - index) * value))
        adjusted[name] = running
    return adjusted


def holm_adjust_preregistered(hypothesis: str, p_values: Mapping[str, float]) -> dict[str, float]:
    """Reject missing/extra tests before adjusting one exact preregistered family."""
    expected = CONFIRMATORY_FAMILIES.get(hypothesis)
    if expected is None:
        raise M6ExperimentError("unknown preregistered hypothesis family")
    if set(p_values) != expected:
        raise M6ExperimentError("Holm input must contain the complete preregistered hypothesis family")
    return holm_adjust(p_values)


def aggregate_by_experiment(
    manifest: Mapping[str, Any], ledger_records: Iterable[Mapping[str, Any]],
    records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Score exact terminal ledger assignments and apply method applicability."""
    frozen = validate_controller_manifest(manifest)
    ledger_rows = [dict(row) for row in ledger_records]
    ledger_report = validate_run_ledger(frozen, ledger_rows)
    if not ledger_report["complete"]:
        raise M6ExperimentError("cannot aggregate an incomplete run ledger")
    terminal_by_assignment = {
        (row["experiment_id"], row["sample_id"]): row
        for row in ledger_rows if row["terminal"] is True
    }
    configs = {row["experiment_id"]: row for row in frozen["configs"]}
    expected = {(experiment_id, sample_id) for experiment_id in configs for sample_id in frozen["sample_ids"]}
    groups: dict[str, list[Mapping[str, Any]]] = {}
    seen: set[tuple[str, str]] = set()
    for row in records:
        experiment_id = row.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id:
            raise M6ExperimentError("scoring record requires experiment_id")
        key = (experiment_id, row.get("sample_id"))
        if key not in expected:
            raise M6ExperimentError("scoring record is not assigned by the Controller manifest")
        if key in seen:
            raise M6ExperimentError("scoring records must contain one terminal row per assignment")
        terminal = terminal_by_assignment[key]
        if row.get("terminal_run_id") != terminal["run_id"]:
            raise M6ExperimentError("scoring record is not bound to the terminal ledger run_id")
        expected_failure = None if terminal["status"] == "success" else terminal["status"]
        if row.get("failure_type") != expected_failure:
            raise M6ExperimentError("scoring failure_type disagrees with the terminal ledger status")
        seen.add(key)
        groups.setdefault(experiment_id, []).append(row)
    if seen != expected:
        raise M6ExperimentError("scoring records must cover every manifest assignment")
    return {
        experiment_id: apply_method_applicability(
            configs[experiment_id]["method"]["method_id"], score_records(rows)
        )
        for experiment_id, rows in sorted(groups.items())
    }
