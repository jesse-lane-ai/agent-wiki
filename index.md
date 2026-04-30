---
id: meta.index
pageType: index
title: Agentics Wiki Index
status: active
createdAt: 2026-04-12
updatedAt: 2026-04-30
aliases: []
tags:
  - meta
  - index
---

# Agentics Wiki

Welcome to the Agentics vault — a structured knowledge base designed for both human reading and agent consumption.

---

## Navigation

| Section | Purpose |
|---|---|
| `sources/` | Raw material and source-backed pages |
| `entities/` | Durable things: people, orgs, projects, products |
| `concepts/` | Definitions, methods, frameworks, principles |
| `claims/` | Standalone atomic claim pages with evidence |
| `syntheses/` | Cross-source analyses and overviews |
| `procedures/` | Runbooks, checklists, workflows |
| `questions/` | Open questions and research gaps |
| `reports/` | Generated maintenance views |

---

## Intake

New material lands in `_inbox/` as pointer files before being processed into canonical `source` pages.

See [[INBOX]] for the pointer schema and intake lifecycle.

---

## Key files

| File | Purpose |
|---|---|
| [[WIKI]] | Schema, page types, folder meanings, and editorial rules |
| [[AGENTS]] | Agent behavior contract |
| [[INBOX]] | Inbox pointer schema and intake workflow |
| [[AGENT-WIKI-SPEC-v1]] | Full v1 specification |

---

## Compile pipeline

To regenerate the machine-facing cache files and reports:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

Cache outputs live in `_wiki/cache/`. Required outputs:

- `pages.json` — normalized page index
- `claims.jsonl` — all extracted claims
- `relations.jsonl` — all extracted relations
- `agent-digest.json` — high-signal agent context

---

<!-- AI:GENERATED START name=summary -->
This vault is initialized with the v1 schema. Folders, compile pipeline, and root docs are in place. Begin adding source, entity, and concept pages to populate the knowledge graph.
<!-- AI:GENERATED END name=summary -->
