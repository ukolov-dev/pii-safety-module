# Quality benchmark: ru_pii_quality_v1

Dataset version: `1`; cases: **30**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 100.00% |
| Recall | 54.84% |
| F1 | 70.83% |
| Exact masks | 16/30 (53.33%) |
| Exact round trips | 30/30 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_CITY | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_COUNTRY | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_HOUSE | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_POSTAL_CODE | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| ADDRESS_STREET | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| BANK_CARD | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| CITIZENSHIP | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| CVV | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DRIVER_LICENSE_RF | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| EMAIL | 3 | 0 | 1 | 100.00% | 75.00% | 85.71% |
| INN | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |
| PASSPORT_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PERSON | 2 | 0 | 1 | 100.00% | 66.67% | 80.00% |
| PHONE_RF | 2 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PIN | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 0 | 0 | 1 | 0.00% | 0.00% | 0.00% |

## Cases with a non-exact mask

- `person-uppercase`: missing=[('PERSON', 12, 23)]; unexpected=[]
- `repeated-email`: missing=[('EMAIL', 40, 56)]; unexpected=[]
- `place-of-birth`: missing=[('PLACE_OF_BIRTH', 16, 28)]; unexpected=[]
- `citizenship`: missing=[('CITIZENSHIP', 13, 33)]; unexpected=[]
- `passport-issuer`: missing=[('PASSPORT_ISSUER', 14, 41)]; unexpected=[]
- `passport-issue-date`: missing=[('PASSPORT_ISSUE_DATE', 22, 32)]; unexpected=[]
- `driver-license`: missing=[('DRIVER_LICENSE_RF', 28, 40)]; unexpected=[]
- `address-country`: missing=[('ADDRESS_COUNTRY', 19, 25)]; unexpected=[]
- `address-postal-code`: missing=[('ADDRESS_POSTAL_CODE', 25, 31)]; unexpected=[]
- `address-city`: missing=[('ADDRESS_CITY', 18, 24)]; unexpected=[]
- `address-street`: missing=[('ADDRESS_STREET', 18, 26)]; unexpected=[]
- `address-house`: missing=[('ADDRESS_HOUSE', 13, 16)]; unexpected=[]
- `address-apartment`: missing=[('ADDRESS_APARTMENT', 18, 20)]; unexpected=[]
- `cardholder`: missing=[('CARDHOLDER_NAME', 21, 32)]; unexpected=[]

## Sources

- `../database/chunks/CH-SRC-001-05.md`
- `../database/chunks/CH-SRC-001-06.md`
- `../database/chunks/CH-SRC-001-07.md`
