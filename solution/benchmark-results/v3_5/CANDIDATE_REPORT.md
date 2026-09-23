# Candidate v3.5 evaluation

## Scope

- Baseline: `proposals/detector_v3_3.py` (production v3.3 logic).
- Candidate: `proposals/detector_v3_5.py`.
- Production files were not changed.
- `sealed_holdout_v6.json` and its tests were not read or executed.
- v3.5 was designed from production behavior, disclosed v5 errors, requirements, and
  previously public benchmark sets.

## General changes

- Inflected and uppercase three-part Russian names behind personal ownership syntax.
- Luhn-validated card numbers with spaces, hyphens, dots, or no separators.
- More passport, issuing-division, issuer, driver-license, birth-date, citizenship,
  birthplace, cardholder, and personal-address labels.
- Semantic distinction between birth dates, passport issue dates, and event dates.
- Additional ownership gates for personal addresses and payment data.
- Suppression for shared mailboxes, public/example card numbers, documentation values,
  and CVV-like product codes.

## Exact-span results

| Dataset | v3.3 precision | v3.3 recall | v3.3 F1 | v3.5 precision | v3.5 recall | v3.5 F1 |
|---|---:|---:|---:|---:|---:|---:|
| Quality | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| Adversarial | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| Blind v3 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| FP stress v3 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| Sealed v4 (disclosed) | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| Sealed v5 (disclosed) | 91.23% | 68.42% | 78.20% | 100.00% | 100.00% | 100.00% |

On disclosed v5, v3.5 improves F1 by **21.80 percentage points**, with precision
improving rather than regressing. This does not predict the exact result on an unseen
holdout; v6 must remain untouched until the candidate is frozen.

## Reversibility and engineering gates

- Exact mask/unmask round-trip: **307/307 cases (100%)** across the six permitted sets.
- Candidate-specific tests: **7 passed**.
- Full test suite: **68 passed**.
- Ruff: passed.
- mypy: passed.
- One existing third-party Starlette/httpx deprecation warning remains unrelated to v3.5.
