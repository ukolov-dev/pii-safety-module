# Quality benchmark: ru_pii_sealed_holdout_v4

Dataset version: `4`; cases: **56**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 100.00% |
| F1 | 100.00% |
| Exact masks | 56/56 (100.00%) |
| Exact round trips | 56/56 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_RF | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 7 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PHONE_RF | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

None.

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
