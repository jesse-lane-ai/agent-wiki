import { copyFileSync, existsSync, mkdirSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CONFIG_PATH, DEFAULT_WORKSPACE_WIKI_DIR, VALID_WIKI_TYPES, WikiType, cleanWikiDir, readJsonObject } from "./config.js";

export const CONTENT_FOLDERS = ["sources", "sources/parts", "entities", "concepts", "claims", "syntheses", "questions", "_attachments", "_archive"];
export const VAULT_RUNTIME_FOLDERS = ["_inbox", "_inbox/trash", "raw"];
export const GENERATED_FOLDERS = ["reports", "_system/cache", "_system/indexes", "_system/logs", "_system/state"];
export const SYSTEM_FOLDERS = ["skills"];
export const REQUIRED_TEMPLATE_FILES = [
  "AGENTS.md",
  "WIKI.md",
  "README.md",
  "skills/compile-wiki/SKILL.md",
  "skills/extract-knowledge-primitives/SKILL.md"
];
export const TEMPLATE_ROOT_FILES = ["AGENTS.md", "WIKI.md", "README.md", "ONBOARD.md", "INBOX.md", "AGENT-WIKI-SPEC-v2.md"];
export const TEMPLATE_DIRECTORIES = ["skills"];
export const TEMPLATE_OPTIONAL_FILES = ["_system/config.example.json"];

export interface InitResult {
  wikiType: WikiType;
  workspaceRoot: string | null;
  wikiRoot: string;
  created: string[];
  configWritten: boolean;
  templateCopied: string[];
}

export interface DoctorIssue {
  level: "error" | "warning" | "info";
  code: string;
  message: string;
  path?: string;
}

export function resolveInitPaths(options: {
  wikiType: string;
  root?: string;
  workspaceRoot?: string;
  wikiDir?: string;
}): { workspaceRoot: string | null; wikiRoot: string } {
  if (!VALID_WIKI_TYPES.has(options.wikiType)) {
    throw new Error(`wiki_type must be one of: ${Array.from(VALID_WIKI_TYPES).sort().join(", ")}`);
  }
  const wikiDir = cleanWikiDir(options.wikiDir ?? DEFAULT_WORKSPACE_WIKI_DIR);
  if (options.wikiType === "workspace") {
    const workspace = resolve(options.workspaceRoot ?? options.root ?? ".");
    return { workspaceRoot: workspace, wikiRoot: resolve(workspace, wikiDir) };
  }
  return { workspaceRoot: null, wikiRoot: resolve(options.root ?? ".") };
}

export function initWiki(options: {
  wikiType: WikiType;
  root?: string;
  workspaceRoot?: string;
  wikiDir?: string;
  writeConfig?: boolean;
  withTemplate?: boolean;
  templateRoot?: string;
}): InitResult {
  const { workspaceRoot, wikiRoot } = resolveInitPaths(options);
  const created = createRequiredFolders(wikiRoot);
  let configWritten = false;
  if (options.writeConfig) {
    writeLocalConfig(wikiRoot, options.wikiType, workspaceRoot, options.wikiDir ?? DEFAULT_WORKSPACE_WIKI_DIR);
    configWritten = true;
  }
  const templateCopied = options.withTemplate
    ? copyTemplateFiles(options.templateRoot ?? defaultTemplateRoot(), wikiRoot)
    : [];
  return { wikiType: options.wikiType, workspaceRoot, wikiRoot, created, configWritten, templateCopied };
}

export function createRequiredFolders(wikiRoot: string): string[] {
  const folders = [...CONTENT_FOLDERS, ...VAULT_RUNTIME_FOLDERS, ...GENERATED_FOLDERS, ...SYSTEM_FOLDERS];
  const created: string[] = [];
  for (const folder of folders) {
    const path = join(wikiRoot, folder);
    if (!existsSync(path)) {
      mkdirSync(path, { recursive: true });
      created.push(path);
    }
  }
  return created;
}

export function writeLocalConfig(wikiRoot: string, wikiType: WikiType, workspaceRoot: string | null, wikiDir: string): void {
  const configPath = join(wikiRoot, CONFIG_PATH);
  mkdirSync(dirname(configPath), { recursive: true });
  const existing = readJsonObject(configPath) ?? {};
  existing.schemaVersion = 1;
  existing.wikiType = wikiType;
  const workspace = typeof existing.workspace === "object" && existing.workspace !== null && !Array.isArray(existing.workspace)
    ? existing.workspace as Record<string, unknown>
    : {};
  workspace.root = workspaceRoot;
  workspace.wikiDir = cleanWikiDir(wikiDir);
  existing.workspace = workspace;
  writeFileSync(configPath, `${JSON.stringify(existing, null, 2)}\n`, "utf8");
}

export function defaultTemplateRoot(): string {
  return resolve(dirname(fileURLToPath(import.meta.url)), "../..");
}

export function copyTemplateFiles(sourceRoot: string, wikiRoot: string): string[] {
  const copied: string[] = [];
  for (const name of [...TEMPLATE_ROOT_FILES, ...TEMPLATE_OPTIONAL_FILES]) {
    const source = join(sourceRoot, name);
    if (existsSync(source) && statSync(source).isFile() && copyFileIfMissing(source, join(wikiRoot, name))) {
      copied.push(join(wikiRoot, name));
    }
  }
  for (const name of TEMPLATE_DIRECTORIES) {
    const source = join(sourceRoot, name);
    if (existsSync(source) && statSync(source).isDirectory()) {
      copied.push(...copyTreeIfMissing(source, join(wikiRoot, name)));
    }
  }
  return copied;
}

export function doctorWiki(wikiRoot: string, wikiType?: string): DoctorIssue[] {
  const root = resolve(wikiRoot);
  if (!existsSync(root)) {
    return [{ level: "error", code: "wiki_root_missing", message: "Wiki root does not exist.", path: root }];
  }
  if (!statSync(root).isDirectory()) {
    return [{ level: "error", code: "wiki_root_not_directory", message: "Wiki root is not a directory.", path: root }];
  }
  const config = readJsonObject(join(root, CONFIG_PATH));
  const detectedType = wikiType ?? detectWikiType(config);
  const issues: DoctorIssue[] = [];
  if (!VALID_WIKI_TYPES.has(detectedType)) {
    issues.push({ level: "error", code: "invalid_wiki_type", message: `Invalid wiki type: ${detectedType}` });
  }
  for (const folder of requiredFoldersForDoctor(detectedType)) {
    const path = join(root, folder);
    if (!existsSync(path) || !statSync(path).isDirectory()) {
      issues.push({ level: "error", code: "missing_folder", message: `Required folder is missing: ${folder}`, path });
    }
  }
  for (const fileName of REQUIRED_TEMPLATE_FILES) {
    const path = join(root, fileName);
    if (!existsSync(path) || !statSync(path).isFile()) {
      issues.push({ level: "warning", code: "missing_template_file", message: `Template file is missing: ${fileName}`, path });
    }
  }
  if (config === null) {
    issues.push({
      level: "info",
      code: "local_config_missing",
      message: "_system/config.json is not present; defaults or _system/config.example.json will be used.",
      path: join(root, CONFIG_PATH)
    });
  } else if (!VALID_WIKI_TYPES.has(String(config.wikiType))) {
    issues.push({ level: "error", code: "config_invalid_wiki_type", message: "_system/config.json has missing or invalid wikiType.", path: join(root, CONFIG_PATH) });
  }
  return issues;
}

export function requiredFoldersForDoctor(wikiType: string | null | undefined): string[] {
  return [...CONTENT_FOLDERS, ...VAULT_RUNTIME_FOLDERS, ...GENERATED_FOLDERS, ...SYSTEM_FOLDERS];
}

export function detectWikiType(config: Record<string, unknown> | null): WikiType {
  return config && VALID_WIKI_TYPES.has(String(config.wikiType)) ? String(config.wikiType) as WikiType : "vault";
}

export function issuesToJson(issues: DoctorIssue[]): string {
  return JSON.stringify(issues, null, 2);
}

export function issuesToText(issues: DoctorIssue[]): string {
  if (issues.length === 0) {
    return "Doctor passed: no issues found.";
  }
  return issues.map(formatIssue).join("\n");
}

function formatIssue(issue: DoctorIssue): string {
  const suffix = issue.path ? ` (${issue.path})` : "";
  return `${issue.level.toUpperCase().padEnd(7)} ${issue.code}: ${issue.message}${suffix}`;
}

function copyTreeIfMissing(source: string, destination: string): string[] {
  const copied: string[] = [];
  for (const entry of readdirSync(source, { withFileTypes: true })) {
    const sourcePath = join(source, entry.name);
    const destinationPath = join(destination, entry.name);
    if (entry.isDirectory()) {
      copied.push(...copyTreeIfMissing(sourcePath, destinationPath));
    } else if (!shouldSkipTemplateFile(relative(source, sourcePath)) && copyFileIfMissing(sourcePath, destinationPath)) {
      copied.push(destinationPath);
    }
  }
  return copied;
}

function shouldSkipTemplateFile(path: string): boolean {
  return path.split(/[\\/]/).includes("__pycache__") || path.endsWith(".pyc");
}

function copyFileIfMissing(source: string, destination: string): boolean {
  if (existsSync(destination)) {
    return false;
  }
  mkdirSync(dirname(destination), { recursive: true });
  copyFileSync(source, destination);
  return true;
}
