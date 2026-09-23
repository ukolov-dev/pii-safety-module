# Quality benchmark: ru_pii_sealed_holdout_v10

Dataset version: `10`; cases: **110**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 82.80% |
| Recall | 75.49% |
| F1 | 78.97% |
| Exact masks | 81/110 (73.64%) |
| Exact round trips | 110/110 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 7 | 0 | 1 | 100.00% | 87.50% | 93.33% |
| ADDRESS_CITY | 2 | 0 | 6 | 100.00% | 25.00% | 40.00% |
| ADDRESS_COUNTRY | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| ADDRESS_HOUSE | 7 | 3 | 1 | 70.00% | 87.50% | 77.78% |
| ADDRESS_POSTAL_CODE | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| ADDRESS_STREET | 7 | 4 | 1 | 63.64% | 87.50% | 73.68% |
| BANK_CARD | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 4 | 0 | 2 | 100.00% | 66.67% | 80.00% |
| CARDHOLDER_NAME | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| DRIVER_LICENSE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 8 | 4 | 0 | 66.67% | 100.00% | 80.00% |
| INN | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| PASSPORT_ISSUE_DATE | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| PASSPORT_RF | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PERSON | 8 | 0 | 4 | 100.00% | 66.67% | 80.00% |
| PHONE_RF | 8 | 4 | 0 | 66.67% | 100.00% | 80.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 0 | 1 | 3 | 0.00% | 0.00% | 0.00% |

## Cases with a non-exact mask

- `v10-pos-002`: missing=[('PERSON', 24, 52)]; unexpected=[]
- `v10-pos-004`: missing=[('PERSON', 21, 50)]; unexpected=[]
- `v10-pos-006`: missing=[('PERSON', 33, 59)]; unexpected=[]
- `v10-pos-007`: missing=[('PERSON', 25, 52)]; unexpected=[]
- `v10-pos-009`: missing=[('ADDRESS_CITY', 47, 53)]; unexpected=[]
- `v10-pos-011`: missing=[('ADDRESS_CITY', 27, 35)]; unexpected=[]
- `v10-pos-012`: missing=[('ADDRESS_APARTMENT', 74, 76), ('ADDRESS_CITY', 27, 33), ('ADDRESS_HOUSE', 62, 63), ('ADDRESS_STREET', 44, 53)]; unexpected=[]
- `v10-pos-013`: missing=[('ADDRESS_CITY', 46, 51), ('ADDRESS_COUNTRY', 27, 29)]; unexpected=[]
- `v10-pos-027`: missing=[('PASSPORT_RF', 19, 53)]; unexpected=[]
- `v10-pos-032`: missing=[('BIRTH_DATE', 29, 39)]; unexpected=[]
- `v10-pos-033`: missing=[('BIRTH_DATE', 20, 28)]; unexpected=[]
- `v10-pos-034`: missing=[('PLACE_OF_BIRTH', 29, 69)]; unexpected=[('PLACE_OF_BIRTH', 15, 69)]
- `v10-pos-035`: missing=[('PLACE_OF_BIRTH', 19, 33)]; unexpected=[]
- `v10-pos-037`: missing=[('PASSPORT_ISSUER', 17, 48)]; unexpected=[]
- `v10-pos-038`: missing=[('PASSPORT_ISSUE_DATE', 31, 41)]; unexpected=[]
- `v10-pos-044`: missing=[('DIVISION_CODE', 81, 88), ('PASSPORT_ISSUE_DATE', 55, 65)]; unexpected=[]
- `v10-pos-048`: missing=[('ADDRESS_CITY', 51, 57)]; unexpected=[]
- `v10-pos-051`: missing=[('PLACE_OF_BIRTH', 23, 35)]; unexpected=[]
- `v10-pos-055`: missing=[('ADDRESS_CITY', 52, 58), ('ADDRESS_POSTAL_CODE', 44, 50)]; unexpected=[]
- `v10-neg-063`: missing=[]; unexpected=[('PHONE_RF', 36, 51)]
- `v10-neg-066`: missing=[]; unexpected=[('EMAIL', 21, 43)]
- `v10-neg-078`: missing=[]; unexpected=[('PHONE_RF', 16, 32)]
- `v10-neg-093`: missing=[]; unexpected=[('ADDRESS_HOUSE', 66, 68), ('ADDRESS_STREET', 51, 60)]
- `v10-neg-096`: missing=[]; unexpected=[('ADDRESS_STREET', 22, 30)]
- `v10-neg-098`: missing=[]; unexpected=[('EMAIL', 6, 32)]
- `v10-neg-099`: missing=[]; unexpected=[('ADDRESS_HOUSE', 63, 65), ('ADDRESS_STREET', 49, 57)]
- `v10-neg-104`: missing=[]; unexpected=[('EMAIL', 45, 71), ('PHONE_RF', 24, 40)]
- `v10-neg-108`: missing=[]; unexpected=[('ADDRESS_HOUSE', 76, 77), ('ADDRESS_STREET', 60, 70)]
- `v10-neg-110`: missing=[]; unexpected=[('EMAIL', 30, 47), ('PHONE_RF', 49, 65)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
