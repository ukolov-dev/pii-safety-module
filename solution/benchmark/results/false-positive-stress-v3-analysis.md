# False-positive stress v3: baseline v2

Dataset: `benchmark/false_positive_stress_v3.json`; 64 cases, including 56
negative stress cases and 8 positive controls. The dataset is synthetic and does
not contain production personal data.

## Baseline metrics

| Metric | Result |
|---|---:|
| True-positive entities | 12 |
| False-positive entities | 36 |
| False-negative entities | 1 |
| Precision | 25.00% |
| Recall | 92.31% |
| F1 | 39.34% |
| Entity FP share (`FP / (TP + FP)`) | 75.00% |
| Negative cases with at least one FP | 34 / 56 (60.71%) |
| Exact masks | 29 / 64 (45.31%) |
| Exact round trips | 64 / 64 (100.00%) |

This is intentionally a precision-hostile set, so these values should not be
mixed with the balanced quality benchmark. It exposes a genuine weakness:
checksums and lexical patterns establish that a value *looks* valid, but do not
establish that it belongs to a person.

The only positive-control miss is `positive-real-birth-date`: the detector does
not accept `Дата рождения клиента: 29.02.2000` because the current immediate
context rule does not allow `клиента` between the label and value.

## False positives

- Public phones: `+7 (495) 123-45-67`, `+7 812 555-12-34`,
  `8 (499) 321-54-76`, `+7-343-200-10-20`, and the company contact
  `+7 495 111-22-33`.
- Identifier/placeholder phones: `89991234567` used as a ticket number and
  `+7 (999) 999-99-99` used as a format sample.
- Public/generic email addresses: `info@example.ru`, `sales@company.test`,
  `press@museum.example`, `jobs@factory.example`, `security@example.com`, and
  `office@example.ru`.
- Documentation/code email addresses: `user@example.com`,
  `developer@example.com`, `'test@example.com`, and
  `recipient=noreply@example.org`. The last two also demonstrate over-wide
  email spans caused by punctuation accepted at the start of the local part.
- Organizational or synthetic INNs: `7707083893` twice and
  `500100732259` twice.
- Test/build card-like values: `4111 1111 1111 1111`,
  `4111-1111-1111-1111`, and `4111111111111111`.
- Historical, fictional, or bibliographic names: `Пушкин Александр
  Сергеевич`, `Толстой Лев Николаевич`, `Гагарин Юрий Алексеевич`,
  `Менделеев Дмитрий Иванович`, `Иванов Иван Иванович`, and `Булгаков Михаил
  Афанасьевич`.
- Documentation examples: passport `45 10 123456`, labelled passport `серия
  45 10, номер 123456`, division code `770-001`, birth date `01.01.1990`, CVV
  `123`, and PIN `4821`.

## General filters worth testing

1. Add scoped negative context classification before entity-specific rules.
   Windows containing documentation/example/template/sandbox/test/format/code/log
   language should lower confidence or suppress a match, while explicit personal
   context (`клиент`, `заявитель`, `физическое лицо`, `личный`) should raise it.
   Scope should be sentence or field based, not a document-wide switch.
2. Separate syntactic validity from PII classification. Luhn and INN checksums
   remain validators, but card/INN values should require a personal or transaction
   context. In particular, a 10-digit INN normally identifies a legal entity;
   treating every checksum-valid value as personal creates systematic over-mask.
3. Classify contact ownership. Suppress phone/email in organizational contexts
   such as hotline, reception, office, department, press service, sales, jobs and
   company contacts. Keep personal labels as strong positive evidence. Generic
   mailbox local-parts may be a supporting signal, but should not be the only rule.
4. Tighten email span boundaries: require an alphanumeric first and final local
   character for the unquoted form, so SQL quotes and `key=` log prefixes cannot
   become part of the entity span. If full RFC syntax is needed, parse quoted
   local-parts explicitly instead of accepting punctuation greedily.
5. Gate fallback PERSON recognition with discourse context. Bibliographic,
   historical, literary, educational and example contexts should suppress the
   fallback. This is more general than maintaining a blacklist of famous names.
6. Recognize placeholder structure before PII detection. Existing `{{TYPE_N}}`
   tokens are safe, but repeated-digit phone/PAN patterns, `example.*` domains,
   and values adjacent to words like `format` or `sample` need a placeholder
   confidence penalty.
7. Add a two-threshold policy: high-confidence values mask immediately;
   ambiguous standalone syntactic matches mask only with personal context. Tune
   thresholds jointly against the main, adversarial, and false-positive sets so
   precision gains cannot silently destroy recall.

Do not optimize against individual strings in this file. Each accepted change
should pass all three datasets and preserve the 1000 RPS and 100k-token gates.
