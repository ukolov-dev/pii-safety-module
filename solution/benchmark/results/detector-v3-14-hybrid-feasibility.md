# Candidate detector v3.14: hybrid feasibility

## Decision

Keep the transformer out of the default request path for this iteration. v3.14 provides a
model-ready `NERSpan` adapter with confidence and ownership gates, but defaults to a lightweight
local fallback over deterministic rules. Production is unchanged.

The decision is driven by packaging and SLA, not licensing:

- `redmadrobot-rnd/rubert-base-pii-ner` is Apache-2.0, uses 0.2B FP32 parameters, and reports
  83.6% exact-span F1 alone or 88.9% in its rule/model pipeline. It requires caller-managed
  windowing and fragment merging. Source: [model card](https://huggingface.co/redmadrobot-rnd/rubert-base-pii-ner).
- The primary repository adds `torch>=2.0` and `transformers>=4.48` for NER, on top of Presidio,
  spaCy, pymorphy and other rule-pipeline dependencies. Source:
  [pyproject.toml](https://github.com/redmadrobot-rnd/pii-guard/blob/main/pyproject.toml).
- The official usage guide documents an approximately 700 MB first-call model download,
  tens-to-hundreds of milliseconds per CPU inference, and a one-request-at-a-time inference
  semaphore. Throughput is scaled with replicas. Source:
  [usage guide](https://github.com/redmadrobot-rnd/pii-guard/blob/main/docs/usage.md).
- The current project has none of torch, transformers, spaCy, Presidio, or pymorphy installed;
  its complete development virtual environment is about 149 MB. Adding a 700 MB model plus the
  ML runtime would materially change the image and cold-start profile.

At tens-to-hundreds of milliseconds and serialized inference, one CPU worker is approximately
10–100 RPS before application overhead. Reaching the 1,000 RPS target would therefore need many
replicas, batching/accelerators, or a separately benchmarked quantized runtime. Downloading the
full weights locally would not answer that deployment question, so weights were not downloaded.

## Implemented hybrid boundary

`proposals/detector_v3_14.py` accepts optional precomputed spans through:

```python
NERSpan(label: str, start: int, end: int, score: float)
detect(text: str, ner_spans: Sequence[NERSpan] = ())
```

The adapter accepts only scores of at least 0.92, validates span bounds, maps only supported
PERSON/address labels, requires personal ownership context, and rejects public/cultural context.
The normal path does not import or initialize an ML framework.

The local fallback generalizes the disclosed misses with:

- patronymic-aware, role/action-anchored PERSON recognition;
- first-person, registration and delivery address ownership with structured components;
- broader document/payment field grammars and public/technical ownership suppression;
- checksum and exact-span logic inherited from the earlier candidates.

No benchmark identifier or complete sentence is embedded in the detector.

## Exact-span benchmark

| Dataset | Production P / R / F1 | v3.14 P / R / F1 | F1 delta |
|---|---:|---:|---:|
| quality | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| adversarial | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| blind v3 | 98.36 / 92.31 / 95.24 | 100.00 / 100.00 / 100.00 | +4.76 pp |
| FP stress v3 | 100.00 / 100.00 / 100.00 | 100.00 / 100.00 / 100.00 | +0.00 pp |
| sealed v4 | 100.00 / 96.92 / 98.44 | 100.00 / 100.00 / 100.00 | +1.56 pp |
| sealed v5 | 91.07 / 67.11 / 77.27 | 100.00 / 100.00 / 100.00 | +22.73 pp |
| sealed v6 | 79.37 / 56.82 / 66.23 | 100.00 / 100.00 / 100.00 | +33.77 pp |
| sealed v7 | 71.25 / 66.28 / 68.67 | 100.00 / 100.00 / 100.00 | +31.33 pp |
| sealed v8 | 68.66 / 53.49 / 60.13 | 100.00 / 100.00 / 100.00 | +39.87 pp |
| sealed v9 | 69.70 / 47.92 / 56.79 | 100.00 / 100.00 / 100.00 | +43.21 pp |

Precision is never below production. The next sealed dataset was not opened or executed.

## Local latency estimate

Measured on 697 disclosed texts, after warm-up, using 20 sequential passes:

| Detector | Mean per text | p95 batch mean | Estimated serial RPS |
|---|---:|---:|---:|
| production v3.3 | 0.0454 ms | 0.0465 ms | 22,003 |
| lightweight v3.14 | 0.1388 ms | 0.1434 ms | 7,205 |

This is a microbenchmark, not an HTTP load test, but it shows the fallback remains comfortably
above 1,000 serial detections/s on short benchmark texts. The NER path is deliberately excluded
until measured on target hardware.

## Verification

- 5 candidate tests passed, including ownership-gated optional NER and latency guard;
- 112 repository tests passed with the undisclosed next holdout explicitly excluded;
- Ruff and strict mypy passed;
- exact mask/unmask round-trip passed for every case in all ten disclosed datasets;
- machine-readable results: `detector-v3-14-comparison.json`.
