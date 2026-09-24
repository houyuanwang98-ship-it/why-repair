import unittest

from harness.repair_counterexample import _holds, replay_counterexample
from harness.constrained_repair_search import interface_proposal
from harness.iterative_localization import IterativeRepairSession
from harness.local_inference_v2 import ref
from harness.repair_contract import build_contract


class CounterexampleTest(unittest.TestCase):
    def setUp(self):
        nodes = [{"proof_id": "x", "node_id": i, "version": 1, "order_key": i,
                  "claim": claim, "self_contained_claim": claim, "node_type": "calculation",
                  "depends_on": [] if i == 1 else [{"proof_id": "x", "node_id": 1, "version": 1}]}
                 for i, claim in ((1, "x > 0"), (2, "x * x >= 0"))]
        snapshot = IterativeRepairSession(proof_id="x", theorem="x * x >= 0", assumptions=["x >= 0"],
                                          domain="reals", nodes=nodes).snapshot()
        self.contract = build_contract(snapshot, [ref(nodes[0])])
        self.proposal = interface_proposal(self.contract, snapshot, ["x != 0"])

    def test_zero_refutes_boundary_not_original_theorem(self):
        result = replay_counterexample(self.contract, self.proposal, {"x": "0"})
        self.assertEqual("refuted", result["status"])
        self.assertEqual([0], result["failed_outputs"])
        self.assertNotIn("theorem_false", result)

    def test_invalid_input_does_not_refute(self):
        self.assertEqual("not_counterexample", replay_counterexample(self.contract, self.proposal, {"x": "-1"})["status"])

    def test_supported_point_not_proof(self):
        self.assertEqual("not_counterexample", replay_counterexample(self.contract, self.proposal, {"x": "1/2"})["status"])

    def test_unsupported_premise_blocks(self):
        self.contract["context"]["assumptions"].append("x is continuous")
        self.assertEqual("undetermined", replay_counterexample(self.contract, self.proposal, {"x": "0"})["status"])

    def test_undefined_output_is_unknown(self):
        self.proposal["outputs"][0]["statement"] = "1 / x > 0"
        self.assertEqual("undetermined", replay_counterexample(self.contract, self.proposal, {"x": "0"})["status"])

    def test_no_execution_or_exponentiation(self):
        for text in ("__import__('os') == 0", "x ** 1000000 > 0", "True == 1"):
            with self.assertRaises(ValueError):
                _holds(text, {})

    def test_domain_and_missing_witness(self):
        self.assertEqual("undetermined", replay_counterexample(self.contract, self.proposal, {})["status"])
        self.contract["context"]["domain"] = "integers"
        self.assertEqual("undetermined", replay_counterexample(self.contract, self.proposal, {"x": "1/2"})["status"])


if __name__ == "__main__":
    unittest.main()
