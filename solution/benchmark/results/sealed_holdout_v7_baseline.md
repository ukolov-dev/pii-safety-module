# Quality benchmark: ru_pii_sealed_holdout_v7

Dataset version: `7`; cases: **100**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 71.25% |
| Recall | 66.28% |
| F1 | 68.67% |
| Exact masks | 60/100 (60.00%) |
| Exact round trips | 100/100 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 2 | 0 | 2 | 100.00% | 50.00% | 66.67% |
| ADDRESS_CITY | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_COUNTRY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 2 | 3 | 2 | 40.00% | 50.00% | 44.44% |
| ADDRESS_POSTAL_CODE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| ADDRESS_STREET | 2 | 3 | 2 | 40.00% | 50.00% | 44.44% |
| BANK_CARD | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| BIRTH_DATE | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| CARDHOLDER_NAME | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 2 | 2 | 0 | 50.00% | 100.00% | 66.67% |
| DIVISION_CODE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| DRIVER_LICENSE_RF | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| EMAIL | 9 | 5 | 0 | 64.29% | 100.00% | 78.26% |
| INN | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PASSPORT_ISSUE_DATE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PASSPORT_RF | 3 | 2 | 1 | 60.00% | 75.00% | 66.67% |
| PERSON | 5 | 0 | 4 | 100.00% | 55.56% | 71.43% |
| PHONE_RF | 8 | 7 | 0 | 53.33% | 100.00% | 69.57% |
| PIN | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PLACE_OF_BIRTH | 1 | 1 | 2 | 50.00% | 33.33% | 40.00% |

## Cases with a non-exact mask

- `v7-pos-002`: missing=[('PERSON', 13, 44)]; unexpected=[]
- `v7-pos-003`: missing=[('PERSON', 16, 40)]; unexpected=[]
- `v7-pos-004`: missing=[('PERSON', 18, 46)]; unexpected=[]
- `v7-pos-013`: missing=[('BANK_CARD', 25, 44)]; unexpected=[]
- `v7-pos-017`: missing=[('PASSPORT_RF', 38, 48)]; unexpected=[]
- `v7-pos-019`: missing=[('DIVISION_CODE', 22, 29)]; unexpected=[]
- `v7-pos-020`: missing=[('BIRTH_DATE', 26, 36)]; unexpected=[]
- `v7-pos-023`: missing=[('BIRTH_DATE', 22, 31)]; unexpected=[]
- `v7-pos-024`: missing=[('PLACE_OF_BIRTH', 27, 71)]; unexpected=[('PLACE_OF_BIRTH', 15, 71)]
- `v7-pos-026`: missing=[('CITIZENSHIP', 38, 44)]; unexpected=[]
- `v7-pos-028`: missing=[('PASSPORT_ISSUER', 17, 59)]; unexpected=[]
- `v7-pos-033`: missing=[('DRIVER_LICENSE_RF', 39, 50)]; unexpected=[]
- `v7-pos-034`: missing=[('ADDRESS_CITY', 42, 49)]; unexpected=[]
- `v7-pos-036`: missing=[('ADDRESS_APARTMENT', 72, 75), ('ADDRESS_CITY', 20, 28), ('ADDRESS_HOUSE', 59, 61), ('ADDRESS_STREET', 43, 53)]; unexpected=[]
- `v7-pos-038`: missing=[('PIN', 24, 28)]; unexpected=[]
- `v7-pos-039`: missing=[('CARDHOLDER_NAME', 32, 47)]; unexpected=[]
- `v7-pos-040`: missing=[('BIRTH_DATE', 45, 55)]; unexpected=[]
- `v7-pos-041`: missing=[('PASSPORT_ISSUE_DATE', 54, 64)]; unexpected=[]
- `v7-pos-042`: missing=[('CARDHOLDER_NAME', 55, 68)]; unexpected=[]
- `v7-pos-044`: missing=[('PLACE_OF_BIRTH', 30, 46)]; unexpected=[]
- `v7-pos-046`: missing=[('ADDRESS_APARTMENT', 71, 73), ('ADDRESS_CITY', 30, 34), ('ADDRESS_HOUSE', 58, 60), ('ADDRESS_POSTAL_CODE', 22, 28), ('ADDRESS_STREET', 42, 52)]; unexpected=[]
- `v7-pos-048`: missing=[('PERSON', 26, 50)]; unexpected=[]
- `v7-neg-057`: missing=[]; unexpected=[('PHONE_RF', 30, 48)]
- `v7-neg-058`: missing=[]; unexpected=[('PHONE_RF', 42, 57)]
- `v7-neg-059`: missing=[]; unexpected=[('PHONE_RF', 37, 53)]
- `v7-neg-063`: missing=[]; unexpected=[('EMAIL', 28, 52)]
- `v7-neg-064`: missing=[]; unexpected=[('EMAIL', 31, 52)]
- `v7-neg-065`: missing=[]; unexpected=[('EMAIL', 43, 62)]
- `v7-neg-067`: missing=[]; unexpected=[('ADDRESS_HOUSE', 56, 58), ('ADDRESS_STREET', 42, 50)]
- `v7-neg-070`: missing=[]; unexpected=[('ADDRESS_HOUSE', 69, 71), ('ADDRESS_STREET', 57, 63)]
- `v7-neg-078`: missing=[]; unexpected=[('PHONE_RF', 15, 31)]
- `v7-neg-081`: missing=[]; unexpected=[('PASSPORT_RF', 43, 55)]
- `v7-neg-085`: missing=[]; unexpected=[('CVV', 25, 28)]
- `v7-neg-091`: missing=[]; unexpected=[('EMAIL', 39, 59), ('PHONE_RF', 21, 37)]
- `v7-neg-092`: missing=[]; unexpected=[('PHONE_RF', 51, 67)]
- `v7-neg-093`: missing=[]; unexpected=[('ADDRESS_HOUSE', 59, 62), ('ADDRESS_STREET', 46, 53)]
- `v7-neg-094`: missing=[]; unexpected=[('CVV', 58, 61)]
- `v7-neg-095`: missing=[]; unexpected=[('EMAIL', 59, 81)]
- `v7-neg-096`: missing=[]; unexpected=[('PASSPORT_RF', 20, 44)]
- `v7-neg-100`: missing=[]; unexpected=[('PHONE_RF', 43, 59)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
