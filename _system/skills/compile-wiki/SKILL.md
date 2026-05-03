---
name: compile-wiki
description: "Run the compile pipeline whenever the underlying vault data changes. Trigger this skill whenever the user says \"compile the wiki\", \"regenerate the cache\", \"compile\", \"run compile\", or similar phrases indicating they want to update the machine-facing artifacts."
---
# Compile the Wiki Cache

Run the compile pipeline to regenerate all machine-facing cache artifacts, the deterministic root page catalog, and maintenance reports from vault page frontmatter.

---

## When to run

Run the compile pipeline after:
- Adding or editing pages with structured frontmatter (claims, relations, timeline entries)
- Adding new question pages
- Adding source pages
- Adding source parent or source part pages for large documents
- Extracting knowledge primitives from source pages
- Resolving questions (status changes)
- Any bulk edit to page metadata

The compile pipeline is **safe to run at any time**. It is fully regenerative. It does not modify canonical knowledge pages, but it does rewrite the deterministic root `index.md` page catalog from `_system/cache/pages.json`.

---

## How to run

From the vault root:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

With verbose output:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py --verbose
```

From a different working directory:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py --vault-root /path/to/vault
```

---

## What it produces

### Required cache files (`_system/cache/`)

| File | Purpose |
|---|---|
| `pages.json` | Normalized index of all parsed pages |
| `claims.jsonl` | All extracted claims with owning page info |
| `relations.jsonl` | All extracted relations |
| `agent-digest.json` | High-signal agent context pack |
| `contradictions.json` | Detected contradiction registry |
| `questions.json` | Question registry |
| `timeline-events.json` | Chronological event index |
| `source-index.json` | Source metadata registry |

### Indexes (`_system/indexes/`)

| File | Purpose |
|---|---|
| `alias-index.json` | Alias → page ID map |
| `tag-index.json` | Tag → page IDs map |
| `id-to-path.json` | Page ID → path map |
| `path-to-id.json` | Path → page ID map |
| `pagetype-index.json` | Page type → page IDs map |

### Root page catalog (`index.md`)

The compile pipeline runs:

```bash
python3 _system/scripts/index.py --write --no-log
```

This regenerates the full root `index.md` page catalog from `_system/cache/pages.json`.

`index.py` also supports:

```bash
python3 _system/scripts/index.py --check
```

Use `--check` when you need to verify that `index.md` matches the compiled page metadata without rewriting it.

### Reports (`reports/`)

| Report | Purpose |
|---|---|
| `open-questions.md` | All open/active questions |
| `contradictions.md` | Tracked claim conflicts |
| `low-confidence.md` | Claims below confidence threshold |
| `claim-health.md` | Evidence gap and staleness overview |
| `stale-pages.md` | Pages not updated recently |
| `orphaned-claims.md` | Claims whose owning page is missing |
| `evidence-gaps.md` | Claims with no direct evidence |

### Logs (`_system/logs/`)

The compile pipeline writes one operational log entry to `_system/logs/log.md` on each run through `_system/scripts/log.py`.

---

## Validation Responsibility

This skill owns validation, cache regeneration, root catalog generation, report generation, and compile logs.

When running compile:

- validate page frontmatter and generated records
- warn when authored knowledge pages are missing required Markdown body prose
- validate large-source parent and source-part structure
- detect duplicate IDs and malformed records
- regenerate cache files, `_system/indexes/`, root `index.md`, and report artifacts
- write a concise operational log entry through `_system/scripts/log.py`
- report validation issues clearly

If validation errors occur, fix the affected canonical page or structured frontmatter, then re-run this skill. Do not repair generated cache, index, report, or log files by hand.

---

## Requirements

- Python 3.8+
- No third-party Python packages are required.

---

## Important rules

- Do NOT hand-edit files in `_system/cache/` or `_system/indexes/`. They are regenerated on each compile.
- Do NOT hand-edit `index.md` for durable prose. It is regenerated as the deterministic root page catalog.
- Reports in `reports/` are views — do not treat them as primary data.
- The compile pipeline reads `pageType`, `id`, `claims`, `relations`, `timeline` from frontmatter.
- For source pages, the compile pipeline also preserves `sourceRole`, `parentSourceId`, `sourceParts`, `partIndex`, `partCount`, and `locator` in `pages.json` and `source-index.json`.
- Pages without frontmatter, or without `id` and `pageType`, are skipped.
- The compile only modifies generated artifacts and the deterministic root `index.md` catalog.
