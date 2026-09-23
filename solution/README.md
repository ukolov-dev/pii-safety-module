# PII Safety Module — версия 0.1

Первая версия сервиса для идентификации, обратимого маскирования и демаскирования
персональных данных через единый `POST /process`.

## Контракт

```http
POST /process
Content-Type: application/json

{"payload":"Иван Петров, +7 999 123-45-67","payload_id":"demo-1"}
```

Первый вызов с новым `payload_id` маскирует строку. Вызов с тем же `payload_id` и
замаскированной строкой восстанавливает исходные значения. Повтор исходного запроса
возвращает прежний результат маскирования.

Ответ:

```json
{"result":"{{PERSON_1}}, {{PHONE_RF_1}}"}
```

## Локальный запуск

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Или:

```bash
docker compose up --build
```

Основной Compose-контур запускает две реплики API за Nginx и общий Redis.
На host публикуется только proxy на `127.0.0.1:8080`; API и Redis не имеют
host ports. `key-init` однократно генерирует 256-битный ключ в named volume;
обе реплики монтируют его read-only. Ключ не записан в Compose или image.

Для публичной экспозиции перед `127.0.0.1:8080` обязателен доверенный HTTPS
ingress с TLS и аутентикацией. Этот Compose-файл не притворяется защищённым
банковским периметром: сертификаты и внешнюю IAM-политику должен дать
целевой контур эксплуатации.

Опционально сам endpoint `/process` проверяет `X-API-Key`, если задана переменная
`PROCESS_API_KEY` (минимум 16 символов). Для portal-теста она не задана, потому что
контракт портала не предусматривает пользовательский заголовок. В защищённом
развёртывании ключ следует передавать через менеджер секретов, а не записывать в
Compose или image.

Проверка:

```bash
curl -s http://127.0.0.1:8080/health/live
curl -s http://127.0.0.1:8080/health/ready
curl -s -X POST http://127.0.0.1:8080/process \
  -H 'Content-Type: application/json' \
  -d '{"payload":"Иван Петров, email ivan@example.com","payload_id":"demo-1"}'
```

`/health/live` проверяет процесс, `/health/ready` дополнительно выполняет Redis
`PING`. Proxy ограничивает request body до 8 MiB; ASGI middleware повторяет
лимит до JSON-парсинга. Контейнеры запускаются с read-only root filesystem,
drop-all capabilities, `no-new-privileges`, а также лимитами CPU, memory и PID.

## Метрики

```bash
curl -s http://127.0.0.1:8080/metrics
```

Prometheus-экспозиция содержит request count, 4xx/5xx error count, latency
histogram, число in-flight запросов и суммарное число принятых символов.
Последний счётчик позволяет вычислить пропускную способность без хранения текста;
это не метрика токенов конкретного LLM. Единственная метка `operation` имеет фиксированный набор
(`process`, health checks, `metrics`, `other`). Payload, result, `payload_id` и значения
персональных данных в метрики не попадают. При сборе на уровне реплик
скрейпер должен опрашивать `api1:8080/metrics` и `api2:8080/metrics` из edge-сети.

## Тесты

```bash
.venv/bin/pytest -q
k6 run tests/load/process.js
tests/integration/test_compose_failover.sh
```

Failover-тест передаёт первый запрос на `api1`, останавливает эту реплику и
проверяет через proxy, что `api2` доступен и демаскирует запись из общего Redis
тем же общим ключом. Тест сам останавливает Compose-контур после проверки.

Локальные benchmark-контуры и фактические результаты версии 1 описаны в
[`benchmark-results/LOCAL_BENCHMARK_V1.md`](benchmark-results/LOCAL_BENCHMARK_V1.md).
Результаты итерации детектора v2: [`benchmark-results/v2/IMPROVEMENT_REPORT.md`](benchmark-results/v2/IMPROVEMENT_REPORT.md).
Отдельные инструкции: [`benchmark/README.md`](benchmark/README.md) и
[`tests/load/README.md`](tests/load/README.md).

## Ограничения версии 0.1

- Встроенный детектор детерминированный; ML/LLM в горячем пути отсутствуют.
- ФИО определяются эвристикой и требуют развития до полноценного Natasha/Presidio pipeline.
- При ручном запуске без `REDIS_URL` используется память одного процесса.
- Вне Compose для production необходимо задать общий постоянный ключ через
  `MAPPING_ENCRYPTION_KEY` или `MAPPING_ENCRYPTION_KEY_FILE`, а также общий Redis.
- Поддержка всех типов ПД и 1000 RPS должна быть подтверждена отдельным benchmark.
