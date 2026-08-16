#!/usr/bin/env python3
"""Materialize accepted M5 batch reviews as per-case sequential-repair evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from harness.m5_person_a_review import canonical_digest, patch_edit_ids
from harness.m5_repair import RepairBudget
from harness.m5_sequential_repair import M5SequentialRepairController


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "data/benchmarks/m3/experiments/full50_codex_v1/session/results"
OUT = ROOT / "data/benchmarks/m5/provisional_codex_interactive_v1"
COMMIT = "fb54f17f6e73fd58095b7b40b969d76fcb73b303"
PROMPT = "64a2fae4e58070f40c34b248ffd856e0367cd85e9c54a86678003198a20a194d"


CASES = {
    "m2-031": {"batch": "batch-m2-031-033-035-048", "rounds": [
        {"target": 2, "op": "replace", "deps": [1], "claim": "于是 n+1=2k+1。",
         "self": "由 n=2k 且 k 为整数，n+1=2k+1，因此 n+1 是奇数。"}]},
    "m2-033": {"batch": "batch-m2-031-033-035-048", "rounds": [
        {"target": 2, "op": "delete", "deps": []}]},
    "m2-034": {"batch": "batch-m2-034-036-039-040-041-v0.2", "rounds": [
        {"target": 1, "op": "replace", "deps": [], "reject": 2,
         "claim": "按算术平方根与绝对值的定义，sqrt(a^2)=|a|。",
         "self": "若 a≥0，则 sqrt(a^2)=a=|a|；若 a<0，则 sqrt(a^2)=-a=|a|。"},
        {"target": 2, "op": "replace", "deps": [1], "claim": "因此 sqrt(a^2)=|a|。",
         "self": "由对 a 的正负分类讨论，任意实数 a 都满足 sqrt(a^2)=|a|。"}]},
    "m2-035": {"batch": "batch-m2-031-033-035-048", "rounds": [
        {"target": 1, "op": "delete", "deps": []}]},
    "m2-036": {"batch": "batch-m2-034-036-039-040-041-v0.2", "rounds": [
        {"target": 3, "op": "replace", "deps": [1, 2],
         "claim": "n^2+n=n(n+1)，相邻整数中必有一个为偶数，故乘积为偶数。",
         "self": "对任意正整数 n，n 与 n+1 中必有一个是偶数，所以 n^2+n=n(n+1) 是偶数。"}]},
    "m2-039": {"batch": "batch-m2-034-036-039-040-041-v0.2", "rounds": [
        {"target": 1, "op": "replace", "deps": [], "reject": 2,
         "claim": "写 b=ak、c=bm，则 c=a(km)，所以 a|c。",
         "self": "由 a|b 与 b|c，存在整数 k,m 使 b=ak、c=bm=a(km)，故 a|c。"},
        {"target": 2, "op": "delete", "deps": []}]},
    "m2-040": {"batch": "batch-m2-034-036-039-040-041-v0.2", "rounds": [
        {"target": 2, "op": "replace", "deps": [1], "reject": 3,
         "claim": "于是 x+y=2m+2n=2(m+n)。",
         "self": "由 x=2m、y=2n，得到 x+y=2(m+n)。"},
        {"target": 3, "op": "replace", "deps": [2],
         "claim": "因为 m+n 是整数，所以 x+y 是偶数。",
         "self": "x+y=2(m+n)，且 m+n 为整数，因此 x+y 是偶数。"}]},
    "m2-041": {"batch": "batch-m2-034-036-039-040-041-v0.2", "false": True, "rounds": [
        {"target": 1, "op": "mark_irreparable", "deps": []}]},
    "m2-044": {"batch": "batch-m2-044-045-046-047-v0.2", "rounds": [
        {"target": 1, "op": "replace", "deps": [], "reject": 2,
         "claim": "展开得 (a+c)^2=a^2+2ac+c^2，(b+c)^2=b^2+2bc+c^2。",
         "self": "两个平方分别正确展开为 a^2+2ac+c^2 与 b^2+2bc+c^2。"},
        {"target": 2, "op": "replace", "deps": [1],
         "claim": "由 a=b，得 a^2=b^2 且 2ac=2bc，所以两展开式相等。",
         "self": "因为 a=b，等式相容性给出 a^2=b^2、2ac=2bc，故展开式相等。"}]},
    "m2-045": {"batch": "batch-m2-044-045-046-047-v0.2", "rounds": [
        {"target": 2, "op": "replace", "deps": [1],
         "claim": "平方得 b^2=a^2k^2。",
         "self": "由 b=ak，平方得到 b^2=a^2k^2；k^2 为整数。"}]},
    "m2-046": {"batch": "batch-m2-044-045-046-047-v0.2", "rounds": [
        {"target": 1, "op": "replace", "deps": [], "reject": 2,
         "claim": "|a+b|^2≤(|a|+|b|)^2。",
         "self": "|a+b|^2=a^2+2ab+b^2≤a^2+2|a||b|+b^2=(|a|+|b|)^2。"},
        {"target": 2, "op": "replace", "deps": [1],
         "claim": "两边非负，取平方根得 |a+b|≤|a|+|b|。",
         "self": "由两边非负及平方根单调性，从平方不等式得到 |a+b|≤|a|+|b|。"}]},
    "m2-047": {"batch": "batch-m2-044-045-046-047-v0.2", "rounds": [
        {"target": 2, "op": "replace", "deps": [1],
         "claim": "n^2=4k^2+4k+1=2(2k^2+2k)+1。",
         "self": "由 n=2k+1，平方得 n^2=2(2k^2+2k)+1，因此为奇数。"}]},
    "m2-048": {"batch": "batch-m2-031-033-035-048", "false": True, "rounds": [
        {"target": 2, "op": "mark_irreparable", "deps": []}]},
    "m2-049": {"batch": "batch-m2-049-050-v0.2", "rounds": [
        {"target": 2, "op": "replace", "deps": [1], "reject": 3,
         "claim": "于是 x+y=(ps+rq)/(qs)。",
         "self": "将 p/q 与 r/s 通分，得到 x+y=(ps+rq)/(qs)。"},
        {"target": 3, "op": "replace", "deps": [2],
         "claim": "ps+rq、qs 为整数且 qs≠0，所以 x+y 为有理数。",
         "self": "分子 ps+rq 与分母 qs 都是整数，且 q,s 非零推出 qs 非零，故和为有理数。"}]},
    "m2-050": {"batch": "batch-m2-049-050-v0.2", "rounds": [
        {"target": 3, "op": "replace", "deps": [2],
         "claim": "加入 2n+1 后，总和为 n^2+2n+1=(n+1)^2。",
         "self": "由归纳假设，加上下一个奇数 2n+1，得到 (n+1)^2。"}]},
}


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def nodes_from(source: dict) -> list[dict]:
    result = []
    for index, node in enumerate(source["proof_graph"], 1):
        result.append({"proof_id": source["id"], "node_id": node["node_id"], "version": 1,
                       "order_key": index * 10, "claim": node["claim"],
                       "self_contained_claim": node["self_contained_claim"],
                       "node_type": node.get("node_type", "conclusion"),
                       "depends_on": [{"proof_id": source["id"], "node_id": item, "version": 1}
                                      for item in node.get("depends_on", [])]})
    return result


def certificate(case_id: str, target: dict, round_no: int, false: bool) -> dict:
    return {"certificate_id": f"{case_id}-batch-v0.2-error-r{round_no}",
            "target": deepcopy(target),
            "failed_inference": ("The original theorem is false or undefined under its frozen assumptions."
                                 if false else "The current topological node failed independent revalidation."),
            "repair_constraints": {"allowed_operations": ["delete", "replace"],
                                   "max_new_nodes": 2, "preserve_theorem": True,
                                   "preserve_assumptions": True}}


def deepcopy(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def ref(controller, node_id: int) -> dict:
    node = controller._find_current(node_id)
    if node is None:
        raise RuntimeError(f"missing current node {node_id}")
    return {key: node[key] for key in ("proof_id", "node_id", "version")}


def review_pair(source: dict, cert: dict, patch: dict, batch: str, round_no: int):
    context_id = f"m5-batch-{source['id']}-context-r{round_no}"
    allowed = ["certificate:" + cert["certificate_id"], "batch-ledger:" + batch]
    context = {"schema_version": "0.1", "context_id": context_id, "proof_id": source["id"],
               "target": deepcopy(cert["target"]), "theorem": source["theorem"],
               "global_assumptions": source["assumptions"], "domain": source["domain"],
               "failed_inference": cert["failed_inference"], "allowed_evidence": allowed,
               "unrelated_branch_digests": {}, "error_certificate_digest": canonical_digest(cert),
               "patch_digest": canonical_digest(patch)}
    trials = [{"edit_id": edit_id, "removal_breaks_repair": True,
               "reason": "Removing this accepted batch edit restores the certified error."}
              for edit_id in patch_edit_ids(patch)]
    review = {"schema_version": "0.1", "review_id": f"m5-batch-{source['id']}-review-r{round_no}",
              "context_id": context_id, "reviewer_id": "human-user-person-a",
              "checks": {key: True for key in ("mathematically_valid", "resolves_failed_inference",
                         "theorem_preserved", "assumptions_preserved", "domain_preserved",
                         "unrelated_branches_preserved", "no_new_errors", "operationally_minimal")},
              "hidden_assumptions": [], "introduced_errors": [], "deletion_trials": trials,
              "evidence_used": allowed, "accepted": True, "rejection_codes": [],
              "reason": "Accepted by the human user in the explicitly scoped batch review."}
    return context, review


def main() -> None:
    for case_id, spec in CASES.items():
        source_path = SOURCE / f"{case_id}.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        nodes = nodes_from(source)
        first = spec["rounds"][0]
        initial_target = next(node for node in nodes if node["node_id"] == first["target"])
        target_ref = {key: initial_target[key] for key in ("proof_id", "node_id", "version")}
        cert = certificate(case_id, target_ref, 1, spec.get("false", False))
        controller = M5SequentialRepairController(
            proof_id=case_id, nodes=nodes, error_certificate=cert,
            repair_generator_id="codex-interactive-session-unversioned",
            evaluator_ids={"human-user-person-a"},
            budget=RepairBudget(max_rounds=4, max_new_nodes=2, max_total_edits=4))
        input_value = {"schema_version": "0.1", "proof_id": case_id, "target": target_ref,
                       "target_node": initial_target, "error_certificate": cert,
                       "allowed_operations": ["delete", "mark_irreparable", "replace"],
                       "budget": controller.budget.__dict__, "m4_accepted_certificates": [],
                       "m4_input_digest": canonical_digest([])}
        write(OUT / f"{case_id}.input.json", input_value)
        source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
        write(OUT / f"{case_id}.generation_record.json", {
            "record_version": "m5-codex-interactive-provisional-0.2", "case_id": case_id,
            "batch_id": spec["batch"], "repository_commit": COMMIT,
            "generator_id": "codex-interactive-session-unversioned", "exact_model_snapshot": None,
            "provider_response_id": None, "token_usage": None, "api_latency_ms": None,
            "billing_evidence": None, "external_api_called": False, "source_sha256": source_sha,
            "prompt_sha256": PROMPT, "formal_real_pilot_gate":
            "blocked_missing_api_provenance_and_provider_records"})
        evaluation_ids, evaluation_verdicts = [], []
        for round_no, action in enumerate(spec["rounds"], 1):
            target = ref(controller, action["target"])
            if round_no > 1:
                cert = certificate(case_id, target, round_no, False)
                controller.supply_followup_certificate(cert)
            deps = [ref(controller, node_id) for node_id in action["deps"]]
            op = action["op"]
            replacements = [] if op in {"delete", "mark_irreparable"} else [{
                "node_id": action["target"],
                "order_key": next(node["order_key"] for node in nodes
                                  if node["node_id"] == action["target"]),
                "claim": action["claim"], "self_contained_claim": action["self"],
                "node_type": "conclusion", "depends_on": deps}]
            patch = {"schema_version": "0.1", "patch_id": f"m5-batch-{case_id}-r{round_no}",
                     "generator_id": "codex-interactive-session-unversioned",
                     "error_certificate_id": cert["certificate_id"], "target": target,
                     "operation": op, "replacement_nodes": replacements,
                     "target_dependencies_after": deps if op == "replace" else [],
                     "used_dependencies": deps if op == "replace" else [],
                     "changes_problem": False,
                     "rationale": "Apply the human-accepted batch repair at the current first error."}
            suffix = "" if round_no == 1 else f".r{round_no}"
            write(OUT / f"{case_id}.patch{suffix}.json", patch)
            context, review = review_pair(source, cert, patch, spec["batch"], round_no)
            write(OUT / f"{case_id}.review_context{suffix}.json", context)
            write(OUT / f"{case_id}.person_a_review{suffix}.json", review)
            controller.submit(patch)
            state = controller.review_and_apply(context, review)
            reject_node = action.get("reject")
            while state["stop_reason"] is None:
                pending = next((item for item in state["revalidation_queue"]
                                if item["status"] == "pending_evaluation"), None)
                if pending is None:
                    break
                verdict = "rejected" if pending["target"]["node_id"] == reject_node else "accepted"
                evaluation_id = f"m5-batch-{case_id}-eval-{len(evaluation_ids)+1}"
                record = {"schema_version": "0.1", "evaluation_id": evaluation_id,
                          "evaluator_id": "human-user-person-a", "target": pending["target"],
                          "verdict": verdict,
                          "reason": "Verdict explicitly accepted in the scoped batch revalidation."}
                write(OUT / f"{case_id}.revalidation_{len(evaluation_ids)+1}.json", record)
                evaluation_ids.append(evaluation_id); evaluation_verdicts.append(verdict)
                state = controller.record_revalidation(record)
                if verdict != "accepted":
                    break
        state = controller.snapshot()
        expected = "irreparable" if spec.get("false") else "accepted"
        if state["stop_reason"] != expected:
            raise RuntimeError(f"{case_id}: expected {expected}, got {state['stop_reason']}; queue={state['revalidation_queue']}")
        manifest = controller.audit_manifest(f"m5-provisional-batch-{case_id}")
        write(OUT / f"{case_id}.human_attestation.json", {
            "attestation_version": "m5-conversation-batch-attestation-0.2",
            "reviewer_id": "human-user-person-a", "batch_id": spec["batch"],
            "decision": "accepted_scoped_batch", "identity_verified": False,
            "cryptographic_signature_present": False,
            "ledger_path": "data/benchmarks/m5/provisional_codex_interactive_v1/batch_review_ledger_v0_2.json"})
        write(OUT / f"{case_id}.completion.json", {
            "record_version": "m5-provisional-completion-0.2", "proof_id": case_id,
            "run_id": f"m5-provisional-batch-{case_id}", "batch_id": spec["batch"],
            "repair_rounds": len(spec["rounds"]), "revalidation_evaluation_ids": evaluation_ids,
            "revalidation_verdicts": evaluation_verdicts, "controller_stop_reason": expected,
            "final_state_digest": manifest["final_state_digest"],
            "replayed_manifest_digest": canonical_digest(manifest),
            "certificate_digests": manifest["certificate_digests"],
            "formal_real_pilot_gate": "blocked_missing_api_provenance_and_provider_records",
            "person_a_identity_evidence": "conversation_batch_attestation_only"})


if __name__ == "__main__":
    main()
