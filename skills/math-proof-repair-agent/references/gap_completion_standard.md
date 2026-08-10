# AI Intermediate-Step Completion Standard

## Purpose

Use this standard only after deterministic checking cannot decide whether a
local proof node is complete. The AI must attempt to complete the obligation;
it must not classify a gap from linguistic length or sentence splitting alone.

## Input

```text
Context_i |- Claim_i
```

The context contains theorem assumptions, accepted predecessor claims, and
retrieved rule hints. Retrieved rules are not automatically valid: their
preconditions must hold in the context.

## Completion requirements

A valid completion must satisfy all of the following:

1. **Fixed context**: Do not add assumptions or strengthen existing ones.
2. **Fixed target**: The final step must establish the original claim exactly.
3. **Connected endpoints**: The first inference uses only the supplied context;
   every later inference depends on context or an earlier bridge step.
4. **Atomic steps**: Each bridge step performs one recognizable mathematical
   inference.
5. **Explicit justification**: Cite a rule, definition, assumption, or earlier
   bridge step for every inference.
6. **Satisfied preconditions**: Check every cited rule's domain and conditions.
7. **No hidden inference**: Do not use words such as "clearly" as a substitute
   for a missing argument.
8. **Minimality**: Return the shortest complete mathematical chain. Do not split
   one direct rule application into cosmetic language fragments.

## Classification

### Directly justified

Use when one rule application directly connects the context to the claim:

```text
completion_assessment: directly_justified
original_step_requires_completion: false
bridge_steps: []
bridge_length: 0
```

The node is `closed`, not a gap.

### Omitted intermediate steps

Use only when at least one mathematical intermediate claim is absent from the
student's step and the returned chain satisfies every completion requirement:

```text
completion_assessment: omitted_intermediate_steps
original_step_requires_completion: true
bridge_length: len(bridge_steps) > 0
```

The node is `missing_bridge_lemma / repairable_gap`.

### Undetermined

Use when no complete proof chain or checked counterexample is available, when a
rule condition cannot be established, or when the proposed chain fails an
endpoint, dependency, atomicity, or minimality requirement:

```text
decision: undetermined
completion_assessment: not_applicable
```

The node remains `undetermined / indeterminate`.

## Counterexamples

A counterexample must satisfy every supplied assumption and refute the exact
claim. Failure to find a counterexample does not establish derivability.

## Required bridge-step shape

```json
{
  "claim": "One atomic intermediate mathematical claim.",
  "justification": "Named rule and its instantiated use.",
  "depends_on_context": ["Exact context or earlier bridge claims used."]
}
```

The checker performs structural consistency checks on the returned assessment,
boolean flag, bridge list, and bridge length. A future replay verifier should
independently validate each mathematical inference.
