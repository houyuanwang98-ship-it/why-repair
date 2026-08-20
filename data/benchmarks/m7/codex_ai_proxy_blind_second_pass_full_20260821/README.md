# M7 blind AI second pass — full 124-case run (2026-08-21)

This directory preserves the complete 124-case blind second-pass Codex AI proxy
run. The model input projected exactly `case_id`, `problem`, and ordered
`proof_nodes`; it excluded the frozen verdict, candidate mapping, first-pass
output, scope, and Gold. The run is AI evidence only and does not change frozen
annotations or open the formal M7/scientific gate.

All 31 four-case batches completed on their first runner attempt. There were no
terminal failures, timeouts, malformed JSONL lines, top-level transport errors,
or fallback error items. Recomputed usage is 848,289 input tokens, 341,504
cached input tokens, 124,662 output tokens, and 99,621 reasoning output tokens.
Provider response IDs and per-call subscription cost were unavailable.

The outputs contain 116 `invalid_localized`, 6 `valid_no_error`, and 2
`undetermined` assessments. Confidence is high for 123 cases and medium for one.
Six rows request theorem verification. These distributions are not Gold or
scientific metrics.

The first strict audit found one isolation caveat that is preserved rather than
hidden: batches 024 and 027 each made one read-only shell call to the global
`math-proof-repair-agent/SKILL.md`. The empty model working directory stayed
empty, and neither call accessed the repository, first-pass evidence, candidate
mapping, or Gold. Nevertheless, those eight cases fail the protocol's stronger
tool-free requirement. They must be rerun in a separate directory with the
shell and skill-search features disabled; this directory remains immutable.

Run the current audit with:

```bash
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_full_20260821
```

Evidence integrity, blind-input isolation, output semantics, case completeness,
and ordering must pass. `tool_free_execution_passed` is expected to remain
false for this archived run.
