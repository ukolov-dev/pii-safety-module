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

if (existsSync(resolve(root, ".project-context", "source-map.json"))) {
  throw new Error("В публичной версии источники уже объединены с .project-context/active. Используйте context:index; context:import предназначен для исходного рабочего архива.");
}

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
