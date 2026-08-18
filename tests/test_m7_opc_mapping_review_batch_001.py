import json
import re
import unittest

from scripts.build_m7_opc_mapping_review_batch_001 import OUT, build


class M7OPCMappingReviewBatch001Test(unittest.TestCase):
    def test_materialized_review_rebuilds(self):
        packet, markdown = build()
        self.assertEqual(packet, json.loads((OUT / "mapping_review_batch_001.json").read_text()))
        self.assertEqual(markdown + "\n", (OUT / "mapping_review_batch_001.md").read_text())
        self.assertEqual(25, packet["row_count"])
        self.assertEqual(25, len({row["case_id"] for row in packet["rows"]}))

    def test_packet_contains_all_unmapped_cases_and_usable_context(self):
        packet, _ = build()
        manual = [row for row in packet["rows"] if row["proposed_first_error_node"] is None]
        self.assertEqual(["opc250-077", "opc250-083", "opc250-180"],
                         [row["case_id"] for row in manual])
        self.assertEqual(3, len(manual))
        self.assertTrue(all(row["context_nodes"] for row in manual))
        sampled = [row for row in packet["rows"] if row["proposed_first_error_node"] is not None]
        self.assertTrue(all(1 <= len(row["context_nodes"]) <= 3 for row in sampled))
        self.assertTrue(all(row["human_verification"] is None for row in packet["rows"]))

    def test_chinese_review_is_complete_and_has_no_generator_artifacts(self):
        text = (OUT / "mapping_review_batch_001_zh.md").read_text()
        headings = re.findall(r"^## 第 \d+ 题｜(opc250-\d+)$", text, re.MULTILINE)
        self.assertEqual(25, len(headings))
        self.assertEqual([row["case_id"] for row in build()[0]["rows"]], headings)
        self.assertEqual(25, text.count("### 原题（中文释义）"))
        self.assertEqual(25, text.count("### 审查摘要"))
        self.assertEqual(25, text.count("展开完整原证明（已按节点编号）"))
        self.assertEqual(25, text.count("</details>"))
        self.assertNotRegex(text, r"ZXQ\d+QXZ")
        self.assertIn("中文 LaTeX 版", text)
        self.assertRegex(text, r"\\(?:frac|sum|triangle|leq|geq|infty)")


if __name__ == "__main__":
    unittest.main()
