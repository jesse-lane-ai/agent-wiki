import { copyFileSync, cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { compileWiki } from "./compile.js";
import { renderIndexCommand } from "./catalog.js";
import { detectWikiType, doctorWiki, requiredFoldersForDoctor, writeLocalConfig } from "./lifecycle.js";
import { readJsonObject } from "./config.js";
import { writeJson } from "./wiki-utils.js";

interface MigrationAction {
  action: "remove" | "rewrite" | "copy" | "mkdir" | "doctor" | "compile" | "index";
  path?: string;
  message: string;
}

const OBSOLETE_PATHS = [
  "pyproject.toml",
  "agent_wiki",
  "_system/scripts/create-page.py",
  "_system/scripts/index.py",
  "_system/scripts/log.py",
  "_system/scripts/migrate-refs-to-links.py",
  "_system/scripts/onboard.py",
  "_system/skills/compile-wiki/scripts/compile.py",
  "_system/skills/import-link/scripts/uuid.py",
  "skills/compile-wiki/scripts/compile.py",
  "skills/import-link/scripts/uuid.py",
  "tests/e2e_smoke.py",
  "tests/test_lifecycle.py",
  "tests/test_onboard.py",
  "tests/test_workspace.py"
];

const TEMPLATE_FILES = [
  "AGENTS.md",
  "WIKI.md",
  "README.md",
  "ONBOARD.md",
  "INBOX.md",
  "AGENT-WIKI-SPEC-v2.md",
  "_system/config.example.json"
];

const TEMPLATE_DIRS = ["skills"];

const REWRITES: Array<[RegExp, string]> = [
  [/AGENT-WIKI-SPEC-v1\.md/g, "AGENT-WIKI-SPEC-v2.md"],
  [/AGENT-WIKI-SPEC-v1/g, "AGENT-WIKI-SPEC-v2"],
  [/python3 -m agent_wiki\.cli/g, "agent-wiki"],
  [/python -m agent_wiki\.cli/g, "agent-wiki"],
  [/python3 _system\/scripts\/create-page\.py/g, "agent-wiki create-page"],
  [/python _system\/scripts\/create-page\.py/g, "agent-wiki create-page"],
  [/_system\/scripts\/create-page\.py/g, "agent-wiki create-page"],
  [/create-page\.py/g, "agent-wiki create-page"],
  [/python3 _system\/scripts\/onboard\.py/g, "agent-wiki onboard"],
  [/python _system\/scripts\/onboard\.py/g, "agent-wiki onboard"],
  [/_system\/scripts\/onboard\.py/g, "agent-wiki onboard"],
  [/python3 _system\/scripts\/log\.py/g, "agent-wiki log"],
  [/python _system\/scripts\/log\.py/g, "agent-wiki log"],
  [/_system\/scripts\/log\.py/g, "agent-wiki log"],
  [/python3 _system\/scripts\/index\.py/g, "agent-wiki index"],
  [/python _system\/scripts\/index\.py/g, "agent-wiki index"],
  [/_system\/scripts\/index\.py/g, "agent-wiki index"],
  [/python3 _system\/scripts\/migrate-refs-to-links\.py/g, "agent-wiki migrate-refs-to-links"],
  [/python _system\/scripts\/migrate-refs-to-links\.py/g, "agent-wiki migrate-refs-to-links"],
  [/_system\/scripts\/migrate-refs-to-links\.py/g, "agent-wiki migrate-refs-to-links"],
  [/python3 skills\/compile-wiki\/scripts\/compile\.py/g, "agent-wiki compile"],
  [/python skills\/compile-wiki\/scripts\/compile\.py/g, "agent-wiki compile"],
  [/_system\/skills\/compile-wiki\/scripts\/compile\.py/g, "agent-wiki compile"],
  [/skills\/compile-wiki\/scripts\/compile\.py/g, "agent-wiki compile"],
  [/skills\/import-link\/scripts\/uuid\.py/g, "agent-wiki uuid"],
  [/_system\/skills\/import-link\/scripts\/uuid\.py/g, "agent-wiki uuid"],
  [/scripts\/uuid\.py/g, "agent-wiki uuid"]
];

export function migrateWiki(args: Record<string, unknown>): number {
  const from = String(args.from ?? "");
  const check = Boolean(args.check);
  const write = Boolean(args.write);
  if (from !== "v1") throw new Error("migrate requires --from v1");
  if (check === write) throw new Error("migrate requires exactly one of --check or --write");

  const root = process.cwd();
  const templateRoot = fileURLToPath(new URL("../..", import.meta.url));
  const actions = planMigration(root, templateRoot);
  const summary = {
    schemaVersion: 1,
    migration: "v1-to-v2",
    mode: check ? "check" : "write",
    root,
    actions,
    counts: countActions(actions)
  };

  if (write) {
    const backupRoot = join(root, "_archive/migrations/v1-to-v2", timestamp());
    mkdirSync(backupRoot, { recursive: true });
    for (const action of actions) {
      if (action.action === "remove" && action.path) {
        backupPath(root, backupRoot, action.path);
        rmSync(join(root, action.path), { recursive: true, force: true });
      } else if (action.action === "rewrite" && action.path) {
        backupPath(root, backupRoot, action.path);
        writeFileSync(join(root, action.path), rewriteText(readFileSync(join(root, action.path), "utf8")), "utf8");
      } else if (action.action === "copy" && action.path) {
        copyTemplatePath(templateRoot, root, action.path);
      } else if (action.action === "mkdir" && action.path) {
        mkdirSync(join(root, action.path), { recursive: true });
      }
    }
    writeLocalConfig(root, detectWikiType(readJsonObject(join(root, "_system/config.json"))), null, "wiki");
    writeJson(join(backupRoot, "migration-summary.json"), summary);
    const doctorIssues = doctorWiki(root);
    const originalLog = console.log;
    try {
      console.log = () => undefined;
      compileWiki({});
      renderIndexCommand({ write: true, "no-log": true });
    } finally {
      console.log = originalLog;
    }
    summary.actions.push({ action: "doctor", message: `doctor completed with ${doctorIssues.length} issue(s)` });
    summary.actions.push({ action: "compile", message: "compile completed" });
    summary.actions.push({ action: "index", message: "index completed" });
  }

  console.log(JSON.stringify(summary, null, 2));
  return 0;
}

function planMigration(root: string, templateRoot: string): MigrationAction[] {
  const actions: MigrationAction[] = [];
  for (const path of OBSOLETE_PATHS) {
    if (existsSync(join(root, path))) actions.push({ action: "remove", path, message: `Remove obsolete Python-era path: ${path}` });
  }
  if (isCopiedAgentWikiPackage(join(root, "package.json"))) {
    actions.push({ action: "remove", path: "package.json", message: "Remove copied Agent Wiki npm package metadata from wiki root" });
  }
  const wikiType = detectWikiType(readJsonObject(join(root, "_system/config.json")));
  for (const path of requiredFoldersForDoctor(wikiType)) {
    if (!existsSync(join(root, path))) actions.push({ action: "mkdir", path, message: `Create missing required folder: ${path}` });
  }
  for (const path of [...TEMPLATE_FILES, ...templateFiles(templateRoot, TEMPLATE_DIRS)]) {
    if (!existsSync(join(root, path))) actions.push({ action: "copy", path, message: `Copy missing v2 template file: ${path}` });
  }
  for (const path of rewriteCandidateFiles(root)) {
    const text = readFileSync(join(root, path), "utf8");
    if (rewriteText(text) !== text) actions.push({ action: "rewrite", path, message: `Rewrite old helper command references in ${path}` });
  }
  return actions.sort((a, b) => `${a.action}:${a.path ?? ""}`.localeCompare(`${b.action}:${b.path ?? ""}`));
}

function isCopiedAgentWikiPackage(path: string): boolean {
  const packageJson = readJsonObject(path);
  if (!packageJson) return false;
  const name = String(packageJson.name ?? "");
  return name === "@creativeaitools/agent-wiki" || name === "@jesse-lane-ai/agent-wiki" || name === "agent-wiki";
}

function rewriteCandidateFiles(root: string): string[] {
  const dirs = [".", "skills", "_system/skills"];
  const files: string[] = [];
  for (const dir of dirs) collectMarkdown(root, dir, files);
  return Array.from(new Set(files)).sort();
}

function collectMarkdown(root: string, dir: string, files: string[]): void {
  const full = join(root, dir);
  if (!existsSync(full) || !statSync(full).isDirectory()) return;
  for (const entry of readdirSync(full, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || ["node_modules", "dist", "_system", "_archive"].includes(entry.name)) continue;
    const rel = dir === "." ? entry.name : join(dir, entry.name);
    const path = join(root, rel);
    if (entry.isDirectory()) collectMarkdown(root, rel, files);
    else if (entry.isFile() && /\.(md|json)$/i.test(entry.name)) files.push(rel.split("\\").join("/"));
  }
}

function rewriteText(text: string): string {
  return REWRITES.reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), text);
}

function templateFiles(templateRoot: string, dirs: string[]): string[] {
  const files: string[] = [];
  for (const dir of dirs) collectAllFiles(templateRoot, dir, files);
  return files;
}

function collectAllFiles(root: string, dir: string, files: string[]): void {
  const full = join(root, dir);
  if (!existsSync(full) || !statSync(full).isDirectory()) return;
  for (const entry of readdirSync(full, { withFileTypes: true })) {
    const rel = join(dir, entry.name);
    if (entry.isDirectory()) collectAllFiles(root, rel, files);
    else if (entry.isFile()) files.push(rel.split("\\").join("/"));
  }
}

function copyTemplatePath(templateRoot: string, root: string, path: string): void {
  const source = join(templateRoot, path);
  const destination = join(root, path);
  mkdirSync(dirname(destination), { recursive: true });
  copyFileSync(source, destination);
}

function backupPath(root: string, backupRoot: string, path: string): void {
  const source = join(root, path);
  if (!existsSync(source)) return;
  const destination = join(backupRoot, path);
  mkdirSync(dirname(destination), { recursive: true });
  if (statSync(source).isDirectory()) {
    cpSync(source, destination, { recursive: true });
  } else {
    copyFileSync(source, destination);
  }
}

function countActions(actions: MigrationAction[]): Record<string, number> {
  return actions.reduce((counts, action) => {
    counts[action.action] = (counts[action.action] ?? 0) + 1;
    return counts;
  }, {} as Record<string, number>);
}

function timestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, "-");
}
