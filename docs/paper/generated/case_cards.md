# 十个历史代表案例

从既有工程集抽取，用于展示；不是新题、独立测试集或新增人工审核。保留原始文本与复核意见，不自动规范化争议标签。

## m2-011

证明两个奇整数之和为偶数。

假设：x、y 为奇整数。

- n1：存在整数 m,n，使 x=2m+1，y=2n+1。
- n2：所以 x+y 是偶数。

历史案例复核记录：

```json
{
  "case_id": "m2-011",
  "reviewer_slot": "user_person_a",
  "verification": "confirmed",
  "correction": null
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-011.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-011-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-011-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-011",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "x+y=(2m+1)+(2n+1)=2(m+n+1)，且 m+n+1 为整数。",
      "self_contained_claim": "由 x=2m+1、y=2n+1 且 m,n 为整数，得到 x+y=2(m+n+1)，其中 m+n+1 为整数。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-011",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-011",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-011",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single omitted algebraic bridge that rewrites the sum as twice an integer; preserve the original conclusion node and all theorem assumptions."
}
```

## m2-018

证明若 x,y 为实数且 x=y，则 x^2=y^2。

假设：x,y 为实数且 x=y。

- n1：等式两边分别乘以 x 和 y。
- n2：因此 x^2=y^2。

历史案例复核记录：

```json
{
  "case_id": "m2-018",
  "reviewer_slot": "user_person_a",
  "verification": "confirmed",
  "correction": null
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-018.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-018-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-018-human-gap-node-2-v1",
  "target": {
    "proof_id": "m2-018",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "由 x=y，在等式两边同乘 x，得到 x^2=xy。",
      "self_contained_claim": "由 x=y，根据等式的乘法相容性，两边同乘 x 得 x^2=xy。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-018",
          "node_id": 1,
          "version": 1
        }
      ]
    },
    {
      "node_id": "2b",
      "order_key": 16,
      "claim": "由 x=y，在等式两边同乘 y，得到 xy=y^2；结合 x^2=xy，故 x^2=y^2。",
      "self_contained_claim": "由 x=y，两边同乘 y 得 xy=y^2；再由 x^2=xy 的传递性得到 x^2=y^2。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-018",
          "node_id": "2a",
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-018",
      "node_id": "2b",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-018",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Make the equality-substitution chain explicit with two same-factor multiplications, resolving the ambiguous original wording without changing the theorem."
}
```

## m2-021

证明若 a+b 为偶数，则 a、b 都为偶数。

假设：a,b 为整数且 a+b 为偶数。

- n1：偶数可以写成 2k。
- n2：因此 a=2m 且 b=2n。
- n3：所以 a、b 都为偶数。

历史案例复核记录：

```json
{
  "case_id": "m2-021",
  "reviewer_slot": "user_person_a",
  "verification": "confirmed",
  "correction": null
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-021.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-021-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-021-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-021",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: a=1 and b=1 give an even sum while neither integer is even. No theorem-preserving patch exists under the frozen assumptions."
}
```

## m2-026

证明若整数 ab 为偶数，则 a 与 b 都为偶数。

假设：a,b 为整数且 ab 为偶数。

- n1：偶数乘积只能由两个偶因子产生。
- n2：因此 a、b 都是偶数。

历史案例复核记录：

```json
{
  "case_id": "m2-026",
  "reviewer_slot": "person_b",
  "verification": "confirmed",
  "correction": null
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-026.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-026-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-026-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-026",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: a=2 and b=3 have an even product while b is odd. The valid conclusion that at least one factor is even changes the theorem."
}
```

## m2-028

证明任意整数 n 都满足 n^2≥n。

假设：n 为整数。

- n1：因为 n^2 是非负数。
- n2：所以 n^2≥n。

历史案例复核记录：

```json
{
  "case_id": "m2-028",
  "reviewer_slot": "person_b",
  "verification": "corrected",
  "correction": "首个问题位于 n2：错误类型为 跳步"
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-028.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-028-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-028-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-028",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "若 n≤0，则 n^2≥0≥n；若 n≥1，则 n≥0，从 n≥1 两边同乘 n 得 n^2≥n。",
      "self_contained_claim": "整数 n 或满足 n≤0，或满足 n≥1。前一种情形由 n^2≥0≥n；后一种情形因 n≥0，将 n≥1 两边同乘 n 得 n^2≥n。因此所有整数 n 均有 n^2≥n。",
      "node_type": "case_analysis",
      "depends_on": [
        {
          "proof_id": "m2-028",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-028",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-028",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single exhaustive integer case split that connects nonnegativity of n squared to the required comparison with n."
}
```

## m2-032

证明若实数 x>1，则 x^2>x。

假设：x 为实数且 x>1。

- n1：由 x>1 可知 x^2>1。
- n2：因此 x^2>x。

历史案例复核记录：

```json
{
  "case_id": "m2-032",
  "reviewer_slot": "person_b",
  "verification": "corrected",
  "correction": "首个问题位于 n2；错误类型为 `algebraic_invalidity`"
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-032.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-032-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-032-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-032",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "因 x>1>0，将 x>1 两边同乘正数 x，得到 x^2>x。",
      "self_contained_claim": "由 x>1 可知 x 是正数。把不等式 x>1 的两边同时乘以正数 x，不等号方向不变，因此 x^2>x。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-032",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-032",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-032",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single positive-multiplier argument that directly establishes the required comparison."
}
```

## m2-034

证明对任意实数 a，都有 sqrt(a^2)=|a|。

假设：a 为实数。

- n1：平方与开平方互相抵消，所以 sqrt(a^2)=a。
- n2：又因为每个实数 a 都等于 |a|，所以 sqrt(a^2)=|a|。

历史案例复核记录：

```json
{
  "case_id": "m2-034",
  "reviewer_slot": "person_b",
  "verification": "confirmed",
  "correction": null
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-034.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-034-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-034-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-034",
    "node_id": 1,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 1,
      "order_key": 10,
      "claim": "按算术平方根与绝对值的定义，sqrt(a^2)=|a|。",
      "self_contained_claim": "若 a≥0，则 sqrt(a^2)=a=|a|；若 a<0，则 sqrt(a^2)=-a=|a|。",
      "node_type": "conclusion",
      "depends_on": []
    }
  ],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-034.patch.r2.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-034-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-034-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-034",
    "node_id": 2,
    "version": 2
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "因此 sqrt(a^2)=|a|。",
      "self_contained_claim": "由对 a 的正负分类讨论，任意实数 a 都满足 sqrt(a^2)=|a|。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-034",
          "node_id": 1,
          "version": 2
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-034",
      "node_id": 1,
      "version": 2
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-034",
      "node_id": 1,
      "version": 2
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```

## m2-038

证明对任意实数 x，都有 |x|≥x。

假设：x 为实数。

- n1：实数的平方总是非负，所以 x^2≥0。
- n2：因此 |x|≥x。

历史案例复核记录：

```json
{
  "case_id": "m2-038",
  "reviewer_slot": "person_b",
  "verification": "corrected",
  "correction": "首个问题位于n2；错误类型为 `false_generation`"
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-038.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-038-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-038-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-038",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "若 x≥0，则 |x|=x；若 x<0，则 |x|=-x>0>x。故总有 |x|≥x。",
      "self_contained_claim": "按照绝对值的定义分情况：若 x 大于或等于零，则 x 的绝对值等于 x；若 x 小于零，则 x 的绝对值等于负 x，并且负 x 大于零、零大于 x，所以 x 的绝对值大于 x。因此总有 x 的绝对值大于或等于 x。",
      "node_type": "case_analysis",
      "depends_on": [
        {
          "proof_id": "m2-038",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-038",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-038",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the exhaustive absolute-value definition cases that directly establish the comparison."
}
```

## m2-042

证明若实数 x<y，则 x^2<y^2。

假设：x,y 为实数且 x<y。

- n1：平方函数严格递增。
- n2：因此 x^2<y^2。

历史案例复核记录：

```json
{
  "case_id": "m2-042",
  "reviewer_slot": "person_b",
  "verification": "corrected",
  "correction": "原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。首个问题位于 n1；错误类型为 `missing_assumption`"
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-042.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-042-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-042-m3-false-theorem-node-1-v1",
  "target": {
    "proof_id": "m2-042",
    "node_id": 1,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: -2<-1 but 4>1. Restricting x and y to nonnegative reals or comparing absolute values would change the theorem."
}
```

## m2-044

证明若实数 a=b，则 (a+c)^2=(b+c)^2。

假设：a,b,c 为实数且 a=b。

- n1：展开两边，得到 (a+c)^2=a^2+2ac+c^2，且 (b+c)^2=b^2+bc+c^2。
- n2：因为 a=b，所以 a^2+2ac+c^2=b^2+bc+c^2。
- n3：因此 (a+c)^2=(b+c)^2。

历史案例复核记录：

```json
{
  "case_id": "m2-044",
  "reviewer_slot": "person_b",
  "verification": "corrected",
  "correction": "M3 判断为 `invalid_with_gap`；首个问题位于 n1；错误类型为 跳步"
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-044.patch.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-044-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-044-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-044",
    "node_id": 1,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 1,
      "order_key": 10,
      "claim": "展开得 (a+c)^2=a^2+2ac+c^2，(b+c)^2=b^2+2bc+c^2。",
      "self_contained_claim": "两个平方分别正确展开为 a^2+2ac+c^2 与 b^2+2bc+c^2。",
      "node_type": "conclusion",
      "depends_on": []
    }
  ],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```

补丁来源：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-044.patch.r2.json`

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-044-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-044-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-044",
    "node_id": 2,
    "version": 2
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "由 a=b，得 a^2=b^2 且 2ac=2bc，所以两展开式相等。",
      "self_contained_claim": "因为 a=b，等式相容性给出 a^2=b^2、2ac=2bc，故展开式相等。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-044",
          "node_id": 1,
          "version": 2
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-044",
      "node_id": 1,
      "version": 2
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-044",
      "node_id": 1,
      "version": 2
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```
