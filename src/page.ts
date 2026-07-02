import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { idToFilename, pathToWikilink, readText, refToWikilink, renderMarkdown, today, walkMarkdownPages, writeOperationalLog, writeText } from "./wiki-utils.js";

const PAGE_FOLDERS: Record<string, string> = {
  source: "sources",
  entity: "entities",
  concept: "concepts",
  claim: "claims",
  question: "questions",
  synthesis: "syntheses"
};

const SOURCE_TYPES = new Set(["webpage", "article", "document", "pdf", "transcript", "email", "meeting-notes", "dataset", "screenshot", "bridge", "import", "other"]);
const ENTITY_TYPES = new Set(["person", "organization", "project", "product", "system", "place", "event", "artifact", "document", "other"]);
const CONCEPT_TYPES = new Set(["definition", "principle", "framework", "method", "policy", "standard", "pattern", "workflow", "runbook", "checklist", "playbook", "theory", "taxonomy", "other"]);
const SYNTHESIS_TYPES = new Set(["summary", "overview", "analysis", "timeline", "brief", "comparison"]);
const CLAIM_TYPES = new Set(["descriptive", "historical", "causal", "interpretive", "normative", "forecast"]);

export function createPage(args: Record<string, string | boolean | string[] | undefined>): number {
  const wikiRoot = process.cwd();
  try {
    const pageType = required(args, "type");
    const subtype = required(args, "subtype");
    const slug = required(args, "slug");
    const title = required(args, "title");
    if (!(pageType in PAGE_FOLDERS)) throw new Error("--type must be source, entity, concept, claim, question, or synthesis");
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) throw new Error("--slug must use kebab-case lowercase letters, numbers, and hyphens");
    validateSubtype(pageType, subtype);
    const body = readBody(args, wikiRoot);
    if (pageType !== "source" && wordCount(body) < 5) throw new Error("authored knowledge pages require substantive body prose");
    const createdAt = stringOpt(args.date, today());
    const sourceRole = stringOpt(args["source-role"], "whole");
    const sourceDate = stringOpt(args["source-date"], stringOpt(args["retrieved-at"], createdAt));
    const pageId = buildPageId(pageType, subtype, slug, pageType === "source" ? sourceDate : createdAt, sourceRole, numberOpt(args["part-index"]));
    const folder = pageType === "source" && sourceRole === "part" ? "sources/parts" : PAGE_FOLDERS[pageType];
    const relPath = join(folder, idToFilename(pageId)).split("\\").join("/");
    const absPath = join(wikiRoot, relPath);
    const duplicate = walkMarkdownPages(wikiRoot).find((page) => page.id === pageId);
    if (duplicate) throw new Error(`page ID already exists in ${duplicate.path}`);
    if (existsSync(absPath)) throw new Error(`target file already exists: ${relPath}`);

    const frontmatter = buildFrontmatter(args, pageType, subtype, title, pageId, createdAt, sourceRole);
    const result: Record<string, unknown> = {
      schemaVersion: 1,
      mode: args["dry-run"] ? "dry-run" : "write",
      mutating: !args["dry-run"],
      id: pageId,
      path: relPath,
      pageType,
      status: frontmatter.status,
      written: false
    };
    if (args["dry-run"]) {
      result.frontmatter = frontmatter;
    } else {
      writeText(absPath, renderMarkdown(frontmatter, body));
      result.written = true;
      if (!args["no-log"]) writeOperationalLog(wikiRoot, `create-page: created ${pageType} page ${pageId} at ${relPath}`);
    }
    console.log(JSON.stringify(result, null, args.compact ? undefined : 2));
    return 0;
  } catch (error) {
    console.log(JSON.stringify({ schemaVersion: 1, mode: args["dry-run"] ? "dry-run" : "write", mutating: false, written: false, error: error instanceof Error ? error.message : String(error) }, null, args.compact ? undefined : 2));
    return 1;
  }
}

function buildFrontmatter(args: Record<string, string | boolean | string[] | undefined>, pageType: string, subtype: string, title: string, id: string, createdAt: string, sourceRole: string): Record<string, unknown> {
  const fm: Record<string, unknown> = { id, pageType, title, status: defaultStatus(args, pageType, sourceRole) };
  const subtypeField: Record<string, string> = { source: "sourceType", entity: "entityType", concept: "conceptType", claim: "claimType", synthesis: "synthesisType" };
  if (subtypeField[pageType]) fm[subtypeField[pageType]] = subtype;
  if (pageType === "source") {
    if (!args["source-url"] && !args["origin-path"]) throw new Error("source pages require --source-url or --origin-path");
    fm.sourceRole = sourceRole;
    fm.sourceParts = list(args["source-part"]);
    if (sourceRole === "part") {
      fm.parentSourceId = required(args, "parent-source-id");
      fm.partIndex = numberRequired(args, "part-index");
      fm.partCount = numberRequired(args, "part-count");
      fm.locator = required(args, "locator");
    } else if (sourceRole === "parent") {
      if (list(args["source-part"]).length === 0) throw new Error("parent source pages require at least one --source-part path");
      fm.partCount = numberOpt(args["part-count"]);
    }
    if (args["source-url"]) fm.originUrl = args["source-url"];
    if (args["origin-path"]) fm.originPath = pathToWikilink(String(args["origin-path"]));
    fm.retrievedAt = stringOpt(args["retrieved-at"], createdAt);
    for (const [flag, key] of [["published-at", "publishedAt"], ["converted-at", "convertedAt"], ["conversion-tool", "conversionTool"], ["conversion-tool-version", "conversionToolVersion"], ["conversion-backend", "conversionBackend"]] as const) {
      if (args[flag]) fm[key] = args[flag];
    }
    if (list(args["conversion-warning"]).length) fm.conversionWarnings = list(args["conversion-warning"]);
    fm.attachments = list(args.attachment);
  } else if (pageType === "entity") {
    fm.canonicalName = stringOpt(args["canonical-name"], title);
  } else if (pageType === "claim") {
    fm.confidence = Number(stringOpt(args.confidence, "0.6"));
    fm.text = stringOpt(args["claim-text"], title);
    fm.subjectPageId = stringOpt(args["subject-page-id"], "");
    fm.sourceIds = list(args["source-id"]);
    fm.evidence = list(args.evidence).map(parseEvidence);
  } else if (pageType === "question") {
    fm.priority = stringOpt(args.priority, "medium");
    fm.relatedClaims = list(args["related-claim"]).map(refToWikilink);
    fm.relatedPages = list(args["related-page"]).map(refToWikilink);
    fm.openedAt = stringOpt(args["opened-at"], createdAt);
  } else if (pageType === "synthesis") {
    if (!args.scope) throw new Error("synthesis pages require --scope");
    fm.scope = args.scope;
    fm.sourcePages = list(args["source-page"]).map(refToWikilink);
    fm.derivedClaims = list(args["derived-claim"]).map(refToWikilink);
  }
  if (!["claim", "question", "synthesis"].includes(pageType) && list(args["source-page"]).length) fm.sourcePages = list(args["source-page"]).map(refToWikilink);
  if (pageType !== "question" && list(args["related-page"]).length) fm.relatedPages = list(args["related-page"]).map(refToWikilink);
  fm.createdAt = createdAt;
  fm.updatedAt = stringOpt(args["updated-at"], createdAt);
  fm.aliases = list(args.alias);
  fm.tags = list(args.tag);
  return fm;
}

function buildPageId(pageType: string, subtype: string, slug: string, createdAt: string, sourceRole: string, partIndex?: number): string {
  if (pageType === "source") return `source.${createdAt}.${subtype}.${slug}${sourceRole === "part" ? `.part${String(partIndex).padStart(3, "0")}` : ""}`;
  if (pageType === "question") return `question.${subtype}.${slug}`;
  return `${pageType}.${subtype}.${slug}`;
}

function defaultStatus(args: Record<string, unknown>, pageType: string, sourceRole: string): string {
  if (typeof args.status === "string") return args.status;
  if (pageType === "source") return sourceRole === "parent" ? "partitioned" : "unprocessed";
  if (pageType === "claim") return "unverified";
  if (pageType === "question") return "open";
  return "active";
}

function validateSubtype(pageType: string, subtype: string): void {
  const sets: Record<string, Set<string>> = { source: SOURCE_TYPES, entity: ENTITY_TYPES, concept: CONCEPT_TYPES, claim: CLAIM_TYPES, synthesis: SYNTHESIS_TYPES };
  if (sets[pageType] && !sets[pageType].has(subtype)) throw new Error(`--subtype ${subtype} is not valid for page type ${pageType}`);
}

function parseEvidence(value: string): Record<string, unknown> {
  const raw = value.trim().startsWith("{") ? JSON.parse(value) : Object.fromEntries(value.split(";").filter(Boolean).map((part) => part.split("=", 2).map((x) => x.trim())));
  for (const key of ["id", "sourceId", "path", "kind", "relation", "weight", "updatedAt"]) if (!raw[key]) throw new Error("--evidence is missing required fields");
  raw.weight = Number(raw.weight);
  return raw;
}

function readBody(args: Record<string, string | boolean | string[] | undefined>, wikiRoot: string): string {
  const bodyFile = stringOpt(args["body-file"]);
  const body = bodyFile ? readText(resolve(wikiRoot, bodyFile)) : stringOpt(args.body, "");
  if (!body.trim()) throw new Error("body prose/content is required");
  return body;
}

function required(args: Record<string, string | boolean | string[] | undefined>, key: string): string {
  const value = stringOpt(args[key]);
  if (!value) throw new Error(`missing required --${key}`);
  return value;
}
function stringOpt(value: unknown, fallback?: string): string { return typeof value === "string" ? value : fallback ?? ""; }
function list(value: unknown): string[] { return Array.isArray(value) ? value.map(String) : typeof value === "string" ? [value] : []; }
function numberOpt(value: unknown): number | undefined { return typeof value === "string" ? Number(value) : undefined; }
function numberRequired(args: Record<string, unknown>, key: string): number { const value = numberOpt(args[key]); if (!Number.isFinite(value)) throw new Error(`missing required --${key}`); return value as number; }
function wordCount(value: string): number { return (value.match(/\b\w+\b/g) ?? []).length; }
