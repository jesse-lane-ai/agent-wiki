# Agentics Vault

Agentics Vault is a structured, markdown-first wiki for building an Obsidian knowledge base that humans can read and agents can safely maintain.

The vault keeps human-authored pages, structured frontmatter, claims, evidence, relations, and generated machine-facing caches in separate lanes. [[AGENT-WIKI-SPEC-v1]] is the canonical technical contract.

## Quick Start

Start with the onboarding docs:

1. [[INITIALIZE]] for first-run setup and local `import-note` configuration.
2. [[AGENTS]] for the agent behavior contract.
3. [[WIKI]] for the human-readable schema guide.
4. [[AGENT-WIKI-SPEC-v1]] for the full v1.1 specification.

For a new agent session, use a prompt like:

```text
Read INITIALIZE.md, AGENTS.md, WIKI.md, and AGENT-WIKI-SPEC-v1.md before editing.
Treat AGENT-WIKI-SPEC-v1.md as the canonical schema.
```

Before importing external material, configure `_wiki/skills/import-note/config.json` as described in [[INITIALIZE]]. Do not assume another user's Obsidian path, browser profile, model, or retrieval tools are valid.

## What This Repo Contains

- The v1.1 wiki specification in [[AGENT-WIKI-SPEC-v1]]
- Human and agent operating docs in [[WIKI]], [[AGENTS]], [[INITIALIZE]], [[INBOX]], and [[index]]
- A stdlib-only compile pipeline in `_wiki/skills/compile-wiki/`
- Agent skills for import, inbox processing, extraction, and compilation under `_wiki/skills/`
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
  procedures/
  questions/
  reports/

  _inbox/
  _attachments/
  _archive/
  _wiki/
    cache/
    indexes/
    logs/
    skills/
```

## Compile

The compiler has no third-party Python dependencies. Run it with the system Python:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

It reads vault pages and emits generated artifacts such as:

- `_wiki/cache/pages.json`
- `_wiki/cache/claims.jsonl`
- `_wiki/cache/relations.jsonl`
- `_wiki/cache/agent-digest.json`
- `_wiki/cache/validation-issues.json`
- `_wiki/indexes/`
- `_wiki/logs/`
- `reports/`

These outputs are compile artifacts. Do not hand-edit them, and do not treat reports as primary truth.

## Skills

Skills live under `_wiki/skills/`:

- `compile-wiki` regenerates caches, indexes, logs, and reports.
- `import-note` imports external material after local configuration in `_wiki/skills/import-note/config.json`.
- `process-new-notes` triages `_inbox/` pointer files into canonical `source` pages.
- `extract-knowledge-primitives` extracts entities, concepts, claims, evidence, and relations from sources.

## Scheduled Work

This repo does not ship a scheduler, daemon, or task runner. For recurring maintenance, run an external scheduler that launches agents with narrow tasks:

- inbox triage via `_wiki/skills/process-new-notes/`
- compile/regeneration via `_wiki/skills/compile-wiki/`
- extraction or cleanup via the relevant skill

Re-run compile after meaningful vault changes so caches, indexes, logs, and reports stay current.

## Customization

Treat this repository as a foundation for your own wiki, not a finished off-the-shelf knowledge system.

You will likely customize:

- domain-specific page conventions
- source import settings
- extraction prompts and review workflows
- maintenance schedules
- ontology and relationship vocabularies

Keep [[AGENT-WIKI-SPEC-v1]] as the source of truth when changing schema behavior.
