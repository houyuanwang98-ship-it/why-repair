# Explicit topology replacement v2

This opt-in transaction extends RegionRepairSearch. The v1 patch format and frozen
protocols remain available. This is an engineering implementation with external
semantic review, not an automatic proof verifier.

Use `generator_input(policy="region-topology-replacement-v2")` after the current
interface is reviewed. Submit the new schema in
`schemas/region_topology_replacement_v2.schema.json` through `prepare` and `decide`.

The editing rules are deliberately conservative:

- A topology edit replaces a contiguous declared region with a nonempty ordered
  list. Explicit consumer expansion or whole-proof selection chooses the region.
  Retained IDs preserve relative order. Other graph shapes are not yet supported.
- Insert at most three nodes per transaction. New IDs are
  `repair-r<NEXT_REVISION>-n<POSITIVE_INTEGER>`, never reused in the live session;
  their initial version is 1. Existing affected nodes increment their version.
- References in the submitted patch use exact current versions for retained
  nodes and version 1 for new nodes. Validate references and source order before
  mechanically rebasing them. Cycles, future premises and dangling references fail.
- Every deleted node needs its exact old reference, nonempty `replacement_ids`
  inside the new region and a reason. The separate deletion review must explain
  which needed obligations, definitions and witnesses transfer, and check every
  former consumer. An old erroneous assertion need not be reproved. The mapping
  is a review obligation, never proof that deletion is valid.
- A producer with an outside consumer cannot be deleted. Include that consumer
  in the region before explicitly reconnecting it. Outside dependency identities
  and mathematical text stay unchanged. No implicit semantic redirection exists.
- Order keys are mechanically spaced by 10; outside relative order is preserved.
  Accounting records insertions, deletions, substantive edits and mechanical
  order/version/reference changes. All affected evidence requires revalidation.

The candidate request contains before/after graphs, fixed context, reviewed
outputs, a freshly extracted boundary and per-deletion obligations. Removing the
old final node adds an explicit original-goal audit. Whole-proof rewriting also
keeps its goal check. Missing, rejected or undetermined checks block application.
The previous graph and deleted node bodies are archived in the application event.

All validation and review checks finish before the live graph changes. A failed
candidate preserves the proof and localization report; search attempts and feedback
stay charged. Success invalidates the report and returns `applied_requires_rescan`.
The existing whole-proof scan and final target-coverage review still decide
completion, including surviving independent branches. There is no concurrent
transaction or cross-process recovery guarantee.

Run the disclosed fixture replay:

```sh
python scripts/run_region_topology_demo.py --output outputs/region_topology_demo.json
python -m unittest discover -s tests -p test_region_topology.py
```

The replay inserts a node, deletes an erroneous predecessor, explicitly reconnects
an edited consumer, and checks the retained branch. Semantic judgments are fixtures.
It establishes neither independent mathematical correctness nor token savings.
Natural-language dependency omissions and variable scope remain external review
responsibilities. Automatic routing and real model evaluations remain disabled.
