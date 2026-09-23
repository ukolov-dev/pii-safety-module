---
kind: policy
modules: [requirements, hackathon, sources, specifications, project_rules]
routing: core
required: true
last_verified: "2026-09-23"
verify_with: [context_lint]
---

# playbooks — инструкции и регламенты

Инструкции и регламенты процессов работы с базой знаний.

## Правила
- Каждый процесс — отдельный файл.
- Инструкции конкретны и выполнимы.

## Таблица плейбуков

| Запрос | Плейбук |
| --- | --- |
| Обработать новый источник из RAW | `process_source.md` |
| Управлять требованиями / спецификацией | `manage_requirements.md` |
| Разрешить открытый вопрос или конфликт | `resolve_questions.md` |
| Вести словарь данных | `maintain_data_dictionary.md` |
| Вести глоссарий | `maintain_glossary.md` |
| Подготовить задачи разработки | `prepare_developer_tasks.md` |
| Создать чеклист приемки | `create_acceptance_checklist.md` |
| Обработать результаты тестирования | `process_test_results.md` |
| Поддерживать трассируемость | `maintain_traceability.md` |
