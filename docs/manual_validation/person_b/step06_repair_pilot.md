# 第6步：真实修复 Pilot 与逐补丁人工审核——Person B工作包

## 简介

对仓库中每个补丁版本逐一判断是否真正修复原证明，并把补丁接受与整篇证明成功分开记录。

本工作包分配给 **Person B**，共 **21 个补丁版本**。只完成本文件不足以关闭该步骤；必须与另一人的工作包合并、比较分歧并完成必要裁决。

## 本步要求

1. 补丁生成者不得作最终数学接受判断。
2. 所有声称成功、false repair 和 new-error introduction 必须全量审核。
3. 新增假设、弱化结论、改变定义域或偷换目标必须拒绝。
4. 后代未完整重验不得计为成功。

## 公共记录

- 验证批次编号：________
- 分支：________
- 提交 SHA：________
- 对象摘要或范围清单：________
- 审核者：________
- 审核角色：________
- 审核时间：________
- 证据目录：________
- 已知限制：____________________________________________________________________

## 执行纪律

1. 逐项独立判断，不复制系统预测或另一审核者答案。
2. 机器结果只作定位线索，不构成数学、语义、权利或发布正确性证据。
3. 不确定时填写“不确定”或“需修订”，不得猜测通过。
4. 保留原始意见；复核与裁决不得覆盖初次记录。
5. 每个抽样、异常或需要裁决的对象都必须填写结论、理由和证据路径；其余对象由批次决定覆盖。

## 报告内容

### 001. m5-batch-m2-033-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-033.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `675d1bec98b101c667136b31199a7c1ee245452a1126891490ceb401fab78a23`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-033-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-033-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-033",
    "node_id": 2,
    "version": 1
  },
  "operation": "delete",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 002. m5-batch-m2-034-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-034.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `9ecadf9c357ee4eb140d1276a53c165149bf37f113b6ccb6c264ea1e469dae57`


#### 原始记录

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


---

### 003. m5-batch-m2-036-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-036.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `03780e66d8f72cfb170ddbaec7b6278dffc51db64d07d19f7321c02e67265a1f`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-036-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-036-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-036",
    "node_id": 3,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 3,
      "order_key": 30,
      "claim": "n^2+n=n(n+1)，相邻整数中必有一个为偶数，故乘积为偶数。",
      "self_contained_claim": "对任意正整数 n，n 与 n+1 中必有一个是偶数，所以 n^2+n=n(n+1) 是偶数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-036",
          "node_id": 1,
          "version": 1
        },
        {
          "proof_id": "m2-036",
          "node_id": 2,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-036",
      "node_id": 1,
      "version": 1
    },
    {
      "proof_id": "m2-036",
      "node_id": 2,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-036",
      "node_id": 1,
      "version": 1
    },
    {
      "proof_id": "m2-036",
      "node_id": 2,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 004. m5-batch-m2-039-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-039.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `00eba6aaa07e191f7c7d138e7ed7b95d15c0907aed28b3742bc6c9f068107710`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-039-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-039-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-039",
    "node_id": 2,
    "version": 2
  },
  "operation": "delete",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 005. m5-batch-m2-040-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-040.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `b8fcada5d985953444d7f0564bb260ab2d987fa2e49ac1f8c5514e030603f023`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-040-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-040-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-040",
    "node_id": 3,
    "version": 2
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 3,
      "order_key": 30,
      "claim": "因为 m+n 是整数，所以 x+y 是偶数。",
      "self_contained_claim": "x+y=2(m+n)，且 m+n 为整数，因此 x+y 是偶数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-040",
          "node_id": 2,
          "version": 2
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-040",
      "node_id": 2,
      "version": 2
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-040",
      "node_id": 2,
      "version": 2
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 006. m5-batch-m2-044-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-044.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `32cf98e1890b16e1d722eabc48949ee48efdefc8171bf343fdfa7385628a1fbf`


#### 原始记录

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


---

### 007. m5-batch-m2-045-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-045.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `741b622b261f7ed0e9d8df198bcad0dc831beea76d3094b647d75aeff6ec46bd`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-045-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-045-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-045",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "平方得 b^2=a^2k^2。",
      "self_contained_claim": "由 b=ak，平方得到 b^2=a^2k^2；k^2 为整数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-045",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-045",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-045",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 008. m5-batch-m2-046-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-046.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `b0db9593c76940b6028b5971324477f1f4a6f6e8d350a240453a055b72e30770`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-046-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-046-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-046",
    "node_id": 2,
    "version": 2
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "两边非负，取平方根得 |a+b|≤|a|+|b|。",
      "self_contained_claim": "由两边非负及平方根单调性，从平方不等式得到 |a+b|≤|a|+|b|。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-046",
          "node_id": 1,
          "version": 2
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-046",
      "node_id": 1,
      "version": 2
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-046",
      "node_id": 1,
      "version": 2
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 009. m5-batch-m2-048-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-048.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `e4b573b0919dd8b0c985906f36cbcd59520b7e85a007376409a6c608e48d3099`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-048-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-048-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-048",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 010. m5-batch-m2-049-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-049.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `23c1cf6eb66dd7ec648702114c440f75017389e633450b578515cf479b61534f`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-049-r2",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-049-batch-v0.2-error-r2",
  "target": {
    "proof_id": "m2-049",
    "node_id": 3,
    "version": 2
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 3,
      "order_key": 30,
      "claim": "ps+rq、qs 为整数且 qs≠0，所以 x+y 为有理数。",
      "self_contained_claim": "分子 ps+rq 与分母 qs 都是整数，且 q,s 非零推出 qs 非零，故和为有理数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-049",
          "node_id": 2,
          "version": 2
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-049",
      "node_id": 2,
      "version": 2
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-049",
      "node_id": 2,
      "version": 2
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 011. m5-provisional-codex-m2-011-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-011.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `3e4cf8a02476b1ad7eb124d7f78fb1a7783292d531e7f9d1519c35adbffe0ed3`


#### 原始记录

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


---

### 012. m5-provisional-codex-m2-013-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-013.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `bb74366cac97c7fb24be416b112eea31248332f41622dc6bdad634d61237be87`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-013-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-013-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-013",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "若 x^2=0，则 x=0，与 x≠0 矛盾；故 x^2≠0。结合 x^2≥0，得到 x^2>0。",
      "self_contained_claim": "因为 x 为实数且 x≠0，x^2 不可能等于 0；又实数平方非负，所以 x^2>0。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-013",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-013",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-013",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the omitted zero-exclusion argument that upgrades nonnegativity to strict positivity under the existing x!=0 assumption."
}
```


---

### 013. m5-provisional-codex-m2-016-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-016.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `8d1c6e02b072530d0e5cef9038e3507b9a840065014e016af8ee20d81ead35df`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-016-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-016-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-016",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "由 n=6k=3(2k)，且 2k 为整数。",
      "self_contained_claim": "因为 n=6k 且 k 为整数，所以 n=3(2k)，其中 2k 为整数。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-016",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-016",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-016",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single factorization-and-integer-witness bridge required by the definition of divisibility by 3."
}
```


---

### 014. m5-provisional-codex-m2-019-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-019.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `9f17c8539c1c4e73ffe0953c487b3bbdf335e49019ac2c5b9aa871faca2173ab`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-019-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-019-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-019",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "a-b=5m-5n=5(m-n)，且 m-n 为整数。",
      "self_contained_claim": "由 a=5m、b=5n 且 m,n 为整数，得 a-b=5(m-n)，其中 m-n 为整数。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-019",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-019",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-019",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single subtraction-and-integer-witness bridge required by divisibility by 5."
}
```


---

### 015. m5-provisional-codex-m2-022-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-022.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `f62a728d42f8b41c00bc8b17fcdcdc22688ed5d08b920cd940e1f1515a1744eb`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-022-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-022-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-022",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: x=1 and y=-1 are both nonzero real numbers but their sum is zero. No theorem-preserving patch exists under the frozen assumptions."
}
```


---

### 016. m5-provisional-codex-m2-024-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-024.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `29510b236ccfffa97c4a287afb2a080dce8459eb85e3fa1da7592063d611d7f3`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-024-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-024-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-024",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false because 2 is prime and even. No theorem-preserving patch exists without excluding the prime 2."
}
```


---

### 017. m5-provisional-codex-m2-026-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-026.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `996f1c1d2252b6054adc2754c8c04d8ad66e9f0019f2b1a6dc636f64f6c9a4e3`


#### 原始记录

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


---

### 018. m5-provisional-codex-m2-028-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-028.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `468a526aac426256d215dca0c563fc06665166bfa62764e93d3355709f44541d`


#### 原始记录

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


---

### 019. m5-provisional-codex-m2-030-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-030.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `928d93488995894d683f169b47e7d186d91cff500bc131d6818f3d2ecd3f66cb`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-030-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-030-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-030",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "反设 x+r 为有理数，则 x=(x+r)-r 也是有理数，与 x 为无理数矛盾。",
      "self_contained_claim": "假设 x+r 是有理数。因为 r 是有理数，而两个有理数之差仍是有理数，所以 x=(x+r)-r 是有理数，这与 x 是无理数的已知条件矛盾。因此 x+r 不是有理数。",
      "node_type": "contradiction",
      "depends_on": [
        {
          "proof_id": "m2-030",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-030",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-030",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Replace the unsupported closure assertion with the minimal contradiction using closure of rational numbers under subtraction."
}
```


---

### 020. m5-provisional-codex-m2-038-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-038.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `3497f76f07245338d0358c29f6f45d108a129f5c8b78d4f58f2687c1fce48128`


#### 原始记录

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


---

### 021. m5-provisional-codex-m2-043-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-043.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `9823abbc36dc308cad6ea1ba337d3d81eedfae6a28ff59b8258ebe08c8d17335`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-043-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-043-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-043",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The theorem is false: a=6, b=2, c=3 gives a dividing bc while a divides neither factor. Adding primality or coprimality changes the assumptions."
}
```


---

## 批次级人工验证清单

本步骤不要求逐个对象重复填写审核表。审核者应通读本文件列出的全部对象，结合机器检查定位异常，抽查正常对象，并在发现问题时把对象编号、理由与证据集中登记在下方。

- [ ] 补丁生成者不得作最终数学接受判断。
- [ ] 所有声称成功、false repair 和 new-error introduction 必须全量审核。
- [ ] 新增假设、弱化结论、改变定义域或偷换目标必须拒绝。
- [ ] 后代未完整重验不得计为成功。

### 抽样与异常记录

- 抽样方法、覆盖范围与样本量：__________________________________________________
- 机器异常及人工复核结果：______________________________________________________
- 发现问题的对象编号、理由与证据路径：__________________________________________
- 需要另一审核者或第三方裁决的分歧：____________________________________________

### 工作包汇总与最终决定

- 分配总数：21 个补丁版本
- 已完成：________
- 通过：________
- 不通过：________
- 需修订：________
- 不确定：________
- 排除／不适用：________
- 分类数量与分配总数一致：________（是／否）
- 阻塞问题：____________________________________________________________________
- 下一步行动：__________________________________________________________________
- 最终决定：________（通过／修订后通过／部分排除／不通过／不确定）
- 决定理由与证据路径：__________________________________________________________
- 本工作包状态：________（未开始／进行中／阻塞／完成）
