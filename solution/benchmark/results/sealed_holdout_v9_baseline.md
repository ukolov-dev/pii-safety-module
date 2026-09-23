# Quality benchmark: ru_pii_sealed_holdout_v9

Dataset version: `9`; cases: **100**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 69.70% |
| Recall | 47.92% |
| F1 | 56.79% |
| Exact masks | 53/100 (53.00%) |
| Exact round trips | 100/100 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 1 | 0 | 4 | 100.00% | 20.00% | 33.33% |
| ADDRESS_CITY | 2 | 0 | 4 | 100.00% | 33.33% | 50.00% |
| ADDRESS_COUNTRY | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 1 | 1 | 4 | 50.00% | 20.00% | 28.57% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_STREET | 1 | 0 | 4 | 100.00% | 20.00% | 33.33% |
| BANK_CARD | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| CARDHOLDER_NAME | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 1 | 1 | 2 | 50.00% | 33.33% | 40.00% |
| DIVISION_CODE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| DRIVER_LICENSE_RF | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| EMAIL | 6 | 7 | 1 | 46.15% | 85.71% | 60.00% |
| INN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_ISSUE_DATE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_RF | 3 | 2 | 2 | 60.00% | 60.00% | 60.00% |
| PERSON | 5 | 0 | 4 | 100.00% | 55.56% | 71.43% |
| PHONE_RF | 8 | 7 | 1 | 53.33% | 88.89% | 66.67% |
| PIN | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| PLACE_OF_BIRTH | 1 | 2 | 2 | 33.33% | 33.33% | 33.33% |

## Cases with a non-exact mask

- `v9-pos-003`: missing=[('ADDRESS_APARTMENT', 79, 81), ('ADDRESS_CITY', 44, 51), ('ADDRESS_HOUSE', 72, 73), ('ADDRESS_POSTAL_CODE', 36, 42), ('ADDRESS_STREET', 59, 67)]; unexpected=[]
- `v9-pos-004`: missing=[('BIRTH_DATE', 46, 56)]; unexpected=[]
- `v9-pos-005`: missing=[('CARDHOLDER_NAME', 66, 77), ('CVV', 44, 47)]; unexpected=[]
- `v9-pos-006`: missing=[('CITIZENSHIP', 51, 53)]; unexpected=[]
- `v9-pos-007`: missing=[('DRIVER_LICENSE_RF', 38, 50)]; unexpected=[]
- `v9-pos-009`: missing=[('PERSON', 25, 53)]; unexpected=[]
- `v9-pos-010`: missing=[('PLACE_OF_BIRTH', 36, 76)]; unexpected=[('PLACE_OF_BIRTH', 24, 76)]
- `v9-pos-011`: missing=[('DIVISION_CODE', 80, 87), ('PASSPORT_ISSUE_DATE', 64, 74)]; unexpected=[]
- `v9-pos-014`: missing=[('ADDRESS_APARTMENT', 86, 88), ('ADDRESS_CITY', 35, 44), ('ADDRESS_COUNTRY', 17, 23), ('ADDRESS_HOUSE', 72, 74), ('ADDRESS_POSTAL_CODE', 26, 32), ('ADDRESS_STREET', 53, 65)]; unexpected=[]
- `v9-pos-015`: missing=[('PASSPORT_RF', 27, 52)]; unexpected=[]
- `v9-pos-017`: missing=[('PERSON', 16, 39)]; unexpected=[]
- `v9-pos-024`: missing=[('PASSPORT_ISSUER', 26, 62)]; unexpected=[]
- `v9-pos-025`: missing=[('PASSPORT_ISSUE_DATE', 34, 44)]; unexpected=[]
- `v9-pos-026`: missing=[('DIVISION_CODE', 30, 37)]; unexpected=[]
- `v9-pos-027`: missing=[('CVV', 36, 39)]; unexpected=[]
- `v9-pos-028`: missing=[('CARDHOLDER_NAME', 28, 45)]; unexpected=[]
- `v9-pos-030`: missing=[('PASSPORT_RF', 28, 38)]; unexpected=[]
- `v9-pos-031`: missing=[('BIRTH_DATE', 39, 49), ('PLACE_OF_BIRTH', 52, 63)]; unexpected=[]
- `v9-pos-033`: missing=[('DIVISION_CODE', 89, 96), ('PASSPORT_ISSUER', 31, 65)]; unexpected=[]
- `v9-pos-034`: missing=[('ADDRESS_APARTMENT', 68, 70), ('ADDRESS_CITY', 35, 40), ('ADDRESS_HOUSE', 60, 62), ('ADDRESS_POSTAL_CODE', 27, 33), ('ADDRESS_STREET', 48, 54)]; unexpected=[]
- `v9-pos-035`: missing=[('DRIVER_LICENSE_RF', 55, 67)]; unexpected=[]
- `v9-pos-036`: missing=[('CARDHOLDER_NAME', 59, 72)]; unexpected=[]
- `v9-pos-040`: missing=[('PERSON', 18, 46)]; unexpected=[]
- `v9-pos-041`: missing=[('PHONE_RF', 19, 35)]; unexpected=[]
- `v9-pos-042`: missing=[('EMAIL', 30, 58)]; unexpected=[('EMAIL', 29, 58)]
- `v9-pos-043`: missing=[('BIRTH_DATE', 26, 59)]; unexpected=[]
- `v9-pos-044`: missing=[('ADDRESS_COUNTRY', 27, 47)]; unexpected=[]
- `v9-pos-047`: missing=[('PIN', 37, 41)]; unexpected=[]
- `v9-pos-048`: missing=[('PERSON', 26, 55)]; unexpected=[]
- `v9-pos-050`: missing=[('ADDRESS_APARTMENT', 53, 55), ('ADDRESS_CITY', 65, 71), ('ADDRESS_HOUSE', 40, 42), ('ADDRESS_STREET', 26, 34)]; unexpected=[]
- `v9-neg-056`: missing=[]; unexpected=[('PHONE_RF', 35, 53)]
- `v9-neg-059`: missing=[]; unexpected=[('PHONE_RF', 29, 45)]
- `v9-neg-060`: missing=[]; unexpected=[('PHONE_RF', 10, 26)]
- `v9-neg-061`: missing=[]; unexpected=[('EMAIL', 29, 47)]
- `v9-neg-062`: missing=[]; unexpected=[('EMAIL', 21, 43)]
- `v9-neg-063`: missing=[]; unexpected=[('EMAIL', 21, 43)]
- `v9-neg-064`: missing=[]; unexpected=[('EMAIL', 28, 54)]
- `v9-neg-070`: missing=[]; unexpected=[('ADDRESS_HOUSE', 78, 80)]
- `v9-neg-078`: missing=[]; unexpected=[('PHONE_RF', 17, 33)]
- `v9-neg-081`: missing=[]; unexpected=[('PASSPORT_RF', 27, 39)]
- `v9-neg-085`: missing=[]; unexpected=[('CVV', 12, 15)]
- `v9-neg-089`: missing=[]; unexpected=[('PLACE_OF_BIRTH', 44, 58)]
- `v9-neg-091`: missing=[]; unexpected=[('EMAIL', 37, 60), ('PHONE_RF', 19, 35)]
- `v9-neg-095`: missing=[]; unexpected=[('EMAIL', 56, 80)]
- `v9-neg-096`: missing=[]; unexpected=[('PASSPORT_RF', 25, 49)]
- `v9-neg-099`: missing=[]; unexpected=[('PHONE_RF', 39, 55)]
- `v9-neg-100`: missing=[]; unexpected=[('PHONE_RF', 48, 64)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
