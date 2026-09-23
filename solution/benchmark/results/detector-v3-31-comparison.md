# Candidate detector v3.31 comparison

| Dataset | Detector | Precision | Recall | F1 | Exact masks | Round-trip |
|---|---|---:|---:|---:|---:|---:|
| sealed_holdout_v4.json | v3.26 | 100.0000% | 100.0000% | 100.0000% | 100.0000% | 100.0000% |
| sealed_holdout_v4.json | v3.31 | 100.0000% | 100.0000% | 100.0000% | 100.0000% | 100.0000% |
| sealed_holdout_v5.json | v3.26 | 98.6842% | 98.6842% | 98.6842% | 97.0588% | 100.0000% |
| sealed_holdout_v5.json | v3.31 | 98.6842% | 98.6842% | 98.6842% | 97.0588% | 100.0000% |
| sealed_holdout_v6.json | v3.26 | 98.8636% | 98.8636% | 98.8636% | 97.7778% | 100.0000% |
| sealed_holdout_v6.json | v3.31 | 98.8636% | 98.8636% | 98.8636% | 97.7778% | 100.0000% |
| sealed_holdout_v7.json | v3.26 | 98.8235% | 97.6744% | 98.2456% | 97.0000% | 100.0000% |
| sealed_holdout_v7.json | v3.31 | 98.8235% | 97.6744% | 98.2456% | 97.0000% | 100.0000% |
| sealed_holdout_v8.json | v3.26 | 100.0000% | 98.8372% | 99.4152% | 99.0000% | 100.0000% |
| sealed_holdout_v8.json | v3.31 | 100.0000% | 98.8372% | 99.4152% | 99.0000% | 100.0000% |
| sealed_holdout_v9.json | v3.26 | 100.0000% | 97.9167% | 98.9474% | 98.0000% | 100.0000% |
| sealed_holdout_v9.json | v3.31 | 100.0000% | 97.9167% | 98.9474% | 98.0000% | 100.0000% |
| sealed_holdout_v10.json | v3.26 | 99.0196% | 99.0196% | 99.0196% | 98.1818% | 100.0000% |
| sealed_holdout_v10.json | v3.31 | 99.0196% | 99.0196% | 99.0196% | 98.1818% | 100.0000% |
| sealed_holdout_v11.json | v3.26 | 100.0000% | 96.0784% | 98.0000% | 99.1667% | 100.0000% |
| sealed_holdout_v11.json | v3.31 | 100.0000% | 96.0784% | 98.0000% | 99.1667% | 100.0000% |
| sealed_holdout_v12.json | v3.26 | 98.9899% | 98.0000% | 98.4925% | 97.5000% | 100.0000% |
| sealed_holdout_v12.json | v3.31 | 98.9899% | 98.0000% | 98.4925% | 97.5000% | 100.0000% |
| sealed_holdout_v13.json | v3.26 | 98.8636% | 97.7528% | 98.3051% | 97.5000% | 100.0000% |
| sealed_holdout_v13.json | v3.31 | 98.8636% | 97.7528% | 98.3051% | 97.5000% | 100.0000% |
| sealed_holdout_v14.json | v3.26 | 100.0000% | 98.4962% | 99.2424% | 98.5714% | 100.0000% |
| sealed_holdout_v14.json | v3.31 | 100.0000% | 98.4962% | 99.2424% | 98.5714% | 100.0000% |
| sealed_holdout_v15.json | v3.26 | 95.8333% | 95.8333% | 95.8333% | 92.5000% | 100.0000% |
| sealed_holdout_v15.json | v3.31 | 95.8333% | 95.8333% | 95.8333% | 92.5000% | 100.0000% |
| sealed_holdout_v16.json | v3.26 | 92.5170% | 89.4737% | 90.9699% | 88.3333% | 100.0000% |
| sealed_holdout_v16.json | v3.31 | 92.5170% | 89.4737% | 90.9699% | 88.3333% | 100.0000% |
| sealed_holdout_v19.json | v3.26 | 98.2759% | 55.8824% | 71.2500% | 25.0000% | 100.0000% |
| sealed_holdout_v19.json | v3.31 | 99.0486% | 70.6637% | 82.4824% | 25.0000% | 100.0000% |
| sealed_holdout_v20.json | v3.26 | 96.8665% | 55.5469% | 70.6058% | 28.4375% | 100.0000% |
| sealed_holdout_v20.json | v3.31 | 100.0000% | 100.0000% | 100.0000% | 100.0000% | 100.0000% |

v3.31 remains isolated from `app.detection`. It adds boundary-restricted, value-validated semantic field parsing and contains no benchmark entity-value dictionaries or benchmark IDs.
