import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m2_benchmark import (  # noqa: E402
    M2ValidationError,
    build_agreement_report,
    build_gold,
    build_gold_manifest,
    cohen_kappa,
    confusion_matrix,
    create_adjudication_template,
    sha256_file,
    validate_adjudications,
    validate_annotations,
    validate_sources,
    write_jsonl,
)


def sources():
    return [
        {
            "id": "m2_001",
            "domain": "algebra",
            "topic": "groups",
            "theorem": "If x = e, then x is the identity.",
            "assumptions": ["G is a group."],
            "flawed_proof_steps": ["Assume x = e.", "Thus x is the identity."],
        },
        {
            "id": "m2_002",
            "domain": "algebra",
            "topic": "fields",
            "theorem": "For a nonzero field element a, a/a = 1.",
            "assumptions": ["F is a field.", "a is nonzero."],
            "flawed_proof_steps": ["Because a is nonzero, a has an inverse.", "Therefore a/a = 1."],
        },
    ]


def m2_sources():
    return [
        {
            "schema_version": "m2-source-0.1",
            "proof_id": "m2-001",
            "theorem_version": 1,
            "domain": "elementary_algebra",
            "theorem": "A theorem.",
            "assumptions": ["An assumption."],
            "proof_steps": [{"node_id": "n1", "text": "A proof step."}],
        }
    ]


def annotations(annotator="person_a"):
    return [
        {
            "schema_version": "m2.1",
            "sample_id": "m2_001",
            "annotator_id": annotator,
            "validity_status": "valid",
            "first_gap_step": None,
            "first_invalid_step": None,
            "error_type": "no_error",
            "counterexample_status": "not_applicable",
            "minimal_repair": None,
            "notes": "",
        },
        {
            "schema_version": "m2.1",
            "sample_id": "m2_002",
            "annotator_id": annotator,
            "validity_status": "valid",
            "first_gap_step": None,
            "first_invalid_step": None,
            "error_type": "no_error",
            "counterexample_status": "not_applicable",
            "minimal_repair": None,
            "notes": "",
        },
    ]


class M2ValidationTests(unittest.TestCase):
    def test_valid_sources_and_annotations(self):
        validate_sources(sources(), expected_count=2)
        validate_annotations(annotations(), sources(), expected_annotator="person_a")

    def test_official_m2_source_shape_is_accepted(self):
        validate_sources(m2_sources(), expected_count=1)

    def test_duplicate_m2_node_id_is_rejected(self):
        rows = m2_sources()
        rows[0]["proof_steps"].append({"node_id": "n1", "text": "Another step."})
        with self.assertRaisesRegex(M2ValidationError, "duplicate node_id"):
            validate_sources(rows)

    def test_duplicate_source_id_is_rejected(self):
        rows = sources()
        rows[1]["id"] = rows[0]["id"]
        with self.assertRaisesRegex(M2ValidationError, "duplicate proof_id/id"):
            validate_sources(rows)

    def test_annotation_sample_mismatch_is_rejected(self):
        rows = annotations()[:-1]
        with self.assertRaisesRegex(M2ValidationError, "sample set mismatch"):
            validate_annotations(rows, sources())

    def test_invalid_step_out_of_range_is_rejected(self):
        rows = annotations()
        rows[0].update(validity_status="invalid", error_type="algebraic_invalidity", first_invalid_step=3)
        with self.assertRaisesRegex(M2ValidationError, "first_invalid_step"):
            validate_annotations(rows, sources())

    def test_invalid_label_is_rejected(self):
        rows = annotations()
        rows[0]["error_type"] = "confident_guess"
        with self.assertRaisesRegex(M2ValidationError, "invalid error_type"):
            validate_annotations(rows, sources())

    def test_validity_and_location_conflict_is_rejected(self):
        rows = annotations()
        rows[0]["first_invalid_step"] = 1
        with self.assertRaisesRegex(M2ValidationError, "valid annotations"):
            validate_annotations(rows, sources())

    def test_write_jsonl_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "rows.jsonl"
            write_jsonl(destination, [{"b": 2, "a": 1}])
            self.assertEqual(destination.read_text(encoding="utf-8"), '{"a": 1, "b": 2}\n')
            self.assertEqual(
                sha256_file(destination),
                "fdcde7d03783fce2e97b7a775ef45379b3ecab4cab4ddb1156e65057b811f44c",
            )


class M2AgreementTests(unittest.TestCase):
    def test_identical_annotations_have_full_agreement(self):
        report, disagreements = build_agreement_report(annotations("person_a"), annotations("person_b"))
        self.assertEqual(report["disagreement_count"], 0)
        self.assertEqual(report["fields"]["error_type"]["exact_agreement"], 1.0)
        self.assertEqual(disagreements, [])

    def test_same_annotator_cannot_be_compared_with_itself(self):
        with self.assertRaisesRegex(M2ValidationError, "annotator_id values must differ"):
            build_agreement_report(annotations("same_person"), annotations("same_person"))

    def test_each_side_must_have_one_annotator(self):
        person_a = annotations("person_a")
        person_a[1]["annotator_id"] = "another_person"
        with self.assertRaisesRegex(M2ValidationError, "exactly one annotator_id"):
            build_agreement_report(person_a, annotations("person_b"))

    def test_disagreement_is_field_level(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[1].update(
            validity_status="invalid",
            first_invalid_step=2,
            error_type="algebraic_invalidity",
            counterexample_status="valid",
            minimal_repair="Replace step 2.",
        )
        report, disagreements = build_agreement_report(person_a, person_b)
        self.assertEqual(report["disagreement_count"], 5)
        self.assertEqual({row["field"] for row in disagreements}, {
            "validity_status", "first_invalid_step", "error_type", "counterexample_status", "minimal_repair"
        })
        matrix = report["fields"]["validity_status"]["confusion_matrix"]
        self.assertIn(
            {"person_a_value": "valid", "person_b_value": "invalid", "count": 1},
            matrix,
        )
        self.assertFalse(report["fields"]["minimal_repair"]["cohen_kappa_applicable"])
        self.assertIsNone(report["fields"]["minimal_repair"]["cohen_kappa"])

    def test_kappa_handles_constant_agreement(self):
        self.assertEqual(cohen_kappa([None, None], [None, None]), 1.0)

    def test_confusion_matrix_supports_null_labels(self):
        self.assertEqual(
            confusion_matrix([None, 1, None], [None, 2, 1]),
            [
                {"person_a_value": 1, "person_b_value": 2, "count": 1},
                {"person_a_value": None, "person_b_value": 1, "count": 1},
                {"person_a_value": None, "person_b_value": None, "count": 1},
            ],
        )

    def test_adjudication_template_is_incomplete_by_design(self):
        _, disagreements = build_agreement_report(
            annotations("person_a"),
            [
                {**annotations("person_b")[0], "error_type": "theorem_misuse"},
                annotations("person_b")[1],
            ],
        )
        template = create_adjudication_template(disagreements)
        self.assertEqual(template[0]["final_value"], None)
        with self.assertRaisesRegex(M2ValidationError, "invalid final error_type"):
            validate_adjudications(template, disagreements)

    def test_adjudication_rejects_invalid_final_enum_early(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[0]["error_type"] = "theorem_misuse"
        _, disagreements = build_agreement_report(person_a, person_b)
        row = {
            **disagreements[0],
            "final_value": "invented_label",
            "disagreement_type": "label_definition",
            "evidence": ["Frozen guideline."],
            "rationale": "The value must use the frozen enum.",
            "adjudicators": ["person_a", "person_b"],
        }
        with self.assertRaisesRegex(M2ValidationError, "invalid final error_type"):
            validate_adjudications([row], disagreements)

    def test_adjudication_is_bound_to_current_compared_values(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[0]["error_type"] = "theorem_misuse"
        _, disagreements = build_agreement_report(person_a, person_b)
        stale = {
            **disagreements[0],
            "person_a_value": "outdated_a",
            "person_b_value": "outdated_b",
            "final_value": "no_error",
            "disagreement_type": "label_definition",
            "evidence": ["Frozen guideline."],
            "rationale": "Resolve from current evidence only.",
            "adjudicators": ["person_a", "person_b"],
        }
        with self.assertRaisesRegex(M2ValidationError, "compared values do not match"):
            validate_adjudications([stale], disagreements)

    def test_gold_manifest_binds_all_inputs_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, content in enumerate((b"source", b"a", b"b", b"decisions", b"gold")):
                path = Path(tmp) / f"file-{index}"
                path.write_bytes(content)
                paths.append(path)
            manifest = build_gold_manifest(*paths, row_count=2)
            self.assertEqual(manifest["row_count"], 2)
            self.assertEqual(manifest["output_sha256"], sha256_file(paths[-1]))
            self.assertEqual(manifest["inputs"]["adjudications_sha256"], sha256_file(paths[3]))

    def test_gold_requires_every_disagreement_to_be_adjudicated(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[0].update(validity_status="invalid", first_invalid_step=1, error_type="theorem_misuse")
        with self.assertRaisesRegex(M2ValidationError, "coverage mismatch"):
            build_gold(sources(), person_a, person_b, [])

    def test_gold_uses_explicit_adjudication(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[0].update(validity_status="invalid", first_invalid_step=1, error_type="theorem_misuse")
        _, disagreements = build_agreement_report(person_a, person_b)
        final_values = {
            "validity_status": "valid",
            "first_invalid_step": None,
            "error_type": "no_error",
        }
        decisions = [
            {
                **row,
                "final_value": final_values[row["field"]],
                "disagreement_type": "mathematical_judgment",
                "evidence": ["Definition of identity."],
                "rationale": "Both reviewers accepted the direct definition after discussion.",
                "adjudicators": ["person_a", "person_b"],
            }
            for row in disagreements
        ]
        validate_adjudications(decisions, disagreements)
        gold = build_gold(sources(), person_a, person_b, decisions)
        self.assertEqual(gold[0]["gold_validity_status"], "valid")
        self.assertIsNone(gold[0]["gold_first_invalid_step"])
        self.assertEqual(gold[0]["gold_error_type"], "no_error")

    def test_gold_rejects_an_invalid_adjudicated_value(self):
        person_a = annotations("person_a")
        person_b = annotations("person_b")
        person_b[0]["error_type"] = "theorem_misuse"
        _, disagreements = build_agreement_report(person_a, person_b)
        decisions = [
            {
                **disagreements[0],
                "final_value": "not_a_real_label",
                "disagreement_type": "label_definition",
                "evidence": ["Frozen annotation guideline."],
                "rationale": "Test invalid final value.",
                "adjudicators": ["person_a", "person_b"],
            }
        ]
        with self.assertRaisesRegex(M2ValidationError, "invalid final error_type"):
            build_gold(sources(), person_a, person_b, decisions)


if __name__ == "__main__":
    unittest.main()
