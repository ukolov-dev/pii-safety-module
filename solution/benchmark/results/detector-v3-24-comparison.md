# Candidate detector v3.24

## Boundary

v3.24 is an isolated proposal over frozen v3.22; production v3.20 is unchanged. Evaluation uses
only disclosed datasets through `sealed_holdout_v14.json`. The next sealed holdout and its test were
not opened, searched, or executed.

## Disclosed v14 analysis

Production v3.20 scored 88 TP / 21 FP / 45 FN: 80.73% precision, 66.17% recall, and 72.73% F1.
Misses concentrated in OCR/table separators, semantic field synonyms, Russian inflections,
multiline passport/address records, and personal values appearing after public values. False
positives were primarily public organization contacts and addresses, blank templates, and SDK test
data.

v3.24 adds:

- same-length Unicode/OCR normalization for labels and separators while preserving source offsets;
- semantic field families for document, identity, address, card and contact values;
- clause and multiline-record association for passport and address blocks;
- Russian-inflection variants for residence, citizenship and birthplace;
- calendar validation, numeric shape limits and exact issuer boundaries;
- local public-versus-personal evidence scoring plus hard negatives for blank forms, public venues,
  shared channels and synthetic SDK values.

Rules contain no benchmark IDs, complete benchmark sentences, or case-specific entity values.

## Exact-span results

On disclosed v14, v3.24 scores 133 TP / 0 FP / 0 FN: 100% precision, recall and F1, an absolute
+27.27 percentage-point F1 improvement over production. It also retains v3.22's 100% result on v13
and exactly preserves its metrics on every earlier disclosed dataset. Candidate precision is equal
to or higher than production precision on every disclosed dataset. Full counts are recorded in
`detector-v3-24-comparison.json`.

## Performance

Microbenchmark over 1,307 disclosed short texts, warm cache, 20 sequential passes:

| Detector | Mean per text | p95 batch mean | Estimated serial throughput |
|---|---:|---:|---:|
| production v3.20 | 0.1644 ms | 0.1668 ms | 6,081 texts/s |
| candidate v3.24 | 0.2193 ms | 0.2256 ms | 4,560 texts/s |

Sparse long-document benchmark: 100,005 whitespace-delimited tokens with one personal phone,
20 passes. Candidate mean was 0.3514 s and p95 was 0.3529 s, below the 1 s target. Production-like
HTTP concurrency and adversarial entity-dense payload testing remain necessary before promotion.

Exact mask/unmask round-trip passes on every case in all disclosed datasets.
