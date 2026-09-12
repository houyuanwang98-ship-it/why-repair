#!/usr/bin/env python3
"""Controlled local-edit stress study; not autonomous repair or a natural-proof benchmark."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import argparse
import fcntl
import json
from pathlib import Path
import queue
import signal
import sys
import threading
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.workflow_v2.app_server import PersistentServer
from harness.workflow_v2.contracts import (digest, read, require, write_once, implementation_digest,
    snapshot_implementation, judge_input, validate_judgment, strict_accept, problem_context)
from harness.workflow_v2.controller import ProofState, audit_pass
from harness.workflow_v2.experiment import evidence_files, file_digest
from harness.workflow_v2.runtime import Calls
from harness.workflow_v2.scheduler import atomic_json

STRATEGIES = ("dependency_closure", "all_nodes", "retain_stale_for_experiment")


def fixtures():
    rows = []
    for a,b in [(2,3), (3,4), (4,7)]:
        for delta in (0,1):
            s = a+b
            texts = [f"Define t=a+b={s}.", f"Then t^2={s*s}.",
                     f"a^2={a*a}.", f"b^2={b*b}.", f"Therefore a^2+b^2={a*a+b*b}."]
            graph = {"ambiguities": [], "nodes": [{"node_id": f"n{i+1}", "text": t, "claim": t,
                "scope": [], "depends_on": deps, "goal_refs": ["main"] if i==4 else []}
                for i,(t,deps) in enumerate(zip(texts, [[], ["n1"], [], [], ["n3","n4"]]))]}
            problem = {"theorem": f"Prove a^2+b^2={a*a+b*b}.", "assumptions": [f"a={a}",f"b={b}"],
                       "domain": "integers", "explicit_subgoals": [], "proof_text": "\n".join(texts)}
            # The generator and this exact-integer oracle share an explicitly disclosed template.
            require(s == a+b and s*s == (a+b)**2, "invalid initial arithmetic")
            rows.append({"case_id": f"arith-{a}-{b}-delta-{delta}", "problem": problem, "graph": graph,
                "edit_text": f"Define t=a+b+{delta}={s+delta}.",
                "oracle": {"evidence_kind": "constructed_exact_integer_fixture", "human_verified": False,
                    "initial_all_nodes_locally_valid": True,
                    "after_edit_valid": {f"n{i}": i!=2 or (s+delta)**2 == s*s for i in range(1,6)},
                    "submitted_text_strictly_valid_after_edit": delta == 0,
                    "theorem_true_both_conditions": True},
                "control": "semantics_preserving" if delta==0 else "descendant_becomes_false"})
    return rows


def edited_state(case, strategy):
    state = ProofState(case["problem"], case["graph"], strategy)
    for n in state.nodes:
        state.record(n, {"target": state.ref(n), "status": "closed", "checked_obligation": n["claim"],
            "reason": "Initial fixture verified by disclosed exact-integer construction",
            "unresolved_conditions": [], "counterexample": None}, "constructed_integer_oracle")
    target = state.nodes[0]
    # The controller accepts an authorized stress edit, NOT a claim that a correct node was defective.
    certificate = {"certificate_id": digest({"case": case["case_id"], "purpose": "controlled_edit"}),
        "target": state.ref(target), "graph_digest": state.graph_digest(), "confirmation": "confirmed",
        "kind": "controlled_edit", "purpose": "synthetic edit authorization; no mathematical diagnosis"}
    node = {**case["graph"]["nodes"][0], "text": case["edit_text"], "claim": case["edit_text"]}
    patch = {"base_state_digest": digest(state.snapshot()), "certificate_id": certificate["certificate_id"],
        "target": state.ref(target), "operation": "replace", "nodes": [node], "target_dependencies_after": [],
        "counterexample": None, "reason": "Identical preassigned local edit across revalidation strategies"}
    state.commit(state.draft_patch(patch, certificate))
    return state, patch


def prepare(output):
    cases = fixtures()
    assignments = [{"case_id": c["case_id"], "strategy": s,
        "task_id": digest({"case_id": c["case_id"], "strategy": s})} for c in cases for s in STRATEGIES]
    config = read(ROOT / "docs/workflow_v2/protocol.json")
    manifest = {"schema_version": "controlled-edit-stress-1", "run_id": output.name,
        "dataset_role": "constructed_development_mechanism_stress", "confirmatory_claim_allowed": False,
        "human_verified": False, "fixture_digest": digest(cases), "assignments_digest": digest(assignments),
        "implementation_digest": implementation_digest(), "script_sha256": file_digest(__file__),
        "models": config["models"], "rubric_version": config["final_scoring"]["rubric_version"],
        "internal_budget": {"max_calls": 24, "max_tokens": 80000, "max_seconds": 1800, "max_output_retries": 1},
        "judge_budget": {"max_calls": 1, "max_tokens": 24000, "max_seconds": 1800},
        "servers": {"experiment": 24, "validation": 24}, "restart_policy": "never",
        "comparison": "same initial exact-checked graph and edit, independent model contexts; no autonomous repair",
        "sample_size_warning": "three parameterized arithmetic families, not 18 independent mathematical problems"}
    write_once(output / "fixtures.json", cases)
    write_once(output / "assignments.json", assignments)
    write_once(output / "manifest.json", manifest)
    snapshot_implementation(output / "implementation_snapshot.zip")
    script = output / "runner_snapshot.py"
    if script.exists(): require(file_digest(script) == manifest["script_sha256"], "runner drift")
    else: script.write_bytes(Path(__file__).read_bytes())
    return manifest, {c["case_id"]:c for c in cases}, assignments


def generate(case, assignment, calls):
    state, patch = edited_state(case, assignment["strategy"])
    scheduled = [n["node_id"] for n in state.nodes if n["status"]=="pending"]
    evaluated = []
    failure = None
    audit = None
    try:
        while (node := state.frontier()) is not None:
            payload = {"problem": problem_context(case["problem"]), "target": state.ref(node),
                "target_node": {k:node[k] for k in ("text","claim","scope","depends_on","goal_refs")},
                "closed_predecessors": state.context(node), "rule_candidates": [], "counterexample_search": True}
            result = calls.call("evaluate", payload, validator=lambda v: state.check_evaluation(node,v))
            state.record(node, result, calls.count)
            evaluated.append(node["node_id"])
        local_claim = all(n["status"]=="closed" for n in state.nodes)
        # All strategies audit the SAME frozen text, including failed local checks; no repair is allowed.
        audit = calls.call("audit", {"problem": problem_context(case["problem"]),
            "candidate_text": state.render(), "nodes": [{"node_id":n["node_id"],"text":n["text"]} for n in state.nodes]})
    except Exception as exc:
        local_claim = False
        failure = str(exc)
    return {"assignment": assignment, "candidate_text": state.render(), "patch": patch,
        "scheduled_revalidation": scheduled, "evaluated_nodes": evaluated,
        "local_success_before_audit": local_claim, "internal_audit": audit,
        "success_after_audit": local_claim and audit is not None and audit_pass(audit),
        "state": state.snapshot(), "events": state.events, "failure": failure, "calls": calls.summary(),
        "human_verified": False}


def run(output, manifest, cases, assignments):
    output = Path(output).resolve()
    require(not (output / "runtime").exists() and not (output / "judge").exists(), "use a fresh run")
    servers = [PersistentServer(output / "servers" / f"{role}-{lane:02d}", role, lane)
               for role in ("experiment", "validation") for lane in range(24)]
    tasks, queues = queue.Queue(), [queue.Queue() for _ in range(24)]
    for a in sorted(assignments, key=lambda x:x["task_id"]): tasks.put(a)
    mapping = {a["task_id"]:"blind-"+uuid.uuid4().hex for a in assignments}
    write_once(output / "private_judge_mapping.json", mapping)
    stop, lock = threading.Event(), threading.Lock()
    outcomes, judgments = {}, {}
    started = time.time()
    def abort(reason):
        stop.set()
        for server in servers: server.abort.set()
    handlers = {sig:signal.signal(sig, lambda *_:abort("signal")) for sig in (signal.SIGINT, signal.SIGTERM)}
    def snapshot(status):
        with lock:
            value = {"status":status, "elapsed_seconds":time.time()-started,
                "runtime_completed":len(outcomes), "judge_completed":len(judgments), "assigned":len(assignments),
                "server_restarts":0, "slots":[{"role":s.role,"lane":s.lane,
                    "pid":s.process.pid if s.process else None, "alive":s.process is not None and s.process.poll() is None,
                    "calls":s.call_count,"contexts_released":s.contexts_released} for s in servers]}
        atomic_json(output / "status.json", value)
        return value
    def worker(server):
        try:
            while not stop.is_set():
                try: assignment = tasks.get_nowait()
                except queue.Empty: break
                folder = output / "runtime" / assignment["task_id"]
                calls = Calls(folder, execute=True, live_adapter=server, **manifest["internal_budget"])
                result = generate(cases[assignment["case_id"]], assignment, calls)
                write_once(folder / "result.json", {**result,"evidence_files":evidence_files(folder)})
                freeze = {"task_id":assignment["task_id"],"lane":server.lane,
                          "sha256":file_digest(folder / "result.json")}
                write_once(output / "candidate_freezes" / (assignment["task_id"]+".json"), freeze)
                with lock: outcomes[assignment["task_id"]] = result
                queues[server.lane].put(assignment)
        finally: queues[server.lane].put(None)
    def judge_worker(server):
        while not stop.is_set():
            try: assignment = queues[server.lane].get(timeout=1)
            except queue.Empty: continue
            if assignment is None: return
            task = assignment["task_id"]
            frozen = read(output / "candidate_freezes" / (task+".json"))
            source = output / "runtime" / task / "result.json"
            require(frozen["lane"] == server.lane and file_digest(source)==frozen["sha256"], "pair/freeze drift")
            saved = read(source)
            require(saved["evidence_files"]==evidence_files(source.parent), "runtime evidence drift")
            folder = output / "judge" / mapping[task]
            payload = judge_input(cases[assignment["case_id"]]["problem"], saved["candidate_text"], mapping[task])
            calls = Calls(folder, execute=True, live_adapter=server, judge=True, **manifest["judge_budget"])
            try: scored = {"status":"scored","judgment":validate_judgment(calls.call("judge",payload),payload)}
            except Exception as exc: scored = {"status":"missing","judgment":None,"reason":str(exc)}
            write_once(folder / "result.json", {**scored,"calls":calls.summary(),"evidence_files":evidence_files(folder)})
            with lock: judgments[task] = {**scored,"calls":calls.summary()}
    status, error = "failed", None
    try:
        for s in servers: s.on_failure = abort
        with ThreadPoolExecutor(max_workers=8) as pool:
            for f in as_completed([pool.submit(s.start) for s in servers]): f.result()
            readiness = [f.result() for f in [pool.submit(s.check_ready) for s in servers]]
        write_once(output / "readiness.json", readiness)
        require(all(r["catalog_available"] and r["context_unload_verified"] for r in readiness),
                "server model/lifecycle preflight failed")
        with ThreadPoolExecutor(max_workers=48) as pool:
            futures = [pool.submit(worker if s.role=="experiment" else judge_worker,s) for s in servers]
            while not all(f.done() for f in futures):
                snapshot("running")
                for f in futures:
                    if f.done() and f.exception() is not None:
                        abort(str(f.exception()))
                        raise f.exception()
                time.sleep(5)
            for f in futures: f.result()
        require(len(outcomes)==len(assignments)==len(judgments), "incomplete mechanism run")
        status = "completed_with_failures" if any(r["failure"] for r in outcomes.values()) or any(
            r["status"]!="scored" for r in judgments.values()) else "completed"
    except Exception as exc:
        error = str(exc)
        abort(error)
    finally:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for f in as_completed([pool.submit(s.close) for s in servers]): f.result()
        for sig, handler in handlers.items(): signal.signal(sig,handler)
        write_once(output / "final.json", {**snapshot(status),"error":error})
    summaries = []
    for strategy in STRATEGIES:
        selected = [a for a in assignments if a["strategy"]==strategy]
        records = []
        for a in selected:
            r, j = outcomes.get(a["task_id"]), judgments.get(a["task_id"])
            if not r: continue
            oracle = cases[a["case_id"]]["oracle"]["submitted_text_strictly_valid_after_edit"]
            records.append({"case_id":a["case_id"],"oracle_strictly_valid":oracle,
                "evaluated_nodes":r["evaluated_nodes"],"local_success":r["local_success_before_audit"],
                "success_after_audit":r["success_after_audit"],
                "false_local_success":r["local_success_before_audit"] and not oracle,
                "strict_judge_acceptance":strict_accept(j["judgment"]) if j and j["status"]=="scored" else None,
                "calls":r["calls"],"judge_calls":j["calls"] if j else None,"failure":r["failure"]})
        summaries.append({"strategy":strategy,"assigned":len(selected),"records":records})
    write_once(output / "aggregate.json", {"evidence":"controlled_arithmetic_stress_model_checks",
        "human_verified":False,"summaries":summaries})
    return status


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    args.bundle=args.bundle.resolve()
    args.bundle.mkdir(parents=True,exist_ok=True)
    with (args.bundle/".lock").open("a") as lockfile:
        fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
        m,c,a=prepare(args.bundle)
        print(json.dumps({"assigned":len(a),"execute":args.execute,"models":m["models"]},indent=2),flush=True)
        if args.execute:
            status=run(args.bundle,m,c,a)
            print(status,flush=True)
            sys.exit(0 if status in {"completed","completed_with_failures"} else 1)
