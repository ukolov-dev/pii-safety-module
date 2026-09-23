# Detector v3.21 — disclosed evaluation

Production v3.20 is unchanged. The future sealed holdout v14 and its test were
not opened, searched, or executed.

## v13 error analysis

Production v3.20 had 30 FN and 16 FP. Address components accounted for 17 FN;
PERSON and passport/issuer fields formed most of the remainder. Ten FP were
public phones or role mailboxes, while the rest were public addresses,
technical CVC, an over-wide person span, and a birthplace/city conflict.

v3.21 adds a structural parser for bounded personal form/document blocks. It
supports inflected roles, whitespace, newlines, table pipes, dashes, equals,
slashes, and semicolon-separated address chains. Public and technical evidence
is evaluated independently after candidate merging. Large documents use
merged 1,200-character evidence regions around semantic triggers.

## Results

On v13, v3.20 scores TP=59, FP=16, FN=30, precision=78.67%, recall=66.29%,
F1=71.95%. v3.21 scores TP=89, FP=0, FN=0 and 100% precision/recall/F1.

Across all 14 disclosed datasets through v13, v3.21 introduces no regression
against v3.20 and improves v7 by one TP. Round-trip is exact.

For 100,000-token local documents over 20 runs, v3.21 p95 was 0.4099 s on
benign text and 0.0153 s on sparse PII text. Both are below the 1-second SLA.

Validation: 1,167 disclosed cases have exact mask/unmask round-trip; 86 unit
tests pass; Ruff and mypy pass. The benchmark is reproducible with
`python -m proposals.benchmark_detector_v3_21 --runs 20`.
