# M2：Pilot benchmark 基础设施（Person B）

状态：`in_progress_person_b_annotation_m2.2_complete`

## 范围

Person B 负责数据结构校验、双人标注一致性报告、字段级分歧队列和确定性 Gold 生成，不单方面裁定题目的数学正确性，也不替 Person A 创建金标。

## 已实现

- `scripts/m2_benchmark.py`：共享结构契约、校验、Cohen's kappa、分歧和 Gold 逻辑；
- `schemas/m2_benchmark_v0_2.schema.json`：可移植的 M2 source、annotation、counterexample、disagreement、adjudication 与 Gold manifest 契约；
- `scripts/validate_m2_annotations.py`：源题和独立标注校验；
- `scripts/create_m2_annotation_template.py`：生成默认弃权的独立标注模板；
- `scripts/report_m2_agreement.py`：逐字段一致性报告与分歧队列；
- `scripts/create_m2_adjudication_template.py`：从分歧队列生成默认不可通过验收的字段级裁决模板；
- `scripts/validate_m2_adjudications.py`：在生成 Gold 前独立校验裁决覆盖、枚举值、证据、理由与双人身份；
- `scripts/build_m2_gold.py`：仅从双方一致值或完整裁决生成 Gold；
- `tests/test_m2_benchmark.py`：正反契约、指标和确定性生成测试；
- `data/benchmarks/m2/README.md`：目录、记录格式和运行命令。

一致性报告逐字段记录 exact agreement、Cohen's kappa 和稀疏混淆矩阵，并绑定源题与两份独立标注的 SHA-256。裁决值在合并前执行字段级枚举和类型校验，最终解析出的联合标注还会再次通过完整标注契约。

自检加固后，工具还强制执行：

- Person A 与 Person B 文件各自只能包含一个 `annotator_id`，且两个身份必须不同；
- 每条裁决必须精确绑定当前分歧中的 `person_a_value` 和 `person_b_value`，旧裁决不能复用于变化后的标注；
- `minimal_repair` 等自由文本仅报告 exact agreement 和混淆记录，不计算无解释意义的 Cohen's kappa；
- 每次 Gold 生成自动输出 manifest，绑定源题、A/B 标注、裁决和 Gold 文件 SHA-256、契约版本及生成器。
- `m2.2` 使用完整状态矩阵拒绝矛盾标签，并要求每个有效反例携带结构化证书、覆盖全部源题假设且明确否定目标；
- `.gitattributes` 固定跨平台 LF，避免检出平台改变 benchmark 和 manifest 哈希。

## 基础设施验证

- M2 专项测试：`27 tests, OK`；
- 全仓库回归：`136 tests, OK`；
- 所有 M2 CLI 通过 Python 编译检查；
- 可移植 JSON Schema 可解析，运行时枚举与 Schema 枚举同步测试通过；
- 两个数据 manifest 的源文件及标注哈希均通过复核；
- Git 属性确认 JSON、JSONL、Python 和 Markdown 使用 LF；
- `git diff --check` 通过。

## 标签边界

M2 标注继续使用 `docs/annotation_guideline.md` 的 benchmark 标签，并增加显式 `undetermined`。`docs/milestones/M02_label_mapping.md` 给出到 M1 v0.3 的逐项转换提案；双方批准前，工具不进行隐式转换。

## 当前数据状态

50 题源文件已保存为 `data/benchmarks/m2/source/pilot_50.jsonl`，使用 `m2-source-0.1` 契约，源文件 SHA-256 为 `7f10d1ecf2627f326402580e47055496b3a0041aef1a8e25f374e79ce85f8a0e`。

Person B 已完成全部 50 题独立标注并通过结构校验，结果为：

- `valid`: 12；
- `valid_with_gap`: 12；
- `invalid`: 26。

该分布来自逐题应用冻结规则，不为匹配预设类别配额而修改。当前等待 Person A 独立标注进入 `data/benchmarks/m2/annotations/person_a.jsonl`，之后生成一致性报告和字段级裁决队列。

Person B 标注已迁移到 `m2.2`；全部有效反例均包含结构化证据。补充挑战集 `pilot_B50.jsonl` 使用独立 manifest，保持 `supplemental_unannotated`，不混入当前 Gold 流程。

## M2 退出条件

- 50 个源样本全部进入版本控制并通过结构校验；
- Person A、Person B 独立标注覆盖相同样本集合；
- 自动生成一致性指标和全部字段级分歧；
- 每项分歧有双方参与、包含证据和理由的裁决；
- Gold 可由冻结输入确定性重建；
- Person A 完成交叉审查。
