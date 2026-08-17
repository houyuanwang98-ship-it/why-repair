# M3 human audit v1

This directory records the post-run human audit of the frozen full-50 run.
The session predictions remain unchanged.

The audit adopts one localization rule: when a validated counterexample
refutes the original theorem, proof-step first-invalid localization is not
applicable. The false theorem remains part of proof-validity and error-type
evaluation.

`m2-037` is recorded as `theorem_misuse` for taxonomy compatibility, with the
more precise subtype `circular_reasoning` preserved in the audit record.
