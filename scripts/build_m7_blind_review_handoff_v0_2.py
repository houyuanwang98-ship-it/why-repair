"""Materialize pending A/B review forms without fabricating human decisions."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.m7_interactive_review import build_template  # noqa: E402


SOURCE = ROOT / "data/benchmarks/m7/interactive_engineering_v0_2/blind_review_plan.json"
OUT = ROOT / "human_review/m7_interactive_v0_2"


def build() -> dict[str, dict]:
    plan = json.loads(SOURCE.read_text(encoding="utf-8"))
    return {slot: build_template(plan, reviewer_slot=slot) for slot in ("person_a", "person_b")}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slot, value in build().items():
        (OUT / f"{slot}_blind_review.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
