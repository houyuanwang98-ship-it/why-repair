"""Closed output contracts and immutable identities for workflow v2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_MODEL = ("gpt-5.6-sol", "xhigh")
VALIDATION_MODEL = ("gpt-6-astra", "high")
METHODS = ("original", "direct_rewrite", "self_refine", "generator_critic", "best_of_n", "full_system")
PUBLIC_FIELDS = ("theorem", "assumptions", "domain", "proof_text", "explicit_subgoals")
TERMINALS = ("proof_ready", "counterexample_ready", "undetermined", "repair_not_found",
             "budget_exhausted", "input_invalid", "runtime_failed")


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        require(path.read_text(encoding="utf-8") == data, f"immutable evidence differs: {path}")
    else:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(data)


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def arr(item):
    return {"type": "array", "items": item}


def enum(*values):
    return {"type": "string", "enum": list(values)}


TEXT = {"type": "string", "minLength": 1, "pattern": "\\S"}
STRINGS = arr(TEXT)
REF = obj(node_id=TEXT, version={"type": "integer", "minimum": 1})
NODE = obj(node_id=TEXT, text=TEXT, claim=TEXT, depends_on=STRINGS,
           scope=STRINGS, goal_refs=STRINGS)
ISSUE = obj(node_id=TEXT, kind=enum("gap", "invalid", "undetermined"),
            quote=TEXT, reason=TEXT)
CHECK = enum("pass", "fail", "unknown")
PROBLEM = obj(theorem=TEXT, assumptions=STRINGS, domain=TEXT, proof_text=TEXT,
              explicit_subgoals=STRINGS)
COUNTER = obj(scope=enum("local", "theorem"), target=TEXT, witness=TEXT)
MAYBE_COUNTER = {"anyOf": [COUNTER, {"type": "null"}]}
SCHEMAS = {
    "problem": PROBLEM,
    "graph": obj(nodes=arr(NODE), ambiguities=STRINGS),
    "evaluate": obj(target=REF, status=enum("closed", "gap", "invalid", "undetermined"),
                    checked_obligation=TEXT, reason=TEXT, unresolved_conditions=STRINGS,
                    counterexample=MAYBE_COUNTER),
    "diagnose": obj(target=REF, confirmation=enum("confirmed", "false_positive", "uncertain"),
                    kind=enum("gap", "invalid", "undetermined"), failed_edge=TEXT,
                    quote=TEXT, reason=TEXT),
    "generate_patch": obj(base_state_digest=TEXT, certificate_id=TEXT, target=REF,
                          operation=enum("replace", "insert_before", "delete", "set_dependencies",
                                         "counterexample", "abstain"),
                          nodes=arr(NODE), target_dependencies_after=STRINGS,
                          counterexample=MAYBE_COUNTER, reason=TEXT),
    "review_patch": obj(patch_digest=TEXT, resolved=CHECK, problem_preserved=CHECK,
                        scope_valid=CHECK, dependencies_valid=CHECK,
                        introduced_errors=STRINGS, unresolved_conditions=STRINGS, reason=TEXT),
    "audit": obj(validity=CHECK, rigor=CHECK, problem_preserved=CHECK,
                 goal_coverage=CHECK, issues=arr(ISSUE), unresolved_conditions=STRINGS, reason=TEXT),
    "counterexample_review": obj(counterexample_digest=TEXT, scope=enum("local", "theorem"),
                                 assumptions=CHECK, domain=CHECK, target_refuted=CHECK,
                                 unresolved_conditions=STRINGS, reason=TEXT),
    "candidate": obj(kind=enum("proof", "counterexample", "abstention"), text=TEXT, reason=TEXT),
    "feedback": obj(issues=STRINGS, reason=TEXT),
    "select": obj(selected_id=TEXT, reason=TEXT),
    "judge_input": obj(sample_id=TEXT, theorem=TEXT, assumptions=STRINGS, domain=TEXT,
                       explicit_subgoals=STRINGS, candidate_text=TEXT),
    "judge": obj(sample_id=TEXT, input_digest=TEXT,
                 candidate_kind=enum("proof", "counterexample", "abstention", "malformed"),
                 validity=enum("valid", "invalid", "undetermined", "not_applicable"),
                 rigor=enum("pass", "fail", "unknown", "not_applicable"),
                 problem_preservation=enum("pass", "fail", "unknown", "not_applicable"),
                 goal_coverage=enum("pass", "fail", "unknown", "not_applicable"),
                 counterexample_validity=enum("valid", "invalid", "undetermined", "not_applicable"),
                 findings=arr(obj(quote=TEXT, reason=TEXT)), unresolved_obligations=STRINGS,
                 evidence_scope=enum("model_only"), reason=TEXT),
}


def validate(name, value):
    Draft202012Validator(SCHEMAS[name]).validate(value)
    return value


def public_problem(row):
    value = {key: row[key] for key in PUBLIC_FIELDS}
    validate("problem", value)
    return value


def problem_context(problem):
    return {key: problem[key] for key in PUBLIC_FIELDS if key != "proof_text"}


def judge_input(problem, candidate_text, sample_id):
    value = dict(sample_id=sample_id, **problem_context(problem), candidate_text=candidate_text)
    return validate("judge_input", value)


def validate_judgment(value, payload):
    validate("judge", value)
    require(value["sample_id"] == payload["sample_id"], "judge identity mismatch")
    require(value["input_digest"] == digest(payload), "judge input digest mismatch")
    require(all(f["quote"] in payload["candidate_text"] for f in value["findings"]),
            "judge finding does not quote the candidate")
    if value["candidate_kind"] != "proof":
        require(value["validity"] == "not_applicable", "non-proof validity must be not_applicable")
    else:
        require(value["validity"] != "not_applicable", "proof validity is required")
    require(value["candidate_kind"] == "counterexample" or
            value["counterexample_validity"] == "not_applicable", "counterexample score on non-counterexample")
    if strict_accept(value):
        require(not value["findings"], "strict acceptance contradicts material findings")
    return value


def strict_accept(j):
    return (j["candidate_kind"] == "proof" and j["validity"] == "valid"
            and all(j[k] == "pass" for k in ("rigor", "problem_preservation", "goal_coverage"))
            and not j["unresolved_obligations"])


def implementation_files():
    paths = sorted((ROOT / "harness/workflow_v2").glob("*.py"))
    paths += [ROOT / "harness/codex_cli.py", ROOT / "scripts/run_workflow_v2.py",
              ROOT / "scripts/schedule_workflow_v2.py",
              ROOT / "scripts/analyze_workflow_v2.py",
              ROOT / "docs/workflow_v2/protocol.json", ROOT / "data/theorem_bank/algebra_core.jsonl"]
    paths += sorted((ROOT / "schemas/workflow_v2").glob("*.json"))
    return paths


def implementation_digest():
    return digest({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in implementation_files()})


def snapshot_implementation(path):
    path = Path(path)
    if path.exists():
        with zipfile.ZipFile(path) as archive:
            require(digest({n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist()}) == implementation_digest(),
                    "implementation snapshot drift")
        return
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for file in implementation_files():
            archive.write(file, str(file.relative_to(ROOT)))
