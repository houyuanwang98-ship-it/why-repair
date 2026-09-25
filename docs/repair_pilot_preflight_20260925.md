# Repair pilot startup — 2026-09-25

## Authorization and actual status

The user requested starting the small real-case pilot discussed in the conversation
and publishing progress to GitHub. This supersedes the earlier blanket instruction
not to run real evaluations. It does not settle provider/model selection, spending
limits, independent judging or authorize automatic routing.

Preflight base: `f00dc88`, branch `codex/iterative-first-error-v2`.
**No real provider calls were made. No repair-accuracy or cost-saving result exists.**

## Checks performed

- No `OPENAI_API_KEY` is present in process, user or machine environment; no root
  `.env` exists in this checkout. Only presence was checked; no credentials logged.
- The existing `ProviderRunner` requires that key and supports its OpenAI adapter.
  The new `RepairSearch` accepts callbacks; its demo is explicitly a fixture, not
  a production model integration.
- Unified workflow replay passed, including a simulated generation timeout charged
  to the attempt budget and post-patch rescan. Missing token totals stayed null.
- Topology replay passed, including deletion obligations, insertion, reconnection
  within the region and a final fixture review.
- Local outputs (ignored by Git):
  `outputs/preflight_20260925/unified_fixture.json` and
  `outputs/preflight_20260925/topology_fixture.json`.
- The immediately preceding sync validation ran 593 tests: 592 passed and one
  installer round-trip errored because timestamp-based backup directory names
  collided (`FileExistsError`). This was not repaired as part of the pilot startup.

Both replays use authored semantic responses and make zero production model calls.
Their `complete` state is not an independently validated mathematical success.

## Required next decisions

1. Configure credentials locally, select provider/model and a monetary cap. Do not
   send API keys in chat or commit them. If another provider is preferred, adapt
   and test that provider explicitly rather than relabel its outputs.
2. Freeze a small case manifest, immutable original proofs, mathematical conventions,
   prompts, settings, per-arm call/token caps and explicit routing schedule before
   observing outcomes. Existing sample Gold is not automatically suitable: for
   example `alg_001` calls an implicit rank-nullity inference a gap, which depends
   on the chosen proof-granularity rubric.
3. Establish independent final judging. Without it, label the run exploratory and
   outcomes unadjudicated; do not report human-confirmed success or false-completion
   rates. Never include Gold diagnoses in generation or online-review inputs.
4. Connect real callbacks to the unified workflow and preserve raw replies, failures,
   usage coverage and full rescan costs. Audit the older provider wrapper before
   reusing it: its exception records currently use zero token/cost values, and
   per-assignment budget counters are not a whole-experiment spending guard.
5. Run the bounded pilot, retaining all assigned failures/undetermined cases. Compare
   local repair with a clearly specified rewrite baseline only under matched budgets;
   distinguish bounded topology replacement from unrestricted whole-proof rewriting.

See `repair_experiment_readiness_20260925.md` for the broader proposed protocol.
Its historical "not authorized" status predates this user's startup request; the
unresolved configuration and review requirements still apply.
