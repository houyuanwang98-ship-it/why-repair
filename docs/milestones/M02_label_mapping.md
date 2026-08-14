# M2 benchmark labels to M1 v0.3 runtime mapping

Status: `approved_for_m2.2_and_m1_v0.3`

This document makes the conversion boundary explicit. Person B does not apply
the mapping implicitly; Person A and Person B must approve it before a Gold
release or M3 adapter consumes M2 labels.

| M2 benchmark label | M1 v0.3 result | Conversion rule |
|---|---|---|
| `no_error` | `accepted` | Only with `valid`, no problem location, no repair, and no counterexample. |
| `proof_gap` | `accepted_with_gap` | Only with `valid_with_gap`, a gap location, and a nonempty minimal repair. |
| `missing_assumption` | `unsupported / missing_assumption` | Direct mapping; adding the assumption changes the original problem. |
| `theorem_misuse` | `unsupported / theorem_misuse` | Direct mapping after the invoked theorem and its unmet condition are recorded. |
| `algebraic_invalidity` | `unsupported / algebraic_invalidity` | Direct mapping after the first failed transformation is identified. |
| `target_shift` | `unsupported / target_mismatch` | Spelling conversion only. |
| `quantifier_error` | no automatic mapping | Requires Person A diagnosis; map to `target_mismatch`, `dependency_error`, or another concrete M1 category. |
| `false_generalization` | no automatic mapping | Requires a checked scope. Use `false_local_claim` or `false_theorem` only with a valid structured counterexample certificate; otherwise remain `unsupported`. |
| `undetermined` | `undetermined` | No positive or negative mathematical claim may be inferred. |

## Counterexample conversion

An M2 certificate can be considered for M1 conversion only when:

1. `counterexample_status=valid`;
2. every source assumption appears exactly once with `satisfied=true` and evidence;
3. `target_false=true`;
4. `scope=local_node` names an existing node, or `scope=original_theorem` uses `claim_ref=theorem`;
5. the adapter binds the certificate to exact M1 node/theorem versions and the global-assumption digest.

M2 evidence is benchmark annotation evidence, not an executable M1
`CounterexampleCertificate` until the final version and digest bindings are
created by the adapter.

## Approval gate

Person A and Person B approved this boundary for the frozen `m2.2` Gold and
M1 v0.3 adapter. Future label or contract changes require a new mapping version;
tools must not infer mappings beyond the table above.
