# M0: Scope and Terminology Contract

Status: `draft_for_joint_review`

Owners: Person A (mathematical semantics), Person B (execution semantics)

Exit gate: both owners can independently label the acceptance set at the end
of this document without changing any definition. Every disagreement must be
resolved in a written adjudication note before this contract becomes `v0.1`.

## 1. System objective

Build a training-free, dual-agent harness that audits an existing
natural-language mathematical proof, locates the earliest unsupported local
inference, attempts to construct a checked counterexample, and optionally
requests a minimal local repair from a separate Repair Generator.

The system is an auditable natural-language verifier harness. It is not a
formal proof assistant and must not present model acceptance as a theorem of
soundness.

## 2. Research questions

### RQ1: Error localization

Does dependency-grounded, node-local evaluation reduce false acceptance and
improve first-error localization compared with judging the whole proof in one
prompt?

### RQ2: Counterexample guidance

Does an explicit counterexample-generation and premise-checking protocol
improve detection of false local claims without increasing invalid
counterexamples?

### RQ3: Dual-agent repair

Does an asymmetric ErrorCertificate-to-PatchProposal loop produce more valid
and more local repairs, with fewer newly introduced errors, than single-agent
self-reflection or an unconstrained generator-critic loop?

## 3. Non-goals for the first paper

- Training or fine-tuning a new foundation model.
- Claiming formal or mechanically certified correctness.
- Autonomously solving research-level open problems from scratch.
- Using Lean, Coq, Isabelle, or another formal language as a required core
  representation.
- Supporting every mathematical domain in the first benchmark.
- Treating theorem retrieval score as proof.
- Treating failure to find a counterexample as evidence of truth.
- Rewriting the entire proof when a local patch is sufficient.

## 4. Core objects

### 4.1 Proof instance

A proof instance contains:

- the theorem or question;
- explicit global assumptions;
- an ordered natural-language proof;
- optional domain and source metadata.

### 4.2 Proof node

A proof node is the smallest contiguous span that expresses one checkable
mathematical role without becoming a grammatical or mathematical fragment.

Each node must retain:

- a stable `node_id` within its proof version;
- exact source text;
- source span;
- node type;
- self-contained claim when references or pronouns must be resolved.

Splitting is a representation decision, not a mathematical verdict. A bad
split is a segmentation error and must not be relabeled as a proof error.

### 4.3 Node type

The initial node-type set is:

- `definition`: introduces the meaning of a new term, symbol, or object;
- `assumption`: introduces a local hypothetical premise or case condition;
- `introduction`: restates a given, known theorem, notation, or proof strategy;
- `claim`: announces a target that requires a subsequent subargument;
- `calculation`: performs an algebraic, numerical, inequality, or symbolic
  transformation;
- `conclusion`: asserts a consequence that should follow from available
  context;
- `citation`: invokes a named external theorem or result where applicability
  must be checked.

If a node both cites a theorem and derives a result, classify it by its primary
checkable role and preserve the citation separately as evidence metadata.

### 4.4 Direct dependency

Node A is a direct dependency of node B exactly when B's asserted conclusion
cannot be checked under the global assumptions in the intended proof route
without using A, and no accepted intermediate node already represents the
needed contribution of A.

The edge direction is `A -> B`.

Constraints:

- dependencies must refer to earlier nodes;
- no self-edge or duplicate edge is allowed;
- the graph must be acyclic;
- a dependency is not added merely because a node is topically related;
- standard background mathematics belongs in explicit ambient context or a
  cited rule, not as a fabricated proof-node dependency.

### 4.5 Local proof obligation

For node B with direct parents A1...Ak, the local obligation is:

`global assumptions + validated ambient facts + claims(A1...Ak) |- claim(B)`

The Evaluator may inspect the original wording for interpretation, but it may
not use later nodes, unrelated earlier claims, or the desired final conclusion
as mathematical evidence.

### 4.6 Failed inference edge

A failed inference edge is the smallest identified relation between the
available local premises and the current target that the Evaluator cannot
validate. It should specify:

- the exact premise nodes or global assumptions used;
- the target node;
- the proposed rule or inference, if identifiable;
- the missing condition, invalid operation, target mismatch, or counterexample
  that explains the failure.

## 5. Node verdicts

Every checked node receives exactly one final verdict from this set.

### `accepted`

The claim follows directly from the permitted local context by one explicit
and applicable rule, definition, or checked atomic calculation. No omitted
mathematical bridge is needed.

This is a harness verdict, not a formal soundness guarantee.

### `accepted_with_gap`

The target is derivable from the permitted local context, but the submitted
proof omits a nonempty, minimal, connected chain of intermediate inferences.
The bridge must be constructible and checked; mere evaluator intuition is not
enough.

### `unsupported`

The current conclusion has not been shown to follow from its permitted local
context. This covers missing assumptions, theorem misuse, invalid operations,
and other failed inferences when no checked counterexample certificate is
available.

### `counterexample_found`

A counterexample certificate has been validated: all relevant premises hold
and the target conclusion is false under the supplied interpretation.

The certificate must state whether its scope is `local_claim` or
`global_theorem`.

### `ambiguous`

The natural-language statement has two or more materially different plausible
interpretations, and the verdict depends on which interpretation is chosen.
The ambiguity and candidate readings must be recorded.

### `undetermined`

The system lacks sufficient validated evidence to accept, refute, or classify
the node. Failure to retrieve a theorem or find a counterexample is not enough
to move a node out of this state.

### `blocked_by_invalid_dependency`

The node cannot yet be evaluated because at least one required direct parent
is rejected, stale, or unresolved. This is a propagation state, not an
independent mathematical diagnosis.

## 6. Diagnostic error types

Diagnostics explain `unsupported` or `counterexample_found`; they do not
replace the verdict.

- `missing_assumption`: a necessary premise is absent from the legal context;
- `theorem_misuse`: a cited rule does not match the statement or its
  conditions are unmet;
- `algebraic_invalidity`: an algebraic or symbolic operation is invalid;
- `target_mismatch`: the derived result is not the node's asserted target;
- `dependency_error`: the declared direct parents omit a necessary earlier
  claim or include an illicit source;
- `false_local_claim`: the node is refuted under its local premises, but this
  does not by itself refute the original theorem;
- `false_theorem`: a checked example satisfies every original assumption and
  refutes the theorem conclusion;
- `segmentation_error`: the proof representation split or merged claims in a
  way that changes the local obligation;
- `interpretation_ambiguity`: the source text supports multiple materially
  different readings.

## 7. Counterexample terminology

### Candidate counterexample

A model-proposed assignment, construction, object, or scenario intended to
refute a target. It is not evidence until checked.

### Validated counterexample certificate

A record containing:

- target node and version;
- mathematical domain or structure;
- explicit object or assignment;
- each relevant premise and its check result;
- target conclusion and its false check result;
- local or global scope;
- tool trace when executable checking is used;
- remaining interpretation assumptions.

### Invalid counterexample

A candidate that violates at least one required premise, fails to refute the
target, changes the mathematical structure, or depends on an unlicensed
interpretation.

## 8. Repair terminology

### Local patch

A bounded edit that inserts, replaces, or deletes nodes needed to address one
ErrorCertificate while preserving the original theorem and unrelated proof
structure.

### Successful repair

A patch is successful only when:

1. the Evaluator accepts every inserted or replacement node;
2. the repaired target is accepted or accepted-with-gap according to the
   experiment's declared success policy;
3. every affected descendant has been rechecked;
4. no new unresolved or invalid node is introduced on the target dependency
   path;
5. the original theorem and assumptions are unchanged.

### Problem-changing proposal

A proposal that adds an assumption, weakens the conclusion, or changes the
domain. It may be useful feedback but is not counted as a repair success.

### Minimal repair

Among accepted candidate patches considered by the harness, a repair is
minimal when it contains no inserted or replaced inference that can be removed
without causing re-evaluation failure. This is operational minimality, not a
claim of global proof-length optimality.

## 9. Versioning and revocation

- Every editable node is identified by `(proof_id, node_id, version)`.
- A PatchProposal must target an exact existing version.
- Once node `N@v1` is replaced by `N@v2`, all verdicts whose validated
  dependency closure includes `N@v1` become `stale`.
- `stale` is a controller lifecycle state, not a mathematical verdict.
- A stale node must be rechecked in topological order before it can re-enter
  the accepted proof state.
- Cached model output is never reused across a changed dependency fingerprint.

## 10. Agent authority boundary

### Evaluator may

- interpret, segment, classify, build dependencies, verify, search for
  counterexamples, diagnose, and review patches;
- emit `accepted`, `accepted_with_gap`, `unsupported`,
  `counterexample_found`, `ambiguous`, or `undetermined`;
- reject malformed or mathematically unsupported patches.

### Evaluator may not

- silently repair the proof during grading;
- use later nodes as premises;
- accept a claim solely because retrieval returned a similar theorem;
- convert lack of a counterexample into acceptance.

### Repair Generator may

- propose a bounded local patch based on the supplied ErrorCertificate;
- declare that no repair is available under the original conditions;
- label a suggestion as problem-changing.

### Repair Generator may not

- accept its own patch;
- change the theorem or assumptions without explicit labeling;
- cite inaccessible hidden context;
- rewrite unrelated proof branches.

### Controller may

- validate contracts, apply accepted transitions, manage versions, revoke
  descendants, limit retries, cache exact states, and record manifests.

### Controller may not

- invent a mathematical verdict;
- convert a schema-valid model answer into mathematical evidence without an
  Evaluator decision.

## 11. Primary metrics fixed at M0

- first-error localization accuracy;
- node-verdict macro-F1;
- false acceptance rate;
- dependency edge precision, recall, and F1;
- counterexample discovery rate;
- counterexample validity rate;
- repair success rate;
- new-error introduction rate;
- descendant revalidation correctness;
- abstention/undetermined rate;
- calls, tokens, latency, and estimated cost.

The first paper's primary safety metric is false acceptance rate. Results must
also report abstention so that a system cannot appear safer merely by refusing
every case.

## 12. M0 acceptance set

Both owners must independently assign node type, direct dependencies, verdict,
and diagnostic type where applicable. Store their answers separately before
adjudication.

### Case A: direct cancellation

Theorem assumptions: `a, x, y are real numbers; a != 0; ax = ay`.

Proof node: `Therefore x = y by cancellation.`

Expected issue to discuss: whether explicit citation of cancellation makes the
step `accepted` rather than `accepted_with_gap`.

### Case B: cancellation without nonzero premise

Theorem assumptions: `a, x, y are real numbers; ax = ay`.

Proof node: `Therefore x = y.`

Candidate counterexample: `a = 0, x = 1, y = 2`.

### Case C: omitted two-step bridge

Theorem assumptions: `a, x, y are real numbers; a != 0; ax = ay`.

Proof node: `Thus x = y.`

No rule or intermediate operation is stated in the submitted proof.

Expected issue to discuss: operational boundary between direct standard rule
and a genuine omitted bridge.

### Case D: local false claim but valid theorem route remains possible

Theorem: `If n is an even integer, then n^2 is even.`

Proof nodes:

1. `Let n = 2k for an integer k.`
2. `Then n^2 = 2k^2.`
3. `Therefore n^2 is even.`

Candidate counterexample for node 2 under node 1: `k = 1`, since `n^2 = 4`
but `2k^2 = 2`.

Expected issue to discuss: node 2 is locally false while the original theorem
is true and repairable by replacing it with `n^2 = 4k^2`.

### Case E: ambiguous operation domain

Theorem assumptions: `G is a group; a, b are in G`.

Proof node: `Hence ab = ba.`

Expected issue to discuss: absence of commutativity is not merely a missing
explanation; finite non-abelian groups provide counterexamples.

### Case F: downstream invalidity

Theorem assumptions: `x is a real number`.

Proof nodes:

1. `x^2 = -1.`
2. `Therefore x^4 = 1.`

Expected issue to discuss: node 2 is algebraically conditional on node 1, but
the branch is impossible under the global real-number context. Determine the
controller and mathematical labels separately.

### Case G: definition versus inference

Proof node: `Define f(x) = x^2 + 1.`

Expected issue to discuss: this is a definition and normally requires no
derivation, but its well-formedness still depends on an understood domain.

### Case H: theorem applicability

Theorem assumptions: `f is differentiable on (0,1)`.

Proof node: `By the Extreme Value Theorem, f attains a maximum on (0,1).`

Expected issue to discuss: theorem misuse caused by absence of continuity on a
compact closed interval; distinguish missing assumption from false local
claim and provide a candidate function if possible.

### Case I: segmentation error

Raw text: `If a = 0, then ax = ay for all x and y.`

Bad split:

1. `If a = 0,`
2. `then ax = ay for all x and y.`

Expected issue to discuss: node 1 is a fragment; evaluation must first repair
the representation rather than diagnose a mathematical gap.

### Case J: underdetermined cited result

Proof node: `By the standard extension lemma, the map extends uniquely.`

No statement of the lemma, domain, codomain, or required conditions is
available.

Expected issue to discuss: do not accept from theorem-name plausibility; use
`undetermined` unless retrieval and applicability checks resolve the claim.

## 13. Review checklist

Each reviewer answers:

1. Are any terms circular or dependent on model confidence alone?
2. Can `accepted` and `accepted_with_gap` be consistently distinguished?
3. Can `unsupported`, `ambiguous`, and `undetermined` be consistently
   distinguished?
4. Is local versus global counterexample scope unambiguous?
5. Does every repair-success condition admit a deterministic check or an
   explicitly assigned Evaluator judgment?
6. Are controller states separated from mathematical verdicts?
7. Which acceptance cases still cause disagreement, and why?

## 14. Freeze procedure

1. Person A creates `M00_review_person_a.md` without reading Person B's labels.
2. Person B creates `M00_review_person_b.md` without reading Person A's labels.
3. A script or manual table compares the labels.
4. Both owners write `M00_adjudication.md` for disagreements.
5. Update this contract once, set version to `v0.1`, and record the date.
6. Begin M1 schema work only after the M0 exit gate is satisfied.

