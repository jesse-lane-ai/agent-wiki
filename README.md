# Agent Wiki

An Obsidian-compatible knowledge vault that AI agents can safely maintain.

Drop notes, PDFs, transcripts, links, or research into `_inbox/`. Agents promote them into source pages, extract claims and evidence, link entities and concepts, track open questions, flag contradictions, and compile the vault into machine-readable caches.

Agent Wiki supports two operating modes:

- **Vault wiki** — the current repository/vault structure. Raw files enter through `_inbox/`, agents promote them into `sources/`, and original raw files move to `raw/`.
- **Workspace wiki** — the same wiki structure stored inside a larger workspace, defaulting to `workspace/wiki`. The CLI discovers new or changed non-code files outside `wiki/`; agents decide which files become canonical source pages. Original workspace files stay in place and are never modified by the wiki workflow.

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

Install the local CLI during development:

```bash
npm install
npm run build
npm link
```

Initialize a vault-style wiki folder:

```bash
agent-wiki init --type vault --root /path/to/wiki --write-config
```

Initialize a workspace wiki inside a larger project:

```bash
agent-wiki init --type workspace --workspace-root /path/to/workspace --wiki-dir wiki --write-config
```

Add `--with-template` when the initialized wiki should be runnable by a fresh agent immediately. It copies missing bundled docs and root-level `skills/` into the wiki without overwriting existing files:

```bash
agent-wiki init --type vault --root /path/to/wiki --write-config --with-template
```

Check wiki health without changing files:

```bash
agent-wiki doctor --wiki-root /path/to/wiki
```

Ingest text or markdown from `_inbox/` in a new agent session:

```text
Read AGENTS.md, then run the local process-inbox skill from skills/
```

*Text and markdown ingest works out of the box.*

Then run the `extract-knowledge-primitives` skill to extract claims, evidence, relations, questions, and contradictions. From a new agent session:

```text
Read AGENTS.md and run the local extract-knowledge-primitives skill from skills/
```

Then compile the wiki:

```text
Read AGENTS.md and run the local compile-wiki skill from skills/
```

Write a durable synthesis when you need cross-source interpretation, a brief, a comparison, or a timeline narrative:

```text
Read AGENTS.md and run the local write-synthesis skill from skills/
```

Generate the overview landing page:

```text
Read AGENTS.md and run the local update-overview skill from skills/
```

For daily vault work, start a new agent session, then:

```text
Read AGENTS.md, and WIKI.md sections 4.1, 5, 6, 7, 8, 12, and 13 before ordinary vault work.
Use AGENT-WIKI-SPEC-v2.md only for project changes, ambiguity, or missing runtime detail.
```

These can all be scheduled as tasks for an agent.

## Workspace Mode

Workspace mode is for projects where the wiki lives inside a larger project or company folder:

```text
workspace/
  docs/
  research/
  decisions/
  wiki/
    sources/
    entities/
    concepts/
```

Discover source candidates outside the wiki directory:

```bash
agent-wiki workspace pending --workspace-root /path/to/workspace --json
```

The pending command reports files that are new or changed relative to local state. It returns path, modified time, size, extension, sha256, recommended source type, and any known source-page mapping. The command does not read files semantically, create pages, or modify source files.

Agents should use `skills/process-workspace-sources/SKILL.md` to review that worklist and create canonical source pages inside `wiki/sources/` with `originPath` pointing back to the workspace-relative source path. After source pages exist, the existing extraction and compile workflows apply unchanged.

After an agent creates a source page for a workspace file, it can record the local mapping:

```bash
agent-wiki workspace mark-sourced \
  --workspace-root /path/to/workspace \
  --path docs/customer-research.md \
  --source-id source.2026-06-26.document.customer-research \
  --source-path sources/2026-06-26-document-customer-research.md
```

## Core documents

- [ONBOARD.md](ONBOARD.md) — first-run setup, onboarding probe, local configuration, and import-link setup.
- [AGENTS.md](AGENTS.md) — the agent behavior contract.
- [WIKI.md](WIKI.md) — page types, schemas, status enums, runtime examples, linking rules, and vault rules.
- [AGENT-WIKI-SPEC-v2.md](AGENT-WIKI-SPEC-v2.md) — full project contract for changing behavior, scripts, skills, configuration, or validation.

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
agent-wiki compile
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

Skills live under `skills/`:

- `compile-wiki` regenerates the root page catalog, caches, indexes, logs, and reports.
- `import-link` imports external links and captures into canonical `source` pages after local configuration in `skills/import-link/config.json`. It uses `agent-wiki create-page` to write source pages. Large captures are partitioned into parent source pages and source parts.
- `process-inbox` promotes raw files dropped into `_inbox/` into canonical `source` pages and moves originals to `raw/`. It uses `agent-wiki create-page` to write source pages. Large documents are represented by a short parent source page plus source part pages under `sources/parts/`.
- `process-workspace-sources` promotes selected files discovered outside a workspace wiki into canonical `source` pages without modifying or moving the original workspace files.
- `extract-knowledge-primitives` extracts entities, concepts, claims, evidence, questions, and relations from sources. It uses `agent-wiki create-page` for new primitive page files. For large sources, extraction operates on source parts rather than the parent manifest.
- `write-synthesis` creates or refreshes durable synthesis pages for cross-source summaries, briefs, analyses, comparisons, and timeline narratives. It uses `agent-wiki create-page` for new synthesis page files.
- `update-overview` creates or refreshes root `overview.md` as the human-facing vault landing page.

The page scaffolder covers required frontmatter for `source`, `entity`, `concept`, `claim`, `question`, and `synthesis` pages. It does not invent optional metadata, evidence, relationships, body prose, source capture, synthesis judgment, or large-document split decisions.

## Scheduled Work

This repo does not ship a scheduler, daemon, or task runner. For recurring maintenance, run an external scheduler that launches agents with narrow tasks:

- inbox processing via `skills/process-inbox/`
- compile/regeneration via `skills/compile-wiki/`
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

Use [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) for ordinary wiki work. Keep [AGENT-WIKI-SPEC-v2.md](AGENT-WIKI-SPEC-v2.md) as the source of truth when changing schema, script, skill, configuration, or validation behavior.

## Updating an Existing Agent Wiki

Before updating, commit or back up your current vault. Updates may change root documentation, scripts, skills, configuration templates, and generated behavior.

To update from the upstream repository:

```bash
git fetch origin --tags
git checkout main
git pull --ff-only origin main
```

To update to a specific release tag instead of the latest `main`:

```bash
git fetch origin --tags
git checkout v1.4.0
```

Do not overwrite local `_system/config.json`; it is local-only operator policy. Compare `_system/config.example.json` after updating and copy only settings you explicitly want.

After updating, run the onboarding probe and compile pipeline:

```bash
agent-wiki onboard --check
agent-wiki compile
```

If the release notes mention a migration script, run its dry-run mode first and review the planned changes before applying it.

## Development Workflow

Changes to this project should move from contract to implementation in a consistent order.

When adding a feature or changing project behavior:

1. Update [AGENT-WIKI-SPEC-v2.md](AGENT-WIKI-SPEC-v2.md) first.
2. Update configuration files or configuration templates when the change affects operator policy, defaults, or local setup.
3. Update deterministic scripts.
4. Update skill instructions and skill-local support files.
5. Update root-level Markdown documentation other than the specification.

Skip any step that the change does not affect. The specification should be reviewed first because it defines the contract that configuration, scripts, skills, and root-level documentation implement.

## Harness and Models

This project has been tested and working with:

- OpenCode on Windows (PowerShell) + Kimi K2.6 (openrouter)
- Claude Desktop on Windows + Sonnet 4.6 (low)
- Claude CLI on WSL2 + Sonnet 4.6
- Codex CLI on Windows (PowerShell) and WSL2 + GPT-5.4
