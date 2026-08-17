# M7 Person B：A/B/Controller 执行与复现交叉审查 v0.1

状态：`fixture_engineering_cross_review_passed_after_repairs_formal_m7_blocked`。本记录从 Person B 的数据、配置、运行、成本、失败保留和复现职责审查 M7 Person A、Person B 与 Controller 全部现有内容。它不是具名真人签名、独立盲态证据或正式实验结果。

## 1. 审查范围与角色边界

- Person A 协议和逐例模板：数学 Gold、首错、反例、repairability、最终 Gold 审计、盲态错误分析和 erratum；
- Person B 数据与实验工程：来源/许可、Schema、重复/泄漏、配置族、运行矩阵、失败和成本；
- Controller：实际字节冻结、上游绑定、完整分配、全局运行身份、结果绑定、预算、聚合、盲审计划与回放；
- 三方 Manifest、Schema、测试及 README/ROADMAP/PROJECT_INDEX/CHANGELOG 状态一致性。

Person B 不代签 proof verdict、首错、反例或补丁的数学接受；Controller 不以 JSON、hash 或统计结果替代数学裁决。

## 2. 已确认正确的边界

1. 三方均保持 `m7_execution_allowed=false`，调用者布尔值、普通摘要或字符串签名不能开放真实运行。
2. Person A 的 200–500 数量门、A/B 独立锁定、第三专家裁决、最终 Gold 审计、三类严重错误全量审核和公开 erratum 规则完整。
3. Person B 候选拒绝受限许可、精确重复、无效近重复输入、未解决 critical finding、混合配置族、不完整九方法矩阵、重复分配、删除失败终态和族内重复 run ID。
4. Controller 强制至少一个同模型族与一个异模型族，逐 case 覆盖九方法，绑定终态、原始输出和评分输入，重建资源聚合并确定性抽取回放样本。

## 3. 本轮发现并修复的问题

1. **P1：`run_id` 只在单模型族内唯一。** 相同 `run_id` 可同时出现在同模型与异模型族，运行完整性仍返回成功，回放样本甚至出现重复身份。现运行完整性、聚合和回放入口均要求 Manifest 全局唯一，并增加跨族碰撞攻击测试。
2. **P1：Manifest 只验证 artifact 摘要形状与自身重建，不验证实际文件字节。** 调用者可用不存在路径和任意合法 SHA-256 构建自洽 Manifest。现构建及每次验证都必须给出 repository root，重读全部 artifact 以及固定 A/B 上游 Manifest；不存在、陈旧、替换或路径逃逸均失败闭合。
3. **P1：Person A 要求的盲审抽样与匿名包只有文字规则。** 原 Controller 只有成功 run 的复现抽样，不能机械保证全部 false accept、错误全局反例、false repair 和四类对照样本。现新增确定性盲审计划，保存完整 frame、入选/未入选集合、公开计划摘要与独立密封映射；公开内容不泄漏真实配置 ID。

## 4. 仍未完成但未被冒充完成的事项

- M5/M6 真人门、可信 detached-signature 验证器和 `m7_entry_allowed=true` 退出记录；
- 真实 200–500 题、来源许可、外部污染检索、A/B 独立标注、第三专家裁决和 Gold 冻结；
- provider 原始尝试/重试记录、模型快照、统一截断器、价格与外部账单；
- M6 预注册数学指标、paired bootstrap CI、randomization p 值、Holm、分层与稳定性分析；
- 真正隔离的盲审包交付、人工锁定/签名、揭盲控制和独立目录回放。

这些项目需要真实数据、模型、人员或外部证据，当前正确状态仍是 pending，不能用 fixture 补造。

## 5. 退出决定

Person B 视角的 M7 三方 **fixture 工程交叉审查在三项 P1 修复后通过**。当前协议和确定性 fixture 已达到下一次真人/正式门审查所需的工程边界；M7 正式 Benchmark、Gold、主实验、统计、盲审、复现和整体退出继续为 `blocked_not_executed`，不得进入 M8 强量化主张。
