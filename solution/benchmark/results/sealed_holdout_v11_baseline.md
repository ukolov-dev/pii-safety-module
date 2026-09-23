# Quality benchmark: ru_pii_sealed_holdout_v11

Dataset version: `11`; cases: **120**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 78.05% |
| Recall | 62.75% |
| F1 | 69.57% |
| Exact masks | 83/120 (69.17%) |
| Exact round trips | 120/120 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 5 | 0 | 3 | 100.00% | 62.50% | 76.92% |
| ADDRESS_CITY | 0 | 0 | 8 | 0.00% | 0.00% | 0.00% |
| ADDRESS_COUNTRY | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| ADDRESS_HOUSE | 4 | 1 | 4 | 80.00% | 50.00% | 61.54% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_STREET | 4 | 1 | 4 | 80.00% | 50.00% | 61.54% |
| BANK_CARD | 4 | 1 | 0 | 80.00% | 100.00% | 88.89% |
| BIRTH_DATE | 5 | 0 | 1 | 100.00% | 83.33% | 90.91% |
| CARDHOLDER_NAME | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| CITIZENSHIP | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| CVV | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| DRIVER_LICENSE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 6 | 7 | 0 | 46.15% | 100.00% | 63.16% |
| INN | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUE_DATE | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_RF | 4 | 1 | 1 | 80.00% | 80.00% | 80.00% |
| PERSON | 5 | 1 | 8 | 83.33% | 38.46% | 52.63% |
| PHONE_RF | 7 | 5 | 0 | 58.33% | 100.00% | 73.68% |
| PIN | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PLACE_OF_BIRTH | 1 | 1 | 1 | 50.00% | 50.00% | 50.00% |

## Cases with a non-exact mask

- `v11-pos-002`: missing=[('PERSON', 22, 55)]; unexpected=[]
- `v11-pos-003`: missing=[('PERSON', 28, 54)]; unexpected=[('PERSON', 15, 26)]
- `v11-pos-004`: missing=[('PERSON', 27, 57)]; unexpected=[]
- `v11-pos-006`: missing=[('PERSON', 17, 44)]; unexpected=[]
- `v11-pos-007`: missing=[('PERSON', 19, 44)]; unexpected=[]
- `v11-pos-008`: missing=[('PERSON', 22, 49)]; unexpected=[]
- `v11-pos-009`: missing=[('PERSON', 15, 40)]; unexpected=[]
- `v11-pos-011`: missing=[('ADDRESS_CITY', 45, 50), ('ADDRESS_POSTAL_CODE', 37, 43)]; unexpected=[]
- `v11-pos-012`: missing=[('ADDRESS_CITY', 51, 56)]; unexpected=[]
- `v11-pos-013`: missing=[('ADDRESS_APARTMENT', 79, 81), ('ADDRESS_CITY', 30, 39), ('ADDRESS_HOUSE', 66, 68), ('ADDRESS_STREET', 47, 60)]; unexpected=[]
- `v11-pos-014`: missing=[('ADDRESS_APARTMENT', 60, 62), ('ADDRESS_CITY', 13, 20), ('ADDRESS_HOUSE', 47, 49), ('ADDRESS_STREET', 30, 38)]; unexpected=[]
- `v11-pos-015`: missing=[('ADDRESS_CITY', 54, 66), ('ADDRESS_COUNTRY', 40, 42), ('ADDRESS_HOUSE', 93, 95), ('ADDRESS_POSTAL_CODE', 45, 51), ('ADDRESS_STREET', 75, 86)]; unexpected=[]
- `v11-pos-016`: missing=[('ADDRESS_APARTMENT', 65, 67), ('ADDRESS_CITY', 19, 26), ('ADDRESS_HOUSE', 52, 54), ('ADDRESS_STREET', 37, 46)]; unexpected=[]
- `v11-pos-017`: missing=[('ADDRESS_CITY', 34, 41)]; unexpected=[]
- `v11-pos-035`: missing=[('PASSPORT_RF', 20, 56)]; unexpected=[]
- `v11-pos-039`: missing=[('DIVISION_CODE', 28, 35)]; unexpected=[]
- `v11-pos-042`: missing=[('BIRTH_DATE', 19, 29)]; unexpected=[]
- `v11-pos-045`: missing=[('PLACE_OF_BIRTH', 30, 46)]; unexpected=[('PLACE_OF_BIRTH', 15, 46)]
- `v11-pos-046`: missing=[('CITIZENSHIP', 29, 49)]; unexpected=[]
- `v11-pos-053`: missing=[('PIN', 37, 41)]; unexpected=[]
- `v11-pos-054`: missing=[('CARDHOLDER_NAME', 33, 46)]; unexpected=[]
- `v11-pos-058`: missing=[('ADDRESS_CITY', 33, 40), ('ADDRESS_POSTAL_CODE', 25, 31)]; unexpected=[]
- `v11-pos-060`: missing=[('PERSON', 13, 34)]; unexpected=[]
- `v11-neg-068`: missing=[]; unexpected=[('PHONE_RF', 30, 48)]
- `v11-neg-071`: missing=[]; unexpected=[('PHONE_RF', 23, 39)]
- `v11-neg-072`: missing=[]; unexpected=[('PHONE_RF', 10, 26)]
- `v11-neg-076`: missing=[]; unexpected=[('EMAIL', 31, 53)]
- `v11-neg-078`: missing=[]; unexpected=[('EMAIL', 29, 49)]
- `v11-neg-079`: missing=[]; unexpected=[('EMAIL', 34, 61)]
- `v11-neg-080`: missing=[]; unexpected=[('EMAIL', 34, 63)]
- `v11-neg-082`: missing=[]; unexpected=[('EMAIL', 31, 55)]
- `v11-neg-083`: missing=[]; unexpected=[('EMAIL', 5, 28)]
- `v11-neg-090`: missing=[]; unexpected=[('ADDRESS_HOUSE', 54, 56), ('ADDRESS_STREET', 42, 48)]
- `v11-neg-099`: missing=[]; unexpected=[('PHONE_RF', 9, 25)]
- `v11-neg-102`: missing=[]; unexpected=[('BANK_CARD', 12, 28)]
- `v11-neg-103`: missing=[]; unexpected=[('PASSPORT_RF', 50, 62)]
- `v11-neg-119`: missing=[]; unexpected=[('EMAIL', 29, 51), ('PHONE_RF', 53, 69)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
