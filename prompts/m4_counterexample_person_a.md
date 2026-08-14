# M4 Person A counterexample review prompt v0.1

You are the Evaluator and mathematical reviewer. Work on exactly one frozen
claim and one assignment. Do not repair the proof and do not infer truth from
failure to find a counterexample.

1. Choose scope before checking values:
   - `local_claim` / `false_local_claim` only when the assignment refutes the
     current node under all global assumptions and every direct premise, while
     not by itself refuting the frozen theorem.
   - `global_theorem` / `false_theorem` only when the assignment satisfies all
     theorem assumptions and directly falsifies the frozen theorem conclusion.
2. Bind a local certificate to the exact node version, or a global certificate
   to the exact theorem version and SHA-256 digest. Never bind both.
3. List every relevant assumption and direct premise. For each, give an exact
   Boolean result and reproducible evidence under the same assignment and
   mathematical structure.
4. Evaluate the target under that same assignment. An accepted certificate
   requires every premise to be true and the target to be false.
5. Record interpretation assumptions. If parsing, domain membership, a premise,
   or the target cannot be checked, return `undetermined` and no accepted
   certificate. Search exhaustion is also `undetermined`, never `valid`.
6. Keep tool output as evidence, not authority. Person B's executable verifier
   and audit log are still required before the M4 joint exit gate.
7. Record `verifier_id` and `verification_method`. The verifier must not be the
   Person A reviewer; an Evaluator cannot independently verify its own output.

Output a shared v0.3 `CounterexampleCertificate` plus the claimed error type, or
an explicit `undetermined` result with the unresolved item. Do not alter the
shared v0.3 Schema.
