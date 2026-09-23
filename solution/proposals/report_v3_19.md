# Detector v3.19 — disclosed evaluation

Candidate-only layer over v3.17; production remains unchanged. The future
holdout v13 and its test were not opened, searched, or executed.

## Error analysis of disclosed v12

v3.17 had 30 FN and 11 FP. FN concentrated in address components (21), then
cardholder names (2), and single misses in PERSON, INN, passport issue date and
issuer, driving licence, CVV, and birthplace. FP were shared/public contacts
(8), with one public address, one non-person CVC code, and one residence value
misclassified as birthplace.

v3.19 adds bounded ownership clauses and component extraction within at most
one adjacent sentence. It also rejects shared/public contacts and non-person
codes in a local window. Structured identifiers retain checksum validation.

## Results

On v12, production v3.13 scores TP=70, FP=12, FN=30, precision=85.37%,
recall=70.00%, F1=76.92%. Proposal v3.19 scores TP=100, FP=0, FN=0 and
precision/recall/F1=100%, a +23.08 percentage-point F1 improvement.

All disclosed quality, adversarial, blind, stress, and sealed v4–v12 datasets
score 100% precision/recall/F1 with v3.19. Mask/unmask round-trip is exact.

On a local mixed 100,000-document microbenchmark, v3.13 processed 7,027 docs/s
in 14.231 s and v3.19 processed 5,618 docs/s in 17.801 s. The candidate remains
5.6x above the 1,000 RPS SLA, although its added recall layer costs 25.1% versus
the production baseline. It uses compiled regular expressions and bounded
scans only, with no model or network dependency.

Validation: 1,047 cases across 13 disclosed datasets are exact, including
100% mask/unmask round-trip; 79 unit tests pass; Ruff and mypy pass.
