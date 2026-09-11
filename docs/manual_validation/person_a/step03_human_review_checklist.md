# Person A Step 3 精简人工审核清单

## 本步简介

对 600 道正式样本建立独立人工 Gold，只判断裁决语义和分歧；原材料见 `step03_independent_gold.md`。结果锁定前不得查看 Person B 答案。

## 仅需人工审核

- [ ] **裁决边界**：`accepted`、`unsupported`、`ambiguous`、`undetermined` 等是否符合案例语义。
- [ ] **首错与阻塞**：首个实质错误是否定位正确，后续问题是否只是上游错误造成的阻塞。
- [ ] **理由充分性**：Gold 理由是否足以解释裁决，不确定项是否真实保留。

## 当前证据状态

- `data/benchmarks/m2/annotations/person_a.jsonl` 已保存 50 条 Person A 独立数学标注：12 条 `valid`、10 条 `valid_with_gap`、27 条 `invalid`、1 条 `undetermined`。
- 本工作包目标为 600 题，因此当前可计覆盖为 50／600，仍缺 550 题。
- 剩余对象必须继续保持盲态；Person B 完成记录不得回填为 Person A Gold。

## 异常／分歧登记

| 样本 | 人工裁决 | 关键理由 | 待裁决点 |
|---|---|---|---|
| 剩余 550 题 | 尚未审核 | — | 保持与 Person B 隔离 |

## 最终决定

- 已审核：50／600
- 已知不确定数：1（其余 550 题未审核）
- Person A Step 3：不确定（进行中）
