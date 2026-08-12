# M3-alpha: Person B module runner and metrics

Status: implemented for isolated development; not frozen as M3 Evaluator v1.

## Scope

M3-alpha starts the Person B execution work while Person A's independent M2
annotation is unavailable. It adds an adapter-neutral module runner and the
pre-registered M3 metrics without consuming M2 labels, generating Gold, or
changing the frozen M1 v0.3 contracts.

The implementation is `harness/m3_alpha.py`. It supports these independently
measurable modules:

- `segmentation`;
- `classification`;
- `dependency`;
- `localization`;
- `verdict`.

Every module run declares either `gold_upstream` or `predicted_upstream`.
`gold_upstream` isolates the module by supplying reviewed upstream artifacts;
`predicted_upstream` measures pipeline behavior. The mode is mandatory and is
preserved in every report so an upstream segmentation failure cannot silently
be counted as a mathematical verdict failure.

## Adapter and run audit

The adapter callable receives a module name and one sample, then returns an
`AdapterResponse`. The runner records:

- adapter, model, and prompt versions;
- a deterministic SHA-256 digest of the ordered inputs;
- sample and model-call counts;
- input and output tokens;
- estimated cost when every call reports it;
- total and per-call latency.

This M3-alpha manifest supplements rather than replaces the frozen M1
`RunManifest`. No mathematical label is inferred from usage metadata.

## Metrics

The alpha metric layer implements:

- segmentation boundary precision, recall, and F1;
- node classification macro-F1;
- directed dependency-edge precision, recall, and F1;
- exact first-error localization accuracy;
- node-verdict macro-F1;
- false acceptance rate over Gold-invalid nodes.

Metric functions currently accept explicit normalized inputs. The final M2
Gold adapter must not be implemented until both members approve the M2-to-M1
mapping and complete adjudication.

`evaluate_dataset()` aligns prediction and normalized Gold artifacts by exact
`sample_id`, rejects missing or extra samples, and namespaces boundaries and
edges by sample. This is the stable seam for the later jointly approved Gold
adapter; benchmark rows cannot be compared positionally or silently dropped.

## Verification

Run:

```text
python -m unittest tests.test_m3_alpha -v
python -m unittest discover -s tests -v
```

On 2026-08-11, the M3-alpha suite passed 17 tests and the full repository passed
153 tests.

## Deferred exit conditions

M3-alpha is not the M3 freeze. The following remain blocked on Person A and
joint review:

- final Evaluator prompts and response contracts;
- a jointly approved M2-to-M1 Gold adapter;
- official benchmark metrics and thresholds;
- non-author review of mathematical semantics;
- freezing Evaluator v1.
