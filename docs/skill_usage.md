# Math Proof Repair Agent Usage

This document explains how to use the portable Agent Skill and its checker on
Codex, Claude Code, Gemini CLI, and clients with custom skill directories.

## Install the Skill

Install into one user-level client profile:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target codex --scope user
```

Supported targets are `codex`, `claude`, `gemini`, `opencode`, `openclaw`, and
`agents`. Install every distinct user-level target with:

```text
python scripts/install_local_skill.py install --skill-dir skills/math-proof-repair-agent --target all --scope user
```

Use `--scope workspace --workspace-root <project-directory>` for project-local
installation, or `--dest-root <directory>` for another coding CLI. See
`skills/math-proof-repair-agent/references/compatibility.md` for discovery
paths and platform notes.

## What the Skill Does

The skill checks natural-language algebra proofs by building a structured
obligation trace:

```text
proof steps
  -> proof graph nodes
  -> local obligations
  -> theorem-bank retrieval
  -> node status labels
  -> first gap or first invalid step
  -> minimal repair suggestion
```

It does not fully formalize proofs in Lean. The current checker is a runnable
scaffold for testing the data structure and workflow.

## Input Format

Use one JSONL row per proof:

```json
{
  "id": "example_001",
  "domain": "algebra",
  "topic": "fields",
  "theorem": "If a is nonzero and a*x = a*y, then x = y.",
  "assumptions": [
    "R is a field",
    "a, x, and y are elements of R",
    "a is nonzero",
    "a*x = a*y"
  ],
  "flawed_proof_steps": [
    "Since a is nonzero, a has a multiplicative inverse a^{-1}.",
    "Multiplying both sides by a^{-1}, we get a^{-1}*(a*x) = a^{-1}*(a*y).",
    "Therefore x = y."
  ]
}
```

## Run from the Repository Copy

From the project root:

```text
python skills/math-proof-repair-agent/scripts/check_obligations.py --input data/samples/algebra_pilot_3.jsonl --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl --output-dir outputs/obligation_checker
```

## Run from the Installed Skill

From the project root:

```text
python <client-skill-root>/math-proof-repair-agent/scripts/check_obligations.py --input data/samples/algebra_pilot_3.jsonl --theorem-bank data/theorem_bank/artin_clean_seed_rules.jsonl --output-dir outputs/installed_skill
```

The portable path uses only the Python standard library. Emit an adjudication
template, let the active host agent fill it, and resume with `--adjudications`.
No provider SDK or additional API key is required. The optional
`--uncertain-policy model` adapter is for standalone automation only.

## Run with the Merged Cross-Domain Bank

Use the merged theorem bank when the input may involve multiple domains:

```text
python skills/math-proof-repair-agent/scripts/check_obligations.py \
  --input data/samples/algebra_pilot_3.jsonl \
  --theorem-bank data/theorem_bank/all_clean_seed_rules.jsonl \
  --output-dir outputs/all_bank_smoke_test
```

The merged bank contains the existing Artin algebra rules plus imported clean
seed rules from analysis, linear algebra, abstract algebra, set theory,
probability, topology, complex analysis, and manifolds.

## Available Theorem Banks

```text
data/theorem_bank/artin_clean_seed_rules.jsonl
data/theorem_bank/abbott_understanding_analysis_clean_seed_rules.jsonl
data/theorem_bank/axler_ladr_clean_seed_rules.jsonl
data/theorem_bank/dummit_foote_abstract_algebra_clean_seed_rules.jsonl
data/theorem_bank/enderton_elements_of_set_theory_clean_seed_rules.jsonl
data/theorem_bank/enderton_logic_clean_seed_rules.jsonl
data/theorem_bank/geometry_euclid_and_beyond_clean_seed_rules.jsonl
data/theorem_bank/grinstead_probability_clean_seed_rules.jsonl
data/theorem_bank/ireland_rosen_number_theory_clean_seed_rules.jsonl
data/theorem_bank/munkres_topology_clean_seed_rules.jsonl
data/theorem_bank/stein_and_shakarchi_complex_analysis_clean_seed_rules.jsonl
data/theorem_bank/tu_an_introduction_to_manifolds_clean_seed_rules.jsonl
data/theorem_bank/west_introduction_to_graph_theory_clean.jsonl
data/theorem_bank/all_clean_seed_rules.jsonl
```

The merged bank also includes the imported full-audit and supplemental JSONL
files. Run `python scripts/update_theorem_bank.py` to synchronize it from the
neighboring `Theorem_grabbing` workspace.

## Output Format

The checker writes one JSON file per proof into the output directory.

Each result follows:

```text
schemas/algebra_obligation_result.schema.json
```

Important top-level fields:

```text
validity_status
first_gap_step
first_invalid_step
summary_diagnosis
summary_repair
proof_graph
```

Important node fields:

```text
node_id
claim
depends_on
local_context
obligation
retrieved_rules
status
gap_type
error_type
diagnosis
repair_action
minimal_repair
```

## Node Status Labels

The fixed node status labels are:

```text
closed
valid_with_gap
missing_bridge_lemma
missing_assumption
theorem_misuse
algebraic_invalidity
false_theorem
downstream_invalid
```

## Expected Current Behavior

On the three algebra pilot examples:

```text
alg_001: valid_with_gap, first_gap_step=2, first_invalid_step=null
alg_002: invalid, first_gap_step=null, first_invalid_step=3
alg_003: valid_with_gap, first_gap_step=4, first_invalid_step=null
```

## Restore the Installation

The installation was made with a restore manifest. To restore the machine to
the state before this skill was installed, run:

```text
python scripts/install_local_skill.py restore --manifest <manifest-path>
```

Every installation prints its own manifest path. Restore one manifest per
target that should be rolled back.
