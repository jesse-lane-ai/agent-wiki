---
name: import-link
description: Import a URL, link-derived capture, transcript, or pasted source directly into a canonical source page. Use when the user asks to import a link, capture an external source, ingest a URL, or save source material into the vault.
---

# Import Link

## Configuration
- Before first use, read `ONBOARD.md` and `_system/skills/import-link/config.json`.
- If local setup is uncertain, run `python3 _system/scripts/onboard.py --check` and use the read-only probe output to guide setup questions.
- For first-run setup, prefer `python3 _system/scripts/onboard.py --check --questions` so the user can answer with compact letter choices.
- If the user approves persisting local Python or conversion policy, use `python3 _system/scripts/onboard.py --write-config` with the approved flags. The writer creates local `_system/config.json` from `_system/config.example.json`.
- Confirm `configured` is `true` before importing.
- Do not assume a default model, browser profile, or external retrieval tool.
- This checkout is the only wiki root. Write imports under this repository root using the relative directories in `_system/skills/import-link/config.json`.
- If retrieval modes or attachment policy are unknown, stop and ask the user to configure `_system/skills/import-link/config.json`.
- The default `manual_paste` retrieval mode requires no external tools. Other retrieval modes only apply when configured and available.
- Do not create a virtual environment, install packages, write `_system/config.json`, or change `_system/skills/import-link/config.json` unless the user explicitly asks for setup changes. Do not hand-edit `_system/config.json`; use `onboard.py --write-config` after approval.

## Wiki Root
- Run this skill from the repository root.
- Do not accept a vault name, alternate root, or external destination for this workflow.
- Use repository-relative paths for all writes.
- Source pages are written under `sources/`.
- Attachments are written under `_attachments/`.
- Users who want multiple independent wikis should clone this repository into multiple folders and onboard each checkout separately.

## UUID Generation
- Use `scripts/uuid.py` to generate a new UUID for each source attachment.

## Source Slug
- For any incoming URL or source, always generate a 4 word slug for the source note.
- Infer the four words by summarizing the content of the source note in 4 words.

## Source Schema (required, strictly enforced)

Create source files in `sources/` using `_system/scripts/create-page.py`. The scaffolder writes schema-compliant source pages, validates source parent/part requirements, and prevents duplicate IDs or target path overwrites.

Use `WIKI.md` Section 4.1 as the routine source of truth for page-type schemas, ID formats, and examples. Use `WIKI.md` Sections 5 and 12 for status and source type enums. This skill owns the import workflow, not the source frontmatter schema.

Use `WIKI.md` Section 13 for large-source parent and part handling. Consult `AGENT-WIKI-SPEC-v1.md` only when changing project behavior, resolving ambiguity, or when `WIKI.md` Sections 4.1, 5, 12, or 13 are insufficient.

Use `AGENT-WIKI-SPEC-v1.md` Section 6.6 only when you need the page scaffolding contract or `create-page.py` option semantics.

Newly imported ordinary source pages MUST use `status: unprocessed` and `sourceRole: whole`. The extraction workflow changes source pages to `status: processed` after knowledge primitives have been extracted.

Large source parent pages MUST use `sourceRole: parent`. They SHOULD use `status: partitioned` while one or more child source parts remain unprocessed. Child source part pages MUST use `sourceRole: part` and `status: unprocessed`.

## Deterministic Workflow
1. **Deduplication Check:** Before capturing content, check existing source pages in `sources/` for a matching `originUrl`.
   - If a source with the matching URL already exists, stop and inform the user that it has already been imported or update the existing file if requested.
2. Capture source content using the retrieval modes configured in `_system/skills/import-link/config.json`.
   - If direct fetch is available, try it first.
   - If a transcript tool is configured and the source is a video, capture one English transcript when available and use it as the primary source body.
   - If browser automation is configured and direct retrieval is blocked or incomplete, use the configured browser automation.
   - If no configured retrieval mode works, ask the user to paste the source content or configure another retrieval method.
3. Ensure wiki folders exist:
   - `sources/`
   - `sources/parts/` when the capture needs partitioning
   - `_attachments/`
4. Build a deterministic ID:
   - Create the source slug in 4 words by summarizing the content of the source note. (This is done using the raw source note, after the content has been captured in Steps 2 & 3).
5. Decide whether to partition:
   - If captured text is larger than roughly 25,000 words, or if an agent cannot reliably process the full source in one extraction pass, create a large source.
   - Prefer semantic boundaries such as chapters, headings, appendices, transcript topics, or slide boundaries.
   - Fall back to page ranges, timestamps, or other stable locators.
   - Target 8,000-15,000 words per source part.
   - Do not exceed 20,000 words per part unless preserving an indivisible structure requires it.
   - Avoid splitting inside tables, code blocks, quoted blocks, or list structures when possible.
6. Save the prepared source body or source-part bodies to temporary Markdown files outside the vault, then call `_system/scripts/create-page.py` with `--no-log` for each canonical source page. The skill writes one batch log entry after the import succeeds.
7. For an ordinary source, call the scaffolder with:
   ```bash
   python3 _system/scripts/create-page.py \
     --type source \
     --subtype <sourceType> \
     --slug <sourceSlug> \
     --title "<title>" \
     --source-date <yyyy-mm-dd> \
     --retrieved-at <yyyy-mm-dd> \
     --source-url "<originUrl>" \
     --source-role whole \
     --body-file <prepared-source-body.md> \
     --no-log
   ```
   Use `--origin-path` instead of `--source-url` only when the imported source is local. Add `--attachment <attachment>` once for each saved attachment. The body file must contain the full captured verbatim body with inline images and source URLs below the frontmatter. Images save to `_attachments/` using filename `yyyy-mm-dd-<sourceSlug>-<UUID>-<index>.<ext>`, where `<index>` starts at 1 and increments for each attachment. If a video thumbnail is captured, place it at the top of the transcript. Inline images use Obsidian image syntax `![[filename]]`.
8. For a large source, call the scaffolder once for each child source part, then once for the parent manifest:
   - part pages use `--source-role part`, `--parent-source-id <parentSourceId>`, `--part-index <n>`, `--part-count <count>`, and `--locator "<locator>"`
   - the parent page uses `--source-role parent`, `--source-part <partPath>` once for each ordered child part path, and `--part-count <count>`
   - the parent body should stay short and should not contain the full long-form source text
   - each part body file must contain the verbatim text for its segment
   - use `--no-log` on each scaffolder call and log the import once after all pages and attachments are written
9. Write one operational log entry for the import:
   ```bash
   python3 _system/scripts/log.py --message "import-link: imported source <sourceId> to sources/<filename>; attachments=<count>"
   ```
   Log only after the source page and any attachments have been written successfully.
10. Confirm in chat with:
   - source path
   - source part paths when a large source was partitioned
   - number of attachments saved
