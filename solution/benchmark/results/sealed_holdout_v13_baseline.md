# Quality benchmark: ru_pii_sealed_holdout_v13

Dataset version: `13`; cases: **120**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 70.59% |
| Recall | 53.93% |
| F1 | 61.15% |
| Exact masks | 75/120 (62.50%) |
| Exact round trips | 120/120 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| ADDRESS_CITY | 1 | 1 | 6 | 50.00% | 14.29% | 22.22% |
| ADDRESS_COUNTRY | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| ADDRESS_HOUSE | 3 | 2 | 3 | 60.00% | 50.00% | 54.55% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 4 | 100.00% | 20.00% | 33.33% |
| ADDRESS_STREET | 3 | 1 | 3 | 75.00% | 50.00% | 60.00% |
| BANK_CARD | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 3 | 0 | 2 | 100.00% | 60.00% | 75.00% |
| CARDHOLDER_NAME | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 2 | 2 | 0 | 50.00% | 100.00% | 66.67% |
| DIVISION_CODE | 2 | 0 | 2 | 100.00% | 50.00% | 66.67% |
| DRIVER_LICENSE_RF | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| EMAIL | 5 | 7 | 0 | 41.67% | 100.00% | 58.82% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| PASSPORT_RF | 3 | 0 | 2 | 100.00% | 60.00% | 75.00% |
| PERSON | 3 | 1 | 6 | 75.00% | 33.33% | 46.15% |
| PHONE_RF | 5 | 6 | 0 | 45.45% | 100.00% | 62.50% |
| PIN | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| PLACE_OF_BIRTH | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |

## Cases with a non-exact mask

- `v13-pos-002`: missing=[('PERSON', 19, 49)]; unexpected=[]
- `v13-pos-003`: missing=[('PERSON', 31, 57)]; unexpected=[]
- `v13-pos-004`: missing=[('PERSON', 21, 55)]; unexpected=[]
- `v13-pos-005`: missing=[('PERSON', 30, 58)]; unexpected=[]
- `v13-pos-006`: missing=[('PERSON', 16, 39)]; unexpected=[('PERSON', 10, 32)]
- `v13-pos-008`: missing=[('PERSON', 27, 54)]; unexpected=[]
- `v13-pos-009`: missing=[('ADDRESS_CITY', 56, 64)]; unexpected=[]
- `v13-pos-010`: missing=[('ADDRESS_CITY', 47, 57), ('ADDRESS_COUNTRY', 31, 37), ('ADDRESS_POSTAL_CODE', 39, 45)]; unexpected=[]
- `v13-pos-011`: missing=[('ADDRESS_APARTMENT', 76, 78), ('ADDRESS_CITY', 11, 21), ('ADDRESS_HOUSE', 63, 65), ('ADDRESS_STREET', 46, 55)]; unexpected=[]
- `v13-pos-012`: missing=[('ADDRESS_APARTMENT', 93, 95), ('ADDRESS_CITY', 45, 56), ('ADDRESS_HOUSE', 80, 82), ('ADDRESS_STREET', 67, 74)]; unexpected=[]
- `v13-pos-013`: missing=[('ADDRESS_COUNTRY', 42, 62)]; unexpected=[]
- `v13-pos-015`: missing=[('ADDRESS_POSTAL_CODE', 46, 52)]; unexpected=[]
- `v13-pos-016`: missing=[('ADDRESS_POSTAL_CODE', 36, 42)]; unexpected=[]
- `v13-pos-017`: missing=[('ADDRESS_CITY', 46, 52)]; unexpected=[]
- `v13-pos-019`: missing=[('ADDRESS_STREET', 41, 50)]; unexpected=[]
- `v13-pos-020`: missing=[('ADDRESS_APARTMENT', 50, 52), ('ADDRESS_HOUSE', 35, 38)]; unexpected=[]
- `v13-pos-034`: missing=[('PASSPORT_RF', 16, 49)]; unexpected=[]
- `v13-pos-035`: missing=[('PASSPORT_RF', 43, 53)]; unexpected=[]
- `v13-pos-038`: missing=[('DIVISION_CODE', 23, 30)]; unexpected=[]
- `v13-pos-039`: missing=[('DIVISION_CODE', 40, 47)]; unexpected=[]
- `v13-pos-042`: missing=[('BIRTH_DATE', 38, 48)]; unexpected=[]
- `v13-pos-043`: missing=[('BIRTH_DATE', 33, 41)]; unexpected=[]
- `v13-pos-045`: missing=[('PLACE_OF_BIRTH', 34, 49)]; unexpected=[('ADDRESS_CITY', 37, 49)]
- `v13-pos-048`: missing=[('CITIZENSHIP', 27, 47)]; unexpected=[]
- `v13-pos-050`: missing=[('PASSPORT_ISSUER', 18, 51)]; unexpected=[]
- `v13-pos-051`: missing=[('PASSPORT_ISSUER', 20, 44)]; unexpected=[]
- `v13-pos-053`: missing=[('DRIVER_LICENSE_RF', 38, 50)]; unexpected=[]
- `v13-pos-055`: missing=[('PIN', 37, 41)]; unexpected=[]
- `v13-pos-058`: missing=[('PASSPORT_ISSUER', 32, 68), ('PASSPORT_ISSUE_DATE', 69, 79)]; unexpected=[]
- `v13-pos-059`: missing=[('ADDRESS_CITY', 21, 26), ('ADDRESS_POSTAL_CODE', 13, 19)]; unexpected=[('ADDRESS_HOUSE', 13, 19)]
- `v13-neg-069`: missing=[]; unexpected=[('PHONE_RF', 36, 54)]
- `v13-neg-070`: missing=[]; unexpected=[('PHONE_RF', 29, 44)]
- `v13-neg-074`: missing=[]; unexpected=[('PHONE_RF', 21, 37)]
- `v13-neg-075`: missing=[]; unexpected=[('PHONE_RF', 27, 43)]
- `v13-neg-077`: missing=[]; unexpected=[('EMAIL', 24, 52)]
- `v13-neg-078`: missing=[]; unexpected=[('EMAIL', 28, 57)]
- `v13-neg-079`: missing=[]; unexpected=[('EMAIL', 27, 55)]
- `v13-neg-080`: missing=[]; unexpected=[('EMAIL', 27, 59)]
- `v13-neg-081`: missing=[]; unexpected=[('EMAIL', 31, 56)]
- `v13-neg-083`: missing=[]; unexpected=[('EMAIL', 24, 46)]
- `v13-neg-086`: missing=[]; unexpected=[('ADDRESS_HOUSE', 61, 63), ('ADDRESS_STREET', 43, 55)]
- `v13-neg-107`: missing=[]; unexpected=[('CVV', 23, 26)]
- `v13-neg-115`: missing=[]; unexpected=[('PHONE_RF', 13, 29)]
- `v13-neg-118`: missing=[]; unexpected=[('CVV', 46, 49)]
- `v13-neg-119`: missing=[]; unexpected=[('EMAIL', 19, 43), ('PHONE_RF', 45, 61)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
