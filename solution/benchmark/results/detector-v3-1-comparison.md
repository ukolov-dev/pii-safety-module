# Detector v3.1 public comparison

The candidate keeps v3 recognizers unchanged and applies a post-detection,
sentence-scoped suppression layer. No production module is modified.

| Dataset | Production F1 | v3 F1 | v3.1 F1 | v3.1 vs production |
|---|---:|---:|---:|---:|
| quality | 100.00% | 100.00% | 100.00% | +0.00 pp |
| adversarial | 100.00% | 100.00% | 100.00% | +0.00 pp |
| blind holdout v3 | 51.55% | 68.47% | 71.70% | **+20.15 pp** |
| false-positive stress v3 | 39.34% | 37.50% | 66.67% | **+27.32 pp** |

On the blind set v3.1 has precision 92.68%, recall 58.46%, TP 38, FP 3,
and FN 27. On the false-positive stress set it has precision 52.17%, recall
92.31%, TP 12, FP 11, and FN 1. Suppression removes 28 of v3's 39 stress-set
false positives without removing a positive control.

The layer uses general context families: documentation/examples, code/logs,
organisation-owned contacts and addresses, non-personal identifiers, and
cultural/bibliographic discourse. Email assignment prefixes are normalized as a
boundary correction. It contains no benchmark case IDs or exact sensitive values.

Gate result: PASS. Quality and adversarial remain above 95%; blind improves by
more than 10 percentage points; stress is better than production.
