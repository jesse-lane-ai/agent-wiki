import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export const CONFIG_PATH = "_system/config.json";
export const CONFIG_EXAMPLE_PATH = "_system/config.example.json";
export const DEFAULT_WORKSPACE_WIKI_DIR = "wiki";
export const VALID_WIKI_TYPES = new Set(["vault", "workspace"]);

export type WikiType = "vault" | "workspace";

export interface WorkspaceScanConfig {
  includeExtensions: string[];
  excludeDirs: string[];
  excludeFileGlobs: string[];
}

export interface AgentWikiConfig {
  wikiType: WikiType;
  root: string;
  workspaceRoot: string | null;
  wikiDir: string;
  workspaceScan: WorkspaceScanConfig;
}

const DEFAULT_SCAN: WorkspaceScanConfig = {
  includeExtensions: [".md", ".markdown", ".txt", ".pdf", ".docx", ".csv", ".json", ".yaml", ".yml"],
  excludeDirs: [
    ".git",
    ".hg",
    ".svn",
    ".obsidian",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".cache",
    "_system",
    "reports",
    "target",
    "vendor"
  ],
  excludeFileGlobs: ["*.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock"]
};

export function loadConfig(root = "."): AgentWikiConfig {
  const rootPath = resolve(root);
  const data = readJsonObject(joinPath(rootPath, CONFIG_PATH)) ?? readJsonObject(joinPath(rootPath, CONFIG_EXAMPLE_PATH)) ?? {};
  const rawType = String(data.wikiType ?? data.wiki_type ?? "vault");
  const wikiType = VALID_WIKI_TYPES.has(rawType) ? (rawType as WikiType) : "vault";
  const workspace = isObject(data.workspace) ? data.workspace : {};
  const workspaceRootRaw = workspace.root ?? data.workspaceRoot;
  let workspaceRoot: string | null = null;
  if (typeof workspaceRootRaw === "string" && workspaceRootRaw.length > 0) {
    workspaceRoot = resolve(rootPath, workspaceRootRaw);
  }
  const wikiDir = cleanWikiDir(String(workspace.wikiDir ?? data.wikiDir ?? DEFAULT_WORKSPACE_WIKI_DIR));
  const scan = isObject(workspace.scan) ? workspace.scan : {};
  return {
    wikiType,
    root: rootPath,
    workspaceRoot,
    wikiDir,
    workspaceScan: {
      includeExtensions: tupleFromConfig(scan, "includeExtensions", DEFAULT_SCAN.includeExtensions).map((ext) =>
        ext.startsWith(".") ? ext : `.${ext}`
      ),
      excludeDirs: tupleFromConfig(scan, "excludeDirs", DEFAULT_SCAN.excludeDirs),
      excludeFileGlobs: tupleFromConfig(scan, "excludeFileGlobs", DEFAULT_SCAN.excludeFileGlobs)
    }
  };
}

export function cleanWikiDir(value: string): string {
  return value.trim().replace(/^\/+|\/+$/g, "") || DEFAULT_WORKSPACE_WIKI_DIR;
}

export function readJsonObject(path: string): Record<string, unknown> | null {
  try {
    const data: unknown = JSON.parse(readFileSync(path, "utf8"));
    return isObject(data) ? data : null;
  } catch {
    return null;
  }
}

export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function tupleFromConfig(data: Record<string, unknown>, key: string, defaults: string[]): string[] {
  const value = data[key];
  if (!Array.isArray(value)) {
    return defaults;
  }
  const items = value.filter((item): item is string => typeof item === "string" && item.length > 0);
  return items.length > 0 ? items : defaults;
}

function joinPath(root: string, relative: string): string {
  return resolve(root, relative);
}
