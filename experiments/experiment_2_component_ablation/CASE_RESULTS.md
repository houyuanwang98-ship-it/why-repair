# 实验2逐题结果

`双 Agent 单轮`一列是将已保存完整轨迹截断在第一轮后的回顾性重构；它不是一次新的独立模型调用。

| 证明 | Gold状态 | 无Agent | 单诊断Agent | 双Agent单轮 | 双Agent+Controller | 轮数 | 最终操作 | 人工审核 |
|---|---|---:|---:|---:|---:|---:|---|---|
| m2-012 | `valid_with_gap` | 0 | 0 | 1 | 1 | 1 | `insert_before` | `accepted` |
| m2-014 | `valid_with_gap` | 0 | 0 | 1 | 1 | 1 | `insert_before` | `accepted` |
| m2-018 | `undetermined` | 0 | 0 | 1 | 1 | 1 | `insert_before` | `accepted` |
| m2-021 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-023 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-025 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-027 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-029 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-031 | `invalid` | 0 | 0 | 1 | 1 | 1 | `replace` | `accepted` |
| m2-032 | `valid_with_gap` | 0 | 0 | 1 | 1 | 1 | `insert_before` | `accepted` |
| m2-034 | `invalid` | 0 | 0 | 0 | 1 | 2 | `replace` | `accepted` |
| m2-035 | `invalid` | 0 | 0 | 1 | 1 | 1 | `delete` | `accepted` |
| m2-039 | `invalid` | 0 | 0 | 0 | 1 | 2 | `delete` | `accepted` |
| m2-040 | `invalid` | 0 | 0 | 0 | 1 | 2 | `replace` | `accepted` |
| m2-041 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-042 | `invalid` | 0 | 0 | 0 | 0 | 1 | `mark_irreparable` | `accepted` |
| m2-044 | `invalid` | 0 | 0 | 0 | 1 | 2 | `replace` | `accepted` |
| m2-046 | `invalid` | 0 | 0 | 0 | 1 | 2 | `replace` | `accepted` |
| m2-047 | `invalid` | 0 | 0 | 1 | 1 | 1 | `replace` | `accepted` |
| m2-049 | `invalid` | 0 | 0 | 0 | 1 | 2 | `replace` | `accepted` |
| m2-050 | `invalid` | 0 | 0 | 1 | 1 | 1 | `replace` | `accepted` |

说明：1表示该条件下最终整篇证明被记录为严格通过，0表示没有。仅诊断Agent不生成补丁，因此其最终修复成功状态与原证明相同。
