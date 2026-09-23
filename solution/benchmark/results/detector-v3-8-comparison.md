# Candidate v3.8 disclosed-set report

Production v3.3 remains unchanged. Candidate v3.8 layers general ownership and
syntax rules over candidate v3.6. No future holdout was read or included.

## v6 failure analysis

Production on disclosed v6 had TP 50, FP 13, FN 38: precision 79.37%, recall
56.82%, F1 66.23%. Candidate v3.6 had TP 51, FP 12, FN 37: precision 80.95%,
recall 57.95%, F1 67.55%, only +1.32 percentage points.

False negatives clustered around inflected personal-action names, field-label
variants, slash-separated cards, owned identifiers, settlement/citizenship prose,
issuer aliases, qualified document labels, and unlabelled components inside an
explicit personal address. False positives clustered around organisation-owned
contacts/addresses, all-zero placeholders, equipment/catalog identifiers, and
empty template fields.

## Results

| Dataset | Production F1 | v3.8 F1 | Production precision | v3.8 precision |
|---|---:|---:|---:|---:|
| quality | 100.00% | 100.00% | 100.00% | 100.00% |
| adversarial | 100.00% | 100.00% | 100.00% | 100.00% |
| blind v3 | 95.24% | 97.67% | 98.36% | 98.44% |
| FP stress | 100.00% | 100.00% | 100.00% | 100.00% |
| sealed v4 | 98.44% | 98.44% | 100.00% | 100.00% |
| disclosed v5 | 77.27% | 100.00% | 91.07% | 100.00% |
| disclosed v6 | 66.23% | 100.00% | 79.37% | 100.00% |

On disclosed v6, v3.8 reaches TP 88, FP 0, FN 0. This is a diagnostic result,
not an unbiased estimate. The intended future gate is at least +10 percentage
points F1 over production v3.3 with precision no lower than production.

Round-trip is exact across every case in all seven declared datasets.
