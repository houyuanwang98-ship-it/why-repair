import json
import unittest

from scripts.build_m7_opc_250_node_annotations_v0_1 import OUT, build


class M7OPC250NodeAnnotationsTest(unittest.TestCase):
    def test_materialized_nodes_rebuild_and_cover_all_cases(self):
        item = build()
        self.assertEqual(item, json.loads(OUT.read_text()))
        self.assertEqual(250, item["row_count"])
        self.assertEqual(250, len({row["case_id"] for row in item["rows"]}))
        self.assertTrue(all(row["proof_nodes"] for row in item["rows"]))

    def test_incorrect_rows_have_first_error_and_correct_rows_do_not(self):
        rows = build()["rows"]
        incorrect = [row for row in rows if row["proof_verdict"] == "incorrect"]
        correct = [row for row in rows if row["proof_verdict"] == "correct"]
        self.assertEqual((200, 50), (len(incorrect), len(correct)))
        self.assertEqual(197, sum(bool(row["first_error_node"]) for row in incorrect))
        self.assertEqual(["opc250-077", "opc250-083", "opc250-180"],
                         build()["manual_first_error_required"])
        self.assertTrue(all(row["error_type"] for row in incorrect))
        self.assertTrue(all(row["first_error_node"] is None and row["error_type"] is None for row in correct))

    def test_node_spans_are_ordered_and_exact(self):
        for row in build()["rows"]:
            nodes = row["proof_nodes"]
            self.assertEqual([f"n{i}" for i in range(1, len(nodes) + 1)], [node["node_id"] for node in nodes])
            self.assertTrue(all(node["start_char"] < node["end_char"] for node in nodes))
            self.assertTrue(all(a["end_char"] <= b["start_char"] for a, b in zip(nodes, nodes[1:])))


if __name__ == "__main__":
    unittest.main()
