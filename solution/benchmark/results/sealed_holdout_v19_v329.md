# Quality benchmark: sealed-blind-holdout-v19

Dataset version: `19.0.0`; cases: **280**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 100.00% |
| F1 | 100.00% |
| Exact masks | 280/280 (100.00%) |
| Exact round trips | 280/280 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 26 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 78 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 26 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 78 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| INN | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_RF | 78 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 156 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PHONE_RF | 104 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 52 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

None.

## Sources

- `RAW/requirements.md`
