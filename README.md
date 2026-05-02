# Agentics Vault

Agentics Vault is a structured, markdown-first wiki for building an Obsidian knowledge base that humans can read and agents can safely maintain.

The vault keeps human-authored pages, structured frontmatter, claims, evidence, relations, and generated machine-facing caches in separate lanes. [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) is the compact runtime schema reference; [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md) is the full project and development contract.

## Quick Start

Start with the onboarding docs:

1. [ONBOARD.md](ONBOARD.md) for first-run setup, the onboarding probe, local system configuration, and `import-link` configuration.
2. [AGENTS.md](AGENTS.md) for the agent behavior contract.
3. [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) for the runtime schema and examples; [section 5](WIKI.md#5-status-vocabularies) for status enums; [section 3](WIKI.md#3-page-types) for page types.
4. [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md) only when changing project behavior, scripts, skills, configuration policy, validation behavior, or when [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) is insufficient.

For a new agent session, use a prompt like:

```text
Read ONBOARD.md, AGENTS.md, and WIKI.md sections 4.1, 5, 6, 7, 8, 12, and 13 before ordinary vault work.
Use AGENT-WIKI-SPEC-v1.md only for project changes, ambiguity, or missing runtime detail.
```

Before importing external material, configure `_system/skills/import-link/config.json` as described in [ONBOARD.md](ONBOARD.md). Do not assume another user's Obsidian path, browser profile, model, or retrieval tools are valid.

For fresh checkouts or uncertain local setup, run the read-only onboarding probe:

```bash
python3 _system/scripts/onboard.py --check
```

Use the probe output to choose Python, optional `.venv/` setup, inbox conversion policy, and `_system/config.json` values with the user. For compact setup prompts, run:

```bash
python3 _system/scripts/onboard.py --check --questions
```

## What This Repo Contains

- The compact runtime schema in [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas)
- The v1.3 project/development specification in [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md)
- Human and agent operating docs in [WIKI.md section 1.1](WIKI.md#11-documentation-layers), [AGENTS.md](AGENTS.md), [ONBOARD.md](ONBOARD.md), and [INBOX.md](INBOX.md)
- A deterministic root page catalog in [index.md](index.md)
- An optional human-facing vault landing page in [overview.md](overview.md)
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
  ONBOARD.md
  README.md
  WIKI.md
  index.md
  overview.md

  sources/
    parts/
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
    config.json
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

These outputs are generated artifacts. Do not hand-edit them, and do not treat reports or logs as primary truth. Durable orientation prose belongs in root documentation files such as `overview.md`, not `index.md`.

## Skills

Skills live under `_system/skills/`:

- `compile-wiki` regenerates the root page catalog, caches, indexes, logs, and reports.
- `import-link` imports external links and captures directly into canonical `source` pages after local configuration in `_system/skills/import-link/config.json`. Large captures are partitioned into parent source pages and source parts.
- `process-inbox` promotes raw files dropped into `_inbox/` into canonical `source` pages and moves originals to `raw/`. Large documents are represented by a short parent source page plus source part pages under `sources/parts/`.
- `extract-knowledge-primitives` extracts entities, concepts, claims, evidence, questions, and relations from sources. For large sources, extraction operates on source parts rather than the parent manifest.
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

Use [WIKI.md section 4.1](WIKI.md#41-common-runtime-schemas) for ordinary vault work. Keep [AGENT-WIKI-SPEC-v1.md](AGENT-WIKI-SPEC-v1.md) as the source of truth when changing schema, script, skill, configuration, or validation behavior.
