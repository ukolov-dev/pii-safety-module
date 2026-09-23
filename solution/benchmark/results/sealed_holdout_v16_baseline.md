# Quality benchmark: ru_pii_sealed_holdout_v16

Dataset version: `16`; cases: **180**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 86.49% |
| Recall | 84.21% |
| F1 | 85.33% |
| Exact masks | 151/180 (83.89%) |
| Exact round trips | 180/180 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 7 | 0 | 2 | 100.00% | 77.78% | 87.50% |
| ADDRESS_CITY | 3 | 2 | 6 | 60.00% | 33.33% | 42.86% |
| ADDRESS_COUNTRY | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 7 | 2 | 2 | 77.78% | 77.78% | 77.78% |
| ADDRESS_POSTAL_CODE | 5 | 0 | 1 | 100.00% | 83.33% | 90.91% |
| ADDRESS_STREET | 6 | 3 | 3 | 66.67% | 66.67% | 66.67% |
| BANK_CARD | 6 | 2 | 0 | 75.00% | 100.00% | 85.71% |
| BIRTH_DATE | 8 | 0 | 1 | 100.00% | 88.89% | 94.12% |
| CARDHOLDER_NAME | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 4 | 1 | 0 | 80.00% | 100.00% | 88.89% |
| DIVISION_CODE | 4 | 0 | 2 | 100.00% | 66.67% | 80.00% |
| DRIVER_LICENSE_RF | 4 | 0 | 1 | 100.00% | 80.00% | 88.89% |
| EMAIL | 9 | 4 | 0 | 69.23% | 100.00% | 81.82% |
| INN | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PASSPORT_RF | 7 | 0 | 1 | 100.00% | 87.50% | 93.33% |
| PERSON | 11 | 1 | 4 | 91.67% | 73.33% | 81.48% |
| PHONE_RF | 10 | 5 | 0 | 66.67% | 100.00% | 80.00% |
| PIN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |

## Cases with a non-exact mask

- `v16-pos-002`: missing=[('PERSON', 28, 56)]; unexpected=[]
- `v16-pos-004`: missing=[('PERSON', 17, 45)]; unexpected=[]
- `v16-pos-005`: missing=[('PERSON', 30, 60)]; unexpected=[]
- `v16-pos-009`: missing=[('PERSON', 20, 45)]; unexpected=[('PERSON', 11, 38)]
- `v16-pos-011`: missing=[('ADDRESS_CITY', 35, 50)]; unexpected=[('ADDRESS_CITY', 42, 50)]
- `v16-pos-012`: missing=[('ADDRESS_CITY', 34, 41), ('ADDRESS_STREET', 49, 61)]; unexpected=[('ADDRESS_STREET', 49, 54)]
- `v16-pos-015`: missing=[('ADDRESS_APARTMENT', 58, 60), ('ADDRESS_CITY', 20, 29), ('ADDRESS_HOUSE', 50, 52), ('ADDRESS_STREET', 37, 45)]; unexpected=[]
- `v16-pos-017`: missing=[('ADDRESS_CITY', 33, 45)]; unexpected=[]
- `v16-pos-044`: missing=[('PASSPORT_RF', 19, 53)]; unexpected=[]
- `v16-pos-046`: missing=[('DIVISION_CODE', 22, 29)]; unexpected=[]
- `v16-pos-047`: missing=[('DIVISION_CODE', 17, 24)]; unexpected=[]
- `v16-pos-054`: missing=[('BIRTH_DATE', 23, 33)]; unexpected=[]
- `v16-pos-070`: missing=[('DRIVER_LICENSE_RF', 20, 31)]; unexpected=[]
- `v16-pos-080`: missing=[('ADDRESS_CITY', 31, 46)]; unexpected=[('ADDRESS_CITY', 38, 46)]
- `v16-pos-084`: missing=[('ADDRESS_APARTMENT', 62, 64), ('ADDRESS_CITY', 24, 33), ('ADDRESS_HOUSE', 54, 56), ('ADDRESS_POSTAL_CODE', 16, 22), ('ADDRESS_STREET', 41, 48)]; unexpected=[]
- `v16-pos-086`: missing=[('PASSPORT_ISSUE_DATE', 61, 71)]; unexpected=[]
- `v16-neg-109`: missing=[]; unexpected=[('EMAIL', 20, 43)]
- `v16-neg-113`: missing=[]; unexpected=[('EMAIL', 28, 51)]
- `v16-neg-116`: missing=[]; unexpected=[('EMAIL', 23, 52)]
- `v16-neg-117`: missing=[]; unexpected=[('ADDRESS_HOUSE', 60, 62), ('ADDRESS_STREET', 40, 54)]
- `v16-neg-152`: missing=[]; unexpected=[('BANK_CARD', 21, 40), ('CVV', 47, 50)]
- `v16-neg-155`: missing=[]; unexpected=[('PHONE_RF', 26, 42)]
- `v16-neg-156`: missing=[]; unexpected=[('PHONE_RF', 38, 54)]
- `v16-neg-160`: missing=[]; unexpected=[('EMAIL', 6, 29)]
- `v16-neg-163`: missing=[]; unexpected=[('PHONE_RF', 8, 24)]
- `v16-neg-166`: missing=[]; unexpected=[('PHONE_RF', 11, 27)]
- `v16-neg-167`: missing=[]; unexpected=[('ADDRESS_HOUSE', 54, 56), ('ADDRESS_STREET', 39, 48)]
- `v16-neg-172`: missing=[]; unexpected=[('PHONE_RF', 14, 30)]
- `v16-neg-176`: missing=[]; unexpected=[('BANK_CARD', 13, 29)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
