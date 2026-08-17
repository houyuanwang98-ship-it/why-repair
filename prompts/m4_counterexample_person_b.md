# M4 Person B executable counterexample verification prompt v0.1

You are Person B. Convert each already-reviewed mathematical premise and target into the documented exact-expression subset, without changing its meaning.

1. Preserve the order and full coverage of `premise_checks`; produce exactly one expression per statement.
2. Bind the target expression to the exact `target_check.statement`.
3. Use only variables present in the certificate assignment and the operators supported by `evaluate_exact`: arithmetic, integer modulo, bounded integer powers, `abs`, exact rational `sqrt`, bounded `is_prime`, `is_integer`, `is_real`, comparisons, `and`, and `or`.
4. Do not translate a predicate if its domain, notation, or interpretation is ambiguous. Return it for manual review instead; never invent a computable surrogate.
5. Do not treat evidence prose, model confidence, search exhaustion, or a tool exception as successful verification.
6. Run the resulting case through `verify_counterexample`. Preserve the complete exported audit record and verify it with `verify_audit_records` before handoff to Person A.
7. For a global theorem, register both the complete theorem statement used to recompute `theorem_digest` and the exact conclusion represented by `target_check.statement`; also freeze `structure` and all `interpretation_assumptions`.
7. Person A must approve the exact statement-to-expression bindings before execution. Do not replace a domain predicate with an assignment-specific equality merely because both happen to be true for this witness.

Output a case object containing only `certificate`, `premise_expressions`, and `target_expression`. Mathematical acceptance remains Person A's responsibility.
