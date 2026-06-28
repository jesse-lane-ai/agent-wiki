import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { DEFAULT_WORKSPACE_WIKI_DIR, AgentWikiConfig, WorkspaceScanConfig, cleanWikiDir, isObject } from "./config.js";

export const STATE_PATH = "_system/state/workspace-sources.json";

export interface WorkspaceFile {
  path: string;
  relativePath: string;
  modifiedAt: string;
  size: number;
  extension: string;
  sha256: string;
  reason: "new" | "changed" | "unchanged";
  recommendedSourceType: string;
  alreadySourced: boolean;
  sourceId: string | null;
  sourcePath: string | null;
}

export function defaultWorkspaceRoot(config: AgentWikiConfig, explicitRoot?: string): string {
  if (explicitRoot) {
    return resolve(explicitRoot);
  }
  if (config.workspaceRoot) {
    return resolve(config.workspaceRoot);
  }
  if (config.wikiType === "workspace") {
    return resolve(config.root);
  }
  return process.cwd();
}

export function wikiRootForWorkspace(workspaceRoot: string, wikiDir?: string): string {
  return resolve(workspaceRoot, cleanWikiDir(wikiDir ?? DEFAULT_WORKSPACE_WIKI_DIR));
}

export function loadState(wikiRoot: string): Record<string, unknown> {
  const path = join(wikiRoot, STATE_PATH);
  try {
    const data: unknown = JSON.parse(readFileSync(path, "utf8"));
    if (!isObject(data)) {
      return emptyState();
    }
    if (!isObject(data.files)) {
      data.files = {};
    }
    return data;
  } catch {
    return emptyState();
  }
}

export function writeState(wikiRoot: string, state: Record<string, unknown>): void {
  const path = join(wikiRoot, STATE_PATH);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

export function scanWorkspace(
  workspaceRootInput: string,
  wikiRootInput: string,
  scanConfig: WorkspaceScanConfig,
  options: { since?: Date; state?: Record<string, unknown> } = {}
): WorkspaceFile[] {
  const workspaceRoot = resolve(workspaceRootInput);
  const wikiRoot = resolve(wikiRootInput);
  const filesState = isObject(options.state?.files) ? options.state.files : {};
  const results: WorkspaceFile[] = [];
  for (const path of iterCandidatePaths(workspaceRoot, wikiRoot, scanConfig)) {
    let stat;
    try {
      stat = statSync(path);
    } catch {
      continue;
    }
    const modified = new Date(stat.mtimeMs);
    if (options.since && modified < options.since) {
      continue;
    }
    const relPath = relative(workspaceRoot, path).split("\\").join("/");
    const digest = sha256File(path);
    const previous = isObject(filesState[relPath]) ? filesState[relPath] : null;
    const previousHash = typeof previous?.sha256 === "string" ? previous.sha256 : null;
    const sourceId = typeof previous?.sourceId === "string" ? previous.sourceId : null;
    const sourcePath = typeof previous?.sourcePath === "string" ? previous.sourcePath : null;
    const reason = previousHash === null ? "new" : previousHash === digest ? "unchanged" : "changed";
    results.push({
      path,
      relativePath: relPath,
      modifiedAt: modified.toISOString(),
      size: stat.size,
      extension: extensionOf(path),
      sha256: digest,
      reason,
      recommendedSourceType: recommendSourceType(path),
      alreadySourced: sourceId !== null,
      sourceId,
      sourcePath
    });
  }
  return results.sort((a, b) => a.relativePath.localeCompare(b.relativePath));
}

export function updateStateFromScan(wikiRoot: string, files: WorkspaceFile[], state: Record<string, unknown>): Record<string, unknown> {
  const filesState = isObject(state.files) ? state.files : {};
  const now = new Date().toISOString();
  for (const item of files) {
    const previous = (isObject(filesState[item.relativePath]) ? filesState[item.relativePath] : {}) as Record<string, unknown>;
    filesState[item.relativePath] = {
      path: item.path,
      mtime: item.modifiedAt,
      size: item.size,
      sha256: item.sha256,
      sourceId: typeof previous.sourceId === "string" ? previous.sourceId : null,
      sourcePath: typeof previous.sourcePath === "string" ? previous.sourcePath : null,
      lastSeenAt: now
    };
  }
  state.schemaVersion = 1;
  state.lastScanAt = now;
  state.files = filesState;
  writeState(wikiRoot, state);
  return state;
}

export function markSourced(
  wikiRoot: string,
  state: Record<string, unknown>,
  options: { relativePath: string; sourceId: string; sourcePath: string }
): Record<string, unknown> {
  const filesState = isObject(state.files) ? state.files : {};
  const previous = (isObject(filesState[options.relativePath]) ? filesState[options.relativePath] : {}) as Record<string, unknown>;
  filesState[options.relativePath] = {
    ...previous,
    sourceId: options.sourceId,
    sourcePath: options.sourcePath,
    mappedAt: new Date().toISOString()
  };
  state.schemaVersion = 1;
  state.files = filesState;
  writeState(wikiRoot, state);
  return state;
}

export function filesToJson(files: WorkspaceFile[]): string {
  return JSON.stringify(files, null, 2);
}

export function filesToText(files: WorkspaceFile[]): string {
  if (files.length === 0) {
    return "No workspace source candidates found.";
  }
  return files
    .map((item) => {
      const marker = item.alreadySourced ? "sourced" : item.reason;
      return `${marker.padEnd(9)} ${item.relativePath} (${item.recommendedSourceType}, ${item.size} bytes)`;
    })
    .join("\n");
}

function emptyState(): Record<string, unknown> {
  return { schemaVersion: 1, files: {} };
}

function iterCandidatePaths(workspaceRoot: string, wikiRoot: string, scanConfig: WorkspaceScanConfig): string[] {
  const results: string[] = [];
  const excludedDirs = new Set(scanConfig.excludeDirs);
  function walk(dir: string): void {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        const relParts = relative(workspaceRoot, path).split(/[\\/]/);
        if (isRelativeTo(path, wikiRoot) || relParts.some((part) => excludedDirs.has(part))) {
          continue;
        }
        walk(path);
      } else if (entry.isFile()) {
        const relParts = relative(workspaceRoot, path).split(/[\\/]/);
        if (isRelativeTo(path, wikiRoot) || relParts.slice(0, -1).some((part) => excludedDirs.has(part))) {
          continue;
        }
        if (scanConfig.excludeFileGlobs.some((pattern) => globMatch(entry.name, pattern))) {
          continue;
        }
        if (!scanConfig.includeExtensions.includes(extensionOf(path))) {
          continue;
        }
        results.push(resolve(path));
      }
    }
  }
  walk(workspaceRoot);
  return results;
}

function isRelativeTo(path: string, parent: string): boolean {
  const rel = relative(resolve(parent), resolve(path));
  return rel === "" || (!rel.startsWith("..") && !rel.startsWith("/") && !/^[A-Za-z]:/.test(rel));
}

function sha256File(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function recommendSourceType(path: string): string {
  const suffix = extensionOf(path);
  if (suffix === ".pdf") return "pdf";
  if ([".csv", ".json", ".yaml", ".yml"].includes(suffix)) return "dataset";
  if ([".md", ".markdown", ".txt", ".docx"].includes(suffix)) return "document";
  return "other";
}

function extensionOf(path: string): string {
  const match = /(\.[^./\\]+)$/.exec(path);
  return match ? match[1].toLowerCase() : "";
}

function globMatch(name: string, pattern: string): boolean {
  if (pattern.startsWith("*")) {
    return name.endsWith(pattern.slice(1));
  }
  return name === pattern;
}
