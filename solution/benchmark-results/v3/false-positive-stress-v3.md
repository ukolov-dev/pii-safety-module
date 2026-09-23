# Quality benchmark: ru_pii_false_positive_stress_v3

Dataset version: `3`; cases: **64**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 100.00% |
| F1 | 100.00% |
| Exact masks | 64/64 (100.00%) |
| Exact round trips | 64/64 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| INN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_RF | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PHONE_RF | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

None.

## Sources

- `Synthetic stress cases designed to measure over-masking; no production personal data.`
