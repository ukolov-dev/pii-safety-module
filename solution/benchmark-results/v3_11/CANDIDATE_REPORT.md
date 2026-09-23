# Detector v3.11 candidate report

## Evaluation boundary

v3.11 is an isolated proposal layered on v3.9; production files were not modified. The v8
holdout was disclosed before this iteration, so its result is regression/tuning evidence, not
an unbiased generalization estimate. The future v9 dataset and its tests were not opened,
imported, or executed.

## Generalized changes

- Role-owned person grammar for complaints, claims, principals, and representatives.
- Exact email span normalization for brace/backtick/assignment wrappers without re-enabling
  shared, fixture, log, example, or public mailboxes.
- Document-owned passport, division, textual issue-date, birthplace, citizenship, issuer, and
  driver-license labels.
- Personal address chains with pipe separators, registration/residence/delivery anchors,
  locative city/street forms, houses, and apartments.
- New PIN/cardholder labels plus negative gates for shared/public telephones, shared mailbox
  roles, restaurant/public addresses, device passports, specifications, training stands,
  packaging, and batch identifiers.
- Generic `code NNN-NNN` is accepted only when a passport field context exists.

Rules contain no benchmark case IDs or target values.

## Exact-span results

| Dataset | v3.3 P / R / F1 | v3.9 P / R / F1 | v3.11 P / R / F1 |
|---|---:|---:|---:|
| quality | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| adversarial | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| blind v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| FP stress v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| sealed v4 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v5 | 91.23 / 68.42 / 78.20 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v6 | 79.69 / 57.95 / 67.11 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v7 | 71.60 / 67.44 / 69.46 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v8 | 69.57 / 55.81 / 61.94 | 72.60 / 61.63 / 66.67 | 100 / 100 / 100 |

On disclosed v8, v3.11 has 86 TP, 0 FP, and 0 FN: +38.06 percentage points F1 over v3.3
and +33.33 points over v3.9. Precision is preserved or improved on every disclosed dataset.
Only untouched v9 can measure the requested next-round transfer.

## Hybrid NER research note

The related `redmadrobot-rnd/pii-guard` design supports an eventual hybrid: regex/checksum for
structured identifiers and local Russian NER for PERSON/address. No heavy model is included in
v3.11 because there is no local latency/RPS/model-size benchmark yet. A NER layer should be a
separate experiment with confidence/ownership gates and explicit SLA measurements.

## Verification

- Dedicated v3.11 tests use paraphrases not copied from v8.
- Comparison runner: `python -m proposals.compare_detector_v3_11`.
- Ruff and mypy cover detector, runner, and tests.
- Exact mask/unmask round-trip is checked over disclosed datasets through v8.

