# 实验2方法

## 受控配置

| 配置 | 工作流 | 目的 |
|---|---|---|
| no_agent | 原证明原样送审 | 原始基线 |
| single_agent | 单次直接重写 | 单Agent贡献 |
| single_agent_self_refine | 单Agent起草、自检、修订 | 额外自检贡献 |
| dual_agent | Generator–Critic | 独立批评角色贡献 |
| dual_agent_controller | 双Agent，加依赖感知错误证书、最小局部修复、复核与后继重验证 | 完整项目工作流贡献 |

## 控制变量

600题、题干、假设、领域、生成模型、生成推理档位及盲审器完全一致。一次生成请求为同一题返回4个候选，减少不同时段服务状态造成的混杂。评分阶段按题号和方法名哈希打乱候选顺序，仅暴露 `candidate-N`，不暴露方法身份。

生成模型为 `gpt-5.6-luna`（low），独立评分模型为 `gpt-5.6-terra`（medium）。模型禁止使用工具和仓库文件。评分器同时评价原证明，故无Agent基线与修复组使用相同口径。

主指标为 `verdict=valid AND problem_preserved=true AND rigorous=true` 的比例。辅助指标包括问题保持率、判定分布和平均错误数。只有600题全部完成才生成正式汇总。

本实验是固定模型盲审，不是人工金标准评测；`human_verified=false`。四候选在同一请求中生成，配置结果相关，差值不解释为每个内部机制的严格独立因果效应。
