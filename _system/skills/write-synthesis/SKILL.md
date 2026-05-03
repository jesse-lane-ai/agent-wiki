---
name: write-synthesis
description: "Create or refresh durable synthesis pages. Use this skill when the user asks to synthesize sources, write a brief, compare documents, summarize a research thread, create an analysis, or make a timeline synthesis."
---

# Write Synthesis

This skill creates or refreshes `synthesis` pages in `syntheses/`. It owns judgment and prose for cross-source interpretation. It does not own the vault schema or deterministic file scaffolding.

Runtime synthesis schema lives in `WIKI.md` Section 4.1. Page type rules live in `WIKI.md` Section 3. Status enums live in `WIKI.md` Section 5. Evidence rules live in `WIKI.md` Section 7. Synthesis workflow rules live in `AGENT-WIKI-SPEC-v1.md` Section 10.5. The vault behavior contract lives in `AGENTS.md`.

Use `AGENT-WIKI-SPEC-v1.md` only when changing project behavior, resolving ambiguity, or when `WIKI.md` Sections 3, 4.1, 5, or 7 do not contain enough detail. If this skill or those `WIKI.md` sections conflict with `AGENT-WIKI-SPEC-v1.md`, follow `AGENT-WIKI-SPEC-v1.md`.

## When to Use

Use this skill when the user asks to:
- synthesize multiple sources or pages
- write a brief, analysis, comparison, summary, or timeline synthesis
- compare documents, sources, positions, or claims
- summarize a research thread into durable authored knowledge
- maintain an existing synthesis after new sources or claims are added

Do not use this skill for:
- atomic propositions that should be claim pages
- verbatim captured material that should be source pages
- unresolved unknowns that should be question pages
- deterministic maintenance output that should be reports
- whole-vault landing prose that should be root `overview.md`

## Step 1: Read the Contract and Runtime Reference

Before writing or refreshing a synthesis, read:

1. `AGENTS.md` for behavior rules.
2. `WIKI.md` Sections 3, 4.1, 5, and 7 for page types, runtime schema, status values, and evidence rules.
3. `AGENT-WIKI-SPEC-v1.md` Section 10.5 for synthesis workflow rules.

## Step 2: Compile or Inspect Current Cache

If the synthesis depends on current vault inventory, run compile first:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

If the user asks for a narrow synthesis over explicitly named files and the needed pages are already known, compile is optional. Do not rely on reports or logs as primary truth.

## Step 3: Select Inputs

Use canonical inputs in this order:

1. Explicit source pages, source part pages, claim pages, entities, concepts, or questions named by the user.
2. `_system/cache/pages.json`, `_system/cache/claims.jsonl`, and `_system/cache/source-index.json` for discovery.
3. Canonical pages in `sources/`, `claims/`, `entities/`, `concepts/`, `questions/`, and existing `syntheses/` when richer context is needed.

For large sources, prefer source part pages over parent source manifests when the relevant evidence comes from a specific part.

## Step 4: Decide Whether to Create or Update

Search `syntheses/` and `_system/cache/pages.json` for an existing synthesis with the same scope, audience, and synthesis type.

Update an existing synthesis when it already covers the requested scope. Create a new synthesis when the scope, time horizon, audience, or analytical question is materially different.

Choose `synthesisType` from `WIKI.md` Section 4.1:
- `summary` for compact cross-source restatements
- `overview` for broad topic orientation
- `analysis` for reasoned interpretation
- `timeline` for chronological narrative
- `brief` for decision-relevant summary
- `comparison` for side-by-side interpretation

## Step 5: Write the Body

Write substantive Markdown prose for a human reader. The body should normally include:
- scope and purpose
- source basis or coverage
- main synthesis in paragraph form
- important evidence, claims, or examples
- uncertainty, limits, contradictions, or unresolved questions
- current conclusion or next-step implication, when appropriate

Preserve uncertainty. Do not present weak, incomplete, or contested evidence as established fact.

If the synthesis introduces an important atomic proposition that needs independent evidence tracking, create or update a claim page and include that claim ID in `derivedClaims`.

If the synthesis surfaces a durable unresolved issue, create or update a question page and reference it in the body or related fields.

## Step 6: Create New Synthesis Pages

For new synthesis pages, prepare the body prose in a temporary Markdown file outside the vault, then use the deterministic scaffolder:

```bash
python3 _system/scripts/create-page.py \
  --type synthesis \
  --subtype brief \
  --slug <synthesis-slug> \
  --title "<title>" \
  --scope "<scope>" \
  --source-page <sourceId> \
  --derived-claim <claimId> \
  --body-file <prepared-body.md> \
  --no-log
```

Repeat `--source-page` and `--derived-claim` as needed. `--scope` is required.

The scaffolder owns IDs, filename, required frontmatter, duplicate checks, and body placement. This skill owns source selection, synthesis type selection, body prose, uncertainty handling, and any claim or question updates.

## Step 7: Refresh Existing Synthesis Pages

When updating an existing synthesis:
- preserve human-authored prose unless the operator explicitly asks for a rewrite
- update `updatedAt` when prose or structured fields change
- update `sourcePages` when the source basis changes
- update `derivedClaims` when claim dependencies change
- keep stale or contradicted prior context visible when it matters to the current interpretation

Do not regenerate a synthesis mechanically on every compile run.

## Step 8: Log the Synthesis Batch

After successfully creating or refreshing one or more synthesis pages, write one operational log entry:

```bash
python3 _system/scripts/log.py --message "write-synthesis: updated <count> syntheses; sources=<count> claims=<count>"
```

Do not write a log entry when no synthesis page changed.

## Step 9: Report Results

Report a concise summary:
- synthesis pages created or refreshed
- source pages and claim pages used
- questions or claims created or updated
- notable uncertainty, contradictions, or gaps
- whether compile reported validation issues

## Checklist

- [ ] Read `AGENTS.md`, `WIKI.md` Sections 3, 4.1, 5, and 7, and `AGENT-WIKI-SPEC-v1.md` Section 10.5
- [ ] Identify the synthesis scope, audience, and `synthesisType`
- [ ] Select canonical source pages, source parts, claims, and related pages
- [ ] Check for an existing synthesis before creating a new one
- [ ] Use `_system/scripts/create-page.py --no-log` for new synthesis pages
- [ ] Include required `--scope`
- [ ] List source basis in `sourcePages` when sources are used
- [ ] List tracked claim dependencies in `derivedClaims` when claims are used
- [ ] Preserve uncertainty, contradictions, and important caveats
- [ ] Create or update claim/question pages when needed
- [ ] Write one operational log entry for the synthesis batch
- [ ] Report results
