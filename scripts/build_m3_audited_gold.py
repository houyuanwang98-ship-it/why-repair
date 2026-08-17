import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl"
OUTPUT = ROOT / "data/benchmarks/m3/gold/evaluator_pilot_v1_audited.jsonl"
FALSE_THEOREMS = {"m2-021", "m2-022", "m2-023", "m2-024", "m2-026", "m2-029", "m2-043", "m2-048"}


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()]
    by_id = {row["proof_id"]: row for row in rows}

    by_id["m2-015"].update(
        gold_validity_status="valid",
        gold_error_type="no_error",
        gold_first_gap_step=None,
        gold_minimal_repair=None,
    )
    by_id["m2-015"]["gold_nodes"][1]["verdict_group"] = "accepted"

    by_id["m2-037"].update(
        gold_validity_status="invalid",
        gold_error_type="theorem_misuse",
        gold_first_gap_step=None,
        gold_first_invalid_step=1,
        gold_minimal_repair="Replace the circular restatement with an independent derivation.",
    )
    by_id["m2-037"]["gold_nodes"][0]["verdict_group"] = "invalid"
    by_id["m2-037"]["gold_nodes"][1]["verdict_group"] = "invalid"

    for row in rows:
        row["m3_gold_schema_version"] = "m3-evaluator-gold-0.2-audited"
        row["gold_first_gap_applicable"] = True
        row["gold_first_invalid_applicable"] = row["proof_id"] not in FALSE_THEOREMS

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
