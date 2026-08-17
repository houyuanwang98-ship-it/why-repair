# M4 external evidence completion

The repository has exhausted what can be established retrospectively. The remaining evidence must be produced prospectively; identities, independence, timestamps, or human decisions must not be synthesized by the project authors or an AI agent.

## Two independent human reviews

Give each reviewer the frozen counterexample archive separately. Reviewers must not use model assistance or see the other review before locking their decision. Each reviews all 11 sample IDs, signs the exact archive bytes with an independently controlled SSH key and namespace `why-repair-m4`, and supplies an `allowed_signers` file. Populate the two packet slots only from those returned materials. The verifier rejects metadata-only, duplicate-identity, missing-file, invalid-signature, and non-SSH submissions.

Example signing command:

```powershell
ssh-keygen -Y sign -f <reviewer-private-key> -n why-repair-m4 data/benchmarks/m4/revalidation/global_counterexample_replay_v1.json
```

## Prospective blind run

Create genuinely new challenges outside the exposed M2/M3 corpus. A custodian keeps Gold inaccessible, records and hashes the challenge, and sends only the challenge to the generator. Lock and hash candidate output before revealing Gold. Then score it and complete `prospective_blind_run_v1.template.json`. The strict audit may treat historical independence as superseded only after this record passes chronological and hash checks; it must never rewrite the historical claim.

These steps require real external actors. A local automated replay is useful regression evidence but is not an independent human review or a blind discovery experiment.
