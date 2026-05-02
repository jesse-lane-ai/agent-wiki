# Agentics Vault

Agentics Vault is a structured, markdown-first wiki for building an Obsidian knowledge base that humans can read and agents can safely maintain.

The vault keeps human-authored pages, structured frontmatter, claims, evidence, relations, and generated machine-facing caches in separate lanes. [[AGENT-WIKI-SPEC-v1]] is the canonical technical contract.

## Quick Start

Start with the onboarding docs:

1. [[INITIALIZE]] for first-run setup and local `import-link` configuration.
2. [[AGENTS]] for the agent behavior contract.
3. [[WIKI]] for the human-readable schema guide.
4. [[AGENT-WIKI-SPEC-v1]] for the full v1.3 specification.

For a new agent session, use a prompt like:

```text
Read INITIALIZE.md, AGENTS.md, WIKI.md, and AGENT-WIKI-SPEC-v1.md before editing.
Treat AGENT-WIKI-SPEC-v1.md as the canonical schema.
```

Before importing external material, configure `_system/skills/import-link/config.json` as described in [[INITIALIZE]]. Do not assume another user's Obsidian path, browser profile, model, or retrieval tools are valid.

## What This Repo Contains

- The v1.3 wiki specification in [[AGENT-WIKI-SPEC-v1]]
- Human and agent operating docs in [[WIKI]], [[AGENTS]], [[INITIALIZE]], and [[INBOX]]
- A deterministic root page catalog in [[index]]
- A stdlib-only compile pipeline in `_system/skills/compile-wiki/`
- Agent skills for import, inbox processing, extraction, and compilation under `_system/skills/`
- Gitignored runtime outputs for caches, indexes, logs, and reports

Fresh checkouts may omit empty content and runtime folders. Initialization, import, and compile workflows create missing folders when needed.

Current top-level vault shape:

```text
<vault>/
  AGENTS.md
  AGENT-WIKI-SPEC-v1.md
  INBOX.md
  INITIALIZE.md
  README.md
  WIKI.md
  index.md

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

These outputs are generated artifacts. Do not hand-edit them, and do not treat reports or logs as primary truth. Durable orientation prose belongs in the root documentation files, not `index.md`.

## Skills

Skills live under `_system/skills/`:

- `compile-wiki` regenerates the root page catalog, caches, indexes, logs, and reports.
- `import-link` imports external links and captures directly into canonical `source` pages after local configuration in `_system/skills/import-link/config.json`.
- `process-inbox` promotes raw files dropped into `_inbox/` into canonical `source` pages and moves originals to `raw/`.
- `extract-knowledge-primitives` extracts entities, concepts, claims, evidence, questions, and relations from sources.
- `update-overview` creates or refreshes root `overview.md` as the human-facing vault landing page.

## Scheduled Work

This repo does not ship a scheduler, daemon, or task runner. For recurring maintenance, run an external scheduler that launches agents with narrow tasks:

- inbox processing via `_system/skills/process-inbox/`
- compile/regeneration via `_system/skills/compile-wiki/`
- extraction or cleanup via the relevant skill

Re-run compile after meaningful vault changes so `index.md`, caches, indexes, logs, and reports stay current.

## Customization

Treat this repository as a foundation for your own wiki, not a finished off-the-shelf knowledge system.

You will likely customize:

- domain-specific page conventions
- source import settings
- extraction prompts and review workflows
- maintenance schedules
- ontology and relationship vocabularies

Keep [[AGENT-WIKI-SPEC-v1]] as the source of truth when changing schema behavior.
