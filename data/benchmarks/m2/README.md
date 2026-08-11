# M2 pilot benchmark

`pilot_50.jsonl` contains the shared, immutable source items. It contains no annotator answers.

`person_a_annotation_template.jsonl` is a blank working template. Person A's completed annotations belong in `private/person_a_annotations.jsonl`, which is intentionally ignored by Git while the separately reviewed shards are being prepared for merge.

Person B should create, annotate, and review a different 50-item shard on their own branch. This branch does not define or fill Person B artifacts. The two locked shards will later be normalized, deduplicated, and merged; this design does not support same-item inter-annotator agreement claims.
