# Quality benchmark: ru_pii_quality_v1

Dataset version: `1`; cases: **30**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 100.00% |
| F1 | 100.00% |
| Exact masks | 30/30 (100.00%) |
| Exact round trips | 30/30 (100.00%) |

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
| BIRTH_DATE | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PHONE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

None.

## Sources

- `../database/chunks/CH-SRC-001-05.md`
- `../database/chunks/CH-SRC-001-06.md`
- `../database/chunks/CH-SRC-001-07.md`
