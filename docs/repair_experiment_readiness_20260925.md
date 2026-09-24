# Repair experiment preparation — not authorized to run

Status: proposed evaluation design only. No model experiment, independent semantic
review, new Gold annotation or human signature was produced in this continuation.
Frozen benchmark files, historical results and paper claims were not changed.

The engineering continuation now supports explicit local, expanded and whole-proof
regions, bounded topology changes, shared budgets and callback cost accounting.
These mechanisms do not establish better accuracy, lower token cost or superiority
over rewriting. The illustrative x=0 case still needs independent semantic review
before it is presented as an expert-validated example.

Before a real evaluation, an external reviewer must settle the following items:

| Decision | Required evidence | Current state |
|---|---|---|
| Cases and Gold | Exact case IDs, source/license, untouched original proof, accepted theorem/domain, versioned dependency and scope annotations | Not selected for this new method |
| Independent correctness review | Reviewer provenance, complete original-goal rubric, disagreements and adjudication; final judge independent of online repair decisions | Not supplied; role IDs alone prove no independence |
| Deletion obligations | Review a concrete packet with original/deleted nodes, replacement routes, all former consumers, definitions and witnesses | Fixture packets available; semantic approval pending |
| Routing | Predeclare explicit route schedules or separately approve an automatic policy, with parameters and stopping conditions | Explicit routes only |
| Fair budgets | Same candidate/call/token/fee caps and treatment of failures across arms; unavailable metering never counted as zero | Shared engineering limits available; real caps and providers unset |
| Run authorization | User explicitly lifts the no-real-model-evaluation constraint for an exact dataset and provider configuration | Not authorized |

Proposed comparisons, all under the same original-problem and final-review rules:

| Arm | Controlled change | Implementation/readiness |
|---|---|---|
| Upstream-only | Remove downstream interface guidance | Needs a separate benchmark adapter; not permission to bypass final review |
| No counterexample memory | Disable cross-candidate exact feedback reuse | Needs an explicitly versioned ablation configuration |
| Fixed region | Permit only the initial region | Explicit local mode exists; schedule must be frozen |
| Full mechanism | Reviewed boundaries, memory, expansion and topology | Engineering entrypoint exists; routing schedule and reviewers pending |
| Free local modification | Predefined local editing allowance without contract-guided search | Needs adapter and matching locality/cost measurement |
| Whole-proof rewrite | Start with the whole proof as the edit region | Bounded topology rewrite exists; distinguish its three-new-node limit from unrestricted rewriting |

Report every assigned case, including timeout, budget exhaustion, malformed output,
review disagreement and undetermined outcomes. Primary outcomes should separately
include independently reviewed repair success, false completion and coverage.
Also report new errors, downstream incompatibility, preserved arguments, substantive
edits, mechanical changes, revalidated nodes, expansions/rewrites, all callback
attempts, tokens, currencies/fees and latency with metering coverage. Do not turn
undetermined into correct or drop it from a success denominator without disclosure.

Use fresh output directories and a versioned manifest binding code commit, cases,
Gold digests, prompts, models, inference settings, routing schedule and budgets.
Predeclare blind judging and adjudication before inspecting new outcomes. Historical
50-case auditor accuracy is a different metric, not this method's repair success.
No historical benchmark approval should be repurposed as approval of this design.

Engineering packets can be reproduced without a provider:

```sh
python scripts/run_region_topology_demo.py --output outputs/region_topology_fixture.json
python scripts/run_repair_search_demo.py --output outputs/unified_search_fixture.json
```

Both packets explicitly label semantic judgments as fixtures. They are concrete
materials for external review, not completed human reviews or experiment results.
