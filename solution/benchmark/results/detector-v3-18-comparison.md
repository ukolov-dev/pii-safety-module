# Candidate detector v3.18

## Boundary

v3.18 is a proposal layered directly on production v3.13. Production files are unchanged.
Only disclosed datasets through `sealed_holdout_v11.json` were used. The next sealed dataset and
its test were not opened or executed.

## v11 transfer analysis

Production v3.13 scored 64 TP / 18 FP / 38 FN: 78.05% precision, 62.75% recall, and
69.57% F1. v3.16 scored 68 TP / 18 FP / 34 FN: 79.07% precision, 66.67% recall, and
72.34% F1, only +2.78 percentage points over production.

The residual errors showed two transfer problems:

- recall rules were tied to individual labels rather than ownership evidence spanning a clause
  or adjacent sentence;
- suppression covered named examples of public channels but not the broader semantic classes of
  organizational contacts, role mailboxes, synthetic values, technical documents, and public
  addresses.

v3.18 therefore uses:

- a patronymic-aware sliding PERSON recognizer enabled only by operational ownership evidence;
- document-wide personal-address evidence followed by structured component recognition, which
  supports cross-sentence disclosure and grammatical address forms;
- generalized passport, division, birth, birthplace, citizenship, issuer, issue-date, PIN and
  cardholder field families;
- semantic suppression for cultural names, organizational contacts, role mailboxes, public
  addresses, synthetic dates/phones, invalid-card statements, and technical documents.

Rules contain no benchmark IDs, complete benchmark sentences, or case-specific values.

## Exact-span results

| Dataset | Production P / R / F1 | Candidate P / R / F1 | F1 delta |
|---|---:|---:|---:|
| quality | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| adversarial | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| blind v3 | 98.41 / 95.38 / 96.88 | 98.44 / 96.92 / 97.67 | +0.80 pp |
| FP stress v3 | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| sealed v4 | 100.00 / 98.46 / 99.22 | 100.00 / 100.00 / 100.00 | +0.78 pp |
| sealed v5 | 100.00 / 97.37 / 98.67 | 100.00 / 98.68 / 99.34 | +0.67 pp |
| sealed v6 | 100.00 / 96.59 / 98.27 | 100.00 / 98.86 / 99.43 | +1.16 pp |
| sealed v7 | 100.00 / 95.35 / 97.62 | 100.00 / 97.67 / 98.82 | +1.20 pp |
| sealed v8 | 100.00 / 97.67 / 98.82 | 100.00 / 97.67 / 98.82 | +0.00 pp |
| sealed v9 | 100.00 / 97.92 / 98.95 | 100.00 / 98.96 / 99.48 | +0.53 pp |
| sealed v10 | 82.80 / 75.49 / 78.97 | 100.00 / 100.00 / 100.00 | +21.03 pp |
| sealed v11 | 78.05 / 62.75 / 69.57 | 100.00 / 100.00 / 100.00 | +30.43 pp |

Precision is at least production precision on every disclosed dataset. Detailed results are in
`detector-v3-18-comparison.json`.

## Performance

Microbenchmark: 927 disclosed texts, warm cache, 20 sequential passes.

| Detector | Mean per text | p95 batch mean | Estimated serial throughput |
|---|---:|---:|---:|
| production v3.13 | 0.1219 ms | 0.1228 ms | 8,200 texts/s |
| candidate v3.18 | 0.1383 ms | 0.1398 ms | 7,230 texts/s |

The candidate remains comfortably above the 1,000 detections/s target on short texts in this
rules-only microbenchmark. Production-like HTTP and payload load testing remains necessary before
promotion.

## Verification

- 6 focused v3.18 tests passed;
- 143 repository tests passed with the undisclosed v12 test explicitly excluded;
- Ruff and strict mypy passed;
- exact mask/unmask round-trip passed over every case in all twelve disclosed datasets.
