import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const NPM = process.platform === "win32" ? "npm.cmd" : "npm";
const BIN = process.platform === "win32" ? "agent-wiki.cmd" : "agent-wiki";
const WINDOWS_EXEC = process.platform === "win32" ? { shell: true } : {};

test("packed npm tarball works through node_modules bin shim", () => {
  const tmp = mkdtempSync(join(tmpdir(), "agent-wiki-pack-"));
  let tarball = "";
  try {
    const tarballName = execFileSync(NPM, ["pack", "--silent"], { cwd: REPO_ROOT, encoding: "utf8", ...WINDOWS_EXEC }).trim().split("\n").at(-1);
    assert.ok(tarballName);
    tarball = join(REPO_ROOT, tarballName);
    execFileSync(NPM, ["init", "-y"], { cwd: tmp, stdio: "ignore", ...WINDOWS_EXEC });
    execFileSync(NPM, ["install", tarball], { cwd: tmp, stdio: "ignore", ...WINDOWS_EXEC });
    const bin = join(tmp, "node_modules/.bin", BIN);

    assert.match(execFileSync(bin, ["--help"], { cwd: tmp, encoding: "utf8", ...WINDOWS_EXEC }), /Commands:/);
    const initOut = execFileSync(bin, ["init", "--type", "vault", "--root", "wiki", "--write-config", "--with-template"], { cwd: tmp, encoding: "utf8", ...WINDOWS_EXEC });
    assert.match(initOut, /Initialized vault wiki/);
    assert.ok(existsSync(join(tmp, "wiki/package.json")));
    assert.ok(!existsSync(join(tmp, "wiki/_system/scripts")));

    const bodyPath = join(tmp, "body.md");
    writeFileSync(bodyPath, "Dogfood source body for the packaged command line.\n", "utf8");
    execFileSync(bin, ["create-page", "--type", "source", "--subtype", "document", "--slug", "dogfood-source", "--title", "Dogfood Source", "--origin-path", "raw/dogfood.md", "--source-date", "2026-06-28", "--body-file", bodyPath], { cwd: join(tmp, "wiki"), stdio: "pipe", ...WINDOWS_EXEC });
    execFileSync(bin, ["compile"], { cwd: join(tmp, "wiki"), stdio: "pipe", ...WINDOWS_EXEC });
    execFileSync(bin, ["index", "--check"], { cwd: join(tmp, "wiki"), stdio: "pipe", ...WINDOWS_EXEC });
    const pending = JSON.parse(execFileSync(bin, ["workspace", "pending", "--workspace-root", tmp, "--wiki-dir", "wiki", "--json"], { cwd: tmp, encoding: "utf8", ...WINDOWS_EXEC }));
    assert.ok(Array.isArray(pending));
    assert.equal(readFileSync(join(tmp, "wiki/_system/cache/pages.json"), "utf8").includes("dogfood-source"), true);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
    if (tarball) rmSync(tarball, { force: true });
  }
});
