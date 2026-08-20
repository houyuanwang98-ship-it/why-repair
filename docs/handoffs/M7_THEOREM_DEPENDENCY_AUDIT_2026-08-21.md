# M7 theorem-dependency audit — 2026-08-21

The blind second pass explicitly requested theorem verification for six cases.
All six named results exist, but theorem existence does not by itself validate
the submitted proof. Premises, local use, and later nodes were checked
separately. The machine-readable record is
`data/benchmarks/m7/audits/m7_theorem_verification_20260821.json`.

## Outcomes

- `opc250-070`: Lucas plus CRT is correctly stated and applied; no proof error
  remains. The formalized statement is documented by
  [Mathlib](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Choose/Lucas.html).
- `opc250-119`: irrational-rotation density is valid
  ([Cornell notes](https://pi.math.cornell.edu/~mec/Summer2009/lam/equidistribution.html)),
  but `n13` is false: `floor(2^k 2^theta)` is generally not `2^k`.
- `opc250-139`: Bertrand's postulate is verified in these
  [Stanford notes](https://math.stanford.edu/~ksound/Math152A10/Bertrand.pdf).
  It supplies `q<2p`, making `n35` a repairable omitted bridge rather than a
  false claim.
- `opc250-173`: the Senge-Straus/Stewart digit-sum dependency is verified by
  [Stewart's bibliographic/full-text record](https://eudml.org/doc/152278) and
  [Cambridge notes](https://www.dpmms.cam.ac.uk/~pv270/diophantine.pdf).
  The first remaining error is the floor-removing equality at `n21`; a bounded
  floor-error repair preserves the intended conclusion.
- `opc250-211`: the grid isoperimetric result is supported by
  [Bollobás–Leader](https://digitalcommons.memphis.edu/facpubs/4558/), and the
  exact 100-vertex bound also has a two-line row/column proof. Omitting that
  upper-bound argument at `n51` is a bridge gap.
- `opc250-220`: Gauss/Dirichlet composition is supported by a published
  [composition statement and identity](https://londmathsoc.onlinelibrary.wiley.com/doi/full/10.1112/jlms.12336).
  It validates the main proof through `n55`, but not the later false arithmetic
  example at `n65`.

These are AI/host audit findings, not human signatures or Gold mutations. The
original proxy outputs and frozen annotations remain unchanged.
