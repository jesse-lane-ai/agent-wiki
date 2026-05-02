# AGENTS.md

Agent behavior contract for the Agentics vault.  
Version: v1  
Last updated: 2026-05-02

---

## 1. What this file is

This file is the authoritative description of how agents are expected to behave when reading, writing, or compiling this vault. It is not a style guide — it is a contract.

Agents MUST read this file before making any edits to the vault. See also [[WIKI#4.1 Common runtime schemas]] for schema, [[WIKI#16 Editorial principles]] for editorial rules, and [[INBOX]] for the raw intake workflow.

For routine field-level schema details, use [[WIKI#4.1 Common runtime schemas]]. Use [[AGENT-WIKI-SPEC-v1]] when changing project behavior, resolving ambiguity, or when [[WIKI#4.1 Common runtime schemas]] is insufficient. This file only defines agent behavior.

---

## 2. Core rules

### 2.1 Preserve human content

Agents MUST NOT rewrite or delete human-authored prose, notes, or commentary unless explicitly instructed to do so by the human operator.

Human-authored prose, notes, and commentary are protected.

### 2.2 Keep generated content explicit

Agents SHOULD keep generated structured knowledge in frontmatter fields, claim/evidence/relation records, generated cache files, or fully generated report files.

When updating page body prose, agents MUST preserve human-authored content unless the human operator explicitly asks for a rewrite.

### 2.3 Use stable IDs

Every page, claim, evidence entry, and relation MUST have a stable ID.

When creating new objects, agents MUST follow the naming conventions in section 4.

IDs MUST NOT be regenerated on recompile. Once assigned, an ID is permanent.

### 2.4 Update timestamps

When an agent meaningfully changes structured content (frontmatter, claims, relations), it MUST update `updatedAt` on the affected page.

### 2.5 Do not invent certainty

Agents MUST NOT assign confidence values that are not supported by evidence.

When evidence is weak or absent, claims MUST use:
- `status: unverified` or `status: weakly_supported`
- `confidence` below `0.60`

Agents MUST NOT silently upgrade `weakly_supported` or `unverified` claims to `supported`.

### 2.6 Do not treat reports as truth

Files in `reports/` are generated views. They are NOT authoritative.

Agents MUST NOT read reports as primary data sources when page frontmatter or cache files are available.

Root `overview.md`, if present, is human-facing orientation prose. It is NOT primary evidence for claims unless the relevant material has also been promoted into canonical source, claim, evidence, or page metadata records.

### 2.7 Do not hand-edit cache files

Files in `_system/cache/`, `_system/indexes/`, `_system/logs/`, and root `index.md` are generated artifacts.

Agents MUST NOT manually patch cache files, generated index files, generated log files, or root `index.md`. Agents MUST write operational log entries through `_system/scripts/log.py`.

### 2.8 Respect the inbox boundary

`_inbox/` is a raw item intake queue — NOT a source of canonical knowledge.

Agents MUST NOT read `_inbox/` or `raw/` files as primary data sources or treat them as evidence for claims.

Agents SHOULD process inbox items by converting retained raw files into canonical `source` pages under `sources/`. See [[INBOX]] for the raw intake lifecycle rules.

Large retained sources SHOULD be converted into a short parent source page under `sources/` and child source part pages under `sources/parts/`. Agents SHOULD extract knowledge primitives from source part pages, not from the parent source manifest.

When local setup or converter availability is uncertain, agents SHOULD run the read-only onboarding probe:

```bash
python3 _system/scripts/onboard.py --check
```

Agents MUST NOT create `.venv/`, install packages, write `_system/config.json`, or enable network/OCR/LLM/cloud conversion behavior unless explicitly instructed by the human operator.

---

## 3. What agents may do

- Add new pages in the correct folder for the page type
- Add frontmatter to existing pages
- Add or update claims and evidence in frontmatter
- Add or update relations in frontmatter
- Update page body prose when explicitly instructed
- Create question pages for unresolved unknowns
- Run the compile pipeline to regenerate the root page catalog, caches, and reports
- Create or refresh root `overview.md` when explicitly asked for a human-facing vault overview
- Add aliases and tags to existing pages

---

## 4. Naming conventions

### Page IDs

IDs use dotted lowercase namespace format.

Pattern: `<pageType>.<namespace>.<slug>`

Examples:
- `entity.place.riverside-community-garden`
- `concept.watershed-management`
- `source.2026-04-12.webpage.urban-tree-canopy`
- `source.2026-04-12.document.community-plan.part001`
- `synthesis.overview.coastal-resilience`
- `question.evacuation-routing.accessibility`

### Claim IDs

Pattern: `claim.<page-namespace>.<descriptor>`

Example: `claim.garden.weekly-produce-donations`

### Evidence IDs

Pattern: `ev.<claim-slug>.<index>`

Example: `ev.weekly-produce-donations.01`

### Timeline entry IDs

Pattern: `tl.<page-slug>.<index>`

Example: `tl.riverside-garden.001`

### Filenames

Filenames SHOULD use kebab-case and match the page slug.

Example: `entities/riverside-community-garden.md`

---

## 5. Folder ownership rules

| Folder | Required `pageType` |
|---|---|
| `sources/` | `source` |
| `sources/parts/` | `source` |
| `entities/` | `entity` |
| `concepts/` | `concept` |
| `claims/` | `claim` |
| `syntheses/` | `synthesis` |
| `questions/` | `question` |
| `reports/` | `report` (if frontmatter present) |
| `index.md` | `index` |
| `overview.md` | `overview` |

Agents MUST place pages in the folder that matches their `pageType`.  
Agents MUST NOT place entity pages in `concepts/`, etc.

---

## 6. Compile expectations

The compile pipeline reads the vault and emits:

- `index.md` — deterministic root page catalog
- `_system/cache/pages.json` — normalized page index
- `_system/cache/claims.jsonl` — all extracted claims
- `_system/cache/relations.jsonl` — all extracted relations
- `_system/cache/agent-digest.json` — high-signal prompt supplement
- `_system/cache/contradictions.json` — contradiction registry
- `_system/cache/questions.json` — open question registry
- `_system/cache/timeline-events.json` — chronological event index
- `_system/cache/source-index.json` — source metadata registry

To run the compile pipeline:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

The compile pipeline MUST be run after meaningful vault changes to keep `index.md` and caches fresh. The compile pipeline writes one operational log entry to `_system/logs/log.md`.

---

## 7. Logs

There is one canonical operational log:

- `_system/logs/log.md` contains generated compile/runtime and skill-run entries. Agents MUST NOT hand-edit this file.

Agents MUST use `_system/scripts/log.py` to write one operational log entry after each meaningful skill run or change batch, such as schema updates, new workflows, import configuration changes, or significant content migrations.

Agents SHOULD NOT log trivial report/cache regeneration unless it records a meaningful vault change or operational incident.

Entries are prepended so the most recent entry appears first. Each entry SHOULD include:

- date
- actor or tool, when known
- changed area
- short reason or outcome

Operational log entries SHOULD be written with:

```bash
python3 _system/scripts/log.py --message "<message>"
```

Logs are not authoritative truth records. Agents MUST NOT treat `_system/logs/log.md` as primary evidence for claims unless the relevant material has been promoted into a canonical `source` page.

---

## 8. Claim rules summary

- Claims MUST be atomic (one proposition per claim)
- Claims MUST have a stable unique ID
- Claims MUST have `status`, `confidence`, `claimType`, `createdAt`, `updatedAt`
- Claims SHOULD have at least one evidence entry
- Claim status MUST use the allowed enum: `supported`, `weakly_supported`, `inferred`, `unverified`, `contested`, `contradicted`, `deprecated`
- Confidence MUST be a float between `0.0` and `1.0`

---

## 9. Evidence rules summary

- Evidence MUST reference a `sourceId` when possible
- Evidence `relation` MUST use: `supports`, `weakens`, `contradicts`, `context_only`
- Evidence `context_only` MUST NOT be counted as direct support during compile scoring
- Evidence MUST NOT overstate support strength

---

## 10. Question hygiene

- Agents SHOULD create question pages for important unresolved unknowns
- Resolved questions MUST remain in the vault with updated status
- Agents MUST NOT delete resolved pages

---

## 11. What agents MUST NOT do

- Rewrite human-authored content without explicit instruction
- Delete unresolved uncertainty by omission
- Convert weak evidence to strong support semantics
- Treat reports as primary truth records
- Hand-edit cache files, generated index files, generated log files, or root `index.md`
- Create duplicate IDs
- Place pages in the wrong folder for their `pageType`
- Invent unsupported certainty in claims
- Treat root `overview.md` as primary evidence
- Use standard markdown links for internal vault references (use wikilinks instead)

---

## 12. Internal linking convention

All internal links within the vault MUST use Obsidian-style wikilinks.

| Use case | Format |
|---|---|
| Link to a page | `[[page-slug]]` |
| Link with display text | `[[page-slug\|Display Text]]` |
| Link to a section | `[[page-slug#section-heading]]` |

Standard markdown links (`[text](path)`) MUST NOT be used for internal vault references. They MAY be used for external URLs only.

This convention applies to:
- page body content
- `relatedPages` values in frontmatter (use wikilink strings)
- skill instruction files
- all root-level docs listed in WIKI.md Section 2, including AGENTS.md, the runtime guide itself, INBOX.md, CLAUDE.md, etc.

---

## 13. Full Specification

[[AGENT-WIKI-SPEC-v1]]
