import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const CLI = join(REPO_ROOT, "dist/src/cli.js");

test("migrate v1 reports and applies safe v2 upgrade changes", () => {
  const root = mkdtempSync(join(tmpdir(), "agent-wiki-migrate-"));
  try {
    createOldWiki(root);

    const check = JSON.parse(execFileSync("node", [CLI, "migrate", "--from", "v1", "--check"], { cwd: root, encoding: "utf8" }));
    assert.equal(check.mode, "check");
    assert.ok(check.counts.remove >= 4);
    assert.ok(check.counts.rewrite >= 2);
    assert.ok(existsSync(join(root, "_system/scripts/create-page.py")));

    const write = JSON.parse(execFileSync("node", [CLI, "migrate", "--from", "v1", "--write"], { cwd: root, encoding: "utf8" }));
    assert.equal(write.mode, "write");
    assert.ok(!existsSync(join(root, "_system/scripts/create-page.py")));
    assert.ok(!existsSync(join(root, "_system/skills/compile-wiki/scripts/compile.py")));
    assert.ok(!existsSync(join(root, "_system/skills/import-link/scripts/uuid.py")));
    assert.ok(!existsSync(join(root, "skills/compile-wiki/scripts/compile.py")));
    assert.ok(!existsSync(join(root, "agent_wiki")));
    assert.equal(JSON.parse(readFileSync(join(root, "_system/config.json"), "utf8")).wikiType, "vault");
    assert.match(readFileSync(join(root, "README.md"), "utf8"), /agent-wiki create-page/);
    assert.match(readFileSync(join(root, "README.md"), "utf8"), /AGENT-WIKI-SPEC-v2/);
    assert.match(readFileSync(join(root, "skills/process-inbox/SKILL.md"), "utf8"), /agent-wiki compile/);
    assert.match(readFileSync(join(root, "_system/skills/legacy/SKILL.md"), "utf8"), /AGENT-WIKI-SPEC-v2/);
    assert.ok(existsSync(join(root, "_archive/migrations/v1-to-v2")));
    assert.ok(existsSync(join(root, "_system/cache/pages.json")));
    assert.match(execFileSync("node", [CLI, "index", "--check"], { cwd: root, encoding: "utf8" }), /index\.md is current/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

function createOldWiki(root: string): void {
  for (const dir of ["_system/scripts", "_system/skills/legacy", "_system/skills/compile-wiki/scripts", "_system/skills/import-link/scripts", "skills/compile-wiki/scripts", "skills/process-inbox", "agent_wiki", "sources", "_system/cache", "_system/indexes", "_system/logs"]) {
    mkdirSync(join(root, dir), { recursive: true });
  }
  writeFileSync(join(root, "pyproject.toml"), "[project]\nname = \"agent-wiki\"\n", "utf8");
  writeFileSync(join(root, "_system/config.json"), "{\"schemaVersion\":1,\"pythonCommand\":\"python\"}\n", "utf8");
  writeFileSync(join(root, "agent_wiki/cli.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/scripts/create-page.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/scripts/onboard.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/scripts/log.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/scripts/index.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/scripts/migrate-refs-to-links.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/skills/compile-wiki/scripts/compile.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "_system/skills/import-link/scripts/uuid.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "skills/compile-wiki/scripts/compile.py"), "print('old')\n", "utf8");
  writeFileSync(join(root, "README.md"), "Read AGENT-WIKI-SPEC-v1.md, run python3 _system/scripts/create-page.py then python3 skills/compile-wiki/scripts/compile.py\n", "utf8");
  writeFileSync(join(root, "_system/skills/legacy/SKILL.md"), "Read AGENT-WIKI-SPEC-v1.md and _system/scripts/create-page.py\n", "utf8");
  writeFileSync(join(root, "skills/process-inbox/SKILL.md"), "Use _system/scripts/create-page.py and skills/compile-wiki/scripts/compile.py\n", "utf8");
  writeFileSync(join(root, "sources/example.md"), "---\nid: source.2026-06-28.document.example\npageType: source\ntitle: Example\nstatus: unprocessed\ncreatedAt: 2026-06-28\nupdatedAt: 2026-06-28\naliases: []\ntags: []\n---\n\nExample body.\n", "utf8");
}
