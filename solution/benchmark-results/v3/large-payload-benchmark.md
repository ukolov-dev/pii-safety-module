# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 8.586 | 8.743 | 0.008 | 0.009 | 0.052 | 21.266 | yes |
| 10,000 | 0.150 | 3 | 82.448 | 83.254 | 0.036 | 0.037 | 0.483 | 21.844 | yes |
| 100,000 | 1.502 | 3 | 826.112 | 828.731 | 0.241 | 0.314 | 4.796 | 31.641 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
