import json
import re
import unittest

from scripts.build_m7_opc_v0_2_review_transfer import H2, V2, build


class M7OPCV02ReviewTransferTest(unittest.TestCase):
    def test_exact_proofs_only_are_transferred(self):
        transfer, supplemental = build()
        self.assertEqual(transfer, json.loads((V2 / "inherited_human_review.json").read_text()))
        self.assertEqual(supplemental, json.loads((H2 / "supplemental_review_batch_001.json").read_text()))
        self.assertEqual(19, transfer["exact_proof_review_count"])
        self.assertEqual(17, transfer["inherited_usable_node_gold_count"])
        self.assertEqual(6, transfer["changed_proof_review_required_count"])
        self.assertEqual(6, supplemental["row_count"])

    def test_changed_proofs_fail_closed(self):
        _, supplemental = build()
        self.assertTrue(all(not row["proof_identity_verified"] for row in supplemental["rows"]))
        self.assertTrue(all(row["human_verification"] is None for row in supplemental["rows"]))

    def test_supplemental_chinese_review_is_complete(self):
        text = (H2 / "supplemental_review_batch_001_zh.md").read_text()
        self.assertEqual(6, len(re.findall(r"^## 第 \d+ 题｜opc250-\d+$", text, re.MULTILINE)))
        self.assertEqual(6, text.count("### 审查摘要"))
        self.assertEqual((6, 6), (text.count("<details>"), text.count("</details>")))
        self.assertNotRegex(text, r"ZXQ\d+QXZ")


if __name__ == "__main__":
    unittest.main()
