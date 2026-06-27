---
name: process-workspace-sources
description: "Process workspace-mode source candidates discovered outside the wiki directory. Use this when the user asks to process workspace files, scan workspace sources, or promote changed workspace files into canonical source pages."
---

# Process Workspace Sources

This skill promotes selected files from a workspace into canonical `source` pages inside the workspace wiki. It is the workspace-mode counterpart to `process-inbox`, but it does **not** move, rewrite, archive, or otherwise modify the original workspace files.

## Step 1: Read the Contract

Before touching anything, read:

1. `AGENTS.md`
2. `WIKI.md` Sections 4.1, 5, 12, and 13
3. `AGENT-WIKI-SPEC-v2.md` only when changing behavior or resolving ambiguity

Key rules:

- The source files belong to the workspace owner. Leave them in place.
- Workspace files are discovery inputs, not canonical evidence until represented by `sources/` pages.
- Canonical source pages live inside the wiki directory, usually `wiki/sources/`.
- Use `_system/scripts/create-page.py` from the wiki root to create source pages.
- New source pages use `status: unprocessed` and `sourceRole: whole` unless partitioned.
- Large source parent/part behavior matches the existing source schema.

## Step 2: Get the Workspace Worklist

From the project root, list new or changed non-code source candidates:

```bash
agent-wiki workspace pending --workspace-root . --json
```

If the console script is not installed yet, use:

```bash
python3 -m agent_wiki.cli workspace pending --workspace-root . --json
```

The command returns an agent-readable list with:

- workspace-relative path
- absolute path
- modified time
- size
- sha256
- reason (`new` or `changed`)
- recommended source type
- existing source mapping, when known

Use `workspace scan --write-state` only when you intentionally want to refresh the local scan state after reviewing the candidate set.

## Step 3: Select Files To Promote

For each pending file, decide whether it should become a canonical source page.

Skip files that are:

- generated output
- local configuration
- dependency/cache/build artifacts
- source code or scripts
- temporary notes not worth durable source treatment

If a file is already represented by a source page and only changed, update or supersede the source page only when the user wants changed source content reflected in the wiki. Do not silently overwrite an existing source body.

## Step 4: Create Canonical Source Pages

For each selected file:

1. Read the workspace file in place.
2. Infer conservative metadata.
3. Create a source page in the wiki with `_system/scripts/create-page.py`.
4. Set `originPath` to the workspace-relative path of the original file.
5. Do not move or modify the original workspace file.

For a normal text or Markdown source, from the wiki root:

```bash
python3 _system/scripts/create-page.py \
  --type source \
  --subtype <sourceType> \
  --slug <sourceSlug> \
  --title "<title>" \
  --source-date <yyyy-mm-dd> \
  --retrieved-at <yyyy-mm-dd> \
  --origin-path "<workspace-relative-path>" \
  --source-role whole \
  --body-file "<absolute-or-relative-workspace-file>" \
  --no-log
```

For large files, use the same parent/source-part pattern as `process-inbox`, but `originPath` remains the workspace-relative path and there is no `raw/` retained-file move.

## Step 5: Update Workspace State

After successful promotion, record the mapping from workspace file to source page:

```bash
agent-wiki workspace mark-sourced \
  --workspace-root . \
  --path "<workspace-relative-path>" \
  --source-id "<sourceId>" \
  --source-path "sources/<source-file>.md"
```

If the console script is not installed yet, use `python3 -m agent_wiki.cli workspace mark-sourced` with the same arguments.

The command writes `wiki/_system/state/workspace-sources.json`. This state file is local generated state and should not be treated as canonical knowledge.

## Step 6: Continue The Existing Pipeline

After source pages exist:

1. Run `extract-knowledge-primitives` to process `status: unprocessed` source pages.
2. Run `compile-wiki` to regenerate caches, indexes, reports, and root catalog.

## Important Rules

- Workspace mode has no raw-file lifecycle.
- Do not move files to `raw/`.
- Do not use `_inbox/` for workspace discovery unless the user explicitly placed files there.
- Do not treat discovered workspace files as evidence until a canonical source page exists.
- Do not modify the original workspace file.
