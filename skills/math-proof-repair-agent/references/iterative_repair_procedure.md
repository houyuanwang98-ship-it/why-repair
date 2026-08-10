# Iterative Repair Procedure

Read this reference only in repair mode, after every checker obligation is
resolved. Grading mode must not load or apply this file.

The repair procedure scans proof nodes sequentially and attempts to fix each
problematic node. It maintains an ordered list of accepted claims (initial
theorem assumptions plus all nodes processed so far, including inserted bridge
steps) and produces a repaired proof with minimal inserted steps.

### Step 1: Classify the node error

Read the node's `status` from the diagnosis output:

- `missing_bridge_lemma` - the node is correct but omitted a standard argument.
- `missing_assumption`, `theorem_misuse`, `algebraic_invalidity`,
  `false_local_claim`, `false_theorem`, `target_mismatch` - the node contains a
  non-gap error.

### Step 2A: Repair a gap (missing_bridge_lemma)

If the node is a `missing_bridge_lemma`:

1. Identify the node's direct dependency claims from `depends_on`. These are
   the conditions already established before this node.
2. Identify the node's `self_contained_claim` as the target conclusion.
3. Construct a short step-by-step derivation that starts from the dependency
   claims and ends at the target conclusion. Each step must be a single
   mathematical inference with an explicit justification (rule, definition,
   earlier claim, or assumption). The derivation should read like a natural
   self-contained solution to the subproblem:

   ```text
   Dependencies (conditions) |- Target conclusion
   ```

4. Insert the generated derivation steps **between** the dependency nodes and
   the current node in the proof sequence. These inserted steps become part of
   the accepted claims for subsequent node checking.
5. Display every inserted bridge step in **red font** (for example, wrap it in
   `<span style="color:red">...</span>` for HTML-capable output or use the
   output format's equivalent red styling) so it is visually distinct from
   original proof nodes.
6. Update `first_gap_step` if this was the first unresolved gap.
7. **Continue** to the next node (go to Step 1) - the repair is local and
   does not affect the validity of later nodes.

> Example: If node 3 claims `x = y` and depends on node 1 (`a != 0`) and
> node 2 (`a*x = a*y`), the repair generates:
> ```
> Inserted step 3a: Since a != 0, a has a multiplicative inverse a^{-1}.
> Inserted step 3b: Multiply both sides of a*x = a*y by a^{-1}:
>                   a^{-1}*(a*x) = a^{-1}*(a*y).
> Inserted step 3c: By associativity, (a^{-1}*a)*x = (a^{-1}*a)*y,
>                   i.e., 1*x = 1*y, so x = y.
> ```
> Node 3 then becomes `closed` with these inserted steps as its justification.

### Step 2B: Handle a non-gap error

If the node has a non-gap error (`missing_assumption`, `theorem_misuse`,
`algebraic_invalidity`, `false_local_claim`, `false_theorem`, or
`target_mismatch`):

1. Determine whether the node's `self_contained_claim` is derivable from the
   **original problem conditions** (the theorem statement + the theorem
   assumptions), ignoring any missing local premises. Use your mathematical
   judgment: is the claim mathematically true under the problem's global
   hypotheses?

2. **If the claim is NOT derivable** from the problem conditions:
   - Delete this node from the proof node list because its conclusion cannot
     be derived from the given conditions.
   - Scan all later nodes in order. If an `introduction` node explicitly
     references or cites the deleted node as a previously established result,
     delete that introduction node too. Keep nodes that merely list the
     deleted node in `depends_on`; dependency alone does not trigger deletion.
   - Record every deletion in `deleted_nodes` with its node ID and reason.
   - Record the first deleted irreparable node in `first_irreparable_error`.
   - Continue with the next remaining node. Do not stop the repair loop.

3. **If the claim IS derivable** from the problem conditions:
   - Generate a step-by-step derivation from the problem conditions to the
     target conclusion. This derivation should:
     - Use the original theorem assumptions as the starting point.
     - Refer to earlier accepted proof nodes wherever they are helpful
       (to avoid redundant reasoning).
     - Fill in any missing premises or rule applications that the original
       proof step omitted.
     - Each step must be a single inference with explicit justification.
   - Insert the derivation steps before the current node, replacing the
     original faulty step.
   - Display every inserted replacement step in **red font**, using the same
     output-specific styling as Step 2A.
   - The node becomes `closed` after repair.
   - **Continue** to the next node (go to Step 1).

### Step 2C: Global proof completion

After all nodes have been processed, including local repairs and deletions,
perform a global proof-completion pass:

1. Collect every remaining valid original node and every inserted bridge or
   replacement step.
2. Start from the theorem assumptions and inspect the remaining nodes in
   order.
3. Identify every break in the logical flow where the surviving nodes do not
   form a connected derivation to the final conclusion.
4. Insert only the derivation steps needed to bridge those breaks. Reuse the
   surviving claims as much as possible and do not add redundant steps.
5. Display every globally inserted completion step in **red font**, using the
   same output-specific styling as Steps 2A and 2B.
6. Record these steps separately in `completion_steps`.

For example, if nodes 3 and 4 are deleted because node 3 is irreparable and
node 4 is an introduction that cites node 3, connect node 2 to node 5 using
only the assumptions, surviving nodes, and the minimum required completion
steps.

### Step 3: Continue, delete, or complete

- If the node was repaired (Step 2A or Step 2B case 3), move to the next node
  and return to Step 1.
- If the node was deleted (Step 2B case 2), move to the next remaining node
  and return to Step 1.
- After all nodes are processed, run Step 2C and return the repaired proof with
  inserted bridge steps, deleted nodes, and completion steps in their correct
  positions.

### Repair invariants

1. Inserted bridge steps must be minimal: do not add steps that are already
   explicit in the original proof or that are logically redundant.
2. The repaired proof order must be consistent: inserted steps go immediately
   before the node they repair, after that node's declared dependencies.
3. A repaired gap does not change the original node's status in the
   `proof_graph` - create a separate `inserted_steps` list in the output to
   record the new steps. The updated output format is:

```text
{
  "repaired_proof": [
    {"type": "original", "node_id": 1, "claim": "..."},
    {"type": "original", "node_id": 2, "claim": "..."},
    {"type": "inserted", "repairs_node": 3, "step": "a", "claim": "..."},
    {"type": "inserted", "repairs_node": 3, "step": "b", "claim": "..."},
    {"type": "original", "node_id": 3, "claim": "..."},
    ...
  ],
  "deleted_nodes": [
    {"node_id": 4, "reason": "erroneous conclusion not derivable from conditions"},
    {"node_id": 5, "reason": "introduction node referencing deleted node 4"}
  ],
  "completion_steps": [
    {"step": 1, "after_node": 3, "claim": "..."},
    {"step": 2, "after_node": 6, "claim": "..."}
  ],
  "repair_outcome": "fully_repaired" | "partial_with_error",
  "first_irreparable_error": null | {"node_id": 3, "reason": "..."}
}
```

Display all `inserted_steps`, inserted entries in `repaired_proof`, and
`completion_steps` in red font.

4. For non-gap errors repaired from problem conditions, the derivation should
   still use intermediate results from earlier accepted proof nodes wherever
   applicable, to keep the repair minimal and connected to the existing proof
   structure.

12. If the helper emits unresolved adjudications, complete them as the active
    host agent, rerun the helper with those responses, and use only the
    validated resumed result.
