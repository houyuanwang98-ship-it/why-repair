# Experiment 1: full 600-case results

Strict success means the blind judge marked the output valid, rigorous, and problem-preserving.

| Method | Strict success | Rate | Valid | Rigorous | Preserved |
|---|---:|---:|---:|---:|---:|
| original | 167/600 | 27.8% | 170 | 168 | 580 |
| direct_rewrite | 367/600 | 61.2% | 367 | 402 | 588 |
| self_refine | 368/600 | 61.3% | 368 | 406 | 588 |
| generator_critic | 372/600 | 62.0% | 372 | 411 | 588 |
| full_system | 379/600 | 63.2% | 379 | 420 | 588 |

## Structured-gold invalid subset

This subset contains the 216 inputs whose original project gold label is `invalid`.

| Method | Strictly valid output | Rate |
|---|---:|---:|
| original | 7/216 | 3.2% |
| direct_rewrite | 56/216 | 25.9% |
| self_refine | 56/216 | 25.9% |
| generator_critic | 57/216 | 26.4% |
| full_system | 57/216 | 26.4% |

## Interpretation boundary

These are AI-judged experimental measurements, not human gold labels for the newly generated repairs. The four repair workflows were produced together in one schema-constrained generator call per problem, so this run is an exploratory controlled prompted comparison; it is not yet an isolated compute-matched ablation. Human adjudication of a stratified output sample is required before using the numbers as a paper's headline claim.
