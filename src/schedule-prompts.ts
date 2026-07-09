import { listRegistryEntries, WikiRegistryEntry } from "./registry.js";

const JOBS = new Set(["process-inbox", "extract-primitives", "update-overview"]);

export function schedulePrompt(args: Record<string, unknown>): number {
  const subcommand = Array.isArray(args._) ? String(args._[1] ?? "") : "";
  if (subcommand !== "prompt") throw new Error("schedule requires prompt");
  const job = Array.isArray(args._) ? String(args._[2] ?? "") : "";
  if (!JOBS.has(job)) throw new Error("schedule prompt requires process-inbox, extract-primitives, or update-overview");
  const selected = selectedNames(args);
  const entries = selected.length > 0
    ? listRegistryEntries().filter((entry) => selected.includes(entry.name))
    : listRegistryEntries();
  const missing = selected.filter((name) => !entries.some((entry) => entry.name === name));
  if (missing.length > 0) throw new Error(`Unknown registered wiki: ${missing.join(", ")}`);
  console.log(renderPrompt(job, entries));
  return 0;
}

function selectedNames(args: Record<string, unknown>): string[] {
  const values: string[] = [];
  const wiki = args.wiki;
  if (typeof wiki === "string") values.push(wiki);
  else if (Array.isArray(wiki)) values.push(...wiki.map(String));
  if (Array.isArray(args._)) values.push(...args._.slice(3).map(String));
  return Array.from(new Set(values.filter(Boolean)));
}

function renderPrompt(job: string, entries: WikiRegistryEntry[]): string {
  const header = {
    "process-inbox": "Scheduled Agent Wiki job: process new inbox notes",
    "extract-primitives": "Scheduled Agent Wiki job: extract knowledge primitives",
    "update-overview": "Scheduled Agent Wiki job: compile and refresh overview"
  }[job];
  const task = {
    "process-inbox": "Run source intake: use process-inbox for vault wikis and process-workspace-sources for workspace wikis.",
    "extract-primitives": "Run the local extract-knowledge-primitives workflow for source pages with `status: unprocessed`.",
    "update-overview": "Run the local update-overview workflow, which compiles first and then refreshes `overview.md`."
  }[job];
  const empty = {
    "process-inbox": "If `_inbox/` is empty or has no processable files, note it and continue.",
    "extract-primitives": "If no unprocessed source pages exist, note it and continue.",
    "update-overview": "If compile reports validation issues, report them and continue to the next wiki."
  }[job];

  const lines = [
    header,
    "",
    "Use `agent-wiki list --json` to confirm the registered Agent Wiki roots before starting.",
    "Process only registered Agent Wiki roots. Do not use hardcoded vault paths or unregistered folders.",
    "If one wiki fails, log the error, summarize the failure, and continue to the next wiki.",
    "Do not hand-edit `_system/config.json`, `_system/cache/`, or `_system/indexes/`.",
    "",
    `Task: ${task}`,
    `Skill: ${skillSummary(job)}`,
    "",
    "Registered wiki targets for this run:"
  ];
  if (entries.length === 0) {
    lines.push("- No registered wikis found. Report that there is nothing to run.");
  } else {
    for (const entry of entries) lines.push(targetLine(job, entry));
  }
  lines.push(
    "",
    "For each target wiki, in order:",
    "1. Run `agent-wiki --wiki <name> onboard --check` and review the JSON summary.",
    "2. Read that wiki's `AGENTS.md` and `WIKI.md` before editing.",
    `3. Follow ${skillInstruction(job)} exactly.`,
    `4. ${empty}`,
    "5. Report a compact per-wiki result: processed, skipped, failed, and why.",
    "",
    "Act without asking unless the local skill requires an explicit operator decision."
  );
  return `${lines.join("\n")}\n`;
}

function targetLine(job: string, entry: WikiRegistryEntry): string {
  if (job === "process-inbox" && entry.type === "workspace") {
    return `- ${entry.name}: ${entry.root} (workspace wiki; use skills/process-workspace-sources/SKILL.md)`;
  }
  return `- ${entry.name}: ${entry.root}`;
}

function skillInstruction(job: string): string {
  if (job === "process-inbox") {
    return "the wiki's local `skills/process-inbox/SKILL.md` instructions for vault wikis and `skills/process-workspace-sources/SKILL.md` instructions for workspace wikis";
  }
  const skill = {
    "extract-primitives": "skills/extract-knowledge-primitives/SKILL.md",
    "update-overview": "skills/update-overview/SKILL.md"
  }[job];
  return `\`${skill}\``;
}

function skillSummary(job: string): string {
  if (job === "process-inbox") {
    return "skills/process-inbox/SKILL.md for vault wikis; skills/process-workspace-sources/SKILL.md for workspace wikis";
  }
  const skill = {
    "extract-primitives": "skills/extract-knowledge-primitives/SKILL.md",
    "update-overview": "skills/update-overview/SKILL.md"
  }[job];
  return String(skill);
}
