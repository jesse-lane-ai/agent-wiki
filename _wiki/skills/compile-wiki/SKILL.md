---
name: compile-wiki
description: "Run the compile pipeline whenever the underlying vault data changes. Trigger this skill whenever the user says \"compile the wiki\", \"regenerate the cache\", \"compile\", \"run compile\", or similar phrases indicating they want to update the machine-facing artifacts."
---
# Compile the Wiki Cache

Run the compile pipeline to regenerate all machine-facing cache artifacts and maintenance reports from vault page frontmatter.

---

## When to run

Run the compile pipeline after:
- Adding or editing pages with structured frontmatter (claims, relations, timeline entries)
- Adding new question pages
- Adding source pages
- Extracting knowledge primitives from source pages
- Resolving questions (status changes)
- Any bulk edit to page metadata

The compile pipeline is **safe to run at any time**. It is fully regenerative and does not modify page content.

---

## How to run

From the vault root:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

With verbose output:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py --verbose
```

From a different working directory:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py --vault-root /path/to/vault
```

---

## What it produces

### Required cache files (`_wiki/cache/`)

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

### Indexes (`_wiki/indexes/`)

| File | Purpose |
|---|---|
| `alias-index.json` | Alias → page ID map |
| `tag-index.json` | Tag → page IDs map |
| `id-to-path.json` | Page ID → path map |
| `path-to-id.json` | Path → page ID map |
| `pagetype-index.json` | Page type → page IDs map |

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

### Logs (`_wiki/logs/`)

A daily compile log (`compile-YYYY-MM-DD.jsonl`) is appended on each run.

---

## Validation Responsibility

This skill owns validation, cache regeneration, report generation, and compile logs.

When running compile:

- validate page frontmatter and generated records
- detect duplicate IDs and malformed records
- regenerate cache, index, report, and log artifacts
- report validation issues clearly

If validation errors occur, fix the affected canonical page or structured frontmatter, then re-run this skill. Do not repair generated cache, index, report, or log files by hand.

---

## Requirements

- Python 3.8+
- No third-party Python packages are required.

---

## Important rules

- Do NOT hand-edit files in `_wiki/cache/` or `_wiki/indexes/`. They are regenerated on each compile.
- Reports in `reports/` are views — do not treat them as primary data.
- The compile pipeline reads `pageType`, `id`, `claims`, `relations`, `timeline` from frontmatter.
- Pages without frontmatter, or without `id` and `pageType`, are skipped.
- The compile does not modify any page files.
