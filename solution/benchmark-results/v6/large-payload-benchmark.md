# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 55.630 | 56.270 | 0.009 | 0.009 | 0.054 | 23.906 | yes |
| 10,000 | 0.150 | 3 | 191.910 | 193.156 | 0.043 | 0.046 | 0.486 | 24.219 | yes |
| 100,000 | 1.502 | 3 | 851.786 | 854.724 | 0.251 | 0.321 | 4.796 | 34.016 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
