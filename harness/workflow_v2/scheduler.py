"""24 paired experiment/judge lanes with persistent servers and streaming freezes."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import queue
import signal
import threading
import time
import uuid

from .app_server import PersistentServer
from .contracts import digest, judge_input, read, require, validate_judgment, write_once
from .engine import Workflow
from .experiment import aggregate, evidence_files, file_digest, validate_bundle
from .runtime import Calls

LANES = 24


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


class Scheduler:
    def __init__(self, bundle, *, server_factory=PersistentServer, lanes=LANES, mode="pipeline"):
        require(mode in {"pipeline", "experiment_only", "judge_only"}, "unknown scheduler mode")
        self.mode = mode
        self.roles = (("experiment",) if mode == "experiment_only" else
                      ("validation",) if mode == "judge_only" else ("experiment", "validation"))
        self.path = Path(bundle).resolve()
        self.manifest, self.cases, self.assignments = validate_bundle(self.path)
        require((mode == "judge_only") == (self.manifest.get("schema_version") == "workflow-v2-judgment-bundle-1"),
                "judge-only mode requires a separate frozen-source judge bundle")
        self.runtime_path = Path(self.manifest.get("source_bundle", self.path))
        self.factory, self.lanes = server_factory, lanes
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.servers = []
        self.events = []
        self.completed = {}
        if mode == "judge_only":
            self.completed = {a["task_id"]: read(self.runtime_path / "runtime" / a["task_id"] / "result.json")["outcome"]
                              for a in self.assignments}
        self.judgments = {}
        self.active = {}
        self.status = "starting"
        self.started = time.time()
        self.reason = None
        self.judge_queues = [queue.Queue() for _ in range(lanes)]
        self.tasks = queue.Queue()
        for assignment in sorted(self.assignments, key=lambda a: a["task_id"]):
            self.tasks.put(assignment)

    def event(self, event, **fields):
        row = {"time": time.time(), "event": event, **fields}
        with self.lock:
            self.events.append(row)
            with (self.path / "scheduler/events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def cancel(self, reason):
        if not self.stop.is_set():
            self.reason = reason
            self.stop.set()
            self.event("dispatch_stopped", reason=reason)
            for server in self.servers:
                server.abort.set()

    def snapshot(self):
        with self.lock:
            slots = [{"lane": s.lane, "role": s.role,
                "pid": s.process.pid if s.process else None,
                "alive": s.process is not None and s.process.poll() is None,
                "healthy": s.healthy, "calls": s.call_count,
                "contexts_released": s.contexts_released} for s in self.servers]
            result = {"status": self.status, "pid": os.getpid(), "started_at": self.started,
                "updated_at": time.time(), "elapsed_seconds": time.time()-self.started,
                "mode": self.mode, "judge_stage": "deferred" if self.mode == "experiment_only" else "enabled",
                "inherited_runtime_results": len(self.completed) if self.mode == "judge_only" else 0,
                "new_experiment_model_calls": sum(s.call_count for s in self.servers if s.role == "experiment"),
                "lanes": self.lanes, "expected_servers": self.lanes*len(self.roles), "server_restarts": 0,
                "assigned": len(self.assignments), "runtime_completed": len(self.completed),
                "runtime_failed": sum(r["terminal_status"] == "runtime_failed" for r in self.completed.values()),
                "judge_completed": len(self.judgments),
                "judge_scored": sum(r["status"] == "scored" for r in self.judgments.values()),
                "known_internal_tokens": sum(r["known_total_tokens"] for r in self.completed.values()),
                "known_judge_tokens": sum(r["calls"]["known_total_tokens"] for r in self.judgments.values()),
                "active": dict(self.active), "slots": slots, "stop_reason": self.reason}
        atomic_json(self.path / "scheduler/status.json", result)
        return result

    def adapter(self, server, task_id):
        def call(**kwargs):
            require(not self.stop.is_set(), "scheduler dispatch stopped")
            server.on_failure = lambda reason: self.cancel(f"{server.role} lane {server.lane}: {reason}")
            self.event("model_call_started", task_id=task_id, lane=server.lane, role=server.role,
                       model=server.model, effort=server.effort, call=server.call_count+1)
            try:
                raw = server(**kwargs)
            except Exception as exc:
                # Runtime/schema failures remain observations; transport/config failures stop dispatch.
                self.cancel(f"{server.role} lane {server.lane}: {exc}")
                raise
            self.event("model_call_finished", task_id=task_id, lane=server.lane, role=server.role,
                thread_id=raw.get("codex_thread_id"), context_released=raw.get("context_released"),
                server_pid=raw.get("server_pid"))
            return raw
        return call

    def run_assignment(self, assignment, server):
        require(self.mode != "judge_only", "generation is forbidden in judge-only mode")
        task_id = assignment["task_id"]
        folder = self.path / "runtime" / task_id
        write_once(folder / "identity.json", assignment)
        budget = self.manifest["budget"]
        calls = Calls(folder, execute=True, live_adapter=self.adapter(server, task_id),
            max_calls=budget["max_model_attempts_per_task"],
            max_tokens=budget["max_total_tokens_per_task"], max_seconds=budget["max_wall_seconds_per_task"],
            max_output_retries=budget.get("max_output_contract_retries", 0))
        outcome = Workflow(self.cases[assignment["case_id"]], calls).run(assignment["method"])
        write_once(folder / "result.json", {"assignment": assignment, "outcome": outcome,
                                            "evidence_files": evidence_files(folder)})
        freeze = {"task_id": task_id, "lane": server.lane,
                  "result_sha256": file_digest(folder / "result.json")}
        write_once(self.path / "candidate_freezes" / (task_id + ".json"), freeze)
        with self.lock:
            self.completed[task_id] = outcome
        self.event("candidate_frozen", **freeze)
        if self.mode == "pipeline":
            self.judge_queues[server.lane].put(assignment)

    def judge_assignment(self, assignment, server):
        require(self.mode in {"pipeline", "judge_only"}, "external judging is deferred in experiment_only mode")
        task_id = assignment["task_id"]
        freeze = read(self.runtime_path / "candidate_freezes" / (task_id + ".json"))
        require(freeze["lane"] == server.lane, "judge dispatched to wrong paired server")
        source = self.runtime_path / "runtime" / task_id / "result.json"
        require(file_digest(source) == freeze["result_sha256"], "candidate changed after freeze")
        saved = read(source)
        require(saved["evidence_files"] == evidence_files(source.parent), "runtime evidence changed")
        sample = self.mapping[task_id]
        folder = self.path / "judge" / sample
        payload = judge_input(self.cases[assignment["case_id"]], saved["outcome"]["candidate_text"], sample)
        calls = Calls(folder, execute=True, judge=True, live_adapter=self.adapter(server, task_id),
                      **self.manifest["external_judge_budget"])
        self.event("judge_started", task_id=task_id, lane=server.lane, sample_id=sample)
        try:
            judgment = validate_judgment(calls.call("judge", payload), payload)
            result = {"status": "scored", "judgment": judgment}
        except Exception as exc:
            result = {"status": "missing", "reason": str(exc), "judgment": None}
        result.update(calls=calls.summary(), evidence_files=evidence_files(folder))
        write_once(folder / "result.json", result)
        with self.lock:
            self.judgments[task_id] = result
        self.event("judge_finished", task_id=task_id, lane=server.lane, status=result["status"])

    def experiment_worker(self, server):
        key = "experiment-" + str(server.lane)
        try:
            while not self.stop.is_set():
                try:
                    assignment = self.tasks.get_nowait()
                except queue.Empty:
                    break
                with self.lock:
                    self.active[key] = {"task_id": assignment["task_id"], "case_id": assignment["case_id"],
                                        "method": assignment["method"], "started_at": time.time()}
                self.run_assignment(assignment, server)
        except Exception as exc:
            self.cancel(f"experiment worker {server.lane}: {exc}")
        finally:
            with self.lock:
                self.active.pop(key, None)
            self.judge_queues[server.lane].put(None)

    def judge_worker(self, server):
        key = "validation-" + str(server.lane)
        try:
            while not self.stop.is_set():
                try:
                    assignment = self.judge_queues[server.lane].get(timeout=1)
                except queue.Empty:
                    continue
                if assignment is None:
                    break
                with self.lock:
                    self.active[key] = {"task_id": assignment["task_id"], "started_at": time.time()}
                self.judge_assignment(assignment, server)
        except Exception as exc:
            self.cancel(f"judge worker {server.lane}: {exc}")
        finally:
            with self.lock:
                self.active.pop(key, None)

    def run(self):
        require(not (self.path / "runtime").exists() and not (self.path / "judge").exists(),
                "scheduler requires a fresh bundle; evidence is never overwritten")
        record = self.path / "scheduler"
        record.mkdir(exist_ok=True)
        write_once(record / "startup.json", {"pid": os.getpid(), "started_at": self.started,
            "lanes": self.lanes, "servers": self.lanes*len(self.roles), "mode": self.mode,
            "manifest_digest": digest(self.manifest),
            "freeze_policy": "per_candidate_before_paired_judge", "server_restart_policy": "never"})
        if self.mode in {"pipeline", "judge_only"}:
            self.mapping = {a["task_id"]: "blind-" + uuid.uuid4().hex for a in self.assignments}
            write_once(self.path / "private_judge_mapping.json", self.mapping)
        if self.mode == "judge_only":
            for assignment in sorted(self.assignments, key=lambda a: self.mapping[a["task_id"]]):
                lane = read(self.runtime_path / "candidate_freezes" / (assignment["task_id"] + ".json"))["lane"]
                self.judge_queues[lane].put(assignment)
            for work in self.judge_queues:
                work.put(None)
        handlers = {}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGTERM, signal.SIGINT):
                handlers[sig] = signal.signal(sig, lambda signum, frame: self.cancel(f"signal {signum}"))
        try:
            self.servers = [self.factory(record / "servers" / f"{role}-{lane:02d}", role, lane)
                for role in self.roles for lane in range(self.lanes)]
            # Only the enabled roles are started and probed; no validation process in experiment_only.
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {pool.submit(server.start): server for server in self.servers}
                for future in as_completed(futures):
                    future.result()
                    server = futures[future]
                    self.event("server_started", lane=server.lane, role=server.role, pid=server.process.pid)
                    self.snapshot()
            require(not self.stop.is_set(), "startup cancelled")
            with ThreadPoolExecutor(max_workers=8) as pool:
                checks = list(pool.map(lambda server: server.check_ready(), self.servers))
            write_once(record / "readiness.json", {"servers": checks, "new_model_calls": 0})
            unavailable = sorted({r["model"] for r in checks if not r["catalog_available"]})
            require(not unavailable, "fixed models missing from server catalog: " + ", ".join(unavailable))
            self.status = "running"
            self.event("all_servers_ready", count=len(self.servers))
            workers = [threading.Thread(target=self.experiment_worker if s.role == "experiment" else self.judge_worker,
                                         args=(s,), name=f"{s.role}-{s.lane}") for s in self.servers]
            for worker in workers:
                worker.start()
            while any(worker.is_alive() for worker in workers):
                state = self.snapshot()
                print(json.dumps({k: state[k] for k in ("status", "runtime_completed", "judge_completed",
                                                       "judge_scored", "runtime_failed", "elapsed_seconds")}), flush=True)
                for server in self.servers:
                    if server.process.poll() is not None:
                        self.cancel(f"server exited: {server.role}-{server.lane}; no restart")
                time.sleep(5)
            for worker in workers:
                worker.join()
            if len(self.completed) == len(self.assignments):
                write_once(self.path / "candidate_freeze.json", {a["task_id"]:
                    file_digest(self.runtime_path / "runtime" / a["task_id"] / "result.json") for a in self.assignments})
                if self.mode == "experiment_only":
                    write_once(record / "judge_handoff.json", {"status": "deferred_by_user",
                        "candidate_count": len(self.completed), "new_external_model_calls": 0,
                        "candidate_freeze_sha256": file_digest(self.path / "candidate_freeze.json"),
                        "pending_task_ids": [a["task_id"] for a in self.assignments]})
            write_once(record / "aggregate.json", aggregate(self.path))
            failures = self.mode != "judge_only" and any(r["terminal_status"] == "runtime_failed" for r in self.completed.values())
            missing = any(r["status"] != "scored" for r in self.judgments.values())
            self.status = "stopped" if self.stop.is_set() else "completed_with_failures" if failures or missing else "completed"
        except Exception as exc:
            self.status = "failed"
            self.cancel(str(exc))
            self.event("scheduler_failed", reason=str(exc))
        finally:
            with ThreadPoolExecutor(max_workers=8) as pool:
                for future in as_completed([pool.submit(s.close) for s in self.servers]):
                    try:
                        future.result()
                    except Exception as exc:
                        self.event("shutdown_error", reason=str(exc))
            for sig, old in handlers.items():
                signal.signal(sig, old)
            self.event("scheduler_finished", status=self.status)
            final = self.snapshot()
            write_once(record / "final.json", final)
        return final
