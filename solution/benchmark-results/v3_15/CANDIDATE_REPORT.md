# Detector v3.15 candidate report

## Boundary

v3.15 is an isolated proposal over v3.13. Production files were not modified. Disclosed v10
was used for error analysis and is therefore tuning data. The future v11 dataset and its tests
were not opened, imported, or executed.

## Generalized approach

v3.15 retains v3.13's separate `detect_candidates` and `should_mask` stages. Recall expansion
is limited to strong personal/document clauses:

- consent giver, parcel recipient, benefit recipient, and account-holder PERSON roles;
- first-person home address, declared residence, applicant/insured home, recipient response,
  and home-delivery clauses;
- city recognition in comma/semicolon layouts and locative `живёт в`/`дом ... во`
  forms;
- passport field bundles, issuer, issue-date and passport-scoped division labels;
- document-owned and `родом из` birthplace clauses.

The policy layer suppresses shared/public phone and email clauses plus store, branch, pickup,
workplace, and organisation addresses. Rules contain no benchmark case IDs or target values.
Address parsing is bounded to a 400-character clause to avoid payload-size quadratic work.

## Exact-span results

v3.15 has 100% precision, recall, and F1 on every disclosed dataset: quality, adversarial,
blind v3, FP stress v3, and sealed v4 through disclosed v10. On v10 specifically:

| Detector | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| v3.13 | 80 | 16 | 22 | 83.33% | 78.43% | 80.81% |
| v3.15 | 102 | 0 | 0 | 100% | 100% | 100% |

The disclosed-set improvement is +19.19 percentage points F1. Only untouched v11 can measure
the requested unseen improvement.

## Performance

Local sequential in-process benchmarks:

| Workload | v3.13 | v3.15 |
|---|---:|---:|
| 807 disclosed short texts, 20 passes | 7,846 calls/s | 7,860 calls/s |
| Short-text p95 | 0.271 ms | 0.276 ms |
| 100k benign text mean | 127.91 ms | 128.53 ms |
| 100k sparse-PII text mean | 131.89 ms | 134.03 ms |
| 100k sparse-PII throughput | 758k chars/s | 746k chars/s |

The 100k payload remains far below a one-second rule-layer latency. This is not an HTTP/vault
load test. The small differences are within a single-process microbenchmark's run-to-run noise.

## Verification

- Comparison runner: `python -m proposals.compare_detector_v3_15`.
- Dedicated tests cover paraphrased ownership clauses, exact spans, policy rejection, and
  reversible masking.
- Ruff and mypy cover detector, runner, and tests.
- Mask/unmask round-trip is checked over every disclosed dataset through v10.

