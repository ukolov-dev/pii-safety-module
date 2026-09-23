# Detector v3.7 candidate report

## Scope and leakage boundary

This is an isolated proposal; production detector files were not changed. The v3.7
implementation was developed after `sealed_holdout_v6.json` had been disclosed, so v6 is a
tuning set and no longer an unbiased estimate. The future v7 dataset and its tests were not
opened, read, imported, or executed.

## Design

The candidate composes v3.5 and adds reusable recognizers rather than case identifiers or
literal benchmark values:

- ownership-gated Russian person morphology and flexible `Ф.И.О.` punctuation;
- wrapper-safe email spans, validated personal INN, Luhn-valid slash-separated cards;
- passport/division, numeric birth-date, birthplace, citizenship, issuer and driver-license
  label variants;
- personally anchored address components and payment-secret/cardholder labels;
- inflection-aware suppression for public contacts, organisations, documentation, templates,
  catalogues, placeholders and non-person equipment identifiers.

Suppression is applied to both inherited and new entities. It is semantic and local; it does
not contain benchmark case IDs or target values.

## Exact-span comparison on disclosed datasets

| Dataset | v3.3 P / R / F1 | v3.7 P / R / F1 | F1 delta |
|---|---:|---:|---:|
| quality | 100 / 100 / 100 | 100 / 100 / 100 | 0 pp |
| adversarial | 100 / 100 / 100 | 100 / 100 / 100 | 0 pp |
| blind v3 | 100 / 100 / 100 | 100 / 100 / 100 | 0 pp |
| FP stress v3 | 100 / 100 / 100 | 100 / 100 / 100 | 0 pp |
| sealed v4 | 100 / 100 / 100 | 100 / 100 / 100 | 0 pp |
| disclosed sealed v5 | 91.23 / 68.42 / 78.20 | 100 / 100 / 100 | +21.80 pp |
| disclosed sealed v6 | 79.69 / 57.95 / 67.11 | 100 / 100 / 100 | +32.89 pp |

For v6, v3.7 produced 88 TP, 0 FP, and 0 FN. Across every disclosed dataset it preserves or
improves v3.3 precision. These numbers demonstrate regression safety on known data, not the
requested unseen-v7 improvement; only an untouched v7 evaluation can establish that.

## Verification

- Candidate unit tests: 6 passed.
- Ruff: passed for detector, comparison runner, and tests.
- Mypy: passed for detector and comparison runner.
- Reversible mask/unmask: 397/397 exact round trips over all disclosed datasets.
- Comparison runner: `python -m proposals.compare_detector_v3_7`.

