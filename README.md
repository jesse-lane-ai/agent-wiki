# Agent Wiki

An Obsidian-compatible knowledge vault that AI agents can safely maintain.

Drop notes, PDFs, transcripts, links, or research into `_inbox/`. Agents promote them into source pages, extract claims and evidence, link entities and concepts, track open questions, flag contradictions, and compile the vault into machine-readable caches.

Most LLM wiki projects focus on generating and maintaining wiki pages.

Agent Wiki focuses on evidence-aware structured knowledge:

- claims
- evidence
- relations
- questions
- contradictions
- timelines
- compiled agent caches

It is markdown-first, Git-friendly, Obsidian-compatible, and designed for both humans and agents.

Inspired by Karpathy’s [LLM Wiki gist][karpathy-wiki].

[karpathy-wiki]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Why Agent Wiki exists

LLMs are useful when they have reliable context. They are unreliable when every task starts from a pile of raw files, old notes, chat logs, and half-remembered summaries.

Agent Wiki gives agents a maintained knowledge layer:

- sources stay separate from summaries
- claims stay separate from prose
- evidence stays attached to claims
- contradictions are tracked instead of hidden
- open questions remain visible
- generated caches can be rebuilt instead of hand-edited

The result is a vault humans can read and agents can compile into compact runtime context.

## How it works

```text
_inbox/
  raw notes, PDFs, links, transcripts
        ↓
sources/
  canonical source pages
        ↓
claims/       entities/       concepts/       questions/
  structured knowledge primitives with evidence and relations
        ↓
_system/cache/
  compact agent-facing indexes
        ↓
index.md      overview.md      reports/
  human-facing generated views
```

Structured evidence, relations, contradictions, and timeline events are stored in page frontmatter and compiled cache files rather than separate root folders.

## Quick Start

Clone the repo and ask your agent:

```text
Read ONBOARD.md, then onboard me.
```

Ingest text or markdown from `_inbox/` in a new agent session:

```text
Read AGENTS.md, then run the local process-inbox skill from _system/skills/
```

*Text and markdown ingest works out of the box.*

Then run the `extract-knowledge-primitives` skill to extract claims, evidence, relations, questions, and contradictions. From a new agent session:

```text
Read AGENTS.md and run the local extract-knowledge-primitives skill from _system/skills/
```

Then compile the wiki:

```text
Read AGENTS.md and run the local compile-wiki skill from _system/skills/
```

Write a durable synthesis when you need cross-source interpretation, a brief, a comparison, or a timeline narrative:

```text
Read AGENTS.md and run the local write-synthesis skill from _system/skills/
```

Generate the overview landing page:

```text
Read AGENTS.md and run the local update-overview skill from _system/skills/
```

For daily vault work, start a new agent session, then:

```text
Read AGENTS.md, and WIKI.md sections 4.1, 5, 6, 7, 8, 12, and 13 before ordinary vault work.
Use AGENT-WIKI-SPEC-v1.md only for project changes, ambiguity, or missing runtime detail.
```

These can all be scheduled as tasks for an agent.

## Core documents

- [ONBOARD.md](ONBOARD.md) — first-run setup, onboarding probe, local configuration, and import-link setup.
- [AGENTS.md](AGENTS.md) — the agent behavior contract.
- [WIKI.md](WIKI.md) — page types, schemas, status enums, runtime examples, and vault rules.
- [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md) — full project contract for changing behavior, scripts, skills, configuration, or validation.

## How Agent Wiki differs from other LLM wiki projects

Other LLM wiki projects focus on generating and maintaining wiki pages.

Agent Wiki focuses on evidence-aware structured knowledge. The wiki is not just prose; it is a vault of linked primitives that agents can safely maintain and compile.

| Area | Typical LLM wiki | Agent Wiki |
|---|---|---|
| Main output | Wiki pages | Wiki pages + structured knowledge primitives |
| Truth model | Summaries and links | Claims backed by evidence |
| Contradictions | Usually prose-level | First-class tracked objects |
| Runtime use | Read pages as context | Compile compact machine-facing caches |
| Human editing | Often mixed with generated content | Human and generated lanes stay separate |
| Agent safety | Prompt conventions | Explicit behavior contract and schemas |

## What Agent Wiki produces

A maintained vault can produce human-readable pages and machine-facing artifacts such as:

```text
sources/
  canonical source pages

entities/
  people, companies, projects, tools, locations, and other named things

concepts/
  reusable ideas, patterns, methods, and definitions

claims/
  atomic statements with source-backed evidence

questions/
  unresolved issues, unknowns, and research targets

syntheses/
  higher-level summaries and interpretations

reports/
  generated human-readable views

_system/cache/
  agent-digest.json
  claims.jsonl
  relations.jsonl
  pages.json

_system/indexes/
  generated machine-readable indexes
```

## Design principles

Agent Wiki is built around a few strict rules:

- Human-authored notes and agent-authored material should stay distinguishable.
- Sources are not the same thing as summaries.
- Claims should be traceable to evidence.
- Contradictions should be tracked, not hidden.
- Generated reports are views, not canonical truth.
- Compiled caches should be rebuilt by tools, not hand-edited.
- Agents should follow explicit schemas and behavior contracts.

## Compile

The compiler has no third-party Python dependencies. Run it with the system Python:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

It reads vault pages and emits generated artifacts such as:

- `index.md`
- `_system/cache/pages.json`
- `_system/cache/claims.jsonl`
- `_system/cache/relations.jsonl`
- `_system/cache/agent-digest.json`
- `_system/cache/validation-issues.json`
- `_system/indexes/`
- `_system/logs/log.md`
- `reports/`

These outputs are generated artifacts. Do not hand-edit them, and do not treat reports or logs as primary truth. Durable orientation prose belongs in root documentation files such as `overview.md`, not `index.md`.

## Skills

Skills live under `_system/skills/`:

- `compile-wiki` regenerates the root page catalog, caches, indexes, logs, and reports.
- `import-link` imports external links and captures into canonical `source` pages after local configuration in `_system/skills/import-link/config.json`. It uses `_system/scripts/create-page.py` to write source pages. Large captures are partitioned into parent source pages and source parts.
- `process-inbox` promotes raw files dropped into `_inbox/` into canonical `source` pages and moves originals to `raw/`. It uses `_system/scripts/create-page.py` to write source pages. Large documents are represented by a short parent source page plus source part pages under `sources/parts/`.
- `extract-knowledge-primitives` extracts entities, concepts, claims, evidence, questions, and relations from sources. It uses `_system/scripts/create-page.py` for new primitive page files. For large sources, extraction operates on source parts rather than the parent manifest.
- `write-synthesis` creates or refreshes durable synthesis pages for cross-source summaries, briefs, analyses, comparisons, and timeline narratives. It uses `_system/scripts/create-page.py` for new synthesis page files.
- `update-overview` creates or refreshes root `overview.md` as the human-facing vault landing page.

The page scaffolder covers required frontmatter for `source`, `entity`, `concept`, `claim`, `question`, and `synthesis` pages. It does not invent optional metadata, evidence, relationships, body prose, source capture, synthesis judgment, or large-document split decisions.

## Scheduled Work

This repo does not ship a scheduler, daemon, or task runner. For recurring maintenance, run an external scheduler that launches agents with narrow tasks:

- inbox processing via `_system/skills/process-inbox/`
- compile/regeneration via `_system/skills/compile-wiki/`
- extraction, synthesis, or cleanup via the relevant skill

Re-run compile after meaningful vault changes so `index.md`, caches, indexes, logs, and reports stay current.

## Customization

Treat this repository as a foundation for your own wiki, not a finished off-the-shelf knowledge system.

You will likely customize:

- domain-specific page conventions
- source import settings
- extraction prompts and review workflows
- maintenance schedules
- ontology and relationship vocabularies

Use [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) for ordinary vault work. Keep [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md) as the source of truth when changing schema, script, skill, configuration, or validation behavior.

## Harness and Models

This project has been tested and working with:

- OpenCode on Windows (PowerShell) + Kimi K2.6 (openrouter)
- Claude Desktop on Windows + Sonnet 4.6 (low)
- Claude CLI on WSL2 + Sonnet 4.6
- Codex CLI on Windows (PowerShell) and WSL2 + GPT-5.4
