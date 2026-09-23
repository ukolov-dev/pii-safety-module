# Quality benchmark: ru_pii_sealed_holdout_v4

Dataset version: `4`; cases: **56**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 84.85% |
| Recall | 43.08% |
| F1 | 57.14% |
| Exact masks | 29/56 (51.79%) |
| Exact round trips | 56/56 (100.00%) |

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
| BANK_CARD | 3 | 1 | 0 | 75.00% | 100.00% | 85.71% |
| BIRTH_DATE | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| CARDHOLDER_NAME | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| CVV | 1 | 0 | 1 | 100.00% | 50.00% | 66.67% |
| DIVISION_CODE | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| DRIVER_LICENSE_RF | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| EMAIL | 6 | 2 | 0 | 75.00% | 100.00% | 85.71% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_RF | 3 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 3 | 0 | 4 | 100.00% | 42.86% | 60.00% |
| PHONE_RF | 4 | 1 | 0 | 80.00% | 100.00% | 88.89% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 0 | 1 | 3 | 0.00% | 0.00% | 0.00% |

## Cases with a non-exact mask

- `sealed-prose-person-02`: missing=[('PERSON', 21, 49)]; unexpected=[]
- `sealed-prose-person-04`: missing=[('PERSON', 14, 42)]; unexpected=[]
- `sealed-form-division-01`: missing=[('DIVISION_CODE', 29, 36)]; unexpected=[]
- `sealed-prose-birth-02`: missing=[('BIRTH_DATE', 24, 55)]; unexpected=[]
- `sealed-form-birthplace-01`: missing=[('PLACE_OF_BIRTH', 16, 49)]; unexpected=[('PLACE_OF_BIRTH', 16, 19)]
- `sealed-prose-birthplace-02`: missing=[('PLACE_OF_BIRTH', 35, 67)]; unexpected=[]
- `sealed-prose-citizenship-02`: missing=[('CITIZENSHIP', 31, 51)]; unexpected=[]
- `sealed-form-issuer-01`: missing=[('PASSPORT_ISSUER', 25, 57)]; unexpected=[]
- `sealed-prose-issuer-02`: missing=[('PASSPORT_ISSUER', 35, 67)]; unexpected=[]
- `sealed-form-issue-date-01`: missing=[('PASSPORT_ISSUE_DATE', 21, 31)]; unexpected=[]
- `sealed-prose-issue-date-02`: missing=[('PASSPORT_ISSUE_DATE', 31, 47)]; unexpected=[]
- `sealed-form-license-01`: missing=[('DRIVER_LICENSE_RF', 20, 32)]; unexpected=[]
- `sealed-prose-license-02`: missing=[('DRIVER_LICENSE_RF', 35, 46)]; unexpected=[]
- `sealed-form-address-01`: missing=[('ADDRESS_APARTMENT', 88, 90), ('ADDRESS_CITY', 37, 51), ('ADDRESS_COUNTRY', 15, 21), ('ADDRESS_HOUSE', 75, 77), ('ADDRESS_POSTAL_CODE', 23, 29), ('ADDRESS_STREET', 59, 69)]; unexpected=[]
- `sealed-form-address-02`: missing=[('ADDRESS_APARTMENT', 83, 86), ('ADDRESS_CITY', 40, 51), ('ADDRESS_HOUSE', 74, 77), ('ADDRESS_POSTAL_CODE', 29, 35), ('ADDRESS_STREET', 53, 60)]; unexpected=[]
- `sealed-prose-address-03`: missing=[('ADDRESS_APARTMENT', 59, 60), ('ADDRESS_CITY', 16, 19), ('ADDRESS_HOUSE', 45, 48), ('ADDRESS_STREET', 29, 39)]; unexpected=[]
- `sealed-form-cvv-01`: missing=[('CVV', 31, 34)]; unexpected=[]
- `sealed-form-cardholder-01`: missing=[('CARDHOLDER_NAME', 13, 31)]; unexpected=[]
- `sealed-multi-contact-01`: missing=[('PERSON', 8, 28)]; unexpected=[]
- `sealed-multi-document-02`: missing=[('DIVISION_CODE', 39, 46), ('PASSPORT_ISSUER', 54, 89), ('PASSPORT_ISSUE_DATE', 90, 100)]; unexpected=[]
- `sealed-multi-payment-03`: missing=[('CARDHOLDER_NAME', 67, 79)]; unexpected=[]
- `sealed-multi-biography-04`: missing=[('PLACE_OF_BIRTH', 44, 57)]; unexpected=[]
- `sealed-multi-loose-prose-06`: missing=[('PERSON', 38, 62)]; unexpected=[]
- `sealed-negative-reception-04`: missing=[]; unexpected=[('PHONE_RF', 40, 58)]
- `sealed-negative-mailbox-05`: missing=[]; unexpected=[('EMAIL', 35, 57)]
- `sealed-negative-mailbox-06`: missing=[]; unexpected=[('EMAIL', 31, 53)]
- `sealed-negative-test-payment-15`: missing=[]; unexpected=[('BANK_CARD', 51, 70)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
