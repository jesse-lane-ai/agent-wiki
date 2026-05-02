# WIKI.md

Human-readable schema and editorial guide for the Agentics vault.  
Spec version: v1  
Last updated: 2026-05-01

---

## 1. What this wiki is

This vault is a structured knowledge base designed to be useful for both humans and AI agents.

This file is a quick editorial guide. The canonical technical schema lives in [[AGENT-WIKI-SPEC-v1]].

It separates:
- **things** from **ideas**
- **claims** from **evidence**
- **sources** from **summaries**
- **facts** from **interpretations**
- **human-edited content** from **compiled/generated artifacts**
- **page structure** from **compiled machine caches**

---

## 2. Folder meanings

Current vault structure:

```text
<vault>/
  AGENTS.md
  AGENT-WIKI-SPEC-v1.md
  INBOX.md
  INITIALIZE.md
  README.md
  WIKI.md
  index.md
  overview.md

  sources/
  entities/
  concepts/
  claims/
  syntheses/
  questions/
  reports/

  _inbox/
  raw/
  _attachments/
  _archive/
  _system/
    cache/
    indexes/
    logs/
    scripts/
    skills/
```

Fresh template checkouts may omit empty content and runtime folders. Initialization, import, and compile workflows create missing folders as needed.

| Folder | What goes here |
|---|---|
| `sources/` | Raw material and source-backed pages: webpages, PDFs, articles, transcripts, meeting notes, datasets |
| `entities/` | Durable things: people, orgs, projects, products, systems, places, events, artifacts |
| `concepts/` | Abstract ideas and reusable instructions: definitions, methods, frameworks, workflows, runbooks, checklists |
| `claims/` | Standalone claim pages: individual atomic propositions with their own evidence and provenance |
| `syntheses/` | Maintained cross-source interpretations: overviews, analyses, comparisons, briefs, timelines |
| `questions/` | Unresolved uncertainties and research gaps |
| `reports/` | Generated maintenance views and dashboards |
| `_attachments/` | Attachments referenced by source or other pages (created on init, may be empty) |
| `_archive/` | Archived content no longer actively maintained (created on init, may be empty) |
| `_system/` | Machine-generated runtime and compile artifacts (do not hand-edit) |
| `_inbox/` | Raw intake queue for unprocessed items |
| `raw/` | Retained original raw files after inbox promotion |

---

## 3. Page types

Every authored page has a `pageType` in its frontmatter.

| `pageType`  | Folder        | Purpose                               |
| ----------- | ------------- | ------------------------------------- |
| `source`    | `sources/`    | Information origin                    |
| `entity`    | `entities/`   | Durable thing                         |
| `concept`   | `concepts/`   | Abstract idea, definition, or reusable instruction |
| `claim`     | `claims/`     | Standalone atomic proposition         |
| `synthesis` | `syntheses/`  | Cross-source rollup or interpretation |
| `question`  | `questions/`  | Open question or research gap         |
| `report`    | `reports/`    | Generated view or dashboard           |
| `index`     | `index.md`    | Deterministic root page catalog       |
| `overview`  | `overview.md` | Human-facing vault landing page       |

---

## 4. Required frontmatter

Every authored page (except purely generated reports and the generated root catalog) should include:

```yaml
id: <pageType>.<primitiveSubtype>.<slug>
pageType: <pageType>
title: <title>
status: <status>
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Recommended additional fields:

```yaml
canonicalName: <canonicalName>
owner:
summary:
sourcePages: []
relatedPages: []
confidence:
freshness:
```

---

## 5. Status vocabularies

### General page status

| Status | Meaning |
|---|---|
| `processed` | Page has been processed by an agent |
| `unprocessed` | Page has not been processed by an agent |
| `archived` | No longer maintained |
| `deprecated` | Superseded or no longer valid |

### Question status

| Status | Meaning |
|---|---|
| `open` | Unresolved, actively tracked |
| `researching` | Actively being investigated |
| `blocked` | Cannot proceed without external input |
| `resolved` | Answer found and recorded |
| `dropped` | No longer relevant or pursued |


---

## 6. Claim rules

Claims are first-class records that can be evaluated, tracked, and compiled.

A claim should express **one proposition**, not several glued together.

### Claim status

| Status | Meaning |
|---|---|
| `supported` | Has strong, direct evidence |
| `weakly_supported` | Has some evidence but not strong |
| `inferred` | Derived logically, not directly evidenced |
| `unverified` | Not yet checked against sources |
| `contested` | Active disagreement exists |
| `contradicted` | Evidence directly contradicts it |
| `deprecated` | No longer applicable |

### Confidence

`confidence` is a float from `0.0` to `1.0`.

| Range | Meaning |
|---|---|
| `0.0 – 0.49` | Low confidence — should appear in low-confidence reports |
| `0.50 – 0.74` | Moderate confidence |
| `0.75 – 0.89` | High confidence |
| `0.90 – 1.0` | Very high confidence |

### Claim types

| Type | Meaning |
|---|---|
| `descriptive` | What something is or does |
| `historical` | What happened at a point in time |
| `causal` | Why something happened |
| `interpretive` | What something means |
| `normative` | What should be done |
| `forecast` | What is expected to happen |

---

## 7. Evidence rules

Evidence attaches provenance and support semantics to a claim.

### Evidence kinds

| Kind | Meaning |
|---|---|
| `quote` | Direct quotation from a source |
| `summary` | Summarized content from a source |
| `measurement` | Quantitative data point |
| `observation` | Direct observation record |
| `screenshot` | Visual capture |
| `transcript` | Spoken record |
| `inference` | Derived from other evidence |

### Evidence relations

| Relation | Meaning |
|---|---|
| `supports` | Strengthens the claim |
| `weakens` | Reduces confidence in the claim |
| `contradicts` | Directly conflicts with the claim |
| `context_only` | Provides context but not direct support |

`context_only` evidence is NOT counted as support during compile scoring.

---

## 8. Relationship predicates

The v1 controlled predicate set:

| Predicate | Meaning |
|---|---|
| `is_a` | Type relationship |
| `part_of` | Composition |
| `depends_on` | Dependency |
| `uses` | Usage relationship |
| `produces` | Output relationship |
| `founded_by` | Founding relationship |
| `owned_by` | Ownership |
| `located_in` | Location |
| `related_to` | General association |
| `supports` | Supports another object |
| `contradicts` | Conflicts with another object |
| `mentions` | References without strong relation |
| `applies_to` | Scope or applicability |
| `derived_from` | Derived or based on |

---

## 9. Generated content

Generated structured knowledge should live in frontmatter fields, claim/evidence/relation records, cache files, indexes, reports, or the deterministic root `index.md` catalog.

Agents should preserve human-authored page prose unless explicitly asked to rewrite it. Page body prose is ordinary markdown.

`index.md` is generated as the root page catalog. Do not place durable manual prose there; use root documentation files such as [[overview]], [[README]], [[WIKI]], [[INBOX]], or [[AGENTS]] instead.

`overview.md` is durable AI-maintained orientation prose. It should summarize the vault for a human reader, but it is not primary evidence and should not replace canonical source, claim, evidence, or page metadata records.

---

## 10. Compile outputs

The compile pipeline reads the vault, emits machine-readable caches to `_system/cache/`, and regenerates the root `index.md` page catalog.

Run with:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

Required outputs:
- `pages.json` — normalized page index
- `claims.jsonl` — all extracted claims
- `relations.jsonl` — all extracted relations
- `agent-digest.json` — high-signal agent context

Recommended outputs:
- `contradictions.json`, `questions.json`
- `timeline-events.json`, `source-index.json`

Catalog output:
- `index.md` — deterministic root-level page catalog rendered from `_system/cache/pages.json`

---

## 11. Reports

Reports in `reports/` are generated views. They are NOT authoritative.

| Report | Purpose |
|---|---|
| `open-questions.md` | All open question pages |
| `contradictions.md` | Tracked claim conflicts |
| `low-confidence.md` | Claims with confidence below 0.50 |
| `claim-health.md` | Evidence gap and staleness overview |
| `stale-pages.md` | Pages not updated recently |

Do not treat reports as primary data — they derive from page frontmatter and caches.

---

## 12. Source types

| Type | Meaning |
|---|---|
| `webpage` | Web page |
| `article` | Published article |
| `pdf` | PDF document |
| `transcript` | Conversation or meeting transcript |
| `email` | Email thread |
| `meeting-notes` | Meeting notes |
| `dataset` | Structured data |
| `screenshot` | Visual capture |
| `bridge` | Bridge page pointing to an external source |
| `import` | Raw imported file |
| `other` | Other source type |

---

## 13. Inbox intake strategy

The `_inbox/` folder is the raw item intake queue. New unprocessed material should land here first.

Raw inbox items are promoted into canonical `source` pages by the `process-inbox` skill. See [[INBOX]] for the full intake lifecycle.

### Intake lifecycle

1. Raw item arrives in `_inbox/`
2. `process-inbox` reads the raw item
3. If retained: item becomes a canonical `source` page under `sources/` with `status: unprocessed`
4. The original raw file moves to `raw/`
5. If discarded: the raw file moves to `_inbox/trash/`

### `_inbox/` is not canonical

- Inbox raw files are NOT `source` pages.
- Files in `raw/` are retained originals, not canonical source records.
- Agents MUST NOT treat `_inbox/` or `raw/` items as authoritative source records.
- Agents SHOULD process inbox items by converting them into proper `source` pages.

---

## 14. Internal linking convention

All internal links within the vault use Obsidian-style wikilinks.

| Format | Use |
|---|---|
| `[[page-slug]]` | Link to a page |
| `[[page-slug\|Display Text]]` | Link with custom display text |
| `[[page-slug#section]]` | Link to a section |

Standard markdown links are only used for external URLs.
---

## 15. Editorial principles

- Claims should be atomic — one proposition per claim.
- Important assertions should be in frontmatter, not buried in prose, if they matter for agents.
- Questions should remain open until explicitly resolved.
- Human-authored notes should be preserved unless explicitly changed by the operator.
- Reports are views, not truth sources.
- Inbox items MUST be processed into canonical source pages before being treated as evidence.
