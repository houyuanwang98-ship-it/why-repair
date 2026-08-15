# M6 Person B：基线、消融与实验工程候选 v0.1

状态：`person_a_engineering_cross_review_passed_fixture_only`。本交付只机械化 Person A 的两份内容已锁定、待真人签署的 Markdown，不运行 Pilot 或正式实验，不产生可用于论文的模型结果。当前 `data/benchmarks/m5/joint_acceptance_v0_1.json` 仍为 `m6_entry_allowed=false`；真实运行必须 fail closed。

## 1. 方法实现面

`harness/m6_experiments.py` 注册九种配置：`direct_judgment`、`self_reflection`、`generator_critic`、`no_graph`、`no_structured_certificate`、`no_counterexample_protocol`、`no_descendant_invalidation`、`single_round_repair` 与 `full_system`。每个配置显式声明节点、图、结构化证书、反例协议、后代失效、补丁与轮次权限。`validate_ablation_purity` 固定五个因果消融相对完整系统的精确字段差异；意外多删或多开组件会停止运行。

普通三基线仅参与 RQ1；证书/反例消融参与 RQ2；具备补丁接口的无图、无后代失效、单轮修复参与 RQ3。代码分别要求主 Manifest 含完整九配置、每个确认性比较含该 H 的完整预注册方法集合，拒绝跨 RQ 拼接或事后遗漏不利基线。`direct_judgment` 不因缺少补丁而被记作修复失败或进入 repair 分母。

## 2. 预注册预算候选

以下数值是结果前候选，须经 Person A 复核并由 Controller 绑定 Manifest 后才可运行。所有额度均为每样本硬上限，不跨样本转移。

| 字段 | 候选值 | 强制规则 |
|---|---:|---|
| 输入+输出 token | 8,000 | 所有主要比较相同；结构化序列化计入 |
| 模型调用 | 4 | 未用额度不转移；完整系统不得隐藏追加 |
| 墙钟超时 | 180 秒 | 所有配置相同 |
| 技术重试 | 1 次 | 保留首轮失败、成本和关联 run ID |
| 补丁轮次 | 3（单轮消融为 1） | 这是目标消融差异，不改变总 token/call 上限 |

同模型双角色和异模型双角色使用不同配置族，不混合解释。模型 ID/快照、采样参数、上下文窗、价格表与统一截断器尚未冻结，因此当前不得声称预算表已获签或可执行。

## 3. 功效分析预注册输入候选

在不知道正式结果的前提下，Person B 提交如下输入供独立复核：H1 以首错精确率基线 0.55、最小有意义绝对提升 0.10；H2 以有效反例覆盖率基线 0.40、最小提升 0.12；H3 以 verified repair success 基线 0.35、最小提升 0.12。双侧 `alpha=0.05`，每个 H 内 Holm 校正，目标 power 0.80，以样本为配对单位。配对不一致率和指标适用样本占比必须由开发集或外部先验估计；在这些输入冻结并完成正式计算前，确认性运行保持阻塞。不得用测试结果反推或放宽阈值。

## 4. 运行、缓存和失败边界

- `build_experiment_config` 由完整方法、generator/critic 模型、Prompt、数据、定理库、工具、代码、评分器、输出 Schema、采样、截断器和预算内容生成唯一实验 ID；所有 digest 强制为小写 64 位 SHA-256，同模型与异模型角色绑定由代码校验。
- `validate_experiment_config` 重新计算实验 ID 并匹配冻结方法规格，生成后的任何篡改都会被拒绝。
- `validate_experiment_suite` 要求一个模型/角色配置族完整包含九种方法；`validate_comparison` 要求一个 H family 完整无缺。两者均要求模型组合、角色模式、数据摘要、定理库、工具实现、代码、评分器、Schema、采样、截断器和硬预算一致。
- `cache_fingerprint` 绑定上述完整配置、样本和精确序列化输入，禁止跨方法或跨配置复用响应。
- `assert_execution_allowed` 仅放行未接触模型的 fixture 计算；v0.1 没有可信 detached-signature 验证器，故真实运行即使收到调用者自报的 `true`/`signed` 也一律拒绝。
- 每个分配样本保留在 intention-to-treat 集合。API、超时、预算、Schema、工具和重试耗尽均为显式失败类型；不能静默删除或覆盖。

## 5. 手算 fixture 验收

`tests/test_m6_person_b_experiments.py` 手算验证首错 exact、Gold 无首错时的位置假阳性、false accept、unsupported resolution、false-claim detection、反例覆盖/候选精确率、abstention、verified repair success、false repair、新错误引入率及错误总数和基础设施失败率。基础设施失败对 accuracy/repair success 记未成功，对错误输出比例不虚构数学错误，并同时计算最坏情形上界；主动 `undetermined` 的 abstention 分母只含成功产生数学输出的记录，并另报排除的基础设施失败数。零分母必须为 `undefined (0/0)`。失败记录携带数学输出、verified success 缺少完整先决条件、false repair 未先宣称成功、反例计数或新错误计数矛盾时均拒绝计分。方法无权生成补丁或反例协议时，对应机制指标标为 `not_applicable`。

当前覆盖 Person A 候选协议中可机械化的主要口径；Controller 已实现 paired bootstrap CI、配对 sign-flip randomization p 值与 Holm 校正 fixture。macro-F1、图表生成、正式统计环境和 10,000 seed 清单仍须另行冻结验收。bootstrap sign-tail 不再冒充确认性 p 值。

## 6. 交付与未满足门

Person B 工程候选已具备配置、隔离、预算比较、缓存隔离、入口门和手算 fixture，并通过 Person A 视角的工程交叉审查。以下事项仍为 `pending`：M5 真实 Pilot 与人工门；真实 Person A 摘要签名；Person B 交叉审查签名；可信 detached-signature/M5 原始字节验证器；Controller 数据/代码/Prompt/模型/工具/预算/统计 hash Manifest；统一截断器；模型 provider runner；开发集 smoke test；功效计算。故本文件不把 M6 标记为完成，也不授权 M7。
