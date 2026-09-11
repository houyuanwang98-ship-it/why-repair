# M7 blind AI second-pass clean smoke — 2026-08-21

This is the clean-start rerun of the two-case smoke after fixing the runner to
capture repository state before writing any evidence. Both the run manifest and
attempt request bind clean commit
`ba26564d40d4d34f81c838248bb0fa6a13d0f970` with
`repository_dirty_at_run_start=false`.

The isolated Codex call completed in 21,152 ms with 19,098 input tokens, 592
output tokens, and 327 reasoning output tokens. It had no failed or timed-out
attempts, malformed JSONL, transport error events, or fallback items. The raw
prompt contains only `case_id`, `problem`, and `proof_nodes` for `opc250-037`
and `opc250-080`.

Both cases were again classified `valid_no_error` with high confidence and no
theorem dependency. This agrees with the prior smoke and the separate
dependency-guided mathematical check. It remains AI proxy evidence, not human
review, frozen Gold, or a formal M7 result.

Audit with:

```bash
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_smoke_v2_20260821
```

The audit must report all four checks as true.
