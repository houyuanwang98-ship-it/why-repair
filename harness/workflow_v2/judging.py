"""Hash-bound deferred judging of completed experiments under a new judge configuration."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

from .contracts import (ROOT, EXPERIMENT_MODEL, digest, implementation_digest, snapshot_implementation, read,
                        require, write_once)
from .experiment import evidence_files, file_digest, validate_bundle_data
from .runtime import fixed_models

SOURCE_ANCHORS = ("manifest.json", "candidate_freeze.json", "implementation_snapshot.zip",
                  "scheduler/final.json", "scheduler/judge_handoff.json")


def validate_frozen_source(path):
    path = Path(path).resolve()
    manifest = read(path / "manifest.json")
    require(manifest["schema_version"] == "workflow-v2-bundle-1", "expected a generation bundle")
    experiment = manifest["models"]["experiment"]
    require((experiment["requested_model"], experiment["reasoning_effort"]) == EXPERIMENT_MODEL,
            "source experiment model differs from locked experiment model")
    with zipfile.ZipFile(path / "implementation_snapshot.zip") as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and all(not n.endswith("/") for n in names),
                "ambiguous source implementation archive")
        archived_digest = digest({n: hashlib.sha256(archive.read(n)).hexdigest() for n in names})
    require(archived_digest == manifest["implementation_digest"], "source implementation archive drift")
    _, cases, assignments = validate_bundle_data(path, manifest)
    frozen = read(path / "candidate_freeze.json")
    require(set(frozen) == {a["task_id"] for a in assignments}, "source freeze incomplete")
    final = read(path / "scheduler/final.json")
    require(final["runtime_completed"] == len(assignments) and
            final["status"] in {"completed", "completed_with_failures"}, "source execution incomplete")
    require(not any(s["alive"] for s in final["slots"]), "source servers still active")
    handoff = read(path / "scheduler/judge_handoff.json")
    require(handoff["candidate_freeze_sha256"] == file_digest(path / "candidate_freeze.json") and
            len(handoff["pending_task_ids"]) == len(assignments) and
            set(handoff["pending_task_ids"]) == set(frozen), "source handoff differs from freeze")
    for assignment in assignments:
        task = assignment["task_id"]
        folder = path / "runtime" / task
        saved = read(folder / "result.json")
        require(saved["assignment"] == assignment, "source assignment changed")
        require(file_digest(folder / "result.json") == frozen[task], "source result changed after freeze")
        require(saved["evidence_files"] == evidence_files(folder), "source call evidence changed")
        item = read(path / "candidate_freezes" / (task + ".json"))
        require(item["task_id"] == task and item["result_sha256"] == frozen[task], "source per-item freeze changed")
        require(type(item["lane"]) is int and 0 <= item["lane"] < 24, "source lane out of range")
    return manifest, cases, assignments


def source_anchors(source):
    anchors = {name: file_digest(source / name) for name in SOURCE_ANCHORS}
    anchors.update({str(f.relative_to(source)): file_digest(f)
                    for f in sorted((source / "candidate_freezes").glob("*.json"))})
    return anchors


def prepare_judging(source, output):
    """Reference every frozen outcome, including failures; never invoke the experiment model."""
    fixed_models()
    source, output = Path(source).resolve(), Path(output).resolve()
    require(source != output and not output.is_relative_to(source), "judge output must be a separate bundle")
    original, _, assignments = validate_frozen_source(source)
    config = read(ROOT / "docs/workflow_v2/protocol.json")
    manifest = {"schema_version": "workflow-v2-judgment-bundle-1", "run_id": output.name,
        "status": "prepared_judge_not_started", "source_bundle": str(source),
        "source_implementation_digest": original["implementation_digest"],
        "source_anchors": source_anchors(source), "models": config["models"],
        "generation_models": original["models"], "budget": original["budget"],
        "external_judge_budget": original["external_judge_budget"],
        "dataset_role": original["dataset_role"], "input_mode": original["input_mode"],
        "tool_calls_cap": 0, "pilot_cases": original["pilot_cases"], "assignment_count": len(assignments),
        "implementation_digest": implementation_digest(), "new_experiment_model_calls": 0,
        "files": {"candidate_freeze.json": file_digest(source / "candidate_freeze.json")},
        "scientific_confirmatory_claim_allowed": False, "human_verified": False}
    write_once(output / "candidate_freeze.json", read(source / "candidate_freeze.json"))
    write_once(output / "manifest.json", manifest)
    snapshot_implementation(output / "implementation_snapshot.zip")
    return manifest


def validate_judge_bundle(path):
    path = Path(path).resolve()
    manifest = read(path / "manifest.json")
    require(manifest["implementation_digest"] == implementation_digest(), "judge implementation drift")
    config = read(ROOT / "docs/workflow_v2/protocol.json")
    require(manifest["models"] == config["models"], "judge model configuration drift")
    source = Path(manifest["source_bundle"])
    require(source != path and not path.is_relative_to(source), "judge output overlaps source")
    require(manifest["source_anchors"] == source_anchors(source), "source anchors changed")
    original, cases, assignments = validate_frozen_source(source)
    require(manifest["generation_models"] == original["models"] and
            manifest["source_implementation_digest"] == original["implementation_digest"], "generation provenance changed")
    require(manifest["external_judge_budget"] == original["external_judge_budget"], "judge budget changed")
    require(manifest["assignment_count"] == len(assignments) and manifest["pilot_cases"] == len(cases),
            "judge matrix incomplete")
    require(file_digest(path / "candidate_freeze.json") == manifest["files"]["candidate_freeze.json"] and
            read(path / "candidate_freeze.json") == read(source / "candidate_freeze.json"), "judge input freeze drift")
    require(not (path / "runtime").exists(), "new generation evidence in judge-only bundle")
    return manifest, cases, assignments
