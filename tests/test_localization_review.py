import copy
import json
import tempfile
import unittest
from pathlib import Path
from checker_test_case import CHECKER, ROOT
from proof_repair.localization import validate_review
from scripts.run_localization_review import run


class LocalInferenceReviewTest(unittest.TestCase):
    def item(self, first="Nonzero real numbers have a nonzero sum."):
        return {"id": "fresh", "theorem": "Prove u+v is nonzero.",
                "assumptions": ["u and v are nonzero real numbers."],
                "flawed_proof_steps": [first, "Therefore u+v is nonzero."]}

    def build(self, item, reviews=None, **kw):
        return CHECKER.build_result(item, [], 5, localization_reviews=reviews or {}, **kw)

    def response(self, request, decision="invalid", reason="u=7, v=-7 refutes the assertion."):
        return {"input_digest": request["input_digest"], "decision": decision,
                "used_premise_ids": [], "rule": "Addition over the reals",
                "condition_checks": ["7 and -7 are both nonzero; their sum is zero."],
                "circularity_check": "Target was not used as a premise.",
                "reason": reason, "bridge_steps": [],
                "error_type": "false_local_claim" if decision == "invalid" else None}

    def test_opening_assertion_no_longer_silently_accepted(self):
        item = self.item()
        self.assertEqual("closed", CHECKER.build_result(item, [], 5)["proof_graph"][0]["status"])
        new = self.build(item)
        self.assertEqual("undetermined", new["proof_graph"][0]["status"])
        request = new["proof_graph"][0]["local_inference_request"]
        reviewed = self.build(item, {request["input_digest"]: self.response(request)})
        self.assertEqual(1, reviewed["first_invalid_step"])
        self.assertEqual("downstream_invalid", reviewed["proof_graph"][1]["status"])

    def test_correct_opening_and_circular_opening_both_require_evidence(self):
        for text in ["The sum of two positive real numbers is positive.",
                     "Because u+v is nonzero, u+v is nonzero.",
                     "因为两个正数之和为正，所以两个正数之和为正。"]:
            with self.subTest(text=text):
                node = self.build(self.item(text))["proof_graph"][0]
                self.assertEqual("pending", node["local_review_state"])
                self.assertIn("circular reasoning", node["local_inference_request"]["instructions"])

    def test_stale_review_cannot_close_changed_claim_or_assumptions(self):
        item = self.item()
        request = self.build(item)["proof_graph"][0]["local_inference_request"]
        reviews = {request["input_digest"]: self.response(request, "accepted")}
        for field in ("theorem", "assumptions", "flawed_proof_steps"):
            changed = copy.deepcopy(item)
            if isinstance(changed[field], list):
                changed[field][0] += " Changed."
            else:
                changed[field] += " Changed."
            self.assertEqual("pending", self.build(changed, reviews)["proof_graph"][0]["local_review_state"])

    def test_request_has_no_future_gold_or_hidden_reasoning(self):
        item = self.item()
        item.update(gold_first_invalid_step=1, hidden_reasoning="SECRET")
        item["flawed_proof_steps"][1] = "FUTURE_SECRET"
        request = self.build(item)["proof_graph"][0]["local_inference_request"]
        self.assertNotIn("SECRET", json.dumps(request))
        self.assertNotIn("gold", json.dumps(request))

    def test_review_contract_rejects_future_premise_and_empty_evidence(self):
        request = self.build(self.item())["proof_graph"][0]["local_inference_request"]
        for field, value in [("used_premise_ids", [2]), ("condition_checks", []),
                             ("input_digest", "wrong"), ("bridge_steps", ["unneeded"]),
                             ("error_type", "false_theorem"), ("decision", []), ("error_type", [])]:
            review = self.response(request)
            review[field] = value
            self.assertFalse(validate_review(review, request))

    def test_prefix_review_must_complete_before_successor(self):
        item = self.item("u and v are nonzero real numbers.")
        initial = self.build(item)
        request = initial["proof_graph"][0]["local_inference_request"]
        self.assertEqual("blocked", initial["proof_graph"][1]["local_review_state"])
        accepted = self.response(request, "accepted", "Exact restatement of supplied assumptions.")
        resumed = self.build(item, {request["input_digest"]: accepted})
        self.assertEqual("closed", resumed["proof_graph"][0]["status"])
        self.assertEqual("pending", resumed["proof_graph"][1]["local_review_state"])

    def test_legacy_cache_cannot_bypass_review(self):
        cache = {"results": {}}
        item = self.item()
        CHECKER.build_result(item, [], 5, node_cache=cache)
        self.assertEqual("pending", self.build(item, node_cache=cache)["proof_graph"][0]["local_review_state"])

    def test_automatic_reviewer_receives_only_local_request_and_is_bounded(self):
        calls = []
        def reviewer(request):
            calls.append(request)
            return self.response(request, "accepted")
        result = CHECKER.build_result(self.item(), [], 5, localization_reviewer=reviewer,
                                      max_local_reviews=1)
        self.assertEqual(1, len(calls))
        self.assertEqual("pending", result["proof_graph"][1]["local_review_state"])
        self.assertEqual([], calls[0]["input"]["premises"])

    def test_failed_callback_abstains_and_preserves_failure(self):
        def fail(request):
            raise TimeoutError("test timeout")
        node = CHECKER.build_result(self.item(), [], 5, localization_reviewer=fail)["proof_graph"][0]
        self.assertEqual("undetermined", node["status"])
        self.assertEqual("failed:TimeoutError", node["local_review_call"])

    def test_correct_review_and_invalid_circular_review_are_distinct(self):
        for decision, expected in [("accepted", "closed"), ("invalid", "false_local_claim")]:
            result = CHECKER.build_result(self.item(), [], 5,
                localization_reviewer=lambda q: self.response(q, decision))
            self.assertEqual(expected, result["proof_graph"][0]["status"])

    def test_cli_session_resume_and_input_freeze(self):
        with tempfile.TemporaryDirectory() as temp:
            source, session = Path(temp) / "input.jsonl", Path(temp) / "session"
            source.write_text(json.dumps(self.item()) + "\n", encoding="utf-8")
            run(source, session)
            path = session / "pending.json"
            requests = json.loads(path.read_text(encoding="utf-8"))
            requests[0]["response"] = self.response(requests[0])
            path.write_text(json.dumps(requests), encoding="utf-8")
            run(source, session)
            result = json.loads((session / "results.json").read_text(encoding="utf-8"))[0]
            self.assertEqual(1, result["first_error_step"])
            self.assertTrue(result["first_error_certified"])
            source.write_text(json.dumps(self.item("changed")), encoding="utf-8")
            with self.assertRaises(ValueError):
                run(source, session)

    def test_chinese_session_requires_valid_graph_before_local_reviews(self):
        with tempfile.TemporaryDirectory() as temp:
            source, session = Path(temp) / "input.jsonl", Path(temp) / "session"
            item = self.item()
            item["flawed_proof_steps"] = ["非零实数相加仍非零。", "所以和非零。"]
            source.write_text(json.dumps(item), encoding="utf-8")
            summary = run(source, session)
            self.assertEqual(1, summary["pending_graph_reviews"])
            self.assertEqual(0, summary["pending_local_reviews"])
            path = session / "pending_graphs.json"
            requests = json.loads(path.read_text(encoding="utf-8"))
            requests[0]["response"] = {"nodes": [
                {"node_id": 1, "depends_on": [], "self_contained_claim": item["flawed_proof_steps"][0]},
                {"node_id": 2, "depends_on": [1], "self_contained_claim": item["flawed_proof_steps"][1]}]}
            path.write_text(json.dumps(requests), encoding="utf-8")
            summary = run(source, session)
            self.assertEqual(0, summary["pending_graph_reviews"])
            self.assertEqual(1, summary["pending_local_reviews"])


if __name__ == "__main__":
    unittest.main()
