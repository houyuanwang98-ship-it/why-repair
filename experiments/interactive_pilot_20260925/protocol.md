# Built-in model pilot v1 (frozen before model responses)

Exploratory engineering pilot, not a blinded benchmark or a human-adjudicated study.
User authorized GPT-5.6 subagents and GitHub publication. Requested model for all
semantic workers: `gpt-5.6-sol`, reasoning effort `high`, fresh context per role.
The coordinating assistant has seen historical Gold; semantic workers must not.
Requested model is transport configuration, not an independently attested snapshot.

Cases: all three public examples in `data/samples/algebra_pilot_3.jsonl`, in file
order, without Gold fields. No result-based selection. Original text unchanged.
Graphs conservatively list all previous nodes as dependencies. These annotations
are controller-authored, not independently verified minimal dependency graphs.
Ring conventions: associative rings, not assumed commutative; ideal means two-sided.

Rubric: ordinary textbook mathematics, explicit false reasons are errors; standard
short implicit inferences may be accepted when the reviewer supplies a noncircular
bridge from admissible premises. Missing essential arguments require repair.
Do not force agreement with historical Gold, especially implicit rank-nullity.

Workflow: existing IterativeRepairSession + RepairSearch, body replacement only,
fixed single-node initial error region, up to three applied repairs per case,
at most eight candidate attempts and 40 feedback events; at most 80 local reviews.
No automatic route selection, expansion, deletion, counterexample injection or
whole-proof baseline in this first transport pilot. Unsuccessful or malformed
responses are retained, never replaced by coordinator-authored mathematical verdicts.
Stop a case on a rejected candidate, unresolved review or exhausted bound.

Roles: generator sees current generation/contract proposal packets; online reviewer
sees exact current review packets; final reviewer gets only original theorem,
assumptions and final submitted proof, with no online verdict or Gold. Roles have
separate conversational contexts but use the same model family: this does NOT
establish statistically independent errors or constitute human review. Workers are
instructed not to inspect other files; shared filesystem is not access isolation.

Preserve actual request and response JSON, agent identities, controller terminal
states, failure reasons, original and final text. Replay restores deterministic
controller state; it is not a new semantic model call. Costs/tokens unavailable
from subagent transport remain null. Callback replay latency is not model latency.
Do not infer cost savings from word counts or subscription percentages.

Report all three assigned cases, repairs applied, completion gate status, final
model verdict and disagreements. No repair-accuracy, false-success-rate or superiority
claim without independent reference adjudication. Save and publish intermediate
progress before exhausting subscription usage. No reset credits automatically used.
