# Quality benchmark: ru_pii_sealed_holdout_v8

Dataset version: `8`; cases: **100**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 68.66% |
| Recall | 53.49% |
| F1 | 60.13% |
| Exact masks | 60/100 (60.00%) |
| Exact round trips | 100/100 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_CITY | 0 | 0 | 4 | 0.00% | 0.00% | 0.00% |
| ADDRESS_COUNTRY | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 0 | 1 | 4 | 0.00% | 0.00% | 0.00% |
| ADDRESS_POSTAL_CODE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| ADDRESS_STREET | 0 | 1 | 4 | 0.00% | 0.00% | 0.00% |
| BANK_CARD | 2 | 1 | 1 | 66.67% | 66.67% | 66.67% |
| BIRTH_DATE | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| CARDHOLDER_NAME | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 2 | 2 | 0 | 50.00% | 100.00% | 66.67% |
| DIVISION_CODE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| DRIVER_LICENSE_RF | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| EMAIL | 6 | 5 | 1 | 54.55% | 85.71% | 66.67% |
| INN | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_ISSUE_DATE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PASSPORT_RF | 3 | 2 | 1 | 60.00% | 75.00% | 66.67% |
| PERSON | 7 | 0 | 3 | 100.00% | 70.00% | 82.35% |
| PHONE_RF | 9 | 8 | 0 | 52.94% | 100.00% | 69.23% |
| PIN | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PLACE_OF_BIRTH | 1 | 1 | 2 | 50.00% | 33.33% | 40.00% |

## Cases with a non-exact mask

- `v8-pos-002`: missing=[('PERSON', 16, 44)]; unexpected=[]
- `v8-pos-003`: missing=[('PERSON', 15, 39)]; unexpected=[]
- `v8-pos-004`: missing=[('PERSON', 26, 54)]; unexpected=[]
- `v8-pos-006`: missing=[('EMAIL', 26, 46)]; unexpected=[('EMAIL', 25, 46)]
- `v8-pos-014`: missing=[('BANK_CARD', 20, 39)]; unexpected=[]
- `v8-pos-017`: missing=[('PASSPORT_RF', 45, 55)]; unexpected=[]
- `v8-pos-018`: missing=[('DIVISION_CODE', 31, 38)]; unexpected=[]
- `v8-pos-022`: missing=[('BIRTH_DATE', 33, 43)]; unexpected=[]
- `v8-pos-023`: missing=[('BIRTH_DATE', 13, 21)]; unexpected=[]
- `v8-pos-024`: missing=[('PLACE_OF_BIRTH', 25, 57)]; unexpected=[]
- `v8-pos-025`: missing=[('PLACE_OF_BIRTH', 33, 56)]; unexpected=[('PLACE_OF_BIRTH', 15, 56)]
- `v8-pos-026`: missing=[('CITIZENSHIP', 30, 32)]; unexpected=[]
- `v8-pos-028`: missing=[('PASSPORT_ISSUER', 25, 66)]; unexpected=[]
- `v8-pos-031`: missing=[('PASSPORT_ISSUE_DATE', 21, 52)]; unexpected=[]
- `v8-pos-032`: missing=[('DRIVER_LICENSE_RF', 29, 41)]; unexpected=[]
- `v8-pos-033`: missing=[('DRIVER_LICENSE_RF', 30, 41)]; unexpected=[]
- `v8-pos-034`: missing=[('ADDRESS_CITY', 43, 51), ('ADDRESS_COUNTRY', 25, 31), ('ADDRESS_HOUSE', 74, 76), ('ADDRESS_POSTAL_CODE', 34, 40), ('ADDRESS_STREET', 60, 67)]; unexpected=[]
- `v8-pos-035`: missing=[('ADDRESS_APARTMENT', 65, 68), ('ADDRESS_CITY', 31, 35), ('ADDRESS_HOUSE', 57, 59), ('ADDRESS_POSTAL_CODE', 20, 26), ('ADDRESS_STREET', 41, 52)]; unexpected=[]
- `v8-pos-036`: missing=[('ADDRESS_APARTMENT', 60, 62), ('ADDRESS_CITY', 14, 23), ('ADDRESS_HOUSE', 47, 49), ('ADDRESS_STREET', 33, 41)]; unexpected=[]
- `v8-pos-038`: missing=[('PIN', 23, 27)]; unexpected=[]
- `v8-pos-039`: missing=[('CARDHOLDER_NAME', 23, 38)]; unexpected=[]
- `v8-pos-041`: missing=[('DIVISION_CODE', 98, 105), ('PASSPORT_ISSUER', 37, 75)]; unexpected=[]
- `v8-pos-046`: missing=[('ADDRESS_APARTMENT', 72, 74), ('ADDRESS_CITY', 28, 39), ('ADDRESS_HOUSE', 64, 66), ('ADDRESS_POSTAL_CODE', 20, 26), ('ADDRESS_STREET', 47, 58)]; unexpected=[]
- `v8-pos-048`: missing=[('BIRTH_DATE', 79, 89)]; unexpected=[]
- `v8-neg-057`: missing=[]; unexpected=[('PHONE_RF', 29, 47)]
- `v8-neg-058`: missing=[]; unexpected=[('PHONE_RF', 31, 46)]
- `v8-neg-059`: missing=[]; unexpected=[('PHONE_RF', 37, 53)]
- `v8-neg-060`: missing=[]; unexpected=[('PHONE_RF', 46, 62)]
- `v8-neg-061`: missing=[]; unexpected=[('EMAIL', 33, 57)]
- `v8-neg-065`: missing=[]; unexpected=[('EMAIL', 30, 49)]
- `v8-neg-070`: missing=[]; unexpected=[('ADDRESS_HOUSE', 68, 70), ('ADDRESS_STREET', 54, 62)]
- `v8-neg-078`: missing=[]; unexpected=[('PHONE_RF', 20, 35)]
- `v8-neg-081`: missing=[]; unexpected=[('PASSPORT_RF', 43, 55)]
- `v8-neg-085`: missing=[]; unexpected=[('CVV', 15, 18)]
- `v8-neg-091`: missing=[]; unexpected=[('EMAIL', 38, 58), ('PHONE_RF', 20, 36)]
- `v8-neg-092`: missing=[]; unexpected=[('PHONE_RF', 41, 57)]
- `v8-neg-094`: missing=[]; unexpected=[('BANK_CARD', 28, 47), ('CVV', 53, 56)]
- `v8-neg-095`: missing=[]; unexpected=[('EMAIL', 52, 76)]
- `v8-neg-096`: missing=[]; unexpected=[('PASSPORT_RF', 24, 48)]
- `v8-neg-100`: missing=[]; unexpected=[('PHONE_RF', 54, 70)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
