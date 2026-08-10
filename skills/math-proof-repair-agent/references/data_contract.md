# Algebra Obligation Data Contract

## Contents

- [Input row](#input-row)
- [Output row](#output-row)
- [Dependency graph construction](#dependency-graph-construction)
- [Node status labels](#node-status-labels)
- [Logical classes](#logical-classes)
- [Calculation adjudication](#calculation-adjudication)
- [Error diagnosis adjudication](#error-diagnosis-adjudication)
- [Required theorem verification](#required-theorem-verification)
- [Diagnosis evidence](#diagnosis-evidence)
- [Repair actions](#repair-actions)
- [First problem policy](#first-problem-policy)

Use this contract for dependency-guided obligation checking of algebra proofs.

## Input row

Each input JSONL row should contain one proof instance:

```json
{
  "id": "alg_001",
  "domain": "algebra",
  "topic": "linear_algebra",
  "theorem": "The theorem statement.",
  "assumptions": ["Assumption 1.", "Assumption 2."],
  "flawed_proof_steps": ["Step 1.", "Step 2."]
}
```

Optional gold fields may be present for benchmark evaluation:

```json
{
  "gold_validity_status": "valid_with_gap",
  "gold_first_gap_step": 2,
  "gold_first_invalid_step": null,
  "gold_error_type": "missing_bridge_lemma",
  "gold_minimal_repair": "Insert the missing bridge lemma."
}
```

### Explicit subquestions

For automatic splitting, provide `problem_text` and `proof_text` containing at
least two sequential explicit labels at line starts. Unlabeled consecutive
questions are not split.

Alternatively, provide an explicit structured array:

```json
{
  "id": "multipart_001",
  "domain": "algebra",
  "topic": "fields",
  "assumptions": ["F is a field"],
  "explicit_subquestions": [
    {
      "label": "1",
      "theorem": "Prove P.",
      "proof_steps": ["Proof of P."]
    },
    {
      "label": "2",
      "theorem": "Using part (1), prove Q.",
      "proof_steps": ["Proof of Q."]
    }
  ]
}
```

Each subquestion produces a separate result with `parent_id`,
`subquestion_label`, and `prior_subquestion_rule_ids`. Accepted intermediate
nodes and conclusions from earlier parts become temporary `DerivedRule` entries
for later parts of the same problem only.

## Output row

The checker should emit one JSON object per proof. The canonical schema is:

```text
schemas/algebra_obligation_result.schema.json
```

## Typed ambient-fact adjudication

Before node adjudication, emit one submission-level `kind: ambient` response
covering every proof instance. This is an exchange-only structure; accepted
canonical statements are merged into each node's existing `ambient_facts`
array, so the canonical result schema does not change.

Permit only the fact kinds `euclidean_space`, `extended_real_expression`,
`finite_dimensional`, `metric`, `metric_space`, `normed_space`,
`positive_integer`, `real_numbers`, `real_sequence`, `subset`, and
`topological_space`. Permit only `explicit_statement`, `type_declaration`, and
`standard_notation` derivations. Require each fact to contain a subject, an
optional object, an exact source-text excerpt from the theorem or assumptions,
and one short reasoning sentence.

Reject the whole response unless it covers every requested result exactly
once. Reject facts based on topic labels, neighboring problems, student proof
steps, or unstated chapter context. A background fact must not establish a
local mathematical step that the student was required to prove. Put uncertain
candidates in `abstained_conditions`; abstentions never enter proof state.

Emit the ambient batch in the same initial frontier as graph obligations so it
does not add a host round. Reuse accepted facts across all nodes in the proof
instance and include their exact canonical statements in every node-cache
fingerprint.

The key object is `proof_graph`. Each node represents one proof step:

```json
{
  "node_id": 1,
  "claim": "Current proof claim.",
  "self_contained_claim": "The claim with references and omissions resolved.",
  "depends_on": [],
  "dependency_source": "host_agent_graph_builder",
  "local_context": ["Assumptions and earlier valid claims."],
  "ambient_facts": ["Facts explicitly implied by the problem statement."],
  "obligation": "Given local_context, prove claim.",
  "retrieved_rules": [
    {
      "id": "rule_id",
      "name": "Rule name",
      "score": 3.0,
      "matched_fields": ["topic", "statement"]
    }
  ],
  "rule_applicability": [],
  "satisfied_conditions": [],
  "missing_conditions": [],
  "matched_conclusion": null,
  "applicable_rule_id": null,
  "operation_check": null,
  "counterexample": null,
  "model_adjudication": null,
  "diagnosis_adjudication": null,
  "theorem_candidates": [],
  "theorem_verification": null,
  "status": "closed",
  "logic_class": "no_error",
  "repair_scope": "none",
  "gap_type": null,
  "error_type": null,
  "diagnosis": "Why this node is classified this way.",
  "repair_action": null,
  "minimal_repair": null
}
```

## Dependency graph construction

When proof nodes are already available, construct their dependency graph before
checking any local obligation. The Graph Builder reads the theorem,
assumptions, and complete ordered node list in one pass. It returns exactly one
entry per node with `node_id`, direct earlier `depends_on` identifiers, and a
nonempty `self_contained_claim`.

The helper validates full node coverage, unique identifiers, existing strictly
earlier dependencies, absence of duplicate edges, and nonempty self-contained statements.
Because every edge must point from an earlier node to a later node, a validated
graph is acyclic. Reject the complete response if any entry is invalid; never
partially merge a graph. The portable host-agent exchange uses `kind: graph`
and `node_id: 0` for this proof-level response.

Generate each local context from theorem assumptions and the claims of the
validated direct dependencies. `heuristic_fallback` is retained only for
offline compatibility when no validated Graph Builder response is available.

A deterministic graph fast path may be used only for exactly two nodes when
the second is an explicit, unambiguous continuation of the first. It produces
the edge `1 -> 2`, preserves both original claims as self-contained claims, and
records `dependency_source=deterministic_linear_graph`. Pronouns, named-node
references, case splits, reverse directions, and longer proofs are excluded.

## Incremental node cache

The optional node cache is outside the canonical result schema. It is a derived
execution artifact and must not be cited as proof evidence. Cache reuse requires
an exact content fingerprint over:

- the checker source and cache schema version;
- the active theorem bank and retrieval limit;
- theorem assumptions and other proof-level context;
- the current claim, node type, and validated graph entry;
- the complete cached results of direct predecessors;
- accepted claims and the active calculation context;
- the exact effective calculation source endpoint, when applicable;
- the generated local context; and
- the adjudicator mode and stable model/provider configuration; and
- all available proof, calculation, diagnosis, and theorem responses for the
  current node.

When a node misses, recompute it normally. Its changed result digest causes
dependent descendants to miss in the same ordered pass. Unrelated stable nodes
may still be reused. A malformed cache, a cache with an unsupported schema
version, or a fingerprint mismatch is a cache miss, never `undetermined` and
never a reason to change a mathematical status.

Direct library callers using runtime adjudicator callbacks must provide a
stable `adjudicator_key` in the cache context. Without that key, the checker
disables node reuse for the affected result rather than guessing callback
identity.

## Node status labels

Use these labels exactly:

- `closed`: The claim is locally justified by context and retrieved rules.
- `valid_with_gap`: The claim is likely correct but omits a standard argument.
- `missing_bridge_lemma`: The proof needs an explicit bridge lemma.
- `missing_assumption`: A required hypothesis is absent from the theorem context.
- `theorem_misuse`: A theorem or construction is invoked under the wrong condition.
- `algebraic_invalidity`: The local inference is mathematically invalid.
- `false_local_claim`: The current node is false without refuting the original theorem.
- `false_theorem`: The theorem statement itself is false under the assumptions.
- `target_mismatch`: The proof establishes a different target.
- `downstream_invalid`: The node depends on an earlier invalid node.
- `undetermined`: Neither deterministic checks nor model adjudication established a proof or counterexample.

## Logical classes

- `no_error`: The local obligation is closed.
- `repairable_gap`: The route is valid and needs only a short local bridge.
- `unsupported_inference`: The conclusion does not follow from the available state.
- `false_claim`: A verified counterexample refutes the theorem or final claim.
- `downstream_dependency`: The node relies on an invalid predecessor.
- `indeterminate`: Available verification methods cannot decide the obligation.

For a model-adjudicated node, store the structured three-way result in
`model_adjudication`: `derivable`, `counterexample`, or `undetermined`. Never
infer derivability merely from failure to find a counterexample.

For `derivable`, apply `references/gap_completion_standard.md`:

- `directly_justified`, no bridge steps, and `bridge_length=0` means `closed`;
- `omitted_intermediate_steps` requires a nonempty minimal atomic bridge chain
  and means `missing_bridge_lemma`;
- inconsistent completion metadata or an incomplete chain means `undetermined`.

The required completion fields are `completion_assessment`,
`original_step_requires_completion`, `bridge_steps`, and `bridge_length`.

## Calculation adjudication

Every node records `calculation_context`. Calculation nodes additionally record
`calculation_source_expression` and `calculation_adjudication`. The context is
inherited when the mathematical structure and local conditions do not change.

The model must return one of `valid_transformation`, `repairable_gap`,
`missing_precondition`, `invalid_transformation`, `context_mismatch`, or
`undetermined`. The checker rejects changed endpoints, introduced assumptions,
and `used_axioms` not present in the active context. See
`references/calculation_adjudication_standard.md` for the full contract.

Use `repair_scope` to distinguish local insertion, premise establishment, step
replacement, theorem revision, and predecessor repair.

## Error diagnosis adjudication

After proof or calculation adjudication, every non-closed, non-downstream node
receives a structured diagnosis review. Store it in `diagnosis_adjudication`.
The review must be `confirmed`, `false_positive`, or `uncertain` and must name
the exact failed inference, violated obligation, error scope, concrete
evidence, global derivability, repairability, and minimal repair. Apply
`references/diagnosis_adjudication_standard.md`.

A validated diagnosis may replace the preliminary error category. A
false-positive review changes the node to `closed`; an uncertain review changes
it to `undetermined`. Recompute logical class, repair scope, first-problem
indices, accepted context, and downstream propagation after any change.

Pending templates may combine the primary review and conditional diagnosis as
`proof_diagnosis` or `calculation_diagnosis`. A bundled response has exactly
these logical fields:

```json
{
  "primary_response": {},
  "diagnosis_response": null
}
```

`primary_response` follows the existing proof or calculation schema. Set
`diagnosis_response` to null when the primary response closes the node or when
a high-confidence, structurally valid primary gap already supplies the final
category and evidence. Otherwise it follows the diagnosis schema. The checker
expands valid bundles
into the same internal proof/calculation and diagnosis records used by legacy
separate adjudication files, so the canonical result schema does not change.

After a validated graph is available, pending entries form a dependency
frontier: a candidate is emitted only when none of its graph ancestors is also
unresolved. Independent candidates may be emitted together. Calculation
candidates are additionally blocked by unresolved earlier nodes that change
the active calculation context. Without a validated graph, pending emission
remains single-node and sequential.

Each pending document owns a top-level `rule_dictionary`. Nested
`retrieved_rules` arrays are replaced by `retrieved_rule_refs`; each reference
includes the rule identifier and a digest of the exact scored retrieval
variant. The host resolves those references from the dictionary. This is an
exchange-format optimization only: canonical result nodes continue to contain
the complete retrieved rule objects.

Problem-statement facts such as an explicitly declared metric space, its
metric, and set membership in that ambient space are added to `ambient_facts`
and may satisfy rule conditions. Topic labels alone never create ambient
facts. A conclusion-matching retrieval candidate with missing conditions may
create a deterministic `missing_assumption` only when the student explicitly
invokes it or retrieval also matches assumptions or direct predecessors.
Goal/domain-only retrieval abstains and leaves the node for diagnosis.

On session resume, a stored calculation response is valid only for its current
source and target endpoints. If predecessor acceptance changes the effective
source expression, or the current claim changes the target expression, emit a
new calculation pending entry even when the stored response decision was not
`undetermined`. The replacement response may overwrite the same ledger key
after it passes normal endpoint validation.

For a validated dependency graph, derive a calculation source only from its
direct predecessor nodes. If it has no direct predecessors, use the theorem
assumptions as the source endpoint rather than the most recently accepted
unrelated node. The historical accepted-claim fallback remains limited to the
heuristic compatibility path.

## Required theorem verification

When `diagnosis_adjudication.theorem_dependency` is non-null, store local
lookup results in `theorem_candidates` and keep the positive reclassification
provisional until `theorem_verification` is validated. Apply
`references/theorem_verification_standard.md`.

The host inspects local candidates first. If none verifies the proposed
theorem, it searches an authoritative web source. Record whether the theorem
was locally verified, web verified, or not found; its exact statement and
conditions; source identifier or URL; premise satisfaction; foundational
status; and whether direct use is acceptable or an omitted bridge. Do not
trigger theorem search for disputes resolved directly by calculation,
counterexample, target comparison, context, or OCR reliability.

## Diagnosis evidence

- `rule_applicability` records condition and conclusion checks for every retrieved rule.
- `satisfied_conditions` and `missing_conditions` summarize the best conclusion-matching candidate.
- `matched_conclusion` reports whether that candidate's conclusion structurally matches the goal.
- `applicable_rule_id` is set only when the conclusion matches and every condition is satisfied.
- `operation_check` names a deterministic local algebra failure when one is found.
- `counterexample` is non-null only after a supported counterexample template is verified.

The optional theorem-bank fields `deterministic_safe: true` and
`deterministic_safe_kind` opt a curated rule into a fail-closed direct-use
path. The kind must be implemented in the checker's fixed allowlist; the bank
cannot provide executable matching patterns. Direct closure requires exactly
one applicable safe rule, a checker-owned conclusion-shape match, every rule
condition satisfied by the local or typed ambient context, and no OCR/source
uncertainty. A missing condition, unsupported kind, negative or different
goal, or multiple safe candidates leaves the node on the normal host path.

Classify a node as `calculation_step` only when its complete content is a
parseable symbolic relation or relation chain with an operation, or its prose
explicitly announces a calculation/transformation. Do not classify ordinary
prose as calculation merely because it contains `=`. Deterministic replay must
consume the entire target. It may evaluate exact rational and finite-decimal
arithmetic, numeric absolute values, perfect-square radicals, and fully numeric
relation chains. It may also recognize one checker-owned symbolic identity
whose axiom is present in `calculation_context`. If any fragment, relation, or
required axiom is unsupported, replay abstains and emits the host obligation.

## Repair actions

Use these actions exactly:

- `expand_step`
- `insert_bridge_lemma`
- `add_assumption`
- `replace_theorem`
- `replace_step`
- `counterexample`
- `null`

## First problem policy

Track gaps and invalid steps separately:

- `first_gap_step` is the first node that is correct but underexplained.
- `first_invalid_step` is the first node that is mathematically wrong or uses an invalid premise.
- If a proof only has gaps, set `validity_status` to `valid_with_gap` and `first_invalid_step` to `null`.
- If a proof has a genuine invalid step, set `validity_status` to `invalid`.
