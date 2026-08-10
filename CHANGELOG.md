# Changelog

Notable project changes are grouped by release date and change type. Dates use Hong Kong time (`+08:00`).

## 2026-08-10 +08:00 — Freeze M1 shared harness contracts v0.1

### Added

- Added shared dual-agent contracts, a deterministic Controller, stable node ordering and exact version references.
- Added replacement, bridge-node insertion, dependency-gated re-evaluation, ambiguity branching and four no-model replay fixtures.
- Added `docs/milestones/M01_freeze_record.md` with the frozen scope and compatibility rules.

### Integration

- Integrated member B's completed M0 review from remote `main` before freezing M1.

### Validation

- Passed the complete 85-test suite and JSON Schema parsing before the freeze.

## 2026-08-10 +08:00 — Complete the M0 person B review

### Documentation

- Replaced the placeholder copy in
  `docs/milestones/M00_review_person_b.md` with person B's complete review of
  cases A–J, including node types, direct dependencies, verdicts, error types,
  counterexample scopes, and Controller lifecycle handling.
- Answered all seven M0 review questions and documented execution requirements
  for version binding, descendant invalidation, independent patch review, and
  strict Schema enum spelling.
- Recorded the procedural limitation that the existing member A review and
  adjudication were already present when this review was completed, so the new
  record is not represented as retrospectively proven blind review evidence.

### Validation

- Passed all 63 standard-library unit tests and verified the review document's
  UTF-8 integrity and required section coverage.

## 2026-07-23 21:35:18 +08:00 — Modularize the proof checker and test suite

### Changed

- Replaced the 5,153-line checker implementation with a portable
  `scripts/proof_repair/` package while preserving
  `scripts/check_obligations.py` as the compatible CLI and import surface.
- Split proof parsing, dependency graphs, retrieval, calculation checking,
  diagnosis, adjudication, session I/O, pipeline orchestration, and CLI
  handling into focused implementation modules.
- Reduced `build_result()` from 568 lines to 186 lines by separating node
  context preparation, node evaluation, problem-summary updates, and final
  result assembly.
- Split the checker test suite into diagnosis, calculation, graph and
  subquestion, adjudication and theorem, and session/cache/I/O modules with one
  shared test fixture.

### Fixed

- Extended checker source fingerprints across the compatibility entrypoint and
  every implementation module so changes in modular code invalidate stale node
  caches.
- Preserved all 111 legacy checker function exports for existing direct Python
  callers.

### Documentation

- Updated the repository map and Skill compatibility layout to identify
  `skills/math-proof-repair-agent/` as the checker source of truth and document
  the adjacent implementation package.
- Clarified that `requirements.txt` is needed only for the baseline runner and
  optional standalone OpenAI adapter; the default portable checker uses only
  the Python standard library.
- Renamed `CHANGELOGS.md` to the conventional singular `CHANGELOG.md` and
  updated repository references.

### Validation

- Passed 63 automated tests, Python compilation, JSON/JSONL validation, ASCII
  source validation, dependency-cache reuse, and an isolated installed-Skill
  smoke test.
- Confirmed byte-for-byte equivalence of sample result JSON and the pending
  adjudication template before and after modularization.

## 2026-07-23 00:11:13 +08:00 — Repository cleanup

### Changed

- The theorem-bank synchronizer now writes rule data only; it no longer creates
  dated import manifests or a merged-bank JSON manifest.
- Ignore rules now cover local tool state, generated Skill backups, Python
  bytecode, and packaged release archives.

### Removed

- Removed committed Python bytecode, generated local Skill backups, and local
  OpenClaude settings from version control.
- Removed the three non-runtime JSON manifest files from `data/theorem_bank`,
  leaving one consistent JSONL format for theorem and rule data.
- Removed student homework inputs, student-specific grading outputs, repaired
  proof artifacts, local release bundles, and one-off Python generation scripts.
- Removed reproducible OCR text, candidate indexes, draft theorem rules, and
  generated Markdown views; their source scripts remain available.

### Documentation

- Replaced the monolithic README with a concise project overview and quick
  start.
- Added `docs/usage-guide.md` for installation, command-line workflows,
  resumable sessions, evaluation, and input formats.
- Added `docs/development-guide.md` for architecture, data contracts,
  retrieval and diagnosis behavior, and theorem-bank maintenance.
- Removed the former combined `docs/technical-guide.md` after distributing all
  of its content between the two focused guides.
- Moved release history into this changelog and categorized each release by the
  type of change.

## 2026-07-20 01:55:16 +08:00 — Reduce deterministic proof-checking overhead

Commit: `1ded68d Reduce deterministic proof-checking overhead`

### Added

- Added one submission-level typed ambient-fact adjudication to the initial
  graph frontier. The host uses only a small amount of reasoning, must quote
  theorem/assumption evidence, and may emit only allowlisted background fact
  shapes. Accepted facts are reused by every node and included in cache
  fingerprints; uncertain or proof-discharging facts are rejected.
- Added fail-closed `deterministic_safe` theorem-bank rules. A bank flag alone
  cannot execute a rule: the checker must also recognize a fixed conclusion
  shape, establish every typed condition, find exactly one safe match, and
  detect no OCR/source uncertainty. The repository ships three curated analysis
  rules for interiors, Euclidean separability, and monotone convergence.

### Changed

- Tightened calculation classification so ordinary prose containing an equals
  sign no longer enters the calculation adjudicator. Complete symbolic
  relations, relation chains, and explicit calculation language remain
  eligible.
- Extended deterministic replay with exact finite decimals, numeric fractions,
  absolute values, perfect-square radicals, fully checked numeric relation
  chains, and checker-owned single-axiom identity, inverse, commutativity,
  associativity, and distributivity shapes. Any unsupported fragment causes
  complete abstention rather than partial acceptance.

### Fixed

- Fixed automatic-session endpoint recovery: a stored calculation response is
  requeued when its source or target no longer matches the node's effective
  endpoint. Validated independent graph branches now derive calculation sources
  from theorem assumptions instead of unrelated accepted nodes.

### Compatibility

- Preserved legacy response compatibility and dependency-aware cache behavior.
  Endpoint bindings and typed ambient facts now participate in cache
  fingerprints, so only affected nodes and descendants are rebuilt.

### Validation

- Expanded the automated suite to 62 passing tests, compiled the checker to an
  isolated `/tmp` bytecode target, parsed both curated theorem banks, passed
  `quick_validate.py`, and completed a fresh isolated evaluation first-frontier
  replay over 19 proof instances and 68 nodes. It emitted 16 initial host
  obligations: one shared ambient batch and 15 graphs, with four graph instances
  handled by the existing conservative fast path.

## 2026-07-20 00:45:55 +08:00 — Reduce proof adjudication reasoning overhead

Commit: `1daf7f9 Reduce proof adjudication reasoning overhead`

### Added

- Added `--workflow-mode grading|repair` and froze the selected mode in session
  manifests and pending files so automatic resume cannot silently change it.
- Added exact deterministic calculation replay for complete rational numeric
  relations and a small set of single-step identity axioms. Unsupported
  expressions continue to require host adjudication; the evaluation set contained no
  eligible calculation, so no dataset-specific saving is claimed.
- Added a conservative deterministic graph fast path for unambiguous two-node
  continuations. It safely covered 9 of 60 evaluated proof instances, reducing
  graph host judgments by 15 percent in that replay. Longer proofs, branches,
  pronouns, and explicit cross-node references remain host-built.
- Added problem-statement ambient facts for metric and Euclidean contexts and
  retrieval abstention for goal/domain-only candidate matches. Weak retrieval
  can no longer manufacture `missing_assumption`; 22 such preliminary triggers
  were removed from the measured evaluation first frontier without treating
  retrieval as proof evidence.

### Changed

- Split grading and repair workflows. Grading is the default, does not load the
  iterative repair procedure, and cannot emit repaired-proof artifacts. Repair
  instructions now live in a repair-only reference loaded after all checker
  obligations are resolved.
- Allowed a structurally complete, high-confidence proof or calculation
  primary to supply the final `missing_bridge_lemma` diagnosis. Eight of the 11
  evaluated post-primary diagnoses satisfy the guarded rule; low-confidence,
  invalid, counterexample, theorem-dependent, and OCR-sensitive cases retain
  independent diagnosis.

### Performance

- Added a shared top-level `rule_dictionary` to pending files. Repeated scored
  retrieval variants are referenced by stable rule-and-digest keys while the
  canonical result keeps the complete retrieval trace. The evaluation
  first-frontier pending payloads were 4.3 percent smaller in the measured replay.

### Compatibility

- Preserved legacy response compatibility by applying an existing validated
  diagnosis before creating a new primary obligation, while still replaying a
  legacy calculation primary when its preliminary node was initially closed.

### Validation

- Expanded the automated suite from 45 to 51 passing tests, compiled the
  checker with an isolated bytecode cache, validated the Skill package, and
  parsed the canonical JSON Schema.
- Replayed all six evaluation submissions with their historical graph, proof,
  calculation, and diagnosis responses: 60 proof instances and 210 proof
  nodes finished with zero pending obligations. All six students had zero
  differences in validity status, first-problem indices, node status, gap/error
  type, logical class, and repair scope.

## 2026-07-20 00:00:33 +08:00 — Optimize incremental adjudication sessions

Commit: `174a0cf Optimize incremental adjudication sessions`

### Added

- Added an opt-in persistent node cache for repeated host-agent resume rounds.
- Added `--write-changed-only` to preserve identical result and pending files
  when one output directory is reused across rounds.
- Added dependency-frontier batching so independent unresolved nodes from the
  validated proof DAG can be adjudicated in one host turn.
- Added `proof_diagnosis` and `calculation_diagnosis` pending bundles, while
  retaining full compatibility with legacy separate response files.
- Added `--session-dir`, which persists configuration, response history, cache,
  results, and the current pending frontier. Later runs need only the session
  directory and automatically ingest filled pending responses.
- Added a durable `responses.jsonl` ledger and frozen `session.json` manifest.
  Filled `pending.json` responses and optional legacy `--adjudications` files
  are imported before each resume, so earlier response files no longer need to
  be repeated manually.

### Changed

- Reuses only nodes with matching checker, theorem-bank, proof-context, graph,
  predecessor, calculation-context, local-context, adjudicator-configuration,
  and response fingerprints.
- Propagates cache invalidation through changed predecessor digests so affected
  descendants are recomputed while unrelated stable nodes remain reusable.
- Restricted validated-graph classification context to direct predecessors,
  matching the documented data contract and preventing unrelated branch state
  from influencing frontier decisions. Heuristic dependency fallback remains
  single-node and sequential.

### Performance

- Reduced the evaluation set's nonzero post-graph adjudication rounds from eight to five,
  a 37.5 percent reduction, while a warm unchanged rerun reused all 68 cached
  nodes and rewrote no result files.

### Compatibility

- Kept the cache outside the canonical result schema and added regression tests
  comparing cached results with clean full recomputation.
- Kept graph, proof, calculation, diagnosis, and theorem validation unchanged
  after bundle expansion. Invalid or missing bundled diagnosis responses fall
  back to a normal later diagnosis obligation instead of bypassing validation.
- Preserved backward compatibility for the legacy stateless CLI, separate
  adjudication kinds, existing response files, and canonical result schema.

### Validation

- Expanded the automated suite from 41 to 45 passing tests, including cache
  invalidation, independent frontier batching, bundle expansion, graph-ledger
  persistence, and path-free session restoration.
- Validated the Skill package with `quick_validate.py`, compiled the checker,
  and completed a real evaluation replay covering 19 proof instances and 68 proof
  nodes. All 19 final JSON results were byte-identical to the prior validated
  output and the final pending count was zero.

## 2026-07-13 20:29:00 +08:00 — Complete the proof repair workflow

### Added

- Added cascading deletion of **introduction-type nodes** that explicitly
  reference a deleted node, distinct from a mere dependency relationship.
- Added a **global proof completion pass** (Step 2C) after all nodes are
  processed, inserting derivation steps that connect the remaining valid nodes
  into a complete proof.
- Added `deleted_nodes` and `completion_steps` to the repair output format.

### Changed

- Replaced irreparable termination with **node deletion**: when a non-gap
  error is not derivable from problem conditions, the erroneous node is deleted
  instead of stopping the repair loop.
- Required all inserted repair steps (bridge gaps, replacement derivations,
  and completion steps) to be displayed in **red font** so they remain distinct
  from original proof nodes.
- Updated Step 3 to continue after deletions and trigger global completion once
  every remaining node has been processed.

## 2026-07-13 17:15:36 +08:00 — Add structured diagnosis and theorem verification

Commit: `85d5d43 Add structured diagnosis and theorem verification`

### Added

- Added a mandatory structured diagnosis stage for every non-closed,
  non-downstream node after proof or calculation adjudication.
- Added the diagnosis adjudication contract with an independent
  `confirmed` / `false_positive` / `uncertain` review, the exact failed
  inference, violated obligation, concrete evidence, error scope, global
  derivability, repairability, minimal repair, and confidence.
- Added source-reliability tracking so OCR uncertainty is represented
  separately from mathematical invalidity and can be routed to manual review.
- Added `false_local_claim` to distinguish a false proof node from a false
  original theorem, and added `target_mismatch` as an independent error type.
  `false_theorem` now requires a counterexample satisfying every original
  assumption and refuting the original theorem conclusion.
- Added a complete diagnosis standard requiring specific mathematical
  explanations and rejecting vague, malformed, or internally inconsistent
  model responses.
- Added optional `theorem_dependency` metadata for disputes whose positive
  resolution genuinely depends on a specific necessary theorem.
- Added the portable `kind: theorem` adjudication to the existing
  `emit -> adjudicate -> validate -> resume` loop without creating a parallel
  model workflow.
- Added local-first theorem lookup. Authoritative web search is permitted only
  after no emitted local candidate verifies the proposed theorem; direct
  calculations, target mismatches, explicit counterexamples, OCR disputes, and
  context-settled claims do not trigger search.
- Added theorem-verification results for the exact theorem statement,
  conditions, conclusion, source, premise satisfaction, foundational status,
  and whether direct use is acceptable or constitutes an omitted bridge.
- Added anti-hallucination validation: locally verified theorem text must match
  an emitted candidate exactly, premise satisfaction is recomputed from the
  local context, web verification requires an opened source URL and title, web
  search must follow local lookup, and an unfound theorem cannot clear the
  preliminary error.
- Added deterministic status effects for verified theorems: applicable direct
  use closes the node, an omitted citation or derivation becomes
  `missing_bridge_lemma`, missing premises become `missing_assumption` or
  `theorem_misuse`, and failed search preserves the preliminary problem.
- Added regression coverage for cross-category overrides, false local claims
  versus false theorems, local-before-web theorem lookup, fabricated local
  theorem rejection, required web-search order, premise recomputation, unfound
  theorem handling, Unicode preservation, and ASCII-only Skill sources.
- Added targeted regressions for three diagnosis-category failures that
  motivated the change: Exercise 2.6 becomes a repairable selection gap,
  Exercise 2.26 becomes a local construction error rather than a false theorem,
  and Exercise 3.5 distinguishes threshold-index gaps from a false local step.

### Changed

- Renamed and repackaged the portable Skill from
  `algebra-obligation-checker` to `math-proof-repair-agent`, and synchronized
  repository documentation, client metadata, install paths, and tests with the
  new identity.
- Allowed a validated diagnosis to replace the preliminary deterministic error
  category and recompute status, logical class, repair scope, accepted context,
  first-problem indices, and downstream propagation.
- Extended the canonical result schema, data contract, cross-agent standard,
  and checker output with diagnosis adjudication, theorem candidates, theorem
  verification, error scope, OCR source reliability, and the new statuses.

### Compatibility

- Preserved UTF-8 proof input and user-facing output, including Chinese source
  text, while keeping Skill-authored rules and source files English ASCII.
  JSON, prompts, and CLI output now serialize Unicode without forced escape
  sequences.

### Validation

- Expanded the automated suite from 24 to 37 passing tests, validated the
  portable Skill package and installed Codex copy, checked the canonical JSON
  schema, and compared generated results against the installed Skill.
- Completed a fresh 15-exercise forward test with new graph and host
  adjudications, zero unresolved entries, and all final results passing the
  Canonical Schema. The run also exposed remaining evaluation sensitivity to
  OCR normalization, compressed source wording, and the grading severity of
  obvious notation slips.

## 2026-07-12 20:03:10 +08:00 — Add iterative proof repair

Commit: `54ff394 Add iterative proof repair procedure`

### Added

- Added an iterative repair procedure that processes problematic proof nodes
  in dependency order while preserving the accepted proof state.
- Added separate handling for non-gap errors: conclusions derivable from the
  original problem conditions receive replacement derivations, while genuinely
  unsupported conclusions terminate the repair as irreparable.

### Changed

- Expanded bridge-gap repair from a one-line suggestion into a minimal,
  step-by-step derivation from direct dependency claims to the target claim.
- Defined repaired-proof ordering, inserted-step provenance, repair outcomes,
  and first-irreparable-error reporting for host-agent repair output.
- Updated deterministic repair guidance for missing bridge lemmas, missing
  rule conditions, rank-nullity gaps, and unresolved proof expansions to request
  explicit derivations instead of isolated repair hints.

### Compatibility

- Kept diagnosis statuses and the canonical checker schema unchanged; the new
  procedure is a host-agent repair protocol layered on validated obligation
  results.

## 2026-07-12 10:30:16 +08:00 — Expand and synchronize the theorem bank

Commit: `1e9cbce Expand and synchronize theorem bank`

### Added

- Added clean seed coverage for mathematical logic, Euclidean geometry,
  number theory, and graph theory.
- Added a reproducible synchronization script, a dated source manifest with
  SHA-256 checksums, and an expanded merged-bank manifest.

### Changed

- Synchronized all 25 JSONL rule files from the immediate subdirectories of
  the neighboring `Theorem_grabbing` workspace.
- Imported the available full-audit and supplemental rule banks alongside the
  existing analysis, linear algebra, abstract algebra, set theory, probability,
  topology, complex analysis, and manifolds banks.
- Rebuilt `all_clean_seed_rules.jsonl` with 1,673 unique rules: 1,512 imported
  rules plus 161 existing Artin algebra rules.

### Validation

- Validated JSON parsing, global rule-ID uniqueness, exact source-to-merged
  consistency, ASCII-only merged output, and all 24 automated tests.

## 2026-07-11 17:35:51 +08:00 — Add the global proof dependency graph builder

Commit: `e4cc9b8 Add global proof dependency graph builder`

### Added

- Added proof-level host-agent `kind: graph` adjudication. Each response returns
  every node's direct earlier dependencies and a self-contained claim before
  node-level checking begins.
- Added strict whole-graph validation for complete node coverage, unique node
  identifiers, strictly backward edges, duplicate dependencies, nonempty
  self-contained claims, and unexpected response fields. Invalid graph
  responses are rejected as a whole and emitted again for correction.
- Added `self_contained_claim` and `dependency_source` to the canonical result
  schema and documented the Graph Builder contract in the Skill and data
  contract.
- Added an optional standalone OpenAI Graph Builder adapter while retaining the
  API-free Codex/Claude/Gemini host-agent workflow as the default Skill path.
- Added regression coverage for multi-parent dependencies, exclusion of
  unrelated historical nodes, complete-graph rejection, and preservation of
  the existing diagnosis behavior. The full test suite passes 24 tests.

### Changed

- Replaced the primary linear predecessor policy with a ProofFlow-style global
  Graph Builder that reads the theorem, assumptions, and all recognized proof
  nodes in one pass.
- Changed validated-graph obligation contexts to contain theorem assumptions
  plus only direct parent claims. The previous explicit-reference/latest-node
  heuristic remains an offline compatibility fallback.

### Validation

- Validated the installed Codex Skill on a multi-exercise PDF through a complete
  graph/adjudication/resume cycle. The generated PDF-specific input and output
  artifacts are local evaluation files and are intentionally excluded from
  this upload.

## 2026-07-10 23:01:46 +08:00 — Add portable host-agent proof adjudication

Commit: `65d7f1b Add portable host-agent proof adjudication`

### Added

- Added rule-applicability evidence, including satisfied and missing conditions,
  conclusion matching, and applicable rule identifiers.
- Added evidence-based error diagnosis, coarse logical classes, repair scopes,
  conservative counterexamples, and explicit `undetermined` handling.
- Added the AI intermediate-step completion standard: direct one-rule inference
  is closed, while only a nonempty minimal bridge chain counts as a proof gap.
- Added calculation-context inference and propagation across nodes, plus a
  guarded host-agent calculation contract for atomic transformations.
- Added explicit numbered-subquestion splitting. Accepted intermediate nodes and
  conclusions from earlier parts become temporary rules for later parts of the
  same problem.
- Added portable Agent Skills packaging and installation profiles for Codex,
  Claude Code, Gemini CLI, the shared `.agents/skills` convention, and custom
  client directories.
- Added the cross-agent packaging standard, compatibility reference, diagnosis
  roadmap, calculation standard, gap-completion standard, schemas, samples, and
  regression tests.
- Added host-agent `emit -> adjudicate -> resume` exchange so the active Agent
  can directly perform reasoning while deterministic helpers validate and merge
  the response.

### Changed

- Delegated unresolved proposition checks to a structured host-agent
  adjudication contract instead of assuming a helper process can access the
  host model.

## 2026-07-10 17:23:23 +08:00 — Improve node-level obligation retrieval

Commit: `1ed7886 Improve node-level obligation retrieval`

### Added

- Added node classification and node-level retrieval switches.
- Added conservative direct-predecessor selection.
- Added query normalization, topic/domain candidate filtering, and weighted
  retrieval scoring.
- Added an extracted PDF proof sample and validated its retrieval trace.

### Changed

- Replaced sentence-only retrieval queries with structured proof obligations.

### Compatibility

- Kept retrieval diagnostic-only and separate from deterministic verification.

### Documentation

- Documented the retrieval workflow in English and added a standalone retrieval
  optimization roadmap.
