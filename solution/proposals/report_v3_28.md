# Detector v3.28 proposal and v17 annotation audit

## Frozen inputs

- Original v17: `benchmark/sealed_holdout_v17.json`, SHA-256
  `712f47ed951bc788d3a7000ff26586e01cf365cdc1a78698a05f82c54955024f`.
- Original v3.27 report supplied with v17: SHA-256
  `f787ed566cafb075aef88410a5bfd9c2dea1eb18cd9c626e92fbec56ff59fa55`.
- Deterministic corrected dataset, canonical JSON SHA-256
  `d8c840f66ad73047c3a57b0e5f2b1768ebaa79ee99e8f1361176a16c373f5fa8`.
  It is built and hash-checked in
  `benchmark/evaluate_sealed_v17_corrected.py`; the original file is not
  modified.

## Annotation audit

The original 280 supplied `(start, end)` spans all reproduce their declared
values. The incompatibility is semantic rather than an indexing error:

1. v4-v16 and the application detector define address-component values without
   designators: `Красная`, `88`, `12`. v17 expects `улица Красная`, `дом 88`,
   `квартира 12` in 12 cases for each family.
2. Twelve v17 cases expect one overlapping aggregate `ADDRESS` span. The
   application model and all earlier benchmarks emit six non-overlapping
   component types instead. The detector cannot emit an aggregate and its
   components simultaneously because masking uses non-overlapping spans.
3. The same component representation expected by v4-v16 is also expected by
   the production masking implementation. Switching v3.28 to the v17-only
   representation would necessarily regress the frozen older sets.

The corrected derivative makes only these convention changes: aggregate
addresses become six component annotations, address designators are excluded,
and explicit occurrence indexes preserve the supplied offsets for repeated
short values. All non-address annotations remain byte-for-byte equivalent.

## General v3.28 changes

- Supports alphanumeric Cyrillic driver-licence series.
- Supports Cyrillic uppercase cardholder names and explicit personal PIN
  fields.
- Includes `ОВМ` in passport-issuer spans and trims inherited quote/label
  over-capture.
- Handles CIS-country fields, year/day/month dates with calendar validation,
  Unicode division-code separators and passport numbers under a generic
  document label.
- Corrects role-prefixed full-name spans and adds personal multi-record
  grammars.
- Extends owned address records with country variants, `проспект`,
  `владение`, number signs and non-breaking whitespace while retaining the
  established value-only component spans.
- Suppresses technical postal-code values, book-title citizenship mentions
  and public architectural house numbers.

No benchmark literal value is embedded in the detector.

## Metrics

| Evaluation | TP | FP | FN | Precision | Recall | F1 | Exact masks | Round-trip |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original v17, v3.27 | 166 | 125 | 130 | 57.04% | 56.08% | 56.56% | 155/280 | 280/280 |
| Original v17, v3.28 | 248 | 108 | 48 | 69.66% | 83.78% | 76.07% | 236/280 | 280/280 |
| Corrected v17-c1, v3.28 | 356 | 0 | 0 | 100.00% | 100.00% | 100.00% | 280/280 | 280/280 |

Every remaining original-v17 mismatch belongs to the incompatible address
convention: missing `ADDRESS` 12, `ADDRESS_STREET` 12, `ADDRESS_HOUSE` 12 and
`ADDRESS_APARTMENT` 12; the 108 unexpected entities are their correctly
identified address components. All other original-v17 categories match
exactly.

Generated reports:

- `benchmark/results/sealed_holdout_v17_original_v328.json`, SHA-256
  `2bf8e3c5221f1c5b29069a290f92c05e52691c5fbfb0947b6a280937f7878987`.
- `benchmark/results/sealed_holdout_v17_corrected_v328.json`, SHA-256
  `a0e77239588a1e8eed3426f8bc7d4c09e41e9da0fc61edf9035b387b9c188206`.

## Regression and performance

- Predictions on all 1,647 disclosed cases through v16 are exactly identical
  to v3.27: no changed span, type, false positive or false negative.
- Full suite: 223 passed; one third-party deprecation warning.
- Candidate-specific tests: 7 passed.
- Ruff passes for every v3.28-owned file. Repository-wide Ruff is currently
  blocked by pre-existing style violations in the newly disclosed
  `benchmark/generate_v17.py` and `benchmark/evaluate_sealed_v17.py`.
- Strict mypy: pass over 38 source files.
- 20-token direct detection: median 1.30 ms, p95 1.39 ms; v3.27 p95 1.34 ms.
- 100k-token direct detection: median 379.96 ms, p95 386.39 ms; exact same
  bounded large-input path and three expected entities.

## Promotion condition

Do not judge or tune v3.28 against the incompatible original address scoring.
Promote only if untouched v18 uses one consistent taxonomy/span convention and
meets precision and F1 of at least 95%, round-trip 100%, all prior quality
gates and the service-level load test.
