# Full-50 disagreement audit queue

## Proof validity disagreements

- `m2-015`: Gold `valid_with_gap`; prediction `valid`.
- `m2-028`: Gold `invalid`; prediction `valid_with_gap`.
- `m2-037`: Gold `valid_with_gap`; prediction `valid`.

## Error-type disagreements

- `m2-015`: Gold `proof_gap`; prediction `no_error`.
- `m2-028`: Gold `algebraic_invalidity`; prediction `proof_gap`.
- `m2-036`: Gold `false_generalization`; prediction `theorem_misuse`.
- `m2-037`: Gold `proof_gap`; prediction `no_error`.

## First-invalid localization disagreements

The following globally false statements have Gold position 1 but were marked
at the first explicit erroneous conclusion, position 2:

- `m2-021`, `m2-022`, `m2-023`, `m2-024`
- `m2-026`, `m2-029`, `m2-043`, `m2-048`

`m2-028` has Gold invalid position 2, while the prediction classified node 2
as a repairable gap and therefore emitted no invalid position.

## First-gap localization disagreements

- `m2-015`: Gold position 2; prediction none.
- `m2-028`: Gold none; prediction position 2.
- `m2-037`: Gold position 1; prediction none.

## Required human audit

For each item above, record whether the prediction is wrong, the Gold policy
is being applied correctly, or the case exposes a genuine annotation-policy
ambiguity. Preserve the frozen predictions regardless of the audit outcome.
