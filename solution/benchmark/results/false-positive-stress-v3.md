# Quality benchmark: ru_pii_false_positive_stress_v3

Dataset version: `3`; cases: **64**.

## Summary

| Metric | Result |
|---|---:|
| Precision | 25.00% |
| Recall | 92.31% |
| F1 | 39.34% |
| Exact masks | 29/64 (45.31%) |
| Exact round trips | 64/64 (100.00%) |

Detection uses exact `(type, start, end)` matching. Exact-mask rate compares the full
generated string with a mask built from gold spans. Round trip verifies that the actual
detected-and-masked string restores byte-for-byte to the input.

## Metrics by type

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 1 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 1 | 3 | 0 | 25.00% | 100.00% | 40.00% |
| BIRTH_DATE | 0 | 1 | 1 | 0.00% | 0.00% | 0.00% |
| CVV | 0 | 1 | 0 | 0.00% | 0.00% | 0.00% |
| DIVISION_CODE | 0 | 1 | 0 | 0.00% | 0.00% | 0.00% |
| EMAIL | 1 | 10 | 0 | 9.09% | 100.00% | 16.67% |
| INN | 1 | 4 | 0 | 20.00% | 100.00% | 33.33% |
| PASSPORT_RF | 1 | 2 | 0 | 33.33% | 100.00% | 50.00% |
| PERSON | 1 | 6 | 0 | 14.29% | 100.00% | 25.00% |
| PHONE_RF | 1 | 7 | 0 | 12.50% | 100.00% | 22.22% |
| PIN | 0 | 1 | 0 | 0.00% | 0.00% | 0.00% |

## Cases with a non-exact mask

- `neg-public-phone-office`: missing=[]; unexpected=[('PHONE_RF', 22, 40)]
- `neg-public-phone-reception`: missing=[]; unexpected=[('PHONE_RF', 23, 39)]
- `neg-public-phone-courier-service`: missing=[]; unexpected=[('PHONE_RF', 43, 60)]
- `neg-public-phone-museum`: missing=[]; unexpected=[('PHONE_RF', 18, 34)]
- `neg-public-email-info`: missing=[]; unexpected=[('EMAIL', 31, 46)]
- `neg-public-email-sales`: missing=[]; unexpected=[('EMAIL', 24, 42)]
- `neg-public-email-press`: missing=[]; unexpected=[('EMAIL', 14, 34)]
- `neg-public-email-jobs`: missing=[]; unexpected=[('EMAIL', 22, 42)]
- `neg-public-email-security`: missing=[]; unexpected=[('EMAIL', 40, 60)]
- `neg-org-inn-bank`: missing=[]; unexpected=[('INN', 31, 41)]
- `neg-org-inn-contractor`: missing=[]; unexpected=[('INN', 34, 46)]
- `neg-org-card-test`: missing=[]; unexpected=[('BANK_CARD', 58, 77)]
- `neg-org-card-token-doc`: missing=[]; unexpected=[('BANK_CARD', 26, 45)]
- `neg-ticket-number`: missing=[]; unexpected=[('PHONE_RF', 10, 21)]
- `neg-build-number`: missing=[]; unexpected=[('BANK_CARD', 13, 29)]
- `neg-version-number`: missing=[]; unexpected=[('INN', 29, 41)]
- `neg-famous-pushkin`: missing=[]; unexpected=[('PERSON', 0, 26)]
- `neg-famous-tolstoy`: missing=[]; unexpected=[('PERSON', 21, 43)]
- `neg-famous-gagarin`: missing=[]; unexpected=[('PERSON', 0, 23)]
- `neg-famous-mendeleev`: missing=[]; unexpected=[('PERSON', 0, 26)]
- `neg-fictional-character`: missing=[]; unexpected=[('PERSON', 0, 20)]
- `neg-author-bibliography`: missing=[]; unexpected=[('PERSON', 14, 41)]
- `neg-doc-passport-instruction`: missing=[]; unexpected=[('PASSPORT_RF', 26, 38)]
- `neg-doc-passport-labels`: missing=[]; unexpected=[('PASSPORT_RF', 19, 44)]
- `neg-doc-division-code`: missing=[]; unexpected=[('DIVISION_CODE', 35, 42)]
- `neg-doc-birth-date`: missing=[]; unexpected=[('BIRTH_DATE', 31, 41)]
- `neg-doc-cvv`: missing=[]; unexpected=[('CVV', 30, 33)]
- `neg-doc-pin`: missing=[]; unexpected=[('PIN', 33, 37)]
- `neg-placeholder-email-angle`: missing=[]; unexpected=[('EMAIL', 19, 35)]
- `neg-placeholder-phone-digits`: missing=[]; unexpected=[('PHONE_RF', 15, 33)]
- `neg-code-comment-email`: missing=[]; unexpected=[('EMAIL', 18, 39)]
- `neg-sql-fixture`: missing=[]; unexpected=[('EMAIL', 33, 50)]
- `neg-log-local-email`: missing=[]; unexpected=[('EMAIL', 6, 35)]
- `neg-multiple-public-values`: missing=[]; unexpected=[('EMAIL', 37, 54), ('INN', 60, 70), ('PHONE_RF', 19, 35)]
- `positive-real-birth-date`: missing=[('BIRTH_DATE', 23, 33)]; unexpected=[]

## Sources

- `Synthetic stress cases designed to measure over-masking; no production personal data.`
