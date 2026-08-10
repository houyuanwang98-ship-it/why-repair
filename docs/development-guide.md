# Development guide

This guide covers repository structure, architecture, data contracts, retrieval and diagnosis behavior, and theorem-bank maintenance.

Before changing proof segmentation, retrieval, diagnosis, model adjudication, schemas, prompts, or checker behavior, follow the canonical instructions in [`skills/math-proof-repair-agent/SKILL.md`](../skills/math-proof-repair-agent/SKILL.md).

## Directory layout

```text
math-proof-repair-agent/
  README.md
  CHANGELOG.md
  requirements.txt
  data/
    samples/
      algebra_pilot_3.jsonl
      algebra_diagnosis_cases.jsonl
      explicit_subquestion_demo.jsonl
    theorem_bank/
      algebra_core.jsonl
      all_clean_seed_rules.jsonl
      *_clean_seed_rules.jsonl
      *_full_audit_supplemental.jsonl
  docs/
    annotation_guideline.md
    artin_coverage_audit.md
    development-guide.md
    usage-guide.md
  prompts/
    direct.md
    stepwise.md
    agentic.md
  schemas/
    proof_repair_result.schema.json
    algebra_obligation_result.schema.json
  scripts/
    extract_artin_results.py
    make_artin_theorem_markdown.py
    extract_artin_rule_candidates.py
    run_baseline.py
    evaluate_basic.py
    install_local_skill.py
    update_theorem_bank.py
  skills/
    math-proof-repair-agent/
      SKILL.md
      agents/
        openai.yaml
      references/
        data_contract.md
        compatibility.md
        ...
      scripts/
        check_obligations.py
        proof_repair/
          contracts.py
          text.py
          parsing.py
          graph.py
          subquestions.py
          retrieval.py
          calculation.py
          diagnosis.py
          adjudication.py
          io_session.py
          pipeline.py
          cli.py
  tests/
    checker_test_case.py
    test_diagnosis.py
    test_calculation.py
    test_graph_and_subquestions.py
    test_adjudication_and_theorem.py
    test_session_cache_and_io.py
    test_skill_installer.py
  outputs/                         # Generated at runtime; ignored by Git
```

`skills/math-proof-repair-agent/` is the single source of truth for the
checker implementation. Root-level `scripts/` contains development,
evaluation, installation, extraction, and data-maintenance utilities; do not
create a second checker implementation there or elsewhere in the repository.
`scripts/check_obligations.py` is a compatibility entrypoint; the
`scripts/proof_repair/` package contains the implementation modules. Keep that
package together when copying or installing the Skill.

## Upgraded workflow

The intended math-proof repair pipeline is:

```text
proof input
  -> proof segmentation
  -> proof dependency graph
  -> local obligation generation
  -> theorem-bank retrieval
  -> bridge-lemma and fallacy lookup
  -> node status classification
  -> first gap and first invalid step localization
  -> minimal repair proposal
```

The proof graph is a directed dependency graph. A tree is too restrictive,
because one algebraic step may depend on several earlier claims.

## Fixed obligation data structure

The canonical output schema is:

```text
schemas/algebra_obligation_result.schema.json
```

Each result has this top-level shape:

```json
{
  "id": "alg_001",
  "domain": "algebra",
  "topic": "linear_algebra",
  "theorem": "The theorem statement.",
  "assumptions": ["Assumption 1."],
  "proof_graph": [],
  "validity_status": "valid_with_gap",
  "first_gap_step": 2,
  "first_invalid_step": null,
  "summary_diagnosis": "Short diagnosis.",
  "summary_repair": "Minimal repair."
}
```

Each proof node has this shape:

```json
{
  "node_id": 1,
  "claim": "The proof step claim.",
  "self_contained_claim": "The proof step with references resolved.",
  "node_type": "conclusion",
  "depends_on": [],
  "dependency_source": "host_agent_graph_builder",
  "local_context": ["Available assumptions and earlier accepted claims."],
  "obligation": "Given the local context, prove the claim.",
  "retrieval_required": true,
  "retrieval_reason": "The conclusion does not follow directly from the accepted context.",
  "retrieval_query": {
    "domain": "algebra",
    "topic": "field_axioms",
    "goal": "x = y.",
    "assumptions": ["a != 0", "a*x = a*y"],
    "predecessor_node_ids": [1],
    "predecessor_claims": ["a^{-1}*a*x = a^{-1}*a*y."],
    "formal_obligation": "a != 0, a*x = a*y, a^{-1}*a*x = a^{-1}*a*y. |- x = y.",
    "normalized_query": {
      "topic_tokens": ["axioms", "field"],
      "goal_tokens": ["equal"],
      "assumption_tokens": ["equal", "multiply", "nonzero"],
      "predecessor_tokens": ["equal", "inverse", "multiply"]
    }
  },
  "retrieval_scope": "topic",
  "candidate_pool_size": 12,
  "retrieval_role": "diagnostic_only",
  "verification_source": "deterministic_checker",
  "retrieved_rules": [
    {
      "id": "artin_clean_field_cancellation",
      "name": "Cancellation in a field",
      "score": 13.0,
      "score_breakdown": {
        "goal": 4.0,
        "predecessors": 3.0,
        "assumptions": 4.0,
        "topic": 2.0,
        "domain": 0.0,
        "topic_conflict": 0.0
      },
      "matched_query_fields": ["goal", "predecessors", "assumptions", "topic"],
      "matched_rule_fields": ["conditions", "conclusion", "statement", "topic"],
      "matched_fields": ["conditions", "conclusion", "statement", "topic"]
    }
  ],
  "rule_applicability": [
    {
      "rule_id": "artin_clean_field_cancellation",
      "rule_name": "Cancellation in a field",
      "satisfied_conditions": ["F is a field", "a,b,c are in F", "a is nonzero", "ab=ac"],
      "missing_conditions": [],
      "matched_conclusion": true,
      "applicable": true,
      "common_misuses": ["Cancelling a factor that may be zero."]
    }
  ],
  "satisfied_conditions": ["F is a field", "a,b,c are in F", "a is nonzero", "ab=ac"],
  "missing_conditions": [],
  "matched_conclusion": true,
  "applicable_rule_id": "artin_clean_field_cancellation",
  "operation_check": null,
  "counterexample": null,
  "model_adjudication": null,
  "status": "missing_bridge_lemma",
  "logic_class": "repairable_gap",
  "repair_scope": "insert_local_justification",
  "gap_type": "implicit_standard_step",
  "error_type": "missing_bridge_lemma",
  "diagnosis": "Reason for the node status.",
  "repair_action": "insert_bridge_lemma",
  "minimal_repair": "Insert the applicable cancellation rule."
}
```

## Node-level obligation retrieval

The deterministic checker performs retrieval at the node level. It preserves
the existing node classifier and uses the node type and status only to decide
whether retrieval is needed:

```text
definition / assumption / introduction -> no retrieval
closed node                           -> no retrieval
downstream_invalid node               -> no retrieval
unclosed claim / calculation / conclusion -> retrieve supporting rules
```

For a node that requires retrieval, the query is a structured proof state of
the form `Gamma |- Goal`, rather than the current sentence alone. `Gamma`
contains the theorem assumptions and conservatively selected predecessor
claims. Without a validated Graph Builder response, the compatibility fallback is:

1. Use accepted nodes explicitly referenced as `step N`, `node N`, or
   `claim N`.
2. If there is no explicit reference, use the most recent accepted node.
3. If an explicit reference points only to an invalid node, do not silently
   replace it with an unrelated accepted node.
4. Keep all accepted claims in `local_context`, but use only direct
   predecessors in the retrieval query.

The primary dependency policy follows ProofFlow. Before node checking, one
Graph Builder reads the theorem, assumptions, and all already recognized proof
nodes. It returns every node's direct earlier dependencies and a
`self_contained_claim` in one structured response. The checker rejects the
whole response if node coverage, identifiers, edge direction, edge uniqueness,
or statements are invalid. With a validated graph, `local_context` and the
retrieval query contain theorem assumptions plus only direct parent claims.

Before matching, the checker normalizes common mathematical surface forms. For
example, `*`, `\cdot`, and the middle-dot character map to `multiply`;
`a^{-1}` maps to `inverse`; and `a != 0`, `a non-zero`, and `a nonzero` share
the token `nonzero`. Low-information one-character variable names are excluded
from token matching.

Candidate selection uses a staged fallback:

```text
topic or configured topic alias
  -> compatible domain
  -> global theorem bank
```

The selected stage is recorded in `retrieval_scope`, and the number of rules
considered at that stage is recorded in `candidate_pool_size`. This makes it
possible to distinguish a poor ranking from an overly broad fallback.

Candidates are ranked with an explainable field-weighted score:

```text
4.0 * goal-token matches
+ 3.0 * predecessor-token matches
+ 2.0 * assumption-token matches
+ topic match or alias bonus
+ domain match or compatibility bonus
- topic-conflict penalty during broad fallback
```

Each retrieved rule includes `score_breakdown`, `matched_query_fields`, and
`matched_rule_fields`. Retrieval remains diagnostic evidence only. A high
retrieval score does not close a proof node: `retrieval_role` is
`diagnostic_only`, while `verification_source` remains
`deterministic_checker`. Rule applicability and premise satisfaction must be
checked separately before retrieval can participate in formal verification.

## Evidence-based error diagnosis

For every retrieved rule, the checker compares theorem-bank `conditions` with
the assumptions and direct predecessor claims. The result is recorded in
`rule_applicability`; the best candidate is summarized by
`satisfied_conditions`, `missing_conditions`, `matched_conclusion`, and
`applicable_rule_id`.

An unclosed node is diagnosed in this order:

```text
verified counterexample                         -> false_theorem
invalid inverse/cancellation/reordering/equality -> algebraic error category
matched conclusion, all conditions satisfied    -> missing_bridge_lemma
matched conclusion, conditions missing           -> missing_assumption
explicit use of rule with missing conditions     -> theorem_misuse
insufficient deterministic evidence              -> valid_with_gap
```

Counterexample diagnosis is intentionally conservative and currently supports
only mechanically checked templates such as cancellation without a nonzero
hypothesis, universal group commutativity, and zero-product claims without a
no-zero-divisors assumption. Later nodes become `downstream_invalid` only when
their selected direct predecessor is invalid; unrelated later nodes are still
checked independently.

After proof or calculation adjudication, a structured diagnosis model
independently reclassifies every non-closed, non-downstream node. The validated
diagnosis may replace the deterministic category, including changing
`missing_assumption` to `missing_bridge_lemma` and changing `false_theorem` to
`false_local_claim`. A local counterexample refutes only the current node;
`false_theorem` requires a counterexample that satisfies every original
assumption and refutes the original theorem conclusion.

Theorem lookup is conditional, not universal. It runs only when the diagnosis
makes a disputed positive or gap classification depend on a specific necessary
theorem. The host checks local theorem-bank candidates first. If none verifies
the exact theorem, the host searches an authoritative web source, verifies the
statement and premises, and decides whether direct use is acceptable or an
omitted bridge. If neither local nor web search finds the theorem, the
preliminary problem remains. Direct calculations, target mismatches, explicit
counterexamples, OCR disputes, and context-settled claims do not trigger this
search.

The fine-grained `status` is also mapped to a coarse logical category:

```text
closed                                  -> no_error
valid_with_gap / missing_bridge_lemma   -> repairable_gap
missing_assumption / theorem_misuse /
algebraic_invalidity / target_mismatch -> unsupported_inference
false_local_claim / false_theorem      -> false_claim
downstream_invalid                      -> downstream_dependency
```

`repairable_gap` means that a short local justification can complete an
otherwise valid route. `unsupported_inference` means the current conclusion
does not follow from the available proof state and requires a premise or step
replacement, rather than merely more exposition. `repair_scope` records that
distinction explicitly.

If deterministic checking remains inconclusive, the checker sends the local
obligation to a model adjudicator. The model must choose exactly one result:

```text
derivable + directly_justified           -> closed / no_error
derivable + omitted_intermediate_steps   -> missing_bridge_lemma / repairable_gap
counterexample -> false_theorem / false_claim
undetermined   -> undetermined / indeterminate
```

The adjudicator receives only the theorem, local context, current claim, and
retrieved rule hints. For a derivable claim, it must apply the AI intermediate-
step completion standard in
`skills/math-proof-repair-agent/references/gap_completion_standard.md`.
Only a nonempty, minimal, connected bridge chain counts as a gap. A direct
one-rule inference is closed, while an inconsistent or incomplete chain remains
undetermined. Not finding a counterexample is never treated as a proof. The
structured response is stored in `model_adjudication`; `verification_source`
becomes `model_adjudicator`.

Calculation nodes use a separate model contract. The checker infers an active
`calculation_context` from the theorem and assumptions, then propagates it to
later accepted nodes until a structure declaration or local condition changes
it. The context lists the carrier, operations, allowed axioms, properties, and
local conditions. A calculation model must preserve the supplied endpoints,
return atomic steps, and use exact allowed axiom names. The checker rejects
unavailable or unreported axioms, introduced assumptions, and unsatisfied step
conditions. See
`skills/math-proof-repair-agent/references/calculation_adjudication_standard.md`.

Allowed node statuses:

```text
closed
valid_with_gap
missing_bridge_lemma
missing_assumption
theorem_misuse
algebraic_invalidity
false_theorem
downstream_invalid
```

Allowed repair actions:

```text
expand_step
insert_bridge_lemma
add_assumption
replace_theorem
replace_step
counterexample
null
```

Important policy:

```text
first_gap_step != first_invalid_step
```

A proof may be mathematically correct but underexplained. In that case,
`validity_status` should be `valid_with_gap`, `first_gap_step` should identify
the first gap, and `first_invalid_step` should be `null`.

## Notes for adding Artin-based material

When adding material from a textbook, do not copy long passages. Use your own
wording for definitions, theorem statements, common uses, and common misuses.
Keep source metadata so that later dataset release decisions are clear.

## Artin index workflow

The Artin PDF can be converted to OCR text with:

```bash
pdftotext -layout "Algebra, Second Edition (Michael Artin) (Z-Library).pdf" data/artin_algebra_layout.txt
```

The OCR text and all indexes produced by this workflow are reproducible local
review artifacts and are intentionally excluded from version control.

Extract theorem-like result candidates:

```bash
python scripts/extract_artin_results.py
```

Generated files:

```text
data/theorem_bank/artin_result_index.jsonl
data/theorem_bank/artin_theorem_index.jsonl
```

Build a readable theorem index:

```bash
python scripts/make_artin_theorem_markdown.py
```

Generated file:

```text
docs/artin_theorem_index.md
```

These files are OCR-derived working indexes. Review each candidate against the
PDF and rewrite statements before adding them to
`data/theorem_bank/artin_clean_seed_rules.jsonl`.

Extract theorem statement candidates and create a draft rule file:

```bash
python scripts/extract_artin_theorem_statements.py
```

Generated files:

```text
docs/artin_theorem_statements.md
data/theorem_bank/artin_theorem_rules.jsonl
```

You can run the agent with the Artin-derived draft rules:

```bash
python scripts/run_baseline.py \
  --method agentic \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_theorem_rules.jsonl \
  --output-dir outputs/agentic
```

Entries with `status: needs_pdf_review` should be checked manually before use.

## Artin broader rule-bank workflow

The theorem-only file is too narrow for proof repair. Many useful proof rules
in algebra are propositions, lemmas, corollaries, definitions, or numbered facts.
Build the broader OCR-derived candidate bank with:

```bash
python scripts/extract_artin_rule_candidates.py
```

Generated files:

```text
docs/artin_rule_candidates.md
data/theorem_bank/artin_rule_candidate_index.jsonl
data/theorem_bank/artin_rule_candidates.jsonl
```

This broader file includes explicit results, definitions, and selected numbered
facts. It is still OCR-derived, so treat it as a review queue, not as a clean
public theorem library.

For the first agent experiments, prefer the hand-cleaned seed rules:

```text
data/theorem_bank/artin_clean_seed_rules.jsonl
```

This file currently contains 161 rewritten seed rules. It is not a complete
formalization of the textbook, but it now covers the main proof-repair rules
from matrices, groups, vector spaces, linear operators, bilinear forms, rings,
modules, Jordan form, Smith normal form, finite representations, characters,
algebraic integers, ideal class groups, field extensions, finite fields, and
basic Galois theory.

See the coverage audit:

```text
docs/artin_coverage_audit.md
```

Run the agent with the clean seed bank:

```bash
python scripts/run_baseline.py \
  --method agentic \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --output-dir outputs/agentic
```

## Cross-domain clean seed rule banks

The repository also contains imported clean seed rule banks for several
mathematical domains:

```text
data/theorem_bank/abbott_understanding_analysis_clean_seed_rules.jsonl
data/theorem_bank/axler_ladr_clean_seed_rules.jsonl
data/theorem_bank/dummit_foote_abstract_algebra_clean_seed_rules.jsonl
data/theorem_bank/enderton_elements_of_set_theory_clean_seed_rules.jsonl
data/theorem_bank/enderton_logic_clean_seed_rules.jsonl
data/theorem_bank/geometry_euclid_and_beyond_clean_seed_rules.jsonl
data/theorem_bank/grinstead_probability_clean_seed_rules.jsonl
data/theorem_bank/ireland_rosen_number_theory_clean_seed_rules.jsonl
data/theorem_bank/munkres_topology_clean_seed_rules.jsonl
data/theorem_bank/stein_and_shakarchi_complex_analysis_clean_seed_rules.jsonl
data/theorem_bank/tu_an_introduction_to_manifolds_clean_seed_rules.jsonl
data/theorem_bank/west_introduction_to_graph_theory_clean.jsonl
```

Full-audit and supplemental rule files from the same source directories are
also imported and included in the merged bank.

The merged bank is:

```text
data/theorem_bank/all_clean_seed_rules.jsonl
```

Only JSONL rule data is stored in `data/theorem_bank`; dated import manifests and merged-bank metadata are intentionally not committed.

Synchronize and validate the bank from the neighboring `Theorem_grabbing` workspace with:

```bash
python scripts/update_theorem_bank.py
```
