# Error Diagnosis Optimization Roadmap

## 1. Current baseline

The checker currently provides:

- theorem-bank condition and conclusion checks;
- `satisfied_conditions`, `missing_conditions`, and `matched_conclusion`;
- coarse logical classes such as `repairable_gap`, `unsupported_inference`,
  `false_claim`, and `indeterminate`;
- deterministic checks for missing inverse or division preconditions, unsupported
  factor reordering, and false numeric equalities;
- a small set of conservative counterexample templates;
- dependency-aware propagation of `downstream_invalid`;
- separate `first_gap_step`, `first_invalid_step`, and
  `first_undetermined_step` fields;
- model adjudication when deterministic checks remain inconclusive; and
- an offline `--uncertain-policy undetermined` mode that disables model calls.

The model adjudicator receives a local obligation and must return exactly one
of:

```text
derivable
counterexample
undetermined
```

The system is therefore a hybrid prototype: deterministic checks run first,
and the model handles only unresolved obligations. The next improvements should
focus on structured expressions, executable evidence, and calibration instead
of adding more problem-specific string patterns.

## 2. Improve local algebra operation checking

### 2.1 Parse structured expressions

The current operation checker mainly uses normalized text and regular
expressions. Common algebraic expressions should instead be parsed into an
abstract syntax tree:

```text
a^{-1} * (a * x) = a^{-1} * (a * y)

Eq(
  Mul(Inv(a), Mul(a, x)),
  Mul(Inv(a), Mul(a, y))
)
```

Structural parsing would make checks independent of variable names, brackets,
and alternative multiplication notation.

### 2.2 Define operation preconditions

Maintain a structured precondition table for common operations:

| Operation | Required condition | Failure diagnosis |
| --- | --- | --- |
| Divide by `a` | `a != 0` or `a` is invertible | `missing_assumption` or `theorem_misuse` |
| Cancel a factor | The structure has the required cancellation law | `theorem_misuse` |
| Reorder factors | The structure or the elements commute | `algebraic_invalidity` |
| Multiply both sides | The operation is defined and applied consistently | `algebraic_invalidity` |
| Apply an inverse map | The map is invertible on the relevant range | `missing_assumption` |
| Square or take roots | Sign and implication-direction conditions hold | `algebraic_invalidity` |

The checker should emit structured evidence:

```json
{
  "operation": "cancel_left_factor",
  "source_expression": "a*x = a*y",
  "target_expression": "x = y",
  "required_conditions": ["a is cancellable"],
  "satisfied_conditions": [],
  "missing_conditions": ["a is cancellable"],
  "equivalence_preserved": false
}
```

### 2.3 Distinguish implication directions

Some transformations preserve only one direction. For example, `x = y`
implies `x^2 = y^2`, but the reverse implication does not generally hold. The
checker should record:

```text
forward_valid
backward_valid
equivalence_valid
```

This supports explicit diagnosis of converse errors and invalid equivalence
claims.

### 2.4 Replay small algebra steps

For calculation nodes, attempt a bounded replay using:

1. associativity;
2. identity laws;
3. inverse laws;
4. distributivity;
5. valid cancellation; and
6. substitution by accepted equalities.

A successful one-step replay may close a node. A short verified chain may be a
`repairable_gap`. A transformation that does not preserve the required
direction should be `unsupported_inference`.

## 3. Improve counterexample verification

### 3.1 Separate generation from verification

Counterexample handling should have two independent stages:

```text
candidate generation
  -> verify every theorem assumption
  -> verify that the conclusion is false
  -> record an execution trace
  -> false_theorem
```

The current built-in templates include prewritten verification explanations.
The model can also return a counterexample and an explanation, but model output
is not yet rechecked by an independent executor. The model or a template should
eventually generate candidates only; a deterministic verifier should decide
whether they are valid.

### 3.2 Add bounded finite-structure search

Prioritize structures that can be exhaustively enumerated:

- small integers and `Z/nZ`;
- small finite groups;
- small finite fields;
- low-dimensional vector spaces and matrices; and
- functions on small finite sets.

For example, ring claims can be tested in `Z/4Z` and `Z/6Z`, while elementary
group claims can be tested against a catalog of small groups.

### 3.3 Record counterexample provenance

Add fields such as:

```text
counterexample_source: template | model | finite_enumeration | solver
assumptions_verified: true | false
conclusion_refuted: true | false
verification_trace
```

Only evidence with `assumptions_verified=true` and
`conclusion_refuted=true` should produce a high-confidence `false_claim`.
Before independent verification is available, a model-proposed example should
preferably remain a `counterexample_candidate`.

### 3.4 Separate a bad proof from a false theorem

An invalid intermediate node does not imply that the theorem is false. The
checker should first attempt to:

1. replace the local step;
2. prove the conclusion through another rule chain; and
3. search for a counterexample under all original assumptions.

Only the third result can establish `false_theorem`.

## 4. Improve dependency propagation

### 4.1 Extract real dependency edges

The current conservative strategy uses explicit references or nearby accepted
nodes. Future dependency extraction should determine:

- which predecessor claims occur in the current expression;
- where objects and variables were introduced;
- whether the current step uses only global assumptions; and
- whether several predecessor claims are combined.

A node may have multiple dependencies:

```text
node 4 depends_on [1, 3]
```

`downstream_invalid` should propagate only when an invalid dependency is
actually necessary.

### 4.2 Distinguish hard and soft dependencies

Add dependency metadata:

```text
dependency_type: explicit | expression | semantic | heuristic
dependency_strength: hard | soft
```

A hard dependency is explicitly cited or required. A soft dependency may be
helpful, but the current claim might still have an independent proof. Automatic
invalidity propagation should follow hard dependencies only.

### 4.3 Retry after removing invalid context

When a selected predecessor is invalid, retry the obligation without that
claim:

```text
remove invalid predecessor
  -> rebuild the local obligation
  -> retry retrieval and verification
  -> closed / repairable_gap / downstream_invalid
```

This separates a proof presentation that uses a bad step from a claim that
cannot be established independently.

## 5. Sharpen the gap-versus-invalid boundary

### 5.1 Require verified evidence for `repairable_gap`

A node should be a repairable gap only when:

1. the goal follows from the original assumptions;
2. a verified rule or short rule chain is available;
3. every rule condition is satisfied;
4. no theorem assumption must be added; and
5. no existing mathematical claim must be changed.

Bound the bridge to one to three rules and record `bridge_length`.

### 5.2 Refine `unsupported_inference`

Add a `logic_subtype` field with values such as:

```text
premise_not_established
rule_precondition_failed
invalid_rewrite
wrong_implication_direction
type_or_domain_mismatch
unrelated_conclusion
```

`unrelated_conclusion` is the precise category for a step with no verified
connection to the assumptions, predecessors, or candidate rules.

### 5.3 Add confidence and evidence sources

Each diagnosis should report:

```json
{
  "logic_class": "unsupported_inference",
  "logic_subtype": "unrelated_conclusion",
  "diagnosis_confidence": "high",
  "evidence_sources": ["dependency_graph", "rule_applicability"],
  "alternative_diagnoses": []
}
```

Parsing, retrieval, and knowledge-coverage failures should lower confidence
instead of being reported as mathematical errors.

## 6. Improve model adjudication

### 6.1 Current fallback workflow

The model is called only after deterministic diagnosis remains inconclusive:

```text
Context_i |- Claim_i
  -> deterministic checks inconclusive
  -> model adjudication
       derivable
       counterexample
       undetermined
```

The structured result contains:

```text
decision
reasoning_summary
proof_outline
counterexample_description
counterexample_verification
confidence
```

Currently, `derivable` maps to `missing_bridge_lemma`, `counterexample` maps to
`false_theorem`, and `undetermined` maps to `undetermined / indeterminate`.

### 6.2 Replay model-proposed proofs

A `derivable` response should not immediately establish a gap. Split the
`proof_outline` into small steps and check:

1. which assumptions each step uses;
2. which theorem or rule is applied;
3. whether every rule condition is satisfied;
4. whether intermediate conclusions connect; and
5. whether the final statement exactly matches the claim.

Add fields such as:

```text
model_proof_replayed
verified_model_steps
failed_model_step
unverified_model_claims
```

Only a successfully replayed model proof should produce a high-confidence
`repairable_gap`. Otherwise, retain `undetermined`.

### 6.3 Independently verify model counterexamples

Parse a model-proposed counterexample into a structure and assignments:

```json
{
  "structure": "real_numbers",
  "assignments": {"a": 0, "x": 0, "y": 1}
}
```

Then evaluate every assumption and the negated conclusion independently. The
model's verification text is an explanation, not the final verifier.

### 6.4 Check adjudication consistency

For difficult obligations, bounded independent roles can be used:

```text
prover: attempt a proof
refuter: attempt a counterexample
judge: compare executable evidence
```

The final status must still depend on replayable evidence, not majority vote.
Conflicting, unverifiable outputs should remain `undetermined`.

### 6.5 Cache and limit model calls

Call the model only when:

- deterministic checking did not close the node;
- no explicit local algebra error was found;
- no verified built-in counterexample exists;
- the node is not `downstream_invalid`; and
- the normalized obligation is not cached.

Use `formal_obligation + retrieved_rule_ids + model_version` as a cache key.
Record call count, latency, token usage, and cache-hit rate.

### 6.6 Handle model failures explicitly

API failures, schema errors, truncated responses, and low-confidence results
should produce:

```text
status: undetermined
logic_class: indeterminate
repair_scope: manual_review
```

Record `model_failure_reason`; never fall back to `valid_with_gap`.

## 7. Separate system limitations from mathematical errors

Use explicit internal states:

```text
parse_failure
dependency_uncertain
retrieval_failure
knowledge_coverage_failure
verification_timeout
unsupported_operation
model_unavailable
model_output_invalid
model_evidence_unverified
```

These conditions must not map directly to `unsupported_inference` or
`false_claim`. Otherwise, checker limitations become false accusations against
the proof.

## 8. Evaluation metrics

Report at least:

- `repairable_gap` versus `unsupported_inference` accuracy;
- `logic_subtype` accuracy;
- first-gap, first-invalid, and first-undetermined accuracy;
- dependency-propagation precision and recall;
- counterexample validity rate;
- false-positive rate on correct proofs;
- errors caused by parser, retrieval, or knowledge coverage;
- model-proof replay success rate;
- model-counterexample independent verification rate;
- unresolved rate after model adjudication;
- average model calls, latency, and token cost per proof; and
- average minimal-repair length.

The benchmark should contain paired examples with the same surface topic but
different outcomes: valid gap, missing premise, theorem misuse, invalid rewrite,
unrelated conclusion, false theorem, and genuinely undetermined obligation.

## 9. Recommended implementation order

1. Add model failure reasons, evidence sources, and adjudication caching.
2. Add `logic_subtype` and calibrated diagnosis confidence.
3. Parse common algebra expressions into structured syntax trees.
4. Implement one-step replay and implication-direction checks.
5. Replay every model-proposed proof outline.
6. Independently verify model-proposed counterexamples.
7. Require a verified bounded rule chain for `repairable_gap`.
8. Extract hard, soft, and multi-predecessor dependencies.
9. Retry downstream nodes after removing invalid predecessors.
10. Add finite-group, modular-ring, and low-dimensional linear-algebra search.
11. Build a paired diagnosis benchmark and report metrics by error type.

The highest-priority next step is independent validation of model evidence:
proofs must be replayable, and counterexamples must be executable. Structured
expression parsing and local rule replay should follow because they support
both validation paths and reduce dependence on problem-specific text patterns.
