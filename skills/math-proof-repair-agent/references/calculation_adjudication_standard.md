# Calculation Context and Adjudication Standard

## Responsibility boundary

The deterministic checker owns the active mathematical context. The model owns
the proposed calculation chain.

The checker must:

- infer the initial structure and its allowed axioms;
- propagate an unchanged context to the next node;
- update context when a node changes structure or adds a local condition;
- reject axioms outside the active context; and
- reject assumptions introduced by the model.

The model must:

- preserve the supplied source and target expressions;
- produce the shortest atomic calculation chain;
- use exact axiom names from `calculation_context.axioms`;
- list all required conditions; and
- return `undetermined` instead of inventing a rule or premise.

Before emitting a host obligation, the checker may deterministically replay a
complete simple relation. The accepted subset is exact rational numeric
arithmetic or comparison, or one atomic identity whose named axiom is present
in the active context, for example `x * 1 = x`. Parsing must cover the entire
expression. General variable rewrites, multi-step chains, functions, powers
outside the safe numeric subset, and missing axioms are not guessed and remain
host obligations.

## Calculation context

Each proof node receives:

```json
{
  "structure": "field",
  "carrier": "F",
  "operations": ["addition", "multiplication", "negation", "inverse"],
  "axioms": [
    "multiplicative_associativity",
    "multiplicative_identity",
    "multiplicative_inverse"
  ],
  "properties": ["commutative_multiplication"],
  "local_conditions": ["a is nonzero"],
  "source_node_ids": [],
  "inherited_from_node_id": 1,
  "context_changed": false,
  "change_reason": null
}
```

If a node does not change the structure or local conditions, inherit the prior
context. A structure declaration, case assumption, nonzero condition, or
invertibility condition updates the context. Context changes from invalid or
undetermined nodes are not propagated.

## Model decisions

```text
valid_transformation
repairable_gap
missing_precondition
invalid_transformation
context_mismatch
undetermined
```

- `valid_transformation` requires exactly one atomic step and becomes `closed`.
- `repairable_gap` requires at least two atomic steps and becomes
  `missing_bridge_lemma`.
- `missing_precondition` becomes `missing_assumption`.
- `invalid_transformation` becomes `algebraic_invalidity`.
- `context_mismatch` or an unavailable used axiom becomes `theorem_misuse`.
- incomplete, endpoint-changing, or unverified output becomes `undetermined`.

## Atomic step

```json
{
  "expression": "(a^{-1}*a)*x=(a^{-1}*a)*y",
  "rule": "multiplicative_associativity",
  "required_conditions": []
}
```

One atomic step applies one named rule. Cosmetic sentence splitting does not
create additional calculation steps.

## Current limitations

The context tracker currently supports common fields, real numbers, rings,
commutative rings, groups, abelian groups, and vector spaces. Scope exit and
nested case tracking are conservative heuristics. The checker validates model
metadata and axiom membership. Deterministic replay currently covers only the
small safe subset above; all other atomic steps still require host validation.
