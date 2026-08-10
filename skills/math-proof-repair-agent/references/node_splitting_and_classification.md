# Node Splitting and Classification Standard

## Contents

- [Node Splitting Rules](#node-splitting-rules)
- [Node Classification Rules](#node-classification-rules)
- [Classification Priority](#classification-priority)

## Node Splitting Rules

Apply the rules in the order given. A split is valid only when every resulting
piece expresses a usable proof unit. After splitting, run the fragment-merge
safeguards and then the safe period-resplit pass.

### 1. Base segmentation

First split on strong sentence and list boundaries:

- sentence-ending punctuation;
- semicolons that separate complete clauses;
- explicit ordered proof-step or case labels;
- line breaks that separate complete mathematical statements.

Do not split inside mathematical notation, decimal numbers, citations, or
parenthesized expressions solely because they contain punctuation.

### 2. Cause-and-effect connectors

Connectors such as `therefore`, `thus`, `hence`, `consequently`, `so`, and
`as a result` may begin a new node when the material on both sides is a
complete clause.

Do not split a connector from the conclusion it introduces. Do not split
inside a fixed phrase or when either side lacks a subject-predicate structure.

Example:

```text
a is nonzero; therefore a has an inverse.
```

may become two nodes, while `therefore x` alone must remain attached to its
surrounding clause.

### 3. Conditional connectors

Connectors such as `if`, `unless`, `provided that`, `suppose`, and `assume`
introduce conditions. Split a condition from its consequence only when both
sides become complete usable proof units.

Keep an incomplete condition with its consequence:

```text
If a = 0, then ax = ay.
```

Do not emit `If a = 0,` as a standalone node unless the proof deliberately
uses that condition as a case assumption and the next node states the case
consequence.

### 4. Comma safeguards

A comma is not, by itself, a node boundary. Split at a comma only when a
recognized logical connector is present and both resulting pieces are
complete clauses.

Never split commas used in:

- tuples, sets, function arguments, or coordinate lists;
- number ranges and enumerations such as `1, 2, ..., n`;
- dependent introductory phrases;
- a condition whose consequence is required to complete the sentence;
- mathematical expressions whose punctuation is syntactic rather than prose.

### 5. Fragment-merge safeguards

After tentative splitting, merge any unusable fragment:

- If a node starts with punctuation, merge it with the next node.
- If a node ends with punctuation but lacks a subject-predicate structure,
  merge it with the previous node when possible.
- If a node has neither boundary punctuation nor a subject-predicate
  structure, merge it with the next node.
- Preserve mathematical relations such as `x in A`, `a = b`, and `x < y` as
  predicate evidence.
- Never leave a bare connector, qualifier, citation, or dependent clause as a
  standalone node.

Example:

```text
We consider two cases. Assume x is in A.
```

contains two complete nodes. By contrast, `If a = 0,` remains attached unless
it is intentionally used as a standalone case assumption.

### 6. Safe period resplitting

If a node still contains multiple sentences, split at a period only when both
pieces have usable subject-predicate structure. Protect decimal points,
abbreviations, theorem numbering, and ellipses.

## Node Classification Rules

Every node receives exactly one type from the following closed set:

```text
definition
introduction
assumption
claim
calculation_step
conclusion
```

### Definition

Use `definition` only when the node creates a mathematical term, object,
function, set, or notation.

Examples:

```text
Let A := lim sup a_n.
Let f(x) = sqrt(2 + sqrt(x)).
Define E0 as the set of interior points of E.
```

Using an existing definition or restating an object from the theorem is not a
new definition.

### Introduction

Use `introduction` when the node restates known information or organizes the
proof without asserting a new intermediate result. This includes:

- restating a theorem hypothesis or named object;
- citing a known theorem or an earlier established result;
- introducing a variable or notation without defining a new concept;
- announcing a proof strategy;
- reductive declarations such as `It suffices to show that ...`, `It remains
  to prove that ...`, or `The problem reduces to ...`.

Examples:

```text
Let d be the metric on E.
Recall that every compact subset of a metric space is closed.
Use l to denote the limit of the sequence.
It suffices to show that the sequence is bounded and monotone.
```

A reductive declaration is `introduction`, not `claim`, because it changes the
proof target rather than asserting that the reduced target has been proved.

### Assumption

Use `assumption` for a hypothesis, case condition, contradiction premise, or
temporary premise.

Examples:

```text
Assume for contradiction that p is in A.
If x is a limit point of E, ...
Case 1: A and B are finite.
Otherwise, suppose x is negative.
```

### Claim

Use `claim` for an explicit declaration of a proposition that the proof will
establish. Accepted declaration forms include:

- direct: `We show that ...`, `We prove that ...`, `We claim that ...`;
- goal: `Our goal is to prove that ...`, `We aim to establish that ...`;
- sectional: `First we show that ...`, `As a first step, we prove that ...`.

Examples:

```text
We claim that the sequence converges.
Our goal is to prove that K is compact.
As a first step, we show that Q is dense.
```

Do not classify reductive forms such as `It suffices to show that ...` as
claims; they are introductions.

### Calculation step

Use `calculation_step` when the node performs an algebraic, inequality,
logical, limit, or symbolic transformation. The node must contain an actual
inference chain, not merely a single displayed equality or assertion.

Typical evidence includes:

- chained equalities or inequalities;
- an equivalence transformation;
- substitution, expansion, cancellation, or limit evaluation;
- applying a named rule to derive a new formula;
- a contradiction derived from earlier formulas.

Examples:

```text
By the triangle inequality, d(x,z) <= d(x,y) + d(y,z) < epsilon.
This is equivalent to |a| <= |a-b| + |b|.
Taking n to infinity gives L = f(L).
```

A lone statement such as `B(p,r) intersect E is empty` is normally a
`conclusion`, unless its surrounding text supplies an explicit derivation.

### Conclusion

Use `conclusion` for a derived mathematical statement that does not fit a
higher-priority type. This is the mandatory catch-all category.

Examples:

```text
Therefore every limit point of E is in E.
Hence K is compact.
This is a contradiction.
No.
```

## Classification Priority

When multiple labels appear plausible, apply this exact priority:

1. `definition`
2. `claim`
3. `assumption`
4. `introduction`
5. `calculation_step`
6. `conclusion`

Declaration syntax takes precedence over content keywords. For example,
`We show that K is compact` is a `claim`, not a `conclusion`. Reductive
declarations remain `introduction` by explicit exception. Anything not
captured by the first five categories must be `conclusion`.
