---
name: import-link
description: Import a URL, link-derived capture, transcript, or pasted source directly into a canonical source page. Use when the user asks to import a link, capture an external source, ingest a URL, or save source material into the vault.
---

# Import Link

## Configuration
- Before first use, read `ONBOARD.md` and `_system/skills/import-link/config.json`.
- If local setup is uncertain, run `python3 _system/scripts/onboard.py --check` and use the read-only probe output to guide setup questions.
- For first-run setup, prefer `python3 _system/scripts/onboard.py --check --questions` so the user can answer with compact letter choices.
- If the user approves persisting local Python, conversion, or vault placement policy, use `python3 _system/scripts/onboard.py --write-config` with the approved flags. The writer creates local `_system/config.json` from `_system/config.example.json`.
- Confirm `configured` is `true` before importing.
- Do not assume a default model, browser profile, Obsidian path, or external vault.
- If vault placement is undecided, importing into this repository root is allowed only when the user confirms that this checkout is the target markdown workspace.
- If `vaultRoot`, retrieval modes, or attachment policy is unknown, stop and ask the user to configure `_system/skills/import-link/config.json`.
- Use the repository root as `vaultRoot` only when the user wants imports written into this checkout.
- The default `manual_paste` retrieval mode requires no external tools. Other retrieval modes only apply when configured and available.
- Do not create a virtual environment, install packages, write `_system/config.json`, or change `_system/skills/import-link/config.json` unless the user explicitly asks for setup changes. Do not hand-edit `_system/config.json`; use `onboard.py --write-config` after approval.

## Vault Selection (required)
- Accept an optional vault name or vault root in user input.
- Use `_system/config.json` vault placement fields, when present, to understand whether this checkout is standalone, an Obsidian vault root, inside an Obsidian vault, external-vault controlled, or undecided.
- Resolve the target vault from `_system/skills/import-link/config.json` unless the user explicitly supplies a different path. If `_system/config.json` says `vault.mode: external-vault`, the import-link vault root must agree with the configured external target or the user must choose which path to use.
- If no configured vault root exists, stop and ask the user for the target vault root.
- If the requested vault folder does not exist, stop and report the missing vault instead of guessing.
- Use the resolved vault for all paths (`sources`, `_attachments`).

## UUID Generation
- Use `scripts/uuid.py` to generate a new UUID for each source attachment.

## Source Slug
- For any incoming URL or source, always generate a 4 word slug for the source note.
- Infer the four words by summarizing the content of the source note in 4 words.

## Source Schema (required, strictly enforced)

Create source files in `sources/` using the source page schema and examples in `WIKI.md` Section 4.1.

Use `WIKI.md` Section 4.1 as the routine source of truth for page-type schemas, ID formats, and examples. Use `WIKI.md` Sections 5 and 12 for status and source type enums. This skill owns the import workflow, not the source frontmatter schema.

Use `WIKI.md` Section 13 for large-source parent and part handling. Consult `AGENT-WIKI-SPEC-v1.md` only when changing project behavior, resolving ambiguity, or when `WIKI.md` Sections 4.1, 5, 12, or 13 are insufficient.

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
3. Ensure vault folders exist:
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
6. Write ordinary raw source to:
   - `sources/<yyyy-mm-dd>-<sourceType>-<sourceSlug>.md` using the source page schema and examples in `WIKI.md` Section 4.1.
   - Set `status: unprocessed`.
   - Set `sourceRole: whole`.
   - Include the full captured verbatim body with inline images + source URLs below the frontmatter.
   - images save to `_attachments`. filename: `yyyy-mm-dd-<sourceSlug>-<UUID>-<index>.<ext>` <index> starts at 1 and increments for each attachment.
   - if a video, capture thumbnail and place it at the top of the transcript.
   - inline images uses Obsidian image syntax `![[filename]]`
7. Write large sources as:
   - parent: `sources/<yyyy-mm-dd>-<sourceType>-<sourceSlug>.md`
   - parts: `sources/parts/<yyyy-mm-dd>-<sourceType>-<sourceSlug>-part<nnn>.md`
   - The parent body should stay short and should not contain the full long-form source text.
   - The parent frontmatter should include ordered `sourceParts`.
   - Each part should include verbatim text for its segment, `sourceRole: part`, `parentSourceId`, `partIndex`, `partCount`, and `locator`.
8. Write one operational log entry for the import:
   ```bash
   python3 _system/scripts/log.py --message "import-link: imported source <sourceId> to sources/<filename>; attachments=<count>"
   ```
   Log only after the source page and any attachments have been written successfully.
9. Confirm in chat with:
   - source path
   - source part paths when a large source was partitioned
   - number of attachments saved
