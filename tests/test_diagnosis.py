import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

from checker_test_case import CHECKER, ROOT, CheckerTestCase


class DiagnosisTest(CheckerTestCase):
    def test_pilot_localization_is_preserved(self):
                items = CHECKER.read_jsonl(ROOT / "data/samples/algebra_pilot_3.jsonl")
                results = {item["id"]: self.build(item) for item in items}
                self.assertEqual(2, results["alg_001"]["first_undetermined_step"])
                self.assertEqual(3, results["alg_002"]["first_invalid_step"])
                self.assertEqual("downstream_invalid", results["alg_002"]["proof_graph"][3]["status"])
                self.assertEqual(2, results["alg_003"]["first_undetermined_step"])

    def test_applicability_evidence_is_emitted(self):
                item = {
                    "id": "field_cancellation_fixture",
                    "domain": "analysis",
                    "topic": "field_axioms",
                    "theorem": "If a != 0 and a*x = a*y, then x = y for real numbers a, x, y.",
                    "assumptions": ["a != 0", "a*x = a*y", "a, x, y are real numbers"],
                    "flawed_proof_steps": [
                        "a^{-1} * a * x = a^{-1} * a * y.",
                        "x = y.",
                    ],
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
                node = result["proof_graph"][1]
                self.assertEqual("artin_clean_field_cancellation", node["applicable_rule_id"])
                self.assertTrue(node["matched_conclusion"])
                self.assertFalse(node["missing_conditions"])

    def test_deterministic_error_categories(self):
                items = CHECKER.read_jsonl(
                    ROOT / "data/samples/algebra_diagnosis_cases.jsonl"
                )
                results = {item["id"]: self.build(item) for item in items}
                expected = {
                    "diag_missing_assumption": ("missing_assumption", "unsupported_inference"),
                    "diag_algebraic_invalidity": ("algebraic_invalidity", "unsupported_inference"),
                    "diag_false_theorem": ("false_theorem", "false_claim"),
                }
                for item_id, (status, logic_class) in expected.items():
                    with self.subTest(item_id=item_id):
                        result = results[item_id]
                        node = result["proof_graph"][result["first_invalid_step"] - 1]
                        self.assertEqual(status, node["status"])
                        self.assertEqual(logic_class, node["logic_class"])

    def test_gap_and_invalid_reasoning_are_separate(self):
                pilot = CHECKER.read_jsonl(ROOT / "data/samples/algebra_pilot_3.jsonl")
                def completion_adjudicator(_item, _claim, _context, _rules):
                    return {
                        "decision": "derivable",
                        "reasoning_summary": "A required intermediate dimension claim was omitted.",
                        "proof_outline": ["Apply rank-nullity."],
                        "completion_assessment": "omitted_intermediate_steps",
                        "original_step_requires_completion": True,
                        "bridge_steps": [{
                            "claim": "dim(V)=dim(ker(T))+dim(im(T)).",
                            "justification": "Rank-nullity theorem.",
                            "depends_on_context": ["T is linear", "ker(T)={0}"],
                        }],
                        "bridge_length": 1,
                        "counterexample_description": None,
                        "counterexample_verification": None,
                        "confidence": "high",
                    }

                gap = CHECKER.build_result(
                    pilot[0], self.bank, max_rules=5,
                    model_adjudicator=completion_adjudicator,
                )["proof_graph"][1]
                misuse = self.build(pilot[1])["proof_graph"][2]
                self.assertEqual("repairable_gap", gap["logic_class"])
                self.assertEqual("insert_local_justification", gap["repair_scope"])
                self.assertEqual("unsupported_inference", misuse["logic_class"])
                self.assertEqual("replace_local_step", misuse["repair_scope"])

    def test_false_theorem_requires_verified_counterexample(self):
                item = CHECKER.read_jsonl(
                    ROOT / "data/samples/algebra_diagnosis_cases.jsonl"
                )[-1]
                result = self.build(item)
                node = result["proof_graph"][0]
                self.assertEqual("false_theorem", result["validity_status"])
                self.assertIn("verification", node["counterexample"])

    def test_unresolved_obligation_uses_model_adjudicator(self):
                item = {
                    "id": "model_fallback",
                    "domain": "algebra",
                    "topic": "unknown_topic",
                    "theorem": "If P holds, then Q holds.",
                    "assumptions": ["P holds"],
                    "flawed_proof_steps": ["Therefore Q holds."],
                }

                def adjudicator(_item, _claim, _context, _rules):
                    return {
                        "decision": "derivable",
                        "reasoning_summary": "Q follows from P by the supplied implication.",
                        "proof_outline": ["Apply P implies Q.", "Conclude Q."],
                        "completion_assessment": "omitted_intermediate_steps",
                        "original_step_requires_completion": True,
                        "bridge_steps": [{
                            "claim": "P implies Q applies.",
                            "justification": "Modus ponens using P and P implies Q.",
                            "depends_on_context": ["P holds", "P implies Q"],
                        }],
                        "bridge_length": 1,
                        "counterexample_description": None,
                        "counterexample_verification": None,
                        "confidence": "high",
                    }

                result = CHECKER.build_result(
                    item, self.bank, max_rules=5, model_adjudicator=adjudicator
                )
                node = result["proof_graph"][0]
                self.assertEqual("missing_bridge_lemma", node["status"])
                self.assertEqual("model_adjudicator", node["verification_source"])
                self.assertEqual("derivable", node["model_adjudication"]["decision"])

    def test_unresolved_without_model_stays_undetermined(self):
                item = {
                    "id": "no_model_fallback",
                    "domain": "algebra",
                    "topic": "unknown_topic",
                    "theorem": "If P holds, then Q holds.",
                    "assumptions": ["P holds"],
                    "flawed_proof_steps": ["Therefore Q holds."],
                }
                result = self.build(item)
                node = result["proof_graph"][0]
                self.assertEqual("undetermined", node["status"])
                self.assertEqual("indeterminate", node["logic_class"])
                self.assertEqual(1, result["first_undetermined_step"])

    def test_model_counterexample_marks_false_claim(self):
                item = {
                    "id": "model_counterexample",
                    "domain": "algebra",
                    "topic": "unknown_topic",
                    "theorem": "If P holds, then Q holds.",
                    "assumptions": ["P holds"],
                    "flawed_proof_steps": ["Therefore Q holds."],
                }

                def adjudicator(_item, _claim, _context, _rules):
                    return {
                        "decision": "counterexample",
                        "reasoning_summary": "The assignment satisfies P and refutes Q.",
                        "proof_outline": [],
                        "completion_assessment": "not_applicable",
                        "original_step_requires_completion": False,
                        "bridge_steps": [],
                        "bridge_length": 0,
                        "counterexample_description": "Take P=true and Q=false.",
                        "counterexample_verification": "P is true while Q is false.",
                        "confidence": "high",
                    }

                result = CHECKER.build_result(
                    item, self.bank, max_rules=5, model_adjudicator=adjudicator
                )
                node = result["proof_graph"][0]
                self.assertEqual("false_theorem", node["status"])
                self.assertEqual("false_claim", node["logic_class"])
                self.assertEqual("counterexample", node["model_adjudication"]["decision"])

    def test_model_direct_inference_is_not_a_gap(self):
                adjudication = {
                    "decision": "derivable",
                    "reasoning_summary": "The named rule directly yields the claim.",
                    "proof_outline": ["Apply the named rule."],
                    "completion_assessment": "directly_justified",
                    "original_step_requires_completion": False,
                    "bridge_steps": [],
                    "bridge_length": 0,
                    "counterexample_description": None,
                    "counterexample_verification": None,
                    "confidence": "high",
                }
                classification = CHECKER.classification_from_model_adjudication(adjudication)
                self.assertEqual("closed", classification["status"])

    def test_inconsistent_model_completion_stays_undetermined(self):
                adjudication = {
                    "decision": "derivable",
                    "reasoning_summary": "The model claims a gap but supplies no bridge.",
                    "proof_outline": [],
                    "completion_assessment": "omitted_intermediate_steps",
                    "original_step_requires_completion": True,
                    "bridge_steps": [],
                    "bridge_length": 0,
                    "counterexample_description": None,
                    "counterexample_verification": None,
                    "confidence": "low",
                }
                classification = CHECKER.classification_from_model_adjudication(adjudication)
                self.assertEqual("undetermined", classification["status"])

    def test_deterministic_safe_rule_closes_only_exact_curated_shape(self):
                safe_rule = {
                    "id": "safe_interior_open",
                    "domain": "analysis",
                    "topic": "metric spaces",
                    "name": "Interior is open",
                    "statement": "The interior of a subset of a metric space is open.",
                    "conditions": ["E is a subset of a metric space"],
                    "conclusion": "E^o is open.",
                    "typical_uses": [],
                    "common_misuses": [],
                    "bridge_lemmas": [],
                    "repair_templates": [],
                    "deterministic_safe": True,
                    "deterministic_safe_kind": "interior_is_open",
                }
                item = {
                    "id": "safe_rule",
                    "domain": "analysis",
                    "topic": "metric spaces",
                    "theorem": "Let E be a subset of a metric space. Prove E^o is open.",
                    "assumptions": ["E is a subset of a metric space"],
                    "flawed_proof_steps": ["Choose x in E^o.", "Therefore E^o is open."],
                }
                result = CHECKER.build_result(item, [safe_rule], max_rules=5)
                node = result["proof_graph"][1]
                self.assertEqual("closed", node["status"])
                self.assertTrue(node["rule_applicability"][0]["deterministic_safe"])
                self.assertTrue(node["rule_applicability"][0]["deterministic_safe_goal_match"])

                unsafe_item = copy.deepcopy(item)
                unsafe_item["id"] = "safe_rule_wrong_goal"
                unsafe_item["flawed_proof_steps"][1] = "Therefore E is compact."
                unsafe = CHECKER.build_result(unsafe_item, [safe_rule], max_rules=5)
                self.assertNotEqual("closed", unsafe["proof_graph"][1]["status"])

    def test_deterministic_safe_rule_fails_closed_on_missing_condition_or_ocr(self):
                rule = {
                    "id": "safe_monotone",
                    "domain": "analysis",
                    "topic": "sequences",
                    "name": "Monotone convergence theorem",
                    "statement": "Every monotone bounded real sequence converges.",
                    "conditions": ["the sequence is monotone", "the sequence is bounded"],
                    "conclusion": "the sequence converges.",
                    "typical_uses": [],
                    "common_misuses": [],
                    "bridge_lemmas": [],
                    "repair_templates": [],
                    "deterministic_safe": True,
                    "deterministic_safe_kind": "monotone_bounded_sequence_converges",
                }
                item = {
                    "id": "safe_missing_condition",
                    "domain": "analysis",
                    "topic": "sequences",
                    "theorem": "Prove the sequence converges.",
                    "assumptions": ["the sequence is monotone"],
                    "flawed_proof_steps": ["We consider the sequence.", "Therefore the sequence converges."],
                }
                missing = CHECKER.build_result(item, [rule], max_rules=5)
                self.assertNotEqual("closed", missing["proof_graph"][1]["status"])

                item["assumptions"].append("the sequence is bounded")
                item["source_reliability"] = "OCR uncertain"
                uncertain = CHECKER.build_result(item, [rule], max_rules=5)
                self.assertNotEqual("closed", uncertain["proof_graph"][1]["status"])

    def test_diagnosis_category_regressions_are_reclassified(self):
                cases = [
                    (
                        "missing_assumption",
                        "missing_bridge_lemma",
                        "The construction must choose e_n distinct from x by using a radius below d(y_n,x)/2.",
                        None,
                        True,
                        "insert_bridge",
                        "Choose e_n with d(e_n,y_n)<d(y_n,x)/2.",
                    ),
                    (
                        "false_theorem",
                        "false_local_claim",
                        "The proof uses the complement of a finite intersection instead of the finite union.",
                        "Two disjoint cover members can have empty intersection while their union covers X.",
                        True,
                        "replace_step",
                        "Replace intersection by union in the construction of x_n.",
                    ),
                    (
                        "missing_assumption",
                        "missing_bridge_lemma",
                        "N_epsilon/2 must be replaced by a common threshold indexed by epsilon/2.",
                        None,
                        True,
                        "insert_bridge",
                        "Use max(N_a(epsilon/2),N_b(epsilon/2)).",
                    ),
                ]
                for preliminary_status, category, failure, witness, global_value, repairability, repair in cases:
                    with self.subTest(category=category, failure=failure):
                        review = {
                            "diagnosis_review": "confirmed",
                            "error_category": category,
                            "failed_inference": failure,
                            "violated_obligation": "Supply the exact locally valid inference.",
                            "error_scope": "local_node",
                            "evidence": [failure],
                            "counterexample_or_witness": witness,
                            "claim_globally_derivable": global_value,
                            "repairability": repairability,
                            "minimal_repair": repair,
                            "theorem_dependency": None,
                            "confidence": "high",
                        }
                        preliminary = {
                            "status": preliminary_status,
                            "gap_type": None,
                            "error_type": preliminary_status,
                            "diagnosis": "Preliminary category.",
                            "repair_action": "replace_step",
                            "minimal_repair": "Preliminary repair.",
                        }
                        self.assertTrue(
                            CHECKER.valid_diagnosis_adjudication(
                                review, preliminary_status
                            )
                        )
                        classification = CHECKER.classification_from_diagnosis_adjudication(
                            review, preliminary
                        )
                        self.assertEqual(category, classification["status"])


if __name__ == "__main__":
    unittest.main()
