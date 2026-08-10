# Usage guide

This guide covers installation, command-line workflows, resumable adjudication sessions, evaluation, and input data.

## Setup

The default portable checker and host-agent workflow use only the Python
standard library, so they require no package installation or API key.

Install the optional repository dependency when running
`scripts/run_baseline.py` or the checker's standalone
`--uncertain-policy model` adapter:

```bash
pip install -r requirements.txt
```

Those optional OpenAI-backed workflows also require an API key:

```bash
export OPENAI_API_KEY="your_api_key"
```

## Run a baseline

Run the agentic baseline on the sample data:

```bash
python scripts/run_baseline.py \
  --method agentic \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/algebra_core.jsonl \
  --output-dir outputs/agentic
```

## Run the obligation-checking skill prototype

The portable Agent Skill is stored inside this repository. It follows the
`SKILL.md` layout used by Codex, Claude Code, Gemini CLI, and other compatible
agents:

```text
skills/math-proof-repair-agent
```

Install it for one supported client or every distinct user-level profile:

```bash
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target codex --scope user
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target all --scope user
```

Available targets are `codex`, `claude`, `gemini`, `opencode`, `openclaw`, and
`agents`. Use
`--scope workspace` for project-local discovery or `--dest-root` for a client
with a custom skill directory. Platform and discovery details are documented in
`skills/math-proof-repair-agent/references/compatibility.md`.

Run the deterministic prototype:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --output-dir outputs/obligation_checker
```

The default workflow is host-agent adjudication. Add
`--emit-adjudication-template pending.json`; the first round asks the active
Codex, Claude, Gemini, OpenCode, or OpenClaw agent to build each proof's
complete dependency DAG under the skill standards. Rerun with
`--adjudications pending.json`; later rounds emit the dependency frontier of
unresolved node obligations. Independent frontier nodes are batched, and proof
or calculation review is bundled with its conditional diagnosis.
This requires no
provider SDK or additional API key. `--uncertain-policy model` remains an
explicit optional OpenAI adapter for standalone automation.

For repeated resume rounds, keep one output directory and enable incremental
node reuse:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --output-dir outputs/obligation_checker_session \
  --emit-adjudication-template outputs/obligation_checker_session/pending.json \
  --node-cache outputs/obligation_checker_session/node-cache.json \
  --write-changed-only \
  --adjudications round-1-responses.json
```

The cache is optional and does not change result semantics. Any changed
fingerprint component causes a normal recomputation, and changed predecessor
results invalidate affected descendants. The CLI emits a `node_cache_summary`
line with hit, miss, written, and unchanged-output counts.

The shorter session workflow enables the cache and unchanged-output behavior
automatically:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl \
  --session-dir outputs/algebra_pilot_session

# Fill outputs/algebra_pilot_session/pending.json, then resume:
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --session-dir outputs/algebra_pilot_session
```

Each resume imports completed responses from `pending.json` into
`responses.jsonl` before computing the next frontier. Explicit legacy
`--adjudications` files can also be imported into a session at any time.

The portable path uses only the Python standard library. Relative input paths
are resolved from the current directory first and then from the project root.
Relative output paths are written under the project root.

To use the merged cross-domain theorem bank:

```bash
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/all_clean_seed_rules.jsonl \
  --output-dir outputs/all_bank_smoke_test
```

The prototype is meant to be a runnable scaffold for the later trainable agent.
The later trainable modules should optimize:

```text
proof segmentation
dependency extraction
obligation generation
rule retrieval
node status classification
minimal repair generation
```

Run all three baselines:

```bash
python scripts/run_baseline.py --method direct --input data/samples/algebra_pilot_3.jsonl --theorem-bank data/theorem_bank/algebra_core.jsonl --output-dir outputs/direct
python scripts/run_baseline.py --method stepwise --input data/samples/algebra_pilot_3.jsonl --theorem-bank data/theorem_bank/algebra_core.jsonl --output-dir outputs/stepwise
python scripts/run_baseline.py --method agentic --input data/samples/algebra_pilot_3.jsonl --theorem-bank data/theorem_bank/algebra_core.jsonl --output-dir outputs/agentic
```

## Evaluate

This script checks fields that can be scored automatically:

```bash
python scripts/evaluate_basic.py \
  --gold data/samples/algebra_pilot_3.jsonl \
  --pred-dir outputs/agentic
```

Repair correctness and repair minimality still need human review in the first
prototype.

## Data format

Each JSONL row is one flawed proof instance. Required fields:

```json
{
  "id": "alg_001",
  "domain": "algebra",
  "topic": "group_theory",
  "theorem": "...",
  "assumptions": ["..."],
  "flawed_proof_steps": ["..."],
  "gold_first_invalid_step": 2,
  "gold_error_type": "missing_assumption",
  "gold_diagnosis": "...",
  "gold_minimal_repair": "..."
}
```

Step indices are 1-based.
