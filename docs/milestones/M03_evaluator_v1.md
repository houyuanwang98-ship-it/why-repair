# M3 Evaluator v1

> 2026-08-14 复核说明：下文是历史冻结说明。“退出条件均已满足”仅适用于当时的非盲工程验收，不满足两份总体验收文件要求的发布级严格门。当前权威结论、补充指标和证据缺口见 `M03_full_revalidation.md`。

状态：`m3-evaluator-v1.0` 已于 2026-08-14 冻结。

## 1. 目标

M3 将现有自然语言代数 checker 接到冻结的 M2 Gold，并分别衡量：

- 证明级有效性状态；
- 错误类型；
- 第一处缺口和第一处无效步骤；
- 节点类型；
- 节点裁决组；
- 直接依赖边。

本阶段不训练模型，也不把确定性规则基线的低分解释为最终 Evaluator 能力。模型或人工 host adjudication 必须使用同一输入、输出契约和指标脚本。

## 2. 数据与覆盖

- 输入样本：50；
- 证明级 Gold：50；
- 节点级 Gold：39 个证明、98 个节点；
- 直接依赖边：58；
- 11 个已由全局反例终止过程审查的证明不计算节点指标，但仍计算证明级指标。

节点类型归一规则：Person A 的 `calculation` 映射为 checker 的 `calculation_step`，`citation` 映射为 `introduction`。节点数学裁决压缩成 `accepted / gap / invalid / undetermined`，避免把生命周期状态混入数学指标。

## 3. 实现

- `scripts/prepare_m3_checker_input.py`：把 M2/M3 行转换成 checker 输入；
- `scripts/m3_evaluator.py`：读取 JSONL 或逐题 JSON 目录并生成模块化指标；
- `schemas/m3_evaluator_report_v0_1.schema.json`：报告契约；
- `data/benchmarks/m3/gold/evaluator_pilot_v1.jsonl`：Evaluator v1 Gold；
- `data/benchmarks/m3/gold/evaluator_pilot_v1.manifest.json`：Gold 摘要；
- `data/benchmarks/m3/reports/deterministic_v1.json`：无模型确定性冒烟基线。

指标对缺失预测采用失败闭合：预测覆盖率单独报告，同时缺失项在准确率中计错，不因跳过困难样本提高分数。首错定位只在相应 Gold 位置存在时计算 exact accuracy，并对不应报告位置的样本单独计算假阳性率。依赖边采用微平均 precision、recall 和 F1。

## 4. 确定性冒烟基线

无模型、`uncertain-policy=undetermined` 的结果为：

- 预测覆盖率：1.000；
- 证明有效性 accuracy：0.120；macro-F1：0.110；
- 错误类型 accuracy：0.060；macro-F1：0.049；
- 节点类型 accuracy：0.439；macro-F1：0.152；
- 节点裁决组 accuracy：0.398；macro-F1：0.290；
- 依赖边 precision：0.932；recall：0.948；F1：0.940；
- 第一处缺口 exact accuracy：0.091；
- 第一处无效步骤 exact accuracy：0.077。

该结果证明整条评测管线可执行，也清楚显示确定性 checker 大量弃权，不能替代后续模型裁决。

## 5. 人工验收

1. 确认 50 个 M3 输入与冻结 M2 样本逐题同源；
2. 抽查含节点 Gold 的题目，确认 `node_id`、节点类型与直接依赖；
3. 确认全局反例终止的 11 题没有伪造节点 Gold；
4. 用完整预测、删除一条预测、加入错误首错位置三种 fixture 检查指标行为；
5. 重跑全套单元测试；
6. 模型支持的 Evaluator 运行完成并人工抽查前，不冻结 M3。

## 6. 当前状态与退出条件

以上退出条件均已满足。全 50 题运行、分歧人工审计、已知 benchmark
缺陷和冻结哈希见 `M03_freeze_record.md`。M3 的冻结版本为
`m3-evaluator-v1.0`；后续修改必须启用新版本，不得覆盖冻结工件。
