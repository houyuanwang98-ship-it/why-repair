# 第6步：真实修复 Pilot 与逐补丁人工审核——Person A工作包

## 简介

对仓库中每个补丁版本逐一判断是否真正修复原证明，并把补丁接受与整篇证明成功分开记录。

本工作包分配给 **Person A**，共 **21 个补丁版本**。只完成本文件不足以关闭该步骤；必须与另一人的工作包合并、比较分歧并完成必要裁决。

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

### 001. m5-batch-m2-031-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-031.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `5e9ef04c6b49c5384377e5865361fe7df2fb5bb82ac601911006445069926e02`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-031-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-031-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-031",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "于是 n+1=2k+1。",
      "self_contained_claim": "由 n=2k 且 k 为整数，n+1=2k+1，因此 n+1 是奇数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-031",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-031",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-031",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 002. m5-batch-m2-034-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-034.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `48c58c95d5054f940513911912c41e9a01ac267806496453939e1c35fda3b9c2`


#### 原始记录

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


---

### 003. m5-batch-m2-035-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-035.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `0d486d9afb684d430a520a238fbb24d735c9bde2a7706c65583ece893b2739ae`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-035-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-035-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-035",
    "node_id": 1,
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

### 004. m5-batch-m2-039-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-039.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `01132f3512240b001549b12a30456a8bba7d26587bf6cd200dfab7398f3acc85`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-039-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-039-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-039",
    "node_id": 1,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 1,
      "order_key": 10,
      "claim": "写 b=ak、c=bm，则 c=a(km)，所以 a|c。",
      "self_contained_claim": "由 a|b 与 b|c，存在整数 k,m 使 b=ak、c=bm=a(km)，故 a|c。",
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

### 005. m5-batch-m2-040-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-040.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `e30032bfe9e5b42ff164df4616705c57cbda59b1bbc67a590748e2ef1224f5a9`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-040-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-040-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-040",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "于是 x+y=2m+2n=2(m+n)。",
      "self_contained_claim": "由 x=2m、y=2n，得到 x+y=2(m+n)。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-040",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-040",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-040",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 006. m5-batch-m2-041-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-041.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `fbe7bbadc6489e5320dad1358d1fdf335558f1bc251bf522ec9d5fb868a99dd5`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-041-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-041-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-041",
    "node_id": 1,
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

### 007. m5-batch-m2-044-r2

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-044.patch.r2.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `576c94a58431e2594234cd2a63c62e8468bb379fd727419be859d1eab1f7cebf`


#### 原始记录

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


---

### 008. m5-batch-m2-046-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-046.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `a088a5078249a0cd45d345f232940eeae2fe144c8fbb4a0617c83566f5b210aa`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-046-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-046-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-046",
    "node_id": 1,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 1,
      "order_key": 10,
      "claim": "|a+b|^2≤(|a|+|b|)^2。",
      "self_contained_claim": "|a+b|^2=a^2+2ab+b^2≤a^2+2|a||b|+b^2=(|a|+|b|)^2。",
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

### 009. m5-batch-m2-047-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-047.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `9749697d96b9db9889180e1877d67acc3862824798a83ce1d8f58aae6dfbb02c`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-047-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-047-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-047",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "n^2=4k^2+4k+1=2(2k^2+2k)+1。",
      "self_contained_claim": "由 n=2k+1，平方得 n^2=2(2k^2+2k)+1，因此为奇数。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-047",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-047",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-047",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 010. m5-batch-m2-049-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-049.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `00c63d373fe592c764e76255e53f89bc2d9d95089a338ad243a387d79d14936a`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-049-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-049-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-049",
    "node_id": 2,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 2,
      "order_key": 20,
      "claim": "于是 x+y=(ps+rq)/(qs)。",
      "self_contained_claim": "将 p/q 与 r/s 通分，得到 x+y=(ps+rq)/(qs)。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-049",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-049",
      "node_id": 1,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-049",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 011. m5-batch-m2-050-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-050.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `6dad58ad38afccb511330b1841bb50fa40f0ed83d0c8b9580c69c856d450a175`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-batch-m2-050-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-050-batch-v0.2-error-r1",
  "target": {
    "proof_id": "m2-050",
    "node_id": 3,
    "version": 1
  },
  "operation": "replace",
  "replacement_nodes": [
    {
      "node_id": 3,
      "order_key": 30,
      "claim": "加入 2n+1 后，总和为 n^2+2n+1=(n+1)^2。",
      "self_contained_claim": "由归纳假设，加上下一个奇数 2n+1，得到 (n+1)^2。",
      "node_type": "conclusion",
      "depends_on": [
        {
          "proof_id": "m2-050",
          "node_id": 2,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-050",
      "node_id": 2,
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-050",
      "node_id": 2,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Apply the human-accepted batch repair at the current first error."
}
```


---

### 012. m5-provisional-codex-m2-012-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-012.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `2df39d402cde9d963eaa18007e1ae4730775ac6f273f1b7270a44a5a7198f808`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-012-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-012-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-012",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "由 b=am 与 c=bn，得 c=(am)n=a(mn)；又 mn 为整数。",
      "self_contained_claim": "由 b=am、c=bn 且 m,n 为整数，代入得到 c=a(mn)，其中 mn 为整数。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-012",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-012",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-012",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single substitution-and-witness bridge needed to apply the definition of a dividing c, while preserving the original conclusion."
}
```


---

### 013. m5-provisional-codex-m2-014-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-014.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `da1f3999389defac57aae03f7dd652fa10cda968dded894eae4c86b47a472f5b`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-014-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-014-m3-gap-node-2-v1",
  "target": {
    "proof_id": "m2-014",
    "node_id": 2,
    "version": 1
  },
  "operation": "insert_before",
  "replacement_nodes": [
    {
      "node_id": "2a",
      "order_key": 15,
      "claim": "由 n=2k，得 n^2=(2k)^2=4k^2；又 k^2 为整数。",
      "self_contained_claim": "因为 n=2k 且 k 为整数，所以 n^2=4k^2，其中 k^2 为整数。",
      "node_type": "calculation",
      "depends_on": [
        {
          "proof_id": "m2-014",
          "node_id": 1,
          "version": 1
        }
      ]
    }
  ],
  "target_dependencies_after": [
    {
      "proof_id": "m2-014",
      "node_id": "2a",
      "version": 1
    }
  ],
  "used_dependencies": [
    {
      "proof_id": "m2-014",
      "node_id": 1,
      "version": 1
    }
  ],
  "changes_problem": false,
  "rationale": "Insert the single squaring-and-integer-witness bridge required by divisibility by 4."
}
```


---

### 014. m5-provisional-codex-m2-018-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-018.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `846e19c540e377949294e4c7f10b974f2f9ff85ca37478eb950e9e0a666afafb`


#### 原始记录

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


---

### 015. m5-provisional-codex-m2-021-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-021.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `2a92575844294fb962298eb153a7fc1ae8622b8babd98c10050a4a9ad4bf5e54`


#### 原始记录

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


---

### 016. m5-provisional-codex-m2-023-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-023.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `4e1fe6120ab787b4becf4d6c086c46dca8384a99540e01559f33ab2c99e2731b`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-023-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-023-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-023",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: n=2 has n squared equal to 4, divisible by 4, while n itself is not divisible by 4. No theorem-preserving patch exists."
}
```


---

### 017. m5-provisional-codex-m2-025-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-025.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `fd99859c009811359970cd855c96f2b2254f7312fb9177bfac4e7d0e3a5ec9c8`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-025-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-025-m3-false-theorem-node-1-v1",
  "target": {
    "proof_id": "m2-025",
    "node_id": 1,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: x=1 and y=-1 have equal squares but are not equal. A valid conclusion would be x=y or x=-y, which changes the theorem."
}
```


---

### 018. m5-provisional-codex-m2-027-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-027.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `7fe27f2e76318c7730e43a453632be3f89cadd7d6bb0d8796f614c4687f3af41`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-027-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-027-m3-false-theorem-node-1-v1",
  "target": {
    "proof_id": "m2-027",
    "node_id": 1,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem has the reciprocal inequality direction reversed. For example, 1<2 but 1 is greater than 1/2. Correcting the direction changes the theorem."
}
```


---

### 019. m5-provisional-codex-m2-029-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-029.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `4aaded7ed2597f3a1067b6341cec0f5a2e180bcde962495ac17c5c01272d114e`


#### 原始记录

```json
{
  "schema_version": "0.1",
  "patch_id": "m5-provisional-codex-m2-029-r1",
  "generator_id": "codex-interactive-session-unversioned",
  "error_certificate_id": "m2-029-m3-false-theorem-node-2-v1",
  "target": {
    "proof_id": "m2-029",
    "node_id": 2,
    "version": 1
  },
  "operation": "mark_irreparable",
  "replacement_nodes": [],
  "target_dependencies_after": [],
  "used_dependencies": [],
  "changes_problem": false,
  "rationale": "The original theorem is false: x=1 and y=-1 have zero sum but neither is zero. Replacing the conclusion by y=-x changes the theorem."
}
```


---

### 020. m5-provisional-codex-m2-032-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-032.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `e93febe53e4dbe39b7a49e7167a5dcab7afee7ee9ac1e752daff7c6f02ca8df1`


#### 原始记录

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


---

### 021. m5-provisional-codex-m2-042-r1

- 对象：`data/benchmarks/m5/provisional_codex_interactive_v1/m2-042.patch.json`
- 任务：逐补丁核对输入隔离、数学正确性、局部性、问题保持、后代重验和整篇证明结果
- 机器线索：JSON 可解析；SHA-256 `2134d4be1f157390137213725ab06074c053af71fe0a021d5b560c8aeac48abd`


#### 原始记录

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
