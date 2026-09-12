#!/usr/bin/env python3
"""New-process continuation of an interrupted pilot; verified completed results are imported unchanged."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import signal
import sys
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harness.workflow_v2.contracts import (read, require, write_once, implementation_digest,
    judge_input, validate_judgment, digest)
from harness.workflow_v2.experiment import prepare, validate_bundle_data, evidence_files, file_digest, aggregate
from harness.workflow_v2.reporting import archive_check
from harness.workflow_v2.scheduler import Scheduler, atomic_json


def verified_result(folder):
    try:
        saved=read(folder/"result.json")
        for name,expected in saved["evidence_files"].items():
            require(file_digest(folder/name)==expected,"evidence hash mismatch")
        require(evidence_files(folder)==saved["evidence_files"],"evidence inventory differs")
        return saved
    except (OSError,json.JSONDecodeError,KeyError):
        return None


def inspect_source(source):
    manifest=archive_check(source)
    require(manifest["implementation_digest"]==implementation_digest(),
            "continuation must preserve the original core implementation")
    _,cases,assignments=validate_bundle_data(source,manifest)
    mapping=read(source/"private_judge_mapping.json")
    runtimes,judges={},{}
    for a in assignments:
        task=a["task_id"]
        saved=verified_result(source/"runtime"/task)
        if saved:
            require(saved["assignment"]==a,"source assignment differs")
            runtimes[task]=saved
            score=verified_result(source/"judge"/mapping[task])
            if score:
                if score["status"]=="scored":
                    payload=judge_input(cases[a["case_id"]],saved["outcome"]["candidate_text"],mapping[task])
                    validate_judgment(score["judgment"],payload)
                judges[task]=score
    return manifest,cases,assignments,mapping,runtimes,judges


def rpc_accounting(source):
    ledgers,errors={},[]
    hashes={}
    for file in sorted((source/"scheduler/servers").glob("*/rpc.jsonl")):
        try:
            text=file.read_text()
            hashes[str(file.relative_to(source))]=file_digest(file)
        except OSError as exc:
            errors.append({"path":str(file),"error":str(exc)});continue
        for line_number,line in enumerate(text.splitlines(),1):
            try:r=json.loads(line)
            except ValueError:
                errors.append({"path":str(file),"line":line_number,"error":"incomplete RPC line"});continue
            msg=r["message"];method=msg.get("method");params=msg.get("params",{})
            thread=params.get("threadId")
            if not thread:continue
            row=ledgers.setdefault(thread,{"role":file.parent.name.rsplit("-",1)[0],
                "started":False,"completed":False,"usage":None})
            if r["direction"]=="send" and method=="turn/start":row["started"]=True
            if r["direction"]=="receive" and method=="thread/tokenUsage/updated":row["usage"]=params["tokenUsage"]["total"]
            if r["direction"]=="receive" and method=="turn/completed":row["completed"]=params["turn"]["status"]=="completed"
    started={k:v for k,v in ledgers.items() if v["started"]}
    totals={role:sum(v["usage"]["inputTokens"]+v["usage"]["outputTokens"] for v in started.values()
                      if v["role"]==role and v["usage"] is not None) for role in ("experiment","validation")}
    return {"rpc_files":hashes,"threads":started,"known_tokens_lower_bound":totals,"read_errors":errors,
            "unknown_usage_threads":[k for k,v in started.items() if v["usage"] is None],
            "incomplete_turns":[k for k,v in started.items() if not v["completed"]],
            "accounting_complete":not errors and all(v["usage"] is not None and v["completed"] for v in started.values())}


def prepare_continuation(source,output):
    require(source!=output and not output.is_relative_to(source),"continuation must be separate")
    m,c,a,mapping,runtimes,judges=inspect_source(source)
    prepare(output,case_ids=list(c),selection_note="Interrupted iteration2 continuation: import verified completed tasks unchanged; rerun only incomplete tasks in a separate attempt.")
    provenance={"source_bundle":str(source),"source_manifest_sha256":file_digest(source/"manifest.json"),
        "continuation_manifest_sha256":file_digest(output/"manifest.json"),"runner_sha256":file_digest(__file__),
        "core_implementation_unchanged":True,
        "runtime_imports":{k:file_digest(source/"runtime"/k/"result.json") for k in runtimes},
        "judge_imports":{k:{"sample_id":mapping[k],"sha256":file_digest(source/"judge"/mapping[k]/"result.json")} for k in judges},
        "runtime_to_rerun":[x["task_id"] for x in a if x["task_id"] not in runtimes],
        "judgments_to_run":[x["task_id"] for x in a if x["task_id"] not in judges],
        "interruption_policy":"completed evidence is byte-identical; incomplete tasks start fresh under original per-attempt caps; all interrupted usage is reported separately, unknown never zero-filled",
        "scientific_limit":"interrupted and repeated tasks are not an uninterrupted equal-total-budget replicate",
        "original_log_last_line":(source/"console.log").read_text().splitlines()[-1]}
    write_once(output/"continuation.json",provenance)
    write_once(output/"interruption_accounting.json",rpc_accounting(source))
    script=output/"continuation_runner.py"
    if script.exists():require(file_digest(script)==provenance["runner_sha256"],"continuation runner drift")
    else:script.write_bytes(Path(__file__).read_bytes())
    return provenance


class ContinuationScheduler(Scheduler):
    def __init__(self,bundle,source,**kwargs):
        self.source=source
        _,_,_,self.old_mapping,self.runtime_imports,self.judge_imports=inspect_source(source)
        self.provenance=read(bundle/"continuation.json")
        require(self.provenance["runner_sha256"]==file_digest(__file__),"continuation runner changed")
        require(self.provenance["runtime_imports"]=={k:file_digest(source/"runtime"/k/"result.json") for k in self.runtime_imports},"imported runtime changed")
        super().__init__(bundle,**kwargs)

    def copy_evidence(self,source,dest,saved):
        for name,expected in {**saved["evidence_files"],"result.json":file_digest(source/"result.json")}.items():
            require(file_digest(source/name)==expected,"source changed while importing")
            (dest/name).parent.mkdir(parents=True,exist_ok=True)
            require(not (dest/name).exists(),"import target already exists")
            shutil.copyfile(source/name,dest/name)
            require(file_digest(dest/name)==expected,"copied evidence differs")

    def run_assignment(self,assignment,server):
        task=assignment["task_id"]
        if task not in self.runtime_imports:return super().run_assignment(assignment,server)
        saved=self.runtime_imports[task]
        folder=self.path/"runtime"/task
        self.copy_evidence(self.source/"runtime"/task,folder,saved)
        freeze={"task_id":task,"lane":server.lane,"result_sha256":file_digest(folder/"result.json")}
        write_once(self.path/"candidate_freezes"/(task+".json"),freeze)
        with self.lock:self.completed[task]=saved["outcome"]
        self.event("candidate_imported_and_frozen",source_bundle=str(self.source),**freeze)
        self.judge_queues[server.lane].put(assignment)

    def judge_assignment(self,assignment,server):
        task=assignment["task_id"]
        if task not in self.judge_imports:return super().judge_assignment(assignment,server)
        sample=self.mapping[task]
        require(sample==self.old_mapping[task],"import must preserve the original blind identity")
        saved=self.judge_imports[task]
        source=self.source/"judge"/sample
        require(file_digest(source/"result.json")==self.provenance["judge_imports"][task]["sha256"],"source judge changed")
        self.copy_evidence(source,self.path/"judge"/sample,saved)
        with self.lock:self.judgments[task]=saved
        self.event("judgment_imported",task_id=task,sample_id=sample,source_bundle=str(self.source))

    def snapshot(self):
        value=super().snapshot()
        value.update(inherited_runtime_results=sum(k in self.completed for k in self.runtime_imports),
            inherited_judgments=sum(k in self.judgments for k in self.judge_imports),
            new_judge_model_calls=sum(s.call_count for s in self.servers if s.role=="validation"),
            interrupted_source_accounting_complete=read(self.path/"interruption_accounting.json")["accounting_complete"])
        atomic_json(self.path/"scheduler/status.json",value)
        return value

    def run(self):
        require(not (self.path/"runtime").exists() and not (self.path/"judge").exists(),"use a fresh continuation")
        record=self.path/"scheduler";record.mkdir(exist_ok=True)
        write_once(record/"startup.json",{"started_at":self.started,"continuation_of":str(self.source),
            "manifest_digest":digest(self.manifest),"servers":48,"server_restart_policy":"never"})
        self.mapping={a["task_id"]:self.old_mapping[a["task_id"]] if a["task_id"] in self.judge_imports
                      else "blind-"+uuid.uuid4().hex for a in self.assignments}
        write_once(self.path/"private_judge_mapping.json",self.mapping)
        handlers={}
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGTERM,signal.SIGINT):handlers[sig]=signal.signal(sig,lambda *_:self.cancel("signal"))
        try:
            self.servers=[self.factory(record/"servers"/f"{role}-{lane:02d}",role,lane)
                          for role in self.roles for lane in range(self.lanes)]
            with ThreadPoolExecutor(max_workers=8) as pool:
                for f in as_completed([pool.submit(s.start) for s in self.servers]):f.result()
                checks=list(pool.map(lambda s:s.check_ready(),self.servers))
            write_once(record/"readiness.json",{"servers":checks,"new_model_calls":0})
            require(all(r["catalog_available"] and r["context_unload_verified"] for r in checks),"startup preflight failed")
            self.status="running"
            workers=[threading.Thread(target=self.experiment_worker if s.role=="experiment" else self.judge_worker,args=(s,)) for s in self.servers]
            for w in workers:w.start()
            while any(w.is_alive() for w in workers):
                state=self.snapshot()
                print(json.dumps({k:state[k] for k in ("status","runtime_completed","judge_completed","runtime_failed","inherited_runtime_results","inherited_judgments","elapsed_seconds")}),flush=True)
                for s in self.servers:
                    if s.process.poll() is not None:self.cancel("server exited; no restart")
                time.sleep(5)
            for w in workers:w.join()
            require(len(self.completed)==len(self.assignments)==len(self.judgments),"continuation incomplete")
            write_once(self.path/"candidate_freeze.json",{a["task_id"]:file_digest(self.path/"runtime"/a["task_id"]/"result.json") for a in self.assignments})
            write_once(record/"aggregate.json",aggregate(self.path))
            self.status="completed_with_failures" if any(r["terminal_status"]=="runtime_failed" for r in self.completed.values()) or any(r["status"]!="scored" for r in self.judgments.values()) else "completed"
        except Exception as exc:
            self.status="failed";self.cancel(str(exc));self.event("scheduler_failed",reason=str(exc))
        finally:
            with ThreadPoolExecutor(max_workers=8) as pool:
                for f in as_completed([pool.submit(s.close) for s in self.servers]):
                    try:f.result()
                    except Exception as exc:self.event("shutdown_error",reason=str(exc))
            for sig,handler in handlers.items():signal.signal(sig,handler)
            write_once(record/"final.json",self.snapshot())
        return self.snapshot()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--execute",action="store_true")
    a=p.parse_args();source,bundle=a.source.resolve(),a.bundle.resolve();bundle.mkdir(parents=True,exist_ok=True)
    with (bundle/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        provenance=prepare_continuation(source,bundle)
        print(json.dumps({"runtime_imports":len(provenance["runtime_imports"]),"judge_imports":len(provenance["judge_imports"]),
            "runtime_to_rerun":len(provenance["runtime_to_rerun"]),"judgments_to_run":len(provenance["judgments_to_run"])}),flush=True)
        if a.execute:
            result=ContinuationScheduler(bundle,source).run()
            sys.exit(0 if result["status"] in {"completed","completed_with_failures"} else 1)
