# Codex CLI runtime migration — 2026-08-20

## Outcome

All active Python model-call paths now execute `codex exec` with the user's
saved Codex CLI account session. The repository no longer imports the OpenAI
Python SDK, checks `OPENAI_API_KEY`, or computes API-list-price costs.

Historical manifests, frozen hashes and prior reports are not rewritten. They
remain evidence of the runtime used when they were produced.

## Runtime contract

- Every call uses an ephemeral session and a temporary isolated working root.
- Model-generated commands are restricted by the Codex read-only sandbox.
- Project/user execution rules and user config are ignored for experiment
  isolation; authentication still comes from `CODEX_HOME`.
- `OPENAI_API_KEY` and `CODEX_API_KEY` are explicitly removed from the child
  environment, so a configured key cannot silently replace saved CLI login.
- Structured outputs use `--output-schema` and are validated locally.
- `--json` JSONL events, stderr, final output, thread ID, token usage, latency,
  retries, timeouts and failures are retained where the calling workflow keeps
  evidence.
- Codex CLI does not expose a Responses API response ID, exact returned model
  snapshot, or per-call USD amount for saved-account runs. Those fields remain
  `null`, with explicit availability notes; no value is estimated or invented.

## Active entrypoints

- `scripts/run_baseline.py`
- `scripts/prepare_m5_codex_smoke.py`
- `scripts/run_codex_smoke.py`
- `check_obligations.py --uncertain-policy model`
- `scripts/run_codex_ai_proxy_review.py`

The historical `prepare_m5_provider_smoke.py` and `run_provider_smoke.py`
filenames are retained as compatibility aliases to the same Codex CLI backend.

## Official behavior used

The implementation follows the official Codex non-interactive-mode contract:
`codex exec` can read stdin, emit JSONL events, constrain the final answer with
an output schema, write the final message separately, run ephemerally, and
reuse CLI authentication. See:

- <https://learn.chatgpt.com/docs/non-interactive-mode.md>
- <https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-exec>
