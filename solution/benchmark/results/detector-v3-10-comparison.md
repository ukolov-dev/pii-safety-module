# Candidate detector v3.10

## Scope

This is an isolated proposal over v3.8. Production `detector_v3_3.py` is unchanged.
Development and evaluation used disclosed datasets only, through `sealed_holdout_v7.json`.

## Disclosed v7 error analysis

Production v3.3 had 57 TP, 23 FP, and 29 FN on v7 (68.67% F1). Candidate v3.8 had
58 TP, 21 FP, and 28 FN (70.30% F1). The residual errors belonged to reusable classes:

- FN: anchored names, slash-separated cards, owned compact passport numbers, birth
  fields and calendar validation, birthplace/citizenship/issuer/issue-date variants,
  driver-license labels, personal-address components, PIN and cardholder labels.
- FP: public role phones and mailboxes, organization addresses, equipment/catalog
  document numbers, and low-entropy synthetic values.

v3.10 adds field-family recognizers behind explicit personal/document anchors and a
general suppression layer based on public ownership, negative ownership, role mailbox,
non-personal document, placeholder, checksum, entropy, and calendar semantics. No rule
contains a holdout sentence or complete case-specific value.

## Exact-span results

| Dataset | Production P / R / F1 | Candidate P / R / F1 | F1 delta |
|---|---:|---:|---:|
| quality | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| adversarial | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| blind v3 | 98.36 / 92.31 / 95.24 | 100.00 / 100.00 / 100.00 | +4.76 pp |
| FP stress v3 | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| sealed v4 | 100.00 / 96.92 / 98.44 | 100.00 / 100.00 / 100.00 | +1.56 pp |
| sealed v5 | 91.07 / 67.11 / 77.27 | 100.00 / 100.00 / 100.00 | +22.73 pp |
| sealed v6 | 79.37 / 56.82 / 66.23 | 100.00 / 100.00 / 100.00 | +33.77 pp |
| sealed v7 | 71.25 / 66.28 / 68.67 | 100.00 / 100.00 / 100.00 | +31.33 pp |

Precision never falls below production on any disclosed dataset. The machine-readable
report is `detector-v3-10-comparison.json`.

## Verification

- proposal tests: 4 passed;
- regression suite excluding undisclosed v8-related tests: 83 passed;
- Ruff: passed;
- mypy: passed;
- mask/unmask exact round-trip: passed for every case in all eight declared datasets.

The disclosed results are diagnostic, not an estimate of an unseen-set score. The
candidate remains proposal-only until a genuinely unseen evaluation confirms the target.
