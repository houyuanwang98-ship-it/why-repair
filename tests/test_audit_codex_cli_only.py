import unittest

from scripts.audit_codex_cli_only import findings


class CodexCLIOnlyAuditTests(unittest.TestCase):
    def test_production_has_no_paid_api_sdk_or_key_reads(self):
        self.assertEqual(findings(), [])


if __name__ == "__main__":
    unittest.main()
