#!/usr/bin/env python3
"""Compare frozen development pilots, separating repeated cases from additions."""
import argparse
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from harness.workflow_v2.contracts import METHODS, read, write_once, strict_accept, require
from harness.workflow_v2.experiment import file_digest
from harness.workflow_v2.reporting import frozen_rows


def summarize(rows):
    out={}
    for method in METHODS:
        selected=[r for r in rows if r[0]["method"]==method]
        counts=Counter(assigned=len(selected))
        for a,p,o,j,*_ in selected:
            counts[o["terminal_status"]]+=1
            counts["calls"]+=o["model_attempts"]
            counts["tokens"]+=o["known_total_tokens"]
            counts["corrections"]+=o.get("output_contract_corrections",0)
            accepted=j["status"]=="scored" and strict_accept(j["judgment"])
            counts["strict_accepted"]+=accepted
            counts["ready_and_accepted"]+=accepted and o["terminal_status"]=="proof_ready"
            counts["missing_judgments"]+=j["status"]!="scored"
        out[method]=dict(counts)
    return out


def compare(old_source,old_judge,new_source,output):
    require(not output.exists(),"use a fresh comparison directory")
    old=frozen_rows(old_source,old_judge)
    new=frozen_rows(new_source,new_source)
    before_ids={r[0]["case_id"] for r in old}
    after_ids={r[0]["case_id"] for r in new}
    require(before_ids<=after_ids,"regression cases missing")
    regression=[r for r in new if r[0]["case_id"] in before_ids]
    additions=[r for r in new if r[0]["case_id"] not in before_ids]
    before,after,extra=summarize(old),summarize(regression),summarize(additions)
    pairs=[]
    keyed={(r[0]["case_id"],r[0]["method"]):r for r in old}
    for r in regression:
        a,p,o,j,*_=r
        prior=keyed[(a["case_id"],a["method"])]
        def success(row):return row[2]["terminal_status"]=="proof_ready" and row[3]["status"]=="scored" and strict_accept(row[3]["judgment"])
        pairs.append({"case_id":a["case_id"],"method":a["method"],"old_success":success(prior),
            "new_success":success(r),"old_terminal":prior[2]["terminal_status"],"new_terminal":o["terminal_status"],
            "old_tokens":prior[2]["known_total_tokens"],"new_tokens":o["known_total_tokens"]})
    value={"evidence":"development_model_judgment_only","human_verified":False,
        "script_sha256":file_digest(__file__),"old_source":str(old_source.resolve()),"old_judge":str(old_judge.resolve()),
        "new_source":str(new_source.resolve()),"original_cases":sorted(before_ids),"additional_cases":sorted(after_ids-before_ids),
        "original_pilot_same_rubric":before,"regression_iteration2":after,"additions_iteration2":extra,"pairs":pairs}
    interruption=None
    if (new_source/"continuation.json").exists():
        provenance=read(new_source/"continuation.json")
        ledger=read(new_source/"interruption_accounting.json")
        copied_internal=sum(r[2]["known_total_tokens"] for r in new if r[0]["task_id"] in provenance["runtime_imports"])
        copied_judge=sum(r[3]["calls"]["known_total_tokens"] for r in new if r[0]["task_id"] in provenance["judge_imports"])
        selected_internal=sum(r[2]["known_total_tokens"] for r in new)
        selected_judge=sum(r[3]["calls"]["known_total_tokens"] for r in new)
        interruption={"source":provenance["source_bundle"],"inherited_runtime":len(provenance["runtime_imports"]),
            "inherited_judgments":len(provenance["judge_imports"]),"source_accounting_complete":ledger["accounting_complete"],
            "selected_result_internal_tokens":selected_internal,"selected_result_judge_tokens":selected_judge,
            "all_attempts_internal_tokens_lower_bound":selected_internal+max(0,ledger["known_tokens_lower_bound"]["experiment"]-copied_internal),
            "all_attempts_judge_tokens_lower_bound":selected_judge+max(0,ledger["known_tokens_lower_bound"]["validation"]-copied_judge),
            "unknown_prior_usage_calls":len(ledger["unknown_usage_threads"]),"equal_total_budget_comparison_valid":False}
        value["interruption"]=interruption
    write_once(output/"comparison.json",value)
    lines=["# 两轮开发先导比较","","两轮使用相同的明确后审核规则。旧评分独立保留；这里使用第一轮候选的同规则重评分。所有接受判断均来自模型，未做人工校准。","",
           "## 原 12 题配对回归","","| 方法 | 首轮就绪且接受 | 第二轮就绪且接受 | 协议失败（前→后） | 总 token（前→后） | 第二轮纠错 |","|---|---:|---:|---|---|---:|"]
    for m in METHODS:
        b,a=before[m],after[m]
        lines.append(f"| {m} | {b.get('ready_and_accepted',0)}/12 | {a.get('ready_and_accepted',0)}/12 | {b.get('runtime_failed',0)} → {a.get('runtime_failed',0)} | {b['tokens']} → {a['tokens']} | {a.get('corrections',0)} |")
    lines += ["","## 新增 6 题","","| 方法 | 就绪且接受 | 协议失败 | 预算耗尽 | 总 token |","|---|---:|---:|---:|---:|"]
    for m in METHODS:
        a=extra[m]
        lines.append(f"| {m} | {a.get('ready_and_accepted',0)}/{a['assigned']} | {a.get('runtime_failed',0)} | {a.get('budget_exhausted',0)} | {a['tokens']} |")
    lines += ["","原证明对照不表示修复成功。缺陷原证明的可靠标签尚未齐备，不将此表冒充条件修复率。每题失败、预算耗尽、不确定和缺评保留在分母。","",
        "这是一次开发期改动包的比较，含提示词、元数据与纠错机制的共同变化，不能将全部差值因果归于某一改动。模型采样也有变异；12 题不作正式显著性或优越性声明。","",
        "逐题配对与所有计数见 [comparison.json](comparison.json)。",""]
    if interruption:
        lines += ["## 中断与续跑的成本限制","",
            f"第二轮继承 {interruption['inherited_runtime']} 份生成和 {interruption['inherited_judgments']} 份审核，未完成任务在新批次重新执行。上表 token 是被选用的完整结果的调用用量，不包含中断尝试开销。",
            f"合并中断日志且扣除继承结果的重复计数后，实验用量下限为 {interruption['all_attempts_internal_tokens_lower_bound']:,} token，审核用量下限为 {interruption['all_attempts_judge_tokens_lower_bound']:,} token。另有 {interruption['unknown_prior_usage_calls']} 个原调用缺少完整用量。",
            "因此成本只能报告下限，不能将它当作未中断且严格等总预算的一轮实验，也不能以被选用结果的用量宣称完整成本优势。",""]
    (output/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    return value


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("old-source","old-judge","new-source","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    compare(a.old_source,a.old_judge,a.new_source,a.output)
    print(a.output/"REPORT.md")
