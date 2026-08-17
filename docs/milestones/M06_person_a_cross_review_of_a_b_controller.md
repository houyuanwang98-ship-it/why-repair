# M6 Person A：A/B/Controller 数学可比性交叉审查 v0.1

状态：`engineering_cross_review_passed_human_signature_pending_m5_entry_blocked`。本记录是以 Person A 数学语义与公平性职责完成的代码/协议工程审查，不构成真实人员身份、独立盲态或 detached signature。M5 `m6_entry_allowed=false`，M6 真实运行继续禁止。

## 1. 审查范围

- Person A 预注册协议、盲态错误分析模板及摘要清单；
- Person B 九种基线/消融、配置与缓存隔离、预算及手算评分器；
- Controller artifact/样本/配置绑定、运行账本、失败保留和统计 fixture；
- README、ROADMAP、PROJECT_INDEX、CHANGELOG 与 M5→M6 边界。

审查标准来自 `docs/m0_m8_research_execution_sequence.md` 第 11、29、30 节和 `docs/project_validation_and_acceptance_plan.md` 第 32、42 节。

## 2. 已发现并修复的实质问题

1. **P0：形式门可由自报布尔值和字符串签名绕过。** 旧 Controller 在调用者传入 `m5_entry_allowed=true` 和三项 `signed` 后即可构造正式 Manifest，却未读取/核验实时 M5 原始字节或 detached signature。现 v0.1 对所有非 fixture Manifest/执行无条件 fail closed；未来必须新版本实现可信验证器。
2. **P1：修复成功与 false repair 可由记录自报。** 旧评分器只检查四个弱前提，调用者可把缺少问题保持、独立复核、最小性或后代重验的补丁写成成功，也可把“宣称成功但未验证”写成非 false repair。现成功由七项数学门派生，false repair 由 `claimed && !verified` 强制派生。
3. **P1：墙钟预算按尝试而非样本累计。** 一次重试可把 180 秒预算扩大到 360 秒。现 token、调用和墙钟均跨同一样本全部尝试累计。
4. **P1：unsupported resolution 误计。** Gold `gap` 对应预测 `accepted_with_gap` 原被算作过度解决。现仅 `gap→accepted`，以及 `undetermined→accepted/accepted_with_gap` 计入。
5. **P1：bootstrap sign-tail 被当作确认性 p 值。** 现 bootstrap 仅提供 paired CI，确认性 p 值使用独立 paired sign-flip randomization，再按预注册 H 分别做 Holm。
6. **P1：任意方法可拼成“比较组”。** 现只允许含完整系统的 H1/H2/H3 预注册方法集合，拒绝跨 RQ 拼接。
7. **P1：名为 digest 的字段只要求非空。** 现所有配置 artifact digest 必须是小写 64 位 SHA-256。
8. **P1：评分 Gold 与修复字段可缺失或类型漂移。** 现强制核心 Gold/failure 字段、布尔类型、repairability 枚举、首错可评分一致性、反例资格和 invalid 状态一致。
9. **P2：基础设施失败可使若干安全率虚假下降。** 现首错无位置假阳性、false accept、unsupported resolution、false repair 和新错误引入率均保留最坏情形上界。
10. **P2：结果未暴露是不可机械证明的事实。** Controller Manifest 现显式记录 `self_attested_unverified`，不把自述当作盲态证据。
11. **P1：比较 family 可只提交有利子集，主 Manifest 也无法同时冻结九配置。** 现分别提供完整 H1/H2/H3 family 校验和完整九方法 suite 校验，缺失或重复任何方法均拒绝。
12. **P1：Gold 分母字段可省略。** 现每条记录强制提供首错可评分状态及原因、反例资格、repairability 与 failure 状态；有效反例必须伴随 `invalid` 数学裁决，基础设施失败不得携带数学证据计数。

## 3. Person A 数学可比性结论

- H1/H2/H3 方法归属与协议一致；无图消融同时失去图派生的后代失效能力属于定义内耦合，必须在论文中按“图机制包”解释，不能声称只删除一条边字段。
- 主要比较固定样本、模型组合、数据/定理库/工具实现、代码、评分器、Schema、采样、截断和总预算；方法 Prompt 与权限差异属于预注册处理定义，须逐方法冻结摘要。
- 所有零分母保持 `undefined (0/0)`；基础设施失败保留在 intention-to-treat、成本与失败分母中，不得删除。
- 现有实现仅证明 fixture 契约在测试范围内成立，不证明模型输出的数学正确性、真实人员独立性、数据未泄漏或主实验可运行。

## 4. 仍阻塞的强制门

1. M5 真实 Repair Generator Pilot、Person A 全量补丁复核、真实成本审计和外部 Controller 审查；
2. 真实 Person A 对精确协议摘要签名、Person B 交叉审查及 Controller 签名；
3. live M5 原始字节、签名身份/算法/公钥和 detached signature 的可信验证器；
4. 模型快照、价格表、Prompt、统一截断器、provider runner、统计库与 10,000 seed 正式 Manifest；
5. 结果前功效计算、开发集 smoke test、字段完整性验收和实际输入泄漏抽查。

退出决定：Person A 视角的 **fixture 工程交叉审查通过（十二项问题已修复）**；M6 人工签署门、真实运行门、M6 整体退出门和 M7 入口均 **不通过**。
