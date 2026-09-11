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
            config, rows = build(ROOT, model="fixture-model", output_dir=out,
                                 repository_commit="a" * 40,
                                 cli_version="codex-cli fixture")
            self.assertEqual(list(SAMPLE_IDS), [row["sample_id"] for row in rows])
            self.assertEqual("codex_cli", config["provider"])
            self.assertEqual(0, config["max_cost_usd"])
            self.assertEqual("object", config["output_schema"]["type"])
            first = (out / "config.json").read_bytes(), (out / "assignments.jsonl").read_bytes()
            build(ROOT, model="fixture-model", output_dir=out,
                  repository_commit="a" * 40, cli_version="codex-cli fixture")
            self.assertEqual(first, ((out / "config.json").read_bytes(),
                                     (out / "assignments.jsonl").read_bytes()))
            parsed = [json.loads(line) for line in (out / "assignments.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(row["method_id"] == "full_system" for row in parsed))

    def test_packet_refuses_post_freeze_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            build(ROOT, model="fixture-model", output_dir=out,
                  repository_commit="a" * 40, cli_version="codex-cli fixture")
            with self.assertRaises(SystemExit):
                build(ROOT, model="different-model", output_dir=out,
                      repository_commit="a" * 40, cli_version="codex-cli fixture")


if __name__ == "__main__":
    unittest.main()
