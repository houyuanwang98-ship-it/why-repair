import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

from checker_test_case import CHECKER, ROOT, CheckerTestCase


class AdjudicationAndTheoremTest(CheckerTestCase):
    def test_bundled_response_expands_to_legacy_adjudications(self):
                primary = {"decision": "not_derivable"}
                diagnosis = {"diagnosis_review": "confirmed"}
                entry = {
                    "result_id": "bundle",
                    "node_id": 2,
                    "kind": "proof_diagnosis",
                    "response": {
                        "primary_response": primary,
                        "diagnosis_response": diagnosis,
                    },
                }
                expanded = CHECKER.expanded_adjudication_entries(entry)
                self.assertEqual(["proof", "diagnosis"], [item["kind"] for item in expanded])
                self.assertIs(primary, expanded[0]["response"])
                self.assertIs(diagnosis, expanded[1]["response"])

    def test_shared_rule_dictionary_externalizes_duplicate_rules(self):
                rule = {
                    "id": "identity",
                    "name": "Identity",
                    "score": 4.0,
                    "matched_fields": ["conclusion"],
                }
                payload = {
                    "primary_input": {"retrieved_rules": [rule]},
                    "diagnosis_if_nonclosed": {"retrieved_rules": [rule]},
                }
                dictionary = {}
                compact = CHECKER.externalize_retrieved_rules(payload, dictionary)
                primary_refs = compact["primary_input"]["retrieved_rule_refs"]
                diagnosis_refs = compact["diagnosis_if_nonclosed"]["retrieved_rule_refs"]
                self.assertEqual(primary_refs, diagnosis_refs)
                self.assertEqual(1, len(dictionary))
                self.assertEqual(rule, dictionary[primary_refs[0]])

    def test_high_confidence_gap_primary_supplies_final_diagnosis(self):
                primary = {
                    "decision": "derivable",
                    "reasoning_summary": "One intermediate equality is omitted.",
                    "completion_assessment": "omitted_intermediate_steps",
                    "original_step_requires_completion": True,
                    "bridge_steps": [{
                        "claim": "a=a*1",
                        "justification": "Multiplicative identity.",
                        "depends_on_context": ["a is in F"],
                    }],
                    "bridge_length": 1,
                    "counterexample_description": None,
                    "counterexample_verification": None,
                    "confidence": "high",
                }
                classification = {
                    "status": "missing_bridge_lemma",
                    "minimal_repair": "Insert a=a*1.",
                }
                diagnosis = CHECKER.diagnosis_from_high_confidence_primary(
                    "proof", primary, classification
                )
                self.assertEqual("confirmed", diagnosis["diagnosis_review"])
                self.assertEqual("missing_bridge_lemma", diagnosis["error_category"])
                low_confidence = dict(primary)
                low_confidence["confidence"] = "medium"
                self.assertIsNone(CHECKER.diagnosis_from_high_confidence_primary(
                    "proof", low_confidence, classification
                ))

    def test_problematic_node_emits_structured_diagnosis_request(self):
                item = CHECKER.read_jsonl(
                    ROOT / "data/samples/algebra_diagnosis_cases.jsonl"
                )[0]
                result = self.build(item)
                template = CHECKER.build_host_adjudication_template([result])
                entry = template["adjudications"][0]
                self.assertEqual("diagnosis", entry["kind"])
                self.assertEqual("DIAGNOSIS_ADJUDICATION_SCHEMA", entry["response_schema"])
                self.assertIn("preliminary_status", entry["input"])
                self.assertIn("deterministic_evidence", entry["input"])

    def test_false_positive_diagnosis_closes_node(self):
                preliminary = {
                    "status": "missing_bridge_lemma",
                    "gap_type": "implicit_standard_step",
                    "error_type": "missing_bridge_lemma",
                    "diagnosis": "A bridge appears to be missing.",
                    "repair_action": "insert_bridge_lemma",
                    "minimal_repair": "Insert a bridge.",
                }
                review = {
                    "diagnosis_review": "false_positive",
                    "error_category": "directly_justified",
                    "failed_inference": "No inference fails; the original sentence explicitly applies cancellation after stating the factor is nonzero.",
                    "violated_obligation": "No obligation is violated.",
                    "error_scope": "none",
                    "evidence": ["The preceding clause states a is nonzero before cancellation."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "none",
                    "minimal_repair": None,
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_diagnosis_adjudication(review, preliminary["status"])
                )
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary
                )
                self.assertEqual("closed", classification["status"])

    def test_confirmed_diagnosis_names_exact_failure(self):
                preliminary = {
                    "status": "theorem_misuse",
                    "gap_type": None,
                    "error_type": "theorem_misuse",
                    "diagnosis": "A theorem was misused.",
                    "repair_action": "replace_theorem",
                    "minimal_repair": "Replace the step.",
                }
                review = {
                    "diagnosis_review": "confirmed",
                    "error_category": "target_mismatch",
                    "failed_inference": "The calculation starts from sqrt(n^2-n)-n although the theorem asks for sqrt(n^2+n)-n.",
                    "violated_obligation": "The proof must preserve and establish the theorem's exact target expression.",
                    "error_scope": "local_node",
                    "evidence": ["The signs of the linear n terms differ."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "change_target",
                    "minimal_repair": "Restart the rationalization from sqrt(n^2+n)-n.",
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_diagnosis_adjudication(review, preliminary["status"])
                )
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary
                )
                self.assertEqual("target_mismatch", classification["status"])
                self.assertEqual("target_mismatch", classification["error_type"])
                self.assertIn("sqrt(n^2-n)-n", classification["diagnosis"])

    def test_vague_or_incompatible_diagnosis_is_rejected(self):
                vague = {
                    "diagnosis_review": "confirmed",
                    "error_category": "missing_bridge_lemma",
                    "failed_inference": "Proof is incomplete",
                    "violated_obligation": "More proof is required.",
                    "error_scope": "local_node",
                    "evidence": ["The proof is short."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "insert_bridge",
                    "minimal_repair": "Add detail.",
                    "theorem_dependency": None,
                    "confidence": "low",
                }
                self.assertFalse(
                    CHECKER.valid_diagnosis_adjudication(vague, "missing_bridge_lemma")
                )
                incompatible = dict(vague)
                incompatible["failed_inference"] = "The factor is cancelled without a nonzero premise."
                incompatible["error_category"] = "false_theorem"
                self.assertFalse(
                    CHECKER.valid_diagnosis_adjudication(
                        incompatible, "missing_bridge_lemma"
                    )
                )

    def test_host_diagnosis_can_reverse_deterministic_false_positive(self):
                item = {
                    "id": "diagnosis_false_positive",
                    "domain": "algebra",
                    "topic": "group_theory",
                    "theorem": "If N is normal in G, coset multiplication on G/N is well-defined.",
                    "assumptions": ["G is a group"],
                    "flawed_proof_steps": [
                        "N is a normal subgroup of G.",
                        "Coset multiplication is well-defined because N is a subgroup.",
                    ],
                }
                pending = self.build(item)
                self.assertEqual("theorem_misuse", pending["proof_graph"][1]["status"])
                review = {
                    "diagnosis_review": "false_positive",
                    "error_category": "directly_justified",
                    "failed_inference": "No inference fails because the direct predecessor already establishes that N is normal, which is the required condition.",
                    "violated_obligation": "No obligation is violated once the direct predecessor is included.",
                    "error_scope": "none",
                    "evidence": ["Node 1 states that N is a normal subgroup of G."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "none",
                    "minimal_repair": None,
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                resumed = CHECKER.build_result(
                    item,
                    self.bank,
                    max_rules=5,
                    host_adjudications={
                        ("diagnosis_false_positive", 2, "diagnosis"): review
                    },
                )
                node = resumed["proof_graph"][1]
                self.assertEqual("closed", node["status"])
                self.assertEqual("valid", resumed["validity_status"])
                self.assertEqual(review, node["diagnosis_adjudication"])
                self.assertEqual("host_agent_adjudication", node["verification_source"])
                self.assertEqual(
                    [], CHECKER.build_host_adjudication_template([resumed])["adjudications"]
                )

    def test_diagnosis_can_reclassify_missing_assumption_as_gap(self):
                preliminary = {
                    "status": "missing_assumption",
                    "gap_type": None,
                    "error_type": "missing_assumption",
                    "diagnosis": "A premise appears absent.",
                    "repair_action": "add_assumption",
                    "minimal_repair": "Add a premise.",
                }
                review = {
                    "diagnosis_review": "confirmed",
                    "error_category": "missing_bridge_lemma",
                    "failed_inference": "The construction does not state the smaller-radius choice that forces e_n to differ from x.",
                    "violated_obligation": "Construct points of E distinct from x and converging to x.",
                    "error_scope": "local_node",
                    "evidence": ["Choosing radius below d(y_n,x)/2 supplies the required distinctness."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "insert_bridge",
                    "minimal_repair": "Choose e_n with d(e_n,y_n)<d(y_n,x)/2.",
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_diagnosis_adjudication(review, preliminary["status"])
                )
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary
                )
                self.assertEqual("missing_bridge_lemma", classification["status"])

    def test_diagnosis_distinguishes_false_local_claim_from_false_theorem(self):
                preliminary = {
                    "status": "false_theorem",
                    "gap_type": None,
                    "error_type": "false_theorem",
                    "diagnosis": "The theorem was marked false.",
                    "repair_action": "counterexample",
                    "minimal_repair": "Change the theorem.",
                }
                review = {
                    "diagnosis_review": "confirmed",
                    "error_category": "false_local_claim",
                    "failed_inference": "The proof uses the complement of a finite intersection instead of the complement of the finite union.",
                    "violated_obligation": "Choose x_n outside every one of the first n cover members.",
                    "error_scope": "local_node",
                    "evidence": ["The original compactness theorem is not refuted by this local construction error."],
                    "counterexample_or_witness": "Two disjoint cover members have empty intersection but may cover X by their union.",
                    "claim_globally_derivable": True,
                    "repairability": "replace_step",
                    "minimal_repair": "Replace finite intersection by finite union.",
                    "theorem_dependency": None,
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_diagnosis_adjudication(review, preliminary["status"])
                )
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary
                )
                self.assertEqual("false_local_claim", classification["status"])

    def test_required_theorem_uses_local_candidates_before_web(self):
                bank = [{
                    "id": "quotient_group_construction",
                    "name": "Quotient group construction",
                    "domain": "algebra",
                    "topic": "group_theory",
                    "statement": "If G is a group and N is normal in G, coset multiplication on G/N is well-defined.",
                    "conditions": ["G is a group", "N is normal in G"],
                    "conclusion": "Coset multiplication on G/N is well-defined.",
                    "source": "Standard group theory",
                }]
                item = {
                    "id": "theorem_gate",
                    "domain": "algebra",
                    "topic": "group_theory",
                    "theorem": "If N is normal in G, multiplication on G/N is well-defined.",
                    "assumptions": ["G is a group"],
                    "flawed_proof_steps": [
                        "N is a normal subgroup of G.",
                        "Coset multiplication is well-defined because N is a subgroup.",
                    ],
                }
                dependency = {
                    "name": "Quotient group construction",
                    "statement": "A normal subgroup defines a quotient group.",
                    "conditions": ["G is a group", "N is normal in G"],
                    "conclusion": "Coset multiplication on G/N is well-defined.",
                    "why_required": "It is the exact rule justifying coset multiplication.",
                    "search_query": "normal subgroup quotient group multiplication well-defined",
                    "student_explicitly_invokes_theorem": False,
                }
                review = {
                    "diagnosis_review": "false_positive",
                    "error_category": "directly_justified",
                    "failed_inference": "No inference fails if the quotient-group theorem is valid and applicable.",
                    "violated_obligation": "No obligation is violated after theorem verification.",
                    "error_scope": "none",
                    "evidence": ["The direct predecessor states that N is normal in G."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "none",
                    "minimal_repair": None,
                    "theorem_dependency": dependency,
                    "confidence": "high",
                }
                diagnosis_key = ("theorem_gate", 2, "diagnosis")
                pending = CHECKER.build_result(
                    item,
                    bank,
                    max_rules=5,
                    host_adjudications={diagnosis_key: review},
                )
                node = pending["proof_graph"][1]
                self.assertTrue(node["theorem_candidates"])
                template = CHECKER.build_host_adjudication_template([pending])
                entry = template["adjudications"][0]
                self.assertEqual("theorem", entry["kind"])
                self.assertTrue(entry["input"]["local_candidates"])

                candidate = node["theorem_candidates"][0]
                theorem_response = {
                    "verification_status": "local_verified",
                    "theorem_name": candidate["name"],
                    "statement": candidate["statement"],
                    "conditions": candidate["conditions"],
                    "conclusion": candidate["conclusion"] or candidate["statement"],
                    "source_id": candidate["id"],
                    "source_url": None,
                    "source_title": candidate["source"] or candidate["name"],
                    "search_query": dependency["search_query"],
                    "search_attempted": "local_only",
                    "supports_claim": True,
                    "premises_satisfied": candidate["conditions"],
                    "missing_premises": [],
                    "is_foundational": True,
                    "direct_use_assessment": "direct_use_acceptable",
                    "evidence": ["The local rule states the exact quotient construction."],
                    "confidence": "high",
                }
                fabricated = dict(theorem_response)
                fabricated["statement"] = "A stronger theorem not present in the local bank."
                self.assertFalse(
                    CHECKER.valid_theorem_verification(
                        fabricated, dependency, node["theorem_candidates"], node["local_context"]
                    )
                )
                resumed = CHECKER.build_result(
                    item,
                    bank,
                    max_rules=5,
                    host_adjudications={
                        diagnosis_key: review,
                        ("theorem_gate", 2, "theorem"): theorem_response,
                    },
                )
                self.assertEqual("closed", resumed["proof_graph"][1]["status"])

    def test_web_verified_theorem_can_be_classified_as_gap(self):
                dependency = {
                    "name": "Supporting theorem",
                    "statement": "P implies Q.",
                    "conditions": ["P"],
                    "conclusion": "Q",
                    "why_required": "It is the required bridge.",
                    "search_query": "P implies Q theorem",
                    "student_explicitly_invokes_theorem": False,
                }
                verification = {
                    "verification_status": "web_verified",
                    "theorem_name": "Supporting theorem",
                    "statement": "P implies Q.",
                    "conditions": ["P"],
                    "conclusion": "Q",
                    "source_id": None,
                    "source_url": "https://example.edu/theorem",
                    "source_title": "University theorem notes",
                    "search_query": "P implies Q theorem",
                    "search_attempted": "local_and_web",
                    "supports_claim": True,
                    "premises_satisfied": ["P"],
                    "missing_premises": [],
                    "is_foundational": False,
                    "direct_use_assessment": "omission_is_gap",
                    "evidence": ["The opened source states P implies Q."],
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_theorem_verification(verification, dependency, [], ["P"])
                )
                skipped_local_search = dict(verification)
                skipped_local_search["search_attempted"] = "local_only"
                self.assertFalse(
                    CHECKER.valid_theorem_verification(
                        skipped_local_search, dependency, [], ["P"]
                    )
                )
                review = {
                    "diagnosis_review": "confirmed",
                    "error_category": "missing_bridge_lemma",
                    "failed_inference": "The proof omits the theorem connecting P to Q.",
                    "violated_obligation": "Supply the P-to-Q bridge.",
                    "error_scope": "local_node",
                    "evidence": ["P is available and Q is the target."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "insert_bridge",
                    "minimal_repair": "Cite the supporting theorem and apply it to P.",
                    "theorem_dependency": dependency,
                    "confidence": "high",
                }
                preliminary = {
                    "status": "missing_assumption", "gap_type": None,
                    "error_type": "missing_assumption", "diagnosis": "Unsupported.",
                    "repair_action": "add_assumption", "minimal_repair": "Add P.",
                }
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary, verification
                )
                self.assertEqual("missing_bridge_lemma", classification["status"])

    def test_unfound_proposed_theorem_does_not_clear_preliminary_error(self):
                dependency = {
                    "name": "Invented theorem",
                    "statement": "Every P implies Q.",
                    "conditions": ["P"],
                    "conclusion": "Q",
                    "why_required": "The model proposed it as the only bridge.",
                    "search_query": "invented theorem every P implies Q",
                    "student_explicitly_invokes_theorem": False,
                }
                verification = {
                    "verification_status": "not_found",
                    "theorem_name": "Invented theorem",
                    "statement": "",
                    "conditions": [],
                    "conclusion": "",
                    "source_id": None,
                    "source_url": None,
                    "source_title": None,
                    "search_query": dependency["search_query"],
                    "search_attempted": "local_and_web",
                    "supports_claim": False,
                    "premises_satisfied": [],
                    "missing_premises": [],
                    "is_foundational": None,
                    "direct_use_assessment": "not_applicable",
                    "evidence": ["Neither local lookup nor authoritative web search found the theorem."],
                    "confidence": "high",
                }
                self.assertTrue(
                    CHECKER.valid_theorem_verification(verification, dependency, [], [])
                )
                review = {
                    "diagnosis_review": "false_positive",
                    "error_category": "directly_justified",
                    "failed_inference": "No failure if the proposed theorem exists.",
                    "violated_obligation": "Verify the proposed theorem.",
                    "error_scope": "none",
                    "evidence": ["The proposed theorem would close the node."],
                    "counterexample_or_witness": None,
                    "claim_globally_derivable": True,
                    "repairability": "none",
                    "minimal_repair": None,
                    "theorem_dependency": dependency,
                    "confidence": "low",
                }
                preliminary = {
                    "status": "missing_assumption", "gap_type": None,
                    "error_type": "missing_assumption", "diagnosis": "Unsupported.",
                    "repair_action": "add_assumption", "minimal_repair": "Establish support.",
                }
                classification = CHECKER.classification_from_diagnosis_adjudication(
                    review, preliminary, verification
                )
                self.assertEqual("missing_assumption", classification["status"])


if __name__ == "__main__":
    unittest.main()
