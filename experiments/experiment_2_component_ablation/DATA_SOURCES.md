# 实验2数据引用

## 队列定义

采用 `data/manual_validation/person_b_step05_case_results.jsonl` 的全部300个case_id，保留原始审核清单的纳入范围。参考同目录 `person_b_step05_completion_record.json` 验证分组计数。

| 组别 | 纳入 | 原始文件 |
|---|---:|---|
| M2 B50 | 25 | data/benchmarks/m2/source/pilot_B50.jsonl |
| M2 工程Pilot | 25 | data/benchmarks/m2/source/pilot_50.jsonl |
| OPC-250 v0.2 | 123 | data/benchmarks/m7/opc_250_v0_2/candidate.jsonl |
| ProofNet-250 v0.1 | 127 | data/benchmarks/m7/proofnet_250_v0_1/candidate.jsonl |

300是这一审核清单的规模，不等于全部源文件的总记录数，也不是250道OPC加50道M2。以清单ID逐题join源文件，缺失、重复ID、空问题或空证明都报错；同内容重复仅报告，不擅自删除原清单题目。

## 转换规则

M2的theorem作为problem，assumptions原样保留，proof_steps按原顺序以换行连接text。OPC和ProofNet的problem/proof原文不改。四个数据集都不将领域、来源split、Gold、错误计划、旧Agent判断及私有形式化字段传入模型。

## 来源与许可

OPC冻结上游：insait-institute/open-proof-corpus，commit `e92a6ca848e50f5d3f9c2a1393da72720760d931`，Apache-2.0。ProofNet冻结上游：zhangir-azerbayev/ProofNet，commit `509ad79710ed4f46ff5c282ed5640c1aa9ac3f30`，MIT。许可文件位于相应数据目录，并纳入source_manifest。未重新下载网络数据。

## 评分证据限制

300条“与节点Agent一致”是审核确认，不是300个修复成功标签。148题具有可访问的历史Agent引用文件；152题未单独归档。可访问文件也不能当作新方法的输出。

ProofNet manifest声明其为原始证明来源、错误派生和数学Gold待标注；不能将derivation_plan中的计划错误类别当成原证明已经包含的真实错误。OPC节点定位中含AI预填与待核对条目。因此完整300题的统一、独立最终证明评分尚未具备。

source_manifest冻结本次读取的源文件字节，case_audit保存每题输入摘要与来源。新生成的输入和运行计划不计为模型结果。
