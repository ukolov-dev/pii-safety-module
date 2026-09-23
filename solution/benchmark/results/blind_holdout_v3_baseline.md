# Quality benchmark: ru_pii_blind_holdout_v3

Dataset version: `3`; cases: **60**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 78.12% |
| Recall | 38.46% |
| F1 | 51.55% |
| Exact masks | 29/60 (48.33%) |
| Exact round trips | 60/60 (100.00%) |

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
| BIRTH_DATE | 1 | 0 | 3 | 100.00% | 25.00% | 40.00% |
| CARDHOLDER_NAME | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| CVV | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 1 | 0 | 2 | 100.00% | 33.33% | 50.00% |
| DRIVER_LICENSE_RF | 0 | 0 | 2 | 0.00% | 0.00% | 0.00% |
| EMAIL | 6 | 3 | 1 | 66.67% | 85.71% | 75.00% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 0 | 0 | 3 | 0.00% | 0.00% | 0.00% |
| PASSPORT_RF | 2 | 1 | 2 | 66.67% | 50.00% | 57.14% |
| PERSON | 2 | 0 | 3 | 100.00% | 40.00% | 57.14% |
| PHONE_RF | 6 | 1 | 0 | 85.71% | 100.00% | 92.31% |
| PIN | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PLACE_OF_BIRTH | 1 | 1 | 1 | 50.00% | 50.00% | 50.00% |

## Cases with a non-exact mask

- `blind-person-dative-label`: missing=[('PERSON', 30, 58)]; unexpected=[]
- `blind-person-mixed-case`: missing=[('PERSON', 13, 34)]; unexpected=[]
- `blind-person-hyphen`: missing=[('PERSON', 13, 42)]; unexpected=[]
- `blind-email-short-label`: missing=[('EMAIL', 7, 30)]; unexpected=[('EMAIL', 0, 30)]
- `blind-passport-words`: missing=[('PASSPORT_RF', 10, 35)]; unexpected=[]
- `blind-passport-nospace`: missing=[('PASSPORT_RF', 28, 38)]; unexpected=[]
- `blind-division-slash`: missing=[('DIVISION_CODE', 23, 30)]; unexpected=[]
- `blind-division-hyphen`: missing=[('DIVISION_CODE', 4, 11)]; unexpected=[]
- `blind-birth-date-slashes`: missing=[('BIRTH_DATE', 26, 36)]; unexpected=[]
- `blind-birth-date-iso`: missing=[('BIRTH_DATE', 8, 18)]; unexpected=[('PLACE_OF_BIRTH', 35, 47)]
- `blind-birth-date-text-case`: missing=[('BIRTH_DATE', 31, 49)]; unexpected=[]
- `blind-place-city-abbrev`: missing=[('PLACE_OF_BIRTH', 11, 28)]; unexpected=[]
- `blind-citizenship-short`: missing=[('CITIZENSHIP', 24, 26)]; unexpected=[]
- `blind-citizenship-foreign`: missing=[('CITIZENSHIP', 12, 31)]; unexpected=[]
- `blind-issuer-mvd`: missing=[('PASSPORT_ISSUER', 11, 46)]; unexpected=[]
- `blind-issuer-ovd`: missing=[('PASSPORT_ISSUER', 15, 65)]; unexpected=[]
- `blind-issue-date-slash`: missing=[('PASSPORT_ISSUE_DATE', 14, 24)]; unexpected=[]
- `blind-issue-date-text`: missing=[('PASSPORT_ISSUE_DATE', 24, 41)]; unexpected=[]
- `blind-driver-hyphen`: missing=[('DRIVER_LICENSE_RF', 14, 26)]; unexpected=[]
- `blind-driver-series-number`: missing=[('DRIVER_LICENSE_RF', 30, 44)]; unexpected=[('PASSPORT_RF', 24, 44)]
- `blind-address-one-line-abbrev`: missing=[('ADDRESS_APARTMENT', 68, 70), ('ADDRESS_CITY', 29, 41), ('ADDRESS_HOUSE', 60, 62), ('ADDRESS_POSTAL_CODE', 18, 24), ('ADDRESS_STREET', 47, 55)]; unexpected=[]
- `blind-address-one-line-full`: missing=[('ADDRESS_APARTMENT', 83, 84), ('ADDRESS_CITY', 40, 46), ('ADDRESS_COUNTRY', 18, 24), ('ADDRESS_HOUSE', 69, 72), ('ADDRESS_POSTAL_CODE', 26, 32), ('ADDRESS_STREET', 57, 63)]; unexpected=[]
- `blind-address-building`: missing=[('ADDRESS_APARTMENT', 63, 65), ('ADDRESS_CITY', 16, 21), ('ADDRESS_HOUSE', 45, 48), ('ADDRESS_STREET', 29, 40)]; unexpected=[]
- `blind-card-cvv-combined`: missing=[('CARDHOLDER_NAME', 48, 60)]; unexpected=[]
- `blind-pin-context`: missing=[('PIN', 20, 24)]; unexpected=[]
- `blind-cardholder-slash`: missing=[('CARDHOLDER_NAME', 14, 27)]; unexpected=[]
- `blind-multi-passport`: missing=[('PASSPORT_ISSUER', 28, 54), ('PASSPORT_ISSUE_DATE', 55, 65)]; unexpected=[]
- `blind-negative-corporate-phone`: missing=[]; unexpected=[('PHONE_RF', 27, 45)]
- `blind-negative-shared-sales-email`: missing=[]; unexpected=[('EMAIL', 40, 56)]
- `blind-negative-press-email`: missing=[]; unexpected=[('EMAIL', 23, 45)]
- `blind-negative-public-card-example`: missing=[]; unexpected=[('BANK_CARD', 56, 75)]

## Sources

- `../../database/chunks/CH-SRC-001-05.md`
- `../../database/chunks/CH-SRC-001-06.md`
- `../../database/chunks/CH-SRC-001-07.md`
