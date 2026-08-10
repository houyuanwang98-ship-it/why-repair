# Artin Algebra Coverage Audit

Source checked from a local OCR extraction of the Artin PDF produced with
`pdftotext -layout`. The reproducible OCR and candidate files are not committed.

This audit compares the clean seed theorem bank with the full book structure.
The goal is practical proof repair coverage, not a public replacement for the
textbook. OCR-derived entries must still be reviewed against the PDF.

## Current Files

- `data/theorem_bank/artin_clean_seed_rules.jsonl`
  - 161 rewritten seed rules.
  - Recommended for first agent experiments.
- Local OCR review queue
  - 301 generated theorem, proposition, lemma, corollary, definition, and
    numbered-fact candidates were inspected during the audit.
  - The generated JSONL and Markdown views are deliberately not committed.

## Coverage Status

High-priority clean seed coverage is now present for:

- Chapter 1: matrices, row reduction, determinants, permutation matrices.
- Chapter 2: groups, cyclic groups, homomorphisms, kernels, normal subgroups,
  cosets, quotient groups, correspondence theorem, first isomorphism theorem.
- Chapter 3: fields, vector spaces, bases, dimension, direct sums.
- Chapter 4: linear maps, rank-nullity, change of basis, eigenvalues,
  characteristic polynomial, triangularization, diagonalization, Jordan form,
  generalized eigenvectors, and finite-order diagonalizability.
- Chapter 6-7: group actions, orbit-stabilizer, class equation, p-groups,
  conjugacy in symmetric groups, Sylow theorems.
- Chapter 11-12: polynomial rings, ideals, quotient rings, ring homomorphisms,
  maximal/prime ideals, Euclidean domains, PIDs, UFDs.
- Chapter 13: algebraic integers in quadratic fields, product ideals, ideal
  cancellation, prime ideals, unique factorization of ideals, class groups,
  ideal norms, prime splitting in imaginary quadratic integer rings, and real
  quadratic unit criteria.
- Chapter 8: bilinear forms, Hermitian forms, nondegenerate forms, projection,
  positive definiteness, spectral theorem, and skew-symmetric forms.
- Chapter 14: quotient modules, free modules, matrices over rings, change of
  basis, Noetherian rings, Hilbert basis theorem, and finitely generated
  abelian groups, Smith normal form over Z, module presentations, Smith normal
  form over F[t], rational canonical form, and Smith normal form reduction
  patterns.
- Chapter 10: finite complex representations, invariant subspaces, Maschke
  theorem, unitarizability, characters, character orthogonality, permutation
  characters, regular representations, Schur lemma, character table checks,
  and cyclic/S3 table patterns.
- Chapter 15: algebraic elements, irreducible polynomials, simple extensions,
  extension degree, tower law, adjoining roots, finite fields, Frobenius, and
  primitive elements.
- Chapter 16: root preservation under F-isomorphisms, splitting fields, fixed
  field theorem, Galois extension characterizations, the main theorem of
  Galois theory, normal subgroups and intermediate Galois extensions, cubic
  discriminants, quartic resolvents, cyclotomic fields, Kummer extensions,
  radical solvability, quartic decision tables, and the A5/S5 quintic
  obstruction.

## Remaining Gaps

These areas are present in the full book but are not yet deeply represented in
the clean seed bank:

- Chapter 5 matrix exponential and differential-equation material.
- Chapter 6 plane isometry and crystallographic group classification.
- Chapter 9 classical matrix groups and Lie algebra material.
- Chapter 10 detailed character-table construction for A4, A5, dihedral groups,
  and representations of SU2 beyond the seed rules.
- Chapter 13 worked class group computations, fundamental-unit algorithms, and
  lattice estimates beyond the seed rules.
- Chapter 14 extended Smith normal form worked examples, relation-module
  algorithms, Hermitian normal form, and multivariable polynomial module
  freeness tests.
- Chapter 15 deeper finite-field computations beyond the basic Frobenius and
  primitive-element rules.
- Chapter 16 detailed resolvent computations, explicit radical formulas, and
  deeper cyclotomic/Kummer computations beyond the seed rules.

## Recommendation

For the first proof-repair agent, use the clean seed bank as the active theorem
bank. It now covers the main proof moves that commonly cause undergraduate
algebra mistakes: illegal cancellation, missing normality, invalid quotient
construction, confusing image/kernel, dimension mistakes, determinant mistakes,
diagonalization over the wrong field, and field-extension degree mistakes.

The next cleaning pass should stay topic-driven rather than chapter-driven:

1. Add Chapter 10 concrete character-table rules for A4, A5, and dihedral
   groups if representation-theory problems are in scope.
2. Add Chapter 14 extended Smith normal form examples and Hermitian normal form
   rules if abelian group/module computation problems are in scope.
3. Add deeper Chapter 16 explicit resolvent and radical-formula rules if field
   theory proof repair is in scope.
4. Add Chapter 13 fundamental-unit and worked class-group computation rules
   if number-theory algebra problems are in scope.
5. Leave Chapters 5, 6, and 9 out of the first agent unless your dataset
   contains those topics.
