# M7 blind second-pass tool-free eight-case rerun — 2026-08-21

This directory reruns the eight cases from full-run batches 024 and 027 after
the strict audit found one read-only global-skill lookup in each batch. The raw
full run remains unchanged. This rerun uses a new clean commit, new output
directory, ephemeral session, empty read-only working directory, ignored user
config/rules, disabled shell and skill-search features, and an explicitly
disabled `math-proof-repair-agent` skill.

Both four-case batches completed on their first attempt. Total usage was 52,467
input tokens, 12,032 cached input tokens, 7,784 output tokens, and 6,206
reasoning output tokens. There were no tool items, transport errors, fallbacks,
failures, timeouts, malformed JSONL lines, schema failures, or order failures.
All five audit gates pass.

Seven cases retain the same invalid/valid assessment as the archived full run;
six also retain the same first-error node. The material conflicts are:

- `opc250-202`: both say invalid, but the first-error node moves from `n21` to
  `n18`;
- `opc250-203`: both say invalid, but the first-error node moves from `n24` to
  `n25`;
- `opc250-220`: the archived full run says a late false numerical example at
  `n65`; this tool-free rerun says the proof is valid under Gauss/Dirichlet
  composition.

These conflicts are retained for dependency-guided adjudication. No frozen
mapping or Gold is changed.

Audit with:

```bash
python scripts/audit_m7_blind_second_pass.py \
  data/benchmarks/m7/codex_ai_proxy_blind_second_pass_tool_free_rerun_20260821
```
