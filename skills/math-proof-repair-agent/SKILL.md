---
name: math-proof-repair-agent
description: Dependency-guided obligation checking for natural-language algebra proofs. Use when an AI coding agent needs to build a proof dependency graph, retrieve theorem-bank rules, distinguish repairable gaps from invalid reasoning, identify the first problematic node, and propose a minimal repair.
---

# Math Proof Repair Agent

## Overview

Use this skill to audit algebra proofs with a dependency graph and local proof obligations. The goal is not to fully formalize the proof, but to produce a structured trace that separates proof gaps from genuine invalid reasoning.

This skill follows the portable Agent Skills directory layout. It can be used
by Codex, Claude Code, Gemini CLI, or another agent that can load `SKILL.md`.
Ignore `agents/openai.yaml` on clients that do not use OpenAI UI metadata. Read
`references/compatibility.md` when installing or invoking the skill on a new
CLI or operating system.

When deterministic checking leaves a possible proof gap, read and apply
`references/gap_completion_standard.md`. Gap classification is delegated to
the AI completion stage under that standard; sentence splitting alone is not
evidence of a mathematical gap.

For calculation nodes, read and apply
`references/calculation_adjudication_standard.md`. The checker owns and
propagates the active axiom context; the calculation model proposes atomic
steps and may use only axioms exposed by that context.

For every non-closed node after proof or calculation adjudication, read and
apply `references/diagnosis_adjudication_standard.md`. Require the host model
to identify the exact failed inference edge and independently return
`confirmed`, `false_positive`, or `uncertain`; reject vague or
internally inconsistent diagnoses. Allow a validated diagnosis to replace the
preliminary error category.

When a disputed positive classification genuinely depends on a specific
theorem, read and apply `references/theorem_verification_standard.md`. Search
the local theorem bank first. Only if no local candidate verifies the theorem,
use the host's web search to find an authoritative source. Then decide whether
the theorem's premises hold and whether direct use is acceptable or a proof
gap. Do not search for disputes settled by direct context, calculation,
counterexample, target comparison, or OCR reliability.

## Workflow

1. Read the proof instance as theorem, assumptions, and ordered proof steps.
2. If the problem contains at least two explicit sequential subquestion labels,
   split it and check the subquestions in order. Do not split unlabeled adjacent
   questions. Add accepted nodes from each earlier subquestion to a temporary
   theorem bank for later subquestions.
3. If the proof is given as a single text block, use `split_proof_into_nodes()` to
   decompose it into individual node-level claims (see Node Splitting Rules below).
4. Convert each proof step into one graph node.
5. Before checking any node, complete one submission-level `ambient` batch.
   Use only a small amount of reasoning to record typed background conditions
   directly implied by each theorem, its assumptions, or standard notation.
   Require quoted source evidence and abstain from unstated context or facts
   that would discharge a student proof step.
6. Give the theorem, assumptions, and complete
   ordered node list to one Graph Builder pass. Require exactly one result per
   node containing its direct earlier dependencies and a self-contained claim.
   Validate the complete DAG as specified in `references/data_contract.md`.
7. For each node, create the local obligation from theorem assumptions and
   only its validated direct dependencies:

```text
Given assumptions and earlier accepted claims, prove the current claim.
```

8. Retrieve relevant rules from the theorem bank. A rule marked
   `deterministic_safe` may close a node without host reasoning only through a
   checker-owned conclusion-shape handler, with every typed condition satisfied
   and no source uncertainty or competing safe match.
9. Classify the node with the fixed status labels in `references/data_contract.md`.
10. Run structured error diagnosis for each non-closed, non-downstream node.
   Validate the diagnosis before it replaces the preliminary error category.
11. If the diagnosis depends on a disputed necessary theorem, verify it through
    local lookup and, only after local failure, authoritative web search.
12. Record gap, invalid, and undetermined locations separately.
13. Apply the selected workflow mode. In grading mode, perform submission
    completeness checking and stop without loading or generating repairs. In
    repair mode, read `references/iterative_repair_procedure.md` only after all
    checker obligations are resolved, then generate the requested repair.

## Workflow Mode

Choose exactly one mode before loading mode-specific references:

- **Grading mode**: Use for grading, auditing, checking, diagnosis, feedback, or
  status classification. This is the default when the request does not ask for
  a repaired proof. Do not read
  `references/iterative_repair_procedure.md`. Stop after every proof instance
  has a validated graph, zero pending obligations, final node statuses, and a
  submission-completeness check. Do not generate `repaired_proof`,
  `inserted_steps`, `deleted_nodes`, or `completion_steps`.
- **Repair mode**: Use only when the user asks to repair, fix, complete, or
  rewrite the proof. First finish the same validated obligation-checking
  workflow as grading mode. Then read and apply
  `references/iterative_repair_procedure.md`.

An explicit user-selected mode overrides the default. Never load repair-only
instructions speculatively while operating in grading mode.

## Explicit Subquestions

Split only when the problem has at least two sequential line-leading labels,
such as `(1)/(2)`, `(a)/(b)`, `1./2.`, or `Part 1/Part 2`. Two consecutive
questions without labels remain one proof instance. Inputs may provide
`problem_text` plus `proof_text`, or an `explicit_subquestions` array. See
`references/data_contract.md` for the structured form.

After checking a subquestion, convert its `closed`, `valid_with_gap`, and
`missing_bridge_lemma` nodes into temporary `DerivedRule` entries. Add those
entries only to the working theorem bank for later subquestions of the same
parent problem. Never write them into the persistent theorem-bank file.

## Node Splitting and Classification
Before splitting raw proof text or assigning a node type, read and apply
`references/node_splitting_and_classification.md`. Preserve its splitting
order, fragment-merge safeguards, classification priority, and catch-all rule.

### CLI Usage
Locate this skill directory through the active client's skill registry. Invoke
the bundled Python script without assuming a repository-relative skill path.
Use `--raw-proof` to pass raw proof text directly:

```text
python <skill-dir>/scripts/check_obligations.py --input <input.jsonl> --theorem-bank <rules.jsonl> --output-dir <output-dir> --raw-proof "Since a is nonzero, a has an inverse. Therefore x = y."
```

## Data Contract

Read `references/data_contract.md` before changing schemas, prompts, or checker scripts. The canonical result schema is:

```text
schemas/algebra_obligation_result.schema.json
```

## Script

Run the portable first pass from any operating system with Python 3.9 or newer:

```text
python <skill-dir>/scripts/check_obligations.py --input <input.jsonl> --theorem-bank <rules.jsonl> --output-dir <output-dir> --emit-adjudication-template <pending.json>
```

If `<pending.json>` contains entries, fill each `response` directly as the
active host agent. After graph validation, the helper emits every unresolved
node in the current dependency frontier. Independent branches may appear in
the same round; a node with an unresolved ancestor remains blocked. Calculation
nodes also remain behind unresolved earlier context-changing nodes. When only
heuristic dependencies are available, the helper conservatively emits only the
earliest unresolved node. A proof-level `graph`
entry is emitted first and must be completed from the entire supplied node
list; its `node_id` is `0`. Use
`references/gap_completion_standard.md` for `proof` entries and
`references/calculation_adjudication_standard.md` for `calculation` entries.
Use `references/diagnosis_adjudication_standard.md` for `diagnosis` entries.
For `proof_diagnosis` and `calculation_diagnosis`, fill `primary_response`
under the corresponding proof or calculation contract. If that response does
not close the node, fill `diagnosis_response` in the same host turn; otherwise
set it to null. Legacy separate entries and response files remain valid.
Use `references/theorem_verification_standard.md` for `theorem` entries. Web
search is required only when no emitted local candidate verifies the proposed
necessary theorem.

The initial frontier also contains one submission-level `ambient` entry. Fill
every proof-instance result in that one response. Each typed fact must use an
allowed fact kind and derivation rule, quote source text from the theorem or
assumptions, and give one short reason. Record uncertain candidates under
`abstained_conditions`. The checker rejects incomplete coverage, unsupported
fact shapes, evidence not present in the source, and facts inferred from topic
labels or student proof steps. Valid facts are reused by every node in their
proof instance and participate in node-cache fingerprints.

Pending files contain one top-level `rule_dictionary`. Node inputs refer to
retrieved candidates through `retrieved_rule_refs`, so an identical scored rule
is serialized once per pending frontier. Resolve every reference before
adjudicating the node; the canonical result still stores its full
`retrieved_rules` trace.

The checker may conservatively build a two-node linear graph without a host
round when the second node explicitly continues the first and neither node has
ambiguous, branching, or cross-reference language. All other graphs still
require a validated host response. It may also replay a complete, exact numeric
relation or one supported identity axiom deterministically. Calculation
classification requires a complete parseable relation/chain or explicit
calculation language; a prose sentence is not a calculation merely because it
contains an equals sign. Safe replay accepts exact rational/decimal arithmetic,
perfect-square radicals, numeric absolute values and relation chains, plus a
small set of checker-owned one-axiom symbolic identities. It rejects the entire
replay when any expression fragment is unsupported; unsupported expressions
remain host obligations.
Resume with:

```text
python <skill-dir>/scripts/check_obligations.py --input <input.jsonl> --theorem-bank <rules.jsonl> --output-dir <output-dir> --adjudications <round-1.json> --adjudications <round-2.json>
```

For repeated resume rounds, enable the optional dependency-aware node cache and
reuse one stable output directory:

```text
python <skill-dir>/scripts/check_obligations.py --input <input.jsonl> --theorem-bank <rules.jsonl> --output-dir <output-dir> --node-cache <cache.json> --write-changed-only --adjudications <round-1.json> --adjudications <round-2.json>
```

The cache is a derived optimization artifact, never mathematical evidence. A
node is reusable only when its checker version, theorem bank, proof context,
claim, graph entry, predecessor results, accepted claims, calculation context,
local context, adjudicator configuration, and node-level host responses have
the same validated content fingerprint. A changed node therefore invalidates
every affected descendant.
Malformed or obsolete caches are ignored. `--write-changed-only` preserves an
existing result or pending file when its serialized content is unchanged.
Direct Python callers that supply runtime adjudicator callbacks must also
supply a stable `adjudicator_key` in `cache_context`; otherwise caching is
disabled for that result.

For automatic resume, create a session once:

```text
python <skill-dir>/scripts/check_obligations.py --input <input.jsonl> --theorem-bank <rules.jsonl> --session-dir <session-dir>
```

Fill `<session-dir>/pending.json` in place. Every later round needs only:

```text
python <skill-dir>/scripts/check_obligations.py --session-dir <session-dir>
```

The session manifest freezes the input, theorem bank, output paths, and checker
options. Each resume imports filled pending responses and optional explicit
`--adjudications` files into `responses.jsonl`, then writes the next frontier.
The session-owned node cache and changed-only writes are enabled automatically.
If predecessor acceptance changes a calculation node's effective source
endpoint, the checker invalidates the stale endpoint binding and emits that
node again even when the stored response claimed a non-undetermined decision.
With a validated graph, an independent calculation uses the theorem assumptions
as its stable source endpoint; unrelated accepted nodes cannot move it.

Do not stop after emitting pending obligations. Do not invoke a separate model
API merely to replace the active host agent. Missing or invalid responses must
remain `undetermined`. Repeat emit, adjudicate, and resume until no pending
entry remains or a round makes no progress. In legacy mode, pass every
completed prior-round file when resuming. In session mode, the response ledger
preserves all earlier validated context automatically.

The portable path uses only the Python standard library. Paths are handled
with `pathlib`, so `/`, Windows drive paths, and platform-native separators are
supported. Relative input paths are resolved from the current directory first
and then from a discoverable project root. Relative output paths use that same
project root. An explicit `--uncertain-policy model` provider adapter exists for
standalone automation, but it is not the default Agent Skills workflow.

The helper performs deterministic parsing, retrieval, context propagation, and
response validation. The activated host agent performs unresolved mathematical
reasoning. This boundary makes the same skill usable by Codex, Claude Code,
Gemini CLI, OpenCode, OpenClaw, and other Agent Skills clients.

## Implementation Rules

- Keep skill-authored rules and source text in English ASCII. Preserve original
  Unicode in proof inputs, adjudication exchanges, and user-facing outputs.
- Do not collapse gaps and invalid steps into one label.
- Treat theorem-linked common misuses as diagnosis evidence, not as the verifier itself.
- Prefer bridge-lemma repairs over full proof rewrites.
- Preserve the proof order when finding the first problem.
- Never use a cache hit when any dependency-aware fingerprint component changed.
