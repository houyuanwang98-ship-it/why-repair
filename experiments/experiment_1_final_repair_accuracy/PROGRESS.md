# 实验1全量运行进度

更新时间：2026-09-12（Asia/Shanghai）

## 当前进度

- 数据集：600/600 题已整理。
- 四种方法的候选证明：600/600 题已生成（每题4个候选，共2400个）。
- 独立盲评：600/600 题已完成（100%）。
- 剩余：0题。
- 最后一批题号 `opc250-223`、`opc250-226`、`opc250-228`、`opc250-230` 已补跑成功。

## 所处步骤

全量模型运行、独立盲评、结果聚合和完整性检查均已完成。600题均具有候选生成、匿名映射和独立判定文件；汇总表包含原证明及四种方法，共3000条比较记录。

## 当前快照说明

- 生成模型：`gpt-5.6-luna`，reasoning effort 为 low。
- 独立判定模型：`gpt-5.6-terra`，reasoning effort 为 medium。
- 四种方法：`direct_rewrite`、`self_refine`、`generator_critic`、`full_system`。
- 严格成功口径：判定为 `valid`，同时 `rigorous=true` 且 `problem_preserved=true`。
- 新生成修复结果尚未经过人工逐题金标，因此当前模型判定只能作为实验中间结果，不能冒充人工准确率。

机器可读运行摘要见 `runs/full600_v1/run_summary.json`；全部题目的生成结果、匿名映射和判定结果保存在相应题号目录。最终汇总见 `aggregate_results.json` 和 `FULL_RESULTS.md`。
