# Detector v3.27 proposal

## Scope

`app/detection/detector_v3_27.py` is an isolated candidate over production
v3.26. It was developed from disclosed datasets through v16. No later blind
dataset was read or used. The production export in `app/detection/__init__.py`
is unchanged.

## General changes

- Added clause-bounded grammars for inflected three-part Russian names after
  ownership/action phrases.
- Added owned address-record parsing for multiword cities, postal codes,
  streets, houses and apartments, including abbreviated `д.` / `кв.` fields.
- Added reordered passport fields, passport issue dates across short clauses,
  birth-date phrases and driver-license variants.
- Added clause-local suppression for organisation contacts, role mailboxes,
  public addresses, examples and identifiers of technical objects.
- Preserved source offsets, deterministic overlap resolution, semantic date
  checks and the existing bounded path for inputs of at least 100,000 chars.

## Disclosed quality

Exact `(type, start, end)` comparison was run with
`proposals/compare_detector_v3_27.py` over 17 disclosed datasets / 1,647 cases
from `benchmark/`.

| Scope | Detector | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| All disclosed | v3.26 | 1,412 | 24 | 43 | 98.33% | 97.04% | 97.68% |
| All disclosed | v3.27 | 1,455 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| sealed v15 | v3.26 | 138 | 6 | 6 | 95.83% | 95.83% | 95.83% |
| sealed v15 | v3.27 | 144 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| sealed v16 | v3.26 | 136 | 11 | 16 | 92.52% | 89.47% | 90.97% |
| sealed v16 | v3.27 | 152 | 0 | 0 | 100.00% | 100.00% | 100.00% |

The v16 gain is **+9.03 percentage points F1**. No disclosed dataset regressed
in F1. Exact masks matched gold in 1,647/1,647 cases; masking/unmasking restored
1,647/1,647 inputs. This perfect disclosed score increases overfitting risk and
therefore cannot replace an untouched blind evaluation.

## Verification

- Full suite: `206 passed`.
- Candidate-specific tests: `5 passed`.
- Ruff: pass.
- Strict mypy over `app`, the comparator and candidate tests: pass.
- Direct 100k-token detection, 20 iterations: median 390.10 ms, p95 394.92 ms,
  max 395.68 ms; three expected entities found.
- Candidate overhead against v3.26 on the deterministic 20-token sample:
  median 1.26 ms vs 1.13 ms; p95 1.32 ms vs 1.19 ms.

## Limits and promotion condition

The disclosed result is not evidence of 95% on the portal's closed dataset.
Promotion should require an untouched blind set with F1 and precision at least
95%, exact round-trip 100%, no disclosed quality-gate regression and a repeat
of the service-level load test after the production export is switched.
