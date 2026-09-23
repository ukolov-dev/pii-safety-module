# Large payload benchmark

Python: `3.12.7`. Warm-up runs per size: 1.

| Tokens | Input, MiB | Entities | Mask p50, ms | Mask p95, ms | Unmask p50, ms | Unmask p95, ms | Trace peak, MiB | RSS peak, MiB | Round-trip |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1,000 | 0.015 | 3 | 1.269 | 1.360 | 0.007 | 0.010 | 0.051 | 20.875 | yes |
| 10,000 | 0.150 | 3 | 12.325 | 12.348 | 0.039 | 0.039 | 0.482 | 21.266 | yes |
| 100,000 | 1.502 | 3 | 121.152 | 122.664 | 0.271 | 0.319 | 4.795 | 31.062 | yes |

`Mask` includes entity detection and token substitution. `Unmask` measures exact token restoration. RSS is the process-wide peak reported by the operating system; trace peak is Python allocation memory measured separately for each iteration.
