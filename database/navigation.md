# navigation.md — маршруты чтения

Маршруты для быстрого наполнения контекстного окна нового агента. Загружай только нужное по задаче.

## Быстрый старт (обязательно)
1. `START_HERE.md` — порядок работы.
2. `AGENTS.md` — правила работы (категории, источники, сохранность).
3. `database/current_context.md` — краткое состояние проекта.
4. `PROJECT.yaml` — паспорт проекта.

## По задаче
- **Сбор требований** → `playbooks/` (процедуры сбора), затем `RAW/`.
- **Извлечение знаний** → `playbooks/` (процедуры извлечения), затем `RAW/` → `database/`.
- **Подготовка документов** → `playbooks/` (процедуры подготовки), затем `database/` → `COOKED/`.
- **Правила работы** → `AGENTS.md`.

## Справочно
- `RAW/README.md` — что лежит в исходниках.
- `database/README.md` — что лежит в извлеченных знаниях (требования к системе).
- `hackathon_database/README.md` — база знаний хакатона (регламент, правила, инструкции).
- `COOKED/README.md` — что лежит в подготовленных документах.
- `playbooks/README.md` — какие процедуры доступны.

## База знаний хакатона (hackathon_database/)
- Материалы о регламенте проведения хакатона: правила, инструкции, критерии оценки, расписание.
- Отделена от `database/` (требования к самой системе).
- `registry_sources.md`, `registry_decisions.md`, `registry_questions.md`, `registry_conflicts.md`, `registry_coverage.md` — реестры.
- `chunks/` — смысловые чанки.
- `overview.md`, `rules_and_regulations.md`, `evaluation_criteria.md`, `instructions.md` — тематические файлы.

## Реестры (database/)
- `registry_sources.md` — источники (`SRC-NNN`).
- `registry_decisions.md` — согласованные решения (`DEC-NNN`).
- `registry_questions.md` — открытые вопросы (`Q-NNN`).
- `registry_conflicts.md` — конфликты (`CONF-NNN`).
- `registry_coverage.md` — покрытие материалов (`COV-NNN`).

## Чанки (database/chunks/)
- `chunks/index.md` — индекс всех чанков.
- `chunks/_template.md` — шаблон чанка.
- Файлы чанков: `chunks/CH-SRC-NNN-NN.md`.

## Тематические файлы (database/)
- `overview.md` — обзор проекта.
- `goals_and_boundaries.md` — цели и границы.
- `glossary.md` — глоссарий терминов.
- `processes.md` — процессы.
- `data.md` — данные.
- `architecture.md` — архитектура.
- `testing.md` — тестирование.

## Процедуры (playbooks/)
- `process_source.md` — обработка источника на чанки.
- `manage_requirements.md` — управление требованиями.
- `resolve_questions.md` — разрешение вопросов и конфликтов.
- `maintain_data_dictionary.md` — ведение словаря данных.
- `maintain_glossary.md` — ведение глоссария.
- `prepare_developer_tasks.md` — подготовка задач разработки.
- `create_acceptance_checklist.md` — создание чеклиста приемки.
- `process_test_results.md` — обработка результатов тестирования.
- `maintain_traceability.md` — поддержание трассируемости.

## Спецификация (COOKED/requirements/)
- `current_specification.md` — текущая спецификация требований.

## Рабочие файлы (database/working/)
- `id_rules.md` — правила идентификаторов (REQ-/TASK-/AC-/CHK-/RES-).
- `data_dictionary.md` — словарь данных.
- `developer_tasks.md` — задачи разработки.
- `checklists/index.md` — индекс чеклистов; файлы `checklists/CHK-001.md`.
- `test_results/index.md` — индекс результатов проверок; файлы `test_results/RES-001.md`.
- `traceability_matrix.md` — матрица трассируемости.

## Передача контекста
- `session_handoff.md` — шаблон передачи контекста следующей сессии.
- `audit_history.md` — история аудитов и проверок.

## Принцип
- Стартовый контекст держи небольшим.
- Подробности загружай только по конкретной задаче.
- Учитывай место под инструкции, историю и ответы инструментов.