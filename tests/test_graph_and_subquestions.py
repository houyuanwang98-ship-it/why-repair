import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

from checker_test_case import CHECKER, ROOT, CheckerTestCase


class GraphAndSubquestionsTest(CheckerTestCase):
    def test_explicit_subquestions_are_split(self):
                item = {
                    "id": "multipart",
                    "domain": "algebra",
                    "topic": "fields",
                    "assumptions": ["F is a field"],
                    "problem_text": "(1) Prove P.\n(2) Prove Q using part (1).",
                    "proof_text": "(1) P holds.\n(2) Therefore Q holds.",
                }
                parts = CHECKER.split_item_into_subquestions(item)
                self.assertEqual(["1", "2"], [part["subquestion_label"] for part in parts])
                self.assertEqual("multipart_part_1", parts[0]["id"])
                self.assertEqual(["P holds."], parts[0]["flawed_proof_steps"])
                self.assertEqual(["Therefore Q holds."], parts[1]["flawed_proof_steps"])

    def test_unlabeled_consecutive_questions_are_not_split(self):
                item = {
                    "id": "unlabeled",
                    "theorem": "Is P true? Is Q true?",
                    "flawed_proof_steps": ["P holds.", "Q holds."],
                }
                self.assertEqual([item], CHECKER.split_item_into_subquestions(item))

    def test_accepted_prior_nodes_become_temporary_rules(self):
                item = {
                    "id": "part_1",
                    "parent_id": "multipart",
                    "subquestion_label": "1",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Prove x*0=0.",
                    "assumptions": ["x is in a field"],
                    "flawed_proof_steps": ["x*0=0."],
                }
                def valid_calculation(source, target, _context):
                    return {
                        "decision": "valid_transformation",
                        "source_expression": source,
                        "target_expression": target,
                        "atomic_steps": [{
                            "expression": target,
                            "rule": "multiplicative_identity",
                            "required_conditions": [],
                        }],
                        "used_axioms": ["multiplicative_identity"],
                        "introduced_assumptions": [],
                        "missing_conditions": [],
                        "reasoning_summary": "The field identity law closes the calculation.",
                        "confidence": "high",
                    }

                result = CHECKER.build_result(
                    item, self.bank, max_rules=5,
                    calculation_adjudicator=valid_calculation,
                )
                rules = CHECKER.rules_from_accepted_subquestion(result)
                self.assertEqual(1, len(rules))
                self.assertEqual("prior_subquestion", rules[0]["rule_role"])
                self.assertEqual("x*0=0.", rules[0]["conclusion"])
                self.assertEqual("Earlier subquestion 1", rules[0]["source"])

    def test_ambient_fact_adjudication_uses_direct_source_evidence(self):
                item = {
                    "id": "ambient_rk",
                    "theorem": "Prove R^k is separable.",
                    "assumptions": [],
                    "flawed_proof_steps": ["Use rational points."],
                }
                response = {"results": [{
                    "result_id": item["id"],
                    "facts": [{
                        "kind": "positive_integer",
                        "subject": "k",
                        "object": None,
                        "source_text": "R^k",
                        "derivation_rule": "standard_notation",
                        "reasoning": "The exponent in the standard notation R^k is a positive integer.",
                    }],
                    "abstained_conditions": [],
                }]}
                facts = CHECKER.ambient_facts_from_adjudication(response, [item])
                self.assertEqual(
                    {item["id"]: ["k is a positive integer."]},
                    facts,
                )
                self.assertTrue(CHECKER.condition_satisfied(
                    "k is a positive integer", facts[item["id"]]
                ))

                unsupported = copy.deepcopy(response)
                unsupported["results"][0]["facts"][0]["source_text"] = (
                    "The student later assumes k is positive."
                )
                self.assertIsNone(
                    CHECKER.ambient_facts_from_adjudication(unsupported, [item])
                )

    def test_ambient_facts_are_reused_by_every_node_and_cache_fingerprint(self):
                item = {
                    "id": "ambient_reuse",
                    "domain": "real analysis",
                    "topic": "metric spaces",
                    "theorem": "Prove R^k is separable.",
                    "assumptions": [],
                    "flawed_proof_steps": [
                        "Choose rational coordinates.",
                        "Therefore Q^k is dense in R^k.",
                    ],
                }
                graph_response = {"nodes": [
                    {"node_id": 1, "depends_on": [],
                     "self_contained_claim": item["flawed_proof_steps"][0]},
                    {"node_id": 2, "depends_on": [1],
                     "self_contained_claim": item["flawed_proof_steps"][1]},
                ]}
                fact = "k is a positive integer."
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={(item["id"], 0, "graph"): graph_response},
                    extra_ambient_facts=[fact],
                )
                self.assertTrue(all(
                    fact in node["ambient_facts"] for node in result["proof_graph"]
                ))

                common = {
                    "cache_context": {"checker": "test"},
                    "item": item,
                    "node_id": 1,
                    "is_final_node": False,
                    "claim": item["flawed_proof_steps"][0],
                    "node_type": "conclusion",
                    "dependency_source": "host_agent_graph_builder",
                    "dependency_entry": graph_response["nodes"][0],
                    "predecessor_nodes": [],
                    "accepted_claims": [],
                    "calculation_context": {"structure": "unknown"},
                    "calculation_source_expression": None,
                    "local_context": [],
                    "host_adjudications": {},
                }
                without_fact = CHECKER.node_cache_fingerprint(
                    ambient_facts=[], **common
                )
                with_fact = CHECKER.node_cache_fingerprint(
                    ambient_facts=[fact], **common
                )
                self.assertNotEqual(without_fact, with_fact)

    def test_ambient_facts_and_retrieval_abstention(self):
                item = {
                    "domain": "analysis",
                    "topic": "metric spaces",
                    "theorem": "Let E be a subset of the metric space (X,d).",
                    "assumptions": [],
                }
                facts = CHECKER.infer_ambient_facts(item)
                self.assertTrue(CHECKER.condition_satisfied(
                    "E is a subset of a metric space", facts
                ))
                self.assertTrue(CHECKER.condition_satisfied("d is a metric", facts))
                base = {
                    "status": "valid_with_gap",
                    "gap_type": "implicit_standard_step",
                    "error_type": "proof_gap",
                    "diagnosis": "Needs checking.",
                    "repair_action": "expand_step",
                    "minimal_repair": "Check the step.",
                }
                weak = {
                    "rule_name": "Unrelated criterion",
                    "matched_conclusion": True,
                    "missing_conditions": ["A premise"],
                    "matched_query_fields": ["goal", "domain"],
                }
                abstained = CHECKER.diagnose_from_evidence(
                    item, "The conclusion.", base, weak, None, None
                )
                self.assertEqual(base["status"], abstained["status"])
                self.assertTrue(abstained["retrieval_abstained"])
                strong = dict(weak)
                strong["matched_query_fields"] = ["goal", "predecessors"]
                self.assertEqual(
                    "missing_assumption",
                    CHECKER.diagnose_from_evidence(
                        item, "The conclusion.", base, strong, None, None
                    )["status"],
                )

    def test_deterministic_graph_fast_path_is_strictly_linear(self):
                proof_steps = [
                    "Let x be a real number.",
                    "Therefore x+0=x.",
                ]
                plan = CHECKER.deterministic_linear_graph(proof_steps)
                self.assertEqual([], plan[1]["depends_on"])
                self.assertEqual([1], plan[2]["depends_on"])
                self.assertIsNone(CHECKER.deterministic_linear_graph([
                    "Let x be a real number.",
                    "Therefore x+0=x.",
                    "Hence x+0+0=x.",
                ]))
                self.assertIsNone(CHECKER.deterministic_linear_graph([
                    "Let x be a real number.",
                    "This proves the claim.",
                ]))

    def test_global_graph_builder_connects_multiple_direct_dependencies(self):
                item = {
                    "id": "global_graph",
                    "domain": "algebra",
                    "topic": "linear_equations",
                    "theorem": "Given x+y=5 and x-y=1, prove x=3.",
                    "assumptions": [],
                    "flawed_proof_steps": [
                        "We have x+y=5.",
                        "We have x-y=1.",
                        "Adding the equations gives 2x=6.",
                    ],
                }
                graph_response = {
                    "nodes": [
                        {"node_id": 1, "depends_on": [], "self_contained_claim": "x+y=5."},
                        {"node_id": 2, "depends_on": [], "self_contained_claim": "x-y=1."},
                        {
                            "node_id": 3,
                            "depends_on": [1, 2],
                            "self_contained_claim": "Adding x+y=5 and x-y=1 gives 2x=6.",
                        },
                    ]
                }
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={("global_graph", 0, "graph"): graph_response},
                )
                node = result["proof_graph"][2]
                self.assertEqual([1, 2], node["depends_on"])
                self.assertEqual(item["flawed_proof_steps"][:2], node["local_context"])
                self.assertEqual("host_agent_graph_builder", node["dependency_source"])
                self.assertIn("Adding x+y=5 and x-y=1", node["obligation"])

    def test_graph_context_excludes_unrelated_earlier_nodes(self):
                item = {
                    "id": "selected_context",
                    "domain": "algebra",
                    "topic": "groups",
                    "theorem": "Prove Q.",
                    "assumptions": ["P implies Q"],
                    "flawed_proof_steps": ["P holds.", "R holds.", "Therefore Q holds."],
                }
                graph_response = {
                    "nodes": [
                        {"node_id": 1, "depends_on": [], "self_contained_claim": "P holds."},
                        {"node_id": 2, "depends_on": [], "self_contained_claim": "R holds."},
                        {"node_id": 3, "depends_on": [1], "self_contained_claim": "Q holds."},
                    ]
                }
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={("selected_context", 0, "graph"): graph_response},
                )
                self.assertEqual(
                    ["P implies Q", "P holds."],
                    result["proof_graph"][2]["local_context"],
                )

    def test_invalid_global_graph_is_rejected_as_a_whole(self):
                proof_steps = ["P holds.", "Therefore Q holds."]
                missing_node = {
                    "nodes": [
                        {"node_id": 1, "depends_on": [], "self_contained_claim": "P holds."}
                    ]
                }
                forward_reference = {
                    "nodes": [
                        {"node_id": 1, "depends_on": [2], "self_contained_claim": "P holds."},
                        {"node_id": 2, "depends_on": [], "self_contained_claim": "Q holds."},
                    ]
                }
                self.assertIsNone(
                    CHECKER.validate_graph_builder_response(missing_node, proof_steps)
                )
                self.assertIsNone(
                    CHECKER.validate_graph_builder_response(forward_reference, proof_steps)
                )

    def test_dependency_frontier_batches_independent_nodes(self):
                item = {
                    "id": "frontier",
                    "domain": "algebra",
                    "topic": "groups",
                    "theorem": "Show the final claim.",
                    "assumptions": [],
                    "flawed_proof_steps": [
                        "Start with the construction.",
                        "P holds.",
                        "Q holds.",
                        "The final claim follows from P.",
                    ],
                }
                graph_response = {"nodes": [
                    {"node_id": 1, "depends_on": [],
                     "self_contained_claim": "Start with the construction."},
                    {"node_id": 2, "depends_on": [], "self_contained_claim": "P holds."},
                    {"node_id": 3, "depends_on": [], "self_contained_claim": "Q holds."},
                    {"node_id": 4, "depends_on": [2],
                     "self_contained_claim": "The final claim follows from P."},
                ]}
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={("frontier", 0, "graph"): graph_response},
                )
                template = CHECKER.build_host_adjudication_template([result])
                self.assertEqual(
                    [2, 3],
                    [entry["node_id"] for entry in template["adjudications"]],
                )
                legacy = CHECKER.build_host_adjudication_template(
                    [result], use_frontier=False, bundle_primary=False
                )
                self.assertEqual(1, len(legacy["adjudications"]))
                self.assertEqual("proof", legacy["adjudications"][0]["kind"])


if __name__ == "__main__":
    unittest.main()
