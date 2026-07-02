import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { doctorWiki, initWiki } from "../src/lifecycle.js";

function tempDir(): string {
  return mkdtempSync(join(tmpdir(), "agent-wiki-test-"));
}

test("init vault creates expected folders, config, and template by default", () => {
  const tmp = tempDir();
  try {
    const root = join(tmp, "vault");
    const result = initWiki({ wikiType: "vault", root, writeConfig: true, withTemplate: true });
    assert.equal(result.wikiType, "vault");
    assert.ok(readJson(join(root, "_system/config.json")).wikiType === "vault");
    assert.doesNotThrow(() => readFileSync(join(root, "_system/config.json"), "utf8"));
    assert.ok(isDir(join(root, "sources/parts")));
    assert.ok(isDir(join(root, "skills")));
    assert.ok(isFile(join(root, "AGENTS.md")));
    assert.ok(isFile(join(root, "skills/process-inbox/SKILL.md")));
    assert.ok(!isDir(join(root, "_system/skills")));
    assert.ok(isDir(join(root, "_inbox/trash")));
    assert.ok(isDir(join(root, "raw")));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("init workspace creates wiki inside workspace with inbox lifecycle", () => {
  const tmp = tempDir();
  try {
    const workspace = join(tmp, "project");
    const result = initWiki({ wikiType: "workspace", workspaceRoot: workspace, wikiDir: "wiki", writeConfig: true });
    const wiki = join(workspace, "wiki");
    assert.equal(result.workspaceRoot, workspace);
    assert.ok(isDir(join(wiki, "sources/parts")));
    assert.ok(isDir(join(wiki, "skills")));
    assert.ok(!isDir(join(wiki, "_system/skills")));
    assert.ok(isDir(join(wiki, "_inbox/trash")));
    assert.ok(isDir(join(wiki, "raw")));
    const config = readJson(join(wiki, "_system/config.json"));
    assert.equal(config.wikiType, "workspace");
    assert.equal(config.workspace.wikiDir, "wiki");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("init with template copies docs and skills", () => {
  const tmp = tempDir();
  try {
    const root = join(tmp, "vault");
    const result = initWiki({ wikiType: "vault", root, writeConfig: true, withTemplate: true });
    assert.ok(result.templateCopied.length > 0);
    assert.ok(isFile(join(root, "AGENTS.md")));
    assert.ok(isFile(join(root, "WIKI.md")));
    assert.ok(!isFile(join(root, "package.json")));
    assert.ok(isFile(join(root, "skills/process-inbox/SKILL.md")));
    const issues = doctorWiki(root, "vault");
    assert.equal(issues.some((issue) => issue.level === "error" || issue.level === "warning"), false);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("init with template does not overwrite existing files", () => {
  const tmp = tempDir();
  try {
    const root = join(tmp, "vault");
    mkdirSync(root);
    const existing = join(root, "AGENTS.md");
    writeFileSync(existing, "custom\n", "utf8");
    initWiki({ wikiType: "vault", root, withTemplate: true });
    assert.equal(readFileSync(existing, "utf8"), "custom\n");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("doctor reports missing template files as warnings", () => {
  const tmp = tempDir();
  try {
    const root = join(tmp, "vault");
    initWiki({ wikiType: "vault", root });
    const issues = doctorWiki(root, "vault");
    assert.equal(issues.some((issue) => issue.level === "error"), false);
    assert.equal(issues.some((issue) => issue.code === "missing_template_file"), true);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("init can create a bare skeleton without config or template", () => {
  const tmp = tempDir();
  try {
    const root = join(tmp, "vault");
    initWiki({ wikiType: "vault", root, writeConfig: false, withTemplate: false });
    assert.ok(isDir(join(root, "sources/parts")));
    assert.ok(!isFile(join(root, "_system/config.json")));
    assert.ok(!isFile(join(root, "AGENTS.md")));
    assert.ok(!isFile(join(root, "skills/process-inbox/SKILL.md")));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

function readJson(path: string): any {
  return JSON.parse(readFileSync(path, "utf8"));
}

function isDir(path: string): boolean {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

function isFile(path: string): boolean {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}
