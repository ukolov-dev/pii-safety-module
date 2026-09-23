# PII Safety Module — детектор v3.26

Версия сервиса для идентификации, обратимого маскирования и демаскирования
персональных данных через единый `POST /process`.

Активен детектор `v3.26`; версия Python-пакета и API остаётся `0.1.0`.
Происхождение сборки и проверки описаны в [`VERSION.md`](VERSION.md).

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

Исторические результаты сборки v6 с детектором v3.26 описаны в
[`benchmark-results/v6/IMPROVEMENT_REPORT.md`](benchmark-results/v6/IMPROVEMENT_REPORT.md).
Отдельные инструкции: [`benchmark/README.md`](benchmark/README.md) и
[`tests/load/README.md`](tests/load/README.md).

## Ограничения версии 0.1

- Встроенный детектор детерминированный; ML/LLM в горячем пути отсутствуют.
- ФИО определяются эвристикой и требуют развития до полноценного Natasha/Presidio pipeline.
- При отсутствии `REDIS_URL` используется память одного процесса.
- Для production необходимо задать постоянный `MAPPING_ENCRYPTION_KEY` и Redis.
- Поддержка всех типов ПД и 1000 RPS должна быть подтверждена отдельным benchmark.
