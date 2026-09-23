# Quality benchmark: ru_pii_sealed_holdout_v12

Dataset version: `12`; cases: **120**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 85.19% |
| Recall | 69.00% |
| F1 | 76.24% |
| Exact masks | 85/120 (70.83%) |
| Exact round trips | 120/120 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 2 | 0 | 3 | 100.00% | 40.00% | 57.14% |
| ADDRESS_CITY | 0 | 0 | 6 | 0.00% | 0.00% | 0.00% |
| ADDRESS_COUNTRY | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 2 | 1 | 3 | 66.67% | 40.00% | 50.00% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_STREET | 2 | 0 | 3 | 100.00% | 40.00% | 57.14% |
| BANK_CARD | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 4 | 0 | 1 | 100.00% | 80.00% | 88.89% |
| CARDHOLDER_NAME | 2 | 0 | 2 | 100.00% | 50.00% | 66.67% |
| CITIZENSHIP | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 3 | 1 | 1 | 75.00% | 75.00% | 75.00% |
| DIVISION_CODE | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| EMAIL | 6 | 4 | 0 | 60.00% | 100.00% | 75.00% |
| INN | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PASSPORT_ISSUER | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PASSPORT_ISSUE_DATE | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PASSPORT_RF | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 6 | 0 | 1 | 100.00% | 85.71% | 92.31% |
| PHONE_RF | 6 | 5 | 0 | 54.55% | 100.00% | 70.59% |
| PIN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 4 | 1 | 1 | 80.00% | 80.00% | 80.00% |

## Cases with a non-exact mask

- `v12-pos-002`: missing=[('PERSON', 13, 41)]; unexpected=[]
- `v12-pos-008`: missing=[('INN', 38, 50)]; unexpected=[]
- `v12-pos-015`: missing=[('BIRTH_DATE', 29, 39)]; unexpected=[]
- `v12-pos-024`: missing=[('PASSPORT_ISSUE_DATE', 20, 45)]; unexpected=[]
- `v12-pos-026`: missing=[('DRIVER_LICENSE_RF', 36, 47)]; unexpected=[]
- `v12-pos-027`: missing=[('ADDRESS_COUNTRY', 36, 42)]; unexpected=[]
- `v12-pos-028`: missing=[('ADDRESS_COUNTRY', 48, 50)]; unexpected=[]
- `v12-pos-029`: missing=[('ADDRESS_POSTAL_CODE', 42, 48)]; unexpected=[]
- `v12-pos-030`: missing=[('ADDRESS_POSTAL_CODE', 44, 50)]; unexpected=[]
- `v12-pos-031`: missing=[('ADDRESS_CITY', 36, 41)]; unexpected=[]
- `v12-pos-032`: missing=[('ADDRESS_CITY', 9, 18)]; unexpected=[]
- `v12-pos-033`: missing=[('ADDRESS_STREET', 31, 45)]; unexpected=[]
- `v12-pos-034`: missing=[('ADDRESS_STREET', 28, 37)]; unexpected=[]
- `v12-pos-035`: missing=[('ADDRESS_HOUSE', 24, 27)]; unexpected=[]
- `v12-pos-036`: missing=[('ADDRESS_HOUSE', 32, 34)]; unexpected=[]
- `v12-pos-037`: missing=[('ADDRESS_APARTMENT', 27, 30)]; unexpected=[]
- `v12-pos-038`: missing=[('ADDRESS_APARTMENT', 25, 27)]; unexpected=[]
- `v12-pos-039`: missing=[('CVV', 37, 40)]; unexpected=[]
- `v12-pos-043`: missing=[('CARDHOLDER_NAME', 18, 31)]; unexpected=[]
- `v12-pos-044`: missing=[('CARDHOLDER_NAME', 35, 52)]; unexpected=[]
- `v12-pos-048`: missing=[('ADDRESS_CITY', 27, 32), ('ADDRESS_COUNTRY', 11, 17), ('ADDRESS_POSTAL_CODE', 19, 25)]; unexpected=[]
- `v12-pos-052`: missing=[('ADDRESS_CITY', 35, 43)]; unexpected=[]
- `v12-pos-055`: missing=[('PASSPORT_ISSUER', 26, 50)]; unexpected=[]
- `v12-pos-058`: missing=[('ADDRESS_APARTMENT', 91, 93), ('ADDRESS_CITY', 44, 48), ('ADDRESS_HOUSE', 78, 80), ('ADDRESS_STREET', 59, 72)]; unexpected=[]
- `v12-pos-060`: missing=[('ADDRESS_CITY', 89, 95), ('PLACE_OF_BIRTH', 28, 64)]; unexpected=[('PLACE_OF_BIRTH', 82, 95)]
- `v12-neg-069`: missing=[]; unexpected=[('EMAIL', 27, 50)]
- `v12-neg-072`: missing=[]; unexpected=[('EMAIL', 25, 48)]
- `v12-neg-073`: missing=[]; unexpected=[('PHONE_RF', 30, 48)]
- `v12-neg-076`: missing=[]; unexpected=[('PHONE_RF', 10, 26)]
- `v12-neg-081`: missing=[]; unexpected=[('ADDRESS_HOUSE', 55, 57)]
- `v12-neg-093`: missing=[]; unexpected=[('PHONE_RF', 17, 33)]
- `v12-neg-101`: missing=[]; unexpected=[('CVV', 13, 16)]
- `v12-neg-110`: missing=[]; unexpected=[('EMAIL', 14, 41)]
- `v12-neg-115`: missing=[]; unexpected=[('PHONE_RF', 33, 49)]
- `v12-neg-116`: missing=[]; unexpected=[('EMAIL', 18, 44), ('PHONE_RF', 46, 62)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
