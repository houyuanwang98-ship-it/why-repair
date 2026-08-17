# M7 人工复核：Person B 检查 m2-026–m2-050

每题内容均已预填。请直接核对；若同意写‘确认’，若不同意只需指出错误位置和理由。

## m2-026：证明若整数 ab 为偶数，则 a 与 b 都为偶数。

### 假设

- a,b 为整数且 ab 为偶数。

### 原证明

n1. 偶数乘积只能由两个偶因子产生。
n2. 因此 a、b 都是偶数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- The original theorem is false: a=2 and b=3 have an even product while b is odd. The valid conclusion that at least one factor is even changes the theorem.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 2, "b": 3}, "assumption_checks": [{"assumption": "a,b 为整数且 ab 为偶数。", "evidence": "ab=6 为偶数", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "b=3 不是偶数；structure=integers；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "a": 2,
    "b": 3
  },
  "assumption_checks": [
    {
      "assumption": "a,b 为整数且 ab 为偶数。",
      "evidence": "ab=6 为偶数",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "b=3 不是偶数；structure=integers；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 2, "b": 3}, "assumption_checks": [{"assumption": "a,b 为整数且 ab 为偶数。", "evidence": "ab=6 为偶数", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "b=3 不是偶数；structure=integers；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-027：证明若正实数 a<b，则 1/a<1/b。

### 假设

- a,b 为正实数且 a<b。

### 原证明

n1. 取倒数保持不等号方向。
n2. 所以 1/a<1/b。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- The original theorem has the reciprocal inequality direction reversed. For example, 1<2 but 1 is greater than 1/2. Correcting the direction changes the theorem.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 1, "b": 2}, "assumption_checks": [{"assumption": "a,b 为正实数且 a<b。", "evidence": "0<a<b", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "1/a=1 大于 1/b=1/2；structure=positive_reals；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "a": 1,
    "b": 2
  },
  "assumption_checks": [
    {
      "assumption": "a,b 为正实数且 a<b。",
      "evidence": "0<a<b",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "1/a=1 大于 1/b=1/2；structure=positive_reals；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 1, "b": 2}, "assumption_checks": [{"assumption": "a,b 为正实数且 a<b。", "evidence": "0<a<b", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "1/a=1 大于 1/b=1/2；structure=positive_reals；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-028：证明任意整数 n 都满足 n^2≥n。

### 假设

- n 为整数。

### 原证明

n1. 因为 n^2 是非负数。
n2. 所以 n^2≥n。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `valid_with_gap`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Insert the single exhaustive integer case split that connects nonnegativity of n squared to the required comparison with n.

### 修改后的完整证明

n1. 因为 n^2 是非负数。
n2a. 整数 n 或满足 n≤0，或满足 n≥1。前一种情形由 n^2≥0≥n；后一种情形因 n≥0，将 n≥1 两边同乘 n 得 n^2≥n。因此所有整数 n 均有 n^2≥n。
n2. 所以 n^2≥n。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-029：证明若实数 x+y=0，则 x=y=0。

### 假设

- x,y 为实数且 x+y=0。

### 原证明

n1. 和为零时每个加数都必须为零。
n2. 因此 x=0 且 y=0。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- The original theorem is false: x=1 and y=-1 have zero sum but neither is zero. Replacing the conclusion by y=-x changes the theorem.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"x": 1, "y": -1}, "assumption_checks": [{"assumption": "x,y 为实数且 x+y=0。", "evidence": "x+y=0", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "x、y 均不为零；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "x": 1,
    "y": -1
  },
  "assumption_checks": [
    {
      "assumption": "x,y 为实数且 x+y=0。",
      "evidence": "x+y=0",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "x、y 均不为零；structure=real_numbers；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"x": 1, "y": -1}, "assumption_checks": [{"assumption": "x,y 为实数且 x+y=0。", "evidence": "x+y=0", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "x、y 均不为零；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-030：证明无理数与有理数之和是无理数。

### 假设

- x 为无理实数，r 为有理数。

### 原证明

n1. 无理数不属于有理数集，而有理数属于有理数集。
n2. 一个不属于有理数集的数与一个属于有理数集的数相加，结果仍不属于有理数集。
n3. 因此 x+r 是无理数。

### 我的判断

冻结数学判断为 `valid_with_gap`；M3 判断为 `valid_with_gap`；首个问题位于 n2；错误类型为 `proof_gap`。

修改理由：

- Replace the unsupported closure assertion with the minimal contradiction using closure of rational numbers under subtraction.

### 修改后的完整证明

n1. 无理数不属于有理数集，而有理数属于有理数集。
n2. 假设 x+r 是有理数。因为 r 是有理数，而两个有理数之差仍是有理数，所以 x=(x+r)-r 是有理数，这与 x 是无理数的已知条件矛盾。因此 x+r 不是有理数。
n3. 因此 x+r 是无理数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-031：证明若整数 n 为偶数，则 n+1 为奇数。

### 假设

- n 为偶整数。

### 原证明

n1. 存在整数 k，使 n=2k。
n2. 于是 n+1=2k+2。
n3. 所以 n+1 可以写成 2k+1 的形式，是奇数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 存在整数 k，使 n=2k。
n2. 由 n=2k 且 k 为整数，n+1=2k+1，因此 n+1 是奇数。
n3. 所以 n+1 可以写成 2k+1 的形式，是奇数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-032：证明若实数 x>1，则 x^2>x。

### 假设

- x 为实数且 x>1。

### 原证明

n1. 由 x>1 可知 x^2>1。
n2. 因此 x^2>x。

### 我的判断

冻结数学判断为 `valid_with_gap`；M3 判断为 `valid_with_gap`；首个问题位于 n2；错误类型为 `proof_gap`。

修改理由：

- Insert the single positive-multiplier argument that directly establishes the required comparison.

### 修改后的完整证明

n1. 由 x>1 可知 x^2>1。
n2a. 由 x>1 可知 x 是正数。把不等式 x>1 的两边同时乘以正数 x，不等号方向不变，因此 x^2>x。
n2. 因此 x^2>x。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-033：证明方程 x^2=1 的实数解恰为 x=1 或 x=-1。

### 假设

- x 为实数且 x^2=1。

### 原证明

n1. 由 x^2-1=0 得 (x-1)(x+1)=0。
n2. 等式两边约去因子 x-1，得到 x+1=0。
n3. 因此 x=1 或 x=-1。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 由 x^2-1=0 得 (x-1)(x+1)=0。
n3. 因此 x=1 或 x=-1。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-034：证明对任意实数 a，都有 sqrt(a^2)=|a|。

### 假设

- a 为实数。

### 原证明

n1. 平方与开平方互相抵消，所以 sqrt(a^2)=a。
n2. 又因为每个实数 a 都等于 |a|，所以 sqrt(a^2)=|a|。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 若 a≥0，则 sqrt(a^2)=a=|a|；若 a<0，则 sqrt(a^2)=-a=|a|。
n2. 由对 a 的正负分类讨论，任意实数 a 都满足 sqrt(a^2)=|a|。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-035：证明若实数 a<b 且 c<0，则 ac>bc。

### 假设

- a,b,c 为实数，a<b 且 c<0。

### 原证明

n1. 将不等式 a<b 两边同时乘以 c，得到 ac<bc。
n2. 因为 c 是负数，所以把不等号改为相反方向，得到 ac>bc。
n3. 因此 ac>bc。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n2. 因为 c 是负数，所以把不等号改为相反方向，得到 ac>bc。
n3. 因此 ac>bc。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-036：证明对任意正整数 n，n^2+n 是偶数。

### 假设

- n 为正整数。

### 原证明

n1. 当 n=1 时，n^2+n=2 是偶数。
n2. 当 n=2 时，n^2+n=6 是偶数。
n3. 因此对任意正整数 n，n^2+n 都是偶数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n3；错误类型为 `false_generalization`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 当 n=1 时，n^2+n=2 是偶数。
n2. 当 n=2 时，n^2+n=6 是偶数。
n3. 对任意正整数 n，n 与 n+1 中必有一个是偶数，所以 n^2+n=n(n+1) 是偶数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-037：证明两个偶整数之和为偶数。

### 假设

- x,y 为偶整数。

### 原证明

n1. 因为两个偶整数之和为偶数，所以 x+y 为偶数。
n2. 因此命题成立。

### 我的判断

冻结数学判断为 `valid_with_gap`；M3 判断为 `valid`；首个问题位于 n1；错误类型为 `proof_gap`。

修改理由：

- 用 x=2m、y=2n 以及 x+y=2(m+n) 替换循环表述。

### 修改后的完整证明

n1. 因为 x、y 为偶整数，存在整数 m,n，使 x=2m、y=2n。
n2. 于是 x+y=2m+2n=2(m+n)。
n3. m+n 为整数，所以 x+y 为偶数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-038：证明对任意实数 x，都有 |x|≥x。

### 假设

- x 为实数。

### 原证明

n1. 实数的平方总是非负，所以 x^2≥0。
n2. 因此 |x|≥x。

### 我的判断

冻结数学判断为 `valid_with_gap`；M3 判断为 `valid_with_gap`；首个问题位于 n2；错误类型为 `proof_gap`。

修改理由：

- Insert the exhaustive absolute-value definition cases that directly establish the comparison.

### 修改后的完整证明

n1. 实数的平方总是非负，所以 x^2≥0。
n2a. 按照绝对值的定义分情况：若 x 大于或等于零，则 x 的绝对值等于 x；若 x 小于零，则 x 的绝对值等于负 x，并且负 x 大于零、零大于 x，所以 x 的绝对值大于 x。因此总有 x 的绝对值大于或等于 x。
n2. 因此 |x|≥x。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-039：证明若整数 a|b 且 b|c，则 a|c。

### 假设

- a,b,c 为整数，a|b 且 b|c。

### 原证明

n1. 由 a|b 可反向得到 b|a，由 b|c 可反向得到 c|b。
n2. 根据整除的传递性，由 c|b 和 b|a 得 c|a。
n3. 因此 a|c。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `theorem_misuse`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 由 a|b 与 b|c，存在整数 k,m 使 b=ak、c=bm=a(km)，故 a|c。
n3. 因此 a|c。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-040：证明两个偶整数之和为偶数。

### 假设

- x,y 为偶整数。

### 原证明

n1. 存在整数 m,n，使 x=2m 且 y=2n。
n2. 于是 x+y=2mn。
n3. 因为 2mn 是偶数，所以 x+y 是偶数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 存在整数 m,n，使 x=2m 且 y=2n。
n2. 由 x=2m、y=2n，得到 x+y=2(m+n)。
n3. x+y=2(m+n)，且 m+n 为整数，因此 x+y 是偶数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-041：证明若实数 a=b，则对任意实数 c 都有 a/c=b/c。

### 假设

- a,b,c 为实数且 a=b。

### 原证明

n1. 等式两边同时除以 c。
n2. 得到 a/c=b/c。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `missing_assumption`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-042：证明若实数 x<y，则 x^2<y^2。

### 假设

- x,y 为实数且 x<y。

### 原证明

n1. 平方函数严格递增。
n2. 因此 x^2<y^2。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- The original theorem is false: -2<-1 but 4>1. Restricting x and y to nonnegative reals or comparing absolute values would change the theorem.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"x": -2, "y": -1}, "assumption_checks": [{"assumption": "x,y 为实数且 x<y。", "evidence": "x<y", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "x^2=4 不小于 y^2=1；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "x": -2,
    "y": -1
  },
  "assumption_checks": [
    {
      "assumption": "x,y 为实数且 x<y。",
      "evidence": "x<y",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "x^2=4 不小于 y^2=1；structure=real_numbers；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"x": -2, "y": -1}, "assumption_checks": [{"assumption": "x,y 为实数且 x<y。", "evidence": "x<y", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "x^2=4 不小于 y^2=1；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-043：证明若整数 a|bc，则 a|b 或 a|c。

### 假设

- a,b,c 为整数且 a|bc。

### 原证明

n1. 由欧几里得引理，a|b 或 a|c。
n2. 结论成立。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- The theorem is false: a=6, b=2, c=3 gives a dividing bc while a divides neither factor. Adding primality or coprimality changes the assumptions.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 6, "b": 2, "c": 3}, "assumption_checks": [{"assumption": "a,b,c 为整数且 a|bc。", "evidence": "a|bc，因为 bc=6", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "a 不整除 b 且 a 不整除 c；structure=integers；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "a": 6,
    "b": 2,
    "c": 3
  },
  "assumption_checks": [
    {
      "assumption": "a,b,c 为整数且 a|bc。",
      "evidence": "a|bc，因为 bc=6",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "a 不整除 b 且 a 不整除 c；structure=integers；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 6, "b": 2, "c": 3}, "assumption_checks": [{"assumption": "a,b,c 为整数且 a|bc。", "evidence": "a|bc，因为 bc=6", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "a 不整除 b 且 a 不整除 c；structure=integers；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-044：证明若实数 a=b，则 (a+c)^2=(b+c)^2。

### 假设

- a,b,c 为实数且 a=b。

### 原证明

n1. 展开两边，得到 (a+c)^2=a^2+2ac+c^2，且 (b+c)^2=b^2+bc+c^2。
n2. 因为 a=b，所以 a^2+2ac+c^2=b^2+bc+c^2。
n3. 因此 (a+c)^2=(b+c)^2。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 两个平方分别正确展开为 a^2+2ac+c^2 与 b^2+2bc+c^2。
n2. 因为 a=b，等式相容性给出 a^2=b^2、2ac=2bc，故展开式相等。
n3. 因此 (a+c)^2=(b+c)^2。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-045：证明若整数 a|b，则 a^2|b^2。

### 假设

- a,b 为整数且 a|b。

### 原证明

n1. 存在整数 k 使 b=ak。
n2. 平方得 b^2=a^2k。
n3. 所以 a^2|b^2。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 存在整数 k 使 b=ak。
n2. 由 b=ak，平方得到 b^2=a^2k^2；k^2 为整数。
n3. 所以 a^2|b^2。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-046：证明对任意实数 a,b，都有 |a+b|≤|a|+|b|。

### 假设

- a,b 为实数。

### 原证明

n1. 因为 |a+b|=sqrt(a^2+b^2)。
n2. 又因为 sqrt(a^2+b^2)≤sqrt(a^2)+sqrt(b^2)=|a|+|b|。
n3. 所以 |a+b|≤|a|+|b|。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n1；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. |a+b|^2=a^2+2ab+b^2≤a^2+2|a||b|+b^2=(|a|+|b|)^2。
n2. 由两边非负及平方根单调性，从平方不等式得到 |a+b|≤|a|+|b|。
n3. 所以 |a+b|≤|a|+|b|。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-047：证明若整数 n 为奇数，则 n^2 为奇数。

### 假设

- n 为奇整数。

### 原证明

n1. 写 n=2k+1。
n2. 则 n^2=4k^2+2k+1。
n3. 所以 n^2 为奇数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 写 n=2k+1。
n2. 由 n=2k+1，平方得 n^2=2(2k^2+2k)+1，因此为奇数。
n3. 所以 n^2 为奇数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-048：证明若实数 ab=0，则 a=0 且 b=0。

### 假设

- a,b 为实数且 ab=0。

### 原证明

n1. 由零乘积性质可知 a=0 或 b=0。
n2. 所以 a=0 且 b=0。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `false_theorem`；首个问题位于 n1；错误类型为 `false_generalization`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 为什么不能给出修订证明

原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 0, "b": 1}, "assumption_checks": [{"assumption": "a,b 为实数且 ab=0。", "evidence": "ab=0", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "b≠0，因此并非 a=0 且 b=0；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。

反例：

```json
{
  "assignments": {
    "a": 0,
    "b": 1
  },
  "assumption_checks": [
    {
      "assumption": "a,b 为实数且 ab=0。",
      "evidence": "ab=0",
      "satisfied": true
    }
  ],
  "claim_ref": "theorem",
  "scope": "original_theorem",
  "target_false": true,
  "verification_method": "manual_exact",
  "verification_notes": "b≠0，因此并非 a=0 且 b=0；structure=real_numbers；checker=person_a_manual_arithmetic_review"
}
```

### 预填审核建议

**原命题在冻结假设下为假或未定义，不能在不改题的情况下给出修正版证明。 反例：`{"assignments": {"a": 0, "b": 1}, "assumption_checks": [{"assumption": "a,b 为实数且 ab=0。", "evidence": "ab=0", "satisfied": true}], "claim_ref": "theorem", "scope": "original_theorem", "target_false": true, "verification_method": "manual_exact", "verification_notes": "b≠0，因此并非 a=0 且 b=0；structure=real_numbers；checker=person_a_manual_arithmetic_review"}`。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-049：证明两个有理数之和为有理数。

### 假设

- x,y 为有理数。

### 原证明

n1. 存在整数 p,q,r,s，且 q,s≠0，使 x=p/q，y=r/s。
n2. 于是 x+y=(p+r)/(qs)。
n3. 因为 p+r 与 qs 都是整数且 qs≠0，所以 x+y 是有理数。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n2；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.
- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 存在整数 p,q,r,s，且 q,s≠0，使 x=p/q，y=r/s。
n2. 将 p/q 与 r/s 通分，得到 x+y=(ps+rq)/(qs)。
n3. 分子 ps+rq 与分母 qs 都是整数，且 q,s 非零推出 qs 非零，故和为有理数。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---

## m2-050：用数学归纳法证明前 n 个正奇数之和等于 n^2。

### 假设

- n 为正整数。

### 原证明

n1. 当 n=1 时，等式 1=1^2 成立。
n2. 假设前 n 个正奇数之和等于 n^2。
n3. 加入下一个奇数 2n+1 后，总和为 n^2+2n+1=n+1。
n4. 所以前 n+1 个正奇数之和等于 (n+1)^2，归纳完成。

### 我的判断

冻结数学判断为 `invalid`；M3 判断为 `invalid`；首个问题位于 n3；错误类型为 `algebraic_invalidity`。

修改理由：

- Apply the human-accepted batch repair at the current first error.

### 修改后的完整证明

n1. 当 n=1 时，等式 1=1^2 成立。
n2. 假设前 n 个正奇数之和等于 n^2。
n3. 由归纳假设，加上下一个奇数 2n+1，得到 (n+1)^2。
n4. 所以前 n+1 个正奇数之和等于 (n+1)^2，归纳完成。

### 预填审核建议

**接受下列完整修订证明。**

复核结果：建议填写 `确认`。如有错误，请写：`纠正：<节点/结论>；理由：<原因>`。

---


