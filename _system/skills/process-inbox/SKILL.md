---
name: process-inbox
description: "Process raw files dropped into the Agentics vault inbox. Use this skill whenever the user says \"process inbox\", \"check the inbox\", \"handle new notes\", \"process raw notes\", \"ingest inbox files\", or wants to convert raw files in _inbox/ into canonical source pages."
---

# Process Inbox

This skill promotes raw files from `_inbox/` into canonical, schema-compliant `source` pages. It does not extract entities, concepts, claims, questions, or relations; use `_system/skills/extract-knowledge-primitives/SKILL.md` after source pages exist.

## Step 1: Read the Vault Contract

Before touching anything, read the vault's agent contract in this order:

1. `AGENTS.md` - the behavioral contract.
2. `AGENT-WIKI-SPEC-v1.md` - the canonical schema.

Key rules for this workflow:
- Preserve raw content.
- Use stable source IDs.
- Do not invent metadata.
- Use Section 10 of `AGENT-WIKI-SPEC-v1.md` for the source page schema and examples.

## Step 2: Check the Inbox

Scan `_inbox/` for raw files. Ignore directories and hidden/system files. Do not treat `_inbox/trash/` or `raw/` as active queue locations.

If `_inbox/` is empty or contains no processable raw files, report that and stop.

## Step 3: Promote Each Raw File

For each raw file, work through files one at a time.

### 3a. Read the raw file

Read the file fully. Preserve the original content exactly when writing the source body.

### 3b. Infer source metadata

Create a source page using the canonical source page schema and example in `AGENT-WIKI-SPEC-v1.md` Section 10.1, "Source pages".

Newly promoted source pages MUST use `status: unprocessed`. The extraction workflow changes source pages to `status: processed` after knowledge primitives have been extracted.

Use this ID pattern:

```text
source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
```

- `yyyy-mm-dd`: processing date unless the raw file clearly includes a retrieval date.
- `sourceType`: the inferred source type from `AGENT-WIKI-SPEC-v1.md` Section 10.1, "Source pages".
- `sourceSlug`: short kebab-case descriptor, preferably four words.

Infer `sourceType` conservatively:
- YouTube transcript -> `transcript`
- Article or blog post -> `article`
- PDF -> `pdf`
- Email -> `email`
- Meeting notes -> `meeting-notes`
- Raw data -> `dataset`
- Screenshot -> `screenshot`
- Unknown or plain notes -> `other`

If a field such as `publishedAt`, `author`, or `originUrl` cannot be inferred, omit optional fields rather than guessing. For local raw files with no external URL, use `originPath` to record the retained raw file path after promotion. Required source fields must still follow `AGENT-WIKI-SPEC-v1.md` Section 10.1, "Source pages".

### 3c. Write the source page

Write the canonical source page to:

```text
sources/<yyyy-mm-dd>-<source-slug>.md
```

The body must contain the full verbatim raw content below the frontmatter. Preserve user context, annotations, and formatting.

### 3d. Move the raw file

After the source page is created successfully, move the original raw file to `raw/`.

Use a collision-resistant retained filename:

```text
raw/<yyyy-mm-dd>-<source-slug>-original<extension>
```

If a filename already exists, append a short unique suffix before the extension.

The source page's `originPath` should match the final retained raw file path.

If a raw file cannot be promoted, leave it in `_inbox/` and report the reason. Do not silently move failed items.

## Step 4: Report to the User

If one or more raw files were promoted, write one operational log entry for the processed batch:

```bash
python3 _system/scripts/log.py --message "process-inbox: promoted <count> raw files to sources; skipped=<count> failed=<count>"
```

Do not write a log entry when no files were promoted.

After processing all items, give a concise summary:

- How many raw files were promoted.
- The source path and ID for each promoted file.
- The retained raw path for each original.
- Any files skipped or failed and why.

## Important Rules

- `_inbox/` is an active raw drop zone, not canonical knowledge.
- `raw/` retains original raw captures after promotion and is not canonical knowledge.
- `sources/` contains the canonical verbatim source pages.
- Do not create separate intake tracking files.
- Do not extract knowledge primitives in this skill.
- Do not touch human prose except to preserve it verbatim in the new source page body.
