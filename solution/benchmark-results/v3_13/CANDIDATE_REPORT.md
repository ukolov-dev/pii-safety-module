# Detector v3.13 candidate report

## Evaluation boundary

v3.13 is an isolated lightweight proposal layered on v3.11; production was not modified. The
v9 holdout was disclosed before this iteration and is therefore tuning/regression data. The
future v10 dataset and its tests were not opened, imported, or executed.

## Architecture and privacy/utility decision

The public detector API remains `detect(text) -> list[DetectedEntity]`, but the candidate now
has two explicit internal stages:

1. `detect_candidates` finds inherited rule/checksum entities and strongly labelled new
   candidates, recording evidence and ownership metadata.
2. `should_mask` makes the independent privacy/utility decision, rejecting public, shared,
   template, documentation, device, and organisation-owned values.

This makes false-positive policy testable without weakening detection. A future local NER can
emit the same `DetectionCandidate` shape for PERSON/address, while structured identifiers stay
on deterministic rules/checksums. No model dependency or runtime was added.

## Generalized rule changes

- Inflected representative, insured, and benefit-recipient roles.
- Passport field bundles, passport-context division codes, issuer and issue-date variants.
- Numeric and textual birth dates, labelled birthplace fields, migration citizenship fields,
  and driver-verification licence labels.
- Slash-separated subscriber phones, card security/cardholder/PIN labels.
- Personal home, actual-residence, parcel-delivery, and first-person address chains.
- Shared/public phone, mailbox, employer-address, placeholder, documentation, equipment, and
  catalogue suppression.

No case IDs or benchmark target values occur in detector rules.

## Exact-span results

| Dataset | v3.3 P / R / F1 | v3.11 P / R / F1 | v3.13 P / R / F1 |
|---|---:|---:|---:|
| quality | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| adversarial | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| blind v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| FP stress v3 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| sealed v4 | 100 / 100 / 100 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v5 | 91.23 / 68.42 / 78.20 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v6 | 79.69 / 57.95 / 67.11 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v7 | 71.60 / 67.44 / 69.46 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v8 | 69.57 / 55.81 / 61.94 | 100 / 100 / 100 | 100 / 100 / 100 |
| disclosed v9 | 70.15 / 48.96 / 57.67 | 81.25 / 54.17 / 65.00 | 100 / 100 / 100 |

On disclosed v9, v3.13 has 96 TP, 0 FP, and 0 FN: +42.33 percentage points F1 over v3.3
and +35.00 points over v3.11. Only untouched v10 can measure next-round transfer.

## Local performance and verification

Sequential in-process microbenchmark over 697 disclosed short texts, 20 passes (13,940 calls):

| Candidate | Throughput | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| v3.11 | 10,094 calls/s | 0.082 ms | 0.215 ms | 0.265 ms |
| v3.13 | 8,860 calls/s | 0.093 ms | 0.246 ms | 0.310 ms |

This confirms the rule layer remains comfortably above 1,000 sequential calls/s on the local
benchmark machine. It is not an HTTP load test and does not include vault/network overhead.

- Dedicated v3.13 tests include candidate/policy separation and paraphrased recognizers.
- Comparison runner: `python -m proposals.compare_detector_v3_13`.
- Ruff and mypy cover detector, runner, and tests.
- Exact mask/unmask round-trip is checked over disclosed datasets through v9.

