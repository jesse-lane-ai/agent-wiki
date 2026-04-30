---
name: import-note
description: Ingest raw notes, links, or snippets into the vault inbox queue using pointer files and full verbatim source records. Use when the user asks to capture or import a note, ingest content, or queue raw material into the vault _inbox.
---

# Import Note

## Configuration
- Before first use, read [[INITIALIZE]] and confirm the `import-note` configuration is complete.
- Do not assume a default model, browser profile, Obsidian path, or external vault.
- If `vaultRoot`, retrieval mode, or attachment policy is unknown, stop and ask the user to configure it.
- Use the repository root as `vaultRoot` only when the user wants imports written into this checkout.

## Vault Selection (required)
- Accept an optional vault name or vault root in user input.
- Resolve the target vault from [[INITIALIZE]] unless the user explicitly supplies a different path.
- If no configured vault root exists, stop and ask the user for the target vault root.
- If the requested vault folder does not exist, stop and report the missing vault instead of guessing.
- Use the resolved vault for all paths (`_inbox`, `sources`, `_attachments`).

## UUID Generation
- Use `scripts/uuid.py` to generate a new UUID for each inbox pointer.
- Also generate a new uuid for each source attachment.

## Source Slug
- For any incoming URL or source, always generate a 4 word slug for the source note.
- Infer the four words by summarizing the content of the source note in 4 words.

## Pointer Schema (required, strictly enforced)

Create pointer files in `_inbox/` using frontmatter and exactly these fields:
- `id`: unique inbox ID, format: `yyyy-mm-dd-inbox-<UUID>`
- `url`: original URL of the source
- `pointer`: pointer to raw item path. format: `sources/source.<yyyy-mm-dd>.<source-slug>`. Always use a native Obsidian wikilink.
- `status`: `UNPROCESSED`

Example:
```yaml
---
id: yyyy-mm-dd-inbox-<UUID>
url: <original URL of the source>
pointer: "[[sources/source.<yyyy-mm-dd>.<source-slug>]]"
status: UNPROCESSED
---
```

## Source Schema (required, strictly enforced)

Create source files in `sources/` using frontmatter and exactly these fields:
- `id`: unique source ID, format: `source.<yyyy-mm-dd>.<source-slug>`
- `pageType`: `source`
- `title`: `<title>`
- `status`: `unprocessed`
- `sourceType`: appropriate source type (allowed values: `webpage`, `article`, `pdf`, `transcript`, `email`, `meeting-notes`, `dataset`, `screenshot`, `bridge`, `import`, `other`)
- `originUrl`: original URL of the source
- `publishedAt`: publication date if known, otherwise leave blank
- `retrievedAt`: `YYYY-MM-DD`
- `updatedAt`: `YYYY-MM-DD`
- `createdAt`: `YYYY-MM-DD`
- `aliases`: `[]`
- `tags`: `[]`
- `attachments`: list of attachment wikilinks or empty `[]`

Example:
```yaml
---
id: source.<yyyy-mm-dd>.<source-slug>
pageType: source
title: <title>
status: unprocessed
sourceType: webpage
originUrl: <original URL of the source>
publishedAt:
retrievedAt: yyyy-mm-dd
updatedAt: yyyy-mm-dd
createdAt: yyyy-mm-dd
aliases: []
tags: []
attachments: []
---
```

## Deterministic Workflow
1. **Deduplication Check:** Before capturing content, check all pointer files in `_inbox/` and `_inbox/trash/` for an existing `url`.
   - If a pointer with the matching URL already exists, stop and inform the user that it has already been imported (provide the existing pointer/source paths) or update the existing files if requested.
2. Capture source content using the retrieval modes configured in [[INITIALIZE]].
   - If direct fetch is available, try it first.
   - If a transcript tool is configured and the source is a video, capture one English transcript when available and use it as the primary source body.
   - If browser fallback is configured and direct retrieval is blocked or incomplete, use the configured browser profile.
   - If no configured retrieval mode works, ask the user to paste the source content or configure another retrieval method.
3. Ensure vault folders exist:
   - `_inbox/`
   - `_inbox/trash/`
   - `sources/`
   - `_attachments/`
4. Build a deterministic ID:
   - Create the uuid using `scripts/uuid.py`
   - Create the source slug in 4 words by summarizing the content of the source note. (This is done using the raw source note, after the content has been captured in Steps 2 & 3).
5. Write raw source to:
   - `sources/source.<yyyy-mm-dd>.<source-slug>` using the frontmatter defined in **Source Schema**.
   - Include the full captured body with inline images + source URLs below the frontmatter.
   - images save to `_attachments`. filename: `yyyy-mm-dd-<source-slug>-<UUID>-<index>.<ext>` <index> starts at 1 and increments for each attachment.
   - if a video, capture thumbnail and place it at the top of the transcript.
   - inline images uses Obsidian image syntax `![[filename]]`
6. Write pointer file to:
   - `_inbox/yyyy-mm-dd-inbox-<UUID>.md`
7. Confirm in chat with:
   - pointer path
   - source path
   - number of attachments saved
