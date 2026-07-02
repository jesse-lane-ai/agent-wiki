import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const CLI = join(REPO_ROOT, "dist/src/cli.js");

test("machine-local registry tracks named Agent Wiki roots", () => {
  const temp = mkdtempSync(join(tmpdir(), "agent-wiki-registry-"));
  const wiki = join(temp, "Business");
  const registry = join(temp, "registry.json");
  const env = { ...process.env, AGENT_WIKI_REGISTRY_PATH: registry };
  try {
    execFileSync("node", [CLI, "init", "--type", "vault", "--root", wiki], { env, encoding: "utf8" });
    const add = execFileSync("node", [CLI, "registry", "add", "Business", "--root", wiki], { env, encoding: "utf8" });
    assert.match(add, /Registered Business/);

    const list = execFileSync("node", [CLI, "list"], { env, encoding: "utf8" });
    assert.match(list, /Business/);
    assert.match(list, /vault/);
    assert.match(list, new RegExp(escapeRegExp(wiki)));

    const doctor = execFileSync("node", [CLI, "--wiki", "Business", "doctor", "--json"], { env, encoding: "utf8" });
    assert.deepEqual(JSON.parse(doctor), []);

    const light = JSON.parse(execFileSync("node", [CLI, "check", "--all", "--json"], { env, encoding: "utf8" }));
    assert.equal(light.results[0].name, "Business");
    assert.equal(light.results[0].ok, true);
    assert.equal(light.results[0].compileStatus, "skipped");

    const full = JSON.parse(execFileSync("node", [CLI, "check", "--all", "--full", "--json"], { env, encoding: "utf8" }));
    assert.equal(full.results[0].ok, true);
    assert.equal(full.results[0].compileStatus, "passed");
    assert.equal(full.results[0].indexStatus, "current");
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
});

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
