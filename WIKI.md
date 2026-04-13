# WIKI.md

Human-readable schema and editorial guide for the Agentics vault.  
Spec version: v1  
Last updated: 2026-04-12

---

## 1. What this wiki is

This vault is a structured knowledge base designed to be useful for both humans and AI agents.

It separates:
- **things** from **ideas**
- **claims** from **evidence**
- **sources** from **summaries**
- **facts** from **interpretations**
- **human-edited content** from **generated content**
- **page structure** from **compiled machine caches**

---

## 2. Folder meanings

| Folder | What goes here |
|---|---|
| `sources/` | Raw material and source-backed pages: webpages, PDFs, articles, transcripts, meeting notes, datasets |
| `entities/` | Durable things: people, orgs, projects, products, systems, places, events, artifacts |
| `concepts/` | Abstract ideas: definitions, principles, methods, frameworks, policies, standards |
| `syntheses/` | Maintained cross-source interpretations: overviews, analyses, comparisons, briefs, timelines |
| `procedures/` | Action-oriented instructions: runbooks, checklists, workflows, playbooks |
| `questions/` | Unresolved uncertainties and research gaps |
| `decisions/` | Recorded judgments, resolutions, and schema choices |
| `reports/` | Generated maintenance views and dashboards |
| `_attachments/` | Attachments referenced by source or other pages |
| `_views/` | Reusable view templates or layout helpers |
| `_wiki/` | Machine-generated runtime and compile artifacts (do not hand-edit) |
| `_inbox/` | Raw intake queue for unprocessed items |
| `_archive/` | Archived content no longer actively maintained |
| `_procedures/` | Internal system-level procedure pages |

---

## 3. Page types

Every authored page has a `pageType` in its frontmatter.

| `pageType`  | Folder        | Purpose                               |
| ----------- | ------------- | ------------------------------------- |
| `source`    | `sources/`    | Information origin                    |
| `entity`    | `entities/`   | Durable thing                         |
| `concept`   | `concepts/`   | Abstract idea or definition           |
| `synthesis` | `syntheses/`  | Cross-source rollup or interpretation |
| `procedure` | `procedures/` | Workflow or instructions              |
| `question`  | `questions/`  | Open question or research gap         |
| `decision`  | `decisions/`  | Recorded judgment or choice           |
| `report`    | `reports/`    | Generated view or dashboard           |

---

## 4. Required frontmatter

Every authored page (except purely generated reports) should include:

```yaml
id: <type>.<namespace>.<slug>
pageType: <type>
title: <title>
status: <status>
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Recommended additional fields:

```yaml
canonicalName: <Canonical Name>
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
| `active` | Currently maintained and relevant |
| `draft` | Work in progress, not finalized |
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

### Decision status

| Status | Meaning |
|---|---|
| `proposed` | Under consideration |
| `accepted` | Adopted and in effect |
| `superseded` | Replaced by a newer decision |
| `rejected` | Considered and declined |

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
| `owned_by` | Ownership |
| `located_in` | Location |
| `related_to` | General association |
| `supports` | Supports another object |
| `contradicts` | Conflicts with another object |
| `mentions` | References without strong relation |
| `applies_to` | Scope or applicability |
| `derived_from` | Derived or based on |

---

## 9. Managed blocks

Generated content lives inside managed blocks so agents can safely regenerate it without clobbering human notes.

```md
<!-- AI:GENERATED START name=summary -->
Generated content here.
<!-- AI:GENERATED END name=summary -->
```

**Human-authored content outside managed blocks is always preserved.**

Common block names: `summary`, `claims`, `evidence`, `relations`, `timeline`, `source-metadata`, `report-body`.

---

## 10. Compile outputs

The compile pipeline reads the vault and emits machine-readable caches to `_wiki/cache/`.

Run with:

```bash
python _wiki/compile.py
```

Required outputs:
- `pages.json` — normalized page index
- `claims.jsonl` — all extracted claims
- `relations.jsonl` — all extracted relations
- `agent-digest.json` — high-signal agent context

Recommended outputs:
- `contradictions.json`, `questions.json`, `decisions.json`
- `timeline-events.json`, `source-index.json`

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

Each item in `_inbox/` is tracked by a **pointer file** — a minimal YAML record that references the raw item and tracks its processing state.

See [INBOX.md](./INBOX.md) for the full pointer schema.

### Intake lifecycle

1. Raw item arrives in `_inbox/`
2. A pointer file is created with `status: unprocessed`
3. The item is reviewed and triaged
4. If retained: item becomes a canonical `source` page under `sources/`; pointer moves to `_inbox/trash/` with `status: processed`
5. If discarded: pointer moves to `_inbox/trash/` with `status: ignored` or `trashed`

### `_inbox/` is not canonical

- Inbox pointer files are NOT `source` pages.
- Agents MUST NOT treat `_inbox/` items as authoritative source records.
- Agents SHOULD process inbox items by converting them into proper `source` pages.

---

## 14. Editorial principles

- Claims should be atomic — one proposition per claim.
- Important assertions should be in frontmatter, not buried in prose, if they matter for agents.
- Questions should remain open until explicitly resolved.
- Decisions should be recorded when schema or interpretation choices are made.
- Human notes outside managed blocks will always be preserved.
- Reports are views, not truth sources.
- Inbox items MUST be processed into canonical source pages before being treated as evidence.
