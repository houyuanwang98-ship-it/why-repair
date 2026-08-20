# M7 authorized Codex AI proxy review — interrupted partial run

This directory preserves the authorized M7 Codex CLI review progress produced
on 2026-08-20 before the user needed to shut down the machine.

## Completed scope

- 13 completed batches, each containing 3 cases.
- 39 completed cases, from `opc250-001` through the 39th selected case
  (`opc250-070`) in the frozen 144-case scope.
- 36 candidate mappings were corrected, 2 were confirmed, and 1 was marked
  undetermined.
- All 39 model rows reported high confidence.
- No completed batch required a runner retry, timed out, or failed schema
  validation.

Batch 14 was interrupted while in progress. Its immutable request and prompt
are retained, but it has no `attempt_result.json` or model output and must not
be counted as completed evidence.

## Evidence boundary

This is an AI proxy review, not human review, independent Gold, formal M7
acceptance, or a scientific result. It must not update frozen annotations
without subsequent human review. The original `run_manifest.json` records the
intended 144-case scope; `partial_run_summary.json` records the actually
completed subset at interruption.

