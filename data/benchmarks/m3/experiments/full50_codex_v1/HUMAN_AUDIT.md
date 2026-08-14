# M3 full-50 disagreement human audit

Status: complete (Person B review, 2026-08-14, Asia/Shanghai).

This audit reviews every proof-validity, error-type, and first-location
disagreement in `ERROR_ANALYSIS.md`. It does not alter the frozen predictions,
Gold, or reported scores.

## Decisions

| Sample(s) | Disagreement | Audit decision |
|---|---|---|
| `m2-015` | `valid` vs Gold `valid_with_gap`; missing first gap 2 | Prediction error. Positivity of `a/b` needs the unstated product-of-positive-numbers inference. The frozen gap convention is applied correctly. |
| `m2-037` | `valid` vs Gold `valid_with_gap`; missing first gap 1 | Prediction error. Node 1 restates the theorem and is circular rather than a proof. The frozen gap convention is applied correctly. |
| `m2-028` | predicted `valid_with_gap` vs Gold `invalid` at node 2 | Benchmark issue. For every integer `n`, `n(n-1) >= 0`, so `n^2 >= n` is true. The supplied proof has a gap, but the frozen M2 Gold incorrectly labels the theorem/proof invalid. Preserve the row and score for reproducibility; correct it only in a future benchmark version. |
| `m2-036` | `theorem_misuse` vs Gold `false_generalization` | Prediction taxonomy error. Checking only `n=1,2` and concluding a universal statement is insufficient generalization; the Gold taxonomy is applied correctly. |
| `m2-021`, `m2-022`, `m2-023`, `m2-024`, `m2-026`, `m2-029`, `m2-043`, `m2-048` | predicted first invalid 2 vs Gold 1 | Prediction-policy mismatch, not a Gold ambiguity under the frozen convention. Each theorem has a valid global counterexample, so M2 terminates process review and assigns position 1. The prediction instead marked the first explicit bad conclusion. |

## Disposition

- All 3 validity disagreements, all 4 error-type disagreements, all 9
  first-invalid disagreements, and all 3 first-gap disagreements are covered.
- No frozen artifact was changed after seeing Gold.
- `m2-028` is registered as a known benchmark limitation. It prevents treating
  the engineering score as a publication score, but does not prevent freezing
  the reproducible M3 Evaluator v1 pipeline and run.

