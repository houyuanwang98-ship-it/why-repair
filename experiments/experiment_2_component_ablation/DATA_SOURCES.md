# 实验2数据引用

纳入 Person A 与 Person B Step 5 清单并集的600个唯一 `case_id`，逐题连接项目内冻结源文件：

| 数据组 | 数量 | 原始文件 |
|---|---:|---|
| M2 B50 | 50 | `data/benchmarks/m2/source/pilot_B50.jsonl` |
| M2 Pilot | 50 | `data/benchmarks/m2/source/pilot_50.jsonl` |
| OPC-250 v0.2 | 250 | `data/benchmarks/m7/opc_250_v0_2/candidate.jsonl` |
| ProofNet-250 v0.1 | 250 | `data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl` |

队列依据为 `data/manual_validation/person_a_step05_case_results.jsonl` 和 `data/manual_validation/person_b_step05_case_results.jsonl`。`source_manifest.json` 固定源文件SHA-256，`case_audit.json` 保存每题来源、输入摘要与分组。

M2使用原 `theorem`、`assumptions`，并按顺序连接 `proof_steps.text`；OPC与ProofNet使用冻结的 `problem` 与 `proof` 原文。Gold、旧Agent结论、错误派生计划和人工审核字段不进入生成输入。ProofNet 的 `derivation_plan` 不被误当作原证明真实错误标签。

OPC许可为 Apache-2.0，冻结上游提交 `e92a6ca848e50f5d3f9c2a1393da72720760d931`；ProofNet许可为MIT，冻结上游提交 `509ad79710ed4f46ff5c282ed5640c1aa9ac3f30`。许可文件及候选文件均列入来源清单。
