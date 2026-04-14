---
name: process-new-notes
description: "Process unprocessed items in the Agentics vault inbox. Use this skill whenever the user says \"process new notes\", \"check the inbox\", \"process the inbox\", \"handle new notes\", \"process the queue\", \"ingest notes\", or wants to convert raw captured content into structured wiki source pages. This skill reads the vault agent contract, scans _inbox/ for unprocessed pointer files, reads each linked source file, and updates its frontmatter to match the v1 source schema. Trigger any time the user mentions inbox processing, note ingestion, or structuring raw sources — even if they don't use those exact words."
---
 
# Process New Notes
 
This skill captures the workflow for processing the Agentics vault inbox: reading raw source files and promoting them to canonical, schema-compliant source pages.
 
## Step 1: Read the Vault Contract
 
Before touching anything, read the vault's agent contract in this order:
 
1. [[AGENTS]] — the behavioral contract (managed blocks, ID rules, what agents may/must not do)
2. [[AGENT-WIKI-SPEC-v1]] — the full v1 schema
 
You need to understand the contract before editing anything. The key things from AGENTS.md that apply here:
- Never rewrite human content outside managed blocks
- Use stable dotted-namespace IDs (`source.<namespace>.<slug>`)
- Update `updatedAt` when you change structured content
- Do not invent certainty
 
## Step 2: Check the Inbox
 
Read all files in `_inbox/` (excluding `_inbox/trash/`). Look for pointer files with `status: UNPROCESSED`. Each pointer has:
 
```yaml
id: <inbox-item-id>
pointer: "[[sources/<filename>]]"
status: UNPROCESSED
```
 
If the inbox is empty or all items are already processed, tell the user and stop.
 
## Step 3: Process Each Source File
 
For each unprocessed pointer, work through them one at a time:
 
### 3a. Read the source file
 
The `pointer:` field is a wikilink to the raw source file. Resolve it to the file path and read it fully — the content is what you use to fill the frontmatter.
 
### 3b. Infer frontmatter fields from content
 
Generate a complete source frontmatter block. Use the schema below.
Source pages use the normal page status vocabulary from [[WIKI]]; after intake, they should usually be `active`, not `processed`.
 
**ID format:** `source.<namespace>.<slug>`
- `namespace`: author handle, platform name, or topic area (e.g., `nav-toor`, `timothy-carbat`, `youtube`)
- `slug`: short kebab-case descriptor of the content (e.g., `ai-income-stack-2026`, `minimax-m2-7-review`)
 
**sourceType** — infer from content:
- YouTube transcript → `transcript`
- X/Twitter post → `webpage`
- Article or blog post → `article`
- PDF → `pdf`
- Email → `email`
- Meeting notes → `meeting-notes`
- Raw data → `dataset`
- Screenshot → `screenshot`
- Unknown → `other`
 
**Required fields:**
 
```yaml
id: source.<namespace>.<slug>
pageType: source
title: "<title from content>"
status: active
sourceType: <inferred>
originUrl: <url if present in content>
author: <author if present>
publishedAt: <date if known, else omit>
retrievedAt: <date found in content or today's date>
createdAt: <today's date>
updatedAt: <today's date>
aliases:
  - <alternate names or IDs>
tags:
  - <relevant topical tags>
attachments:
  - <paths to any referenced attachments>
```
 
**Preserve user context.** If the source file contains a user-added note or context block (e.g., a blockquote, a `## User Context` section, or any human annotation), keep it intact in the file body. Do not remove it. You may mirror a short summary as a `userContext:` field in the frontmatter if useful.
 
### 3c. Edit the source file in place
 
Prepend the frontmatter block to the top of the file. Do not remove, rewrite, or restructure any existing content — only add the `---` frontmatter block above the first line. If the file already has frontmatter, update it rather than duplicating.
 
## Step 4: Mark the Inbox Pointer as Processed
 
For each pointer you've finished:
 
1. **Create a copy in `_inbox/trash/`** with `status: PROCESSED`
2. **Update the original pointer** in `_inbox/` to `status: PROCESSED`
 
If physical deletion of the original isn't possible (permission denied), updating the status in place is acceptable — the active queue is defined by `status: UNPROCESSED`, so a `PROCESSED` item is effectively out of queue.
 
## Step 5: Report to the User
 
After processing all items, give a concise summary:
 
- How many items were processed
- The ID assigned to each source
- Any items skipped and why (e.g., already processed, source file missing)
 
Keep it brief — the user can open the files to inspect details.
 
## Important Rules
 
- **Edit in place** — The source files stay in `sources/` with updated frontmatter.
- **Do not touch human prose** — only add/update the frontmatter block.
- **Do not invent metadata** — if a field (like `publishedAt` or `author`) can't be inferred from content, omit it rather than guessing.
- **Stable IDs** — once you assign an ID, note it. Never regenerate or change it in a subsequent pass.
