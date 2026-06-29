import { existsSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { loadConfig, readJsonObject } from "./config.js";
import { doctorWiki, writeLocalConfig } from "./lifecycle.js";
import { writeJson } from "./wiki-utils.js";

const CONVERTER_COMMANDS = ["markitdown", "pymupdf4llm", "marker_single"];

export function onboard(args: Record<string, unknown>): number {
  const root = resolve(String(args["wiki-root"] || args.root || process.cwd()));
  if (args["write-config"]) return writeConfig(root, args);
  if (!args.check) throw new Error("onboard requires --check or --write-config");

  const report = buildOnboardingReport(root);
  if (args.questions) {
    console.log(renderQuestions(report));
  } else {
    console.log(JSON.stringify(report, null, args.compact ? undefined : 2));
  }
  return report.summary.ready ? 0 : 1;
}

function writeConfig(root: string, args: Record<string, unknown>): number {
  const wikiType = String(args.type || loadConfig(root).wikiType);
  if (wikiType !== "vault" && wikiType !== "workspace") throw new Error("--type must be vault or workspace");
  const wikiDir = String(args["wiki-dir"] || "wiki");
  const workspaceRoot = wikiType === "workspace" ? String(args["workspace-root"] || "") || null : null;
  writeLocalConfig(root, wikiType, workspaceRoot, wikiDir);
  const conversionPolicy = String(args.conversion || "disabled");
  const conversionEnabled = conversionPolicy !== "disabled";
  writeJson(join(root, "_system/config.json"), {
    schemaVersion: 1,
    wikiType,
    workspace: { root: workspaceRoot, wikiDir },
    pythonCommand: args["python-command"] || null,
    conversion: { enabled: conversionEnabled, policy: conversionPolicy }
  });
  console.log("Wrote _system/config.json");
  return 0;
}

function buildOnboardingReport(root: string) {
  const config = loadConfig(root);
  const doctorIssues = doctorWiki(root, config.wikiType);
  const configPath = join(root, "_system/config.json");
  const importLinkPath = join(root, "skills/import-link/config.json");
  const importLinkConfig = readJsonObject(importLinkPath);
  const requiredDocs = ["AGENTS.md", "WIKI.md", "ONBOARD.md", "AGENT-WIKI-SPEC-v2.md"];
  const requiredSkills = [
    "skills/process-inbox/SKILL.md",
    "skills/extract-knowledge-primitives/SKILL.md",
    "skills/compile-wiki/SKILL.md",
    "skills/write-synthesis/SKILL.md",
    "skills/update-overview/SKILL.md"
  ];
  const missingDocs = missingFiles(root, requiredDocs);
  const missingSkills = missingFiles(root, requiredSkills);
  const configExists = existsSync(configPath);
  const importLinkConfigured = Boolean(importLinkConfig?.configured);
  const errors = doctorIssues.filter((issue) => issue.level === "error");

  return {
    schemaVersion: 1,
    command: "agent-wiki onboard --check",
    root,
    platform: {
      os: process.platform,
      arch: process.arch,
      node: process.version
    },
    wiki: {
      type: config.wikiType,
      configExists,
      configPath,
      obsidianVault: existsDir(join(root, ".obsidian")),
      missingDocs,
      missingSkills
    },
    doctor: {
      passed: errors.length === 0,
      issues: doctorIssues
    },
    tools: {
      agentWiki: { available: true, command: "agent-wiki" },
      python: [probeCommand("python3", ["--version"]), probeCommand("python", ["--version"])],
      converters: CONVERTER_COMMANDS.map((command) => probeCommand(command, ["--version"]))
    },
    importLink: {
      configPath: importLinkPath,
      configExists: existsSync(importLinkPath),
      configured: importLinkConfigured
    },
    nextSteps: nextSteps({ configExists, importLinkConfigured, missingDocs, missingSkills, doctorIssues }),
    summary: {
      ready: errors.length === 0 && missingDocs.length === 0 && missingSkills.length === 0,
      needsConfig: !configExists,
      needsImportLinkConfig: !importLinkConfigured,
      errorCount: errors.length,
      warningCount: doctorIssues.filter((issue) => issue.level === "warning").length
    }
  };
}

function renderQuestions(report: ReturnType<typeof buildOnboardingReport>): string {
  const lines = [
    "Agent Wiki onboarding questions",
    "",
    `1. Wiki type: ${report.wiki.type}`,
    "   A. Keep detected wiki type",
    "   B. Re-run init with --type vault",
    "   C. Re-run init with --type workspace",
    "",
    `2. Local config: ${report.wiki.configExists ? "present" : "missing"}`,
    "   A. Leave local config as-is",
    "   B. Write local config with agent-wiki onboard --write-config",
    "",
    `3. Import-link config: ${report.importLink.configured ? "configured" : "not configured"}`,
    "   A. Leave import-link disabled for now",
    "   B. Configure skills/import-link/config.json before importing links",
    "",
    "4. Optional conversion policy",
    "   A. Keep conversion disabled",
    "   B. Enable already-installed local converters only"
  ];
  if (!report.doctor.passed) {
    lines.push("", "Doctor errors must be fixed before editing wiki content.");
  }
  return `${lines.join("\n")}\n`;
}

function nextSteps(input: {
  configExists: boolean;
  importLinkConfigured: boolean;
  missingDocs: string[];
  missingSkills: string[];
  doctorIssues: Array<{ level: string; code: string; message: string; path?: string }>;
}): string[] {
  const steps: string[] = [];
  if (input.doctorIssues.some((issue) => issue.level === "error")) steps.push("Fix doctor errors, then rerun agent-wiki onboard --check.");
  if (input.missingDocs.length || input.missingSkills.length) steps.push("Run agent-wiki init --with-template or migrate to restore missing docs/skills.");
  if (!input.configExists) steps.push("Persist local setup with agent-wiki onboard --write-config after choosing wiki type and policy.");
  if (!input.importLinkConfigured) steps.push("Configure skills/import-link/config.json before importing external links.");
  steps.push("Run agent-wiki compile and agent-wiki index --check before handing the wiki to another agent.");
  return steps;
}

function missingFiles(root: string, paths: string[]): string[] {
  return paths.filter((path) => !existsSync(join(root, path)) || !statSync(join(root, path)).isFile());
}

function existsDir(path: string): boolean {
  return existsSync(path) && statSync(path).isDirectory();
}

function probeCommand(command: string, args: string[]) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: 3000
  });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`.trim().split(/\r?\n/)[0] ?? "";
  return {
    command,
    available: result.status === 0 || Boolean(output),
    version: output || null
  };
}
