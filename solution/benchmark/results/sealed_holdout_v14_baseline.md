# Quality benchmark: ru_pii_sealed_holdout_v14

Dataset version: `14`; cases: **140**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 80.73% |
| Recall | 66.17% |
| F1 | 72.73% |
| Exact masks | 94/140 (67.14%) |
| Exact round trips | 140/140 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 4 | 0 | 3 | 100.00% | 57.14% | 72.73% |
| ADDRESS_CITY | 3 | 1 | 6 | 75.00% | 33.33% | 46.15% |
| ADDRESS_COUNTRY | 2 | 0 | 2 | 100.00% | 50.00% | 66.67% |
| ADDRESS_HOUSE | 3 | 4 | 4 | 42.86% | 42.86% | 42.86% |
| ADDRESS_POSTAL_CODE | 5 | 1 | 1 | 83.33% | 83.33% | 83.33% |
| ADDRESS_STREET | 4 | 5 | 3 | 44.44% | 57.14% | 50.00% |
| BANK_CARD | 6 | 1 | 0 | 85.71% | 100.00% | 92.31% |
| BIRTH_DATE | 5 | 0 | 1 | 100.00% | 83.33% | 90.91% |
| CARDHOLDER_NAME | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| CITIZENSHIP | 3 | 0 | 2 | 100.00% | 60.00% | 75.00% |
| CVV | 4 | 1 | 1 | 80.00% | 80.00% | 80.00% |
| DIVISION_CODE | 4 | 0 | 1 | 100.00% | 80.00% | 88.89% |
| DRIVER_LICENSE_RF | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| EMAIL | 5 | 3 | 2 | 62.50% | 71.43% | 66.67% |
| INN | 5 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 1 | 4 | 50.00% | 20.00% | 28.57% |
| PASSPORT_ISSUE_DATE | 3 | 0 | 2 | 100.00% | 60.00% | 75.00% |
| PASSPORT_RF | 4 | 0 | 2 | 100.00% | 66.67% | 80.00% |
| PERSON | 12 | 1 | 0 | 92.31% | 100.00% | 96.00% |
| PHONE_RF | 5 | 2 | 3 | 71.43% | 62.50% | 66.67% |
| PIN | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PLACE_OF_BIRTH | 3 | 1 | 3 | 75.00% | 50.00% | 60.00% |

## Cases with a non-exact mask

- `v14-pos-005`: missing=[('PHONE_RF', 20, 36)]; unexpected=[]
- `v14-pos-011`: missing=[('PASSPORT_RF', 13, 27)]; unexpected=[]
- `v14-pos-012`: missing=[('PASSPORT_RF', 20, 48)]; unexpected=[]
- `v14-pos-013`: missing=[('DIVISION_CODE', 18, 25)]; unexpected=[]
- `v14-pos-015`: missing=[('BIRTH_DATE', 13, 23)]; unexpected=[]
- `v14-pos-017`: missing=[('PLACE_OF_BIRTH', 16, 49)]; unexpected=[]
- `v14-pos-019`: missing=[('CITIZENSHIP', 16, 36)]; unexpected=[]
- `v14-pos-020`: missing=[('CITIZENSHIP', 32, 53)]; unexpected=[]
- `v14-pos-021`: missing=[('PASSPORT_ISSUER', 12, 47)]; unexpected=[]
- `v14-pos-023`: missing=[('PASSPORT_ISSUE_DATE', 12, 22)]; unexpected=[]
- `v14-pos-025`: missing=[('DRIVER_LICENSE_RF', 7, 19)]; unexpected=[]
- `v14-pos-027`: missing=[('ADDRESS_COUNTRY', 18, 24)]; unexpected=[]
- `v14-pos-031`: missing=[('ADDRESS_CITY', 27, 30)]; unexpected=[]
- `v14-pos-033`: missing=[('ADDRESS_STREET', 15, 28)]; unexpected=[]
- `v14-pos-035`: missing=[('ADDRESS_HOUSE', 15, 18)]; unexpected=[]
- `v14-pos-037`: missing=[('ADDRESS_APARTMENT', 13, 16)]; unexpected=[]
- `v14-pos-039`: missing=[('CVV', 12, 15)]; unexpected=[]
- `v14-pos-041`: missing=[('PIN', 21, 25)]; unexpected=[]
- `v14-pos-043`: missing=[('CARDHOLDER_NAME', 16, 32)]; unexpected=[]
- `v14-pos-044`: missing=[('CARDHOLDER_NAME', 25, 37)]; unexpected=[]
- `v14-pos-046`: missing=[('PASSPORT_ISSUER', 41, 78)]; unexpected=[]
- `v14-pos-048`: missing=[('ADDRESS_HOUSE', 78, 80)]; unexpected=[]
- `v14-pos-049`: missing=[('EMAIL', 84, 111)]; unexpected=[]
- `v14-pos-050`: missing=[('PHONE_RF', 73, 88)]; unexpected=[]
- `v14-pos-051`: missing=[('PLACE_OF_BIRTH', 53, 67)]; unexpected=[]
- `v14-pos-052`: missing=[('EMAIL', 58, 78)]; unexpected=[]
- `v14-pos-053`: missing=[('ADDRESS_APARTMENT', 59, 61), ('ADDRESS_CITY', 26, 30), ('ADDRESS_HOUSE', 51, 53), ('ADDRESS_STREET', 35, 46)]; unexpected=[]
- `v14-pos-056`: missing=[('PASSPORT_ISSUER', 30, 51), ('PASSPORT_ISSUE_DATE', 59, 69)]; unexpected=[]
- `v14-pos-059`: missing=[('PHONE_RF', 86, 102)]; unexpected=[]
- `v14-pos-060`: missing=[('ADDRESS_CITY', 45, 52)]; unexpected=[]
- `v14-pos-062`: missing=[('ADDRESS_CITY', 21, 27), ('ADDRESS_COUNTRY', 11, 13), ('ADDRESS_HOUSE', 46, 48), ('ADDRESS_POSTAL_CODE', 14, 20), ('ADDRESS_STREET', 32, 42)]; unexpected=[('ADDRESS_STREET', 32, 44)]
- `v14-pos-064`: missing=[('PASSPORT_ISSUER', 32, 68)]; unexpected=[('PASSPORT_ISSUER', 32, 81)]
- `v14-pos-065`: missing=[('ADDRESS_CITY', 75, 87)]; unexpected=[('PLACE_OF_BIRTH', 68, 87)]
- `v14-pos-066`: missing=[('CARDHOLDER_NAME', 11, 25)]; unexpected=[]
- `v14-pos-069`: missing=[('PLACE_OF_BIRTH', 58, 68)]; unexpected=[]
- `v14-pos-070`: missing=[('ADDRESS_APARTMENT', 84, 86), ('ADDRESS_CITY', 53, 59)]; unexpected=[]
- `v14-neg-084`: missing=[]; unexpected=[('PHONE_RF', 32, 48)]
- `v14-neg-086`: missing=[]; unexpected=[('EMAIL', 14, 44)]
- `v14-neg-088`: missing=[]; unexpected=[('EMAIL', 11, 38)]
- `v14-neg-095`: missing=[]; unexpected=[('ADDRESS_HOUSE', 44, 45), ('ADDRESS_STREET', 32, 38)]
- `v14-neg-118`: missing=[]; unexpected=[('PERSON', 19, 39)]
- `v14-neg-123`: missing=[]; unexpected=[('ADDRESS_HOUSE', 37, 39), ('ADDRESS_STREET', 21, 31)]
- `v14-neg-124`: missing=[]; unexpected=[('BANK_CARD', 15, 31), ('CVV', 36, 39)]
- `v14-neg-128`: missing=[]; unexpected=[('EMAIL', 18, 37), ('PHONE_RF', 44, 60)]
- `v14-neg-129`: missing=[]; unexpected=[('ADDRESS_CITY', 24, 28), ('ADDRESS_HOUSE', 49, 51), ('ADDRESS_STREET', 36, 43)]
- `v14-neg-138`: missing=[]; unexpected=[('ADDRESS_HOUSE', 52, 53), ('ADDRESS_POSTAL_CODE', 16, 22), ('ADDRESS_STREET', 38, 46)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
