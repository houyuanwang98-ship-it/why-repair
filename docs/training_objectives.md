# Training Objectives for the Algebra Proof Repair Agent

This project is not trying to train a model to prove every mathematical
theorem. The training target is narrower: make an agent better at diagnosing
and repairing natural-language algebra proofs under a fixed task structure.

The core mapping is:

```text
Input:
  theorem statement
  flawed proof
  algebra knowledge base
  bridge lemma bank

Output:
  proof dependency graph
  node-level obligations
  first problematic node
  error diagnosis
  minimal repair
```

This mapping can be decomposed into several trainable objectives.

## 1. Proof Node Identification

The model should learn how to split a natural-language proof into meaningful
proof nodes:

```text
proof text -> proof_nodes
```

It should distinguish between explanatory text, mathematical claims, newly
introduced assumptions, and inference steps.

Optimize:

```text
node segmentation accuracy
claim extraction accuracy
dependency extraction accuracy
```

## 2. Obligation Generation

Each proof node should be converted into a local proof obligation:

```text
Context_i |- Claim_i
```

Example:

```text
Context:
  T: V -> V is linear
  V is finite-dimensional
  ker(T) = {0}

Claim:
  im(T) = V
```

The model should learn to select the right local context and formulate the
current claim as a checkable obligation.

Optimize:

```text
obligation correctness
context selection accuracy
missing premise detection
```

## 3. Node Status Classification

This is the central supervised task:

```text
obligation + retrieved lemmas -> node_status
```

Allowed node statuses:

```text
closed
valid_with_gap
missing_bridge_lemma
missing_assumption
theorem_misuse
algebraic_invalidity
false_theorem
downstream_invalid
```

Optimize:

```text
step validity classification
gap vs invalid distinction
first invalid step localization
```

This is the most important research target. Many systems incorrectly mark an
underexplained but valid proof step as an error. This project should explicitly
separate proof gaps from genuine invalid reasoning.

## 4. Retrieval Selection

If the system has a theorem bank and a bridge lemma bank, the model can also
learn which rules to retrieve for each obligation:

```text
current obligation -> relevant theorem, bridge lemma, fallacy pattern
```

Example for quotient groups:

```text
Retrieve:
  normal subgroup
  coset multiplication well-definedness
  representative dependence

Avoid:
  unrelated group homomorphism theorems
```

Optimize:

```text
relevant theorem retrieval
bridge lemma retrieval
fallacy pattern retrieval
```

## 5. Error Diagnosis

When a node does not close, the model should diagnose why:

```text
Is a bridge lemma missing?
Is an assumption missing?
Is a theorem being misused?
Is the algebraic manipulation invalid?
Is the theorem statement itself false?
```

Optimize:

```text
error_type accuracy
mathematical diagnosis accuracy
```

## 6. Minimal Repair Generation

The repair target is not to rewrite the entire proof. The target is the
smallest local change that fixes the first problematic node.

The model should learn:

```text
invalid node + diagnosis + retrieved lemmas -> minimal repair
```

Common repair actions:

```text
insert_bridge_lemma
add_missing_assumption
replace_invalid_step
weaken_claim
give_counterexample
```

Optimize:

```text
repair minimality
repair correctness
repair consistency with previous proof
```

## Overall Training Objective

In one sentence, the training process optimizes the agent's ability to convert
natural-language algebra proofs into local proof obligations, judge whether
each obligation is closed, a gap, or a genuine error using retrieved knowledge,
and then produce a minimal repair.

A paper-style objective can be written as:

```text
maximize P(
  dependency_graph,
  obligation_trace,
  node_status,
  error_type,
  minimal_repair
  | theorem, proof, retrieved_knowledge
)
```

## Practical Training Stages

Do not start with end-to-end training. A more practical path is:

```text
Stage 1: Train the node_status classifier.
Stage 2: Train the obligation generator.
Stage 3: Train the repair generator.
Stage 4: Compose the modules into an agent.
```

The first target should be the node status classifier, especially:

```text
closed vs valid_with_gap vs invalid
```

This distinction is the main difference between this project and ordinary proof
repair systems.
