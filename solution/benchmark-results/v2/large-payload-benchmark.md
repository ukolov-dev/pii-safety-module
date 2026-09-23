# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 4.750 | 5.216 | 0.009 | 0.010 | 0.052 | 20.891 | yes |
| 10,000 | 0.150 | 3 | 44.219 | 44.781 | 0.037 | 0.038 | 0.483 | 21.484 | yes |
| 100,000 | 1.502 | 3 | 441.372 | 446.125 | 0.247 | 0.261 | 4.795 | 31.281 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
