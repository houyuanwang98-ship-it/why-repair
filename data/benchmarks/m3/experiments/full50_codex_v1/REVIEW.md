# M3 full-50 Codex-hosted run

## Status

The frozen run completed with 50 predictions and zero pending adjudications.
Gold was opened only after the prediction session reached `pending_count=0`.
This is a non-blind engineering result and is not a publication score.

## Metrics

| Metric | Result |
|---|---:|
| Prediction coverage | 1.000 |
| Proof validity accuracy / macro-F1 | 0.940 / 0.940 |
| Error type accuracy / macro-F1 | 0.920 / 0.909 |
| First gap exact accuracy | 0.818 |
| First invalid exact accuracy | 0.654 |
| Node type accuracy / macro-F1 | 0.918 / 0.943 |
| Node verdict accuracy / macro-F1 | 0.908 / 0.838 |
| Dependency precision / recall / F1 | 0.887 / 0.948 / 0.917 |

## Interpretation

Proof-level validity and error taxonomy are strong on this small curated set.
The main weakness is first-invalid localization: false global theorems often
receive their invalid marker at the first explicit erroneous conclusion rather
than node 1, while the frozen Gold convention assigns node 1 when the theorem
is globally refuted before process review. This policy mismatch accounts for
eight of the localization disagreements.

The run must now receive human audit on all validity, error-type, and
localization disagreements listed in `ERROR_ANALYSIS.md`. No prediction or
rule should be changed inside this frozen run.
