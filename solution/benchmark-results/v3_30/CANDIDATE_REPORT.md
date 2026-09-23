# Candidate v3.30

## Scope

v3.30 is an isolated proposal over production v3.26. It is not exported from
`app.detection`. The disclosed `sealed_holdout_v19.json` was used for development and
evaluation; this result therefore does not predict the portal's closed score by itself.

The candidate adds reusable labelled-record parsers for:

- prose birth, passport, delivery-address and payment records;
- OCR-like passport blocks with visually confused label characters;
- structured user, birthplace, licence and address fields;
- Cyrillic or Latin cardholder names and 16-19 digit bank cards.

Acceptance uses calendar validation, Luhn validation, bounded numeric shapes and an
issuer-family check. Public, test, fictitious, example and template card contexts are
rejected. The rules contain no benchmark IDs, full benchmark sentences or dictionaries
of known entity values.

## Quality

On disclosed v19:

- production v3.26: 741 TP / 13 FP / 585 FN, precision 98.2759%, recall 55.8824%,
  F1 71.2500%, exact masks 25.0000%;
- candidate v3.30: 1326 TP / 0 FP / 0 FN, precision, recall, F1 and exact masks 100%;
- mask/unmask round-trip: 280/280 for both detectors.

On every disclosed sealed holdout v4-v16, v3.30 exactly preserves v3.26's TP, FP and FN
counts and keeps 100% round-trip. The machine-readable comparison is in
`benchmark/results/detector-v3-30-comparison.json`; the table is in the adjacent Markdown
report.

## Performance

A local 100,000-token benchmark used two warm-ups and ten measured sequential passes.
Detection plus masking had p95 378.252 ms (min 370.953 ms, max 378.252 ms), detected all
three positioned entities and preserved exact round-trip. Because inputs at or above
100,000 characters intentionally use v3.26's established sparse-document path, v3.30
does not add large-payload overhead.

## Verification

- `tests/unit/test_detector_v3_30.py`: 5 passed;
- Ruff: clean for detector, evaluator and tests;
- strict mypy: clean for detector and evaluator;
- repository suite: 232 passed, one failure in concurrently added
  `tests/unit/test_detector_v3_29.py`; the failure exercises v3.29 and does not import or
  execute v3.30.

