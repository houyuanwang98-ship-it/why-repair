# 首错定位与连续修复 v2

## 已实现的闭环

`harness.iterative_localization.IterativeRepairSession` 管理当前版本的整篇证明：

```text
按原文顺序定位 → 前缀全部接受才签发首错证书
→ Generator 仅看到局部输入 → M5 独立 PatchReview 和事务修改
→ 修改节点与所有后代升级版本 → 整篇重新扫描
→ 下一首错，或等待证据，或所有节点与原题目标均通过
```

依赖图决定节点是否具备可用前提；原文顺序决定哪个错误是首错。
没有通过的前提阻塞实际后代，但其他分支仍可检查。
例如第 2 步未决、第 4 步确定错误时，`first_error_candidate` 指向第 4 步，
`first_error` 和 `certificate` 为空，Generator 无法开始修复。
修完第一个错误后，扫描也覆盖与补丁无依赖关系的分支，避免只重验后代就提前成功。

所有节点均接受后，再执行 final target-coverage 审核，要求最终结论确实完成原题。
缺少目标覆盖证据仍为 `awaiting_evidence`；目标不匹配时修复对象是最后实际节点。
`complete` 表示当前版本按该自然语言审计协议通过，不代表形式化证明。
循环中有些下游症状会随上游修复消失，也可能产生新错误，所以每轮重新定位，
不把初始错误列表视为固定不变。

## 证据绑定

`local_inference_v2.py` 与 `schemas/local_inference_review_v2.schema.json` 定义新协议。
请求包含当前节点版本、原题（仅作目标）、定义域和合法来源目录。
条件、桥接和最终局部结论引用精确的 `source_id` 与摘要；
支持条件没有来源、来源不存在/过期、条件 missing/unknown、循环论证和目标文本不一致
均不能得到 accepted。桥接最多三步，相邻桥接必须连接，最后一步必须对应原断言。
补丁只能使用冻结的直接前提或新插入节点。Generator 不接收后续证明文本。

这些检查保证来源和结构一致；任意自然语言规则的数学真值仍由 Evaluator 判断。
不能把字段通过解释为已经由机器验证全部数学内容。

## 调用成本与版本

- 原样重述已确认前提，以及明确 integers/rationals/reals 域内的封闭有理数运算，
  可由确定性程序验证；仅支持整数常量、正负号、加减乘除和比较，不执行表达式代码。
- 改写的 self-contained claim、未知结构、含变量运算和其他自然语言推理继续送审。
- Evaluator 结果按局部输入摘要复用，包含目标版本和前提证据；修复后的相关版本不能命中旧证据。
- 每次扫描、整个会话和补丁尝试都有预算。失败、拒绝、超时及等价证明循环保留记录。
- PatchReview 后立即清除当前定位报告，必须重扫才能获取下一证书或宣布完成。

## 使用接口

```python
from harness.iterative_localization import IterativeRepairSession

session = IterativeRepairSession(
    proof_id=proof_id, theorem=theorem, assumptions=assumptions,
    domain=domain, nodes=versioned_nodes,
    evaluator_ids={"person-a"}, generator_id="person-b",
)
report = session.evaluate(evaluator_adapter, max_calls=8)
if report["state"] == "error_confirmed":
    frozen_input = session.generator_input()
    # Generator produces an M5 v0.1 PatchProposal from frozen_input.
    # The independent Evaluator supplies the existing M5 review context/review.
    session.apply_patch(patch, review_context, patch_review)
    report = session.evaluate(evaluator_adapter, max_calls=8)
```

`versioned_nodes` 使用 M5 节点字段（proof_id/node_id/version/order_key/claim/
self_contained_claim/node_type/depends_on）。图必须先经 Evaluator 审查，构造器只校验结构。
`evaluator_adapter(request)` 返回 request 内附的 response_schema 对应对象。
也可调用 `evaluate(responses={input_digest: response})` 导入当前请求的结果。
`snapshot()` 提供当前证明、修复次数、审核次数和事件链，供调用方保存。
此接口不自动发起 Provider 请求；真实调用、费用和持久化由上层运行器提供。

本轮还把 v1 的首错汇总移到核心 `build_result`：`first_error_step` 只返回已确认首错，
另以 `first_error_candidate_step`、`localization_blockers` 表达未决前缀。
旧的 first_invalid_step/first_gap_step 仍表示各类首次发现位置，不能直接作为修复授权。
新字段属于 opt-in localization 输出；历史 checker Schema 与冻结数据不变。

## 可重放验证

```powershell
python -X utf8 scripts/run_iterative_localization_demo.py --output outputs/iterative_localization_v2_demo.json
python -X utf8 -m unittest discover -s tests -p test_iterative_localization.py
```

演示先找到第 1 步错误，修复重验后找到独立分支第 2 步错误，再修复重验与核对原题，最终 complete。
错误由精确算术检出；补丁审核和最终目标审核是公开 fixture，不冒充真实模型或独立人工实验。
新测试覆盖独立分支、下游错误、补丁新错误、前缀未决、删除重连、插入检查、版本过期、
条件来源、循环论证一致性、预算、缓存隔离与完整目标检查。
2026-09-23 本地完整回归 487 项通过（含新增 21 项）。

全库额外测试依赖列在 `requirements-test.txt`，Windows 运行使用 `-X utf8`。
尚未以新盲测题进行真实模型对照，因此不把工程回放报告为首错准确率提升。
后续应同时记录单轮首错准确率、整篇连续修复成功率、各轮遗漏/新错误、未决率与总成本。
