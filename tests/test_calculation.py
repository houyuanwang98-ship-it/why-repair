import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

from checker_test_case import CHECKER, ROOT, CheckerTestCase


class CalculationTest(CheckerTestCase):
    def test_calculation_context_is_inherited(self):
                item = {
                    "id": "context_inheritance",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Simplify two field expressions.",
                    "assumptions": ["F is a field", "a is in F"],
                    "flawed_proof_steps": ["Let a be in F.", "a*1=a."],
                }
                result = self.build(item)
                first, second = result["proof_graph"]
                self.assertEqual("field", first["calculation_context"]["structure"])
                self.assertEqual("field", second["calculation_context"]["structure"])
                self.assertEqual(1, second["calculation_context"]["inherited_from_node_id"])

    def test_local_condition_updates_then_propagates(self):
                initial = CHECKER.initial_calculation_context({
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Work in a field.",
                    "assumptions": ["F is a field"],
                })
                changed = CHECKER.calculation_context_for_node(
                    initial, "Assume a is nonzero.", 1, "assumption"
                )
                inherited = CHECKER.calculation_context_for_node(
                    changed, "a*x=a*y.", 2, "calculation_step"
                )
                self.assertTrue(changed["context_changed"])
                self.assertIn("Assume a is nonzero.", changed["local_conditions"])
                self.assertFalse(inherited["context_changed"])
                self.assertEqual(changed["axioms"], inherited["axioms"])

    def test_calculation_model_cannot_use_unavailable_axiom(self):
                context = CHECKER.initial_calculation_context({
                    "domain": "algebra",
                    "topic": "groups",
                    "theorem": "Let G be a group.",
                    "assumptions": ["G is a group"],
                })
                adjudication = {
                    "decision": "valid_transformation",
                    "source_expression": "a*b",
                    "target_expression": "b*a",
                    "atomic_steps": [{
                        "expression": "b*a",
                        "rule": "commutativity",
                        "required_conditions": [],
                    }],
                    "used_axioms": ["commutativity"],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": "Swap the factors.",
                    "confidence": "high",
                }
                classification = CHECKER.classification_from_calculation_adjudication(
                    adjudication, "a*b", "b*a", context
                )
                self.assertEqual("theorem_misuse", classification["status"])

    def test_multi_step_calculation_is_a_gap(self):
                context = CHECKER.initial_calculation_context({
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Cancel a nonzero factor.",
                    "assumptions": ["F is a field", "a is nonzero"],
                })
                adjudication = {
                    "decision": "repairable_gap",
                    "source_expression": "a^{-1}*(a*x)",
                    "target_expression": "x",
                    "atomic_steps": [
                        {"expression": "(a^{-1}*a)*x", "rule": "multiplicative_associativity", "required_conditions": []},
                        {"expression": "1*x", "rule": "multiplicative_inverse", "required_conditions": ["a is nonzero"]},
                        {"expression": "x", "rule": "multiplicative_identity", "required_conditions": []},
                    ],
                    "used_axioms": ["multiplicative_associativity", "multiplicative_inverse", "multiplicative_identity"],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": "The student omitted three atomic simplifications.",
                    "confidence": "high",
                }
                classification = CHECKER.classification_from_calculation_adjudication(
                    adjudication, "a^{-1}*(a*x)", "x", context
                )
                self.assertEqual("missing_bridge_lemma", classification["status"])
                self.assertEqual("omitted_calculation_steps", classification["gap_type"])

    def test_host_agent_can_resume_calculation_adjudication(self):
                item = {
                    "id": "host_resume",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "For a,b,c in F, (a+b)*c=a*c+b*c.",
                    "assumptions": ["F is a field", "a,b,c are in F"],
                    "flawed_proof_steps": ["(a+b)*c=a*c+b*c."],
                }
                pending = self.build(item)
                node = pending["proof_graph"][0]
                self.assertEqual("undetermined", node["status"])
                template = CHECKER.build_host_adjudication_template([pending])
                entry = template["adjudications"][0]
                self.assertEqual("calculation_diagnosis", entry["kind"])
                self.assertEqual("calculation", entry["input"]["primary_kind"])

                response = {
                    "decision": "valid_transformation",
                    "source_expression": node["calculation_source_expression"],
                    "target_expression": node["claim"],
                    "atomic_steps": [{
                        "expression": node["claim"],
                        "rule": "distributivity",
                        "required_conditions": [],
                    }],
                    "used_axioms": ["distributivity"],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": "Apply distributivity.",
                    "confidence": "high",
                }
                resumed = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={("host_resume", 1, "calculation"): response},
                )
                resumed_node = resumed["proof_graph"][0]
                self.assertEqual("closed", resumed_node["status"])
                self.assertEqual("host_agent_adjudication", resumed_node["verification_source"])

    def test_session_resume_requeues_calculation_endpoint_mismatch(self):
                item = {
                    "id": "stale_calculation_endpoint",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "For a,b,c in F, a*(b+c)=a*b+a*c.",
                    "assumptions": ["F is a field", "a,b,c are in F"],
                    "flawed_proof_steps": ["a*(b+c)=a*b+a*c."],
                }
                graph_response = {"nodes": [{
                    "node_id": 1,
                    "depends_on": [],
                    "self_contained_claim": item["flawed_proof_steps"][0],
                }]}
                stale_response = {
                    "decision": "valid_transformation",
                    "source_expression": "An earlier accepted endpoint.",
                    "target_expression": item["flawed_proof_steps"][0],
                    "atomic_steps": [{
                        "expression": item["flawed_proof_steps"][0],
                        "rule": "distributivity",
                        "required_conditions": [],
                    }],
                    "used_axioms": ["distributivity"],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": "Apply distributivity.",
                    "confidence": "high",
                }
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={
                        (item["id"], 0, "graph"): graph_response,
                        (item["id"], 1, "calculation"): stale_response,
                    },
                )
                node = result["proof_graph"][0]
                self.assertEqual("undetermined", node["status"])
                self.assertEqual("valid_transformation", node["calculation_adjudication"]["decision"])

                template = CHECKER.build_host_adjudication_template([result])
                self.assertEqual(1, len(template["adjudications"]))
                entry = template["adjudications"][0]
                self.assertEqual("calculation_diagnosis", entry["kind"])
                self.assertEqual(
                    node["calculation_source_expression"],
                    entry["input"]["primary_input"]["source_expression"],
                )
                self.assertNotEqual(
                    stale_response["source_expression"],
                    entry["input"]["primary_input"]["source_expression"],
                )

    def test_validated_graph_stabilizes_independent_calculation_endpoints(self):
                item = {
                    "id": "stable_calculation_endpoint",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Assume P and prove distributivity.",
                    "assumptions": ["F is a field", "a,b,c are in F"],
                    "flawed_proof_steps": [
                        "Therefore P holds.",
                        "a*(b+c)=a*b+a*c.",
                    ],
                }
                graph_response = {"nodes": [
                    {
                        "node_id": 1,
                        "depends_on": [],
                        "self_contained_claim": item["flawed_proof_steps"][0],
                    },
                    {
                        "node_id": 2,
                        "depends_on": [],
                        "self_contained_claim": item["flawed_proof_steps"][1],
                    },
                ]}
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={
                        (item["id"], 0, "graph"): graph_response,
                    },
                )
                self.assertEqual(
                    " ; ".join(item["assumptions"]),
                    result["proof_graph"][1]["calculation_source_expression"],
                )

    def test_deterministic_calculation_replay_closes_atomic_identity(self):
                item = {
                    "id": "deterministic_calculation",
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "For a in F, a*1=a.",
                    "assumptions": ["F is a field", "a is in F"],
                    "flawed_proof_steps": ["a*1=a."],
                }
                result = self.build(item)
                node = result["proof_graph"][0]
                self.assertEqual("closed", node["status"])
                self.assertEqual("deterministic_checker", node["verification_source"])
                self.assertEqual(
                    "valid_transformation", node["calculation_adjudication"]["decision"]
                )
                self.assertEqual(
                    [], CHECKER.build_host_adjudication_template([result])["adjudications"]
                )

    def test_calculation_classification_requires_a_complete_relation(self):
                self.assertEqual(
                    "calculation_step", CHECKER.classify_node_type("x^2=4.")
                )
                self.assertEqual(
                    "calculation_step", CHECKER.classify_node_type("1/2 < 3/4 < 1.")
                )
                self.assertEqual(
                    "conclusion",
                    CHECKER.classify_node_type("The equation x^2=4 has two solutions."),
                )
                self.assertEqual(
                    "conclusion",
                    CHECKER.classify_node_type("The distance d(x,y)=2 proves separation."),
                )

    def test_safe_calculator_fully_parses_numeric_chains_radicals_and_fractions(self):
                context = CHECKER.initial_calculation_context({
                    "domain": "real analysis",
                    "topic": "real numbers",
                    "theorem": "Work over the real numbers.",
                    "assumptions": [],
                })
                valid = CHECKER.deterministic_calculation_replay(
                    "numeric witness",
                    r"\frac{1}{2} < 0.75 < \sqrt{1}",
                    context,
                )
                self.assertIsNotNone(valid)
                self.assertEqual(2, len(valid["atomic_steps"]))
                self.assertEqual(["ordered_field"], valid["used_axioms"])
                self.assertIsNotNone(CHECKER.deterministic_calculation_replay(
                    "numeric witness", "|-3|=3", context
                ))
                self.assertIsNone(CHECKER.deterministic_calculation_replay(
                    "numeric witness", "1/2 < 0.25 < 1", context
                ))

    def test_safe_calculator_closes_checker_owned_symbolic_identities_only(self):
                context = CHECKER.initial_calculation_context({
                    "domain": "algebra",
                    "topic": "fields",
                    "theorem": "Work in a field.",
                    "assumptions": ["F is a field"],
                })
                distributive = CHECKER.deterministic_calculation_replay(
                    "field axioms", "a*(b+c)=a*b+a*c", context
                )
                self.assertIsNotNone(distributive)
                self.assertEqual(["distributivity"], distributive["used_axioms"])
                self.assertIsNone(CHECKER.deterministic_calculation_replay(
                    "field axioms", "a*(b+c)=a*b+c", context
                ))
                self.assertIsNone(CHECKER.deterministic_calculation_replay(
                    "field axioms", "Because a*(b+c)=a*b+a*c, the claim follows", context
                ))

    def test_legacy_diagnosis_does_not_bypass_its_calculation_primary(self):
                item = {
                    "id": "legacy_calculation_diagnosis",
                    "domain": "real analysis",
                    "topic": "sequences",
                    "theorem": "A recurrence defines s_n. Find its limsup.",
                    "assumptions": [],
                    "flawed_proof_steps": [
                        "Claim s_{2m}=1/2-1/2^m and s_{2m+1}=1-1/2^m."
                    ],
                }
                calculation = {
                    "decision": "repairable_gap",
                    "source_expression": "",
                    "target_expression": item["flawed_proof_steps"][0],
                    "atomic_steps": [
                        {
                            "expression": "Derive the even recurrence.",
                            "rule": "equality_substitution",
                            "required_conditions": [],
                        },
                        {
                            "expression": "Solve the even and odd recurrences.",
                            "rule": "equality_substitution",
                            "required_conditions": [],
                        },
                    ],
                    "used_axioms": ["equality_substitution"],
                    "introduced_assumptions": [],
                    "missing_conditions": [],
                    "reasoning_summary": "The formulas require a recurrence derivation.",
                    "confidence": "high",
                }
                diagnosis = {
                    "diagnosis_review": "confirmed",
                    "error_category": "missing_bridge_lemma",
                    "failed_inference": "The closed forms are announced before they are derived.",
                    "violated_obligation": "Derive both formulas from the recurrence.",
                    "error_scope": "local_node",
                    "evidence": ["The node contains no recurrence calculation."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "insert_bridge",
                    "minimal_repair": "Derive both formulas from the recurrence.",
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                result = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={
                        (item["id"], 1, "calculation"): calculation,
                        (item["id"], 1, "diagnosis"): diagnosis,
                    },
                )
                node = result["proof_graph"][0]
                self.assertEqual(calculation, node["calculation_adjudication"])
                self.assertEqual(diagnosis, node["diagnosis_adjudication"])
                self.assertEqual("missing_bridge_lemma", node["status"])


if __name__ == "__main__":
    unittest.main()
