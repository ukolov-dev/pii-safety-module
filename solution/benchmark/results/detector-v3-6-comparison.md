# Candidate v3.6 comparison

Candidate v3.6 is isolated in `proposals/` and leaves production v3.3 unchanged.
It uses only production behavior, disclosed v5 errors, and previously disclosed
regression datasets.

| Dataset | Production F1 | v3.6 F1 | Production FP | v3.6 FP |
|---|---:|---:|---:|---:|
| quality | 100.00% | 100.00% | 0 | 0 |
| adversarial | 100.00% | 100.00% | 0 | 0 |
| blind v3 | 95.24% | 97.67% | 1 | 1 |
| false-positive stress v3 | 100.00% | 100.00% | 0 | 0 |
| sealed v4 | 98.44% | 98.44% | 0 | 0 |
| disclosed sealed v5 | 77.27% | 100.00% | 5 | 0 |

On disclosed v5 the change is **+22.73 percentage points F1**, exceeding the
requested ten-point gate. False positives do not increase on any evaluated set.

General extensions cover personal-action name anchors, dot-separated PAN under
personal payment context, labelled/compact passports, document-code aliases,
textual birth phrases, bounded birthplace and citizenship fields, issuer and
issue-date wording, driver-license aliases, personal address prose, and cardholder
labels. Suppression covers documentation examples, role-owned public mailboxes,
catalogue-like CVV strings, and glossary mentions without values.

Mask/unmask round-trip is exact for every case in all six declared datasets.
This is not an unbiased generalization result because v5 errors were disclosed.
A fresh unread holdout is required before promotion.
