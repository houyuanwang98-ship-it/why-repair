# M5/M6 项目负责人验收清单

本清单供项目负责人审核新协作者的复现、Provider runner、M5 pilot 和 M6 实验。负责人不重复高成本全量调用，只抽查关键证据和运行少量 smoke。

## A. 接收运行前

- [ ] commit、分支和工作区状态已记录。
- [ ] 输入样本、顺序和 SHA-256 已冻结。
- [ ] 模型精确 ID、Provider、采样参数和日期明确。
- [ ] Prompt、Schema、评分器、工具、代码和截断器摘要齐全。
- [ ] token、调用、超时、重试、补丁轮次和总成本上限明确。
- [ ] fixture、smoke、formal 使用不同 run ID 和目录。
- [ ] API 凭据不进入仓库、Prompt、响应或日志。
- [ ] 失败保留、停止规则和缓存隔离已在测试中验证。

## B. Provider runner PR

- [ ] 原始响应不可被解析器覆盖。
- [ ] attempt ID 唯一，重试能追溯上一 attempt。
- [ ] response ID、token、延迟、错误与成本字段来自 Provider 或明确标为 unavailable。
- [ ] 超时、API 错误、拒绝、Schema 错误和重试耗尽均有记录。
- [ ] 无响应时不会产生数学预测或伪造 token=0。
- [ ] 缓存指纹包含方法和全部冻结配置。
- [ ] 不同 M6 方法不能读取彼此缓存。
- [ ] Repair Generator 无权写 PatchReview、accepted 或 verified success。
- [ ] 有正例、失败、超时、重试、缓存错配和越权输出测试。

## C. M5 smoke/pilot

- [ ] 输入只含允许上下文，无 Gold 修复或 Person A 隐藏 Prompt 泄漏。
- [ ] PatchProposal 精确绑定 proof/node/version/ErrorCertificate。
- [ ] 新增假设或改变问题不会计为成功修复。
- [ ] 补丁由独立数学审核者接受或拒绝。
- [ ] 修改节点后全部受影响后代失效并按拓扑重验。
- [ ] patch accepted 与 verified repair success 分开记录。
- [ ] false repair、新错误、等价循环、最大轮次和 irreparable 分别计数。
- [ ] 至少抽查一个成功、一个失败、一个重试、一个拒绝和一个 irreparable。

## D. M6 九方法 smoke

- [ ] 九种方法完整且只改变预注册字段。
- [ ] 比较方法使用相同模型族、样本、预算、Prompt 版本策略和评分器。
- [ ] 每个样本都保留在 intention-to-treat 分母中。
- [ ] 基础设施失败与主动 `undetermined` 分开。
- [ ] 无补丁/反例能力的方法对应指标为 `not_applicable`。
- [ ] 0、`undefined (0/0)`、`not_applicable` 和 `undetermined` 未混用。
- [ ] 聚合指标可从 ledger 独立重算。
- [ ] 共享历史预测没有被冒充为独立模型结果。

## E. 批准扩大运行的最低条件

只有以下条件同时满足，才批准从 smoke 扩大：

- [ ] Provider runner PR 已独立审查并合并。
- [ ] 小样本原始记录和聚合能完全重放。
- [ ] 预算与成本上限获得负责人确认。
- [ ] 失败样本没有删除或成功覆盖。
- [ ] 缓存隔离攻击测试通过。
- [ ] M5 独立数学审核流程可执行。
- [ ] M6 正式配置在查看正式结果前冻结。
- [ ] 结论模板明确：工程结果与科学结果分开。

## F. 负责人本机只需抽查

负责人无需重复完整 Provider 批次，只需：

1. 检查 Git diff、配置和 manifest；
2. 随机核对 3–5 个原始 attempt；
3. 运行 Controller、预算、缓存和评分单元测试；
4. 独立复算一小批聚合指标；
5. 对一个修复成功和一个失败案例做数学抽查；
6. 确认未修改冻结 Gold、历史 manifest 或指标定义；
7. 给出 accepted / needs_revision / rejected 决定。

