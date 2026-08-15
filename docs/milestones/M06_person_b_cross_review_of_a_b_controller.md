# M6 Person B：A/B/Controller 执行与复现交叉审查 v0.1

状态：`person_b_engineering_cross_review_passed_human_signature_pending_m5_entry_blocked`。本记录从 Person B 的实验实现、失败留痕、配置隔离和复现职责审查 M6 全部 fixture 表面。它不是具名真人签名，也不把 M5 `m6_entry_allowed=false` 攛改为开放状态。

## 1. 审查范围与边界

- Person A 的 RQ、数学定义、方法权限、公平预算、失败分母、统计 family 与盲态案例模板；
- Person B 九方法规格、消融纯度、配置身份、缓存隔离、Gold 字段与指标实现；
- Controller artifact/配置/样本冻结、运行账本、重试历史、预算、聚合与统计；
- README、ROADMAP、PROJECT_INDEX、CHANGELOG、执行顺序及 M5→M6→M7 阶段门。

审查只使用代码、fixture 与仓库文本。它不能证明真实审核者身份、未见结果、数学判断正确、模型版本稳定或外部服务记录完整。

## 2. Person B 发现并修复的问题

1. **P1：聚合结果未绑定 Controller Manifest。** 旧 `aggregate_by_experiment` 接受任意 experiment ID、任意样本子集，可能把越权配置或有利子集计入结果。现聚合前重验 Manifest，只接受精确配置×样本分配，每对必须且只能出现一条终态数学记录。
2. **P1：机制不适用被错误表示为数值。** 不产补丁的普通基线和禁用反例协议的方法仍会输出 repair/counterexample 指标，违反 Person A 的 `not_applicable` 规则。现根据冻结 `MethodSpec` 机械覆盖为 `not_applicable`，不再以 0 或 `undefined` 冒充适用指标。
3. **P1：Manifest artifact 键可逃逸仓库。** `freeze_artifacts` 会拒绝逃逸，但 `build_controller_manifest` 可直接接收 `../outside` 或绝对路径及自报摘要。现 Manifest 同样要求规范化仓库相对路径；正式版本仍须从 `freeze_artifacts` 的可信输出构建并验证实时文件。
4. **P2：主动弃权率被基础设施失败稀释。** 旧 `proof_abstention_rate` 以全部 ITT 样本为分母，却不把超时/API 错误计为弃权，因而故障越多弃权率越低。现分母只含成功产生数学 verdict 的记录，并显式报告排除的基础设施失败数；失败率仍以完整 ITT 为分母。
5. **P1：评分记录未绑定运行账本终态。** 即使配置与样本属于 Manifest，旧聚合器仍可另造一条与真实终态状态不同的数学记录。现聚合必须同时提供完整账本；评分记录绑定精确 terminal `run_id`，成功对应 `failure_type=null`，失败类型必须与账本终态一致。

## 3. 对 Person A 的审查结论

- RQ1–RQ3、主要安全指标、适用集合、失败处理及 H1/H2/H3 family 已可由当前 fixture 机械映射。
- Gold `gap→accepted_with_gap` 不计 unsupported resolution；`gap→accepted` 与 `undetermined→accepted/accepted_with_gap` 才计入，代码与协议一致。
- 盲态模板应在真实执行时由 Controller 生成匿名包并绑定实际序列化输入；当前空白模板不能证明盲态或泄漏不存在。
- Person A 协议仍是候选内容和自述未见结果证据，真实摘要签名、身份与独立性必须由仓库外可信流程完成。

## 4. 对 Person B 的审查结论

- 九方法 suite、三组完整确认性 comparison、五个消融的精确差异、同/异模型角色绑定、逐方法 Prompt 摘要与共享运行资产均由配置校验器约束。
- experiment ID 与缓存 fingerprint 覆盖方法、模型、Prompt、数据、定理库、工具、代码、评分器、Schema、采样、截断、预算、样本和精确序列化输入。
- 当前没有 provider runner、真实 Prompt 包、统一 tokenizer/truncator 或 smoke 输出，因此只能称为 experiment surface，不能称为九种方法已经在真实模型上实现或完成。

## 5. 对 Controller 的审查结论

- fixture Manifest、账本、预算累计、失败保存、配对 bootstrap CI、paired randomization p 值和完整 Holm family 已有确定性测试。
- Controller v0.1 对正式 Manifest 无条件 fail closed 是正确边界；仅传 `true`/`signed` 不具备授权效力。
- 正式版本仍需可信读取 live M5 artifact、核验 detached signatures、公钥/算法/身份、冻结 10,000+10,000 seed 与统计库、验证 artifact 当前字节，并保存原始 provider 调用和账单关联。

## 6. 跨文档一致性与退出决定

README、ROADMAP 和 PROJECT_INDEX 均应表述为：Person A 与 Person B 的 fixture 工程交叉审查已通过；真人签署、M5 人工门、可信签名验证器、provider smoke/Pilot/正式运行及 M6 整体退出均未通过。不得把 fixture 测试数、候选摘要或同一 Agent 自检写成外部/人工证据。

退出决定：**Person B 视角的 M6 fixture 工程交叉审查通过；真实 M6 执行、M6 总退出和 M7 入口继续阻塞。**
