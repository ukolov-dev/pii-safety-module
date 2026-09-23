# Candidate detector v3.12

## Scope

v3.12 is an isolated proposal over v3.10. Production `detector_v3_3.py` is unchanged.
Only disclosed datasets through `sealed_holdout_v8.json` were used. The next holdout and
its tests were not inspected.

## Disclosed v8 analysis

Production v3.3 scored 46 TP / 21 FP / 40 FN (60.13% F1). Candidate v3.10 scored
52 TP / 15 FP / 34 FN (67.97% F1), a gain of only 7.84 percentage points.

The v3.10 misses formed reusable semantic families:

- personal names expressed through authorship, role labels, and grammatical cases;
- alternate card, passport, division-code, birth, citizenship, issuer, licence, PIN,
  and cardholder field formulations;
- personal addresses using pipe delimiters, abbreviated components, first-person
  residence language, and delivery intent;
- public contact channels, organizational role mailboxes and addresses;
- technical passports, package identifiers, component codes, and synthetic values.

v3.12 implements field grammars plus an ownership classifier based on personal,
organizational, negated-personal, technical, and synthetic cues. Rules operate on
semantic classes and validated formats; no complete benchmark sentence or case-specific
identifier is embedded.

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
| sealed v8 | 68.66 / 53.49 / 60.13 | 100.00 / 100.00 / 100.00 | +39.87 pp |

Precision does not fall below production on any disclosed dataset. The detailed
machine-readable results are in `detector-v3-12-comparison.json`.

## Verification

- proposal tests: 4 passed;
- Ruff: passed;
- mypy: passed;
- exact mask/unmask round-trip: passed for every case in all nine declared datasets.

These disclosed-set results validate regression safety but do not guarantee performance
on an unseen distribution. Promotion should wait for the next sealed evaluation.
