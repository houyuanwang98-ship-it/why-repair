# Annotation Guideline

This project studies natural-language algebra proof diagnosis and minimal
repair. Each example contains a theorem and a flawed proof.

## Main labels

### first_invalid_step

The first proof step that does not follow from the theorem assumptions,
definitions, earlier valid steps, or a valid theorem application.

Use 1-based indexing.

If the proof has no error, use null.

### error_type

Choose exactly one label:

- quantifier_error
- missing_assumption
- theorem_misuse
- algebraic_invalidity
- proof_gap
- target_shift
- false_generalization
- no_error

## Label definitions

### quantifier_error

The proof changes the order or scope of quantifiers, or proves a weaker claim
than required.

### missing_assumption

The theorem statement or proof application lacks a condition required by the
argument.

### theorem_misuse

The proof cites or applies a theorem in a way that does not match the theorem's
hypotheses or conclusion.

### algebraic_invalidity

The proof performs an invalid algebraic operation, uses an undefined operation,
or assumes a structure is well-defined when it has not been established.

### proof_gap

A key intermediate claim is asserted without adequate justification, but the
theorem may still be true.

### target_shift

The proof changes the goal and proves a different statement.

### false_generalization

The proof uses an argument that would imply a false stronger statement.

### no_error

The proof is valid as written.

## minimal_repair

The smallest change that makes the proof valid. Prefer:

1. Insert one missing step.
2. Add one missing condition if the theorem statement is incomplete.
3. Replace one misused theorem with a valid theorem.
4. Add a well-definedness check.

Do not rewrite the whole proof unless a local repair is impossible.

## M2 annotation contract addendum

M2 independent annotations use `schema_version: "m2.2"`. The authoritative
portable shape is `schemas/m2_benchmark_v0_2.schema.json`; the executable
cross-file checks are in `scripts/m2_benchmark.py`.

The allowed state combinations are:

| validity_status | error_type | locations | repair | counterexample |
|---|---|---|---|---|
| `valid` | `no_error` | both null | null | `not_applicable`, certificate null |
| `valid_with_gap` | `proof_gap` | gap required, invalid null | nonempty | `not_applicable`, certificate null |
| `invalid` | concrete invalid label | invalid required; an earlier gap may also be recorded | nonempty | valid only with a structured certificate |
| `undetermined` | `undetermined` | both null | null | `undetermined`, certificate null |

A valid counterexample certificate must identify whether it refutes a local
node or the original theorem, bind the exact claim, record concrete
assignments, check every source assumption exactly once with evidence, confirm
that the target is false, and record the verification method. A free-text
example in `notes` is not a valid certificate.

The proposed conversion from these benchmark labels to M1 v0.3 runtime labels
is documented in `docs/milestones/M02_label_mapping.md`. It is not automatic
and requires approval from both project members.
