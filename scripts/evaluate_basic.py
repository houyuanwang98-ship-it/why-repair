#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_prediction(pred_dir, item_id):
    path = Path(pred_dir) / f"{item_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred-dir", required=True)
    args = parser.parse_args()

    gold_rows = read_jsonl(args.gold)
    total = 0
    missing = 0
    step_correct = 0
    type_correct = 0

    for row in gold_rows:
        pred = load_prediction(args.pred_dir, row["id"])
        if pred is None:
            missing += 1
            continue

        total += 1
        pred_first = pred.get("first_invalid_step", {}).get("step_id")
        pred_type = pred.get("first_invalid_step", {}).get("error_type")

        gold_first = row.get("gold_first_invalid_step")
        gold_type = row.get("gold_error_type")

        is_step_correct = pred_first == gold_first
        is_type_correct = pred_type == gold_type
        step_correct += int(is_step_correct)
        type_correct += int(is_type_correct)

        print(
            json.dumps(
                {
                    "id": row["id"],
                    "pred_first_invalid_step": pred_first,
                    "gold_first_invalid_step": gold_first,
                    "first_invalid_step_correct": is_step_correct,
                    "pred_error_type": pred_type,
                    "gold_error_type": gold_type,
                    "error_type_correct": is_type_correct,
                },
                ensure_ascii=True,
            )
        )

    print("")
    print(f"evaluated: {total}")
    print(f"missing_predictions: {missing}")
    if total:
        print(f"first_invalid_step_accuracy: {step_correct / total:.3f}")
        print(f"error_type_accuracy: {type_correct / total:.3f}")


if __name__ == "__main__":
    main()
