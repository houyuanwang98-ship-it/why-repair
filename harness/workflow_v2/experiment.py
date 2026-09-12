"""Offline preparation, immutable assignment execution, and blind aggregation."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from .contracts import (ROOT, METHODS, EXPERIMENT_MODEL, VALIDATION_MODEL, SCHEMAS, digest,
                        read, require, public_problem, judge_input, validate_judgment,
                        strict_accept, implementation_digest, snapshot_implementation, write_once)
from .engine import Workflow
from .runtime import Calls, fixed_models, DISABLED_FEATURES

SOURCES = (
    ("m2_pilot", "data/benchmarks/m2/source/pilot_50.jsonl", 50),
    ("m2_b50", "data/benchmarks/m2/source/pilot_B50.jsonl", 50),
    ("opc", "data/benchmarks/m7/opc_250_v0_2/candidate.jsonl", 250),
    ("proofnet", "data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl", 250),
)
PILOT_IDS = ("m2-011", "m2-018", "m2-034", "B01", "B25", "B50",
             "opc250-001", "opc250-125", "opc250-250",
             "proofnet250-001", "proofnet250-125", "proofnet250-250")


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_files(folder):
    return {str(p.relative_to(folder)): file_digest(p) for p in sorted(Path(folder).rglob("*.json"))
            if p.name != "result.json"}


def explicit_subgoals(theorem):
    matches = list(re.finditer(r"(?m)^\s*(?:\(([1-9a-z])\)|([1-9])\.|Part ([1-9]))\s+", theorem))
    labels = [next(g for g in m.groups() if g) for m in matches]
    if len(labels) < 2 or any(ord(b) != ord(a) + 1 for a, b in zip(labels, labels[1:])):
        return []
    return [theorem[m.start():matches[i+1].start() if i+1 < len(matches) else len(theorem)].strip()
            for i, m in enumerate(matches)]


def source_rows():
    rows, sources = [], {}
    for group, path, expected in SOURCES:
        entries = [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]
        require(len(entries) == expected, f"source count changed: {path}")
        sources[path] = file_digest(ROOT / path)
        for r in entries:
            theorem = r.get("theorem", r.get("problem"))
            proof = r.get("proof") or "\n".join(n["text"] for n in r["proof_steps"])
            p = public_problem({"theorem": theorem, "assumptions": r.get("assumptions", []),
                "domain": r["domain"], "proof_text": proof, "explicit_subgoals": explicit_subgoals(theorem)})
            # Exact-source grouping is sufficient for a disclosed development pilot only.
            family = hashlib.sha256(" ".join(theorem.split()).encode()).hexdigest()
            rows.append({"case_id": r.get("proof_id", r.get("case_id")), "source_group": family,
                         "source_collection": group, "source_path": path,
                         "source_row_digest": digest(r), "problem_digest": digest(p), **p})
    require(len({r["case_id"] for r in rows}) == 600, "missing or duplicate case IDs")
    return rows, sources


def prepare(output, *, case_ids=None, selection_note=None):
    """Only local reads/writes. No model adapter is constructed here."""
    fixed_models()
    output = Path(output)
    rows, sources = source_rows()
    write_once(output / "corpus.json", rows)
    selected_ids = tuple(PILOT_IDS if case_ids is None else case_ids)
    require(selected_ids and len(selected_ids) == len(set(selected_ids)), "empty or duplicate selection")
    selected = [r for r in rows if r["case_id"] in selected_ids]
    require(len(selected) == len(selected_ids), "pilot cases missing")
    write_once(output / "pilot.json", selected)
    config = read(ROOT / "docs/workflow_v2/protocol.json")
    assignments = []
    for row in selected:
        for method in METHODS:
            assignment = {"case_id": row["case_id"], "source_group": row["source_group"],
                          "problem_digest": row["problem_digest"], "method": method, "replicate": 0,
                          "model_config_digest": digest(config["models"])}
            assignments.append({"task_id": digest(assignment), **assignment})
    write_once(output / "assignments.json", assignments)
    manifest = {"schema_version": "workflow-v2-bundle-1", "run_id": output.name,
        "status": "prepared_not_started", "input_mode": "raw_text_end_to_end",
        "dataset_role": "historical_development_pilot", "scientific_confirmatory_claim_allowed": False,
        "source_family_grouping": "exact_normalized_theorem_only_not_semantic_deduplication",
        "selection_note": selection_note or "Original 12-case engineering pilot",
        "models": config["models"], "budget": config["engineering_budget_proposal"],
        "external_judge_budget": {"max_calls": 1, "max_tokens": 24000, "max_seconds": 1800},
        "tool_policy": "no_model_tools_no_external_retrieval", "tool_calls_cap": 0,
        "corpus_cases": len(rows), "pilot_cases": len(selected), "assignment_count": len(assignments),
        "sources": sources, "files": {n: file_digest(output / n) for n in
                                     ("corpus.json", "pilot.json", "assignments.json")},
        "implementation_digest": implementation_digest(), "new_model_calls": 0,
        "new_human_reviews": 0,
        "ceiling_not_cost_estimate": {"internal_model_attempts": len(selected) * 5 * 24,
            "internal_total_tokens": len(selected) * 5 * 80000,
            "external_judge_attempts": len(assignments), "external_total_tokens": len(assignments) * 24000}}
    write_once(output / "manifest.json", manifest)
    snapshot_implementation(output / "implementation_snapshot.zip")
    return manifest


def validate_bundle(path):
    path = Path(path)
    m = read(path / "manifest.json")
    if m.get("schema_version") == "workflow-v2-judgment-bundle-1":
        from .judging import validate_judge_bundle
        return validate_judge_bundle(path)
    require(m["implementation_digest"] == implementation_digest(), "implementation drift; prepare a new bundle")
    config = read(ROOT / "docs/workflow_v2/protocol.json")
    require(m["models"] == config["models"], "model configuration drift")
    require(m["budget"] == config["engineering_budget_proposal"], "budget configuration drift")
    return validate_bundle_data(path, m)


def validate_bundle_data(path, m):
    """Validate data against its own frozen model configuration, without changing old identities."""
    path = Path(path)
    require(m["input_mode"] == "raw_text_end_to_end" and m["tool_calls_cap"] == 0, "unsupported bundle mode")
    for name, expected in m["files"].items():
        require(file_digest(path / name) == expected, "bundle data drift: " + name)
    for name, expected in m["sources"].items():
        require(file_digest(ROOT / name) == expected, "source data drift: " + name)
    cases = {r["case_id"]: r for r in read(path / "pilot.json")}
    assignments = read(path / "assignments.json")
    require(len(cases) == m["pilot_cases"] and len(assignments) == m["assignment_count"], "matrix count mismatch")
    keys = set()
    for a in assignments:
        require(a["task_id"] == digest({k: v for k, v in a.items() if k != "task_id"}), "task ID mismatch")
        require(a["model_config_digest"] == digest(m["models"]), "assignment model mismatch")
        require(a["task_id"] not in keys and a["method"] in METHODS, "duplicate/unknown assignment")
        keys.add(a["task_id"])
        require(a["problem_digest"] == digest(public_problem(cases[a["case_id"]])), "problem mismatch")
    require({(a["case_id"], a["method"]) for a in assignments} == {(c, x) for c in cases for x in METHODS},
            "incomplete method matrix")
    return m, cases, assignments


def local_readiness():
    def probe(args):
        try:
            p = subprocess.run(args, text=True, capture_output=True, timeout=15)
            return p.returncode, p.stdout
        except (OSError, subprocess.TimeoutExpired):
            return -1, ""
    rc, version = probe(["codex", "--version"])
    help_rc, help_text = probe(["codex", "exec", "--help"])
    feature_rc, features = probe(["codex", "features", "list"])
    auth_rc, _ = probe(["codex", "login", "status"])
    flags = ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--output-schema", "--disable")
    feature_names = {line.split()[0] for line in features.splitlines() if line.strip()}
    return {"cli_version": version.strip() if rc == 0 else None,
            "cli_flags_present": help_rc == 0 and all(f in help_text for f in flags),
            "isolation_features_present": feature_rc == 0 and set(DISABLED_FEATURES) <= feature_names,
            "saved_auth_status_ok": auth_rc == 0,
            "fixed_models_available": "not_probed_no_model_calls",
            "backend_snapshot_verified": False, "new_model_calls": 0}


def preflight(path, inspect_environment=True):
    m, cases, assignments = validate_bundle(path)
    for schema in SCHEMAS.values():
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)
    env = local_readiness() if inspect_environment else {"environment_check": "not_requested"}
    for name, schema in SCHEMAS.items():
        require(read(ROOT / "schemas/workflow_v2" / f"{name}.schema.json") == schema, "schema export drift")
    return {"bundle_integrity_passed": True, "schema_count": len(SCHEMAS),
            "case_count": len(cases), "assignment_count": len(assignments),
            "preparation_complete": True, "experiment_started": (Path(path) / "runtime").exists(),
            "preflight_makes_model_calls": False,
            "next_stage": "deferred_judging_requires_explicit_execute" if m.get("source_bundle") else
                          "engineering_pilot_requires_explicit_execute", "environment": env,
            "frozen_generation_source": m.get("source_bundle"),
            "formal_readiness": False,
            "formal_pending": ["pilot_results", "judge_calibration", "new_test_freeze", "human_review_plan"],
            "manifest_digest": digest(m)}


def execute_assignments(path, *, execute=False):
    require(execute, "live execution disabled; pass --execute deliberately")
    path = Path(path)
    m, cases, assignments = validate_bundle(path)
    require(m.get("schema_version") != "workflow-v2-judgment-bundle-1", "judge bundle cannot generate")
    for a in assignments:
        folder = path / "runtime" / a["task_id"]
        if (folder / "result.json").exists():
            saved = read(folder / "result.json")
            require(saved["evidence_files"] == evidence_files(folder), "runtime evidence changed")
            require(saved["assignment"] == a, "saved assignment changed")
            continue
        write_once(folder / "identity.json", a)
        b = m["budget"]
        calls = Calls(folder, execute=True, max_calls=b["max_model_attempts_per_task"],
                      max_tokens=b["max_total_tokens_per_task"], max_seconds=b["max_wall_seconds_per_task"],
                      max_output_retries=b.get("max_output_contract_retries", 0))
        workflow = Workflow(cases[a["case_id"]], calls)
        result = workflow.run(a["method"])
        write_once(folder / "result.json", {"assignment": a, "outcome": result,
                                            "evidence_files": evidence_files(folder)})
    # Freezing every output is a prerequisite for any final judge invocation.
    write_once(path / "candidate_freeze.json", {a["task_id"]: file_digest(path / "runtime" / a["task_id"] / "result.json")
                                               for a in assignments})


def score_assignments(path, *, execute=False):
    require(execute, "live judging disabled; pass --execute deliberately")
    path = Path(path)
    m, cases, assignments = validate_bundle(path)
    runtime_path = Path(m.get("source_bundle", path))
    frozen = read(path / "candidate_freeze.json")
    require(set(frozen) == {a["task_id"] for a in assignments}, "candidate freeze incomplete")
    for a in assignments:
        require(file_digest(runtime_path / "runtime" / a["task_id"] / "result.json") == frozen[a["task_id"]], "candidate changed after freeze")
    mapping_path = path / "private_judge_mapping.json"
    if not mapping_path.exists():
        write_once(mapping_path, {a["task_id"]: "blind-" + uuid.uuid4().hex for a in assignments})
    mapping = read(mapping_path)
    require(set(mapping) == set(frozen) and len(set(mapping.values())) == len(mapping), "invalid blind map")
    # Independent, uniformly shaped sessions; method IDs never enter the request.
    for a in sorted(assignments, key=lambda a: mapping[a["task_id"]]):
        sample = mapping[a["task_id"]]
        folder = path / "judge" / sample
        result_path = folder / "result.json"
        if result_path.exists():
            require(read(result_path)["evidence_files"] == evidence_files(folder), "judge evidence changed")
            continue
        outcome = read(runtime_path / "runtime" / a["task_id"] / "result.json")["outcome"]
        payload = judge_input(cases[a["case_id"]], outcome["candidate_text"], sample)
        calls = Calls(folder, execute=True, judge=True, **m["external_judge_budget"])
        try:
            judgment = validate_judgment(calls.call("judge", payload), payload)
            scored = {"status": "scored", "judgment": judgment}
        except Exception as exc:
            scored = {"status": "missing", "reason": str(exc), "judgment": None}
        write_once(result_path, {**scored, "calls": calls.summary(), "evidence_files": evidence_files(folder)})


def aggregate(path):
    path = Path(path)
    m, _, assignments = validate_bundle(path)
    runtime_path = Path(m.get("source_bundle", path))
    mapping = read(path / "private_judge_mapping.json") if (path / "private_judge_mapping.json").exists() else {}
    frozen = read(path / "candidate_freeze.json") if (path / "candidate_freeze.json").exists() else {}
    groups = {}
    for method in METHODS:
        tasks = [a for a in assignments if a["method"] == method]
        counts = Counter(assigned=len(tasks))
        for a in tasks:
            file = runtime_path / "runtime" / a["task_id"] / "result.json"
            if not file.exists():
                counts["not_run"] += 1
                continue
            saved = read(file)
            if frozen:
                require(frozen.get(a["task_id"]) == file_digest(file), "frozen outcome drift")
            require(saved["evidence_files"] == evidence_files(file.parent), "runtime evidence drift")
            result = saved["outcome"]
            counts[result["terminal_status"]] += 1
            claimed = result["system_claim"] == "proof_valid"
            counts["claims"] += claimed
            jf = path / "judge" / mapping.get(a["task_id"], "not_assigned") / "result.json"
            scored = read(jf) if jf.exists() else None
            if scored:
                require(scored["evidence_files"] == evidence_files(jf.parent), "judge evidence drift")
            if not scored or scored["status"] != "scored":
                counts["missing_judgments"] += 1
                counts["unresolved_claims"] += claimed
                continue
            j = scored["judgment"]
            accepted = strict_accept(j)
            counts["strict_accepted_texts"] += accepted
            counts["system_success"] += accepted and result["terminal_status"] == "proof_ready"
            if claimed and not accepted:
                definite = (j["candidate_kind"] != "proof" or j["validity"] == "invalid" or
                            any(j[k] == "fail" for k in ("rigor", "problem_preservation", "goal_coverage")))
                counts["false_claims" if definite else "unresolved_claims"] += 1
        s = counts["claims"]
        groups[method] = {"counts": dict(counts), "system_success_rate":
                          counts["system_success"] / len(tasks) if not counts["not_run"] and not counts["missing_judgments"] else None,
                          "coverage": s / len(tasks), "false_success_bounds":
                          [counts["false_claims"] / s, (counts["false_claims"] + counts["unresolved_claims"]) / s] if s else None}
    return {"evidence": "model_judgment_only", "human_verified": False, "methods": groups}
