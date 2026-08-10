"""JSON I/O, cache, response-ledger, session, and path helpers."""

import hashlib
import json
import os
from pathlib import Path


from .contracts import (
    NODE_ADJUDICATION_KINDS,
    NODE_CACHE_SCHEMA_VERSION,
    PRIMARY_DIAGNOSIS_BUNDLE_KINDS,
    SESSION_SCHEMA_VERSION,
)


__all__ = [
    "read_jsonl",
    "serialized_json",
    "canonical_json",
    "stable_digest",
    "checker_source_files",
    "checker_source_digest",
    "write_json",
    "empty_node_cache",
    "load_node_cache",
    "write_node_cache",
    "proof_cache_context",
    "node_host_responses",
    "node_cache_fingerprint",
    "adjudication_key",
    "expanded_adjudication_entries",
    "read_adjudication_entries",
    "adjudication_lookup",
    "read_adjudication_file",
    "load_response_ledger",
    "ingest_adjudication_file",
    "write_response_ledger",
    "load_session_manifest",
    "valid_structured_response",
    "host_adjudication",
    "find_project_root",
    "resolve_input_path",
    "resolve_output_path",
    "display_path",
]


def read_jsonl(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def serialized_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def canonical_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def stable_digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def checker_source_files():
    package_dir = Path(__file__).resolve().parent
    entrypoint = package_dir.parent / "check_obligations.py"
    return [entrypoint, *sorted(package_dir.glob("*.py"))]


def checker_source_digest():
    scripts_dir = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in checker_source_files():
        relative_path = path.relative_to(scripts_dir).as_posix()
        digest.update(relative_path.encode("ascii"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def write_json(path, value, only_if_changed=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = serialized_json(value)
    if only_if_changed and path.is_file():
        try:
            if path.read_text(encoding="utf-8") == rendered:
                return False
        except OSError:
            pass
    path.write_text(rendered, encoding="utf-8")
    return True


def empty_node_cache():
    return {
        "schema_version": NODE_CACHE_SCHEMA_VERSION,
        "results": {},
    }


def load_node_cache(path):
    if path is None or not path.is_file():
        return empty_node_cache()
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_node_cache()
    if (
        not isinstance(cache, dict)
        or cache.get("schema_version") != NODE_CACHE_SCHEMA_VERSION
        or not isinstance(cache.get("results"), dict)
    ):
        return empty_node_cache()
    return cache


def write_node_cache(path, cache):
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = serialized_json(cache)
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == rendered:
                return False
        except OSError:
            pass
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary_path.write_text(rendered, encoding="utf-8")
    os.replace(temporary_path, path)
    return True


def proof_cache_context(item):
    excluded = {
        "explicit_subquestions",
        "flawed_proof_steps",
        "gold_error_type",
        "gold_first_gap_step",
        "gold_first_invalid_step",
        "gold_minimal_repair",
        "gold_validity_status",
        "problem_text",
        "proof_text",
    }
    return {key: value for key, value in item.items() if key not in excluded}


def node_host_responses(host_adjudications, result_id, node_id):
    if not host_adjudications:
        return {}
    return {
        kind: host_adjudications.get((str(result_id), int(node_id), kind))
        for kind in NODE_ADJUDICATION_KINDS
        if (str(result_id), int(node_id), kind) in host_adjudications
    }


def node_cache_fingerprint(
    *,
    cache_context,
    item,
    node_id,
    is_final_node,
    claim,
    node_type,
    dependency_source,
    dependency_entry,
    predecessor_nodes,
    accepted_claims,
    calculation_context,
    calculation_source_expression,
    local_context,
    ambient_facts,
    host_adjudications,
):
    return stable_digest({
        "cache_context": cache_context,
        "proof_context": proof_cache_context(item),
        "node_id": node_id,
        "is_final_node": is_final_node,
        "claim": claim,
        "node_type": node_type,
        "dependency_source": dependency_source,
        "dependency_entry": dependency_entry,
        "predecessor_digests": [stable_digest(node) for node in predecessor_nodes],
        "accepted_claims": accepted_claims,
        "calculation_context": calculation_context,
        "calculation_source_expression": calculation_source_expression,
        "local_context": local_context,
        "ambient_facts": ambient_facts,
        "host_responses": node_host_responses(
            host_adjudications, item.get("id", ""), node_id
        ),
    })


def adjudication_key(entry):
    return (
        str(entry.get("result_id", "")),
        int(entry.get("node_id", 0)),
        entry.get("kind"),
    )


def expanded_adjudication_entries(entry):
    kind = entry.get("kind")
    response = entry.get("response")
    if kind not in PRIMARY_DIAGNOSIS_BUNDLE_KINDS:
        return [entry]
    if not isinstance(response, dict):
        return []
    primary_kind = PRIMARY_DIAGNOSIS_BUNDLE_KINDS[kind]
    expanded = []
    primary_response = response.get("primary_response")
    diagnosis_response = response.get("diagnosis_response")
    if primary_response is not None:
        expanded.append({
            "result_id": entry.get("result_id", ""),
            "node_id": entry.get("node_id", 0),
            "kind": primary_kind,
            "response": primary_response,
        })
    if diagnosis_response is not None:
        expanded.append({
            "result_id": entry.get("result_id", ""),
            "node_id": entry.get("node_id", 0),
            "kind": "diagnosis",
            "response": diagnosis_response,
        })
    return expanded


def read_adjudication_entries(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for entry in data.get("adjudications", []):
        entries.extend(expanded_adjudication_entries(entry))
    return entries


def adjudication_lookup(entries):
    lookup = {}
    for entry in entries:
        lookup[adjudication_key(entry)] = entry.get("response")
    return lookup


def read_adjudication_file(path):
    return adjudication_lookup(read_adjudication_entries(path))


def load_response_ledger(path):
    entries = {}
    if not path.is_file():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            key = adjudication_key(entry)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if key[2] in NODE_ADJUDICATION_KINDS and entry.get("response") is not None:
            entries[key] = entry
    return entries


def ingest_adjudication_file(path, ledger):
    changed = 0
    if not path.is_file():
        return changed
    for entry in read_adjudication_entries(path):
        if entry.get("response") is None:
            continue
        key = adjudication_key(entry)
        if key[2] not in NODE_ADJUDICATION_KINDS:
            continue
        normalized = {
            "result_id": key[0],
            "node_id": key[1],
            "kind": key[2],
            "response": entry.get("response"),
        }
        if ledger.get(key) != normalized:
            ledger[key] = normalized
            changed += 1
    return changed


def write_response_ledger(path, ledger):
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = [ledger[key] for key in sorted(ledger)]
    rendered = "".join(
        json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
        for entry in ordered
    )
    if path.is_file() and path.read_text(encoding="utf-8") == rendered:
        return False
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary_path.write_text(rendered, encoding="utf-8")
    os.replace(temporary_path, path)
    return True


def load_session_manifest(path):
    if not path.is_file():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != SESSION_SCHEMA_VERSION
    ):
        return None
    return manifest


def valid_structured_response(response, schema):
    return isinstance(response, dict) and all(
        field in response for field in schema.get("required", [])
    )


def host_adjudication(host_adjudications, result_id, node_id, kind, schema):
    if not host_adjudications:
        return None
    response = host_adjudications.get((str(result_id), int(node_id), kind))
    return response if valid_structured_response(response, schema) else None


def find_project_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    return Path.cwd()


def resolve_input_path(raw_path, project_root):
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate
    return project_root / path


def resolve_output_path(raw_path, project_root):
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return project_root / path


def display_path(path, project_root):
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)
