import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToWikilink, refToWikilink, walkMarkdownPages } from "./wiki-utils.js";

const ID_FIELDS = ["sourcePages", "derivedClaims", "relatedPages", "relatedClaims", "extractedEntities", "extractedConcepts", "extractedClaims", "extractedQuestions"];

export function migrateRefs(args: Record<string, unknown>): number {
  const root = String(args.root || process.cwd());
  const write = Boolean(args.write);
  let changed = 0;
  for (const page of walkMarkdownPages(root)) {
    const path = join(root, page.path);
    let text = readFileSync(path, "utf8");
    const original = text;
    for (const field of ID_FIELDS) {
      text = text.replace(new RegExp(`(^${field}:\\n(?:\\s+-\\s+)([^\\n]+)(?:\\n\\s+-\\s+[^\\n]+)*)`, "gm"), (block) =>
        block.replace(/^(\s+-\s+)(.+)$/gm, (_m: string, prefix: string, value: string) => `${prefix}${refToWikilink(value.trim())}`)
      );
    }
    text = text.replace(/^(originPath:\s*)(.+)$/gm, (_m, prefix, value) => `${prefix}${pathToWikilink(String(value).trim())}`);
    if (text !== original) {
      changed += 1;
      if (write) writeFileSync(path, text, "utf8");
      console.log(`${write ? "updated" : "would update"} ${page.path}`);
    }
  }
  console.log(`${write ? "Updated" : "Would update"} ${changed} files.`);
  return 0;
}
