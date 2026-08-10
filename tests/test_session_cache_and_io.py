import argparse
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from checker_test_case import CHECKER, ROOT, SCRIPT, CheckerTestCase


class SessionCacheAndIoTest(CheckerTestCase):
    def test_checker_source_digest_covers_modular_implementation(self):
        source_files = CHECKER.checker_source_files()
        relative_paths = {
            path.relative_to(SCRIPT.parent).as_posix()
            for path in source_files
        }
        self.assertIn("check_obligations.py", relative_paths)
        self.assertIn("proof_repair/pipeline.py", relative_paths)
        self.assertIn("proof_repair/cli.py", relative_paths)

        scripts_dir = SCRIPT.parent
        digest = hashlib.sha256()
        for path in source_files:
            digest.update(path.relative_to(scripts_dir).as_posix().encode("ascii"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        self.assertEqual(digest.hexdigest(), CHECKER.checker_source_digest())

    def test_node_cache_fingerprint_includes_calculation_endpoint(self):
                common = {
                    "cache_context": {"checker": "test"},
                    "item": {"id": "cached_endpoint", "assumptions": []},
                    "node_id": 1,
                    "is_final_node": True,
                    "claim": "x=x.",
                    "node_type": "calculation_step",
                    "dependency_source": "host_agent_graph_builder",
                    "dependency_entry": {
                        "depends_on": [],
                        "self_contained_claim": "x=x.",
                    },
                    "predecessor_nodes": [],
                    "accepted_claims": [],
                    "calculation_context": {"structure": "field"},
                    "local_context": [],
                    "ambient_facts": [],
                    "host_adjudications": {},
                }
                first = CHECKER.node_cache_fingerprint(
                    calculation_source_expression="old endpoint", **common
                )
                second = CHECKER.node_cache_fingerprint(
                    calculation_source_expression="new endpoint", **common
                )
                self.assertNotEqual(first, second)

    def test_session_ledger_persists_ambient_batch_response(self):
                with tempfile.TemporaryDirectory() as temp_dir:
                    response_path = Path(temp_dir) / "ambient.json"
                    ledger_path = Path(temp_dir) / "responses.jsonl"
                    ambient_response = {"results": [{
                        "result_id": "proof",
                        "facts": [],
                        "abstained_conditions": ["No direct background fact is needed."],
                    }]}
                    CHECKER.write_json(response_path, {"adjudications": [{
                        "result_id": CHECKER.AMBIENT_BATCH_RESULT_ID,
                        "node_id": 0,
                        "kind": "ambient",
                        "response": ambient_response,
                    }]})
                    ledger = {}
                    self.assertEqual(
                        1, CHECKER.ingest_adjudication_file(response_path, ledger)
                    )
                    CHECKER.write_response_ledger(ledger_path, ledger)
                    restored = CHECKER.load_response_ledger(ledger_path)
                    self.assertEqual(
                        ambient_response,
                        restored[(CHECKER.AMBIENT_BATCH_RESULT_ID, 0, "ambient")]["response"],
                    )

    def test_session_ledger_persists_graph_responses(self):
                with tempfile.TemporaryDirectory() as temp_dir:
                    response_path = Path(temp_dir) / "pending.json"
                    ledger_path = Path(temp_dir) / "responses.jsonl"
                    graph_response = {
                        "nodes": [{
                            "node_id": 1,
                            "depends_on": [],
                            "self_contained_claim": "P.",
                        }]
                    }
                    CHECKER.write_json(response_path, {"adjudications": [{
                        "result_id": "proof",
                        "node_id": 0,
                        "kind": "graph",
                        "response": graph_response,
                    }]})
                    ledger = {}
                    self.assertEqual(
                        1, CHECKER.ingest_adjudication_file(response_path, ledger)
                    )
                    CHECKER.write_response_ledger(ledger_path, ledger)
                    restored = CHECKER.load_response_ledger(ledger_path)
                    self.assertEqual(
                        graph_response, restored[("proof", 0, "graph")]["response"]
                    )

    def test_session_configuration_restores_without_repeating_paths(self):
                with tempfile.TemporaryDirectory() as temp_dir:
                    session_dir = Path(temp_dir) / "session"
                    base = {
                        "input": str(ROOT / "data/samples/algebra_pilot_3.jsonl"),
                        "theorem_bank": str(
                            ROOT / "data/theorem_bank/artin_clean_seed_rules.jsonl"
                        ),
                        "output_dir": None,
                        "session_dir": str(session_dir),
                        "max_rules": None,
                        "uncertain_policy": None,
                        "workflow_mode": None,
                        "model": None,
                        "model_max_output_tokens": None,
                        "emit_adjudication_template": None,
                        "adjudications": None,
                        "node_cache": None,
                        "write_changed_only": False,
                        "raw_proof": None,
                    }
                    parser = argparse.ArgumentParser()
                    first = CHECKER.resolve_runtime_configuration(
                        argparse.Namespace(**base), parser, ROOT
                    )
                    restored_args = dict(base)
                    restored_args["input"] = None
                    restored_args["theorem_bank"] = None
                    restored = CHECKER.resolve_runtime_configuration(
                        argparse.Namespace(**restored_args), parser, ROOT
                    )
                    self.assertEqual(first["input_path"], restored["input_path"])
                    self.assertEqual(first["theorem_bank_path"], restored["theorem_bank_path"])
                    self.assertEqual(session_dir / "pending.json", restored["pending_path"])
                    self.assertEqual(session_dir / "responses.jsonl", restored["response_ledger_path"])
                    self.assertEqual("grading", restored["workflow_mode"])

    def test_node_cache_reuses_unchanged_nodes(self):
                item = CHECKER.read_jsonl(
                    ROOT / "data/samples/algebra_pilot_3.jsonl"
                )[0]
                cache = CHECKER.empty_node_cache()
                first_stats = {}
                first = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    node_cache=cache,
                    cache_context={"test_run": "stable"},
                    cache_stats=first_stats,
                )
                self.assertEqual(len(first["proof_graph"]), first_stats["misses"])
                self.assertEqual(0, first_stats["hits"])

                second_stats = {}
                second = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    node_cache=cache,
                    cache_context={"test_run": "stable"},
                    cache_stats=second_stats,
                )
                self.assertEqual(first, second)
                self.assertEqual(len(second["proof_graph"]), second_stats["hits"])
                self.assertEqual(0, second_stats["misses"])

    def test_node_cache_invalidates_changed_node_and_descendants(self):
                item = {
                    "id": "cache_descendants",
                    "domain": "algebra",
                    "topic": "group_theory",
                    "theorem": "If N is normal in G, then G/N is a group.",
                    "assumptions": ["G is a group"],
                    "flawed_proof_steps": [
                        "N is a normal subgroup of G.",
                        "Coset multiplication is well-defined because N is a subgroup.",
                        "Therefore G/N is a group.",
                    ],
                }
                graph_response = {
                    "nodes": [
                        {
                            "node_id": 1,
                            "depends_on": [],
                            "self_contained_claim": "N is a normal subgroup of G.",
                        },
                        {
                            "node_id": 2,
                            "depends_on": [1],
                            "self_contained_claim": "Coset multiplication on G/N is well-defined.",
                        },
                        {
                            "node_id": 3,
                            "depends_on": [2],
                            "self_contained_claim": "G/N is a group.",
                        },
                    ]
                }
                graph_key = (item["id"], 0, "graph")
                cache = CHECKER.empty_node_cache()
                CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={graph_key: graph_response},
                    node_cache=cache,
                    cache_context={"test_run": "descendants"},
                    cache_stats={},
                )
                review = {
                    "diagnosis_review": "false_positive",
                    "error_category": "directly_justified",
                    "failed_inference": "No inference fails because the direct predecessor establishes that N is normal.",
                    "violated_obligation": "No obligation is violated once normality is included.",
                    "error_scope": "none",
                    "evidence": ["Node 1 states that N is normal in G."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "none",
                    "minimal_repair": None,
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                resumed_adjudications = {
                    graph_key: graph_response,
                    (item["id"], 2, "diagnosis"): review,
                }
                resumed_stats = {}
                resumed = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications=resumed_adjudications,
                    node_cache=cache,
                    cache_context={"test_run": "descendants"},
                    cache_stats=resumed_stats,
                )
                uncached = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications=resumed_adjudications,
                )
                self.assertEqual(uncached, resumed)
                self.assertEqual(1, resumed_stats["hits"])
                self.assertEqual(2, resumed_stats["misses"])
                self.assertEqual("closed", resumed["proof_graph"][1]["status"])
                self.assertNotEqual(
                    "downstream_invalid", resumed["proof_graph"][2]["status"]
                )

    def test_write_json_can_preserve_unchanged_file(self):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "result.json"
                    self.assertTrue(CHECKER.write_json(path, {"value": 1}))
                    self.assertFalse(
                        CHECKER.write_json(path, {"value": 1}, only_if_changed=True)
                    )
                    self.assertTrue(
                        CHECKER.write_json(path, {"value": 2}, only_if_changed=True)
                    )

    def test_malformed_node_cache_is_treated_as_empty(self):
                item = CHECKER.read_jsonl(
                    ROOT / "data/samples/algebra_pilot_3.jsonl"
                )[0]
                malformed = {
                    "schema_version": CHECKER.NODE_CACHE_SCHEMA_VERSION,
                    "results": {item["id"]: ["not", "a", "cached", "result"]},
                }
                stats = {}
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    node_cache=malformed,
                    cache_context={"test_run": "malformed"},
                    cache_stats=stats,
                )
                self.assertEqual(len(result["proof_graph"]), stats["misses"])
                self.assertEqual(0, stats["hits"])

    def test_skill_text_sources_are_ascii_only(self):
                skill_dir = ROOT / "skills/math-proof-repair-agent"
                text_suffixes = {".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}
                for path in skill_dir.rglob("*"):
                    if not path.is_file() or path.suffix.lower() not in text_suffixes:
                        continue
                    with self.subTest(path=path.relative_to(skill_dir)):
                        path.read_text(encoding="ascii")

    def test_json_output_preserves_unicode_text(self):
                value = {"theorem": "\u8bc1\u660e\u5e8f\u5217\u6536\u655b"}
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "result.json"
                    CHECKER.write_json(path, value)
                    raw = path.read_text(encoding="utf-8")
                self.assertIn(value["theorem"], raw)
                self.assertNotIn("\\u8bc1", raw)


if __name__ == "__main__":
    unittest.main()
