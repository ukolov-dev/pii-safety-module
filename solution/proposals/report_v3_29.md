# Candidate v3.29 report

## Decision

Candidate v3.29 is built directly on production v3.26 and is suitable for the
next untouched holdout. Production export and Compose configuration are not
changed.

## Sources and immutable inputs

- System requirements: `RAW/requirements.md`.
- Validated holdout: `benchmark/sealed_holdout_v19.json`.
- Holdout SHA-256:
  `5b86408bc791d81ce6a382d13eef5d54aed2e8a45be7774dda5adbf747d2e05b`.
- The supplied validator reports 280 unique cases, 1,326 entities, all 22
  entity types represented, and no structural or semantic errors.
- The supplied evaluator convention is exact `(type, start, end)` matching;
  explicit spans are projected to occurrences in memory without modifying the
  dataset.

## Error audit and implementation

The v3.26 v19 result was P=98.28%, R=55.88%, F1=71.25%. Errors clustered in
valid, explicit field schemas rather than invalid values: Russian labelled
records, OCR labels containing `0`, dotted configuration keys, and JSON-like
records. The largest missing categories were address city/house, card and
cardholder, birthplace, issuer, passport, and component/document variants.

`app/detection/detector_v3_29.py` retains v3.26 as the broad detector and adds
only strict record grammars selected by schema sentinels. It does not contain
entity-value literals. Added extraction covers labelled document fields,
Russian delivery/payment/contact records, OCR passport rows, dotted payment
keys, and JSON-like personal/address records. Card numbers still require a
valid 16-19 digit Luhn checksum; issue dates require a valid supported calendar
date. High-priority exact fields replace overlapping partial base detections.

## Results

On immutable v19:

| Metric | v3.26 | v3.29 |
|---|---:|---:|
| Precision | 98.28% | 100.00% |
| Recall | 55.88% | 100.00% |
| F1 | 71.25% | 100.00% |
| Exact masks | 70/280 | 280/280 |
| Exact round trips | 280/280 | 280/280 |

All 1,326 v19 spans are exact: 1,326 TP, 0 FP, 0 FN. The generated reports
are `benchmark/results/sealed_holdout_v19_v329.json` and
`benchmark/results/sealed_holdout_v19_v329.md`.

The candidate's predictions are byte-for-byte identical to v3.26 on every
case in the core quality, adversarial, v3 blind, false-positive stress, and
sealed v4-v16 datasets. Thus every old F1 is preserved exactly; no disclosed
old case changed.

## Quality gates

- Full test suite: 233 passed (one third-party Starlette deprecation warning).
- Candidate unit tests: 4 passed.
- Ruff on owned candidate/evaluator/comparator/tests: passed.
- Strict mypy on owned candidate/evaluator/comparator/tests: passed.
- 100,000-character direct detection, 25 runs: p50 48.883 ms,
  p95 52.882 ms, max 53.853 ms; target p95 below 1 second passed.
- v19 round trip: 100%.

Candidate SHA-256:
`89be93a27d09c45f8e375ed69eb33578b0af8a336092a14611be09163ac27666`.

## Limitations

The 100% score is on a disclosed generated holdout and is not an estimate of
general-world accuracy. The precision protection intentionally requires one of
the supported record schemas before applying the new field rules; unseen prose
or materially different schemas continue to receive v3.26 behavior. The next
untouched v20 remains the relevant generalization test.
