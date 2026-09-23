# Improvement report v5

## Итог

В production продвинут детектор `v3.20`. На новом слепом holdout v13 его F1
вырос с **61,15%** до **71,95%**, то есть на **+10,80 п.п.**. Precision вырос
с 70,59% до 78,67%, recall — с 53,93% до 66,29%. Точное маскирование получено
для 87 из 120 кейсов, точный round-trip — для 120 из 120.

Источник: `benchmark/results/sealed_holdout_v13_promotion.json`.

## Слепой процесс

- независимый агент сформировал 120 новых кейсов: 60 positive и 60 negative;
- покрыты все 22 типа, усилены PERSON, адресные компоненты и паспортные поля;
- developer agents не читали v13 до заморозки кандидатов;
- v3.19 показал F1 64,60% (+3,45 п.п.) и был отклонён;
- v3.20 показал F1 71,95% (+10,80 п.п.) и прошёл порог +10 п.п.

Источники: `benchmark/sealed_holdout_v13.json`,
`benchmark/results/sealed_holdout_v13_baseline.json`,
`benchmark/results/sealed_holdout_v13_promotion.json`.

## Что изменено

- добавлена нормализованная evidence-scoring прослойка поверх v3.18;
- расширено precision-safe распознавание слабых полей и ownership-контекстов;
- добавлены подавления публичных, автоматизированных и технических значений;
- production API переведён на `app/detection/detector_v3_20.py`;
- для payload от 100 000 символов без расширенных маркеров сохранён быстрый
  маршрут через v3.13, чтобы не нарушать latency SLA;
- v13 добавлен в постоянный quality gate: F1 не ниже 0,711465, precision не ниже
  0,705882, round-trip 100%.

Источники: `app/detection/detector_v3_20.py`, `app/detection/__init__.py`,
`tests/benchmark/test_quality_gate.py`.

## Проверки

- pytest: **160 passed**;
- Ruff: без ошибок;
- mypy strict: без ошибок в 76 source files;
- 100 000 токенов: mask p95 **889,08 мс**, round-trip точный;
- Docker/k6: **30 000 HTTP-запросов за 30 секунд**, то есть **1000 RPS**
  в измеряемой фазе;
- HTTP p95 измеряемой фазы: **1,279 мс**;
- ошибок, failed checks и dropped iterations: **0**;
- всего успешно: 62 000 проверок, включая warm-up.

Источники: `benchmark-results/v5/large-payload-benchmark.json`,
`benchmark-results/v5/load-summary.json`.

## Решение

Кандидат принят: целевой прирост качества достигнут, precision не ухудшен,
round-trip сохранён, локальные latency и load SLA пройдены.
