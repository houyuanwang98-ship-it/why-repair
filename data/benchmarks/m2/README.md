# M2 pilot benchmark workspace

This directory separates source problems, independent annotations,
adjudication, and released gold labels. Do not place one annotator's labels in
the source file, and do not overwrite either independent annotation during
adjudication.

Expected layout after the 50 source problems are added:

```text
source/pilot_50.jsonl
annotations/person_a.jsonl
annotations/person_b.jsonl
adjudication/disagreements.jsonl
adjudication/decisions.jsonl
reports/agreement.json
gold/algebra_pilot_v1.jsonl
```

`annotations/person_a.template.jsonl` is an abstaining handoff template only.
Person A must review the source independently and save the completed result as
`annotations/person_a.jsonl`. The template must never be passed to the
agreement command as if it were a completed annotation.

The source JSONL uses the frozen source contract `m2-source-0.1`: `proof_id`,
`theorem_version`, `domain`, `theorem`, `assumptions`, and ordered `proof_steps`
objects containing stable `node_id` and `text` fields.

Each independent annotation row uses `schema_version: "m2.2"` and contains.
The portable schema is `schemas/m2_benchmark_v0_2.schema.json`; the Python
validator additionally checks source membership, step bounds, exact assumption
coverage, and cross-file identity constraints.

```json
{
  "schema_version": "m2.2",
  "sample_id": "alg_001",
  "annotator_id": "person_b",
  "validity_status": "undetermined",
  "first_gap_step": null,
  "first_invalid_step": null,
  "error_type": "undetermined",
  "counterexample_status": "undetermined",
  "counterexample": null,
  "minimal_repair": null,
  "notes": ""
}
```

When `counterexample_status` is `valid`, `counterexample` must be a structured
certificate containing its local/theorem scope, exact claim reference,
assignments, one true evidence-backed check for every source assumption,
`target_false: true`, a verification method, and verification notes. Free text
in `notes` is never sufficient counterexample evidence.

Run structural validation (this does not judge mathematical correctness):

```text
python scripts/validate_m2_annotations.py --source data/benchmarks/m2/source/pilot_50.jsonl --expected-count 50
python scripts/create_m2_annotation_template.py --source data/benchmarks/m2/source/pilot_50.jsonl --annotator person_b --output data/benchmarks/m2/annotations/person_b.jsonl
```

After independent annotation, create the agreement report and disagreement
queue:

```text
python scripts/report_m2_agreement.py --source data/benchmarks/m2/source/pilot_50.jsonl --person-a data/benchmarks/m2/annotations/person_a.jsonl --person-b data/benchmarks/m2/annotations/person_b.jsonl --report data/benchmarks/m2/reports/agreement.json --disagreements data/benchmarks/m2/adjudication/disagreements.jsonl
python scripts/create_m2_adjudication_template.py --disagreements data/benchmarks/m2/adjudication/disagreements.jsonl --output data/benchmarks/m2/adjudication/decisions.jsonl
python scripts/validate_m2_adjudications.py --disagreements data/benchmarks/m2/adjudication/disagreements.jsonl --decisions data/benchmarks/m2/adjudication/decisions.jsonl
```

The agreement report contains exact agreement, Cohen's kappa, and a sparse
confusion matrix for every compared field. The generated decision queue is
intentionally incomplete: both reviewers must supply an allowed final value,
a disagreement type, evidence, a rationale, and two distinct adjudicator IDs.
The report also records SHA-256 digests for all three inputs so every metric
artifact can be traced to exact source and annotation versions.

After both reviewers record an evidence-backed decision for every field-level
disagreement, build gold data:

```text
python scripts/build_m2_gold.py --source data/benchmarks/m2/source/pilot_50.jsonl --person-a data/benchmarks/m2/annotations/person_a.jsonl --person-b data/benchmarks/m2/annotations/person_b.jsonl --adjudications data/benchmarks/m2/adjudication/decisions.jsonl --output data/benchmarks/m2/gold/algebra_pilot_v1.jsonl --manifest data/benchmarks/m2/gold/algebra_pilot_v1.manifest.json
```

Gold generation fails closed when any disagreement lacks adjudication.
It always writes a companion manifest (the default is `<output>.manifest.json`)
that binds the gold bytes to source, both annotation files, the adjudication
file, the contract version, and the deterministic generator name.

The proposed M2-to-M1 conversion is documented in
`docs/milestones/M02_label_mapping.md`. No automatic conversion is permitted
until both project members approve it.
