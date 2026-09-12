#!/usr/bin/env python3
"""Describe original-graph verification demand; no model calls or mathematical labels."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from harness.workflow_v2.contracts import read, write_once
from harness.workflow_v2.reporting import archive_check
from harness.workflow_v2.evidence import exact_numeric_relation


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();manifest=archive_check(a.bundle);rows=[]
    for task in read(a.bundle/"assignments.json"):
        if task["method"]!="full_system":continue
        folder=a.bundle/"runtime"/task["task_id"]
        graphs=sorted(folder.glob("call-*-graph/validated.json"))
        if not graphs:continue
        nodes=read(graphs[-1])["nodes"]
        numeric=sum(n["claim"].strip()==n["text"].strip() and exact_numeric_relation(n["text"]) is not None for n in nodes)
        optimistic=len(nodes)-numeric+2
        result=read(folder/"result.json")["outcome"] if (folder/"result.json").exists() else None
        rows.append({"case_id":task["case_id"],"initial_nodes":len(nodes),"exact_numeric_nodes":numeric,
            "unchanged_graph_optimistic_model_calls":optimistic,"max_calls":manifest["budget"]["max_model_attempts_per_task"],
            "exceeds_call_cap_without_node_removal":optimistic>manifest["budget"]["max_model_attempts_per_task"],
            "terminal":result["terminal_status"] if result else None,"actual_calls":result["model_attempts"] if result else None,
            "tokens":result["known_total_tokens"] if result else None})
    write_once(a.output,{"bundle":str(a.bundle.resolve()),"rows":rows,"model_calls":0,
        "interpretation":"one graph call + one non-deterministic check per original node + one final audit; assumes every node closes, no repair, no retries, no removals. This describes budget pressure, not impossibility or mathematical correctness."})
    print(rows)
