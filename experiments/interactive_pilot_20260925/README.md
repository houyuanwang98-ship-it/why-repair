# Live built-in GPT-5.6 pilot: checkpoint, not completed repair evaluation

The three assigned examples have real, newly authored model-subagent responses.
These are not historical predictions projected onto new method arms and not fixture
acceptances. The Python controller only replays those externally authored responses.

Initial localization outcomes:

- `alg_001`: all original steps and the controller's final target check accepted;
  no patch applied. Implicit rank-nullity was accepted under the frozen textbook
  rubric. This differs from historical Gold's omission-based gap label and is not
  automatically a localization error or a validated Gold correction.
- `alg_002`: node 3 invalid: being a subgroup alone does not establish coset
  multiplication's representative independence. Generator proposed the boundary
  obligation; online contract review is the next stage.
- `alg_003`: node 4 has a gap: two-sided absorption has not been established.
  Generator submitted the required empty interface list for this terminal region;
  absence of downstream consumers does not waive proving the original theorem.

See `summary.json` and each run's `pending.json`/`terminal.json` for newer state.
No successful repair, cost saving, or general accuracy result is claimed at this
checkpoint. A separate proof-only final review packet has been issued for alg_001;
its response, when present, remains a model judgment, not human adjudication.

The five-hour usage window reached 93% used during this run, so progress was pushed
before exhausting the quota. The final-review worker then hit the usage limit;
the user subsequently reported resetting their quota and explicitly requested
continuation. The controller did not redeem a credit. Budget percentages cannot
be converted into per-case token usage. No further cases should be added until the
two unfinished repair paths are completed or recorded as terminal failures.

## Resume exactly, without regenerating prior judgments

For each unfinished case run:

```powershell
python -X utf8 scripts/run_interactive_repair_pilot.py experiments/interactive_pilot_20260925/cases/alg_002.json experiments/interactive_pilot_20260925/runs/alg_002
```

Exit 3 means a new external response is needed. Send only that pending packet to
the corresponding generator or online reviewer. Save its raw response to the
specified response_filename, without overwriting prior responses, then replay.
Use the same command for alg_003. Do not supply coordinator-made acceptances.
Stop on terminal rejection as declared in protocol; changes to protocol require a
separate run rather than discarding an inconvenient outcome.

After a terminal state, export proof-only final-review packets with
`scripts/build_pilot_final_review.py`, get fresh-context model review, and regenerate
`summary.json` using `scripts/summarize_interactive_pilot.py`.

Validation during this continuation: full suite 598 passed before the four reporting
tests were added; afterward all nine transport/reporting tests passed. The prior
installer timestamp-collision error did not recur, but was not fixed.
