import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import YAML from "yaml";

export interface WikiPage {
  id: string;
  pageType: string;
  title: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  path: string;
  aliases: unknown[];
  tags: unknown[];
  meta: Record<string, unknown>;
  body: string;
  [key: string]: unknown;
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function nowIsoSeconds(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "");
}

export function readText(path: string): string {
  return readFileSync(path, "utf8");
}

export function writeText(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content, "utf8");
}

export function readJson(path: string): unknown | null {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return null;
  }
}

export function writeJson(path: string, value: unknown): void {
  writeText(path, `${JSON.stringify(value, null, 2)}\n`);
}

export function renderMarkdown(frontmatter: Record<string, unknown>, body: string): string {
  return `---\n${YAML.stringify(frontmatter).trimEnd()}\n---\n\n${body.trim()}\n`;
}

export function parseMarkdownPage(path: string, wikiRoot: string): WikiPage | null {
  const text = readFileSync(path, "utf8");
  if (!text.startsWith("---\n")) {
    return null;
  }
  const end = text.indexOf("\n---", 4);
  if (end === -1) {
    return null;
  }
  const raw = text.slice(4, end);
  const parsed = YAML.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return null;
  }
  const meta = parsed as Record<string, unknown>;
  const relPath = relative(wikiRoot, path).split("\\").join("/");
  const body = text.slice(end + 4).replace(/^\s*\n/, "");
  return {
    id: String(meta.id ?? ""),
    pageType: String(meta.pageType ?? ""),
    title: String(meta.title ?? meta.id ?? relPath),
    status: String(meta.status ?? ""),
    createdAt: String(meta.createdAt ?? ""),
    updatedAt: String(meta.updatedAt ?? meta.createdAt ?? ""),
    path: relPath,
    aliases: Array.isArray(meta.aliases) ? meta.aliases : [],
    tags: Array.isArray(meta.tags) ? meta.tags : [],
    meta,
    body,
    ...meta
  };
}

export function walkMarkdownPages(wikiRoot: string): WikiPage[] {
  const skip = new Set([".git", ".obsidian", "_system", "skills", "_archive", "_inbox", "_attachments", "raw", "reports", "node_modules", "dist"]);
  const pages: WikiPage[] = [];
  function walk(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      const relParts = relative(wikiRoot, path).split(/[\\/]/);
      if (entry.isDirectory()) {
        if (relParts.some((part) => skip.has(part))) continue;
        walk(path);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        const page = parseMarkdownPage(path, wikiRoot);
        if (page) pages.push(page);
      }
    }
  }
  if (existsSync(wikiRoot) && statSync(wikiRoot).isDirectory()) {
    walk(wikiRoot);
  }
  return pages.sort((a, b) => a.path.localeCompare(b.path));
}

export function idToFilename(pageId: string): string {
  return pageId.startsWith("source.") ? `${pageId.slice("source.".length).replaceAll(".", "-")}.md` : `${pageId.replaceAll(".", "-")}.md`;
}

export function refToWikilink(value: string): string {
  const text = value.trim();
  if (!text || text.startsWith("[[")) return text;
  return `[[${idToFilename(text).slice(0, -3)}|${text}]]`;
}

export function pathToWikilink(value: string): string {
  const text = value.trim();
  if (!text || text.startsWith("[[")) return text;
  const target = text.endsWith(".md") ? text.slice(0, -3) : text;
  return `[[${target}|${text}]]`;
}

export function writeOperationalLog(wikiRoot: string, message: string): string {
  if (!message.trim()) throw new Error("--message cannot be empty");
  const logPath = join(wikiRoot, "_system/logs/log.md");
  const timestamp = new Date().toISOString();
  const entry = `## ${timestamp}\n\n${message.trim()}\n`;
  const existing = existsSync(logPath) ? readFileSync(logPath, "utf8").trimStart() : "";
  writeText(logPath, existing ? `${entry}\n${existing}` : entry);
  return logPath;
}
