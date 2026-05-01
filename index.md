---
id: meta.index
pageType: index
title: Agentics Wiki Index
status: active
createdAt: 2026-04-12
updatedAt: 2026-05-01
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
| `concepts/` | Definitions, methods, frameworks, workflows |
| `claims/` | Standalone atomic claim pages with evidence |
| `syntheses/` | Cross-source analyses and overviews |
| `questions/` | Open questions and research gaps |
| `reports/` | Generated maintenance views |
| `raw/` | Retained original raw files |

---

## Intake

Raw files can land in `_inbox/` before being promoted into canonical `source` pages. External links can be imported directly into `sources/`.

See [[INBOX]] for the raw intake lifecycle.

---

## Key files

| File | Purpose |
|---|---|
| [[WIKI]] | Schema, page types, folder meanings, and editorial rules |
| [[AGENTS]] | Agent behavior contract |
| [[INBOX]] | Inbox raw intake workflow |
| [[AGENT-WIKI-SPEC-v1]] | Full v1 specification |

---

## Compile pipeline

To regenerate the machine-facing cache files and reports:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

Cache outputs live in `_system/cache/`. Required outputs:

- `pages.json` — normalized page index
- `claims.jsonl` — all extracted claims
- `relations.jsonl` — all extracted relations
- `agent-digest.json` — high-signal agent context

---
