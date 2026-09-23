# Quality benchmark: ru_pii_sealed_holdout_v15

Dataset version: `15`; cases: **160**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 76.27% |
| Recall | 62.50% |
| F1 | 68.70% |
| Exact masks | 106/160 (66.25%) |
| Exact round trips | 160/160 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 4 | 0 | 4 | 100.00% | 50.00% | 66.67% |
| ADDRESS_CITY | 4 | 3 | 5 | 57.14% | 44.44% | 50.00% |
| ADDRESS_COUNTRY | 1 | 0 | 4 | 100.00% | 20.00% | 33.33% |
| ADDRESS_HOUSE | 5 | 4 | 3 | 55.56% | 62.50% | 58.82% |
| ADDRESS_POSTAL_CODE | 0 | 1 | 5 | 0.00% | 0.00% | 0.00% |
| ADDRESS_STREET | 3 | 3 | 5 | 50.00% | 37.50% | 42.86% |
| BANK_CARD | 5 | 1 | 0 | 83.33% | 100.00% | 90.91% |
| BIRTH_DATE | 5 | 1 | 2 | 83.33% | 71.43% | 76.92% |
| CARDHOLDER_NAME | 2 | 0 | 2 | 100.00% | 50.00% | 66.67% |
| CITIZENSHIP | 4 | 0 | 1 | 100.00% | 80.00% | 88.89% |
| CVV | 3 | 0 | 2 | 100.00% | 60.00% | 75.00% |
| DIVISION_CODE | 4 | 0 | 2 | 100.00% | 66.67% | 80.00% |
| DRIVER_LICENSE_RF | 4 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| EMAIL | 6 | 8 | 2 | 42.86% | 75.00% | 54.55% |
| INN | 5 | 2 | 1 | 71.43% | 83.33% | 76.92% |
| PASSPORT_ISSUER | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| PASSPORT_ISSUE_DATE | 3 | 0 | 3 | 100.00% | 50.00% | 66.67% |
| PASSPORT_RF | 4 | 2 | 3 | 66.67% | 57.14% | 61.54% |
| PERSON | 11 | 0 | 4 | 100.00% | 73.33% | 84.62% |
| PHONE_RF | 7 | 3 | 1 | 70.00% | 87.50% | 77.78% |
| PIN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 4 | 0 | 2 | 100.00% | 66.67% | 80.00% |

## Cases with a non-exact mask

- `v15-pos-002`: missing=[('PERSON', 23, 51)]; unexpected=[]
- `v15-pos-003`: missing=[('PERSON', 42, 69)]; unexpected=[]
- `v15-pos-014`: missing=[('PASSPORT_RF', 18, 61)]; unexpected=[]
- `v15-pos-016`: missing=[('DIVISION_CODE', 41, 48)]; unexpected=[]
- `v15-pos-020`: missing=[('PLACE_OF_BIRTH', 39, 47)]; unexpected=[]
- `v15-pos-023`: missing=[('PASSPORT_ISSUER', 33, 67)]; unexpected=[]
- `v15-pos-024`: missing=[('PASSPORT_ISSUER', 42, 67)]; unexpected=[]
- `v15-pos-025`: missing=[('PASSPORT_ISSUE_DATE', 55, 65)]; unexpected=[]
- `v15-pos-026`: missing=[('PASSPORT_ISSUE_DATE', 20, 55)]; unexpected=[]
- `v15-pos-029`: missing=[('ADDRESS_COUNTRY', 64, 70)]; unexpected=[]
- `v15-pos-030`: missing=[('ADDRESS_COUNTRY', 42, 44)]; unexpected=[('ADDRESS_CITY', 35, 41)]
- `v15-pos-031`: missing=[('ADDRESS_POSTAL_CODE', 55, 61)]; unexpected=[]
- `v15-pos-032`: missing=[('ADDRESS_POSTAL_CODE', 43, 49)]; unexpected=[]
- `v15-pos-040`: missing=[('ADDRESS_APARTMENT', 42, 44)]; unexpected=[]
- `v15-pos-041`: missing=[('CVV', 57, 60)]; unexpected=[]
- `v15-pos-045`: missing=[('CARDHOLDER_NAME', 36, 49)]; unexpected=[]
- `v15-pos-046`: missing=[('CARDHOLDER_NAME', 36, 52)]; unexpected=[]
- `v15-pos-047`: missing=[('PHONE_RF', 76, 92)]; unexpected=[]
- `v15-pos-048`: missing=[]; unexpected=[('EMAIL', 26, 49)]
- `v15-pos-049`: missing=[('BIRTH_DATE', 34, 44)]; unexpected=[]
- `v15-pos-051`: missing=[('CVV', 49, 52)]; unexpected=[]
- `v15-pos-052`: missing=[('ADDRESS_CITY', 50, 57), ('ADDRESS_POSTAL_CODE', 42, 48)]; unexpected=[('ADDRESS_HOUSE', 42, 48)]
- `v15-pos-053`: missing=[('PLACE_OF_BIRTH', 43, 56)]; unexpected=[]
- `v15-pos-054`: missing=[('EMAIL', 75, 101), ('INN', 107, 119)]; unexpected=[]
- `v15-pos-055`: missing=[('ADDRESS_APARTMENT', 91, 93), ('ADDRESS_CITY', 51, 57), ('ADDRESS_HOUSE', 78, 80), ('ADDRESS_STREET', 65, 72)]; unexpected=[]
- `v15-pos-056`: missing=[('BIRTH_DATE', 44, 54)]; unexpected=[]
- `v15-pos-058`: missing=[('DIVISION_CODE', 76, 83), ('PASSPORT_ISSUE_DATE', 60, 70)]; unexpected=[]
- `v15-pos-060`: missing=[('PERSON', 10, 38)]; unexpected=[]
- `v15-pos-061`: missing=[('ADDRESS_STREET', 89, 102)]; unexpected=[('ADDRESS_CITY', 28, 36), ('ADDRESS_CITY', 98, 102), ('ADDRESS_HOUSE', 56, 57), ('ADDRESS_STREET', 44, 50)]
- `v15-pos-063`: missing=[]; unexpected=[('BIRTH_DATE', 27, 37)]
- `v15-pos-065`: missing=[('PASSPORT_RF', 23, 35)]; unexpected=[]
- `v15-pos-067`: missing=[('ADDRESS_APARTMENT', 87, 89), ('ADDRESS_CITY', 57, 63), ('ADDRESS_COUNTRY', 41, 47), ('ADDRESS_HOUSE', 79, 81), ('ADDRESS_POSTAL_CODE', 49, 55), ('ADDRESS_STREET', 68, 74)]; unexpected=[]
- `v15-pos-070`: missing=[('EMAIL', 80, 103)]; unexpected=[]
- `v15-pos-072`: missing=[('ADDRESS_CITY', 25, 31), ('ADDRESS_STREET', 41, 49)]; unexpected=[]
- `v15-pos-073`: missing=[('PASSPORT_RF', 19, 60)]; unexpected=[]
- `v15-pos-076`: missing=[('PERSON', 28, 51)]; unexpected=[]
- `v15-pos-077`: missing=[('ADDRESS_APARTMENT', 84, 86), ('ADDRESS_CITY', 41, 47), ('ADDRESS_COUNTRY', 16, 18), ('ADDRESS_HOUSE', 71, 73), ('ADDRESS_POSTAL_CODE', 27, 33), ('ADDRESS_STREET', 55, 65)]; unexpected=[]
- `v15-pos-078`: missing=[('PASSPORT_ISSUER', 34, 60)]; unexpected=[]
- `v15-pos-080`: missing=[('CITIZENSHIP', 75, 77)]; unexpected=[]
- `v15-neg-094`: missing=[]; unexpected=[('PHONE_RF', 18, 34)]
- `v15-neg-095`: missing=[]; unexpected=[('EMAIL', 35, 61)]
- `v15-neg-097`: missing=[]; unexpected=[('EMAIL', 21, 43)]
- `v15-neg-099`: missing=[]; unexpected=[('EMAIL', 28, 54)]
- `v15-neg-100`: missing=[]; unexpected=[('EMAIL', 22, 50)]
- `v15-neg-113`: missing=[]; unexpected=[('INN', 4, 16)]
- `v15-neg-119`: missing=[]; unexpected=[('PASSPORT_RF', 29, 41)]
- `v15-neg-136`: missing=[]; unexpected=[('PASSPORT_RF', 17, 41)]
- `v15-neg-138`: missing=[]; unexpected=[('EMAIL', 19, 42), ('PHONE_RF', 44, 60)]
- `v15-neg-142`: missing=[]; unexpected=[('ADDRESS_HOUSE', 55, 56), ('ADDRESS_STREET', 43, 49)]
- `v15-neg-148`: missing=[]; unexpected=[('EMAIL', 6, 29)]
- `v15-neg-153`: missing=[]; unexpected=[('BANK_CARD', 6, 25)]
- `v15-neg-154`: missing=[]; unexpected=[('EMAIL', 47, 72), ('PHONE_RF', 28, 44)]
- `v15-neg-155`: missing=[]; unexpected=[('ADDRESS_HOUSE', 53, 55), ('ADDRESS_POSTAL_CODE', 13, 19), ('ADDRESS_STREET', 35, 47)]
- `v15-neg-157`: missing=[]; unexpected=[('INN', 4, 16)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
