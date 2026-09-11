# M5 Codex CLI runtime smoke v0.1

This directory preserves every real call made while validating the API-key-free
Codex CLI runtime on 2026-08-20. These are AI-generated engineering smoke
artifacts, not human review, frozen Gold, formal M5 acceptance, or scientific
results. Every run summary keeps `scientific_claim_allowed=false`.

## Retained runs

| Directory | Code commit | Calls | Outcome | Config SHA-256 | Summary SHA-256 |
| --- | --- | ---: | --- | --- | --- |
| `schema_failure_unique_items/` | `3e0ed758f0b6a490eae91ad55ca404623912601d` | 6 | Three assignments exhausted one retry each because Codex rejected `uniqueItems`. | `7856ef755b04849313fed022e1dc3456f5f286ecd8c89c05a46a055ee428fdaf` | `a0899db16a411bedfd96745b08b22a569b85b67d41fbe2138c8e84560936faef` |
| `schema_failure_missing_type/` | `c107b980b245863e7c944d4fac7f23f7fb14f733` | 3 | Three non-retried configuration failures because `const`/`enum` schemas lacked explicit primitive types. | `2ac5f2e97f929593b8428bbbfe79fbeff6b10654eea450f8e5f15ca07a612c3a` | `f98e29e35b754fa1e97d5e178eb1b3f4089eb48a92ff5c8a42146de83dd4f798` |
| `successful_and_budget_bound/evidence/` | `29b3fab08605c0d0b70edefe6b71f0abcc813ccb` | 2 | `m2-011` succeeded; `m2-018` returned schema-valid output but crossed the frozen cumulative 24k-token batch budget; `m2-034` was not called in this batch. | `6e4786ccdc984bb4efc2e2a337ba3fe95ed04ce9c074c8b3f8f3100822cb1673` | `0aa79a01d02725f568829dfd58bf88501b0e2eb59635b77d5660a374cfcd0eaf` |
| `successful_and_budget_bound/evidence-m2-034-only/` | `29b3fab08605c0d0b70edefe6b71f0abcc813ccb` | 1 | `m2-034` succeeded under an independent unchanged 24k-token limit. | same config | `f725a4d3ff36db29bc84baf3b277c8a969e583bd1f351d91e06eccf3a95d518b` |

## Valid model outputs

- `m2-011`: `insert_before`, 15,503 total tokens, 21.29 seconds.
- `m2-018`: `replace`, 15,322 total tokens, 23.86 seconds; the output is
  preserved but its batch terminal status is `budget_exhausted`.
- `m2-034`: `replace`, 15,416 total tokens (14,080 cached input tokens),
  19.41 seconds.

The saved-account Codex CLI runtime exposes neither a Responses API response ID
nor a per-call USD amount. Those fields are deliberately `null`; thread IDs,
CLI version, raw JSONL events, exact prompts, outputs, tokens, latency and all
failed attempts are retained.

The observed input usage is about 14.9k tokens per isolated Codex invocation,
so the inherited 24k cumulative three-case smoke budget cannot accommodate all
three calls. This record does not alter that budget.
