# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 26.527 | 26.868 | 0.008 | 0.009 | 0.055 | 22.094 | yes |
| 10,000 | 0.150 | 3 | 254.280 | 257.031 | 0.039 | 0.040 | 0.484 | 22.344 | yes |
| 100,000 | 1.502 | 3 | 872.312 | 889.080 | 0.252 | 0.279 | 12.780 | 35.359 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
