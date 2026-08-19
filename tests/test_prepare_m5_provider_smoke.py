import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_m5_provider_smoke import SAMPLE_IDS, build


ROOT = Path(__file__).resolve().parents[1]


class PrepareM5ProviderSmokeTest(unittest.TestCase):
    def test_packet_is_deterministic_and_binds_three_diverse_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            config, rows = build(ROOT, model="fixture-model", input_price=1,
                                 cached_input_price=0.1, output_price=2,
                                 max_cost=0.5, output_dir=out,
                                 repository_commit="a" * 40)
            self.assertEqual(list(SAMPLE_IDS), [row["sample_id"] for row in rows])
            self.assertEqual("object", config["output_schema"]["type"])
            first = (out / "config.json").read_bytes(), (out / "assignments.jsonl").read_bytes()
            build(ROOT, model="fixture-model", input_price=1, cached_input_price=0.1,
                  output_price=2, max_cost=0.5, output_dir=out,
                  repository_commit="a" * 40)
            self.assertEqual(first, ((out / "config.json").read_bytes(),
                                     (out / "assignments.jsonl").read_bytes()))
            parsed = [json.loads(line) for line in (out / "assignments.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(row["method_id"] == "full_system" for row in parsed))

    def test_packet_refuses_post_freeze_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            build(ROOT, model="fixture-model", input_price=1, cached_input_price=0.1,
                  output_price=2, max_cost=0.5, output_dir=out,
                  repository_commit="a" * 40)
            with self.assertRaises(SystemExit):
                build(ROOT, model="different-model", input_price=1, cached_input_price=0.1,
                      output_price=2, max_cost=0.5, output_dir=out,
                      repository_commit="a" * 40)


if __name__ == "__main__":
    unittest.main()
