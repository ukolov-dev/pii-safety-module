# Рекомендуемый технологический стек модуля защиты ПД

Дата: **2026-09-23**.

Статус: **предлагаемое архитектурное решение**. Документ не изменяет согласованные требования и не закрывает открытые вопросы `database/Q-002`, `database/Q-003`, `database/Q-004` и `hackathon_database/Q-003`.

Основание: [требования и границы](../goals_and_boundaries.md), [архитектура](../architecture.md), [процессы](../processes.md), [данные](../data.md), [тестирование](../testing.md), [исследование GitHub-аналогов](github_open_source_landscape.md).

## 1. Решение

Для текущего решения рекомендуется **модульный Python-монолит с Redis**, без LLM в горячем пути:

```text
HTTP client
   │
   ▼
FastAPI /process
   │
   ├── consumer policy
   ├── idempotency/state resolver
   │
   ├── deterministic detectors
   │      regex + checksums + context rules
   │
   ├── Russian NER
   │      Natasha/Slovnet
   │
   ├── Presidio span orchestration
   │
   ├── reversible tokenization
   │
   └── encrypted mapping vault ──► Redis
          │
          └── metadata-only logs and metrics
```

Почему не Go-first: основная сложность задачи — качество русскоязычного NLP, а наиболее подходящие библиотеки работают в Python. Вынос HTTP-слоя в Go добавит сетевой hop и второй runtime, но не ускорит CPU-bound NER. При необходимости Go/Rust hot path можно добавить после профилирования, не меняя контракт.

## 2. Конкретный стек

| Слой | Выбор | Назначение |
|---|---|---|
| Язык | **Python 3.12** | Наиболее безопасная совместимость NLP-библиотек и современного async/runtime |
| Управление зависимостями | **uv + pyproject.toml + lock-файл** | Воспроизводимые и быстрые сборки |
| HTTP API | **FastAPI + Pydantic v2 + Uvicorn** | Точный `POST /process`, валидация, OpenAPI, health endpoints |
| JSON | **orjson** | Быстрый разбор/сериализация короткого API-контракта |
| PII orchestration | **Presidio Analyzer + Anonymizer** | Единая модель spans, приоритеты recognizers, расширяемые операторы |
| РФ identifiers | **Собственные Presidio PatternRecognizer** на основе `presidio-ru-recognizers` | ИНН, паспорт, телефон и другие форматы с checksum/context validation |
| Русский NER | **Natasha/Slovnet** | ФИО, организации, локации; CPU/offline inference |
| Rule-based NLP | **Razdel + Yargy** | Сегментация больших текстов и контекстные русские правила |
| Маскирование | **Собственный typed-token operator** | Обратимые маски вида `{{PERSON_1}}`, `{{PHONE_1}}` |
| Оперативное состояние | **Redis 7-compatible** | `payload_id → encrypted mapping`, TTL, атомарность, shared state между репликами |
| Клиент Redis | **redis-py asyncio** | Пул соединений и неблокирующий I/O |
| Шифрование mapping | **cryptography / AES-256-GCM** | Шифрование значений до записи в Redis; authenticated encryption |
| Конфигурация | **YAML + Pydantic Settings** | Версионируемые policy-профили потребителей для MVP |
| Логи | **structlog** | Структурированные metadata-only события без payload и найденных значений |
| Метрики | **prometheus-client** | latency, RPS, результат, 429/4xx/5xx, количество типов без значений |
| Трассировка | **OpenTelemetry без content capture** | Диагностика стадий без prompt/response в spans |
| Тесты | **pytest + pytest-asyncio + Hypothesis** | Unit, API, round-trip, property-based проверки форматов |
| Нагрузка | **k6** | Проверка 1000/2000 RPS, latency, 429, retry и деградации |
| Качество кода | **Ruff + mypy** | Линтинг, форматирование и типизация |
| Поставка MVP | **Docker + Docker Compose** | Воспроизводимый запуск приложения, Redis и мониторинга |
| CI | **GitHub Actions** | Tests, lint, typecheck, container build, dependency scan |

PostgreSQL, Kafka/NATS, Kubernetes и LiteLLM в MVP не нужны. Они не участвуют в обязательном контракте и увеличат время разработки и число точек отказа.

## 3. Структура приложения

```text
app/
  api/             # /process, /health/live, /health/ready, /metrics
  domain/          # state machine и модели предметной области
  detection/
    recognizers/   # РФ regex/checksum recognizers
    ner/           # адаптер Natasha/Slovnet
    pipeline.py    # merge, priorities, confidence thresholds
  masking/         # typed tokens и round-trip restoration
  vault/           # Redis repository + AES-GCM envelope
  policies/        # профили потребителей
  observability/   # безопасные logs/metrics/traces
tests/
  unit/
  integration/
  golden/
  load/
config/
  consumers.yaml
```

Это один deployable service, но модули разделены интерфейсами. NER, vault или API можно будет вынести в отдельный сервис только после измерений.

## 4. Detection pipeline

Порядок обработки влияет и на качество, и на latency:

1. **Нормализация без изменения исходных offsets**: Unicode normalization, унификация технических разделителей.
2. **Дешёвые детекторы**: email, телефон, карта/Luhn, ИНН/checksum, паспорт/context, код подразделения, даты, CVV/PIN при достаточном контексте.
3. **Natasha/Slovnet**: ФИО, организации, локации.
4. **Yargy/context rules**: адресные компоненты, место рождения, орган выдачи, составные паспортные конструкции.
5. **Span resolver Presidio**: устранение пересечений по приоритету, confidence и специфичности.
6. **Policy filter**: какие типы маскировать для конкретного потребителя.
7. **Typed tokenization** и запись mapping.

Приоритет должен отдаваться checksum-валидированному идентификатору перед общим числовым шаблоном и контекстному составному recognizer перед NER-span.

### Почему не использовать локальную LLM в основном pipeline

- непредсказуемая latency и потребление памяти;
- сложнее обеспечить 1000 RPS;
- менее детерминированные spans и повторяемость;
- дополнительные риски логирования и деградации.

GLiNER или локальную LLM можно позднее включить как **опциональный второй проход** для низкоуверенных случаев, отдельным policy-флагом и с жёстким timeout.

## 5. Маскирование и vault

Для обязательного пути рекомендуется typed-token masking, а не AES ciphertext внутри текста и не случайные синтетические данные.

Пример:

```text
Иван Петров, телефон +7 999 123-45-67
→
{{PERSON_1}}, телефон {{PHONE_1}}
```

Преимущества:

- сохраняется роль сущности для LLM;
- токен легко и точно восстановить;
- одна сущность получает один токен в рамках `payload_id`;
- можно обнаруживать выдуманные или повреждённые токены;
- формат маски можно заменить конфигурацией после разрешения `hackathon_database/Q-003`.

### Запись vault

Рекомендуемый ключ:

```text
pii:{consumer_namespace}:{payload_id}
```

Рекомендуемое содержимое до шифрования:

```yaml
state: masked
request_hash: <sha256 canonical request>
masked_hash: <sha256 result>
mapping:
  "{{PERSON_1}}": "Иван Петров"
  "{{PHONE_1}}": "+7 999 123-45-67"
created_at: <timestamp>
expires_at: <timestamp>
policy_version: <version>
```

Mapping шифруется AES-GCM на уровне приложения. Redis не должен видеть исходные значения ПД. В associated data следует включить consumer namespace, `payload_id` и версию формата, чтобы ciphertext нельзя было незаметно перенести в другую запись.

Для MVP ключ шифрования передаётся через secret/environment. Для production — Vault/KMS и ротация ключей.

## 6. Логика `POST /process`

Предлагаемый алгоритм, учитывающий ретраи:

```text
если записи payload_id нет:
    detect → mask → atomic save → return masked

если запись есть и hash(payload) == request_hash:
    вернуть прежний masked result                 # retry маскирования

если запись есть и payload содержит известные токены:
    unmask → return original values               # ответ LLM

иначе:
    controlled 409/422, без вывода payload в лог
```

Это **предлагаемое решение**, а не подтверждённое требование: точное различение повторного маскирования и демаскирования остаётся открытым вопросом `database/Q-004`.

Атомарность первого вызова реализуется Redis Lua script или транзакцией `SET NX`. Повторный запрос на другую реплику должен вернуть тот же результат.

## 7. Производительность

Чтобы приблизиться к целевым показателям:

- все модели загружаются при старте, readiness включается только после прогрева;
- outbound network calls в `/process` отсутствуют;
- regex/checksum выполняются первым слоем и за один проход, где возможно;
- большие тексты сегментируются Razdel по предложениям/блокам, offsets пересчитываются при merge;
- NER обрабатывается батчами;
- приложение запускается несколькими **процессами**, а не только async coroutines, потому что NER CPU-bound;
- масштабирование выполняется репликами с общим Redis;
- Redis-команды объединяются в pipeline/Lua operation;
- config и compiled patterns кэшируются в памяти;
- логирование асинхронное и не содержит body.

Нельзя заранее утверждать, что этот стек выдержит 1000 RPS и payload 100 000 токенов при p95 ≤1 с одновременно. Это нужно доказать k6-профилем и измерениями на целевом железе. Возможная оптимизация после профилирования — отдельный Go/Rust fast-path для regex/checksum, но не до появления доказанного bottleneck.

## 8. Безопасная наблюдаемость

Разрешённые поля логов:

- generated `request_id`;
- необратимый HMAC от `payload_id`, а не исходный ID;
- consumer alias;
- policy version;
- направление `mask|unmask|retry`;
- длительность стадий;
- коды результата;
- количество находок по фиксированному типу.

Запрещённые поля:

- `payload`, `result` и части исходного текста;
- значения найденных сущностей;
- mapping или ciphertext mapping;
- Redis key целиком;
- stack traces с локальными переменными тела запроса.

Prometheus labels должны иметь ограниченную кардинальность. `payload_id`, `request_id` и токены не используются как labels.

## 9. Конфигурация потребителей

Контракт тела запроса менять не нужно. Потребитель определяется по API key или служебному HTTP-заголовку на инфраструктурном слое.

Пример MVP-профиля:

```yaml
consumers:
  default:
    enabled: true
    detect: [PERSON, BIRTH_DATE, PASSPORT_RF, ADDRESS, EMAIL, PHONE_RF, INN, BANK_CARD]
    mask_mode: typed_token
    demask_enabled: true
    vault_ttl_seconds: 900
    confidence_thresholds:
      PERSON: 0.75
      ADDRESS: 0.80
```

YAML достаточно для демонстрации гибкости. PostgreSQL и административный API следует добавлять только если появится требование менять политики во время работы без deployment.

## 10. Поставка по этапам

### Этап 1 — обязательный MVP

- FastAPI `/process`;
- Presidio + российские regex/checksum recognizers;
- Natasha для ФИО;
- typed-token mask/unmask;
- Redis mapping по `payload_id`;
- pytest golden tests;
- safe JSON logs;
- Docker Compose;
- k6 smoke/load scenario.

### Этап 2 — качество

- адреса и составные паспортные данные через Yargy;
- все целевые типы ПД;
- per-consumer profiles;
- confidence calibration;
- негативные примеры: публичные лица и адреса организаций;
- обработка до 100 000 токенов.

### Этап 3 — производительность и надёжность

- worker/repository profiling;
- horizontal replicas;
- 429 и backpressure;
- failure injection Redis;
- p95/p99 dashboards;
- 1000 и 2000 RPS benchmark;
- KMS/Vault integration при production-развитии.

## 11. Что сознательно не выбирать сейчас

- **LiteLLM внутри обязательного `/process` пути** — routing к провайдерам не нужен для автопроверки и расширяет поверхность отказов.
- **LLM Guard** — репозиторий архивирован.
- **Kiji как готовое ядро** — не доказано покрытие российских типов.
- **Собственная ML-модель с нуля** — нет подтверждённого корпуса и времени на корректное обучение.
- **Микросервисная архитектура** — преждевременная сложность для одного endpoint.
- **PostgreSQL в горячем пути** — Redis лучше соответствует TTL/state/idempotency; долговременный audit исходных mappings не нужен и опасен.

## 12. Итоговый выбор

```yaml
runtime: Python 3.12
api: FastAPI + Pydantic + Uvicorn
pii_engine: Presidio
russian_ner: Natasha/Slovnet
rules: custom Presidio recognizers + Yargy
state: Redis
crypto: AES-256-GCM via cryptography
masking: typed reversible tokens
config: YAML + Pydantic Settings
observability: structlog + Prometheus + OpenTelemetry without content
tests: pytest + Hypothesis + k6
delivery: Docker Compose
```

Этот стек оптимизирует вероятность успеть собрать проверяемое решение, не блокирует дальнейшее горизонтальное масштабирование и минимизирует число технологий в критическом пути.
