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
