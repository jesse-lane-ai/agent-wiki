import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { readJson, writeOperationalLog, writeText } from "./wiki-utils.js";

export function renderIndexCommand(args: Record<string, unknown>): number {
  const wikiRoot = process.cwd();
  const data = readJson(join(wikiRoot, "_system/cache/pages.json")) as { pages?: any[] } | null;
  if (!data || !Array.isArray(data.pages)) throw new Error("Missing _system/cache/pages.json; run compile first.");
  const rendered = renderIndex(data.pages);
  const path = join(wikiRoot, "index.md");
  const existing = existsSync(path) ? readFileSync(path, "utf8") : "";
  if (args.check) {
    if (existing !== rendered) {
      console.log("index.md is out of date");
      return 1;
    }
    console.log("index.md is current");
    return 0;
  }
  if (existing === rendered) {
    console.log("index.md is current");
    return 0;
  }
  writeText(path, rendered);
  console.log("Wrote index.md");
  if (!args["no-log"]) writeOperationalLog(wikiRoot, `index: regenerated root page catalog; pages=${data.pages.length}`);
  return 0;
}

export function renderIndex(pages: any[]): string {
  const byType = new Map<string, any[]>();
  for (const page of pages) {
    const type = String(page.pageType || "other");
    byType.set(type, [...(byType.get(type) ?? []), page]);
  }
  const lines = ["---", "id: index.root", "pageType: index", "title: Page Index", "status: active", `updatedAt: ${new Date().toISOString().slice(0, 10)}`, "---", "", "# Page Index", ""];
  for (const type of ["overview", "source", "entity", "concept", "claim", "synthesis", "question", "report", "index"]) {
    const rows = (byType.get(type) ?? []).sort((a, b) => String(a.title).localeCompare(String(b.title)));
    if (!rows.length) continue;
    lines.push(`## ${label(type)}`, "", "| Page | Path | Status | Updated |", "|---|---|---|---|");
    for (const page of rows) {
      lines.push(`| ${esc(page.title || page.id)} | ${esc(page.path)} | ${esc(page.status)} | ${esc(page.updatedAt)} |`);
    }
    lines.push("");
  }
  return `${lines.join("\n").trimEnd()}\n`;
}

function label(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1).replaceAll("-", " ") + "s";
}

function esc(value: unknown): string {
  return String(value ?? "").replaceAll("|", "\\|").replaceAll("\n", " ");
}
