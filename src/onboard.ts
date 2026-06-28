import { existsSync } from "node:fs";
import { join } from "node:path";
import { loadConfig } from "./config.js";
import { doctorWiki, writeLocalConfig } from "./lifecycle.js";
import { writeJson } from "./wiki-utils.js";

export function onboard(args: Record<string, unknown>): number {
  const root = process.cwd();
  if (args["write-config"]) {
    const wikiType = String(args.type || loadConfig(root).wikiType);
    if (wikiType !== "vault" && wikiType !== "workspace") throw new Error("--type must be vault or workspace");
    writeLocalConfig(root, wikiType, null, String(args["wiki-dir"] || "wiki"));
    const config: any = loadConfig(root);
    const path = join(root, "_system/config.json");
    if (args["python-command"]) config.pythonCommand = args["python-command"];
    config.conversion = { enabled: args.conversion && args.conversion !== "disabled", policy: args.conversion || "disabled" };
    writeJson(path, { schemaVersion: 1, wikiType, workspace: { root: null, wikiDir: String(args["wiki-dir"] || "wiki") }, pythonCommand: args["python-command"] || null, conversion: config.conversion });
    console.log(`Wrote _system/config.json`);
    return 0;
  }
  const report = {
    schemaVersion: 1,
    wikiType: loadConfig(root).wikiType,
    root,
    configExists: existsSync(join(root, "_system/config.json")),
    folders: doctorWiki(root).filter((i) => i.code === "missing_folder").map((i) => i.path),
    issues: doctorWiki(root)
  };
  if (args.questions) {
    console.log(`Folders (${report.wikiType} mode): ${report.folders.length ? "missing folders detected" : "looks ready"}`);
    console.log("A. Run agent-wiki init for this wiki type.");
    console.log("B. Leave as-is and continue read-only.");
  } else {
    console.log(JSON.stringify(report, null, args.compact ? undefined : 2));
  }
  return 0;
}
