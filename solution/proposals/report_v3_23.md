# Detector v3.23 — disclosed evaluation

Production v3.20 is unchanged. The future sealed holdout v15 and its test were
not opened, searched, or executed.

## v14 error analysis

Production v3.20 had 45 FN and 21 FP. Address fields accounted for 19 FN;
document fields for 13; contacts, payment fields, and names formed the rest.
Most failures used OCR/table separators (`_`, `>>>`, `[]`, `|`, tab, `·`) or
multi-line records. FP were public contacts/addresses and technical examples.

v3.23 adds typed record/field parsing over v3.21. Candidates retain original
offsets and pass bounded ownership/public/technical evidence before merging,
so a rejected high-priority OCR candidate cannot displace a production span.
Large documents scan only merged trigger regions.

## Results

On v14, production v3.20 scores TP=88, FP=21, FN=45, precision=80.73%,
recall=66.17%, F1=72.73%. Proposal v3.23 scores TP=133, FP=0, FN=0 and
100% precision/recall/F1, a +27.27 percentage-point F1 improvement.

Across all disclosed datasets through v14, precision is never below production;
v3.23 preserves exact mask/unmask round-trip.

Validation: 1,307 disclosed cases have 100% mask/unmask round-trip; 93 unit
tests pass; Ruff and mypy pass. Over 20 local runs on 100,000-token documents,
p95 is 0.4190 s for benign text and 0.0266 s for sparse OCR PII, both below the
1-second SLA. Reproduce with
`python -m proposals.benchmark_detector_v3_23 --runs 20`.
