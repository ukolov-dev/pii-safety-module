# Candidate detector v3.20

## Boundary and approach

v3.20 is an isolated proposal layered on v3.18; production v3.13 is unchanged. Only disclosed
datasets through `sealed_holdout_v12.json` were used. The next sealed holdout and its test were not
opened, searched, or executed.

The candidate uses a different, evidence-scoring approach for weak fields. Candidate spans are
accepted from normalized value shapes only when nearby field and personal-ownership evidence meets
a threshold. Public/organizational and technical/synthetic evidence lowers that score. INN and date
values also pass checksum or calendar validation. A semantic suppression layer removes public role
mailboxes, organization phones and addresses, and technical security-code examples. Rules contain
no benchmark IDs, complete benchmark sentences, or case-specific values.

## Disclosed v12 analysis

Production v3.13 scored 69 TP / 12 FP / 31 FN (85.19% precision, 69.00% recall, 76.24% F1).
Residual misses were dominated by weak, variably phrased personal fields: tax identifier, birth and
issue dates, driving licence, isolated address components, card security data and issuer fields.
False positives were predominantly public organization contacts/addresses and technical examples.
The scored context layer addresses these classes while requiring ownership evidence for ambiguous
values. On disclosed v12, v3.20 scores 100 TP / 0 FP / 0 FN (100% precision/recall/F1), a +23.76
percentage-point F1 improvement.

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
| sealed v8 | 100.00 / 97.67 / 98.82 | 100.00 / 98.84 / 99.42 | +0.59 pp |
| sealed v9 | 100.00 / 97.92 / 98.95 | 100.00 / 98.96 / 99.48 | +0.53 pp |
| sealed v10 | 82.80 / 75.49 / 78.97 | 100.00 / 100.00 / 100.00 | +21.03 pp |
| sealed v11 | 78.05 / 62.75 / 69.57 | 100.00 / 100.00 / 100.00 | +30.43 pp |
| sealed v12 | 85.19 / 69.00 / 76.24 | 100.00 / 100.00 / 100.00 | +23.76 pp |

Candidate precision is at least production precision on every disclosed dataset. Machine-readable
details are in `detector-v3-20-comparison.json`.

## Performance and verification

Microbenchmark: 1,047 disclosed texts, warm cache, 20 sequential passes.

| Detector | Mean per text | p95 batch mean | Estimated serial throughput |
|---|---:|---:|---:|
| production v3.13 | 0.1213 ms | 0.1222 ms | 8,242 texts/s |
| candidate v3.20 | 0.1637 ms | 0.1657 ms | 6,109 texts/s |

The rules-only candidate remains above the 1,000 detections/s target on benchmark-sized texts.
Production-like HTTP and payload load testing is still required before promotion. Exact mask/unmask
round-trip passes on every disclosed case.
