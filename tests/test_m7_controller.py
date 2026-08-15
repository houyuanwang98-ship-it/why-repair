import hashlib
import json
import unittest
from pathlib import Path

from harness.m6_experiments import FIXTURE_DIGEST, METHOD_IDS, build_experiment_config
from harness.m7_controller import (
    build_assignments, build_blind_review_plan, build_controller_manifest, freeze_artifacts,
    select_replay_sample, validate_aggregate_table, validate_controller_manifest,
    validate_run_integrity,
)
from harness.m7_person_b import M7PersonBError

ROOT = Path(__file__).resolve().parents[1]


def configs(model, *, role_mode="same_model"):
    return [build_experiment_config(
        method, model_id=model, prompt_digest=FIXTURE_DIGEST, dataset_digest=FIXTURE_DIGEST,
        theorem_bank_digest=FIXTURE_DIGEST, tool_digest=FIXTURE_DIGEST,
        token_limit=4000, call_limit=4, timeout_seconds=60, role_mode=role_mode,
    ) for method in METHOD_IDS]


def manifest():
    person_a = hashlib.sha256((ROOT / "data/benchmarks/m7/person_a_protocol_candidate_v0_1.json").read_bytes()).hexdigest()
    person_b = hashlib.sha256((ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json").read_bytes()).hexdigest()
    return build_controller_manifest(
        config_families={
            "same-model": configs("a"),
            "different-models": configs({"generator": "a", "critic": "b"},
                                        role_mode="different_models"),
        },
        case_ids=["c1", "c2"], candidate_digest=FIXTURE_DIGEST, gold_digest=FIXTURE_DIGEST,
        artifacts=freeze_artifacts(ROOT, ["harness/m7_controller.py"]),
        person_a_manifest_digest=person_a, person_b_manifest_digest=person_b,
        replay_seed=17, root=ROOT)


def ledger_and_results(item):
    ledger, results = [], []
    for index, assignment in enumerate(build_assignments(item, root=ROOT)):
        status = "timeout" if index == 0 else "succeeded"
        run = {"case_id": assignment["case_id"], "experiment_id": assignment["experiment_id"],
               "run_id": f"run-{index}", "status": status, "terminal": True, "tokens": 10,
               "model_calls": 1, "wall_ms": 5, "raw_output_sha256": FIXTURE_DIGEST}
        ledger.append(run)
        results.append({key: run[key] for key in ("case_id", "experiment_id", "run_id", "status", "raw_output_sha256")} |
                       {"score_input_sha256": FIXTURE_DIGEST})
    return ledger, results


class M7ControllerTest(unittest.TestCase):
    def test_candidate_manifest_schema_shape_hashes_and_closed_gate(self):
        item = json.loads((ROOT / "data/benchmarks/m7/controller_engineering_candidate_v0_1.json").read_text())
        schema = json.loads((ROOT / "schemas/m7_controller_candidate_manifest_v0_1.schema.json").read_text())
        self.assertEqual(set(schema["required"]), set(item))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(item["m7_execution_allowed"])
        self.assertFalse(item["upstream"]["m7_entry_allowed"])
        self.assertTrue(all(item["capabilities"].values()))
        for relative, digest in item["artifacts"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        self.assertEqual(item["upstream"]["person_a_manifest_sha256"], hashlib.sha256(
            (ROOT / "data/benchmarks/m7/person_a_protocol_candidate_v0_1.json").read_bytes()).hexdigest())
        self.assertEqual(item["upstream"]["person_b_manifest_sha256"], hashlib.sha256(
            (ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json").read_bytes()).hexdigest())

    def test_manifest_binds_two_complete_families_and_cases(self):
        item = manifest()
        self.assertEqual(item, validate_controller_manifest(item, root=ROOT))
        self.assertEqual(36, len(build_assignments(item, root=ROOT)))
        item["case_ids"].append("tampered")
        with self.assertRaisesRegex(M7PersonBError, "mutated"):
            validate_controller_manifest(item, root=ROOT)
        malformed = manifest()
        malformed["upstream"] = {}
        with self.assertRaisesRegex(M7PersonBError, "upstream binding"):
            validate_controller_manifest(malformed, root=ROOT)
        with self.assertRaisesRegex(M7PersonBError, "artifact keys"):
            build_controller_manifest(
                config_families={
                    "same": configs("a"),
                    "different": configs({"generator": "a", "critic": "b"},
                                         role_mode="different_models"),
                }, case_ids=["c1"],
                candidate_digest=FIXTURE_DIGEST, gold_digest=FIXTURE_DIGEST,
                artifacts={".": FIXTURE_DIGEST}, person_a_manifest_digest=FIXTURE_DIGEST,
                person_b_manifest_digest=FIXTURE_DIGEST, replay_seed=1, root=ROOT)
        with self.assertRaisesRegex(M7PersonBError, "same_model and one different_models"):
            build_controller_manifest(
                config_families={"same-a": configs("a"), "same-b": configs("b")},
                case_ids=["c1"], candidate_digest=FIXTURE_DIGEST, gold_digest=FIXTURE_DIGEST,
                artifacts={"fixture": FIXTURE_DIGEST}, person_a_manifest_digest=FIXTURE_DIGEST,
                person_b_manifest_digest=FIXTURE_DIGEST, replay_seed=1, root=ROOT)

    def test_formal_manifest_and_self_reported_gate_fail_closed(self):
        kwargs = dict(config_families={
                          "same": configs("a"),
                          "different": configs({"generator": "a", "critic": "b"},
                                               role_mode="different_models"),
                      }, case_ids=["c1"],
                      candidate_digest=FIXTURE_DIGEST, gold_digest=FIXTURE_DIGEST,
                      artifacts={"fixture": FIXTURE_DIGEST}, person_a_manifest_digest=FIXTURE_DIGEST,
                      person_b_manifest_digest=FIXTURE_DIGEST, replay_seed=1, root=ROOT)
        with self.assertRaisesRegex(M7PersonBError, "closed M7"):
            build_controller_manifest(**kwargs, m7_entry_allowed=True)
        with self.assertRaisesRegex(M7PersonBError, "detached signatures"):
            build_controller_manifest(**kwargs, fixture_only=False, m7_entry_allowed=True)

    def test_integrity_binds_every_result_to_terminal_bytes_and_status(self):
        item = manifest()
        ledger, results = ledger_and_results(item)
        report = validate_run_integrity(item, ledger, results, root=ROOT)
        self.assertEqual(36, report["assignment_count"])
        self.assertTrue(report["complete"])
        self.assertEqual(report["result_digest"],
                         validate_run_integrity(item, list(reversed(ledger)),
                                                list(reversed(results)), root=ROOT)["result_digest"])
        results[0]["status"] = "succeeded"
        with self.assertRaisesRegex(M7PersonBError, "disagrees"):
            validate_run_integrity(item, ledger, results, root=ROOT)
        results[0]["status"] = "timeout"
        with self.assertRaisesRegex(M7PersonBError, "one result"):
            validate_run_integrity(item, ledger, results[1:], root=ROOT)
        extra = dict(ledger[0], experiment_id="unknown", run_id="extra")
        with self.assertRaisesRegex(M7PersonBError, "exact frozen assignment"):
            validate_run_integrity(item, ledger + [extra], results, root=ROOT)
        over_budget = [dict(row) for row in ledger]
        over_budget[0]["tokens"] = 4001
        with self.assertRaisesRegex(M7PersonBError, "frozen per-sample budget"):
            validate_run_integrity(item, over_budget, results, root=ROOT)
        cross_family_collision = [dict(row) for row in ledger]
        collision_results = [dict(row) for row in results]
        cross_family_collision[19]["run_id"] = cross_family_collision[1]["run_id"]
        collision_results[19]["run_id"] = collision_results[1]["run_id"]
        with self.assertRaisesRegex(M7PersonBError, "globally unique"):
            validate_run_integrity(item, cross_family_collision, collision_results, root=ROOT)

    def test_aggregate_must_reproduce_complete_ledger(self):
        item = manifest()
        ledger, _ = ledger_and_results(item)
        table = []
        for family, family_configs in item["config_families"].items():
            for config in family_configs:
                subset = [row for row in ledger if row["experiment_id"] == config["experiment_id"]]
                successes = sum(row["status"] == "succeeded" for row in subset)
                table.append({"family_id": family, "experiment_id": config["experiment_id"],
                              "sample_count": 2, "success_count": successes,
                              "failure_count": 2 - successes, "tokens": 20,
                              "model_calls": 2, "wall_ms": 10})
        self.assertEqual(table, validate_aggregate_table(item, ledger, table, root=ROOT))
        table[0]["failure_count"] = 0
        with self.assertRaisesRegex(M7PersonBError, "does not reproduce"):
            validate_aggregate_table(item, ledger, table, root=ROOT)
        table[0]["failure_count"] = 1
        with self.assertRaisesRegex(M7PersonBError, "exact frozen assignment"):
            validate_aggregate_table(item, ledger[:-1], table, root=ROOT)
        over_budget = [dict(row) for row in ledger]
        over_budget[0]["wall_ms"] = 60001
        with self.assertRaisesRegex(M7PersonBError, "frozen per-sample budget"):
            validate_aggregate_table(item, over_budget, table, root=ROOT)

    def test_replay_selection_is_deterministic_and_success_only(self):
        item = manifest()
        ledger, _ = ledger_and_results(item)
        first = select_replay_sample(item, ledger, 5, root=ROOT)
        self.assertEqual(first, select_replay_sample(item, ledger, 5, root=ROOT))
        self.assertNotIn("run-0", first)
        with self.assertRaisesRegex(M7PersonBError, "exceeds"):
            select_replay_sample(item, ledger, 100, root=ROOT)
        forged = dict(ledger[0], experiment_id="unknown", run_id="forged", status="succeeded")
        with self.assertRaisesRegex(M7PersonBError, "exact frozen assignment"):
            select_replay_sample(item, ledger + [forged], 1, root=ROOT)
        duplicate_run = [dict(row) for row in ledger]
        duplicate_run[1]["run_id"] = duplicate_run[0]["run_id"]
        with self.assertRaisesRegex(M7PersonBError, "run_id"):
            select_replay_sample(item, duplicate_run, 1, root=ROOT)

    def test_manifest_rejects_stale_or_fabricated_artifact_bytes(self):
        item = manifest()
        item["artifacts"]["harness/m7_controller.py"] = FIXTURE_DIGEST
        with self.assertRaisesRegex(M7PersonBError, "artifact bytes"):
            validate_controller_manifest(item, root=ROOT)
        kwargs = dict(config_families={
                          "same": configs("a"),
                          "different": configs({"generator": "a", "critic": "b"}, role_mode="different_models"),
                      }, case_ids=["c1"], candidate_digest=FIXTURE_DIGEST, gold_digest=FIXTURE_DIGEST,
                      artifacts={"does/not/exist": FIXTURE_DIGEST},
                      person_a_manifest_digest=hashlib.sha256((ROOT / "data/benchmarks/m7/person_a_protocol_candidate_v0_1.json").read_bytes()).hexdigest(),
                      person_b_manifest_digest=hashlib.sha256((ROOT / "data/benchmarks/m7/person_b_engineering_candidate_v0_1.json").read_bytes()).hexdigest(),
                      replay_seed=1, root=ROOT)
        with self.assertRaisesRegex(M7PersonBError, "not a file"):
            build_controller_manifest(**kwargs)

    def test_blind_review_plan_keeps_all_critical_and_anonymizes_configs(self):
        rows = []
        for case in range(25):
            for experiment in ("real-method-a", "real-method-b"):
                rows.append({"case_id": f"c{case:02d}", "experiment_id": experiment,
                             "false_accept": case == 0, "invalid_global_counterexample": False,
                             "false_repair": case == 1, "correct_verdict": case >= 2,
                             "verified_repair_success": False, "undetermined": False,
                             "infrastructure_failure": False, "review_payload_sha256": FIXTURE_DIGEST})
        first = build_blind_review_plan(rows, seed=71)
        second = build_blind_review_plan(list(reversed(rows)), seed=71)
        self.assertEqual(first["public_plan_sha256"], second["public_plan_sha256"])
        public = json.dumps(first["public_plan"], sort_keys=True)
        self.assertNotIn("real-method-a", public)
        self.assertNotIn("real-method-b", public)
        reviewed = {(row["case_id"], row["anonymized_config_id"])
                    for row in first["public_plan"]["review_rows"]}
        self.assertTrue(any(case == "c00" for case, _ in reviewed))
        self.assertTrue(any(case == "c01" for case, _ in reviewed))
        correct_frames = [frame for frame in first["public_plan"]["frames"]
                          if frame["category"] == "correct_verdict"]
        self.assertTrue(all(len(frame["selected"]) == 20 for frame in correct_frames))


if __name__ == "__main__":
    unittest.main()
