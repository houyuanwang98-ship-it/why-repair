"""Portable command-line entrypoint."""

import argparse
import json
import os
from pathlib import Path


from .adjudication import (
    build_host_adjudication_template,
    make_openai_adjudicator,
    make_openai_calculation_adjudicator,
    make_openai_diagnosis_adjudicator,
    make_openai_graph_builder,
)
from .contracts import AMBIENT_BATCH_RESULT_ID, SESSION_SCHEMA_VERSION
from .graph import (
    build_graph_adjudication_entry,
    deterministic_linear_graph,
    validate_graph_builder_response,
)
from .io_session import (
    checker_source_digest,
    display_path,
    find_project_root,
    ingest_adjudication_file,
    load_node_cache,
    load_response_ledger,
    load_session_manifest,
    read_adjudication_file,
    read_jsonl,
    resolve_input_path,
    resolve_output_path,
    stable_digest,
    write_json,
    write_node_cache,
    write_response_ledger,
)
from .parsing import split_proof_into_nodes
from .pipeline import build_result
from .retrieval import ambient_facts_from_adjudication, build_ambient_adjudication_entry
from .subquestions import rules_from_accepted_subquestion, split_item_into_subquestions


__all__ = [
    "resolve_runtime_configuration",
    "main",
]


def resolve_runtime_configuration(args, parser, project_root):
    session_dir = (
        resolve_output_path(args.session_dir, project_root)
        if args.session_dir
        else None
    )
    manifest_path = session_dir / "session.json" if session_dir else None
    manifest = load_session_manifest(manifest_path) if manifest_path else None

    def choose_scalar(argument_value, key, default):
        if manifest is not None and key in manifest:
            stored = manifest[key]
            if argument_value is not None and argument_value != stored:
                parser.error(
                    f"--{key.replace('_', '-')} conflicts with the existing session"
                )
            return stored
        return argument_value if argument_value is not None else default

    def choose_path(argument_value, key, resolver, default_path=None):
        stored = manifest.get(key) if manifest is not None else None
        explicit = resolver(argument_value, project_root) if argument_value else None
        if stored is not None:
            stored_path = Path(stored)
            if explicit is not None and explicit.resolve() != stored_path.resolve():
                parser.error(
                    f"--{key.replace('_', '-')} conflicts with the existing session"
                )
            return stored_path
        if explicit is not None:
            return explicit
        return default_path

    input_path = choose_path(args.input, "input", resolve_input_path)
    theorem_bank_path = choose_path(
        args.theorem_bank, "theorem_bank", resolve_input_path
    )
    output_dir = choose_path(
        args.output_dir,
        "output_dir",
        resolve_output_path,
        session_dir / "results" if session_dir else None,
    )
    pending_path = choose_path(
        args.emit_adjudication_template,
        "pending_file",
        resolve_output_path,
        session_dir / "pending.json" if session_dir else None,
    )
    node_cache_path = choose_path(
        args.node_cache,
        "node_cache",
        resolve_output_path,
        session_dir / "node-cache.json" if session_dir else None,
    )
    if input_path is None:
        parser.error("--input is required when creating a new session")
    if theorem_bank_path is None:
        parser.error("--theorem-bank is required when creating a new session")
    if output_dir is None:
        parser.error("--output-dir is required without --session-dir")

    max_rules = choose_scalar(args.max_rules, "max_rules", 5)
    uncertain_policy = choose_scalar(
        args.uncertain_policy, "uncertain_policy", "undetermined"
    )
    workflow_mode = choose_scalar(args.workflow_mode, "workflow_mode", "grading")
    model = choose_scalar(
        args.model,
        "model",
        os.environ.get("OPENAI_MODEL", "gpt-5.5"),
    )
    model_max_output_tokens = choose_scalar(
        args.model_max_output_tokens, "model_max_output_tokens", 1200
    )
    raw_proof = choose_scalar(args.raw_proof, "raw_proof", None)

    response_ledger_path = session_dir / "responses.jsonl" if session_dir else None
    resolved = {
        "session_dir": session_dir,
        "manifest_path": manifest_path,
        "input_path": input_path,
        "theorem_bank_path": theorem_bank_path,
        "output_dir": output_dir,
        "pending_path": pending_path,
        "node_cache_path": node_cache_path,
        "response_ledger_path": response_ledger_path,
        "max_rules": max_rules,
        "uncertain_policy": uncertain_policy,
        "workflow_mode": workflow_mode,
        "model": model,
        "model_max_output_tokens": model_max_output_tokens,
        "raw_proof": raw_proof,
        "write_changed_only": args.write_changed_only or session_dir is not None,
    }
    if session_dir is not None:
        session_dir.mkdir(parents=True, exist_ok=True)
        new_manifest = {
            "schema_version": SESSION_SCHEMA_VERSION,
            "input": str(input_path.resolve()),
            "theorem_bank": str(theorem_bank_path.resolve()),
            "output_dir": str(output_dir.resolve()),
            "pending_file": str(pending_path.resolve()),
            "node_cache": str(node_cache_path.resolve()),
            "response_ledger": str(response_ledger_path.resolve()),
            "max_rules": max_rules,
            "uncertain_policy": uncertain_policy,
            "workflow_mode": workflow_mode,
            "model": model,
            "model_max_output_tokens": model_max_output_tokens,
            "raw_proof": raw_proof,
        }
        write_json(manifest_path, new_manifest, only_if_changed=True)
    return resolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--theorem-bank")
    parser.add_argument("--output-dir")
    parser.add_argument("--session-dir")
    parser.add_argument("--max-rules", type=int)
    parser.add_argument(
        "--workflow-mode",
        choices=["grading", "repair"],
        help=(
            "Select grading-only checking or post-check repair. Defaults to grading "
            "and is frozen in session.json."
        ),
    )
    parser.add_argument(
        "--uncertain-policy",
        choices=["model", "undetermined"],
        help="Optional provider adapter. Portable host-agent workflow uses undetermined.",
    )
    parser.add_argument("--model")
    parser.add_argument("--model-max-output-tokens", type=int)
    parser.add_argument(
        "--emit-adjudication-template",
        help="Write unresolved obligations for the active host agent to complete.",
    )
    parser.add_argument(
        "--adjudications",
        action="append",
        help="Read host-agent adjudication responses and merge validated results.",
    )
    parser.add_argument(
        "--node-cache",
        help=(
            "Persist validated node results and reuse nodes whose dependency-aware "
            "fingerprints are unchanged."
        ),
    )
    parser.add_argument(
        "--write-changed-only",
        action="store_true",
        help=(
            "Preserve existing result and pending files when their serialized "
            "content is unchanged."
        ),
    )
    parser.add_argument("--raw-proof", type=str, default=None,
                        help="Raw proof text to split into nodes before checking.")
    args = parser.parse_args()

    project_root = find_project_root()
    runtime = resolve_runtime_configuration(args, parser, project_root)
    input_path = runtime["input_path"]
    theorem_bank_path = runtime["theorem_bank_path"]
    output_dir = runtime["output_dir"]
    pending_path = runtime["pending_path"]
    node_cache_path = runtime["node_cache_path"]
    host_adjudications = {}
    session_ingested_responses = 0
    if runtime["session_dir"] is not None:
        ledger = load_response_ledger(runtime["response_ledger_path"])
        if pending_path is not None:
            session_ingested_responses += ingest_adjudication_file(
                pending_path, ledger
            )
        for adjudication_path in args.adjudications or []:
            session_ingested_responses += ingest_adjudication_file(
                resolve_input_path(adjudication_path, project_root), ledger
            )
        write_response_ledger(runtime["response_ledger_path"], ledger)
        host_adjudications = {
            key: entry["response"] for key, entry in ledger.items()
        }
    else:
        for adjudication_path in args.adjudications or []:
            host_adjudications.update(
                read_adjudication_file(
                    resolve_input_path(adjudication_path, project_root)
                )
            )

    items = read_jsonl(input_path)
    theorem_bank = read_jsonl(theorem_bank_path)
    ambient_items = [
        subitem
        for item in items
        for subitem in split_item_into_subquestions(item)
    ]
    ambient_response = host_adjudications.get(
        (AMBIENT_BATCH_RESULT_ID, 0, "ambient")
    )
    ambient_facts_by_result = ambient_facts_from_adjudication(
        ambient_response, ambient_items
    )
    base_theorem_bank_digest = stable_digest(theorem_bank)
    output_dir.mkdir(parents=True, exist_ok=True)
    node_cache = load_node_cache(node_cache_path) if node_cache_path else None
    cache_stats = {"hits": 0, "misses": 0, "disabled_results": 0}
    cache_context = {
        "checker_source_sha256": checker_source_digest(),
        "uncertain_policy": runtime["uncertain_policy"],
        "model": runtime["model"] if runtime["uncertain_policy"] == "model" else None,
        "model_max_output_tokens": (
            runtime["model_max_output_tokens"]
            if runtime["uncertain_policy"] == "model"
            else None
        ),
        "adjudicator_key": {
            "mode": runtime["uncertain_policy"],
            "model": (
                runtime["model"]
                if runtime["uncertain_policy"] == "model"
                else None
            ),
            "max_output_tokens": (
                runtime["model_max_output_tokens"]
                if runtime["uncertain_policy"] == "model"
                else None
            ),
        },
    }
    model_adjudicator = (
        make_openai_adjudicator(runtime["model"], runtime["model_max_output_tokens"])
        if runtime["uncertain_policy"] == "model"
        else None
    )
    calculation_adjudicator = (
        make_openai_calculation_adjudicator(
            runtime["model"], runtime["model_max_output_tokens"]
        )
        if runtime["uncertain_policy"] == "model"
        else None
    )
    diagnosis_adjudicator = (
        make_openai_diagnosis_adjudicator(
            runtime["model"], runtime["model_max_output_tokens"]
        )
        if runtime["uncertain_policy"] == "model"
        else None
    )
    graph_builder = (
        make_openai_graph_builder(runtime["model"], runtime["model_max_output_tokens"])
        if runtime["uncertain_policy"] == "model"
        else None
    )

    all_results = []
    outputs_written = 0
    outputs_unchanged = 0
    for item in items:
        subitems = split_item_into_subquestions(item)
        working_bank = list(theorem_bank)
        prior_rule_ids = []
        for subitem in subitems:
            subitem["prior_subquestion_rule_ids"] = list(prior_rule_ids)
            result_cache_context = dict(cache_context)
            result_cache_context["theorem_bank_sha256"] = (
                stable_digest(working_bank)
                if prior_rule_ids
                else base_theorem_bank_digest
            )
            result = build_result(
                subitem,
                working_bank,
                runtime["max_rules"],
                raw_proof=runtime["raw_proof"] if len(subitems) == 1 else None,
                model_adjudicator=model_adjudicator,
                calculation_adjudicator=calculation_adjudicator,
                diagnosis_adjudicator=diagnosis_adjudicator,
                host_adjudications=host_adjudications,
                graph_builder=graph_builder,
                extra_ambient_facts=(
                    ambient_facts_by_result.get(str(subitem.get("id", "")), [])
                    if ambient_facts_by_result is not None
                    else []
                ),
                node_cache=node_cache,
                cache_context=result_cache_context,
                cache_stats=cache_stats,
            )
            all_results.append(result)
            out_path = output_dir / f"{result['id']}.json"
            if write_json(
                out_path,
                result,
                only_if_changed=runtime["write_changed_only"],
            ):
                outputs_written += 1
            else:
                outputs_unchanged += 1
            print(json.dumps({
                "id": result["id"],
                "parent_id": result["parent_id"],
                "subquestion_label": result["subquestion_label"],
                "validity_status": result["validity_status"],
                "first_gap_step": result["first_gap_step"],
                "first_invalid_step": result["first_invalid_step"],
                "first_undetermined_step": result["first_undetermined_step"],
                "output": display_path(out_path, project_root),
            }, ensure_ascii=False))
            if len(subitems) > 1:
                derived_rules = rules_from_accepted_subquestion(result)
                working_bank.extend(derived_rules)
                prior_rule_ids.extend(rule["id"] for rule in derived_rules)

    pending_count = None
    if pending_path is not None:
        template_path = pending_path
        initial_entries = []
        if ambient_items and ambient_facts_by_result is None:
            initial_entries.append(build_ambient_adjudication_entry(ambient_items))
        graph_entries = []
        for item in items:
            subitems = split_item_into_subquestions(item)
            for subitem in subitems:
                proof_steps = (
                    split_proof_into_nodes(runtime["raw_proof"])
                    if runtime["raw_proof"] and len(subitems) == 1
                    else subitem.get("flawed_proof_steps", [])
                )
                graph_response = host_adjudications.get(
                    (str(subitem.get("id", "")), 0, "graph")
                )
                if (
                    validate_graph_builder_response(graph_response, proof_steps) is None
                    and deterministic_linear_graph(proof_steps) is None
                ):
                    graph_entries.append(build_graph_adjudication_entry(subitem, proof_steps))
        initial_entries.extend(graph_entries)
        template = (
            {
                "workflow_mode": runtime["workflow_mode"],
                "rule_dictionary": {},
                "instructions": (
                    "The active host agent completes the submission-level ambient "
                    "fact review and each required dependency graph in this same "
                    "frontier, then reruns the checker with --adjudications. Ambient "
                    "reasoning is limited to direct theorem conditions and standard "
                    "notation with quoted source evidence."
                ),
                "adjudications": initial_entries,
            }
            if initial_entries
            else build_host_adjudication_template(
                all_results, workflow_mode=runtime["workflow_mode"]
            )
        )
        write_json(
            template_path,
            template,
            only_if_changed=runtime["write_changed_only"],
        )
        pending_count = len(template["adjudications"])
        print(json.dumps({
            "adjudication_template": display_path(template_path, project_root),
            "pending_count": pending_count,
            "workflow_mode": runtime["workflow_mode"],
        }, ensure_ascii=False))

    if node_cache_path is not None:
        active_result_ids = {str(result["id"]) for result in all_results}
        node_cache["results"] = {
            result_id: cached_result
            for result_id, cached_result in node_cache.get("results", {}).items()
            if result_id in active_result_ids
        }
        write_node_cache(node_cache_path, node_cache)
        print(json.dumps({
            "type": "node_cache_summary",
            "node_cache": display_path(node_cache_path, project_root),
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "disabled_results": cache_stats["disabled_results"],
            "outputs_written": outputs_written,
            "outputs_unchanged": outputs_unchanged,
        }, ensure_ascii=False))

    if runtime["session_dir"] is not None:
        print(json.dumps({
            "type": "session_summary",
            "session_dir": display_path(runtime["session_dir"], project_root),
            "responses_loaded": len(host_adjudications),
            "responses_ingested": session_ingested_responses,
            "pending_count": pending_count,
            "workflow_mode": runtime["workflow_mode"],
        }, ensure_ascii=False))
