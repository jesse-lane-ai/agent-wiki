import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { WorkspaceScanConfig } from "../src/config.js";
import { loadState, markSourced, scanWorkspace, updateStateFromScan } from "../src/workspace.js";

const defaultScan: WorkspaceScanConfig = {
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

function tempDir(): string {
  return mkdtempSync(join(tmpdir(), "agent-wiki-test-"));
}

test("scan excludes wiki and code-heavy directories", () => {
  const root = tempDir();
  try {
    const wiki = join(root, "wiki");
    mkdirSync(join(root, "docs"), { recursive: true });
    mkdirSync(join(root, "node_modules/pkg"), { recursive: true });
    mkdirSync(join(root, "_system/cache"), { recursive: true });
    mkdirSync(wiki);
    writeFileSync(join(root, "docs/research.md"), "research", "utf8");
    writeFileSync(join(wiki, "sources.md"), "canonical", "utf8");
    writeFileSync(join(root, "app.py"), "print('skip')", "utf8");
    writeFileSync(join(root, "node_modules/pkg/readme.md"), "skip", "utf8");
    writeFileSync(join(root, "_system/cache/pages.json"), "{}", "utf8");

    const files = scanWorkspace(root, wiki, defaultScan);
    assert.deepEqual(files.map((item) => item.relativePath), ["docs/research.md"]);
    assert.equal(files[0].recommendedSourceType, "document");
    assert.equal(files[0].reason, "new");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("pending detects changed files from state", () => {
  const root = tempDir();
  try {
    const wiki = join(root, "wiki");
    mkdirSync(wiki);
    const source = join(root, "notes.md");
    writeFileSync(source, "first", "utf8");
    const state = loadState(wiki);
    updateStateFromScan(wiki, scanWorkspace(root, wiki, defaultScan, { state }), state);
    writeFileSync(source, "second", "utf8");
    const changedScan = scanWorkspace(root, wiki, defaultScan, { state: loadState(wiki) });
    assert.equal(changedScan.length, 1);
    assert.equal(changedScan[0].reason, "changed");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("state preserves source mapping", () => {
  const root = tempDir();
  try {
    const wiki = join(root, "wiki");
    const statePath = join(wiki, "_system/state/workspace-sources.json");
    mkdirSync(join(wiki, "_system/state"), { recursive: true });
    writeFileSync(join(root, "memo.txt"), "memo", "utf8");
    writeFileSync(
      statePath,
      JSON.stringify({
        schemaVersion: 1,
        files: {
          "memo.txt": {
            sha256: "old",
            sourceId: "source.2026-06-26.document.memo",
            sourcePath: "sources/2026-06-26-document-memo.md"
          }
        }
      }),
      "utf8"
    );
    const files = scanWorkspace(root, wiki, defaultScan, { state: loadState(wiki) });
    assert.equal(files[0].alreadySourced, true);
    assert.equal(files[0].sourceId, "source.2026-06-26.document.memo");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("mark sourced records mapping", () => {
  const root = tempDir();
  try {
    const wiki = join(root, "wiki");
    markSourced(wiki, loadState(wiki), {
      relativePath: "docs/research.md",
      sourceId: "source.2026-06-26.document.research",
      sourcePath: "sources/2026-06-26-document-research.md"
    });
    const stored: any = JSON.parse(readFileSync(join(wiki, "_system/state/workspace-sources.json"), "utf8"));
    assert.equal(stored.files["docs/research.md"].sourceId, "source.2026-06-26.document.research");
    assert.equal(stored.files["docs/research.md"].sourcePath, "sources/2026-06-26-document-research.md");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
