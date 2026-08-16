import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).parents[1]
PACKET = ROOT / "data/benchmarks/m5/external_evidence_packet_v0_2.json"
SPEC = importlib.util.spec_from_file_location(
    "verify_m5_external_evidence", ROOT / "scripts/verify_m5_external_evidence.py")
VERIFY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(VERIFY)


class M5ExternalEvidencePacketTest(unittest.TestCase):
    def test_packet_is_schema_valid_and_binds_provisional_acceptance(self):
        schema = json.loads((ROOT / "schemas/m5_external_evidence_packet_v0_2.schema.json").read_text())
        packet = json.loads(PACKET.read_text())
        jsonschema.validate(packet, schema)
        acceptance = ROOT / "data/benchmarks/m5/provisional_joint_acceptance_v0_2.json"
        self.assertEqual(packet["locked_provisional_acceptance_sha256"],
                         hashlib.sha256(acceptance.read_bytes()).hexdigest())

    def test_pending_external_slots_fail_closed(self):
        packet = json.loads(PACKET.read_text())
        self.assertEqual(packet["status"], "awaiting_external_evidence")
        self.assertFalse(packet["m6_entry_allowed"])
        self.assertEqual({slot["status"] for slot in packet["evidence_slots"].values()}, {"pending"})
        self.assertFalse(VERIFY.verify_packet(packet))

    def test_metadata_only_completion_cannot_open_m6(self):
        packet = json.loads(PACKET.read_text())
        packet["status"] = "complete"
        packet["m6_entry_allowed"] = True
        for index, slot in enumerate(packet["evidence_slots"].values(), 1):
            slot.update({
                "status": "verified", "evidence_file": "missing.json",
                "evidence_digest": "0" * 64, "reviewer_id": f"fake-reviewer-{index}",
                "signature_method": "ssh", "detached_signature_file": "missing.sig",
                "allowed_signers_file": "missing.allowed",
            })
        self.assertFalse(VERIFY.verify_packet(packet))

    @unittest.skipUnless(shutil.which("ssh-keygen"), "ssh-keygen is required")
    def test_three_real_ssh_signatures_can_verify(self):
        packet = json.loads(PACKET.read_text())
        packet["status"] = "complete"
        packet["m6_entry_allowed"] = True
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            key = temp / "review_key"
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
                           check=True, capture_output=True)
            public_key = (temp / "review_key.pub").read_text().strip()
            for index, slot in enumerate(packet["evidence_slots"].values(), 1):
                identity = f"reviewer-{index}"
                payload = temp / f"evidence-{index}.json"
                payload.write_text(json.dumps({"reviewer": identity, "decision": "pass"}))
                subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key),
                                "-n", "why-repair-m5", str(payload)],
                               check=True, capture_output=True)
                allowed = temp / f"allowed-{index}"
                allowed.write_text(f"{identity} {public_key}\n")
                slot.update({
                    "status": "verified", "evidence_file": str(payload),
                    "evidence_digest": hashlib.sha256(payload.read_bytes()).hexdigest(),
                    "reviewer_id": identity, "signature_method": "ssh",
                    "detached_signature_file": str(payload) + ".sig",
                    "allowed_signers_file": str(allowed),
                })
            self.assertTrue(VERIFY.verify_packet(packet))


if __name__ == "__main__":
    unittest.main()
