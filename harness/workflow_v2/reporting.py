"""Read-only reconstruction of archived pilot evidence and blind human packets."""
from collections import Counter, defaultdict
import csv
import hashlib
import io
from pathlib import Path
import uuid
import zipfile

from .contracts import digest, read, require, write_once, judge_input, strict_accept
from .experiment import evidence_files, file_digest, validate_bundle_data


def archive_check(path):
    manifest = read(path / "manifest.json")
    with zipfile.ZipFile(path / "implementation_snapshot.zip") as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        require(digest({n: hashlib.sha256(archive.read(n)).hexdigest() for n in names}) ==
                manifest["implementation_digest"], "archived implementation drift")
    return manifest


def frozen_rows(source, judged):
    source, judged = Path(source).resolve(), Path(judged).resolve()
    manifest = archive_check(source)
    _, cases, assignments = validate_bundle_data(source, manifest)
    jm = archive_check(judged)
    if source != judged:
        require(Path(jm["source_bundle"]) == source, "judge source mismatch")
        for name, expected in jm["source_anchors"].items():
            require(file_digest(source / name) == expected, "source anchor drift")
    frozen = read(source / "candidate_freeze.json")
    require(set(frozen) == {a["task_id"] for a in assignments}, "incomplete freeze")
    mapping = read(judged / "private_judge_mapping.json")
    require(set(mapping) == set(frozen), "incomplete judgment mapping")
    rows = []
    for a in assignments:
        folder = source / "runtime" / a["task_id"]
        saved = read(folder / "result.json")
        require(saved["assignment"] == a and file_digest(folder / "result.json") == frozen[a["task_id"]],
                "frozen result drift")
        require(saved["evidence_files"] == evidence_files(folder), "runtime evidence drift")
        jf = judged / "judge" / mapping[a["task_id"]]
        score = read(jf / "result.json")
        require(score["evidence_files"] == evidence_files(jf), "judge evidence drift")
        rows.append((a, cases[a["case_id"]], saved["outcome"], score, folder, jf))
    return rows


def failure_category(outcome):
    reason = outcome["stop_reason"]
    for needle, category in [("should be non-empty", "empty_required_text"),
        ("scoped premise escapes", "scope_escape"), ("unknown goal", "unknown_goal_reference"),
        ("closed node has unresolved", "local_global_obligation_confusion"),
        ("Equivalent patch", "repeated_patch"), ("Patch attempt", "patch_budget"),
        ("soft budget", "token_budget"), ("follow-up", "uncertainty"),
        ("cannot be verified", "unverified_reference")]:
        if needle in reason:
            return category
    return outcome["terminal_status"]


def make_report(source, judged, output):
    output = Path(output)
    require(not output.exists(), "use a fresh analysis directory")
    rows = frozen_rows(source, judged)
    details, methods, phases, disputes = [], defaultdict(Counter), defaultdict(Counter), []
    packet, private = [], {}
    for a, problem, o, score, folder, jf in rows:
        stats = Counter()
        attempts = []
        for request_file in sorted(folder.glob("call-*/request.json")):
            call = request_file.parent
            request = read(request_file)
            accounting = read(call / "accounting.json") if (call / "accounting.json").exists() else None
            failure = read(call / "failure.json") if (call / "failure.json").exists() else None
            response = read(call / "response.json") if (call / "response.json").exists() else {}
            item = {"phase": request["phase"], "call_path": str(call), "usage": accounting,
                    "latency_seconds": response.get("latency_seconds"), "failure": failure}
            attempts.append(item)
            stats["calls"] += 1
            stats["reported_latency_seconds"] += item["latency_seconds"] or 0
            if accounting:
                for k in ("input_tokens", "output_tokens", "total_tokens"):
                    stats[k] += accounting[k]
                    phases[(a["method"], request["phase"])][k] += accounting[k]
            phases[(a["method"], request["phase"])]["calls"] += 1
        require(stats["calls"] == o["model_attempts"] and stats["total_tokens"] == o["known_total_tokens"],
                "call accounting differs from outcome")
        accepted = score["status"] == "scored" and strict_accept(score["judgment"])
        success = o["terminal_status"] == "proof_ready" and accepted
        row = {**a, "terminal_status": o["terminal_status"], "stop_reason": o["stop_reason"],
               "failure_category": failure_category(o), "judge_status": score["status"],
               "strict_accepted_text": accepted, "ready_and_accepted": success, **dict(stats),
               "attempts": attempts, "events": o["events"], "source_result": str(folder / "result.json"),
               "judge_result": str(jf / "result.json")}
        details.append(row)
        methods[a["method"]].update(stats)
        methods[a["method"]].update({"assigned": 1, "strict_accepted_texts": int(accepted),
            "ready_and_accepted": int(success), "missing_judgments": int(score["status"] != "scored"),
            o["terminal_status"]: 1})
        if score["status"] != "scored" or accepted != (o["terminal_status"] == "proof_ready"):
            disputes.append({"case_id": a["case_id"], "method": a["method"],
                "kind": "judge_record_failure" if score["status"] != "scored" else "terminal_text_disagreement",
                "reason": score.get("reason"), "source_result": row["source_result"],
                "judge_result": row["judge_result"], "human_resolution": None})
        blind_id = "review-" + uuid.uuid4().hex
        packet.append(judge_input(problem, o["candidate_text"], blind_id))
        private[blind_id] = {"task_id": a["task_id"], "case_id": a["case_id"], "method": a["method"],
                             "source_result": row["source_result"], "judge_result": row["judge_result"]}
    packet.sort(key=lambda r: r["sample_id"])
    totals = Counter()
    for value in methods.values():
        totals.update({k: value[k] for k in ("assigned", "calls", "total_tokens", "input_tokens", "output_tokens")})
    summary = {"source": str(Path(source).resolve()), "judge": str(Path(judged).resolve()),
        "integrity_verified": True, "evidence": "model_only", "human_verified": False,
        "totals": dict(totals), "methods": dict(methods),
        "phase_costs": [{"method": m, "phase": p, **dict(v)} for (m,p),v in sorted(phases.items())],
        "failure_categories": dict(Counter(r["failure_category"] for r in details if r["terminal_status"] != "proof_ready")),
        "disputes": disputes}
    write_once(output / "summary.json", summary)
    write_once(output / "tasks.json", details)
    write_once(output / "human/public/candidates.json", packet)
    write_once(output / "human/private/mapping.json", private)
    write_once(output / "human/public/review_template.json", [{"sample_id": p["sample_id"],
        "reviewer_id": None, "reviewed_at": None, "validity": None, "rigor": None,
        "problem_preservation": None, "goal_coverage": None, "findings": [], "reason": None} for p in packet])
    (output / "human/public/README.md").write_text(
        "# Independent mathematical review\n\nReview each anonymous candidate against its supplied problem. "
        "Keep model judgments and private mappings hidden until the review is submitted. "
        "Record validity, rigor, preservation and coverage separately, including exact quotes and reasons. "
        "For redundant erroneous steps, state whether an independent correct proof remains and whether the "
        "submitted text is rigorous. Do not silently repair the text. Use unknown when unsettled. "
        "Do not fill another person's identity or invent a second review.\n\n"
        "All labels in the template are intentionally blank. Two independent reviews followed by "
        "adjudication are preferred; report single-review evidence honestly if only one reviewer is available.\n",
        encoding="utf-8")
    fields = ["case_id", "method", "terminal_status", "failure_category", "calls", "total_tokens",
              "reported_latency_seconds", "judge_status", "strict_accepted_text", "ready_and_accepted"]
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(details)
    (output / "tasks.csv").write_text(stream.getvalue(), encoding="utf-8")
    lines = ["# 逐题失败与成本复盘", "", "原始数据、候选冻结和调用证据已核对。以下正确性结果均为模型评分，人工标签为空。", "",
        "| 方法 | 任务 | 就绪且接受 | 调用 | 总 token | 每分配任务 token | 每成功任务 token |", "|---|---:|---:|---:|---:|---:|---:|"]
    for method,v in methods.items():
        per_success = round(v["total_tokens"] / v["ready_and_accepted"]) if v["ready_and_accepted"] else "未定义"
        lines.append(f"| {method} | {v['assigned']} | {v['ready_and_accepted']} | {v['calls']} | {v['total_tokens']} | {round(v['total_tokens']/v['assigned'])} | {per_success} |")
    lines += ["", "原证明对照不是修复方法；上述成功列不是仅以缺陷证明为分母的修复率。失败和不确定任务均保留在分母中。", "",
        "## 未就绪任务", "", "| 题目 | 方法 | 分类 | 最后阶段 | token | 原因 |", "|---|---|---|---|---:|---|"]
    for r in details:
        if r["terminal_status"] != "proof_ready":
            reason = r["stop_reason"].splitlines()[0].replace("|", "/")
            lines.append(f"| {r['case_id']} | {r['method']} | {r['failure_category']} | {r['attempts'][-1]['phase']} | {r['total_tokens']} | {reason} |")
    lines += ["", "逐调用成本、完整错误、原始证据路径见 [tasks.json](tasks.json)，可筛选表见 [tasks.csv](tasks.csv)。", "",
        "审核分歧见 [summary.json](summary.json)。人工只分发 human/public；human/private 中含方法映射，须对审核者隐藏。", "",
        "各调用延迟的加和表示服务工作量，不等于并行运行的墙钟时间。美元价格未知，未换算费用。", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return summary
