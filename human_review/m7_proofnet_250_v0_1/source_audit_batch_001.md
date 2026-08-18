# M7 ProofNet-250 来源审计：校准批次 001（25 题）

请核对 AI 对原始 ProofNet 题面与证明的判断。同意写 `确认`；不同意写 `纠正：<理由>`。

## proofnet250-067

### 题目

Prove that $x^3 + 6x + 12$ is irreducible in $\mathbb{Q}$.

### ProofNet 原证明

\begin{proof}

    Apply Eisenstein's criterion with $p=3$. 

\end{proof}

### AI 首审

- 来源状态：`valid_with_gap`
- 首个问题：`proof`
- 理由：Eisenstein applies, but its divisibility conditions are not checked explicitly.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-070

### 题目

Show that 2 is divisible by $(1+i)^{2}$ in $\mathbb{Z}[i]$.

### ProofNet 原证明

\begin{proof}

We have $(1+i)^2=1+2 i-1=2 i$, so $2=-i(1+i)^2$.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The displayed Gaussian-integer factorization is correct.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-084

### 题目

Let $p$ be a prime integer. Prove that the polynomial $x^n-p$ is irreducible in $\mathbb{Q}[x]$.

### ProofNet 原证明

\begin{proof}

   Straightforward application of Eisenstein's criterion with $p$.  

\end{proof}

### AI 首审

- 来源状态：`false_or_underspecified_theorem`
- 首个问题：`theorem`
- 理由：The statement does not restrict n to a positive integer; for n=0 it is not the claimed irreducibility problem.
- 建议用途：`natural_missing_assumption`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-034

### 题目

If $r$ is rational $(r \neq 0)$ and $x$ is irrational, prove that $r+x$ is irrational.

### ProofNet 原证明

\begin{proof}

    If $r$ and $r+x$ were both rational, then $x=r+x-r$ would also be rational.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Closure of the rationals under subtraction gives the contradiction.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-153

### 题目

If $k = 1$ and $\mathbf{x} \in R^{k}$, prove that there does not exist $\mathbf{y} \in R^{k}$ such that $\mathbf{y} \neq 0$ but $\mathbf{x} \cdot \mathbf{y}=0$

### ProofNet 原证明

\begin{proof}

    Not true when $k=1$, since the product of two nonzero real numbers is nonzero.

\end{proof}

### AI 首审

- 来源状态：`false_theorem`
- 首个问题：`theorem`
- 理由：x may be zero; then every nonzero y has x dot y equal to zero.
- 建议用途：`natural_false_theorem`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-007

### 题目

Let $E$ be a bounded set in $R^{1}$. Prove that there exists a real function $f$ such that $f$ is uniformly continuous and is not bounded on $E$.

### ProofNet 原证明

\begin{proof}

    The function $f(x)=x$ is uniformly continuous on the entire line, but not bounded.

\end{proof}

### AI 首审

- 来源状态：`false_theorem`
- 首个问题：`theorem`
- 理由：A uniformly continuous real function is bounded on every bounded subset; f(x)=x is bounded on bounded E.
- 建议用途：`natural_false_theorem`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-247

### 题目

Let $x$ be an element of $G$. Prove that if $|x|=n$ for some positive integer $n$ then $x^{-1}=x^{n-1}$.

### ProofNet 原证明

\begin{proof}

    We have $x \cdot x^{n-1}=x^n=1$, so by the uniqueness of inverses $x^{-1}=x^{n-1}$.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The inverse identity follows immediately from x^n=1.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-250

### 题目

Let $f$ be a continuous real function on a metric space $X$. Let $Z(f)$ (the zero set of $f$ ) be the set of all $p \in X$ at which $f(p)=0$. Prove that $Z(f)$ is closed.

### ProofNet 原证明

\begin{proof}

    $Z(f)=f^{-1}(\{0\})$, which is the inverse image of a closed set. Hence $Z(f)$ is closed.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The zero set is the inverse image of the closed singleton under a continuous map.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-113

### 题目

An element $x$ of a ring $R$ is called nilpotent if some power of $x$ is zero. Prove that if $x$ is nilpotent, then $1+x$ is a unit in $R$.

### ProofNet 原证明

\begin{proof}

    If $x^n=0$, then

$$

(1+x)\left(\sum_{k=0}^{n-1}(-1)^k x^k\right)=1+(-1)^{n-1} x^n=1 .

$$

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The finite geometric-series product equals one because x^n=0.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-123

### 题目

Let $R$ be a commutative ring with $1 \neq 0$. Prove that if $a$ is a nilpotent element of $R$ then $1-a b$ is a unit for all $b \in R$.

### ProofNet 原证明

\begin{proof}

    $\mathfrak{N}(R)$ is an ideal of $R$. Thus for all $b \in R,-a b$ is nilpotent. Hence $1-a b$ is a unit in $R$.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Nilpotence is preserved by multiplication in a commutative ring, and one plus a nilpotent is a unit.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-198

### 题目

Prove that the center of the product of two groups is the product of their centers.

### ProofNet 原证明

\begin{proof}

    We have that $(g_1, g_2)\cdot (h_1, h_2) = (h_1, h_2)\cdot (g_1, g_2)$ if and only if $g_1h_1 = h_1g_1$ and $g_2h_2 = h_2g_2$. 

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Commutation in a direct product is coordinatewise, which characterizes the center.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-025

### 题目

Suppose $f$ is continuous in a region $\Omega$. Prove that any two primitives of $f$ (if they exist) differ by a constant.

### ProofNet 原证明

\begin{proof}

    Suppose $F_1$ adn $F_2$ are primitives of $F$. Then $(F_1-F_2)^\prime = f - f = 0$, therefore $F_1$ and $F_2$ differ by a constant. 

\end{proof}

### AI 首审

- 来源状态：`valid_with_minor_typo`
- 首个问题：`proof`
- 理由：The proof writes primitives of F instead of f, but the derivative argument is sound.
- 建议用途：`unchanged_valid_after_typo_normalization`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-121

### 题目

Deduce that $|a b|=|b a|$ for all $a, b \in G$.

### ProofNet 原证明

\begin{proof}

    Let $a$ and $b$ be arbitrary group elements. Letting $x=a b$ and $g=a$, we see that

$$

|a b|=\left|a^{-1} a b a\right|=|b a| .

$$

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：ab and ba are conjugate, so they have the same order.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-015

### 题目

Prove that $x^2+1$ is irreducible in $\mathbb{F}_7$

### ProofNet 原证明

\begin{proof}

    If $p(x)=x^2+1$ were reducible, its factors must be linear. But no $p(a)$ for $a\in\mathbb{F}_7$ evaluates to 0, therefore $x^2+1$ is irreducible. 

\end{proof}

### AI 首审

- 来源状态：`valid_with_gap`
- 首个问题：`proof`
- 理由：For a quadratic, absence of roots proves irreducibility, but the seven evaluations are only asserted.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-088

### 题目

Prove that $\sqrt{n+1}-\sqrt{n} \rightarrow 0$ as $n \rightarrow \infty$.

### ProofNet 原证明

\begin{proof}

    $$

\sqrt{n+1}-\sqrt{n}=\frac{(\sqrt{n+1}-\sqrt{n})(\sqrt{n+1}+\sqrt{n})}{\sqrt{n+1}+\sqrt{n}}=\frac{1}{\sqrt{n+1}+\sqrt{n}}<\frac{1}{2 \sqrt{n}}

$$

\end{proof}

### AI 首审

- 来源状态：`valid_with_gap`
- 首个问题：`proof`
- 理由：The rationalization is correct; the final squeeze-to-zero step is implicit.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-013

### 题目

Suppose $E\subset\mathbb{R}^k$ is uncountable, and let $P$ be the set of condensation points of $E$. Prove that $P$ is perfect.

### ProofNet 原证明

\begin{proof}

    We see that $E \cap W$ is at most countable, being a countable union of at-most-countable sets. It remains to show that $P=W^c$, and that $P$ is perfect.

\end{proof}

### AI 首审

- 来源状态：`invalid_or_incomplete`
- 首个问题：`proof`
- 理由：W is undefined in the supplied proof and neither P=W^c nor perfection is established.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-086

### 题目

Let $H$ be the subgroup generated by two elements $a, b$ of a group $G$. Prove that if $a b=b a$, then $H$ is an abelian group.

### ProofNet 原证明

\begin{proof}

    Since $a$ and $b$ commute, for any $g, h\in H$ we can write $g=a^ib^j$ and $h = a^kb^l$. Then $gh = a^ib^ja^kb^l = a^kb^la^ib^j = hg$. Thus $H$ is abelian. 

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Every word in commuting generators has the stated form, and such words commute.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-092

### 题目

Show that there is an infinite number of solutions to $x^2 = -1$ in the quaternions.

### ProofNet 原证明

\begin{proof}

Let $x=a i+b j+c k$ then

$$

x^2=(a i+b j+c k)(a i+b j+c k)=-a^2-b^2-c^2=-1

$$

This gives $a^2+b^2+c^2=1$ which has infinitely many solutions for $-1<a, b, c<1$.

\end{proof}

### AI 首审

- 来源状态：`valid_with_gap`
- 首个问题：`proof`
- 理由：The conclusion is correct, but cancellation of quaternion cross terms is omitted.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-182

### 题目

Prove that if $u$ is a unit in $R$ then so is $-u$.

### ProofNet 原证明

\begin{proof}

    Solution: Since $u$ is a unit, we have $u v=v u=1$ for some $v \in R$. Thus, we have

$$

(-v)(-u)=v u=1

$$

and

$$

(-u)(-v)=u v=1 .

$$

Thus $-u$ is a unit.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The element -v is explicitly shown to be a two-sided inverse of -u.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-010

### 题目

Let $G$ be a finite group of composite order $n$ with the property that $G$ has a subgroup of order $k$ for each positive integer $k$ dividing $n$. Prove that $G$ is not simple.

### ProofNet 原证明

\begin{proof}

    Solution: Let $p$ be the smallest prime dividing $n$, and write $n=p m$. Now $G$ has a subgroup $H$ of order $m$, and $H$ has index $p$. Then $H$ is normal in $G$.

\end{proof}

### AI 首审

- 来源状态：`valid_with_gap`
- 首个问题：`proof`
- 理由：The proof invokes without justification the theorem that a subgroup of index equal to the smallest prime divisor is normal.
- 建议用途：`natural_proof_gap`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-119

### 题目

Show that the collection $$\mathcal{T}_\infty = \{U | X - U \text{ is infinite or empty or all of X}\}$$ does not need to be a topology on the set $X$.

### ProofNet 原证明

\begin{proof}

    Let $X=\mathbb{R}, U_1=(-\infty, 0)$ and $U_2=(0, \infty)$. Then $U_1$ and $U_2$ are in $\mathcal{T}_{\infty}$ but $U_1 \cup U_2=\mathbb{R} \backslash\{0\}$ is not.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The two chosen sets belong to the collection while their union does not.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-234

### 题目

Prove that $x^2+x+1$ is irreducible in the field $\mathbb{F}_2$.

### ProofNet 原证明

\begin{proof}

    If $x^2+x+1$ were reducible in $\mathbb{F}_2$, its factors must be linear. But we neither have that $0^2+0+1=$ nor $1^2+1+1=0$, therefore $x^2+x+1$ is irreducible.  

\end{proof}

### AI 首审

- 来源状态：`invalid_textual_step`
- 首个问题：`proof`
- 理由：The evaluation at zero is syntactically incomplete, although the intended finite-field argument is clear.
- 建议用途：`natural_symbolic_error`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-190

### 题目

If $A$ and $B$ are disjoint closed sets in some metric space $X$, prove that they are separated.

### ProofNet 原证明

\begin{proof}

    We are given that $A \cap B=\varnothing$. Since $A$ and $B$ are closed, this means $A \cap \bar{B}=\varnothing=\bar{A} \cap B$, which says that $A$ and $B$ are separated.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Closedness gives A intersect closure(B) and closure(A) intersect B both empty.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-225

### 题目

If $P \triangleleft G$, $P$ a $p$-Sylow subgroup of $G$, prove that $\varphi(P) = P$ for every automorphism $\varphi$ of $G$.

### ProofNet 原证明

\begin{proof}

    Let $\phi$ be an automorphism of $G$. Let $P$ be a normal sylow p-subgroup. $\phi(P)$ is also a sylow-p subgroup. But since $P$ is normal, it is unique. Hence $\phi(P)=P$.

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：Automorphisms preserve Sylow order, and a normal Sylow subgroup is unique.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

## proofnet250-148

### 题目

If $z$ is a complex number such that $|z|=1$, that is, such that $z \bar{z}=1$, compute $|1+z|^{2}+|1-z|^{2}$.

### ProofNet 原证明

\begin{proof}

    $|1+z|^2=(1+z)(1+\bar{z})=1+\bar{z}+z+z \bar{z}=2+z+\bar{z}$. Similarly $|1-z|^2=(1-z)(1-\bar{z})=1-z-\bar{z}+z \bar{z}=2-z-\bar{z}$. Hence

$$

|1+z|^2+|1-z|^2=4 \text {. }

$$

\end{proof}

### AI 首审

- 来源状态：`valid`
- 首个问题：`None`
- 理由：The two norm expansions sum to four using z times conjugate(z)=1.
- 建议用途：`unchanged_valid`

### 人工复核

填写：`确认` 或 `纠正：<理由>`

---

