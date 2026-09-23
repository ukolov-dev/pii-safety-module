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

Проверка:

```bash
curl -s http://127.0.0.1:8080/health/live
curl -s -X POST http://127.0.0.1:8080/process \
  -H 'Content-Type: application/json' \
  -d '{"payload":"Иван Петров, email ivan@example.com","payload_id":"demo-1"}'
```

## Тесты

```bash
.venv/bin/pytest -q
k6 run tests/load/process.js
```

Локальные benchmark-контуры и фактические результаты версии 1 описаны в
[`benchmark-results/LOCAL_BENCHMARK_V1.md`](benchmark-results/LOCAL_BENCHMARK_V1.md).
Результаты итерации детектора v2: [`benchmark-results/v2/IMPROVEMENT_REPORT.md`](benchmark-results/v2/IMPROVEMENT_REPORT.md).
Отдельные инструкции: [`benchmark/README.md`](benchmark/README.md) и
[`tests/load/README.md`](tests/load/README.md).

## Ограничения версии 0.1

- Встроенный детектор детерминированный; ML/LLM в горячем пути отсутствуют.
- ФИО определяются эвристикой и требуют развития до полноценного Natasha/Presidio pipeline.
- При отсутствии `REDIS_URL` используется память одного процесса.
- Для production необходимо задать постоянный `MAPPING_ENCRYPTION_KEY` и Redis.
- Поддержка всех типов ПД и 1000 RPS должна быть подтверждена отдельным benchmark.

## VPS demo и потребители (23.09.2026)

Адрес: `https://demo.vibecodefromvoronezh.com/process`; документация: `/docs`.
Публичный профиль `portal` сохраняет контракт жюри без дополнительных заголовков.
Для именованного профиля передаются `X-Consumer-ID` и `X-API-Key`; ключ берётся из
переменной окружения, указанной в `api_key_env`. Профили имеют изолированные
таблицы соответствий даже при одинаковом `payload_id`.

### Настройка за пять предложений

1. Добавьте потребителя в `deploy/consumers.vps.yaml` и установите `enabled`.
2. Укажите `api_key_env`, а соответствующий случайный ключ длиной не менее 32 символов сохраните в серверном `/opt/projects/pii-safety/.env` и передайте сервису через Compose environment.
3. Задайте `mask_types` (null — все обнаруживаемые типы), `demask_enabled` и `vault_ttl_seconds`.
4. Примените изменения через `docker compose -p pii-safety --env-file /opt/projects/pii-safety/.env -f /opt/projects/pii-safety/releases/20260923-consumers/deploy/compose.vps.yml up -d --force-recreate api`.
5. Проверьте запрос с `X-Consumer-ID` и `X-API-Key`, а также запрет доступа отключённому потребителю.

### Наблюдаемость

- `/metrics` доступен локально и Prometheus; публичный nginx возвращает 404.
- RPS: `sum(rate(pii_api_requests_total{job="pii-safety",operation="process"}[2m]))`.
- Latency p95: `histogram_quantile(0.95,sum by(le)(rate(pii_api_request_duration_seconds_bucket{job="pii-safety",operation="process"}[2m])))`.
- TPS: `sum(rate(pii_api_processed_tokens_total{job="pii-safety"}[2m]))`.
- TPS считает последовательности непробельных символов; это не токенизация LLM.
- JSON-логи содержат сгенерированный request_id, настроенное имя потребителя,
  этап, типы и количество сущностей, длительность; исходные данные, payload_id и ключи не пишутся.
- Readiness проверяет хранилище; недоступность возвращает 503 без деталей подключения.
- Логи контейнеров ротируются; Prometheus хранит метрики, Grafana показывает панель `PII Safety — demo`.

### Эксплуатационные ограничения

`portal` намеренно публичный для автопроверки: его payload_id должен быть случайным
и непредсказуемым (UUID), а реальные ПД для публичного демо не нужны.
Остальные потребители требуют ключ; отключите `portal`, если нужен полностью закрытый контур.
Состояние Redis временное (TTL, без AOF): перезапуск Redis теряет таблицы соответствий;
перезапуск API с тем же постоянным ключом их сохраняет.
Новая наблюдаемость и политики проверены функционально; прежний нагрузочный отчёт
не является измерением этого развёртывания.
