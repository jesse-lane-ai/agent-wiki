# Agentics Vault

Agentics Vault is a structured, markdown-first wiki for building an Obsidian knowledge base that agents can read, maintain, and compile into machine-facing caches.

It is a starting framework, not a finished product. The value comes from adapting it to your own domain, curating the ontology, and iterating on the workflows over time.

## Initialize The Wiki

A fresh agent should not start by guessing how the vault works. Initialize it by having the agent read:

1. [[INITIALIZE]] for the first-run checklist and local configuration.
2. [[AGENTS]] for the operating contract it must follow before making edits.

After that, the agent should read:

- [[index]] for navigation
- [[WIKI]] for schema and editorial rules
- [[INBOX]] for intake pointer handling
- [[AGENT-WIKI-SPEC-v1]] for the full technical specification

In practice, the initialization prompt can be as simple as:

```text
Read INITIALIZE.md and AGENTS.md first. Then read index.md and WIKI.md.
Follow the vault contract before making any changes.
```

Have your agent verify the wiki is initialized. Before using `import-note`, configure the local vault/import settings in [[INITIALIZE]].

## What Exists Today

This repo currently gives you:

- a vault structure for sources, entities, concepts, claims, syntheses, procedures, questions, and reports
- a compile pipeline that emits normalized caches under `_wiki/cache/`
- an import skill in `_wiki/skills/import-note/`
- an inbox-processing skill in `_wiki/skills/process-new-notes/`
- an extraction skill in `_wiki/skills/extract-knowledge-primitives/`
- a compile skill in `_wiki/skills/compile-wiki/`

The compile pipeline is run with:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

That script parses the vault and regenerates machine-facing artifacts such as `pages.json`, `claims.jsonl`, `relations.jsonl`, `agent-digest.json`, and the report pages.

## Scheduled Agent Work

If you want recurring maintenance, do not rely on a long-running hidden process inside the vault. Set up your own scheduler outside the repo and have it launch an agent or subagent on a defined cadence.

Typical scheduled jobs look like this:

- inbox triage on a frequent schedule, pointed at `_wiki/skills/process-new-notes/`
- compile/regeneration on a frequent or post-ingest schedule, pointed at `_wiki/skills/compile-wiki/`
- extraction or cleanup passes, each pointed at a dedicated skill

The important part is the pattern:

1. launch an agent with a narrow task
2. point it at the relevant skill
3. let it run on its own schedule
4. re-run compile so caches and reports stay current

This repo does not currently ship a scheduler, heartbeat daemon, or task runner. You need to supply that orchestration in your own environment.

## What Is Still Missing

This vault is not feature-complete yet.

Skills still need to be created for:

- relation extraction and cleanup
- broader maintenance and QA workflows

Testing is also still incomplete. The compile pipeline has been hardened, but the larger workflow needs stronger coverage around import, extraction, validation, scheduled runs, and end-to-end agent behavior.

## Make It Your Own

This repository should be treated as a foundation for your own wiki, not as a finished off-the-shelf knowledge system.

You will need to:

- refine the schema to match your domain
- configure `import-note` for your local vault paths and retrieval tools
- add or replace skills to fit your workflows
- decide what should be automated versus reviewed by a human
- keep curating pages, claims, evidence, and open questions over time

If you work on the vault consistently, it can become a reliable personal or team knowledge system. If you do not keep shaping it, it will stay a generic starter skeleton.
