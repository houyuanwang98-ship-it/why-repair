# Theorem Retrieval Optimization Roadmap

This document describes practical follow-up work for theorem retrieval after
the current node-level retrieval baseline. It focuses first on improvements
that do not require expanding the theorem bank or training a new model.

## Current baseline

The current deterministic checker already provides:

- proof-step node classification;
- a node-level retrieval switch;
- structured proof obligations in the form `Gamma |- Goal`;
- conservative direct-predecessor selection;
- normalization of common mathematical surface forms;
- topic, domain, and global candidate fallback;
- field-weighted keyword scoring;
- an explainable score breakdown; and
- a strict boundary between retrieval evidence and proof verification.

This baseline is intentionally simple. It is useful for measuring retrieval
behavior, but it does not yet determine whether a retrieved theorem is
applicable to the current proof state.

## Optimization goals

Future work should optimize four outcomes:

1. Retrieve fewer irrelevant rules.
2. Place a sufficient rule or rule set in the top few results.
3. Avoid retrieval calls when the local obligation is already closed.
4. Preserve soundness by requiring a verifier to check rule applicability.

## Phase 1: Improve deterministic query construction

### 1.1 Infer real proof dependencies

The current fallback selects the most recent accepted node. This is a useful
baseline but is not a complete dependency extractor.

Add dependency signals from:

- explicit references such as `by Step 3`;
- repeated mathematical objects and expressions;
- conclusion-to-premise term overlap;
- discourse markers such as `therefore`, `from`, and `using`;
- scope introduced by assumptions and case splits; and
- known proof patterns such as contradiction and induction.

The extractor should return multiple predecessors when required, together with
a confidence score and an explanation for each selected edge.

Suggested output:

```json
{
  "depends_on": [3, 5],
  "dependency_evidence": [
    {
      "node_id": 3,
      "reason": "explicit_reference",
      "confidence": 1.0
    },
    {
      "node_id": 5,
      "reason": "shared_expression",
      "confidence": 0.74
    }
  ]
}
```

### 1.2 Add operation labels

Infer the mathematical operation performed between a predecessor and the
current goal. Initial labels can include:

```text
substitution
cancellation
multiply_both_sides
divide_both_sides
associative_rewrite
inverse_application
identity_simplification
definition_expansion
contradiction
case_split
induction_step
```

Operation labels should become part of the retrieval query. They often carry
more information than short goals such as `x = y`.

### 1.3 Normalize formula structure

Replace purely lexical normalization with a lightweight expression parser for
common algebraic formulas. The parser should identify:

- equality and inequality relations;
- function application;
- products, sums, powers, and inverses;
- repeated factors on both sides of an equality;
- bound and free variables; and
- expression trees independent of variable names.

For example, both of the following should share a structural signature:

```text
a*x = a*y
u*p = u*q
```

Possible signature:

```text
equality(product(V0,V1), product(V0,V2))
```

This makes cancellation rules retrievable without relying on specific variable
names.

## Phase 2: Improve candidate filtering and ranking

### 2.1 Replace static topic aliases with a hierarchy

The current aliases are manually configured. Replace them with a small topic
hierarchy that supports parent, child, and related topics.

Example:

```text
algebra
  groups
  rings
    fields
  linear_algebra
```

Candidate filtering can then distinguish:

- exact topic matches;
- ancestor or descendant matches;
- related-topic matches; and
- genuine topic conflicts.

### 2.2 Check premise satisfiability

After initial retrieval, compare each rule's `conditions` with the proof state.
Classify every condition as:

```text
satisfied
derivable
missing
contradicted
unknown
```

Use this classification for reranking. A rule with a high lexical score but an
unsatisfied essential condition should rank below a rule whose conditions are
already available.

Suggested score extension:

```text
final score
  = retrieval score
  + satisfied-condition bonus
  + derivable-condition bonus
  - missing-condition penalty
  - contradicted-condition penalty
```

### 2.3 Retrieve rule sets, not only individual rules

Some obligations require a short chain rather than one theorem. For example:

```text
nonzero inverse
  -> associativity
  -> inverse identity
  -> multiplicative identity
```

Add bounded bridge search over rule conclusions and conditions. The first
version should use a small depth limit, such as two or three rules, and prefer
the shortest chain whose conditions are available.

### 2.4 Add diversity to Top K

Near-duplicate rules from different books can occupy all Top K positions.
Cluster candidates by normalized conclusion, operation label, or rule family,
then limit the number of candidates from one cluster.

The output should preserve source alternatives without allowing them to crowd
out different proof strategies.

### 2.5 Calibrate retrieval confidence

Raw keyword scores are not probabilities. Add confidence features such as:

- margin between Top 1 and Top 2;
- fraction of goal tokens matched;
- fraction of required conditions satisfied;
- retrieval scope used;
- candidate-pool size; and
- agreement between lexical and structural ranking.

The system should return `no_reliable_candidate` when confidence is below a
calibrated threshold instead of always presenting the highest-scoring rule as
useful.

## Phase 3: Connect retrieval to verification and repair

### 3.1 Add a rule applicability checker

The applicability checker should attempt to instantiate a candidate rule with
terms from the proof state. It should verify:

- type or domain compatibility;
- substitution consistency;
- required assumptions;
- the direction of the implication or rewrite; and
- whether the instantiated conclusion matches the current goal.

Only a successful applicability check may contribute to closing a node.

### 3.2 Separate justification, diagnosis, and repair retrieval

Add an explicit retrieval intent:

```text
justify_step
bridge_to_goal
check_preconditions
diagnose_misuse
repair_gap
```

Each intent should search and rank different theorem-bank fields. For example,
`check_preconditions` should prioritize `conditions`, while `repair_gap` should
prioritize `bridge_lemmas` and `repair_templates`.

### 3.3 Generate minimal repairs from verified bridges

Repair generation should use only rules whose applicability has been checked.
Prefer:

1. naming a missing rule;
2. inserting one bridge lemma;
3. inserting a short verified rule chain; and
4. replacing an invalid step only when local insertion cannot repair it.

The generated repair should retain the original proof structure whenever
possible.

## Phase 4: Add learned retrieval

Learned retrieval should be introduced only after the deterministic evaluation
pipeline is stable.

### 4.1 Build training pairs

Create examples of:

```text
(proof state, useful rule)          positive
(proof state, accessible rule)      ordinary negative
(proof state, similar wrong rule)   hard negative
```

Positive labels can come from verified rule use, annotations, and accepted
minimal repairs. Hard negatives should come from high-ranked candidates that
fail applicability checking.

### 4.2 Train a two-stage retriever

A practical architecture is:

```text
dense or sparse retriever -> Top 50
cross-encoder reranker     -> Top 5
applicability checker      -> verified candidates
```

The retriever should encode the whole proof state, not only the goal. The
reranker should receive the proof state and complete candidate rule together.

### 4.3 Prevent evaluation leakage

Split data by theorem dependency or source document rather than by random proof
step alone. Test the ability to retrieve rules that were not used in training,
and ensure that a proof cannot retrieve declarations introduced after it when
evaluating a formal corpus.

## Phase 5: Improve theorem-bank coverage

Knowledge-base expansion should be measured separately from retrieval quality.
Recommended additions include:

- primitive algebraic laws;
- common bridge lemmas;
- theorem preconditions;
- common misuse patterns;
- normalized conclusions;
- operation labels; and
- equivalence classes for duplicate rules.

When a retrieval failure occurs, classify it as one of:

```text
query construction failure
dependency selection failure
candidate filtering failure
ranking failure
applicability failure
knowledge-base coverage failure
```

This prevents every failed retrieval from being incorrectly attributed to a
missing theorem-bank entry.

## Evaluation plan

Create a fixed node-level benchmark before changing ranking weights. It should
contain nodes that:

- must not trigger retrieval;
- need one direct theorem;
- need a bridge lemma;
- need several premises;
- misuse a theorem;
- contain irrelevant historical context; and
- have close but incorrect distractor rules.

Track at least these metrics:

```text
retrieval trigger precision and recall
Recall@1, Recall@3, Recall@5
MRR
nDCG@K
irrelevant candidates in Top K
direct-predecessor accuracy
condition-satisfaction accuracy
verified rule applicability rate
first-gap and first-invalid accuracy
end-to-end node closure rate
average candidate-pool size
average retrieval calls per proof
```

Evaluation should report results by node type, topic, retrieval scope, and
failure category. End-to-end proof success should be reported separately from
retrieval metrics.

## Recommended implementation order

The next practical sequence is:

1. Add operation labels and structural equality signatures.
2. Add dependency evidence and multi-predecessor selection.
3. Implement condition matching and applicability reranking.
4. Add duplicate clustering and confidence thresholds.
5. Add bounded rule-chain retrieval.
6. Build the fixed node-level benchmark and tune weights only against it.
7. Add learned retrieval after deterministic error categories are stable.
8. Expand theorem-bank coverage based on measured coverage failures.

The highest-value next change is condition satisfiability reranking. The current
retriever can already place relevant rules in Top K, but it cannot reliably
distinguish a merely similar theorem from one whose hypotheses are available in
the current proof state.
