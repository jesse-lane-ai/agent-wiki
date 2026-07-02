import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { homedir } from "node:os";
import { loadConfig, readJsonObject, WikiType } from "./config.js";
import { doctorWiki } from "./lifecycle.js";

export interface WikiRegistryEntry {
  name: string;
  root: string;
  type: WikiType;
  addedAt: string;
}

export interface WikiRegistry {
  schemaVersion: 1;
  wikis: Record<string, WikiRegistryEntry>;
}

export function registryPath(): string {
  return process.env.AGENT_WIKI_REGISTRY_PATH || join(homedir(), ".config", "agent-wiki", "registry.json");
}

export function loadRegistry(): WikiRegistry {
  const data = readJsonObject(registryPath());
  const rawWikis = data && typeof data.wikis === "object" && data.wikis !== null && !Array.isArray(data.wikis)
    ? data.wikis as Record<string, unknown>
    : {};
  const wikis: Record<string, WikiRegistryEntry> = {};
  for (const [name, value] of Object.entries(rawWikis)) {
    if (!value || typeof value !== "object" || Array.isArray(value)) continue;
    const entry = value as Record<string, unknown>;
    if (typeof entry.root !== "string") continue;
    const type = entry.type === "workspace" ? "workspace" : "vault";
    wikis[name] = {
      name,
      root: resolve(entry.root),
      type,
      addedAt: typeof entry.addedAt === "string" ? entry.addedAt : new Date(0).toISOString()
    };
  }
  return { schemaVersion: 1, wikis };
}

export function saveRegistry(registry: WikiRegistry): void {
  const path = registryPath();
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(registry, null, 2)}\n`, "utf8");
}

export function listRegistryEntries(): WikiRegistryEntry[] {
  return Object.values(loadRegistry().wikis).sort((a, b) => a.name.localeCompare(b.name));
}

export function getRegistryEntry(name: string): WikiRegistryEntry {
  const entry = loadRegistry().wikis[name];
  if (!entry) throw new Error(`Unknown wiki: ${name}`);
  return entry;
}

export function addRegistryEntry(name: string, rootInput: string, typeInput?: string): WikiRegistryEntry {
  validateName(name);
  const root = resolve(rootInput);
  if (!existsSync(root)) throw new Error(`Wiki root does not exist: ${root}`);
  const config = loadConfig(root);
  const type = typeInput === "workspace" ? "workspace" : typeInput === "vault" ? "vault" : config.wikiType;
  const issues = doctorWiki(root, type);
  const errors = issues.filter((issue) => issue.level === "error");
  if (errors.length > 0) throw new Error(`Not a valid Agent Wiki root: ${errors.map((issue) => issue.code).join(", ")}`);
  const registry = loadRegistry();
  const entry = { name, root, type, addedAt: new Date().toISOString() };
  registry.wikis[name] = entry;
  saveRegistry(registry);
  return entry;
}

export function removeRegistryEntry(name: string): boolean {
  const registry = loadRegistry();
  if (!registry.wikis[name]) return false;
  delete registry.wikis[name];
  saveRegistry(registry);
  return true;
}

function validateName(name: string): void {
  if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(name)) {
    throw new Error("Wiki name must start with a letter and contain only letters, numbers, underscores, or hyphens.");
  }
}
