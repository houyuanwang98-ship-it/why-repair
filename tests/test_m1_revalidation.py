import json
import hashlib
import re
import unittest
from pathlib import Path

from harness.controller import ALLOWED_TRANSITIONS
from harness.contracts import VALIDATORS


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "data/benchmarks/m1_role_revalidation_v1.json"
RECORD_SCHEMA = ROOT / "schemas/m1_role_revalidation_v1.schema.json"
CONTRACT_SCHEMA = ROOT / "schemas/dual_agent_harness_v0_3.schema.json"


class M1RevalidationTest(unittest.TestCase):
    def test_formal_records_have_all_standard_fields_and_existing_inputs(self):
        data = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual("v0.3.1", data["release"])
        self.assertEqual("pass_with_declared_human_review_limitation", data["engineering_exit"])
        required = {"validation_id", "target", "owner", "reviewer", "method", "inputs", "result", "evidence", "limitations", "timestamp"}
        self.assertEqual(5, len(data["records"]))
        for item in data["records"]:
            self.assertEqual(required, set(item), item["validation_id"])
            self.assertTrue(item["evidence"])
            for relative in item["inputs"]:
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_revalidation_schema_is_fail_closed(self):
        schema = json.loads(RECORD_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["record"]["additionalProperties"])
        self.assertEqual(set(schema["$defs"]["record"]["required"]), {
            "validation_id", "target", "owner", "reviewer", "method",
            "inputs", "result", "evidence", "limitations", "timestamp",
        })

    def test_portable_schema_covers_every_m1_required_object(self):
        schema = json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8"))
        required = {
            "ProofInstance", "ProofNode", "DependencyEdge", "LocalObligation",
            "EvaluationRecord", "ErrorCertificate", "CounterexampleCertificate",
            "PatchProposal", "PatchReview", "NodeVersion", "InvalidationRecord",
            "RunManifest", "ModelInvocation", "RetryRecord", "CacheFingerprint",
        }
        self.assertTrue(required <= set(schema["$defs"]))
        refs = {item["$ref"].split("/")[-1] for item in schema["oneOf"]}
        self.assertTrue(required <= refs)
        validator_defs = {
            "proof_instance": "ProofInstance", "proof_node": "ProofNode",
            "dependency_edge": "DependencyEdge", "local_obligation": "LocalObligation",
            "evaluation_record": "EvaluationRecord", "ambiguity_analysis": "AmbiguityAnalysis",
            "error_certificate": "ErrorCertificate", "counterexample_certificate": "CounterexampleCertificate",
            "patch_proposal": "PatchProposal", "patch_review": "PatchReview",
            "node_version": "NodeVersion", "invalidation_record": "InvalidationRecord",
            "run_manifest": "RunManifest", "model_invocation": "ModelInvocation",
            "retry_record": "RetryRecord", "cache_fingerprint": "CacheFingerprint",
        }
        self.assertEqual(set(VALIDATORS), set(validator_defs))
        self.assertEqual(refs, set(validator_defs.values()))

    def test_eight_m1_fixtures_are_present(self):
        names = {path.name for path in (ROOT / "data/fixtures/m1").glob("*.json")}
        self.assertEqual({
            "accepted_repair.json", "rejected_stale_patch.json",
            "ambiguity_branching.json", "insert_bridge_and_reevaluate.json",
            "illegal_transition.json", "missing_patch_review.json",
            "rollback_failure.json", "missing_version.json",
        }, names)

    def test_documented_state_table_matches_controller_exactly(self):
        text = (ROOT / "docs/milestones/M01_shared_contracts_and_controller.md").read_text(encoding="utf-8")
        match = re.search(r"Controller 生命周期：\n\n```text\n(.*?)\n```", text, re.S)
        self.assertIsNotNone(match)
        documented = {}
        for line in match.group(1).splitlines():
            source, destinations = (part.strip() for part in line.split("->", 1))
            documented[source] = set() if destinations == "(no outgoing transition)" else {
                item.strip() for item in destinations.split("|")
            }
        self.assertEqual(ALLOWED_TRANSITIONS, documented)

    def test_m1_freeze_manifest_binds_complete_release_surface(self):
        manifest = json.loads((ROOT / "data/benchmarks/m1_freeze_manifest_v0_3_1.json").read_text(encoding="utf-8"))
        self.assertEqual("m1-contract-v0.3.1", manifest["release"])
        self.assertEqual("0.3", manifest["wire_contract_version"])
        self.assertEqual(23, len(manifest["artifacts"]))
        for relative, expected in manifest["artifacts"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest(), relative)


if __name__ == "__main__":
    unittest.main()
