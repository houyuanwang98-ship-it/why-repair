# 实验2：600题组件消融结果

> 状态：已完成。下表来自600个唯一原项目题目、5种配置、共3000个逐题盲审判断。

## 主结果

| 配置 | n | 通过数 | 严格接受率 | 相对无Agent提升 | 问题保持率 | 平均错误数 |
|---|---:|---:|---:|---:|---:|---:|
| 无 Agent（原证明） | 600 | 167 | 27.83% | +0.00 pp | 96.67% | 1.298 |
| 单 Agent（直接重写） | 600 | 367 | 61.17% | +33.33 pp | 98.00% | 0.495 |
| 单 Agent + Self-Refine | 600 | 368 | 61.33% | +33.50 pp | 98.00% | 0.460 |
| 双 Agent（Generator–Critic） | 600 | 372 | 62.00% | +34.17 pp | 98.00% | 0.455 |
| 双 Agent + Controller（完整系统） | 600 | 379 | 63.17% | +35.33 pp | 98.00% | 0.420 |

严格接受定义为：独立盲审同时给出 `valid`、`problem_preserved=true`、`rigorous=true`。
这些数值是固定模型盲审接受率，不冒充人工正确率；`human_verified=false`。

## 可复核证据

- 逐题记录：`full600_case_judgments.jsonl`（SHA-256 `0e643769e4a446f5891402cc73451f52ca18e0dadbf41ffab4e1489874109ab1`）
- 每道题包含原证明以及4个匿名候选的独立判断；候选顺序按题号与方法名哈希打乱，评分时不暴露方法身份。
- 600题由 M2 Pilot 50、M2 B50 50、Open Proof Corpus 250、ProofNet 250 组成。

## 配对变化

| 对比 | 失败→通过 | 通过→失败 | 净增通过题 | 配对差值 | exact McNemar p |
|---|---:|---:|---:|---:|---:|
| `single_agent_vs_no_agent` | 209 | 9 | +200 | +33.33 pp | 0.0000 |
| `single_agent_self_refine_vs_single_agent` | 17 | 16 | +1 | +0.17 pp | 1.0000 |
| `dual_agent_vs_single_agent_self_refine` | 15 | 11 | +4 | +0.67 pp | 0.5572 |
| `dual_agent_controller_vs_dual_agent` | 12 | 5 | +7 | +1.17 pp | 0.1435 |
