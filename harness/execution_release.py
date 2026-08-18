"""Validation for the repository-owner M6/M7 execution authorization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


RELEASE_VERSION = "m6-m7-user-execution-release-0.1"


def release_allows(release: Mapping[str, Any] | None, milestone: str) -> bool:
    """Accept only the exact scoped waiver contract; never infer scientific approval."""
    if milestone not in {"m6", "m7"} or not isinstance(release, Mapping):
        return False
    required = {
        "schema_version", "status", "authorized_at", "authority", "user_instruction",
        "cryptographic_signature_policy", "m6_execution_allowed", "m7_execution_allowed",
        "scientific_claim_allowed", "does_not_claim",
    }
    return (
        set(release) == required
        and release.get("schema_version") == RELEASE_VERSION
        and release.get("status") == "active"
        and release.get("authority") == "repository_owner_active_conversation"
        and release.get("cryptographic_signature_policy") == "waived_for_current_project_scope"
        and release.get(f"{milestone}_execution_allowed") is True
        and release.get("scientific_claim_allowed") is False
        and isinstance(release.get("does_not_claim"), list)
        and "publication-grade formal completion" in release["does_not_claim"]
    )
