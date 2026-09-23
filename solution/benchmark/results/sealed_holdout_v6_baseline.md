# Quality benchmark: ru_pii_sealed_holdout_v6

Dataset version: `6`; cases: **90**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 79.37% |
| Recall | 56.82% |
| F1 | 66.23% |
| Exact masks | 55/90 (61.11%) |
| Exact round trips | 90/90 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_CITY | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| ADDRESS_COUNTRY | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| ADDRESS_HOUSE | 1 | 1 | 3 | 50.00% | 25.00% | 33.33% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| ADDRESS_STREET | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| BANK_CARD | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| BIRTH_DATE | 5 | 0 | 2 | 100.00% | 71.43% | 83.33% |
| CARDHOLDER_NAME | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 1 | 1 | 1 | 50.00% | 50.00% | 50.00% |
| DIVISION_CODE | 2 | 1 | 1 | 66.67% | 66.67% | 66.67% |
| DRIVER_LICENSE_RF | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| EMAIL | 8 | 3 | 1 | 72.73% | 88.89% | 80.00% |
| INN | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| PASSPORT_ISSUER | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_ISSUE_DATE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PASSPORT_RF | 2 | 2 | 2 | 50.00% | 50.00% | 50.00% |
| PERSON | 5 | 0 | 4 | 100.00% | 55.56% | 71.43% |
| PHONE_RF | 8 | 4 | 0 | 66.67% | 100.00% | 80.00% |
| PIN | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PLACE_OF_BIRTH | 1 | 1 | 2 | 50.00% | 33.33% | 40.00% |

## Cases with a non-exact mask

- `v6-pos-person-002`: missing=[('PERSON', 23, 51)]; unexpected=[]
- `v6-pos-person-003`: missing=[('PERSON', 18, 42)]; unexpected=[]
- `v6-pos-person-004`: missing=[('PERSON', 20, 48)]; unexpected=[]
- `v6-pos-email-006`: missing=[('EMAIL', 21, 42)]; unexpected=[('EMAIL', 20, 42)]
- `v6-pos-inn-012`: missing=[('INN', 30, 42)]; unexpected=[]
- `v6-pos-card-013`: missing=[('BANK_CARD', 20, 39)]; unexpected=[]
- `v6-pos-passport-016`: missing=[('PASSPORT_RF', 0, 47)]; unexpected=[]
- `v6-pos-passport-017`: missing=[('PASSPORT_RF', 34, 44)]; unexpected=[]
- `v6-pos-division-019`: missing=[('DIVISION_CODE', 14, 21)]; unexpected=[]
- `v6-pos-birth-022`: missing=[('BIRTH_DATE', 25, 35)]; unexpected=[]
- `v6-pos-birth-023`: missing=[('BIRTH_DATE', 15, 24)]; unexpected=[]
- `v6-pos-birthplace-024`: missing=[('PLACE_OF_BIRTH', 25, 60)]; unexpected=[]
- `v6-pos-citizenship-027`: missing=[('CITIZENSHIP', 33, 51)]; unexpected=[]
- `v6-pos-issuer-028`: missing=[('PASSPORT_ISSUER', 22, 56)]; unexpected=[]
- `v6-pos-issuer-029`: missing=[('PASSPORT_ISSUER', 17, 48)]; unexpected=[]
- `v6-pos-license-032`: missing=[('DRIVER_LICENSE_RF', 31, 43)]; unexpected=[]
- `v6-pos-address-035`: missing=[('ADDRESS_APARTMENT', 86, 87), ('ADDRESS_CITY', 35, 46), ('ADDRESS_COUNTRY', 19, 25), ('ADDRESS_HOUSE', 72, 75), ('ADDRESS_POSTAL_CODE', 27, 33), ('ADDRESS_STREET', 48, 57)]; unexpected=[]
- `v6-pos-address-036`: missing=[('ADDRESS_APARTMENT', 55, 58), ('ADDRESS_CITY', 12, 19), ('ADDRESS_HOUSE', 43, 44), ('ADDRESS_STREET', 30, 37)]; unexpected=[]
- `v6-pos-cvv-037`: missing=[('CVV', 33, 36)]; unexpected=[]
- `v6-pos-pin-038`: missing=[('PIN', 26, 30)]; unexpected=[]
- `v6-pos-cardholder-039`: missing=[('CARDHOLDER_NAME', 31, 45)]; unexpected=[]
- `v6-pos-multi-041`: missing=[('PASSPORT_ISSUE_DATE', 54, 64)]; unexpected=[]
- `v6-pos-multi-042`: missing=[('CARDHOLDER_NAME', 62, 75)]; unexpected=[]
- `v6-pos-multi-044`: missing=[('PLACE_OF_BIRTH', 32, 47)]; unexpected=[]
- `v6-pos-multi-046`: missing=[('ADDRESS_APARTMENT', 72, 74), ('ADDRESS_CITY', 32, 39), ('ADDRESS_HOUSE', 64, 66), ('ADDRESS_POSTAL_CODE', 24, 30), ('ADDRESS_STREET', 47, 58)]; unexpected=[]
- `v6-pos-multi-047`: missing=[('PERSON', 24, 46)]; unexpected=[]
- `v6-neg-phone-company-056`: missing=[]; unexpected=[('PHONE_RF', 26, 44)]
- `v6-neg-phone-museum-058`: missing=[]; unexpected=[('PHONE_RF', 33, 49)]
- `v6-neg-email-events-061`: missing=[]; unexpected=[('EMAIL', 36, 56)]
- `v6-neg-invalid-phone-073`: missing=[]; unexpected=[('PHONE_RF', 7, 23)]
- `v6-neg-shape-passport-075`: missing=[]; unexpected=[('PASSPORT_RF', 22, 34)]
- `v6-neg-shape-cvv-079`: missing=[]; unexpected=[('CVV', 19, 22)]
- `v6-neg-template-084`: missing=[]; unexpected=[('PLACE_OF_BIRTH', 27, 61)]
- `v6-neg-multi-public-085`: missing=[]; unexpected=[('ADDRESS_HOUSE', 113, 114), ('EMAIL', 49, 72), ('PHONE_RF', 23, 41)]
- `v6-neg-multi-catalog-087`: missing=[]; unexpected=[('DIVISION_CODE', 64, 71), ('PASSPORT_RF', 34, 45)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
