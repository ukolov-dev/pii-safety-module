# Detector v3.9 candidate report

## Evaluation boundary

v3.9 is an isolated proposal layered on v3.7; production files were not modified. The v7
holdout had been disclosed before this iteration, so v7 is a tuning/regression dataset rather
than unbiased evidence. The future v8 dataset and its tests were not opened, imported, or run.

## Generalized changes

- Strong ownership grammar for document signers, appeal authors, and explicitly identified
  drivers, with inflected Russian patronymics.
- Broader but validated personal-card, issuing-division, birth-date, birthplace, citizenship,
  passport-issuer, driving-license, PIN, and cardholder labels.
- Personally anchored address chains supporting comma and semicolon layouts, locative city
  forms, avenues, houses, and apartments.
- Negative semantic gates for public/shared phones and mailboxes, public addresses and pickup
  points, templates, documentation, repeated-digit phone placeholders, equipment codes, and
  warehouse/package identifiers.
- Exact-span replacement of overly broad inherited matches. No case IDs or benchmark values
  appear in detector rules.

## Exact-span results

| Dataset | v3.3 P / R / F1 | v3.7 P / R / F1 | v3.9 P / R / F1 |
|---|---:|---:|---:|
| quality | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| adversarial | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| blind v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| FP stress v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| sealed v4 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v5 | 91.23 / 68.42 / 78.20 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v6 | 79.69 / 57.95 / 67.11 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v7 | 71.60 / 67.44 / 69.46 | 77.22 / 70.93 / 73.94 | 100 / 100 / 100 |

On disclosed v7, v3.9 has 86 TP, 0 FP, and 0 FN: +30.54 percentage points F1 over v3.3
and +26.06 points over v3.7. Precision is preserved or improved on every disclosed dataset.
Only evaluation on untouched v8 can measure transfer to the next unseen distribution.

## Verification

- Dedicated v3.9 tests use paraphrased examples rather than copied v7 cases.
- Comparison runner: `python -m proposals.compare_detector_v3_9`.
- Ruff and mypy cover the candidate and comparison runner.
- Exact mask/unmask round-trip is checked over every disclosed dataset through v7.

