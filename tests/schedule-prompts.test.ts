import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const CLI = join(REPO_ROOT, "dist/src/cli.js");

test("schedule prompt renders skill-based maintenance prompt for all registered wikis", () => {
  const temp = mkdtempSync(join(tmpdir(), "agent-wiki-schedule-"));
  const env = { ...process.env, AGENT_WIKI_REGISTRY_PATH: join(temp, "registry.json") };
  try {
    registerWiki(env, temp, "Business");
    registerWiki(env, temp, "Research");

    const out = execFileSync("node", [CLI, "schedule", "prompt", "process-inbox"], { env, encoding: "utf8" });
    assert.match(out, /Scheduled Agent Wiki job: process new inbox notes/);
    assert.match(out, /agent-wiki list --json/);
    assert.match(out, /skills\/process-inbox\/SKILL\.md/);
    assert.match(out, /Business:/);
    assert.match(out, /Research:/);
    assert.match(out, /If one wiki fails, log the error/);
    assert.match(out, /Act without asking/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test("process-inbox schedule prompt routes workspace wikis to process-workspace-sources", () => {
  const temp = mkdtempSync(join(tmpdir(), "agent-wiki-schedule-"));
  const env = { ...process.env, AGENT_WIKI_REGISTRY_PATH: join(temp, "registry.json") };
  try {
    registerWiki(env, temp, "Business");
    registerWorkspaceWiki(env, temp, "Project");

    const out = execFileSync("node", [CLI, "schedule", "prompt", "process-inbox"], { env, encoding: "utf8" });
    assert.match(out, /Business:/);
    assert.match(out, /Project: .*workspace wiki; use skills\/process-workspace-sources\/SKILL\.md/);
    assert.match(out, /process-inbox\/SKILL\.md` instructions for vault wikis/);
    assert.match(out, /process-workspace-sources\/SKILL\.md` instructions for workspace wikis/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

test("schedule prompt can target selected registered wikis by positional name or flag", () => {
  const temp = mkdtempSync(join(tmpdir(), "agent-wiki-schedule-"));
  const env = { ...process.env, AGENT_WIKI_REGISTRY_PATH: join(temp, "registry.json") };
  try {
    registerWiki(env, temp, "Business");
    registerWiki(env, temp, "Research");

    const extract = execFileSync("node", [CLI, "schedule", "prompt", "extract-primitives", "Business"], {
      env,
      encoding: "utf8"
    });
    assert.match(extract, /extract knowledge primitives/);
    assert.match(extract, /skills\/extract-knowledge-primitives\/SKILL\.md/);
    assert.match(extract, /Business:/);
    assert.doesNotMatch(extract, /Research:/);

    const overview = execFileSync("node", [CLI, "schedule", "prompt", "update-overview", "--wiki", "Research"], {
      env,
      encoding: "utf8"
    });
    assert.match(overview, /compile and refresh overview/);
    assert.match(overview, /skills\/update-overview\/SKILL\.md/);
    assert.match(overview, /Research:/);
    assert.doesNotMatch(overview, /Business:/);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

function registerWiki(env: NodeJS.ProcessEnv, temp: string, name: string): void {
  const wiki = join(temp, name);
  execFileSync("node", [CLI, "init", "--type", "vault", "--root", wiki], { env, encoding: "utf8" });
  execFileSync("node", [CLI, "registry", "add", name, "--root", wiki], { env, encoding: "utf8" });
}

function registerWorkspaceWiki(env: NodeJS.ProcessEnv, temp: string, name: string): void {
  const workspace = join(temp, name);
  const wiki = join(workspace, "wiki");
  execFileSync("node", [CLI, "init", "--type", "workspace", "--workspace-root", workspace, "--wiki-dir", "wiki"], {
    env,
    encoding: "utf8"
  });
  execFileSync("node", [CLI, "registry", "add", name, "--root", wiki], { env, encoding: "utf8" });
}
