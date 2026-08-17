# M2 Person B completion and handoff

> Historical handoff notice (2026-08-14): the waiting state below describes an
> earlier point in the workflow. A/B annotations, 74 adjudications, and frozen
> engineering Gold now exist. The authoritative current status and its strict
> evidence limitations are recorded in `M02_full_revalidation.md` and
> `data/benchmarks/m2/manifest.json`.

Status: `person_b_complete_waiting_for_person_a`

## Frozen inputs

- Source: `data/benchmarks/m2/source/pilot_50.jsonl`
- Source SHA-256: `7f10d1ecf2627f326402580e47055496b3a0041aef1a8e25f374e79ce85f8a0e`
- Person B annotation: `data/benchmarks/m2/annotations/person_b.jsonl`
- Person B SHA-256: `88241b23793e8d8ec7eaaea90d8505dc62891fc4ea702b65f983681657d6f403`
- Contract: `m2.2`

The desktop copy of `pilot_50.jsonl` was byte-for-byte identical to the frozen
source. Person B reviewed all 50 rows. The final distribution is 12 `valid`,
12 `valid_with_gap`, and 26 `invalid`; 12 invalid rows carry structured,
assumption-complete counterexample certificates.

## Person B verification completed

- Source and annotation coverage: 50/50.
- Stable sample IDs, theorem versions, node IDs, and step bounds validated.
- The `m2.2` state matrix and counterexample certificate contract validated.
- M2 tests: 27 passed.
- Full repository regression suite: 136 passed.
- No Person A labels were inspected or inferred while producing Person B's
  annotations.

## Independent Person A handoff

`data/benchmarks/m2/annotations/person_a.template.jsonl` contains 50 abstaining
rows and exists only to provide the exact field shape. It is not an annotation
result and must not be used to calculate agreement. Person A must work from the
frozen source without reading `person_b.jsonl`, replace every abstaining row
with an evidence-backed independent decision, and save the result as
`data/benchmarks/m2/annotations/person_a.jsonl`.

Validate Person A's completed file:

```text
python scripts/validate_m2_annotations.py --source data/benchmarks/m2/source/pilot_50.jsonl --annotations data/benchmarks/m2/annotations/person_a.jsonl --annotator person_a --expected-count 50
```

## Remaining joint pipeline

The following steps are intentionally blocked until the independent Person A
file exists:

1. Generate the field-level agreement report and disagreement queue.
2. Have both reviewers adjudicate every disagreement with evidence and a
   rationale; neither reviewer may overwrite the other's original annotation.
3. Validate complete adjudication coverage.
4. Build deterministic Gold and its hash-binding manifest.
5. Re-run M2 and full-repository tests, then freeze the M2 release record.

Commands and artifact paths for these steps are maintained in
`data/benchmarks/m2/README.md`. Gold generation fails closed when Person A is
missing or any disagreement remains unresolved.

## Completion boundary

Person B's independent annotation, validation, reproducibility binding, and
Person A handoff are complete. M2 as a two-person milestone is not complete
until Person A supplies an independent annotation and both people complete the
adjudication stage. Creating Person A labels from Person B's results would
invalidate the independence requirement and is therefore prohibited.
