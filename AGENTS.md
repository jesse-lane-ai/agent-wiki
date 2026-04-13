# AGENTS.md

Agent behavior contract for the Agentics vault.  
Version: v1  
Last updated: 2026-04-12

---

## 1. What this file is

This file is the authoritative description of how agents are expected to behave when reading, writing, or compiling this vault. It is not a style guide — it is a contract.

Agents MUST read this file before making any edits to the vault. See also [WIKI.md](./WIKI.md) for schema and editorial rules, and [INBOX.md](./INBOX.md) for the intake pointer schema.

---

## 2. Core rules

### 2.1 Preserve human content

Agents MUST NOT rewrite or delete content that lives outside of managed blocks unless explicitly instructed to do so by the human operator.

Human-authored prose, notes, and commentary are protected.

### 2.2 Stay inside managed blocks

All generated content MUST live inside managed block boundaries.

Managed block format:

```md
<!-- AI:GENERATED START name=<block-name> -->
Generated content here.
<!-- AI:GENERATED END name=<block-name> -->
```

Agents MUST only rewrite the content between matching `START` and `END` delimiters.  
Agents MUST NOT nest managed blocks.  
Agents MUST use stable `name=` values.

### 2.3 Use stable IDs

Every page, claim, evidence entry, and relation MUST have a stable ID.

When creating new objects, agents MUST follow the naming conventions in section 4.

IDs MUST NOT be regenerated on recompile. Once assigned, an ID is permanent unless explicitly superseded by a decision page.

### 2.4 Update timestamps

When an agent meaningfully changes structured content (frontmatter, claims, relations), it MUST update `updatedAt` on the affected page.

Minor regeneration of managed blocks (summary rewrites) SHOULD also update `updatedAt`.

### 2.5 Do not invent certainty

Agents MUST NOT assign confidence values that are not supported by evidence.

When evidence is weak or absent, claims MUST use:
- `status: unverified` or `status: weakly_supported`
- `confidence` below `0.60`

Agents MUST NOT silently upgrade `weakly_supported` or `unverified` claims to `supported`.

### 2.6 Do not treat reports as truth

Files in `reports/` are generated views. They are NOT authoritative.

Agents MUST NOT read reports as primary data sources when page frontmatter or cache files are available.

### 2.7 Do not hand-edit cache files

Files in `_wiki/cache/` and `_wiki/indexes/` are compile artifacts.

Agents MUST NOT manually patch cache files except by running the compile pipeline.

### 2.8 Respect the inbox boundary

`_inbox/` is a raw item intake queue — NOT a source of canonical knowledge.

Agents MUST NOT read `_inbox/` pointer files as primary data sources or treat them as evidence for claims.

Agents SHOULD process inbox items by converting retained items into canonical `source` pages under `sources/`. See [INBOX.md](./INBOX.md) for the pointer schema and lifecycle rules.

---

## 3. What agents may do

- Add new pages in the correct folder for the page type
- Add frontmatter to existing pages
- Add or update claims and evidence in frontmatter
- Add or update relations in frontmatter
- Rewrite content inside managed blocks
- Create decision pages when making schema or interpretation choices
- Create question pages for unresolved unknowns
- Run the compile pipeline to regenerate caches and reports
- Add aliases and tags to existing pages

---

## 4. Naming conventions

### Page IDs

IDs use dotted lowercase namespace format.

Pattern: `<pageType>.<namespace>.<slug>`

Examples:
- `entity.project.my-project`
- `concept.structured-claims`
- `source.my-project.docs`
- `synthesis.market-overview.automation`
- `question.claim-ownership.multi-page`
- `decision.claim-status-enum-v1`

### Claim IDs

Pattern: `claim.<page-namespace>.<descriptor>`

Example: `claim.my-project.compile-outputs`

### Evidence IDs

Pattern: `ev.<claim-slug>.<index>`

Example: `ev.compile-outputs.01`

### Timeline entry IDs

Pattern: `tl.<page-slug>.<index>`

Example: `tl.my-project.001`

### Filenames

Filenames SHOULD use kebab-case and match the page slug.

Example: `entities/my-project.md`

---

## 5. Folder ownership rules

| Folder | Required `pageType` |
|---|---|
| `sources/` | `source` |
| `entities/` | `entity` |
| `concepts/` | `concept` |
| `claims/` | `claim` |
| `syntheses/` | `synthesis` |
| `procedures/` | `procedure` |
| `questions/` | `question` |
| `decisions/` | `decision` |
| `reports/` | `report` (if frontmatter present) |

Agents MUST place pages in the folder that matches their `pageType`.  
Agents MUST NOT place entity pages in `concepts/`, etc.

---

## 6. Compile expectations

The compile pipeline reads the vault and emits:

- `_wiki/cache/pages.json` — normalized page index
- `_wiki/cache/claims.jsonl` — all extracted claims
- `_wiki/cache/relations.jsonl` — all extracted relations
- `_wiki/cache/agent-digest.json` — high-signal prompt supplement
- `_wiki/cache/contradictions.json` — contradiction registry
- `_wiki/cache/questions.json` — open question registry
- `_wiki/cache/decisions.json` — decision registry
- `_wiki/cache/timeline-events.json` — chronological event index
- `_wiki/cache/source-index.json` — source metadata registry

To run the compile pipeline:

```bash
python _wiki/compile.py
```

The compile pipeline MUST be run after meaningful vault changes to keep caches fresh.

---

## 7. Managed block names

Standard block names agents should use:

| Name | Purpose |
|---|---|
| `summary` | Generated summary of the page |
| `claims` | Generated claims block (if not in frontmatter) |
| `evidence` | Generated evidence block |
| `relations` | Generated relations block |
| `timeline` | Generated timeline block |
| `source-metadata` | Generated source metadata |
| `report-body` | Generated report content |

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

## 10. Decision and question hygiene

- Agents SHOULD create decision pages for any schema or interpretation changes they make
- Agents SHOULD create question pages for important unresolved unknowns
- Resolved questions and superseded decisions MUST remain in the vault with updated status
- Agents MUST NOT delete resolved or superseded pages

---

## 11. What agents MUST NOT do

- Rewrite human content outside managed blocks
- Delete unresolved uncertainty by omission
- Convert weak evidence to strong support semantics
- Treat reports as primary truth records
- Hand-edit cache files
- Create duplicate IDs
- Place pages in the wrong folder for their `pageType`
- Invent unsupported certainty in claims

## 12. Full Specification

[[agentic-wiki-v1-spec]]