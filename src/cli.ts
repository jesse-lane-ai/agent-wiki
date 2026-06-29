#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { loadConfig } from "./config.js";
import { renderIndexCommand } from "./catalog.js";
import { compileWiki } from "./compile.js";
import { doctorWiki, initWiki, issuesToJson, issuesToText } from "./lifecycle.js";
import { migrateRefs } from "./migrate.js";
import { onboard } from "./onboard.js";
import { createPage } from "./page.js";
import { migrateWiki } from "./upgrade.js";
import { writeOperationalLog } from "./wiki-utils.js";
import { randomBytes } from "node:crypto";
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
    if (command === "init") return cmdInit(global);
    if (command === "doctor") return cmdDoctor(global);
    if (command === "workspace") return cmdWorkspace(global);
    if (command === "create-page") return createPage(global);
    if (command === "onboard") return onboard(global);
    if (command === "index") return renderIndexCommand(global);
    if (command === "log") return cmdLog(global);
    if (command === "migrate-refs-to-links") return migrateRefs(global);
    if (command === "migrate") return migrateWiki(global);
    if (command === "compile") return compileWiki(global);
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
    writeConfig: Boolean(args["write-config"]),
    withTemplate: Boolean(args["with-template"])
  });
  console.log(`Initialized ${result.wikiType} wiki at ${result.wikiRoot}`);
  if (result.workspaceRoot) console.log(`Workspace root: ${result.workspaceRoot}`);
  console.log(`Created folders: ${result.created.length}`);
  if (result.configWritten) console.log("Wrote _system/config.json");
  if (result.templateCopied.length > 0) console.log(`Copied template files: ${result.templateCopied.length}`);
  return 0;
}

function cmdDoctor(args: Args): number {
  const root = stringOpt(args["wiki-root"], stringOpt(args.root, ".")) ?? ".";
  const type = stringOpt(args.type);
  const issues = doctorWiki(root, type);
  console.log(args.json ? issuesToJson(issues) : issuesToText(issues));
  return issues.some((issue) => issue.level === "error") ? 1 : 0;
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

function printHelp(): void {
  console.log(`agent-wiki

Commands:
  init --type vault|workspace [--root PATH] [--workspace-root PATH] [--wiki-dir wiki] [--write-config] [--with-template]
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
