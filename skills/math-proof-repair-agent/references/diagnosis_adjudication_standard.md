# Error Diagnosis and Reclassification Standard

## Purpose

Use this stage after proof or calculation adjudication produces a non-closed,
non-downstream preliminary status. Independently determine the exact error
category. The preliminary category is evidence, not a constraint.

A separate diagnosis call may be omitted when a high-confidence proof primary
returns `derivable` with `omitted_intermediate_steps` and a nonempty bridge
chain, or when a high-confidence calculation primary returns a structurally
valid `repairable_gap` with at least two atomic steps and no missing or
introduced conditions. In those cases the checker records a confirmed
`missing_bridge_lemma` diagnosis from the primary evidence. Low confidence,
counterexamples, invalidity, theorem dependencies, OCR uncertainty, and
deterministic conflicts still require independent diagnosis.

## Required decision

- `confirmed`: an error exists; choose its most accurate category even when it
  differs from the preliminary category.
- `false_positive`: the original step is directly justified.
- `uncertain`: OCR damage or missing context prevents a responsible decision.

Reject generic statements such as "the proof is incomplete." Identify the
first failed inference edge, its violated obligation, and concrete evidence.

## Error categories

- `directly_justified`: the direct context closes the node.
- `missing_bridge_lemma`: the route is correct but omits a local proof bridge.
- `missing_assumption`: a genuinely required premise is absent.
- `theorem_misuse`: an invoked theorem exists but its conditions are not met.
- `algebraic_invalidity`: an atomic transformation is invalid.
- `false_local_claim`: the current node is false, but the original theorem is
  not refuted.
- `false_theorem`: a counterexample satisfies all original assumptions and
  refutes the original theorem conclusion.
- `target_mismatch`: the proof establishes a different target.
- `ocr_uncertain` or `undetermined`: evidence is insufficient.

## Independent reclassification

Allow a validated diagnosis to replace the preliminary category. In
particular, allow:

- `missing_assumption` to become `missing_bridge_lemma`;
- `false_theorem` to become `false_local_claim`;
- any invalid preliminary status to become `directly_justified`;
- any preliminary gap to become a concrete invalid category.

After reclassification, recompute status, logical class, repair scope, first
problem indices, accepted context, and downstream propagation.

## Theorem dependency trigger

Set `theorem_dependency` only when resolving the dispute genuinely depends on
a specific theorem whose existence or applicability must be checked. Do not
trigger theorem search for direct calculations, target mismatches, explicit
counterexamples, OCR uncertainty, or claims settled directly by context.

When non-null, provide the proposed theorem name, statement, conditions,
conclusion, why it is necessary, a search query, and whether the student
explicitly invoked it. The positive reclassification remains provisional until
`references/theorem_verification_standard.md` is completed.

## Consistency rules

1. Use `directly_justified` only with `false_positive`, `error_scope=none`,
   `claim_globally_derivable=true`, `repairability=none`, and no repair.
2. Use `false_local_claim` only with `error_scope=local_node` and a verified
   local counterexample or witness.
3. Use `false_theorem` only with `error_scope=original_theorem`,
   `claim_globally_derivable=false`, and a counterexample that checks every
   original assumption and the original conclusion.
4. Use `ocr_uncertain` or `undetermined` only with `uncertain` and manual
   review.
5. A gap must supply a concrete minimal bridge.
6. A missing assumption must name the absent premise and show it is absent
   from both original assumptions and direct dependencies.
7. Reject malformed, vague, or internally inconsistent responses.

## Theorem-gated status effect

If `theorem_dependency` is null, apply a validated reclassification directly.
If it is non-null, retain the preliminary status until theorem verification is
complete. A verified theorem with satisfied premises becomes either `closed`
or `missing_bridge_lemma` according to the direct-use assessment. Missing
premises become `missing_assumption` or `theorem_misuse`. If local and web
search do not find the theorem, retain the preliminary problem status.
