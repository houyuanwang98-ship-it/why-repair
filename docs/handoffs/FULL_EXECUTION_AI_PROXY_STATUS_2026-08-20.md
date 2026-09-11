# Full execution and AI proxy status

Date: 2026-08-20  
Branch: `codex/full-execution-ai-proxy-20260820`  
Pulled baseline: `aafde1b643cfe9d50a464e43b9348f48609a42ae`  
Scope: deterministic reproduction, Provider runner hardening, active-session AI proxy review,
failure preservation, and formal-run blocker audit.

## Outcome

- The current branch passes the complete repository test suite: **453/453** tests passed.
- M3, M4, M5, M6 and the available M7 builders were executed in isolated `/tmp` copies so no
  frozen Gold, historical manifest, frozen hash, shared Schema semantics, metric definition, or
  status meaning was overwritten.
- M5's 36 existing patch sequences received a dependency-guided Codex AI proxy review: 24 were
  locally repairable and 12 were correctly disposed as irreparable false/undefined theorems. All
  36 sequences were accepted by the proxy audit. This is explicitly nonhuman, nonindependent, and
  ineligible as scientific Gold.
- A real OpenAI Provider run was **not** made: `OPENAI_API_KEY` is absent. The fail-closed command
  exits before adapter construction and records that no call was attempted.
- An additional isolated Codex review of the 144 pending/provisional M7 mappings was prepared, but
  no successful external call occurred. The first attempt failed before a request because the
  default runtime home was read-only; a second attempt was interrupted under outer network
  isolation; the requested network escalation was refused pending explicit user authorization to
  send the proof payload to the Codex service. Both local failed/incomplete attempts are retained.
- Formal M6/M7 science claims remain closed. Existing historical projections were rebuilt but were
  not relabeled as independent runs.

## Environment and evidence boundaries

| Item | Value |
|---|---|
| OS | Linux 6.18.42-1-lts x86_64, glibc 2.44 |
| Python | CPython 3.14.6 |
| isolated Provider venv | `/tmp/why-repair-provider-venv-20260820` |
| OpenAI SDK | `openai==1.109.1` |
| requested smoke model | `gpt-5.6-terra` |
| Provider API calls | 0 |
| Provider token / cost | 0 / 0 USD |
| active-session M5 proxy calls | 0 separate calls; current collaborator session only |
| M5 proxy model snapshot / response ID / tokens / latency | unavailable / null / null / null |

The temporary M5 Provider candidate used three cases (`m2-011`, `m2-018`, `m2-034`) and a
provisional 1 USD hard cap solely to validate the runner. It is not a frozen formal budget and was
not committed as a formal experiment configuration. Current model and price references were taken
from the official OpenAI model pages. The local authoritative M5 JSON Schema is preserved; the
Provider projection omits unsupported `allOf`/`if`/`then` keywords and every returned object would
still be validated locally against the full Draft 2020-12 schema.

## Deterministic reproduction ledger

### M3

Six build/evaluation/audit commands exited 0. Strict audit exited 1 with the expected result
`engineering_pass_strict_acceptance_blocked`. Metrics reproduced at 50/50 coverage, first-error
overall accuracy 0.8, critical dependency omission rate 0.0517241379, node false acceptance rate
0.1, and proof false acceptance rate 0.0384615385.

The only tracked difference in the isolated copy is the known line-ending directory digest:

```text
cba2ae... (historical CRLF digest) -> 8cc5f2... (current LF digest)
```

No historical file was changed in the real worktree.

### M4

Replay and ordinary audit exited 0. Strict audit exited 1 with the expected
`engineering_pass_strict_acceptance_blocked`; all 11 global counterexamples were verified, neither
negative control was accepted, and external calls/cost were zero. The current-machine 50-round
operational replay benchmark had median 7.470 ms, mean 7.484 ms, and p95 7.643 ms. Its temporary
JSON SHA-256 is `ec7643af6399fa5cfbc3a005ab0f70abb266ac43d2b485777a4c7f22c4ab9738`.

### M5

`materialize_m5_batch_v0_2.py` rebuilt cleanly. `verify_m5_external_evidence.py` exited 1 with the
expected `incomplete_or_invalid_external_evidence`. The new proxy review is at
`data/benchmarks/m5/codex_ai_proxy_review_v0_1/review.json`; its SHA-256 is
`f4fb2e749b025fdf38b4a9b59450c062433c6fc16d6b5e09879f1f16235f4b2d`.

### M6

- Engineering fixture rebuilt: 9 methods x 2 cases = 18 assignments.
- Codex built-in engineering smoke rebuilt: 9 methods x 3 cases = 27 assignments; 16 projected
  accepted repairs, 2 partial outcomes, and 9 diagnosis-only outcomes.
- Historical full projection rebuilt: 9 methods x 50 cases = 450 assignments.
- All have Provider calls 0 and cost 0. The 27- and 450-assignment artifacts share reasoning or
  historical predictions and therefore cannot support method comparisons.

### M7

- The OPC formal candidate contains 250 cases and passes the 200-500 count gate.
- Current proof composition is 191 incorrect and 59 correct; all incorrect proofs have a mapped or
  provisional first-error position.
- Of 155 AI-localized incorrect proofs, 14 have case-level human coverage and 141 still need mapping
  review. Three additional cases (`opc250-078`, `opc250-085`, `opc250-179`) have only provisional
  Codex mappings. The prepared AI proxy scope is therefore 144 cases.
- Available deterministic preflight, transfer, rebuilding, audit, 50-case engineering, blind-review
  packaging, finalization, and ProofNet planning builders were exercised in an isolated copy.
- Two importer invocations intentionally failed closed after a template materializer recreated blank
  human answer forms in that isolated copy (`empty human response` / `requires exactly one human
  answer`). Those failures were not applied to the real worktree.
- Formal readiness remains `blocked_requires_human_and_external_evidence`: M5 live entry, M6 formal
  exit, independent Gold/adjudication, and Provider run evidence are absent. User execution release
  remains valid while `scientific_claim_allowed` remains false.

## Provider runner changes

The hardened runner now records raw requests before calls, raw responses, immutable manifests,
exact SDK/model/config/digests, input/cached/output/total tokens, latency, retries, failures and
frozen price-based cost. Batch budgets cover all assignments and retries; schema-invalid responses
still consume recorded tokens/cost; duplicate attempts and unsafe IDs fail closed; SDK retries are
disabled; and exact repository commit plus clean worktree are required.

The run CLI now exits cleanly with:

```text
OPENAI_API_KEY is not configured; no Provider call was attempted
```

## Preserved failed AI-proxy attempts

The complete local artifacts are under
`data/benchmarks/m7/codex_ai_proxy_smoke_failures_20260820/`. They preserve the exact input prompt,
request metadata, stdout/stderr where produced, attempt result, run manifest, and run summary. No
successful response, response ID, token usage, or cost exists for these attempts.

## Remaining external blockers

1. A real M5 Provider pilot requires an injected `OPENAI_API_KEY` and an explicitly approved hard
   budget; formal budget semantics were not changed.
2. Independent M6 nine-method and M7 144-case Codex proxy calls require explicit authorization to
   transmit the repository's problem/proof payloads to that service.
3. A publication-grade M6/M7 run still needs frozen formal configs and the project's existing
   scientific gates; AI proxy review does not silently replace human Gold or open those gates.
