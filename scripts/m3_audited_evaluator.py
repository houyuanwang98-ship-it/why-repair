"""Evaluate audited M3 Gold without modifying the frozen v1 evaluator."""

from __future__ import annotations

import m3_evaluator as v1


def evaluate(gold_rows, prediction_rows):
    report, details = v1.evaluate(gold_rows, prediction_rows)
    pred_map = {v1.sample_id(row): row for row in prediction_rows}
    gap_pairs = []
    invalid_pairs = []
    for gold, detail in zip(gold_rows, details):
        pred = pred_map.get(v1.sample_id(gold), {})
        gap_applicable = gold.get("gold_first_gap_applicable", True)
        invalid_applicable = gold.get("gold_first_invalid_applicable", True)
        detail["first_gap_applicable"] = gap_applicable
        detail["first_invalid_applicable"] = invalid_applicable
        if gap_applicable:
            gap_pairs.append((gold.get("gold_first_gap_step"), v1.normalize_node_id(pred.get("first_gap_step"))))
        if invalid_applicable:
            invalid_pairs.append((gold.get("gold_first_invalid_step"), v1.normalize_node_id(pred.get("first_invalid_step"))))
    report["first_gap_localization"] = v1.localization_metrics(
        [gold for gold, _ in gap_pairs], [predicted for _, predicted in gap_pairs]
    )
    report["first_invalid_localization"] = v1.localization_metrics(
        [gold for gold, _ in invalid_pairs], [predicted for _, predicted in invalid_pairs]
    )
    return report, details
