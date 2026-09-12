# v2 实验前交接

本文件保留首次实验前的历史交接状态。后续用户已授权启动测试，当前入口和运行状态见 [SCHEDULER.md](SCHEDULER.md)。旧数据包与旧验证记录绑定旧代码指纹，不能混入新的调度器运行。

日期：2026-09-12。停止位置：**S4 工程先导的第一笔真实模型请求之前**。本次没有执行 `runtime --execute` 或 `judge --execute`，没有新增真实模型结果或人工标签。

## 已完成与核对

- S1：13 个封闭模型输出/输入 Schema，问题白名单、匿名评分、固定模型路由、调用/预算记录及按内容核对的恢复逻辑。
- S2：原始文本构图、DAG 与作用域检查、义务判断、独立诊断、局部补丁、独立审核、原子应用、旧图/新图失效范围、后代重验及运行内完整审核。
- S3：original、direct_rewrite、self_refine、generator_critic、best_of_n、full_system 六种真实执行路径。机制配置的证书形式、反例搜索、失效策略、轮数及最终审核开关已通过离线行为测试。
- 有界精确有理数算式检查与本地冻结 `algebra_core.jsonl` 规则检索。检索结果显式标为未核对适用性，不能自动成为数学结论。
- 全部原始 600 题重新构造公开输入，保留原始 `domain`；没有读取历史生成结果或 Gold 来填充候选。
- 39 项相关测试通过：31 项 v2 测试及 8 项既有修复/Controller 相关测试。全部使用脚本化响应或确定性输入；不是模型性能测量。见 [测试记录](verification/offline_tests.json)。

## 固定模型与环境预检

| 用途 | 固定请求配置 |
|---|---|
| 全部运行内模型角色 | `gpt-5.6-sol` / `xhigh` |
| 独立最终裁判 | `gpt-6` / `high` |

无模型 CLI 参数，无自动 fallback；忽略用户模型配置，并在调用前校验固定值。所有模型工具禁用，允许的数学辅助仅由运行器执行。本地 CLI 为 `codex-cli 0.154.0`，必要参数与禁用功能存在，已有登录状态检查通过。

**未用真实请求探测这两个模型的后端可用性或快照**，因此预检只确认本地准备完整。后端若拒绝固定模型，记录失败，不替换模型。CLI 不能提供可靠的每调用美元费用或硬 token 限制；记录已知 token、未知费用及软限制超额，不伪造零成本。

完整预检见 [preflight.json](verification/preflight.json)。

## 冻结的开发先导包

目录：`experiments/workflow_v2/pilot_20260912`。

- [Manifest](../../experiments/workflow_v2/pilot_20260912/manifest.json)
- [600 题公开输入快照](../../experiments/workflow_v2/pilot_20260912/corpus.json)
- [12 题先导清单](../../experiments/workflow_v2/pilot_20260912/pilot.json)
- [72 个预分配任务](../../experiments/workflow_v2/pilot_20260912/assignments.json)

先导按来源取 3 题：M2 为 m2-011、m2-018、m2-034；B50 为 B01、B25、B50；OPC 与 ProofNet 各取 001、125、250。选取用于覆盖来源和已有开发案例，不代表随机总体抽样或统计功效设计。

其中 12 个 original 任务不生成新证明；60 个修复任务最多各 24 次模型调用、80,000 token、1,800 秒。内部上限合计 1,440 次调用/4,800,000 token；独立评分上限为 72 次调用/1,728,000 token。它们是保守预算上限，不是预计消耗或已发生费用。

每题和任务绑定输入、配置及实现摘要。代码、模型、预算或数据变化后必须准备新 bundle；不能用旧请求文件存在性跳过新配置运行。整个任务包只有准备文件，尚无 runtime、judge 或候选冻结结果。

## 可重复的离线操作

在仓库根目录运行以下命令不会调用模型：

```bash
python -m unittest tests.test_workflow_v2 tests.test_live_repair_pilot tests.test_m5_sequential_repair tests.test_m6_end_to_end_ablation_runner
python scripts/run_workflow_v2.py preflight --bundle experiments/workflow_v2/pilot_20260912
python scripts/run_workflow_v2.py aggregate --bundle experiments/workflow_v2/pilot_20260912
```

尚未运行时聚合器保留 not_run，成功率为空，不将计划任务显示成 0% 实验结果。

以下是以后明确开始实验时的操作，**本次未执行**：

```bash
python scripts/run_workflow_v2.py runtime --bundle experiments/workflow_v2/pilot_20260912 --execute
python scripts/run_workflow_v2.py judge --bundle experiments/workflow_v2/pilot_20260912 --execute
```

runtime 完成全部终态后才冻结候选；judge 要求完整候选冻结。评分一次只接收一份匿名正文，评分不能反馈给生成器。原始结果和失败均保留，缺评有明确状态。

## 尚不具备的证据与适用范围

- 目前是开发先导准备，不是已完成正式实验。600 题均按历史/开发数据处理；精确原题分组不等于语义去重，尚无新未见测试集。
- Graph Builder 处理全篇原文，程序检查引用、覆盖及作用域结构；图和推理的数学语义仍由固定模型判断。复杂作用域无法安全表达时会失败/不确定，不能宣称 Lean 级验证。
- 本地规则库先导只使用 9 条代数核心规则；不打开实时网页或模型文件访问。更广规则/符号工具需要另行冻结后才能进入新运行配置。
- 机制开关已可由 Python 接口执行和离线测试；尚未冻结有独立核验依据的机制图/诊断数据包。当前 CLI 先导只运行原文端到端方法比较。
- 裁判校准、真实模型可用性、跨运行随机性、人工抽审及正式样本量需要 S4 之后的工作；不能在模型尚未调用前声称已经验收这些内容。
- 人工与正式统计字段保留后续接口，当前聚合提供完整计数、覆盖率及虚假成功上下界；正式配对统计与专家加权估计在结果和抽审协议具备后完成。

本次停止是遵守“直到开始实验之前”的任务边界，不是因缺少常规工程权限或新增签字要求。
