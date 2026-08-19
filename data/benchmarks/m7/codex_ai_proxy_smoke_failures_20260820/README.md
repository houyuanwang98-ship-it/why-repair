# M7 Codex AI proxy smoke failures (2026-08-20)

These directories intentionally preserve unsuccessful or interrupted attempts. They are not
successful model outputs and must not be scored as mathematical reviews.

- `default_home_readonly/`: the runner terminated before any model request because the outer
  filesystem sandbox made the default `CODEX_HOME` read-only. The full request, empty stdout,
  stderr, attempt result, and run summary are retained.
- `outer_network_isolation_interrupted/`: a writable, isolated `CODEX_HOME` fixed initialization,
  but the outer command still had no network access. The process was manually interrupted after
  it remained pending. Only the immutable run manifest, request metadata, and complete stdin
  prompt existed at interruption time; no response, token usage, response ID, or billable cost was
  produced.

An escalated network run was then refused by the execution safety layer because sending the M7
problem/proof payload to an additional Codex service session requires explicit user authorization.
That rejected command never started and therefore has no local attempt directory.

All contents are engineering evidence only. They do not alter the frozen human verdicts, node
Gold, historical manifests, or M7 scientific gates.
