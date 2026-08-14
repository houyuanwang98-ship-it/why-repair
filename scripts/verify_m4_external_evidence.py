"""Fail-closed verification for M4 external human and prospective-blind evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_ssh_signature(payload: Path, signature: Path, allowed_signers: Path, identity: str) -> bool:
    if not all(path.is_file() for path in (payload, signature, allowed_signers)) or not identity:
        return False
    try:
        completed = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(allowed_signers), "-I", identity,
             "-n", "why-repair-m4", "-s", str(signature)],
            input=payload.read_bytes(), capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def verify_signoffs(packet: dict) -> bool:
    archive = ROOT / packet["review_target"]["archive_file"]
    if not archive.is_file() or digest(archive) != packet["review_target"]["archive_sha256"]:
        return False
    if packet.get("status") != "complete" or len(packet.get("signoffs", [])) != 2:
        return False
    identities = set()
    for item in packet["signoffs"]:
        if item.get("decision") != "pass" or len(set(item.get("reviewed_sample_ids", []))) != 11:
            return False
        if item.get("signature_method") != "ssh":
            return False  # v1 executable verifier supports SSH signatures only; fail closed otherwise.
        identity = item.get("reviewer_id")
        if not identity or identity in identities:
            return False
        identities.add(identity)
        signature = ROOT / item.get("detached_signature_file", "")
        allowed = ROOT / item.get("allowed_signers_file", "")
        if not verify_ssh_signature(archive, signature, allowed, identity):
            return False
    return True


def verify_blind_run(record: dict) -> bool:
    required = ("challenge_file", "candidate_file", "gold_file")
    if record.get("status") != "revealed_and_scored" or not all(record.get(key) for key in required):
        return False
    paths = {key: ROOT / record[key] for key in required}
    if not all(path.is_file() for path in paths.values()):
        return False
    if any(digest(paths[key]) != record.get(key.replace("_file", "_sha256")) for key in required):
        return False
    timeline = record.get("timeline", {})
    return bool(
        timeline.get("challenge_sealed_at")
        and timeline.get("candidate_locked_at")
        and timeline.get("gold_revealed_at")
        and timeline["challenge_sealed_at"] < timeline["candidate_locked_at"] < timeline["gold_revealed_at"]
        and isinstance(record.get("discovery_rate"), (int, float))
        and 0 <= record["discovery_rate"] <= 1
    )

