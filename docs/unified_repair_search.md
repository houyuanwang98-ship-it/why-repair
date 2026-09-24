# Unified explicit repair search

`harness.repair_search.RepairSearch` coordinates diagnosis, current-error episodes,
contract review, candidate generation, staged candidate review, explicit routing,
and whole-proof rescanning. It contains no model client. Callbacks must be supplied
by a caller; the bundled replay uses only disclosed fixtures.

```python
from harness.repair_search import RepairSearch, CallResult

workflow = RepairSearch(session, max_attempts=8, max_routes=4, max_feedback=20)
report = workflow.evaluate(external_evaluator, max_calls=8)
if report["state"] == "error_confirmed":
    draft = workflow.begin()
    # Optionally select_route("expand") or select_route("rewrite") explicitly.
    workflow.review_interface(proposed_outputs, external_contract_reviewer)
    request = workflow.generate_and_prepare(external_generator)
    outcome = workflow.review_candidate(request["input_digest"], external_patch_reviewer)
    if outcome["state"] == "applied_requires_rescan":
        report = workflow.evaluate(external_evaluator, max_calls=8)
```

For insertion/deletion, pass `policy="region-topology-replacement-v2"` to
`generate_and_prepare`. See [topology rules](region_topology_v2.md).
The generator receives the controller's base digest, generator ID, selected patch
policy, editable nodes, admissible upstream nodes and outputs marked as targets.

The shared session ledger covers both older constrained search classes and this
entrypoint. Defaults are 8 candidates, 4 explicit routes and 20 feedback actions;
omitted limits inherit the existing values. Recreating wrappers or switching APIs
cannot reset limits. Successful patches and localization calls additionally obey
the original session limits. Exact refutation replay consumes feedback too.
Imported localization responses share the scan/session review budget while contract
search is active, including unused or malformed submissions; over-budget imports
are recorded and not admitted. They cannot bypass the callback review limit.

Generation is charged **before** the callback. Timeouts, malformed patches,
duplicates, failed reviews and rejected candidates consume their respective
budgets. Failed review replies cannot be retried against the same pending candidate.
A new interface review failure revokes its previous acceptance. Once contract
search attaches to a session, public direct `session.apply_patch` is disabled;
staged constrained application uses an internal controller path. These objects
are trusted serial Python code, not a sandbox against callers editing internals.

`route_options` explains a refuted interface, exhausted budget, missing interface
review or explicit optional choice. It never chooses an action or equates exhausted
search with an irreparable theorem. Expanding does not replenish candidate budget;
reserve an adequate global budget before starting. No cost-optimal route, success
probability or automatic local→expand→rewrite policy is asserted.

Each callback may return its plain response or:

```python
CallResult(response, usage={
    "input_tokens": 100, "output_tokens": 30, "total_tokens": 130,
    "cost": "0.002", "currency": "USD",
}, evidence_kind="external")
```

Usage fields are caller-supplied measurements, not independently verified billing.
Omitted token/cost fields stay null. A failed callback without returned usage also
stays unavailable. Event latency is measured around the callback. Reasoning and
cached-token counts may overlap provider totals and are **not added** to them.
Currency subtotals remain separate; mixed currencies have no aggregate cost.

The snapshot records diagnosis, contract review, candidate generation, candidate
review, revalidation and final audit, including failures and imported responses.
Measured subtotals are separated from totals. Any unmetered lower-level search
event or localization callback makes total cost unavailable. Even a callback that
returns evidence may later fail a protocol check; its cost remains counted.
Automatic local arithmetic and explicit routing are recorded in the proof/search
ledgers and do not imply a provider charge. Latency totals cover measured callbacks,
not total process runtime. External activity bypassing all these APIs cannot be
discovered by this in-process accounting layer.

Snapshots are review/export records, not executable resume files. The implementation
does not offer persistent recovery, concurrent commits, calibrated routing or
general semantic verification. Pending independent mathematical review and real
experiment authorization are not replaced by fixture tests.

Replay: `python scripts/run_repair_search_demo.py --output outputs/repair_search_demo.json`.
It includes a disclosed failed-generation fixture, explicit expansion, accepted
repair, rescan and final target audit, with unavailable token/cost measurements.
