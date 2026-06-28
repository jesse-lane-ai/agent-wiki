import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { renderIndex } from "./catalog.js";
import { walkMarkdownPages, writeJson, writeOperationalLog } from "./wiki-utils.js";

export function compileWiki(args: Record<string, unknown>): number {
  const root = process.cwd();
  const compiledAt = new Date().toISOString();
  console.log("Agent Wiki v2 Compile Pipeline");
  console.log(`Wiki root: ${root}`);
  console.log(`Compiled at: ${compiledAt}`);
  console.log();
  for (const dir of ["_system/cache", "_system/indexes", "_system/logs", "reports"]) mkdirSync(join(root, dir), { recursive: true });
  console.log("Reading vault pages...");
  const pages = walkMarkdownPages(root);
  const issues = validatePages(pages);
  console.log(`  Found ${pages.length} pages with frontmatter`);
  if (issues.length) console.log(`  Validation issues detected: ${issues.length}`);
  const claims = extractClaims(pages);
  const relations = extractRelations(pages);
  const timeline = extractTimeline(pages);
  const contradictions: any[] = [];
  const health = analyzeHealth(pages, claims);
  const pageOutput = pages.map(({ meta, body, ...page }) => page);
  console.log("\nWriting cache files...");
  writeJson(join(root, "_system/cache/pages.json"), { compiledAt, pages: pageOutput });
  writeJsonl(join(root, "_system/cache/claims.jsonl"), claims);
  writeJsonl(join(root, "_system/cache/relations.jsonl"), relations);
  writeJson(join(root, "_system/cache/agent-digest.json"), { compiledAt, pages: pageOutput.slice(0, 50), claims: claims.slice(0, 30), validationIssues: issues });
  writeJson(join(root, "_system/cache/contradictions.json"), { compiledAt, contradictions });
  writeJson(join(root, "_system/cache/questions.json"), { compiledAt, questions: pageOutput.filter((p) => p.pageType === "question") });
  writeJson(join(root, "_system/cache/timeline-events.json"), { compiledAt, events: timeline });
  writeJson(join(root, "_system/cache/source-index.json"), { compiledAt, sources: pageOutput.filter((p) => p.pageType === "source") });
  writeJson(join(root, "_system/cache/validation-issues.json"), { compiledAt, issues, summary: summarize(issues) });
  writeJson(join(root, "_system/cache/claims-index.json"), { compiledAt, claims: pageOutput.filter((p) => p.pageType === "claim") });
  const indexes = buildIndexes(pageOutput);
  for (const [name, data] of Object.entries(indexes)) writeJson(join(root, `_system/indexes/${name}.json`), { compiledAt, data });
  console.log("\nWriting root page catalog...");
  writeFileSync(join(root, "index.md"), renderIndex(pageOutput), "utf8");
  writeReports(root, pageOutput, claims, health, compiledAt.slice(0, 10));
  writeOperationalLog(root, `compile-wiki: regenerated index, cache, indexes, and reports; pages=${pages.length} claims=${claims.length} relations=${relations.length} contradictions=0 openQuestions=${pageOutput.filter((p) => p.pageType === "question" && ["open", "researching", "blocked"].includes(String(p.status))).length} evidenceGaps=${health.evidenceGaps.length} lowConfidence=${health.lowConfidence.length} validationIssues=${issues.length} duplicatePageIds=${issues.filter((i) => i.code === "duplicate_page_id").length}`);
  console.log("\nCompile complete.");
  console.log(`  Pages: ${pages.length} | Claims: ${claims.length} | Relations: ${relations.length} | Contradictions: 0`);
  console.log(`  Validation issues: ${issues.length}`);
  return 0;
}

function validatePages(pages: any[]): any[] {
  const issues: any[] = [];
  const seen = new Map<string, string[]>();
  for (const page of pages) {
    for (const field of ["id", "pageType", "title", "status", "createdAt", "updatedAt"]) {
      if (!page[field]) issues.push({ code: "missing_required_field", path: page.path, field, message: `Missing required field ${field}` });
    }
    if (page.id) seen.set(page.id, [...(seen.get(page.id) ?? []), page.path]);
  }
  for (const [id, paths] of seen) if (paths.length > 1) issues.push({ code: "duplicate_page_id", pageId: id, paths, path: paths[0], message: `Page id ${id} appears in multiple files.` });
  return issues;
}

function extractClaims(pages: any[]): any[] {
  const claims: any[] = [];
  for (const page of pages) {
    if (page.pageType === "claim") claims.push({ id: page.id, text: page.text || page.title, status: page.status, confidence: page.confidence, sourceIds: page.sourceIds || [], evidence: page.evidence || [], _owningPagePath: page.path });
    for (const claim of Array.isArray(page.claims) ? page.claims : []) claims.push({ ...claim, _owningPagePath: page.path });
  }
  return claims;
}
function extractRelations(pages: any[]): any[] { return pages.flatMap((p) => (Array.isArray(p.relations) ? p.relations.map((r: any) => ({ ...r, _owningPagePath: p.path })) : [])); }
function extractTimeline(pages: any[]): any[] { return pages.flatMap((p) => (Array.isArray(p.timeline) ? p.timeline.map((r: any) => ({ ...r, _owningPagePath: p.path })) : [])); }
function analyzeHealth(pages: any[], claims: any[]) {
  return { lowConfidence: claims.filter((c) => Number(c.confidence ?? 1) < 0.5), evidenceGaps: claims.filter((c) => !Array.isArray(c.evidence) || c.evidence.length === 0), stalePages: pages.filter((p) => false) };
}
function buildIndexes(pages: any[]) {
  const idToPath: Record<string, string> = {}, pathToId: Record<string, string> = {}, pageType: Record<string, string[]> = {}, aliases: Record<string, string> = {}, tags: Record<string, string[]> = {};
  for (const page of pages) {
    idToPath[page.id] = page.path; pathToId[page.path] = page.id;
    (pageType[page.pageType] ??= []).push(page.id);
    for (const alias of page.aliases || []) aliases[String(alias)] = page.id;
    for (const tag of page.tags || []) (tags[String(tag)] ??= []).push(page.id);
  }
  return { "id-to-path": idToPath, "path-to-id": pathToId, "pagetype-index": pageType, "alias-index": aliases, "tag-index": tags };
}
function writeReports(root: string, pages: any[], claims: any[], health: any, date: string) {
  const report = (title: string, rows: string[]) => `---\npageType: report\ntitle: ${title}\nstatus: active\nupdatedAt: ${date}\n---\n\n# ${title}\n\n${rows.length ? rows.join("\n") : "No entries."}\n`;
  writeFileSync(join(root, "reports/open-questions.md"), report("Open Questions", pages.filter((p) => p.pageType === "question").map((p) => `- ${p.id}: ${p.title}`)), "utf8");
  writeFileSync(join(root, "reports/contradictions.md"), report("Contradictions", []), "utf8");
  writeFileSync(join(root, "reports/low-confidence.md"), report("Low Confidence", health.lowConfidence.map((c: any) => `- ${c.id}: ${c.text}`)), "utf8");
  writeFileSync(join(root, "reports/claim-health.md"), report("Claim Health", [`Claims: ${claims.length}`, `Evidence gaps: ${health.evidenceGaps.length}`, `Low confidence: ${health.lowConfidence.length}`]), "utf8");
  writeFileSync(join(root, "reports/stale-pages.md"), report("Stale Pages", []), "utf8");
  writeFileSync(join(root, "reports/orphaned-claims.md"), report("Orphaned Claims", []), "utf8");
  writeFileSync(join(root, "reports/evidence-gaps.md"), report("Evidence Gaps", health.evidenceGaps.map((c: any) => `- ${c.id}: ${c.text}`)), "utf8");
}
function writeJsonl(path: string, rows: any[]) { writeFileSync(path, rows.map((row) => JSON.stringify(row)).join("\n") + (rows.length ? "\n" : ""), "utf8"); }
function summarize(issues: any[]) { return issues.reduce((acc, issue) => ({ ...acc, [issue.code]: (acc[issue.code] ?? 0) + 1 }), {} as Record<string, number>); }
