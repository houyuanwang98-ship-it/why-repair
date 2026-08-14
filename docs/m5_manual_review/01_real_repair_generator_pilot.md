# M5 人工审核 1：真实 Repair Generator Pilot

> [!IMPORTANT]
> **本文件包含必须由真人审核的外部真实性事项。** 生产模型身份、提供方调用记录、Gold 隔离和失败运行完整性不能由仓库机器自证。未取得人工审核记录和签名时，本项必须保持 `pending`。

## 目的与责任人

本项用于证明 Repair Generator 在真实生产模型上能够只依据冻结的局部错误证书生成合规补丁。主要执行者为 Person B 或实验工程人员；配置冻结、运行完整性和结果归档需要另一名人工审核者确认。

确定性 fixture、人工写死补丁和缓存输出只能验证程序，不得作为真实 Pilot 证据。

## 机器无法独立验证的事项（必须人工确认）

以下事项即使 Schema 和测试全部通过，也不能由仓库程序独立证明：

- 实际调用的服务确为声明的生产模型和精确版本；
- API 凭据来源、调用账户和提供方后台记录真实；
- 模型在仓库之外没有接触 Gold 修复或隐藏审核提示；
- 操作者没有在机器可见日志之外挑选、删除或替换失败运行；
- 原始响应确实来自该次外部调用，而不是人工编辑或 fixture；
- 模型提供方、版本日期、参数和运行时间的声明与外部账单一致。

这些项目必须由人工查看提供方控制台、凭据治理记录、原始归档和运行环境后签字确认。机器只能检查提交到仓库中的记录彼此一致。

## 开始前必须提供的材料

- 生产模型提供方、精确模型 ID 和版本日期；
- 温度、最大输出 token、超时、重试次数及随机种子（若支持）；
- `prompts/m5_repair_generator_person_b.md` 的文件摘要；
- M5 Pilot 输入清单及 SHA-256；
- 每题冻结的目标节点版本、ErrorCertificate、允许证据和 repair budget；
- M4 v1.1 只读证据的来源与摘要；
- 代码提交 SHA 和运行环境说明；
- 不进入仓库的 API 凭据管理方案。

缺少任一关键材料时，审核者应停止运行并登记阻塞，不得自行猜测模型版本或补写输入。

## Pilot 输入人工校验细则

审核者应逐题确认：

- [ ] `proof_id`、目标 `node_id` 和版本与冻结证明图一致；
- [ ] ErrorCertificate 指向当前版本，不是过期节点；
- [ ] 只包含目标节点、直接依赖和明确允许的数学证据；
- [ ] 不包含 Gold 修复、Person A 隐藏 Prompt 或无关证明分支；
- [ ] `allowed_operations` 和节点/编辑预算与证书一致；
- [ ] M4 证据确属 v1.1 已接受对象，且以只读方式传入；
- [ ] 输入文件摘要已登记，运行后没有原地修改。

## 模型运行人工校验细则

- [ ] 每次调用记录模型、Prompt 版本、输入/输出 token、延迟和状态；
- [ ] 原始模型响应与解析后的 PatchProposal 同时保存；
- [ ] Schema 错误、超时、传输错误和拒绝结果全部保留；
- [ ] 失败运行没有被删除或用成功重跑覆盖；
- [ ] 重试使用同一冻结输入，并有独立 attempt 编号；
- [ ] 模型没有写入 PatchReview 或最终接受状态；
- [ ] 重复等价补丁触发终止，而不是无限重试；
- [ ] 输出中的新增假设或目标变化被标记为 `changes_problem`，不算修复。

## 人工抽查要求

至少由审核者随机抽查以下对象：一次成功调用、一次失败或拒绝调用、一次重试、一次等价补丁终止，以及所有 `mark_irreparable` 输出。抽查应比对原始响应、解析对象、事件日志和最终运行清单是否一致。

## 禁止使用的替代证据

- 单元测试中的 fixture model；
- 手工构造并冒充模型输出的 PatchProposal；
- 未记录精确模型版本的聊天界面结果；
- 只保存最终成功结果而删除失败调用；
- 使用 Gold 修复或 Person A 私有裁决提示模型。

## 审核记录最低字段

```text
review_id:
reviewer_name_or_id:
reviewer_role:
code_commit:
pilot_input_digest:
model_provider:
model_id_and_version:
prompt_digest:
run_manifest_path:
checked_sample_ids:
failed_run_preservation: pass/fail
data_leakage_check: pass/fail
findings:
decision: accepted / rejected / blocked
signed_at:
signature_or_attestation:
```

## 完成判据

全部适用 Pilot 案例均有可回放运行清单，成功和失败调用完整保留，抽查无 Gold 泄漏或越权状态写入，且人工审核记录绑定精确提交和输入摘要。满足这些条件后，才能把 `real_repair_generator_pilot` 从 `pending` 改为 `passed`。
