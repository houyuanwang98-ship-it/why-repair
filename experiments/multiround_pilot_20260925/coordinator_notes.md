# Coordinator-only design expectations — NOT human Gold

Do not pass this file to semantic generator/reviewer roles.

- branch_pair intentionally contains wrong polynomial expansions at nodes 1 and 2,
  with independent graph branches feeding a common target. Intended diagnostic:
  check first-error 1 then 2, two applied repairs, and no completion before both.
  This is an expectation to test, not a forced or authoritative verdict.
- dependent_pair intentionally misrepresents an odd integer at node 1 and gives a
  wrong squared expression at node 2. The downstream requirement can be impossible
  to preserve under a single-node repair. A contract rejection is a meaningful
  limitation of the fixed-region pilot, not evidence that the theorem is false.
- valid_control is a correct standard even-square proof with a short implicit
  divisibility argument; expected no gratuitous repair.

These expectations were written by the coordinating assistant, not independently
validated by a human. Do not calculate a benchmark accuracy from them.
