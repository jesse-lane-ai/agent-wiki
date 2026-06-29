import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const CLI = join(REPO_ROOT, "dist/src/cli.js");

test("onboard check emits deterministic JSON report", () => {
  const root = mkdtempSync(join(tmpdir(), "agent-wiki-onboard-"));
  try {
    execFileSync("node", [CLI, "init", "--type", "vault", "--root", root, "--write-config", "--with-template"], { encoding: "utf8" });
    const report = JSON.parse(execFileSync("node", [CLI, "onboard", "--check", "--wiki-root", root], { encoding: "utf8" }));
    assert.equal(report.schemaVersion, 1);
    assert.equal(report.command, "agent-wiki onboard --check");
    assert.equal(report.root, root);
    assert.equal(report.wiki.type, "vault");
    assert.equal(report.wiki.configExists, true);
    assert.equal(report.doctor.passed, true);
    assert.equal(report.summary.ready, true);
    assert.ok(Array.isArray(report.nextSteps));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("onboard questions emits stable numbered prompts", () => {
  const root = mkdtempSync(join(tmpdir(), "agent-wiki-onboard-"));
  try {
    execFileSync("node", [CLI, "init", "--type", "vault", "--root", root, "--write-config", "--with-template"], { encoding: "utf8" });
    const out = execFileSync("node", [CLI, "onboard", "--check", "--questions", "--wiki-root", root], { encoding: "utf8" });
    assert.match(out, /1\. Wiki type: vault/);
    assert.match(out, /2\. Local config: present/);
    assert.match(out, /4\. Optional conversion policy/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
