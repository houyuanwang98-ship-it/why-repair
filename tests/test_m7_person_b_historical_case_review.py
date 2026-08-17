import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/benchmarks/m7/human_review/person_b_cases_026_050_v0_1.json"

def test_person_b_cases_026_050_accounting():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    records = payload["records"]
    assert len(records) == 25
    assert [r["sample_id"] for r in records] == [f"m2-{i:03d}" for i in range(26, 51)]
    assert sum(r["person_b_verification"] == "confirmed" for r in records) == 20
    assert [r["sample_id"] for r in records if r["person_b_verification"] == "correction_proposed"] == [
        "m2-028", "m2-032", "m2-038", "m2-042", "m2-044"
    ]

