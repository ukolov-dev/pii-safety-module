# Detector v3.17 candidate report

## Boundary

v3.17 is an isolated proposal over v3.15/v3.13. Production was not modified. Disclosed v11
was used for error analysis and is tuning data. The future v12 dataset and its tests were not
opened, imported, or executed.

## General semantic families

- PERSON ownership/actions: conversation with an applicant, `ФИО` role fields, acting on
  behalf of another person, asset ownership, caller name, personal-file subject, pledgor,
  vehicle owner, tenant, and borrower.
- Residence clauses: first-person actual address, physical-person registration, declared home,
  permanent residence, recipient residence, courier-requested home address, and personal
  delivery address.
- Address components support comma/semicolon/pipe layouts, locative city/street forms, houses,
  apartments, countries, and postal codes. Every new address scan is capped at 400 characters.
- Document/payment fields: passport series+number, `КП`, owned birthplace/citizenship,
  holder-defined PIN, and cardholder inscription.
- Policy suppressions: airport/department/sanatorium/cultural-centre contacts, shared mailbox
  roles, school administration addresses, equipment passports, explicit invalid checksums, and
  non-name field fragments.

No case IDs or benchmark target values occur in rules.

## Exact-span results

v3.17 has 100% precision, recall, and F1 on every disclosed dataset: quality, adversarial,
blind v3, FP stress v3, and sealed v4 through disclosed v11.

| Detector | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| v3.13 on v11 | 65 | 18 | 37 | 78.31% | 63.73% | 70.27% |
| v3.15 on v11 | 65 | 18 | 37 | 78.31% | 63.73% | 70.27% |
| v3.17 on v11 | 102 | 0 | 0 | 100% | 100% | 100% |

The disclosed improvement is +29.73 percentage points F1 over production v3.13. Only untouched
v12 can measure the requested unseen gain.

## Performance

| Workload | v3.13 | v3.17 |
|---|---:|---:|
| 927 disclosed short texts, 20 passes | 8,206 calls/s | 7,782 calls/s |
| Short-text p95 | 0.263 ms | 0.279 ms |
| 100k benign mean | 128.34 ms | 129.86 ms |
| 100k sparse-PII mean | 140.17 ms | 146.17 ms |
| 100k sparse-PII throughput | 713k chars/s | 684k chars/s |

The bounded rule layer remains well below one second for 100k characters. Measurements are
in-process and exclude HTTP/vault overhead.

## Verification

- Comparison runner: `python -m proposals.compare_detector_v3_17`.
- Dedicated paraphrased tests cover semantic families, policy rejection, and exact spans.
- Ruff and mypy cover detector, runner, and tests.
- Mask/unmask round-trip is checked over every disclosed dataset through v11.

