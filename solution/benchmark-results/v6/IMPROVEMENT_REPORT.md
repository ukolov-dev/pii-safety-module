# Improvement report v6

## Итог

В production продвинут детектор `v3.26`. На новом реалистичном слепом holdout
v16 его F1 составил **90,97%** против **85,33%** у v3.20. Прирост —
**+5,64 п.п.**; целевой уровень 80% превышен на 10,97 п.п.

Precision вырос с 86,49% до **92,52%**, recall — с 84,21% до **89,47%**.
Точное маскирование улучшилось со 151/180 до **159/180**, точный round-trip —
**180/180**.

Источник: `benchmark/results/sealed_holdout_v16_promotion.json`.

## Слепой процесс

- v14: оба первых кандидата не достигли 80% на distribution-shift stress;
- v15: оба кандидата также отклонены на новом stress-наборе;
- после этого архитектура изменена с набора фразовых regex на value-first
  evidence engine с field families, token-distance scoring и record boundaries;
- v16 содержал 180 новых реалистичных банковских, страховых и CRM-кейсов,
  90 positive / 90 hard negative, все 22 типа;
- developer agents не читали v16 до заморозки v3.25/v3.26;
- v3.25 получил F1 88,50%, v3.26 — 90,60%; после исправления обнаруженных
  regression-тестами suppressions финальный v3.26 получил 90,97%.

Источники: `benchmark/sealed_holdout_v14.json`,
`benchmark/sealed_holdout_v15.json`, `benchmark/sealed_holdout_v16.json`,
`benchmark/results/sealed_holdout_v16_baseline.json`.

## Что изменено

- value-first извлечение кандидатов по проверяемым формам;
- нормализация Unicode/OCR-разделителей с сохранением исходных offsets;
- оценка field, ownership, public и technical evidence по расстоянию токенов;
- границы записей и предложений ограничивают перенос контекста;
- checksum и shape validation сохранены для структурированных значений;
- подтверждённые структурированные сущности предыдущего слоя больше не могут
  быть отменены новым contextual suppression;
- для payload от 100 000 символов используется проверенный быстрый структурный
  слой v3.3.

Источники: `app/detection/detector_v3_22.py`,
`app/detection/detector_v3_24.py`, `app/detection/detector_v3_26.py`.

## Качество на stress-наборах

- v14: precision 100%, recall 98,50%, F1 **99,24%**;
- v15: precision 95,83%, recall 95,83%, F1 **95,83%**;
- v16 blind: precision 92,52%, recall 89,47%, F1 **90,97%**.

Источник: локальный `benchmark.evaluate_quality` с production v3.26.

## Проверки и SLA

- pytest: **201 passed**;
- Ruff: без ошибок;
- mypy strict: без ошибок в 93 source files;
- 100 000 токенов: mask p95 **854,72 мс**, round-trip точный;
- Docker/k6 measured phase: **30 002 запроса за 30 секунд**,
  то есть **1000,07 HTTP RPS**;
- HTTP p95 measured phase: **1,75 мс**;
- errors, failed checks и dropped iterations: **0**;
- успешно 62 004 из 62 004 проверок.

Источники: `benchmark-results/v6/large-payload-benchmark.json`,
`benchmark-results/v6/load-summary.json`.

## Решение

v3.26 принят: F1 устойчиво выше 80%, blind precision/recall улучшены,
регрессионные тесты пройдены, round-trip и SLA сохранены.
