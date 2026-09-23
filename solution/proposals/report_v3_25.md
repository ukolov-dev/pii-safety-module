# Detector v3.25 proposal

## Scope and constraints

This is an isolated proposal; production `detector_v3_20.py` is unchanged. The
design was selected from disclosed failures through v15. No v16 data or test is
used by the candidate, comparison runner, tests, or benchmark.

## Architecture

The pipeline separates recognition from the mask decision:

1. Per-character NFKC/casefold/OCR normalization keeps an exact source-offset
   map, so detections always point back to the original text.
2. A tokenizer assigns record identifiers at semicolon/newline boundaries.
3. Normalized field-family stems open a bounded state; a compatible value shape
   must occur within 150 characters and the same record.
4. Dates, INN and payment-card values pass semantic validation/checksums.
5. Prose ownership anchors and address-record parsing add only bounded evidence.
6. A separate policy decides whether the candidate belongs to a person, a
   public organization/location, or a technical object.
7. Existing production-compatible detections and proposal candidates are merged
   deterministically; the policy is applied again after the merge.

Large documents retain the bounded-region path inherited from v3.23 to keep the
100k-token SLA independent of whole-document normalization.

## Disclosed v15 error analysis

The dominant false-negative families were unstructured person/address context,
place/date-of-birth and passport issue metadata. False positives clustered
around public delivery points, organization contacts and identifiers attached
to industrial objects. These categories informed field families and policy
guards; no complete benchmark sentence is embedded in the implementation.

## Validation

Disclosed regression covers 16 datasets and 1,467 cases (quality,
adversarial, blind/stress v3, and sealed v4-v15):

- v15 production v3.20: TP=90, FP=28, FN=54, precision=76.27%, F1=68.70%.
- v15 proposal v3.25: TP=117, FP=0, FN=27, precision=100%, F1=89.66%.
- Candidate precision is equal to or higher than production on every disclosed
  dataset; no disclosed dataset regresses in F1.
- Exact mask/unmask round-trip and source spans: 1,467/1,467 cases pass.
- Full test suite: 198 passed (one dependency deprecation warning).
- Ruff: pass. Mypy: pass.

The 20-run local 100k-token benchmark measured:

| document | median | p95 | SLA |
| --- | ---: | ---: | --- |
| benign | 0.418 s | 0.634 s | pass |
| sparse PII | 0.816 s | 1.477 s | **fail** |

The candidate therefore meets the disclosed quality and precision gates but
does **not** meet the stated p95 <1 s gate for the sparse-PII 100k-token case.
It must not be promoted without resolving and re-measuring that performance
failure. The candidate file was frozen after this result; no v16 material was
read, searched, or executed.
