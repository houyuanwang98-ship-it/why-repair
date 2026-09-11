# 自动复算结果

本表由 `rebuild.py` 从 Gold、人工同步记录及 Controller completion 重新计算。

| 子集 | 修复前严格接受 | 修复后记录为 repaired | 描述性变化 |
|---|---:|---:|---:|
| 全部21题 | 0/21 | 14/21（66.7%） | +66.7个百分点 |
| 排除未确定题 | 0/20 | 13/20（65.0%） | +65.0个百分点 |
| 仅原Gold为invalid | 0/17 | 10/17（58.8%） | +58.8个百分点 |

统计单位为不同证明，不是补丁轮次。不可修退出不计为修复成功。
这些比例以历史纳入队列为分母；没有独立冻结的可修性标签，不能将14个成功样本反过来定义成可修集合。
Wilson区间见 results.json；由于回顾性选择和同源样本，区间仅供描述，不能建立总体泛化或方法优势。

| Proof ID | 原Gold | 历史终态 | 轮数 | Completion证据 |
|---|---|---|---:|---|
| m2-012 | valid_with_gap | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-012.completion.json) |
| m2-014 | valid_with_gap | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-014.completion.json) |
| m2-018 | undetermined | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-018.completion.json) |
| m2-021 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-021.completion.json) |
| m2-023 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-023.completion.json) |
| m2-025 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-025.completion.json) |
| m2-027 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-027.completion.json) |
| m2-029 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-029.completion.json) |
| m2-031 | invalid | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-031.completion.json) |
| m2-032 | valid_with_gap | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-032.completion.json) |
| m2-034 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-034.completion.json) |
| m2-035 | invalid | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-035.completion.json) |
| m2-039 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-039.completion.json) |
| m2-040 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-040.completion.json) |
| m2-041 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-041.completion.json) |
| m2-042 | invalid | not_repaired_irreparable | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-042.completion.json) |
| m2-044 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-044.completion.json) |
| m2-046 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-046.completion.json) |
| m2-047 | invalid | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-047.completion.json) |
| m2-049 | invalid | repaired | 2 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-049.completion.json) |
| m2-050 | invalid | repaired | 1 | [记录](../../data/benchmarks/m5/provisional_codex_interactive_v1/m2-050.completion.json) |
