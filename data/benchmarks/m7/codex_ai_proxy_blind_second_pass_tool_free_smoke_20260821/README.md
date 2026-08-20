# M7 blind second-pass tool-free smoke — 2026-08-21

This smoke verifies the hardened execution configuration before rerunning the
eight cases from full-run batches 024 and 027. Codex ran with `shell_tool` and
`skill_search` disabled, the global `math-proof-repair-agent` skill explicitly
disabled, user config and rules ignored, an empty read-only working directory,
and an ephemeral session.

The one two-case batch completed on its first attempt in 92,105 ms. It used
23,412 input tokens, 4,593 output tokens, and 4,142 reasoning output tokens.
There were no tool items, transport errors, fallbacks, failures, timeouts, or
malformed JSONL lines. All evidence-integrity, blind-input, tool-free,
output-semantics, and completeness gates pass.

`opc250-201` reproduced the original full-run location at `n26`. `opc250-220`
changed from `invalid_localized` at a late numerical example to
`valid_no_error`; the conflict is retained and requires node-level
adjudication. Neither output is treated as Gold.

Audit with:

```bash
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_smoke_20260821
```
