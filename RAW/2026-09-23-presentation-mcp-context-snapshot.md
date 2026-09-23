# Источники слайда о mcp-context

Дата: 23.09.2026. Снимок локальной документации и конфигурации. Польза для поддержки — ожидаемый эффект возможностей, а не измеренная экономия времени. Пример инцидента — иллюстративный сценарий.

## README.md

```
# PII Safety Module — защита персональных данных для LLM

Сервис распознаёт персональные данные, заменяет их обратимыми масками и
восстанавливает исходные значения через единый `POST /process`.
Реализация, тесты и конфигурация запуска находятся в [`solution/`](solution/README.md).

## Быстрый запуск

```bash
git clone https://github.com/ukolov-dev/pii-safety-module.git
cd pii-safety-module/solution
docker compose up --build
```

Сервис доступен на `http://127.0.0.1:8080`.
Подробности API, локальной установки и тестирования — в
[`solution/README.md`](solution/README.md), требования к защищённому развёртыванию
и ограничения — в [`solution/SECURITY_AND_OPERATIONS.md`](solution/SECURITY_AND_OPERATIONS.md).

## Контекст для сопровождения

Вместе с кодом публикуются исходные требования, база знаний, правила работы и
результаты проверок. Начните с [`START_HERE.md`](START_HERE.md).
Агент может использовать эти материалы и код для объяснения реализации и помощи
в сопровождении; фактическое поведение следует сверять с текущим кодом и тестами.

Для работы с маршрутизатором контекста:

```bash
npm ci
npm run context:index
npm run context:doctor
```

Исходные записи маршрутизатора находятся в [`.project-context/`](.project-context/README.md).
Локальные окружения, кэши, секреты и ZIP-сборки в репозиторий не включаются.

## База знаний для сбора требований к проекту (хакатон)

Структурированное хранилище для сбора, извлечения и подготовки требований к проекту в рамках хакатона.

## Структура

```
.
├── RAW/                  # Исходные материалы (необработанные данные)
├── database/             # Извлеченные знания (требования к системе)
├── hackathon_database/   # База знаний хакатона (регламент, правила, инструкции)
├── COOKED/               # Подготовленные документы (готовые артефакты)
└── playbooks/            # Инструкции и регламенты процессов
```

## Назначение папок

### RAW/
Исходные материалы в первозданном виде: заметки, скриншоты, тексты, ссылки, файлы от заказчика/команды. Ничего не редактируется и не структурируется.

### database/
Извлеченные из RAW знания о самой системе: структурированные требования, сущности, термины, вопросы. Результат анализа исходников.

### hackathon_database/
База знаний о проведении хакатона: правила, регламент, инструкции, критерии оценки. Отделена от требований к самой системе.

### COOKED/
Подготовленные документы: итоговые спецификации, презентации, чек-листы, готовые к использованию артефакты.

### playbooks/
Инструкции и регламенты: как собирать требования, как обрабатывать RAW, как готовить COOKED.

## Поток данных

```
RAW ──(извлечение)──> database ──(подготовка)──> COOKED
```

## Начало работы

Начни с `START_HERE.md` — порядок работы и точки входа для нового агента.

## Правила

- Требования не выдумываются — только извлекаются из исходных материалов.
- Каждый артефакт сопровождается README с описанием содержимого.

```

## .project-context/README.md

```
# Хакатон — модуль безопасности персональных данных project context

This directory is the tracked source of truth for project-context records and routing configuration.

- Edit `project.yaml` to define real modules, aliases, source globs, playbooks, and verification commands.
- Keep reviewed durable records under `active/`.
- Keep generated drafts and SQLite indexes untracked.
- Confirm Task Contracts before implementation and record verification before finalization.

```

## .project-context/project.yaml

```
project:
  name: "Хакатон — модуль безопасности персональных данных"
  repository: "Архив"
  context_version: 1
  timezone: Europe/Moscow
  purpose: "Сбор требований и разработка модуля поиска, маскирования и восстановления конфиденциальной информации для хакатона."
  roles: [Analyst, Developer]
  flows:
    - Validate or derive a task contract before implementation.
    - Build a context pack and inspect existing capabilities.
    - Run applicable verification and finalize the work.
routing:
  default_modules: ["solution"]
  documentation_modules: ["requirements", "hackathon", "sources", "specifications", "project_rules"]
context_router:
  cli_command: npx project-context
  mcp_server_name: project_context
  resource_scheme: project-context
  codex_config_path: .codex/config.toml
  codex_hooks_path: false
  git_hooks_path: false
  brand:
    name: Project Context Router
    short_name: Project Context
    marker: PROJECT_CONTEXT
    logo_text: "[Project Context]"
    description: local-first project memory, backlog, and verification router
modules: 
  solution:
    path: "solution"
    aliases: ["solution"]
    source_globs: ["solution/**/*.{ts,tsx,js,jsx,mjs,cjs,java,kt,kts,go,rs,py,rb,php,cs,sql,xml,yaml,yml,md}"]
    playbooks: [playbooks/prepare_developer_tasks.md, playbooks/create_acceptance_checklist.md, playbooks/process_test_results.md]
  requirements:
    path: "database"
    aliases: ["requirements"]
    source_globs: ["database/**/*.{ts,tsx,js,jsx,mjs,cjs,java,kt,kts,go,rs,py,rb,php,cs,sql,xml,yaml,yml,md}"]
    playbooks: [playbooks/manage_requirements.md, playbooks/maintain_data_dictionary.md, playbooks/maintain_glossary.md, playbooks/maintain_traceability.md, playbooks/resolve_questions.md]
  hackathon:
    path: "hackathon_database"
    aliases: ["hackathon"]
    source_globs: ["hackathon_database/**/*.{ts,tsx,js,jsx,mjs,cjs,java,kt,kts,go,rs,py,rb,php,cs,sql,xml,yaml,yml,md}"]
    playbooks: [playbooks/process_source.md, playbooks/resolve_questions.md]
  sources:
    path: "RAW"
    aliases: ["sources"]
    source_globs: ["RAW/**/*.{txt,yaml,yml,md}"]
    playbooks: [playbooks/process_source.md]
  specifications:
    path: "COOKED"
    aliases: ["specifications"]
    source_globs: ["COOKED/**/*.{ts,tsx,js,jsx,mjs,cjs,java,kt,kts,go,rs,py,rb,php,cs,sql,xml,yaml,yml,md}"]
    playbooks: [playbooks/manage_requirements.md, playbooks/maintain_traceability.md]
  project_rules:
    path: "."
    aliases: ["rules", "playbooks", "project-context"]
    source_globs: ["AGENTS.md", "START_HERE.md", "PROJECT.yaml", "playbooks/**/*.md"]
    playbooks: [playbooks/README.md]
commands:
  context_lint:
    run: npx project-context lint
    required_for: [solution, requirements, hackathon, sources, specifications, project_rules]
    context_pack: true
  context_index:
    run: npx project-context index
    required_for: [solution, requirements, hackathon, sources, specifications, project_rules]
  context_doctor:
    run: npx project-context doctor --json
    required_for: [solution, requirements, hackathon, sources, specifications, project_rules]

```

## scripts/import-project-context.mjs

```
import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { basename, extname, join, relative, resolve } from "node:path";

const root = process.cwd();
const activeRoot = resolve(root, ".project-context", "active");
const importedAt = new Date().toISOString();

const roots = ["RAW", "database", "hackathon_database", "COOKED", "playbooks"];
const rootFiles = ["AGENTS.md", "START_HERE.md", "PROJECT.yaml"];
const allowedExtensions = new Set([".md", ".txt", ".yaml", ".yml"]);

function walk(path) {
  if (!existsSync(path)) return [];
  const entries = readdirSync(path, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const child = join(path, entry.name);
    if (entry.isDirectory()) return walk(child);
    if (!entry.isFile() || !allowedExtensions.has(extname(entry.name).toLowerCase())) return [];
    return [child];
  });
}

function yamlString(value) {
  return JSON.stringify(value);
}

function yamlArray(values) {
  return `[${values.map(yamlString).join(", ")}]`;
}

function moduleFor(path) {
  if (path.startsWith("RAW/")) return "sources";
  if (path.startsWith("database/")) return "requirements";
  if (path.startsWith("hackathon_database/")) return "hackathon";
  if (path.startsWith("COOKED/")) return "specifications";
  return "project_rules";
}

function tagsFor(path) {
  const tags = ["imported", "project-memory", moduleFor(path)];
  if (/transcript|\u0421\u0435\u0433\u043e\u0434\u043d\u044f_/iu.test(path)) tags.push("transcript");
  if (/requirements|specification|database\//iu.test(path)) tags.push("requirements");
  if (/hackathon_database|rules_and_regulations|instructions|evaluation_criteria/iu.test(path)) {
    tags.push("hackathon-regulations");
  }
  if (/playbooks|AGENTS\.md|START_HERE\.md/iu.test(path)) tags.push("workflow-rules");
  return [...new Set(tags)];
}

function firstHeading(content, path) {
  const heading = content.match(/^#{1,3}\s+(.+)$/mu)?.[1]?.trim();
  if (heading) return heading.slice(0, 180);
  const firstLine = content.split(/\r?\n/u).find((line) => line.trim())?.trim();
  return (firstLine || basename(path)).slice(0, 180);
}

function stableNumber(path, used) {
  const digest = createHash("sha256").update(path).digest();
  let value = digest.readUInt32BE(0) % 1000;
  while (used.has(value)) value = (value + 1) % 1000;
  used.add(value);
  return String(value).padStart(3, "0");
}

function classify(path) {
  if (/^(database|hackathon_database)\/chunks\/CH-[^/]+\.md$/u.test(path)) {
    return { type: "source_chunk", segment: "source-chunks", prefix: "SOURCE-CHUNK" };
  }
  if (path === "COOKED/requirements/current_specification.md") {
    return { type: "requirement", segment: "requirements", prefix: "REQUIREMENT" };
  }
  return { type: "source", segment: "sources", prefix: "SOURCE" };
}

function renderRecord(path, content, id, classification) {
  const moduleName = moduleFor(path);
  const tags = tagsFor(path);
  const title = firstHeading(content, path);
  const lines = [
    "---",
    `id: ${yamlString(id)}`,
    `type: ${yamlString(classification.type)}`,
    `status: "active"`,
    `title: ${yamlString(title)}`,
    `created_at: ${yamlString(importedAt)}`,
    `updated_at: ${yamlString(importedAt)}`,
    `retention: "keep"`,
    `modules: ${yamlArray([moduleName])}`,
    `files: ${yamlArray([path])}`,
    `tags: ${yamlArray(tags)}`,
    `source_refs: ${yamlArray([path])}`,
  ];

  if (classification.type === "source_chunk") {
    const chunkId = basename(path, extname(path));
    const sourceId = content.match(/^\s*\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a:\s*([^\n]+)$/imu)?.[1]?.trim() || "unknown";
    const topic = content.match(/^\s*\u0442\u0435\u043c\u0430:\s*([^\n]+)$/imu)?.[1]?.trim() || title;
    lines.push(`chunk_id: ${yamlString(chunkId)}`);
    lines.push(`source_id: ${yamlString(sourceId)}`);
    lines.push(`topic: ${yamlString(topic)}`);
    lines.push(`system_area: ${yamlString(moduleName)}`);
    lines.push(`information_type: "curated-project-knowledge"`);
    lines.push(`knowledge_status: "reviewed"`);
  } else if (classification.type === "source") {
    lines.push(`source_id: ${yamlString(path)}`);
    lines.push(`source_path: ${yamlString(path)}`);
    lines.push(`source_kind: ${yamlString(extname(path).slice(1) || "document")}`);
    lines.push(`processed_status: "imported"`);
  }

  lines.push("---", "", `> Imported from \`${path}\`. The original file remains the source of truth.`, "", content.trim(), "");
  return lines.join("\n");
}

const candidates = [
  ...roots.flatMap((directory) => walk(resolve(root, directory))),
  ...rootFiles.map((path) => resolve(root, path)).filter((path) => existsSync(path) && statSync(path).isFile()),
]
  .map((path) => relative(root, path).replaceAll("\\", "/"))
  .sort((left, right) => left.localeCompare(right, "ru"));

const usedByPrefix = new Map();
const counts = new Map();

for (const path of candidates) {
  const classification = classify(path);
  const used = usedByPrefix.get(classification.prefix) || new Set();
  usedByPrefix.set(classification.prefix, used);
  const number = stableNumber(path, used);
  const id = `${classification.prefix}-20260923-${number}`;
  const targetDir = resolve(activeRoot, classification.segment);
  const target = resolve(targetDir, `${id}.md`);
  const content = readFileSync(resolve(root, path), "utf8");
  mkdirSync(targetDir, { recursive: true });
  writeFileSync(target, renderRecord(path, content, id, classification), "utf8");
  counts.set(classification.type, (counts.get(classification.type) || 0) + 1);
}

const summary = Object.fromEntries([...counts.entries()].sort(([left], [right]) => left.localeCompare(right)));
console.log(JSON.stringify({ status: "IMPORTED", files: candidates.length, records: summary }, null, 2));

```

## node_modules/mcp-project-context-router/README.md

```
# Project Context Router

[![CI](https://github.com/ukolov-dev/mcp-project-context-router/actions/workflows/ci.yml/badge.svg)](https://github.com/ukolov-dev/mcp-project-context-router/actions/workflows/ci.yml)
[![Node.js 22.13+](https://img.shields.io/badge/Node.js-22.13%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-server-5A67D8)](https://modelcontextprotocol.io/)

A local-first CLI and [Model Context Protocol](https://modelcontextprotocol.io/)
server that gives coding agents structured project memory, task contracts, compact
context packs, backlog workflows, and verification evidence.

The router keeps durable knowledge in reviewable Markdown and YAML inside the
consumer repository. A disposable SQLite index makes retrieval fast without
turning an external service into the source of truth.

> Status: active development. The current package is
> `mcp-project-context-router@0.5.0`, requires Node.js 22.13 or newer, and is distributed
> from source or a versioned tarball. It is not currently published to an npm
> registry.

See the [changelog](CHANGELOG.md) and [GitHub releases](https://github.com/ukolov-dev/mcp-project-context-router/releases)
for versioned changes and installable tarballs.

## Why use it?

- Keep project memory versioned beside the code that it describes.
- Give agents a focused context pack instead of an unbounded repository dump.
- Validate and confirm a Task Contract before implementation begins.
- Search existing capabilities before adding duplicate code.
- Track backlog state, dependencies, decisions, and verification evidence.
- Expose the same workflow through a human-friendly CLI and MCP tools.
- Keep generated drafts and indexes out of version control and package artifacts.

## Quick start

Install directly from GitHub in the repository that should own the project
context:

```bash
npm install --save-dev --save-exact github:ukolov-dev/mcp-project-context-router
npx project-context init --name "Example Project" --module app:src
npx project-context index
npx project-context doctor --json
```

`init` is non-destructive: it does not overwrite an existing configuration.
Review `.project-context/project.yaml` after generation and replace the example
modules, source globs, playbooks, and verification commands with real project
values.

A typical agent workflow then looks like this:

```bash
npx project-context validate-task "Add CSV export" --mode feature
npx project-context pack "Add CSV export" --workflow standard --explain
npx project-context reuse-scan "CSV export"
npx project-context verify-task "CSV export"
```

Run `npx project-context --help` for the complete CLI surface.

## Connect your coding agent

The package includes client-specific setup guides and copy-ready configuration
templates:

| Client | Setup guide | Configuration template |
| --- | --- | --- |
| Codex desktop, CLI, and IDE | [Install for Codex](docs/install/codex.md) | [`templates/client-configs/codex.toml`](templates/client-configs/codex.toml) |
| OpenCode stable | [Install for OpenCode](docs/install/opencode.md) | [`templates/client-configs/opencode.json`](templates/client-configs/opencode.json) |
| OpenCode V2 preview | [OpenCode V2 notes](docs/install/opencode.md#opencode-v2-preview) | [`templates/client-configs/opencode-v2.json`](templates/client-configs/opencode-v2.json) |

A complete Russian-language OpenCode guide is also available:
[Использование в OpenCode](docs/install/opencode.ru.md). The Russian
[workflow and artifact guide](docs/workflow.ru.md) explains what is created at
each task stage and what an agent receives before implementation.

All three configurations start the same local stdio MCP server from the consumer
repository. They contain no credentials or workstation-specific absolute paths.
Codex uses `.codex/config.toml`; OpenCode uses `opencode.json` at the repository
root. The two OpenCode schemas are intentionally separate because stable and V2
currently use different MCP nesting and enablement fields.

The server supports scoped tool profiles:

| Profile | Intended use |
| --- | --- |
| `core` | Task contracts, context packs, reuse scans, verification, refactor review, and finalization |
| `developer` | `core` plus assigned-work acceptance and implementation reports |
| `analyst` | `core` plus requirements, source traceability, analyst packs, and Confluence publishing |
| `admin` | `core` plus backlog lifecycle, promotion, retention, and decision management |
| `full` | The complete compatibility surface |

`core` is the default. The legacy `PPM_CONTEXT_TOOL_PROFILE` variable remains
supported for compatibility.

## How data is laid out

```text
.project-context/
├── project.yaml       # routing, modules, commands, and project identity
├── active/            # reviewed, durable project records
├── drafts/            # reviewable generated proposals (ignored)
├── indexes/           # rebuildable SQLite/cache data (ignored)
└── templates/         # Task Contract and Verification Record templates
```

Project data belongs to the consumer repository, not to this package. The
configuration routes queries to modules and playbooks; the index adds fast
retrieval; the CLI and MCP server apply the same workflow and repository-boundary
checks.

## Task execution

Confirmed tasks can have execution manifests, evidence-gated states, and a
separate acceptance review. An optional `project-context run TASK-ID --adapter
execution-adapter.json` command previews external implementation and review
commands; `--execute` runs the workflow in the current checkout. See the
[execution guide](docs/execution.md) for the adapter protocol, CLI/MCP tools,
verification gates, and retry behavior.

## Safety model

- Repository-boundary and symlink-escape checks reject paths outside the project.
- Secret-like values are redacted from generated excerpts.
- Credentials are read from environment variables or supported native credential
  stores and are never written into exported project context.
- Indexes, drafts, trash, build outputs, and local environment files are ignored.
- The npm package allowlist excludes source-project records, credentials, source
  TypeScript, tests, and generated SQLite databases.
- Network integrations such as Confluence and Context Hub are optional and require
  explicit project configuration and credentials.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Develop locally

```bash
git clone https://github.com/ukolov-dev/mcp-project-context-router.git
cd mcp-project-context-router
npm ci
npm run build
npm test
npm run package:check
node bin/project-context doctor --json
```

To exercise the installable artifact locally:

```bash
mkdir -p artifacts
npm pack --pack-destination ./artifacts
```

The tarball contains compiled runtime code, launchers, hooks, credential helper
scripts, installation guides, consumer templates, and this README. It excludes
`.project-context`, `.codex`, tests, source TypeScript, generated indexes, and
`node_modules`.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a change. The required
handoff checks are `npm run build`, `npm test`, `npm run package:check`, and
`node bin/project-context doctor --json`.

## License

No open-source license has been granted yet. The package is marked `UNLICENSED`;
public availability of the source does not grant permission to copy, modify, or
redistribute it.

```
