---
name: import-link
description: Import a URL, link-derived capture, transcript, or pasted source directly into a canonical source page. Use when the user asks to import a link, capture an external source, ingest a URL, or save source material into the vault.
---

# Import Link

## Configuration
- Before first use, read `INITIALIZE.md` and `_system/skills/import-link/config.json`.
- Confirm `configured` is `true` before importing.
- Do not assume a default model, browser profile, Obsidian path, or external vault.
- If `vaultRoot`, retrieval modes, or attachment policy is unknown, stop and ask the user to configure `_system/skills/import-link/config.json`.
- Use the repository root as `vaultRoot` only when the user wants imports written into this checkout.
- The default `manual_paste` retrieval mode requires no external tools. Other retrieval modes only apply when configured and available.

## Vault Selection (required)
- Accept an optional vault name or vault root in user input.
- Resolve the target vault from `_system/skills/import-link/config.json` unless the user explicitly supplies a different path.
- If no configured vault root exists, stop and ask the user for the target vault root.
- If the requested vault folder does not exist, stop and report the missing vault instead of guessing.
- Use the resolved vault for all paths (`sources`, `_attachments`).

## UUID Generation
- Use `scripts/uuid.py` to generate a new UUID for each source attachment.

## Source Slug
- For any incoming URL or source, always generate a 4 word slug for the source note.
- Infer the four words by summarizing the content of the source note in 4 words.

## Source Schema (required, strictly enforced)

Create source files in `sources/` using the canonical source page schema and example in `AGENT-WIKI-SPEC-v1.md` Section 10.1, "Source pages".

Use Section 10 of `AGENT-WIKI-SPEC-v1.md` as the source of truth for page-type schemas, allowed enum values, ID formats, and examples. This skill owns the import workflow, not the source frontmatter schema.

Newly imported source pages MUST use `status: unprocessed`. The extraction workflow changes source pages to `status: processed` after knowledge primitives have been extracted.

## Deterministic Workflow
1. **Deduplication Check:** Before capturing content, check existing source pages in `sources/` for a matching `originUrl`.
   - If a source with the matching URL already exists, stop and inform the user that it has already been imported or update the existing file if requested.
2. Capture source content using the retrieval modes configured in `_system/skills/import-link/config.json`.
   - If direct fetch is available, try it first.
   - If a transcript tool is configured and the source is a video, capture one English transcript when available and use it as the primary source body.
   - If browser automation is configured and direct retrieval is blocked or incomplete, use the configured browser automation.
   - If no configured retrieval mode works, ask the user to paste the source content or configure another retrieval method.
3. Ensure vault folders exist:
   - `sources/`
   - `_attachments/`
4. Build a deterministic ID:
   - Create the source slug in 4 words by summarizing the content of the source note. (This is done using the raw source note, after the content has been captured in Steps 2 & 3).
5. Write raw source to:
   - `sources/<yyyy-mm-dd>-<sourceType>-<sourceSlug>.md` using the source page schema and example in `AGENT-WIKI-SPEC-v1.md` Section 10.1, "Source pages".
   - Set `status: unprocessed`.
   - Include the full captured verbatim body with inline images + source URLs below the frontmatter.
   - images save to `_attachments`. filename: `yyyy-mm-dd-<sourceSlug>-<UUID>-<index>.<ext>` <index> starts at 1 and increments for each attachment.
   - if a video, capture thumbnail and place it at the top of the transcript.
   - inline images uses Obsidian image syntax `![[filename]]`
6. Confirm in chat with:
   - source path
   - number of attachments saved
