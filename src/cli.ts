#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { loadConfig } from "./config.js";
import { renderIndexCommand } from "./catalog.js";
import { compileWiki } from "./compile.js";
import { doctorWiki, initWiki, issuesToJson, issuesToText } from "./lifecycle.js";
import { migrateRefs } from "./migrate.js";
import { buildOnboardingReport, onboard } from "./onboard.js";
import { createPage } from "./page.js";
import { migrateWiki } from "./upgrade.js";
import { writeOperationalLog } from "./wiki-utils.js";
import { randomBytes } from "node:crypto";
import { addRegistryEntry, getRegistryEntry, listRegistryEntries, registryPath, removeRegistryEntry } from "./registry.js";
import {
  defaultWorkspaceRoot,
  filesToJson,
  filesToText,
  loadState,
  markSourced,
  scanWorkspace,
  updateStateFromScan,
  wikiRootForWorkspace
} from "./workspace.js";

interface Args {
  _: string[];
  [key: string]: string | boolean | string[] | undefined;
}

export function main(argv = process.argv.slice(2)): number {
  try {
    const global = parseArgs(argv);
    const command = global._[0];
    if (!command || global.help) {
      printHelp();
      return global.help ? 0 : 2;
    }
    const wikiRoot = resolveWikiRoot(global);
    if (command === "list") return cmdList(global);
    if (command === "registry") return cmdRegistry(global);
    if (command === "check") return cmdCheck(global);
    if (command === "init") return cmdInit(global);
    if (command === "doctor") return cmdDoctor(global, wikiRoot);
    if (command === "workspace") return withWikiRoot(wikiRoot, () => cmdWorkspace(global));
    if (command === "create-page") return withWikiRoot(wikiRoot, () => createPage(global));
    if (command === "onboard") return onboard({ ...global, "wiki-root": wikiRoot ?? global["wiki-root"] });
    if (command === "index") return withWikiRoot(wikiRoot, () => renderIndexCommand(global));
    if (command === "log") return withWikiRoot(wikiRoot, () => cmdLog(global));
    if (command === "migrate-refs-to-links") return withWikiRoot(wikiRoot, () => migrateRefs(global));
    if (command === "migrate") return withWikiRoot(wikiRoot, () => migrateWiki(global));
    if (command === "compile") return withWikiRoot(wikiRoot, () => compileWiki(global));
    if (command === "uuid") return cmdUuid(global);
    throw new Error(`Unknown command: ${command}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    return 2;
  }
}

function cmdInit(args: Args): number {
  const type = String(args.type ?? "");
  if (type !== "vault" && type !== "workspace") {
    throw new Error("init requires --type vault|workspace");
  }
  const result = initWiki({
    wikiType: type,
    root: stringOpt(args["root"], "."),
    workspaceRoot: stringOpt(args["workspace-root"]),
    wikiDir: stringOpt(args["wiki-dir"], "wiki"),
    writeConfig: args["no-config"] ? false : true,
    withTemplate: args["no-template"] ? false : true
  });
  console.log(`Initialized ${result.wikiType} wiki at ${result.wikiRoot}`);
  if (result.workspaceRoot) console.log(`Workspace root: ${result.workspaceRoot}`);
  console.log(`Created folders: ${result.created.length}`);
  if (result.configWritten) console.log("Wrote _system/config.json");
  if (result.templateCopied.length > 0) console.log(`Copied template files: ${result.templateCopied.length}`);
  return 0;
}

function cmdDoctor(args: Args, wikiRoot?: string): number {
  const root = wikiRoot ?? stringOpt(args["wiki-root"], stringOpt(args.root, ".")) ?? ".";
  const type = stringOpt(args.type);
  const issues = doctorWiki(root, type);
  console.log(args.json ? issuesToJson(issues) : issuesToText(issues));
  return issues.some((issue) => issue.level === "error") ? 1 : 0;
}

function cmdList(args: Args): number {
  const entries = listRegistryEntries();
  if (args.json) {
    console.log(JSON.stringify({ schemaVersion: 1, registryPath: registryPath(), wikis: entries }, null, 2));
    return 0;
  }
  if (entries.length === 0) {
    console.log("No Agent Wiki roots registered.");
    return 0;
  }
  const width = Math.max(...entries.map((entry) => entry.name.length), 4);
  for (const entry of entries) console.log(`${entry.name.padEnd(width)}  ${entry.type.padEnd(9)}  ${entry.root}`);
  return 0;
}

function cmdRegistry(args: Args): number {
  const subcommand = args._[1];
  if (subcommand === "list") return cmdList(args);
  if (subcommand === "add") {
    const name = stringOpt(args.name, args._[2]);
    if (!name) throw new Error("registry add requires a wiki name");
    const root = required(args, "root");
    const entry = addRegistryEntry(name, root, stringOpt(args.type));
    console.log(args.json ? JSON.stringify(entry, null, 2) : `Registered ${entry.name}: ${entry.root}`);
    return 0;
  }
  if (subcommand === "show") {
    const name = stringOpt(args.name, args._[2]);
    if (!name) throw new Error("registry show requires a wiki name");
    const entry = getRegistryEntry(name);
    console.log(args.json ? JSON.stringify(entry, null, 2) : `${entry.name}  ${entry.type}  ${entry.root}`);
    return 0;
  }
  if (subcommand === "remove") {
    const name = stringOpt(args.name, args._[2]);
    if (!name) throw new Error("registry remove requires a wiki name");
    const removed = removeRegistryEntry(name);
    console.log(removed ? `Removed ${name}` : `No registered wiki named ${name}`);
    return removed ? 0 : 1;
  }
  throw new Error("registry requires list, add, show, or remove");
}

function cmdCheck(args: Args): number {
  const name = args._[1] && !String(args._[1]).startsWith("--") ? String(args._[1]) : undefined;
  const entries = args.all ? listRegistryEntries() : [getRegistryEntry(name ?? required(args, "wiki"))];
  const results = entries.map((entry) => checkEntry(entry, Boolean(args.full)));
  if (args.json) {
    console.log(JSON.stringify({ schemaVersion: 1, full: Boolean(args.full), results }, null, 2));
  } else {
    for (const result of results) {
      const status = result.ok ? "ok" : "fail";
      console.log(`${status.padEnd(5)} ${result.name} (${result.root})`);
      if (!result.ok) {
        for (const issue of result.doctorIssues) console.log(`  ${issue.level}: ${issue.code} ${issue.message}`);
        if (result.indexStatus) console.log(`  index: ${result.indexStatus}`);
      }
    }
  }
  return results.every((result) => result.ok) ? 0 : 1;
}

function checkEntry(entry: ReturnType<typeof getRegistryEntry>, full: boolean) {
  const doctorIssues = doctorWiki(entry.root, entry.type);
  const onboarding = buildOnboardingReport(entry.root);
  const errors = doctorIssues.filter((issue) => issue.level === "error");
  let compileStatus: "skipped" | "passed" | "failed" = "skipped";
  let indexStatus: "skipped" | "current" | "out-of-date" | "failed" = "skipped";
  if (full && errors.length === 0) {
    const originalLog = console.log;
    try {
      console.log = () => undefined;
      withWikiRoot(entry.root, () => compileWiki({}));
      const indexCode = withWikiRoot(entry.root, () => renderIndexCommand({ check: true }));
      compileStatus = "passed";
      indexStatus = indexCode === 0 ? "current" : "out-of-date";
    } catch {
      compileStatus = "failed";
      indexStatus = "failed";
    } finally {
      console.log = originalLog;
    }
  }
  return {
    name: entry.name,
    root: entry.root,
    type: entry.type,
    ok: errors.length === 0 && onboarding.summary.ready && (!full || (compileStatus === "passed" && indexStatus === "current")),
    doctorIssues,
    onboardingSummary: onboarding.summary,
    compileStatus,
    indexStatus
  };
}

function cmdWorkspace(args: Args): number {
  const subcommand = args._[1];
  if (subcommand === "scan" || subcommand === "pending") {
    const includeUnchanged = subcommand === "scan";
    const { files, wikiRoot } = workspaceFiles(args);
    const filtered = includeUnchanged ? files : files.filter((item) => item.reason !== "unchanged");
    if (subcommand === "scan" && args["write-state"]) {
      updateStateFromScan(wikiRoot, files, loadState(wikiRoot));
    }
    console.log(args.json ? filesToJson(filtered) : filesToText(filtered));
    return 0;
  }
  if (subcommand === "mark-sourced") {
    const path = required(args, "path");
    const sourceId = required(args, "source-id");
    const sourcePath = required(args, "source-path");
    const config = loadConfig(stringOpt(args.root, "."));
    const workspaceRoot = defaultWorkspaceRoot(config, stringOpt(args["workspace-root"]));
    const wikiRoot = wikiRootForWorkspace(workspaceRoot, stringOpt(args["wiki-dir"], config.wikiDir));
    const state = markSourced(wikiRoot, loadState(wikiRoot), { relativePath: path, sourceId, sourcePath });
    updateStateFromScan(wikiRoot, scanWorkspace(workspaceRoot, wikiRoot, config.workspaceScan, { state }), state);
    console.log(`Mapped ${path} -> ${sourceId}`);
    return 0;
  }
  throw new Error("workspace requires scan, pending, or mark-sourced");
}

function cmdLog(args: Args): number {
  const message = required(args, "message");
  const path = writeOperationalLog(process.cwd(), message);
  console.log(`Wrote operational log: ${path}`);
  return 0;
}

function cmdUuid(args: Args): number {
  const length = Number(stringOpt(args.length, "10"));
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const bytes = randomBytes(length);
  let out = "";
  for (const byte of bytes) out += alphabet[byte % alphabet.length];
  console.log(out);
  return 0;
}

function workspaceFiles(args: Args) {
  const config = loadConfig(stringOpt(args.root, "."));
  const workspaceRoot = defaultWorkspaceRoot(config, stringOpt(args["workspace-root"]));
  const wikiRoot = wikiRootForWorkspace(workspaceRoot, stringOpt(args["wiki-dir"], config.wikiDir));
  const sinceHours = stringOpt(args["since-hours"]);
  const since = sinceHours === undefined ? undefined : new Date(Date.now() - Number(sinceHours) * 60 * 60 * 1000);
  const state = loadState(wikiRoot);
  return { files: scanWorkspace(workspaceRoot, wikiRoot, config.workspaceScan, { since, state }), wikiRoot };
}

function parseArgs(argv: string[]): Args {
  const parsed: Args = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token.startsWith("--")) {
      const [key, inlineValue] = token.slice(2).split("=", 2);
      if (inlineValue !== undefined) {
        addArg(parsed, key, inlineValue);
      } else if (argv[index + 1] && !argv[index + 1].startsWith("--")) {
        addArg(parsed, key, argv[index + 1]);
        index += 1;
      } else {
        addArg(parsed, key, true);
      }
    } else {
      parsed._.push(token);
    }
  }
  return parsed;
}

function addArg(parsed: Args, key: string, value: string | boolean): void {
  const existing = parsed[key];
  if (typeof existing === "string") parsed[key] = [existing, String(value)];
  else if (Array.isArray(existing)) existing.push(String(value));
  else parsed[key] = value;
}

function required(args: Args, key: string): string {
  const value = stringOpt(args[key]);
  if (!value) {
    throw new Error(`missing required --${key}`);
  }
  return value;
}

function stringOpt(value: string | boolean | string[] | undefined, fallback?: string): string | undefined {
  return typeof value === "string" ? value : fallback;
}

function resolveWikiRoot(args: Args): string | undefined {
  const name = stringOpt(args.wiki);
  return name ? getRegistryEntry(name).root : undefined;
}

function withWikiRoot(root: string | undefined, fn: () => number): number {
  if (!root) return fn();
  const previous = process.cwd();
  process.chdir(root);
  try {
    return fn();
  } finally {
    process.chdir(previous);
  }
}

function printHelp(): void {
  console.log(`agent-wiki

Commands:
  list [--json]
  registry list|add|show|remove
  check WIKI|--all [--full] [--json]
  --wiki NAME <command>
  init --type vault|workspace [--root PATH] [--workspace-root PATH] [--wiki-dir wiki] [--no-config] [--no-template]
  doctor [--wiki-root PATH] [--type vault|workspace] [--json]
  create-page --type TYPE --subtype SUBTYPE --slug SLUG --title TITLE (--body-file PATH|--body TEXT)
  onboard --check [--wiki-root PATH] [--questions] [--compact]
  onboard --write-config [--type vault|workspace] [--wiki-dir wiki] [--python-command CMD] [--conversion disabled|available-local]
  compile [--verbose]
  index --write|--check
  log --message TEXT
  uuid [--length N]
  migrate-refs-to-links --dry-run|--write
  migrate --from v1 --check|--write
  workspace scan [--workspace-root PATH] [--wiki-dir wiki] [--json] [--since-hours N] [--write-state]
  workspace pending [--workspace-root PATH] [--wiki-dir wiki] [--json] [--since-hours N]
  workspace mark-sourced --path PATH --source-id ID --source-path PATH [--workspace-root PATH] [--wiki-dir wiki]
`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  process.exitCode = main();
}
