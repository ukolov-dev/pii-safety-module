# Sealed blind holdout v18 comparison

Dataset: `sealed_holdout_v18.json`; SHA-256: `6aee9db0f07b050d8be1a7587f1f5eee04f1be37f604765c5389eede06cd7b8a`; cases: **336**; gold entities: **1776**.

## Overall

| Candidate | TP | FP | FN | Precision | Recall | F1 | Exact mask | Round-trip |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v326 | 1171 | 136 | 605 | 89.59% | 65.93% | 75.96% | 91/336 (27.08%) | 336/336 (100.00%) |
| v328 | 1151 | 136 | 625 | 89.43% | 64.81% | 75.16% | 107/336 (31.85%) | 336/336 (100.00%) |

## v326 by category

| Category | TP | FP | FN | P | R | F1 | Exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| address_contact | 384 | 0 | 48 | 100.00% | 88.89% | 94.12% | 0/48 |
| clean_public_technical | 0 | 16 | 0 | 0.00% | 100.00% | 0.00% | 32/48 |
| identity_document | 204 | 120 | 228 | 62.96% | 47.22% | 53.97% | 0/48 |
| ocr_unicode | 44 | 0 | 196 | 100.00% | 18.33% | 30.99% | 0/48 |
| payment_bundle | 192 | 0 | 0 | 100.00% | 100.00% | 100.00% | 48/48 |
| record_boundaries | 192 | 0 | 96 | 100.00% | 66.67% | 80.00% | 0/48 |
| reordered_dates | 155 | 0 | 37 | 100.00% | 80.73% | 89.34% | 11/48 |

### v326 error reasons

| Reason | Count |
|---|---:|
| boundary_mismatch | 84 |
| pure_false_negative | 485 |
| pure_false_positive | 16 |
| wrong_type_same_span | 36 |

### v326 by entity type

| Type | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 96 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 0 | 8 | 96 | 0.00% | 0.00% | 0.00% |
| DRIVER_LICENSE_RF | 48 | 36 | 0 | 57.14% | 100.00% | 72.73% |
| EMAIL | 144 | 0 | 48 | 100.00% | 75.00% | 85.71% |
| INN | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PASSPORT_ISSUER | 0 | 36 | 48 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 11 | 0 | 85 | 100.00% | 11.46% | 20.56% |
| PASSPORT_RF | 60 | 0 | 84 | 100.00% | 41.67% | 58.82% |
| PERSON | 236 | 0 | 4 | 100.00% | 98.33% | 99.16% |
| PHONE_RF | 0 | 8 | 192 | 0.00% | 0.00% | 0.00% |
| PIN | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 0 | 48 | 48 | 0.00% | 0.00% | 0.00% |

## v328 by category

| Category | TP | FP | FN | P | R | F1 | Exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| address_contact | 376 | 0 | 56 | 100.00% | 87.04% | 93.07% | 0/48 |
| clean_public_technical | 0 | 16 | 0 | 0.00% | 100.00% | 0.00% | 32/48 |
| identity_document | 204 | 120 | 228 | 62.96% | 47.22% | 53.97% | 0/48 |
| ocr_unicode | 40 | 0 | 200 | 100.00% | 16.67% | 28.57% | 0/48 |
| payment_bundle | 192 | 0 | 0 | 100.00% | 100.00% | 100.00% | 48/48 |
| record_boundaries | 168 | 0 | 120 | 100.00% | 58.33% | 73.68% | 0/48 |
| reordered_dates | 171 | 0 | 21 | 100.00% | 89.06% | 94.21% | 27/48 |

### v328 error reasons

| Reason | Count |
|---|---:|
| boundary_mismatch | 84 |
| pure_false_negative | 505 |
| pure_false_positive | 16 |
| wrong_type_same_span | 36 |

### v328 by entity type

| Type | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_APARTMENT | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_CITY | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_COUNTRY | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_HOUSE | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_POSTAL_CODE | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| ADDRESS_STREET | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BANK_CARD | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| BIRTH_DATE | 96 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CARDHOLDER_NAME | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CITIZENSHIP | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| CVV | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| DIVISION_CODE | 0 | 8 | 96 | 0.00% | 0.00% | 0.00% |
| DRIVER_LICENSE_RF | 48 | 36 | 0 | 57.14% | 100.00% | 72.73% |
| EMAIL | 144 | 0 | 48 | 100.00% | 75.00% | 85.71% |
| INN | 40 | 0 | 8 | 100.00% | 83.33% | 90.91% |
| PASSPORT_ISSUER | 0 | 36 | 48 | 0.00% | 0.00% | 0.00% |
| PASSPORT_ISSUE_DATE | 27 | 0 | 69 | 100.00% | 28.12% | 43.90% |
| PASSPORT_RF | 60 | 0 | 84 | 100.00% | 41.67% | 58.82% |
| PERSON | 208 | 0 | 32 | 100.00% | 86.67% | 92.86% |
| PHONE_RF | 0 | 8 | 192 | 0.00% | 0.00% | 0.00% |
| PIN | 48 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| PLACE_OF_BIRTH | 0 | 48 | 48 | 0.00% | 0.00% | 0.00% |
