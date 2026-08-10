import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/math-proof-repair-agent/scripts/check_obligations.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("check_obligations", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class CheckerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = CHECKER.read_jsonl(
            ROOT / "data/theorem_bank/artin_clean_seed_rules.jsonl"
        )

    def build(self, item):
        return CHECKER.build_result(item, self.bank, max_rules=5)
