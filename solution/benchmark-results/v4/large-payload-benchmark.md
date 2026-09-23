# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 20.239 | 20.337 | 0.008 | 0.008 | 0.053 | 21.859 | yes |
| 10,000 | 0.150 | 3 | 196.687 | 210.223 | 0.038 | 0.047 | 0.484 | 22.109 | yes |
| 100,000 | 1.502 | 3 | 820.363 | 826.903 | 0.246 | 0.350 | 11.182 | 35.125 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
