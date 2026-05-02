---
name: update-overview
description: "Create or refresh the root overview.md landing page for the vault. Use this skill when the user asks to update the vault overview, create the landing page, summarize the vault, refresh overview.md, or produce a human-facing vault summary."
---

# Update Vault Overview

This skill creates or refreshes root `overview.md`, the human-facing narrative landing page for the vault. It does not own the schema.

Canonical schema, page type rules, authority rules, and examples live in `AGENT-WIKI-SPEC-v1.md`. The vault behavior contract lives in `AGENTS.md`. If this skill conflicts with `AGENT-WIKI-SPEC-v1.md`, follow the spec.

## When to Use

Use this skill when:
- the user asks for a vault overview, vault landing page, or root `overview.md`
- the vault has changed meaningfully and the human-facing overview should be refreshed
- the user wants a paragraph-form summary of the vault and its page types

Do not run this skill automatically as part of compile. `overview.md` is durable AI-maintained prose, not a deterministic compile artifact.

## Step 1: Read the Contract and Spec

Before updating `overview.md`, read:

1. `AGENTS.md` for behavior rules.
2. `AGENT-WIKI-SPEC-v1.md` for the `overview.md` contract, page type rules, and schema.
3. `WIKI.md` as a quick editorial reference when needed.

Use `AGENT-WIKI-SPEC-v1.md` Section 7.9 for the root overview page behavior.

## Step 2: Compile First

Run compile before writing the overview so cache inputs are current:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

If compile reports validation issues, fix or report those issues before relying on generated cache data for the overview.

## Step 3: Gather Inputs

Use compiled and canonical inputs, in this order:

1. `_system/cache/pages.json` for page inventory, page types, titles, statuses, paths, and metadata.
2. `_system/cache/agent-digest.json` for compact high-signal context.
3. Canonical pages in content folders when the overview needs richer context than the cache provides.
4. Root docs such as `README.md`, `WIKI.md`, and `INBOX.md` for project and workflow orientation.

Do not use reports or logs as primary truth. Reports may help identify maintenance concerns, but the overview should be grounded in canonical pages and compiled cache data.

## Step 4: Create or Refresh `overview.md`

Write `overview.md` at the vault root.

If the file does not exist, create it with frontmatter using the canonical universal fields from `AGENT-WIKI-SPEC-v1.md` and:

```yaml
id: meta.overview
pageType: overview
title: Vault Overview
status: active
```

Set `createdAt` and `updatedAt` using `YYYY-MM-DD`. Include `aliases` and `tags` as required by the spec.

If the file already exists:
- preserve any human-authored prose unless the user explicitly asks for a rewrite
- update `updatedAt` when the overview prose or frontmatter changes
- keep `pageType: overview`
- keep the file at root `overview.md`

## Step 5: Write the Overview

Write in long-form article style for a human reader.

The overview should include:
- a vault-level summary
- paragraph-form summaries for each active page type represented in the vault
- clear orientation about what the reader can find and where the material lives
- an honest account of sparse, draft, or incomplete areas when the vault is small or early-stage

Use headings sparingly and make the page readable as a landing article, not a generated table or report.

Do not make unsupported claims about the vault. If the cache shows no pages for a page type, either omit that page type or describe it as a supported structure that currently has no active pages, depending on what best serves the reader.

## Step 6: Authority Rules

`overview.md` is orientation, not evidence.

Do not:
- treat `overview.md` as primary evidence for claims
- place claim/evidence records only in the overview
- use the overview to replace canonical source, entity, concept, claim, synthesis, or question pages
- regenerate it mechanically on every compile run

If the overview describes a substantive claim that should be tracked, create or update the appropriate canonical page or claim record instead of leaving the claim only in overview prose.

## Step 7: Log the Update

After successfully creating or refreshing `overview.md`, write one operational log entry:

```bash
python3 _system/scripts/log.py --message "update-overview: refreshed root overview.md; pageTypes=<count> pages=<count>"
```

Do not write a log entry if no file was changed.

## Step 8: Report Results

Report a concise summary:
- whether `overview.md` was created or refreshed
- which inputs were used
- whether compile had validation issues
- any notable gaps, such as missing summaries or sparse page types
