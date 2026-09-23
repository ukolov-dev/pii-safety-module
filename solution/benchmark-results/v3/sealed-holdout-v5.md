# Quality benchmark: ru_pii_sealed_holdout_v5

Dataset version: `5`; cases: **68**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 91.07% |
| Recall | 67.11% |
| F1 | 77.27% |
| Exact masks | 45/68 (66.18%) |
| Exact round trips | 68/68 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| ADDRESS_CITY | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| ADDRESS_COUNTRY | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| ADDRESS_POSTAL_CODE | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| ADDRESS_STREET | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| BANK_CARD | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| BIRTH_DATE | 5 | 0 | 1 | 100.00% | 83.33% | 90.91% |
| CARDHOLDER_NAME | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 2 | 1 | 0 | 66.67% | 100.00% | 80.00% |
| DIVISION_CODE | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| DRIVER_LICENSE_RF | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| EMAIL | 6 | 1 | 0 | 85.71% | 100.00% | 92.31% |
| INN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_ISSUE_DATE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| PASSPORT_RF | 2 | 1 | 2 | 66.67% | 50.00% | 57.14% |
| PERSON | 6 | 0 | 3 | 100.00% | 66.67% | 80.00% |
| PHONE_RF | 8 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 1 | 2 | 2 | 33.33% | 33.33% | 33.33% |

## Cases with a non-exact mask

- `v5-person-contract-02`: missing=[('PERSON', 19, 48)]; unexpected=[]
- `v5-person-uppercase-03`: missing=[('PERSON', 21, 46)]; unexpected=[]
- `v5-person-hyphen-04`: missing=[('PERSON', 20, 50)]; unexpected=[]
- `v5-card-form-01`: missing=[('BANK_CARD', 19, 38)]; unexpected=[]
- `v5-passport-form-02`: missing=[('PASSPORT_RF', 0, 37)]; unexpected=[]
- `v5-passport-prose-03`: missing=[('PASSPORT_RF', 39, 49)]; unexpected=[]
- `v5-division-form-01`: missing=[('DIVISION_CODE', 20, 27)]; unexpected=[]
- `v5-birth-prose-03`: missing=[('BIRTH_DATE', 25, 45)]; unexpected=[]
- `v5-birthplace-form-01`: missing=[('PLACE_OF_BIRTH', 27, 44)]; unexpected=[]
- `v5-issuer-form-01`: missing=[('PASSPORT_ISSUER', 14, 58)]; unexpected=[]
- `v5-issuer-form-02`: missing=[('PASSPORT_ISSUER', 20, 50)]; unexpected=[]
- `v5-issuedate-form-01`: missing=[('PASSPORT_ISSUE_DATE', 26, 36)]; unexpected=[]
- `v5-license-form-01`: missing=[('DRIVER_LICENSE_RF', 30, 42)]; unexpected=[]
- `v5-license-prose-02`: missing=[('DRIVER_LICENSE_RF', 31, 45)]; unexpected=[('PASSPORT_RF', 25, 45)]
- `v5-address-form-01`: missing=[('ADDRESS_COUNTRY', 16, 22), ('ADDRESS_POSTAL_CODE', 24, 30)]; unexpected=[]
- `v5-address-form-02`: missing=[('ADDRESS_POSTAL_CODE', 19, 25)]; unexpected=[]
- `v5-address-prose-03`: missing=[('ADDRESS_APARTMENT', 68, 70), ('ADDRESS_CITY', 19, 25), ('ADDRESS_HOUSE', 55, 57), ('ADDRESS_STREET', 36, 46)]; unexpected=[]
- `v5-cardholder-form-01`: missing=[('CARDHOLDER_NAME', 15, 32)]; unexpected=[]
- `v5-multi-passport-03`: missing=[('PASSPORT_ISSUE_DATE', 54, 64)]; unexpected=[]
- `v5-multi-biography-05`: missing=[('CITIZENSHIP', 90, 96), ('PLACE_OF_BIRTH', 66, 76)]; unexpected=[('PLACE_OF_BIRTH', 66, 96)]
- `v5-negative-shared-email-06`: missing=[]; unexpected=[('EMAIL', 36, 60)]
- `v5-negative-cvv-shape-19`: missing=[]; unexpected=[('CVV', 20, 23)]
- `v5-negative-org-citizenship-20`: missing=[]; unexpected=[('PLACE_OF_BIRTH', 68, 69)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
