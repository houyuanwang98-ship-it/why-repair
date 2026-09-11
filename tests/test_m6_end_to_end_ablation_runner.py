import unittest

from scripts.run_m6_end_to_end_ablation import ACCEPTANCE_CASES, METHODS, case_ids


class M6EndToEndRunnerTests(unittest.TestCase):
    def test_acceptance_set_is_frozen(self):
        self.assertEqual(case_ids("acceptance3"), ACCEPTANCE_CASES)

    def test_full50_is_exact_and_method_matrix_has_250_assignments(self):
        cases = case_ids("full50")
        self.assertEqual(cases, tuple(f"m2-{index:03d}" for index in range(1, 51)))
        self.assertEqual(len(METHODS) * len(cases), 250)


if __name__ == "__main__":
    unittest.main()
