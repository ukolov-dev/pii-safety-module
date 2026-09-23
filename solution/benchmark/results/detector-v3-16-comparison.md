# Candidate detector v3.16

## Boundary

v3.16 is an isolated proposal layered directly on production v3.13. Production files were not
modified. Development and regression evaluation used disclosed datasets through
`sealed_holdout_v10.json`; the next sealed dataset and its test were not opened or executed.

## Disclosed v10 analysis

Production v3.13 scored 77 TP / 16 FP / 25 FN: 82.80% precision, 75.49% recall, and
78.97% F1.

The errors grouped into reusable semantic families:

- FN: operational PERSON relations (consent giver, recipient, account holder), personal-address
  discourse across sentences and grammatical cases, alternate passport/birth/birthplace/issuer/
  issue-date/division field wording;
- FP: public departmental phones, role mailboxes, synthetic placeholders, store/branch/pickup/
  workplace addresses, support and exhibition-centre contacts.

v3.16 adds high-context semantic recognizers and ownership suppression for those classes. It
validates calendar dates and patronymic morphology, preserves exact spans, and does not contain
benchmark IDs, full benchmark sentences, or case-specific values.

An optional model-ready `NERSpan` boundary is included, but no heavy runtime or weights are
required. Model spans need score >= 0.94, valid offsets, a supported label, and deterministic
personal-address/name evidence.

## Exact-span results

| Dataset | Production P / R / F1 | Candidate P / R / F1 | F1 delta |
|---|---:|---:|---:|
| quality | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| adversarial | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| blind v3 | 98.41 / 95.38 / 96.88 | 98.44 / 96.92 / 97.67 | +0.80 pp |
| FP stress v3 | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| sealed v4 | 100.00 / 98.46 / 99.22 | 100.00 / 98.46 / 99.22 | +0.00 pp |
| sealed v5 | 100.00 / 97.37 / 98.67 | 100.00 / 98.68 / 99.34 | +0.67 pp |
| sealed v6 | 100.00 / 96.59 / 98.27 | 100.00 / 97.73 / 98.85 | +0.58 pp |
| sealed v7 | 100.00 / 95.35 / 97.62 | 100.00 / 96.51 / 98.22 | +0.61 pp |
| sealed v8 | 100.00 / 97.67 / 98.82 | 100.00 / 97.67 / 98.82 | +0.00 pp |
| sealed v9 | 100.00 / 97.92 / 98.95 | 100.00 / 98.96 / 99.48 | +0.53 pp |
| sealed v10 | 82.80 / 75.49 / 78.97 | 100.00 / 100.00 / 100.00 | +21.03 pp |

Precision is at least production precision on every disclosed dataset. Machine-readable results
are in `detector-v3-16-comparison.json`.

## Performance

Microbenchmark: 807 disclosed texts, warm cache, 20 sequential passes.

| Detector | Mean per text | p95 batch mean | Estimated serial throughput |
|---|---:|---:|---:|
| production v3.13 | 0.1152 ms | 0.1169 ms | 8,683 texts/s |
| candidate v3.16 | 0.1286 ms | 0.1299 ms | 7,774 texts/s |

The candidate adds approximately 0.0134 ms per short benchmark text and remains well above the
1,000 detections/s target in this local rules-only microbenchmark. This is not a substitute for
HTTP load testing with production payload distributions.

## Verification

- 6 focused v3.16 tests passed, including optional-NER gates and a latency guard;
- 124 repository tests passed with the undisclosed v11 test explicitly excluded;
- Ruff and strict mypy passed;
- exact mask/unmask round-trip passed for every case in all eleven disclosed datasets.
