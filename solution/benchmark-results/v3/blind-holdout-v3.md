# Quality benchmark: ru_pii_blind_holdout_v3

Dataset version: `3`; cases: **60**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 98.46% |
| F1 | 99.22% |
| Exact masks | 59/60 (98.33%) |
| Exact round trips | 60/60 (100.00%) |

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
| CITIZENSHIP | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 7 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PASSPORT_RF | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PHONE_RF | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

- `blind-multi-passport`: missing=[('PASSPORT_ISSUE_DATE', 55, 65)]; unexpected=[]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
