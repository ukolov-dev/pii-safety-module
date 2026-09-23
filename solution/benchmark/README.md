# Local quality benchmark

The benchmark measures the current deterministic detector with exact span matching and
does not alter production detection rules. Its label set mirrors every mandatory PII
category listed in
[`CH-SRC-001-05`](../../.project-context/active/source-chunks/SOURCE-CHUNK-20260923-925.md). Address components use
separate `ADDRESS_*` labels because the source explicitly requires them to be identified
separately; these names are benchmark labels rather than a new API contract.

Run from `solution/`:

```bash
.venv/bin/python -m benchmark.evaluate_quality
```

The command writes machine-readable output to `benchmark/results/quality.json` and a
reviewable report to `benchmark/results/quality.md`. Use `--dataset`, `--json-out`, and
`--markdown-out` to override those paths.

Metrics:

- precision, recall, and F1 require exact `(type, start, end)` matches;
- exact-mask rate compares the complete actual masked string with one generated from the
  gold spans;
- exact round trip masks the detector output and checks byte-for-byte restoration;
- negative examples cover the specifically required poet and bank-office-address cases,
  plus invalid numeric values.

This small synthetic regression set exposes missing coverage and prevents regressions. It
cannot establish 95% quality on the portal's hidden population; that needs a larger,
representative and independently annotated dataset.
