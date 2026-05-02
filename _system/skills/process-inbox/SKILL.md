---
name: process-inbox
description: "Process raw files dropped into the Agentics vault inbox. Use this skill whenever the user says \"process inbox\", \"check the inbox\", \"handle new notes\", \"process raw notes\", \"ingest inbox files\", or wants to convert raw files in _inbox/ into canonical source pages."
---

# Process Inbox

This skill promotes raw files from `_inbox/` into canonical, schema-compliant `source` pages. It does not extract entities, concepts, claims, questions, or relations; use `_system/skills/extract-knowledge-primitives/SKILL.md` after source pages exist.

## Step 1: Read the Vault Contract

Before touching anything, read the vault's agent contract in this order:

1. `AGENTS.md` - the behavioral contract.
2. `WIKI.md` Sections 4.1, 5, 12, and 13 - the runtime source schema, status/source type enums, ID formats, examples, and large-source rules.
3. `INBOX.md` - the raw inbox lifecycle.

Key rules for this workflow:
- Preserve raw content.
- Use stable source IDs.
- Do not invent metadata.
- Use `WIKI.md` Section 4.1 for source page schema, examples, and conversion provenance fields.
- Use `WIKI.md` Sections 5 and 12 for status values and source types.
- Use `WIKI.md` Section 13 for large-source parent and part handling.
- Use `AGENT-WIKI-SPEC-v1.md` only when changing project behavior, resolving ambiguity, or when `WIKI.md` Sections 4.1, 5, 12, or 13 are insufficient.

If local Python or converter availability is unknown, run the read-only onboarding probe before processing binary or non-markdown files:

```bash
python3 _system/scripts/onboard.py --check
```

For first-run setup decisions, prefer:

```bash
python3 _system/scripts/onboard.py --check --questions
```

Use the generated multiple-choice prompts so the user can answer with compact letter choices.

Use the probe output and `_system/config.json`, when present, to determine which local conversion backends are configured and available. Do not create a virtual environment, install packages, write `_system/config.json`, or create missing folders unless the user explicitly asks for that setup work.

## Step 2: Check the Inbox

Scan `_inbox/` for raw files. Ignore directories and hidden/system files. Do not treat `_inbox/trash/` or `raw/` as active queue locations.

If `_inbox/` is empty or contains no processable raw files, report that and stop.

## Step 3: Promote Each Raw File

For each raw file, work through files one at a time.

### 3a. Read the raw file

Read the file fully. Preserve the original content exactly when writing the source body.

If the raw file is a binary or non-markdown document, use configured local conversion tools only when they are available. Read conversion policy from `_system/config.json` if it exists. Missing config means use conservative local-only defaults.

Do not install dependencies during this skill run. Do not call network, cloud OCR, LLM, transcription, or hosted document-intelligence services unless the operator explicitly configured or requested that behavior.

If no configured conversion path exists, leave the file in `_inbox/` and report that text extraction is required.

When conversion is used, record conversion provenance in the source frontmatter when available:

- `convertedAt`
- `conversionTool`
- `conversionToolVersion`
- `conversionBackend`
- `conversionWarnings`

### 3b. Infer source metadata

Create a source page using the source page schema and examples in `WIKI.md` Section 4.1.

Newly promoted ordinary source pages MUST use `status: unprocessed` and `sourceRole: whole`. The extraction workflow changes source pages to `status: processed` after knowledge primitives have been extracted.

Large source parent pages MUST use `sourceRole: parent`. They SHOULD use `status: partitioned` while one or more child source parts remain unprocessed. Child source part pages MUST use `sourceRole: part` and `status: unprocessed`.

Use this ID pattern:

```text
source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
```

- `yyyy-mm-dd`: processing date unless the raw file clearly includes a retrieval date.
- `sourceType`: the inferred source type from `WIKI.md` Section 12.
- `sourceSlug`: short kebab-case descriptor, preferably four words.

Infer `sourceType` conservatively:
- YouTube transcript -> `transcript`
- Article or blog post -> `article`
- PDF -> `pdf`
- Long generic document -> `document`
- Email -> `email`
- Meeting notes -> `meeting-notes`
- Raw data -> `dataset`
- Screenshot -> `screenshot`
- Unknown or plain notes -> `other`

If a field such as `publishedAt`, `author`, or `originUrl` cannot be inferred, omit optional fields rather than guessing. For local raw files with no external URL, use `originPath` to record the retained raw file path after promotion. Required source fields must still follow `WIKI.md` Section 4.1.

### 3c. Decide whether to partition

If the captured or converted text is larger than roughly 25,000 words, or if an agent cannot reliably process it in one extraction pass, create a large source instead of one giant markdown body.

Use deterministic split rules from `WIKI.md` Section 13:

- prefer semantic boundaries such as chapters, headings, appendices, transcript topics, or slide boundaries
- fall back to page ranges, timestamps, or other stable locators
- target 8,000-15,000 words per source part
- do not exceed 20,000 words per part unless preserving an indivisible structure requires it
- avoid splitting inside tables, code blocks, quoted blocks, or list structures when possible

For ordinary sources, write one canonical source page.

For large sources, write:

- one parent source page under `sources/`
- child source part pages under `sources/parts/`

### 3d. Write the source page or source parts

For an ordinary source, write the canonical source page to:

```text
sources/<yyyy-mm-dd>-<source-slug>.md
```

The body must contain the full verbatim raw content below the frontmatter. Preserve user context, annotations, and formatting. Set `sourceRole: whole`.

For a large source, write the parent source page to:

```text
sources/<yyyy-mm-dd>-<sourceType>-<sourceSlug>.md
```

The parent body should stay short and should not contain the full long-form source text. Include metadata, import notes, attachment references, retained raw path, and an ordered `sourceParts` manifest.

Write child source parts to:

```text
sources/parts/<yyyy-mm-dd>-<sourceType>-<sourceSlug>-part<nnn>.md
```

Each part must contain the verbatim text for that segment, `sourceRole: part`, `parentSourceId`, `partIndex`, `partCount`, and a stable `locator`.

### 3e. Move the raw file

After the source page is created successfully, move the original raw file to `raw/`.

Use a collision-resistant retained filename:

```text
raw/<yyyy-mm-dd>-<source-slug>-original<extension>
```

If a filename already exists, append a short unique suffix before the extension.

The source page's `originPath` should match the final retained raw file path. For large sources, the parent and all child source parts should use the retained raw path as `originPath`.

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
- For large sources, the parent source path and each child part path.
- The retained raw path for each original.
- Any files skipped or failed and why.

## Important Rules

- `_inbox/` is an active raw drop zone, not canonical knowledge.
- `raw/` retains original raw captures after promotion and is not canonical knowledge.
- `sources/` contains the canonical verbatim source pages.
- Large source parent pages are metadata and manifests; extraction should operate on source parts.
- Do not create separate intake tracking files.
- Do not extract knowledge primitives in this skill.
- Do not touch human prose except to preserve it verbatim in the new source page body.
