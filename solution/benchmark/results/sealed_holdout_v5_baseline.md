# Quality benchmark: ru_pii_sealed_holdout_v5

Dataset version: `5`; cases: **68**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 89.47% |
| Recall | 44.74% |
| F1 | 59.65% |
| Exact masks | 37/68 (54.41%) |
| Exact round trips | 68/68 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| ADDRESS_CITY | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| ADDRESS_COUNTRY | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| ADDRESS_POSTAL_CODE | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| ADDRESS_STREET | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| BANK_CARD | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| BIRTH_DATE | 2 | 0 | 4 | 100.00% | 33.33% | 50.00% |
| CARDHOLDER_NAME | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 1 | 1 | 1 | 50.00% | 50.00% | 50.00% |
| DIVISION_CODE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| DRIVER_LICENSE_RF | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| EMAIL | 6 | 1 | 0 | 85.71% | 100.00% | 92.31% |
| INN | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_RF | 2 | 1 | 2 | 66.67% | 50.00% | 57.14% |
| PERSON | 5 | 0 | 4 | 100.00% | 55.56% | 71.43% |
| PHONE_RF | 8 | 1 | 0 | 88.89% | 100.00% | 94.12% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |

## Cases with a non-exact mask

- `v5-person-contract-02`: missing=[('PERSON', 19, 48)]; unexpected=[]
- `v5-person-uppercase-03`: missing=[('PERSON', 21, 46)]; unexpected=[]
- `v5-person-hyphen-04`: missing=[('PERSON', 20, 50)]; unexpected=[]
- `v5-card-form-01`: missing=[('BANK_CARD', 19, 38)]; unexpected=[]
- `v5-passport-form-02`: missing=[('PASSPORT_RF', 0, 37)]; unexpected=[]
- `v5-passport-prose-03`: missing=[('PASSPORT_RF', 39, 49)]; unexpected=[]
- `v5-division-form-01`: missing=[('DIVISION_CODE', 20, 27)]; unexpected=[]
- `v5-birth-form-01`: missing=[('BIRTH_DATE', 26, 36)]; unexpected=[]
- `v5-birth-form-02`: missing=[('BIRTH_DATE', 11, 21)]; unexpected=[]
- `v5-birth-prose-03`: missing=[('BIRTH_DATE', 25, 45)]; unexpected=[]
- `v5-birth-shortyear-04`: missing=[('BIRTH_DATE', 24, 32)]; unexpected=[]
- `v5-birthplace-form-01`: missing=[('PLACE_OF_BIRTH', 27, 44)]; unexpected=[]
- `v5-birthplace-prose-02`: missing=[('PLACE_OF_BIRTH', 38, 71)]; unexpected=[]
- `v5-citizenship-prose-02`: missing=[('CITIZENSHIP', 29, 50)]; unexpected=[]
- `v5-issuer-form-01`: missing=[('PASSPORT_ISSUER', 14, 58)]; unexpected=[]
- `v5-issuer-form-02`: missing=[('PASSPORT_ISSUER', 20, 50)]; unexpected=[]
- `v5-issuedate-form-01`: missing=[('PASSPORT_ISSUE_DATE', 26, 36)]; unexpected=[]
- `v5-issuedate-prose-02`: missing=[('PASSPORT_ISSUE_DATE', 26, 51)]; unexpected=[]
- `v5-license-form-01`: missing=[('DRIVER_LICENSE_RF', 30, 42)]; unexpected=[]
- `v5-license-prose-02`: missing=[('DRIVER_LICENSE_RF', 31, 45)]; unexpected=[('PASSPORT_RF', 25, 45)]
- `v5-address-form-01`: missing=[('ADDRESS_APARTMENT', 84, 86), ('ADDRESS_CITY', 38, 41), ('ADDRESS_COUNTRY', 16, 22), ('ADDRESS_HOUSE', 71, 73), ('ADDRESS_POSTAL_CODE', 24, 30), ('ADDRESS_STREET', 49, 65)]; unexpected=[]
- `v5-address-form-02`: missing=[('ADDRESS_APARTMENT', 66, 69), ('ADDRESS_CITY', 30, 39), ('ADDRESS_HOUSE', 58, 60), ('ADDRESS_POSTAL_CODE', 19, 25), ('ADDRESS_STREET', 45, 53)]; unexpected=[]
- `v5-address-prose-03`: missing=[('ADDRESS_APARTMENT', 68, 70), ('ADDRESS_CITY', 19, 25), ('ADDRESS_HOUSE', 55, 57), ('ADDRESS_STREET', 36, 46)]; unexpected=[]
- `v5-cvv-form-01`: missing=[('CVV', 23, 26)]; unexpected=[]
- `v5-cardholder-form-01`: missing=[('CARDHOLDER_NAME', 15, 32)]; unexpected=[]
- `v5-multi-payment-02`: missing=[('CARDHOLDER_NAME', 71, 84)]; unexpected=[]
- `v5-multi-passport-03`: missing=[('DIVISION_CODE', 70, 77), ('PASSPORT_ISSUER', 27, 53), ('PASSPORT_ISSUE_DATE', 54, 64)]; unexpected=[]
- `v5-multi-free-text-08`: missing=[('PERSON', 11, 33)]; unexpected=[]
- `v5-negative-company-phone-04`: missing=[]; unexpected=[('PHONE_RF', 21, 37)]
- `v5-negative-shared-email-06`: missing=[]; unexpected=[('EMAIL', 36, 60)]
- `v5-negative-cvv-shape-19`: missing=[]; unexpected=[('CVV', 20, 23)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
