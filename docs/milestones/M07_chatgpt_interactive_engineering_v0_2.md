# M7：ChatGPT 交互式工程验收 v0.2

状态：`interactive_engineering_complete_formal_experiment_blocked`。

本阶段依照用户授权暂缓逐题密码学签名，只推进交互式工程。构建器从 M6 已冻结的 50 题、九方法、450 个终态确定性生成 M7 双模型族表面：`same_model` 与 `different_models` 各含完整九方法，共 900 个终态、900 个结果字节绑定、18 行资源聚合和 20 个确定性回放样本。缺失、重复、跨族 `run_id` 冲突、结果与终态不一致或超预算均失败关闭。

v0.2 同时生成匿名盲审公开计划、按摘要寻址的审核载荷和单独密封的实验配置映射。公开包不出现方法、模型族或 Gold 决定；所有 false accept、错误全局反例和 false repair 必须进入审核框，正确裁决、修复成功、未决和基础设施失败则按冻结 seed 每配置最多抽取 20 个。当前只准备审核材料，`blind_review_completed=false`，不代填真人裁决。回放验证报告只证明相同仓库字节可确定性重建并抽取相同成功终态，明确记录 `provider_replay_performed=false`。

`different_models` 只是检验跨模型族配置、身份、账本、聚合和回放的工程标签；它没有产生第二套独立预测。两族都投影同一份历史 M6 输出，Gold 已暴露，Provider 调用、token、延迟和成本均为零。因此不执行配对置信区间、随机化检验、Holm 校正或模型族比较，不允许科学优势或正式多模型实验主张。

当前 50 题也不是正式 M7 所需的 200–500 题新 Benchmark。正式 M7 仍需新数据的来源/许可/去重/泄漏审核、A/B 独立 Gold、第三专家裁决、真实同/异模型 Provider 运行、原始响应和账单、预注册统计、盲态错误分析及独立目录回放。

交互式工程阶段可以继续用于完善 M7 管线、审计界面和未来 Provider 适配器；`formal_m7_experiment_allowed=false` 与 `scientific_claim_allowed=false` 必须保持关闭。
