"""Shared node segmentation and node-id mapping helpers for OPC mapping review.

Batch-001 calibration exposed segmentation noise (Markdown separators emitted
as proof nodes). ``clean_nodes`` is the canonical segmentation used by both the
node-annotation remediation and the review-transfer / supplemental-import
builders, so a rebuilt pipeline always reproduces the on-disk artifacts.
"""

from __future__ import annotations

import re

SEPARATOR = re.compile(r"^[-=#*_~.]{3,}$")


def clean_nodes(text: str) -> list[dict]:
    """Segment a proof into nodes, dropping separators and empty segments."""
    boundaries = {0, len(text)}
    for match in re.finditer(r"\n\s*\n+", text):
        boundaries.add(match.start())
        boundaries.add(match.end())
    for match in re.finditer(r"(?<=[.!?])\s+(?=[A-Z])", text):
        boundaries.add(match.start())
        boundaries.add(match.end())
    points = sorted(boundaries)
    result: list[dict] = []
    for left, right in zip(points, points[1:]):
        raw = text[left:right]
        stripped = raw.strip()
        if not stripped:
            continue
        if SEPARATOR.match(stripped):
            continue
        start = left + len(raw) - len(raw.lstrip())
        end = right - (len(raw) - len(raw.rstrip()))
        result.append({"node_id": f"n{len(result) + 1}", "start_char": start,
                       "end_char": end, "text": text[start:end]})
    return result


def locate(items: list[dict], offset: int | None) -> str | None:
    if offset is None:
        return None
    for item in items:
        if item["start_char"] <= offset < item["end_char"]:
            return item["node_id"]
    following = [item for item in items if item["start_char"] > offset]
    return following[0]["node_id"] if following else items[-1]["node_id"]


def remap_node_id(node_id: str | None, old_nodes: list[dict], new_nodes: list[dict]) -> str | None:
    """Translate a reviewed node id across a re-segmentation using char offsets."""
    if node_id is None or node_id == "proof_end":
        return node_id
    for node in old_nodes:
        if node["node_id"] == node_id:
            return locate(new_nodes, node["start_char"])
    raise ValueError(f"node {node_id} not found in old segmentation")
