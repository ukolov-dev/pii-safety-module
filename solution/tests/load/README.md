# Локальный нагрузочный benchmark

Сценарий `process.js` проверяет полный бизнес-цикл: первый `POST /process`
маскирует ПД, второй запрос с тем же `payload_id` восстанавливает исходный текст.
Поэтому одна итерация k6 всегда создаёт **два HTTP-запроса**.

## Безопасная smoke-проверка

Это профиль по умолчанию: один VU в течение 10 секунд.

```bash
k6 run tests/load/process.js
```

Параметры можно менять:

```bash
VUS=2 DURATION=15s BASE_URL=http://127.0.0.1:8080 \
  k6 run tests/load/process.js
```

## SLA-профиль: 1000 HTTP RPS

Перед тестом поднимите целевую конфигурацию сервиса, предпочтительно с Redis.
Профиль сначала выполняет прогрев, затем запускает измеряемую фазу с 500
бизнес-циклами в секунду, то есть с целевыми 1000 HTTP-запросами в секунду.

```bash
PROFILE=load \
TARGET_HTTP_RPS=1000 \
WARMUP_HTTP_RPS=100 \
WARMUP_DURATION=20s \
DURATION=60s \
PREALLOCATED_VUS=1000 \
MAX_VUS=2000 \
BASE_URL=http://127.0.0.1:8080 \
  k6 run --summary-export=tests/load/load-summary.json tests/load/process.js
```

`TARGET_HTTP_RPS` и `WARMUP_HTTP_RPS` должны быть чётными. Настраиваемые
параметры VU: `WARMUP_PREALLOCATED_VUS`, `WARMUP_MAX_VUS`,
`PREALLOCATED_VUS`, `MAX_VUS`. `RUN_ID` позволяет явно задать префикс
уникальных `payload_id`.

## Критерии прохождения

Для измеряемого сценария `benchmark`, без примеси прогрева:

- HTTP errors (`http_req_failed`) — менее 1%;
- функциональные ошибки (`benchmark_errors`) — менее 1%;
- успешные проверки (`checks`) — более 99%;
- HTTP latency p95 — менее 1000 мс;
- пропущенные итерации (`dropped_iterations`) — 0.

В консольной сводке отображаются `med` (p50), p95 и p99 для HTTP-запросов,
отдельных операций и полного бизнес-цикла. Фактический HTTP RPS показан метрикой
`http_reqs`. Если `dropped_iterations` больше нуля, генератор или сервис не смогли
выдержать заданную скорость; увеличьте VU только если узким местом стал сам k6.
JSON-итог сохраняется в `tests/load/load-summary.json` указанным выше параметром
`--summary-export`.

Для воспроизводимого измерения запускайте k6 не в том же ограниченном
контейнере, что и сервис, и фиксируйте CPU/RAM, число воркеров приложения и
конфигурацию Redis.
