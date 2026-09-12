# Experiment 1: full 600-case results

Strict success means the blind judge marked the output valid, rigorous, and problem-preserving.

| Method | Strict success | Rate | Valid | Rigorous | Preserved |
|---|---:|---:|---:|---:|---:|
| original | 166/596 | 27.9% | 169 | 167 | 576 |
| direct_rewrite | 365/596 | 61.2% | 365 | 400 | 584 |
| self_refine | 366/596 | 61.4% | 366 | 404 | 584 |
| generator_critic | 370/596 | 62.1% | 370 | 409 | 584 |
| full_system | 377/596 | 63.3% | 377 | 418 | 584 |

## Structured-gold invalid subset

This subset contains the 216 inputs whose original project gold label is `invalid`.

| Method | Strictly valid output | Rate |
|---|---:|---:|
| original | 7/213 | 3.3% |
| direct_rewrite | 55/213 | 25.8% |
| self_refine | 55/213 | 25.8% |
| generator_critic | 56/213 | 26.3% |
| full_system | 56/213 | 26.3% |

## Interpretation boundary

These are AI-judged experimental measurements, not human gold labels for the newly generated repairs. The four repair workflows were produced together in one schema-constrained generator call per problem, so this run is an exploratory controlled prompted comparison; it is not yet an isolated compute-matched ablation. Human adjudication of a stratified output sample is required before using the numbers as a paper's headline claim.
