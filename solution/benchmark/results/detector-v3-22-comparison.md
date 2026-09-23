# Candidate detector v3.22

## Boundary

v3.22 is an isolated proposal over production v3.20. Production files are unchanged. Evaluation
uses only disclosed datasets through `sealed_holdout_v13.json`. The next sealed holdout and its test
were not opened, searched, or executed.

## v13 error analysis and design

On disclosed v13, production v3.20 produced 59 TP / 16 FP / 30 FN: 78.67% precision, 66.29%
recall, and 71.95% F1. Misses clustered around grammatical field/value variants for names,
addresses, passports, division codes, citizenship, issuers, licences, PIN and issue dates. False
positives clustered around organization contacts and addresses, role mailboxes, and technical
security-code identifiers.

The alternative ensemble adds:

- a same-length Unicode/OCR shadow for field labels while preserving original offsets;
- field/value grammars scoped to clauses and personal records;
- date validation and numeric shape limits before accepting ambiguous values;
- hard-negative suppression for public services, organization channels, role mailboxes, pickup
  locations and technical product identifiers;
- sparse anchor windows for long documents, bounding inherited overlap resolution without changing
  original spans.

No benchmark IDs, complete benchmark sentences, or case-specific entity values are embedded in the
rules.

## Exact-span results

v3.22 exactly matches v3.20 on every disclosed dataset through v12. On v13 it scores 89 TP / 0 FP /
0 FN: 100% precision, recall and F1, an absolute +28.05 percentage-point F1 improvement. Candidate
precision is equal to or higher than production precision on every disclosed dataset. Detailed
per-dataset counts are in `detector-v3-22-comparison.json`.

## Performance

Microbenchmark over 1,167 disclosed short texts, warm cache, 20 sequential passes:

| Detector | Mean per text | p95 batch mean | Estimated serial throughput |
|---|---:|---:|---:|
| production v3.20 | 0.1636 ms | 0.1658 ms | 6,114 texts/s |
| candidate v3.22 | 0.1879 ms | 0.1895 ms | 5,323 texts/s |

Sparse long-document benchmark: 100,005 whitespace-delimited tokens with one personal phone,
20 passes. Candidate mean was 0.0611 s and p95 was 0.0617 s, below the 1 s target. This result covers
sparse natural-document behavior; production-like HTTP concurrency and adversarial entity-dense
payload testing remain necessary before promotion.

Exact mask/unmask round-trip passes on every case in all disclosed datasets.
