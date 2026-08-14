"""Audit the frozen M2 pilot against the project M2 acceptance gates.

The normal mode writes/prints an evidence report.  ``--strict`` returns a
non-zero status whenever a publication-grade gate is not backed by evidence;
it deliberately does not turn historical claims into evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
M2 = ROOT / "data" / "benchmarks" / "m2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def normalized(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"\b(?:[a-z]|[m-z]\d*)\b", "<var>", text)
    text = re.sub(r"\d+", "<num>", text)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text)


def graph_is_valid(gold_row: dict) -> bool:
    source_nodes = [step["node_id"] for step in gold_row["proof_steps"]]
    nodes = gold_row.get("gold_nodes", [])
    node_ids = [node["node_id"] for node in nodes]
    if (
        not nodes
        and gold_row["gold_counterexample_status"] == "valid"
        and gold_row["gold_counterexample"]["scope"] == "original_theorem"
    ):
        # The frozen annotation policy terminates before process-node review
        # when a verified global theorem counterexample already settles the task.
        return True
    if node_ids != source_nodes or len(node_ids) != len(set(node_ids)):
        return False
    positions = {node_id: index for index, node_id in enumerate(node_ids)}
    return all(
        len(node.get("depends_on", [])) == len(set(node.get("depends_on", [])))
        and all(parent in positions and positions[parent] < positions[node["node_id"]] for parent in node.get("depends_on", []))
        for node in nodes
    )


def audit() -> dict:
    source_path = M2 / "source" / "pilot_50.jsonl"
    a_path = M2 / "annotations" / "person_a.jsonl"
    b_path = M2 / "annotations" / "person_b.jsonl"
    disagreements_path = M2 / "adjudication" / "disagreements.jsonl"
    agreement_path = M2 / "reports" / "agreement.json"
    decisions_path = M2 / "adjudication" / "decisions.jsonl"
    gold_path = M2 / "gold" / "algebra_pilot_v1.jsonl"
    gold_manifest_path = M2 / "gold" / "algebra_pilot_v1.manifest.json"
    registry_path = M2 / "audit" / "sample_registry_v1.json"

    source = load_jsonl(source_path)
    annotations_a = load_jsonl(a_path)
    annotations_b = load_jsonl(b_path)
    disagreements = load_jsonl(disagreements_path)
    decisions = load_jsonl(decisions_path)
    gold = load_jsonl(gold_path)
    manifest = load_json(gold_manifest_path)
    registry = load_json(registry_path)
    root_manifest = load_json(M2 / "manifest.json")
    ids = [row["proof_id"] for row in source]
    id_set = set(ids)

    exact = defaultdict(list)
    templated = defaultdict(list)
    for row in source:
        exact[row["theorem"].strip()].append(row["proof_id"])
        templated[normalized(row["theorem"])].append(row["proof_id"])
    exact_groups = sorted((v for v in exact.values() if len(v) > 1), key=lambda x: x[0])
    template_groups = sorted((v for v in templated.values() if len(v) > 1), key=lambda x: x[0])

    registered = {sample for group in registry["theorem_families"] for sample in group["sample_ids"]}
    explicit_family_sets = [set(group["sample_ids"]) for group in registry["theorem_families"]]
    duplicate_groups_covered = all(any(set(group) <= family for family in explicit_family_sets) for group in exact_groups)

    corpus_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for folder in (ROOT / "prompts", ROOT / "data" / "theorem_bank") if folder.exists() for path in folder.rglob("*") if path.is_file())
    leaked_ids = [row["proof_id"] for row in source if row["theorem"] in corpus_text]
    replacement_char_files = []
    for path in M2.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl", ".md"} and "\ufffd" in path.read_text(encoding="utf-8", errors="replace"):
            replacement_char_files.append(path.relative_to(ROOT).as_posix())

    m3_gold_path = ROOT / "data" / "benchmarks" / "m3" / "gold" / "evaluator_pilot_v1.jsonl"
    m3_gold = load_jsonl(m3_gold_path)
    m3_graphs_valid = (
        {row["proof_id"] for row in m3_gold} == id_set
        and all(graph_is_valid(row) for row in m3_gold)
    )
    valid_global_counterexamples = {
        row["proof_id"] for row in gold
        if row["gold_counterexample_status"] == "valid"
        and row["gold_counterexample"]["scope"] == "original_theorem"
    }
    m4_acceptance_path = ROOT / "data" / "benchmarks" / "m4" / "integrated_acceptance_v1_1.json"
    m4_acceptance = load_json(m4_acceptance_path)
    m4_counterexample_review_valid = (
        set(m4_acceptance["benchmark"]["sample_ids"]) == valid_global_counterexamples
        and m4_acceptance["reviewer_id"] != m4_acceptance["verifier_id"]
        and m4_acceptance["benchmark"]["valid_counterexample_count"] == len(valid_global_counterexamples)
        and m4_acceptance["benchmark"]["accepted_count"] == len(valid_global_counterexamples)
        and m4_acceptance["status"] == "accepted_by_person_a_and_person_b"
    )

    hashes_match = (
        manifest["inputs"]["source_sha256"] == sha256(source_path)
        and manifest["inputs"]["person_a_sha256"] == sha256(a_path)
        and manifest["inputs"]["person_b_sha256"] == sha256(b_path)
        and manifest["inputs"]["adjudications_sha256"] == sha256(decisions_path)
        and manifest["output_sha256"] == sha256(gold_path)
    )
    same_id_sets = id_set == {x["sample_id"] for x in annotations_a} == {x["sample_id"] for x in annotations_b} == {x["proof_id"] for x in gold}
    dispute_keys = {(x["sample_id"], x["field"]) for x in disagreements}
    decision_keys = {(x["sample_id"], x["field"]) for x in decisions}
    root_manifest_current = (
        root_manifest["release_status"] == "frozen_engineering_pilot_strict_acceptance_blocked"
        and root_manifest["source_sha256"] == sha256(source_path)
        and root_manifest["person_a_annotation_sha256"] == sha256(a_path)
        and root_manifest["person_b_annotation_sha256"] == sha256(b_path)
        and root_manifest["disagreement_sha256"] == sha256(disagreements_path)
        and root_manifest["agreement_report_sha256"] == sha256(agreement_path)
        and root_manifest["adjudication_sha256"] == sha256(decisions_path)
        and root_manifest["gold_sha256"] == sha256(gold_path)
        and root_manifest["registry_sha256"] == sha256(registry_path)
        and root_manifest["held_out"] is False
    )

    automated = {
        "utf8_without_replacement_characters": not replacement_char_files,
        "source_has_50_unique_ids": len(ids) == len(id_set) == 50,
        "a_b_and_gold_cover_source": same_id_sets,
        "all_disagreements_adjudicated_once": dispute_keys == decision_keys and len(decisions) == len(decision_keys),
        "gold_manifest_hashes_match": hashes_match,
        "registry_covers_all_samples": registered == id_set,
        "exact_duplicate_families_registered": duplicate_groups_covered,
        "prompt_and_theorem_bank_exact_leakage_absent": not leaked_ids,
        "root_manifest_binds_current_release": root_manifest_current,
        "posthoc_m3_node_coverage_edges_and_dag_valid": m3_graphs_valid,
        "all_global_counterexamples_have_distinct_m4_reviewer_and_verifier": m4_counterexample_review_valid,
    }
    human_evidence = {
        "reference_proof_per_sample": registry["evidence_status"]["reference_proofs"],
        "source_and_license_per_sample": registry["evidence_status"]["source_and_license"],
        "injector_and_non_injector_diff_review": registry["evidence_status"]["injection_diff_reviews"],
        "annotator_qualification_and_calibration": registry["evidence_status"]["qualification_and_calibration"],
        "blind_independence_reconstructable": registry["evidence_status"]["blind_independence"],
        "global_counterexamples_second_reviewed": "pass" if m4_counterexample_review_valid else "fail_m4_review_coverage_or_identity",
        "held_out_test_without_answer_exposure": registry["evidence_status"]["held_out_test"],
    }
    representation_gates = {
        "source_spans_node_coverage_edges_and_dag": registry["evidence_status"]["graph_and_span_gold"],
        "per_sample_split_and_version_metadata": registry["evidence_status"]["per_sample_split_metadata"],
    }
    strict_pass = (
        all(automated.values())
        and all(value == "pass" for value in human_evidence.values())
        and all(value == "pass" for value in representation_gates.values())
    )
    return {
        "schema_version": "m2-revalidation-1.0",
        "benchmark": "m2_algebra_pilot_50",
        "result": "pass" if strict_pass else "engineering_pass_strict_acceptance_blocked",
        "automated_checks": automated,
        "human_evidence_gates": human_evidence,
        "representation_gates": representation_gates,
        "statistics": {
            "source_rows": len(source),
            "person_a_rows": len(annotations_a),
            "person_b_rows": len(annotations_b),
            "gold_rows": len(gold),
            "field_disagreements": len(disagreements),
            "adjudication_decisions": len(decisions),
            "gold_validity_distribution": dict(sorted(Counter(x["gold_validity_status"] for x in gold).items())),
            "exact_duplicate_groups": exact_groups,
            "variable_normalized_candidate_groups": template_groups,
            "exact_prompt_or_theorem_bank_leak_ids": leaked_ids,
            "replacement_character_files": replacement_char_files,
        },
        "immutable_hashes": {
            "source_sha256": sha256(source_path),
            "person_a_sha256": sha256(a_path),
            "person_b_sha256": sha256(b_path),
            "adjudications_sha256": sha256(decisions_path),
            "disagreements_sha256": sha256(disagreements_path),
            "agreement_report_sha256": sha256(agreement_path),
            "gold_sha256": sha256(gold_path),
            "registry_sha256": sha256(registry_path),
            "m3_graph_gold_sha256": sha256(m3_gold_path),
            "m4_counterexample_acceptance_sha256": sha256(m4_acceptance_path),
        },
        "limitations": registry["limitations"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 1 if args.strict and report["result"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
