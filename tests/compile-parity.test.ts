import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("TypeScript compile matches old Python compiler for core fixture artifacts", { skip: !hasCommand("python3") }, () => {
  const tmp = mkdtempSync(join(tmpdir(), "agent-wiki-parity-"));
  try {
    const oldRoot = join(tmp, "old");
    const newRoot = join(tmp, "new");
    createFixture(oldRoot);
    createFixture(newRoot);
    installOldScripts(oldRoot);

    execFileSync("python3", ["skills/compile-wiki/scripts/compile.py"], { cwd: oldRoot, stdio: "pipe" });
    execFileSync("node", [join(REPO_ROOT, "dist/src/cli.js"), "compile"], { cwd: newRoot, stdio: "pipe" });

    assert.deepEqual(corePages(newRoot), corePages(oldRoot));
    assert.deepEqual(readJson(join(newRoot, "_system/indexes/id-to-path.json")).data, readJson(join(oldRoot, "_system/indexes/id-to-path.json")).data);
    assert.deepEqual(readJson(join(newRoot, "_system/indexes/path-to-id.json")).data, readJson(join(oldRoot, "_system/indexes/path-to-id.json")).data);
    assert.deepEqual(readJson(join(newRoot, "_system/indexes/pagetype-index.json")).data, readJson(join(oldRoot, "_system/indexes/pagetype-index.json")).data);
    assert.deepEqual(coreSourceIndex(newRoot), coreSourceIndex(oldRoot));
    assert.deepEqual(coreQuestions(newRoot), coreQuestions(oldRoot));
    assert.equal(readJsonLines(join(newRoot, "_system/cache/claims.jsonl")).length, readJsonLines(join(oldRoot, "_system/cache/claims.jsonl")).length);
    assert.equal(readJsonLines(join(newRoot, "_system/cache/relations.jsonl")).length, readJsonLines(join(oldRoot, "_system/cache/relations.jsonl")).length);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

function createFixture(root: string): void {
  for (const dir of ["sources", "entities", "concepts", "claims", "questions", "syntheses", "_system/cache", "_system/indexes", "_system/logs", "reports"]) {
    mkdirSync(join(root, dir), { recursive: true });
  }
  writeFileSync(
    join(root, "sources/2026-06-28-document-test-source.md"),
    page({
      id: "source.2026-06-28.document.test-source",
      pageType: "source",
      title: "Test Source",
      status: "processed",
      sourceType: "document",
      sourceRole: "whole",
      sourceParts: [],
      originPath: "[[raw/test-source|raw/test-source.md]]",
      retrievedAt: "2026-06-28",
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: ["Fixture Source"],
      tags: ["fixture"]
    }, "The source says the test project shipped a TypeScript command line interface."),
    "utf8"
  );
  writeFileSync(
    join(root, "entities/test-project.md"),
    page({
      id: "entity.project.test-project",
      pageType: "entity",
      title: "Test Project",
      status: "active",
      entityType: "project",
      canonicalName: "Test Project",
      sourcePages: ["[[2026-06-28-document-test-source|source.2026-06-28.document.test-source]]"],
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: [],
      tags: ["fixture"]
    }, "Test Project is a fixture entity used to compare compile output between implementations."),
    "utf8"
  );
  writeFileSync(
    join(root, "concepts/typescript-cli.md"),
    page({
      id: "concept.method.typescript-cli",
      pageType: "concept",
      title: "TypeScript CLI",
      status: "active",
      conceptType: "method",
      sourcePages: ["[[2026-06-28-document-test-source|source.2026-06-28.document.test-source]]"],
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: [],
      tags: ["fixture"]
    }, "A TypeScript CLI packages operational commands behind one installable Node entry point."),
    "utf8"
  );
  writeFileSync(
    join(root, "claims/descriptive-cli-shipped.md"),
    page({
      id: "claim.descriptive.cli-shipped",
      pageType: "claim",
      title: "CLI Shipped",
      status: "supported",
      claimType: "descriptive",
      confidence: 0.82,
      text: "The project ships a TypeScript CLI.",
      subjectPageId: "entity.project.test-project",
      sourceIds: ["source.2026-06-28.document.test-source"],
      evidence: [{
        id: "ev.cli-shipped.01",
        sourceId: "source.2026-06-28.document.test-source",
        path: "sources/2026-06-28-document-test-source.md",
        kind: "quote",
        relation: "supports",
        weight: 0.8,
        updatedAt: "2026-06-28"
      }],
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: [],
      tags: ["fixture"]
    }, "This claim records that the project ships a TypeScript CLI for parity testing."),
    "utf8"
  );
  writeFileSync(
    join(root, "questions/cli-parity.md"),
    page({
      id: "question.testing.cli-parity",
      pageType: "question",
      title: "CLI Parity",
      status: "open",
      priority: "medium",
      relatedClaims: ["[[claim-descriptive-cli-shipped|claim.descriptive.cli-shipped]]"],
      relatedPages: ["[[entity-project-test-project|entity.project.test-project]]"],
      openedAt: "2026-06-28",
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: [],
      tags: ["fixture"]
    }, "Does the TypeScript compiler preserve the old compiler's core artifact contract?"),
    "utf8"
  );
  writeFileSync(
    join(root, "syntheses/cli-rewrite-summary.md"),
    page({
      id: "synthesis.summary.cli-rewrite-summary",
      pageType: "synthesis",
      title: "CLI Rewrite Summary",
      status: "active",
      synthesisType: "summary",
      scope: "TypeScript CLI rewrite",
      sourcePages: ["[[2026-06-28-document-test-source|source.2026-06-28.document.test-source]]"],
      derivedClaims: ["[[claim-descriptive-cli-shipped|claim.descriptive.cli-shipped]]"],
      createdAt: "2026-06-28",
      updatedAt: "2026-06-28",
      aliases: [],
      tags: ["fixture"]
    }, "The rewrite summary fixture connects a source page and a standalone claim."),
    "utf8"
  );
}

function installOldScripts(root: string): void {
  for (const path of ["skills/compile-wiki/scripts/compile.py", "_system/scripts/index.py", "_system/scripts/log.py"]) {
    const destination = join(root, path);
    mkdirSync(destination.slice(0, destination.lastIndexOf("/")), { recursive: true });
    writeFileSync(destination, execFileSync("git", ["show", `HEAD^:${path}`], { cwd: REPO_ROOT, encoding: "utf8" }), "utf8");
  }
}

function page(frontmatter: Record<string, unknown>, body: string): string {
  return `---\n${yaml(frontmatter)}---\n\n${body}\n`;
}

function yaml(value: Record<string, unknown>, indent = 0): string {
  let out = "";
  for (const [key, item] of Object.entries(value)) {
    const prefix = " ".repeat(indent);
    if (Array.isArray(item)) {
      out += `${prefix}${key}:\n`;
      for (const entry of item) {
        if (entry && typeof entry === "object" && !Array.isArray(entry)) {
          const entries = Object.entries(entry);
          const [firstKey, firstValue] = entries[0];
          out += `${prefix}  - ${firstKey}: ${scalar(firstValue)}\n`;
          for (const [nestedKey, nestedValue] of entries.slice(1)) out += `${prefix}    ${nestedKey}: ${scalar(nestedValue)}\n`;
        } else {
          out += `${prefix}  - ${scalar(entry)}\n`;
        }
      }
    } else {
      out += `${prefix}${key}: ${scalar(item)}\n`;
    }
  }
  return out;
}

function scalar(value: unknown): string {
  return typeof value === "string" ? JSON.stringify(value) : String(value);
}

function corePages(root: string): unknown {
  return readJson(join(root, "_system/cache/pages.json")).pages.map((page: any) => ({
    id: page.id,
    path: page.path,
    pageType: page.pageType,
    title: page.title,
    status: page.status,
    updatedAt: page.updatedAt
  })).sort((a: any, b: any) => a.path.localeCompare(b.path));
}

function coreSourceIndex(root: string): unknown {
  return readJson(join(root, "_system/cache/source-index.json")).sources.map((source: any) => ({
    id: source.id,
    path: source.path,
    sourceType: source.sourceType,
    sourceRole: source.sourceRole,
    status: source.status
  }));
}

function coreQuestions(root: string): unknown {
  return readJson(join(root, "_system/cache/questions.json")).questions.map((question: any) => ({
    id: question.id,
    path: question.path,
    status: question.status,
    priority: question.priority
  }));
}

function readJson(path: string): any {
  return JSON.parse(readFileSync(path, "utf8"));
}

function readJsonLines(path: string): any[] {
  const text = readFileSync(path, "utf8").trim();
  return text ? text.split("\n").map((line) => JSON.parse(line)) : [];
}

function hasCommand(command: string): boolean {
  try {
    execFileSync(command, ["--version"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}
