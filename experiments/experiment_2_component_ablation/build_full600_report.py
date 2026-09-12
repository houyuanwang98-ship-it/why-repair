"""Render the full-600 summary tables from full600_results.json."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = {
    "no_agent": "无 Agent（原证明）",
    "single_agent": "单 Agent（直接重写）",
    "single_agent_self_refine": "单 Agent + Self-Refine",
    "dual_agent": "双 Agent（Generator–Critic）",
    "dual_agent_controller": "双 Agent + Controller（完整系统）",
}


def pp(value):
    return f"{100 * value:.2f}%"


def main():
    data = json.loads((HERE / "full600_results.json").read_text(encoding="utf-8"))
    methods = data["methods"]
    baseline = methods["no_agent"]["acceptance_rate"]
    lines = [
        "# 实验2：600题组件消融结果",
        "",
        "> 状态：已完成。下表来自600个唯一原项目题目、5种配置、共3000个逐题盲审判断。",
        "",
        "## 主结果",
        "",
        "| 配置 | n | 通过数 | 严格接受率 | 相对无Agent提升 | 问题保持率 | 平均错误数 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in LABELS:
        row = methods[method]
        delta = row["acceptance_rate"] - baseline
        lines.append(
            f'| {LABELS[method]} | {row["n"]} | {row["accepted"]} | {pp(row["acceptance_rate"])} | '
            f'{delta * 100:+.2f} pp | {pp(row["problem_preserved"] / row["n"])} | {row["mean_error_count"]:.3f} |'
        )
    lines += [
        "",
        "严格接受定义为：独立盲审同时给出 `valid`、`problem_preserved=true`、`rigorous=true`。",
        "这些数值是固定模型盲审接受率，不冒充人工正确率；`human_verified=false`。",
        "",
        "## 可复核证据",
        "",
        f'- 逐题记录：`{data["case_evidence"]}`（SHA-256 `{data["case_evidence_sha256"]}`）',
        "- 每道题包含原证明以及4个匿名候选的独立判断；候选顺序按题号与方法名哈希打乱，评分时不暴露方法身份。",
        "- 600题由 M2 Pilot 50、M2 B50 50、Open Proof Corpus 250、ProofNet 250 组成。",
        "",
    ]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    report = [
        "# 实验2报告：双Agent与Controller组件消融（600题）",
        "",
        "## 目的",
        "",
        "在同一批600道原项目证明、同一生成模型与同一盲审器下，控制工作流组件，比较无Agent、单Agent、双Agent以及双Agent+Controller。另设单Agent+Self-Refine，区分“增加一次自检”与“引入独立批评者/控制器”的贡献。",
        "",
        "## 公平性控制",
        "",
        "所有配置共享原题、定理、假设与领域。一次生成调用同时返回4种完整候选，避免分批运行造成时间和服务状态偏差；随后独立评分模型看到原证明与打乱顺序的匿名候选，不看到配置名称。主指标使用同一严格接受规则。",
        "",
        "## 结果",
        "",
        "完整数表见 `RESULTS.md`。逐题证据和哈希均随实验提交，可从原始判断重新计算全部数字。",
        "",
        "## 项目独特改进点",
        "",
        "- 双Agent将生成与批评分开，降低单Agent自证偏差。",
        "- Controller提示显式包含依赖感知的错误证书、最小局部修复、独立式复核与后继重验证。",
        "- 问题保持与严谨性单独计入通过门槛，避免通过改题或弱化结论获得虚假提升。",
        "- 逐题匿名映射与盲审使方法身份不参与判分。",
        "",
        "## 限制",
        "",
        "该实验衡量的是固定模型评审下的端到端工作流效果，不是人工金标准正确率；同一次调用生成四个候选可能带来配置间相关性。Controller组是端到端提示化工作流消融，不能单独证明每个内部机制的因果贡献。后续应增加人工抽检、重复随机种子和置信区间。",
        "",
    ]
    (HERE / "REPORT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
