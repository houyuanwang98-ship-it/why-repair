import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/benchmarks/m5/codex_builtin_smoke_v0_1/report.json"


def canonical_digest(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class M5CodexBuiltinSmokeTest(unittest.TestCase):
    def test_report_is_fail_closed_and_binds_every_reused_artifact(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(0, report["provider_api_calls"])
        self.assertFalse(report["scientific_claim_allowed"])
        self.assertEqual("blocked_no_independent_provider_provenance", report["formal_provider_gate"])
        bindings = []
        for case in report["cases"]:
            for key in ("patch", "prior_human_review"):
                if key in case:
                    bindings.append(case[key])
            bindings.extend(case.get("patches", []))
            bindings.extend(case.get("prior_human_reviews", []))
        self.assertEqual(8, len(bindings))
        for binding in bindings:
            with self.subTest(path=binding["path"]):
                self.assertEqual(binding["canonical_json_sha256"], canonical_digest(ROOT / binding["path"]))

    def test_three_cases_cover_one_and_two_round_repairs(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(["m2-011", "m2-018", "m2-034"], report["sample_ids"])
        self.assertEqual([1, 1, 2], [case["repair_rounds"] for case in report["cases"]])
        self.assertEqual(3, report["summary"]["accepted_case_count"])
        self.assertEqual(4, report["summary"]["repair_round_count"])


if __name__ == "__main__":
    unittest.main()
