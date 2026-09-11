# 实验2数据来源

## 主队列

主消融沿用实验1的21个不同证明，不重新选择样本：

- `experiments/experiment_1_final_repair_accuracy/results.json`：逐题Gold状态、最终结果、轮数与证据路径；
- `data/benchmarks/m2/gold/algebra_pilot_v1.jsonl`：原证明Gold状态；
- `data/manual_validation/person_a_step06_completion_record.json`：21题审核完成记录与14/7终态汇总；
- `data/benchmarks/m5/provisional_codex_interactive_v1/<proof_id>.completion.json`：Controller终止原因、修复轮数与重验序列；
- 同目录的 `patch(.r2).json`：局部补丁操作；
- 同目录的 `person_a_review(.r2).json`：问题保持、无新增错误、操作最小性和接受结果。

## 单 Agent 诊断补充集

`data/benchmarks/m3/revalidation/full50_report_v0_2.json` 提供冻结50题诊断指标：证明有效性准确率、错误类型准确率、首错定位和依赖边F1。该数据集只用于说明单 Evaluator Agent 的诊断能力，不进入21题最终修复率的四行主表。

## 冻结与校验

`source_manifest.json` 保存本实验实际读取的全部源文件SHA-256。`rebuild.py --check` 会重新读取源文件、验证21题身份、Gold状态、修复轮数、Controller终态和审核结果，并检查生成文件是否过期。

## 证据等级

- 原证明状态：冻结Gold记录；
- 单轮结果：对完整历史轨迹的第一轮截断重构；
- 完整结果：实验1中已同步人工审核的终态；
- 人工安全指标：项目所有者确认后同步的审核记录；
- 新模型调用：0。

M6的 `chatgpt_interactive_full50_v0_2` 明确记录 `provider_model_calls=0` 且为Gold暴露的历史重放，因此没有被用来填充本实验四行修复率主表。工程fixture也没有被当成论文数据。
