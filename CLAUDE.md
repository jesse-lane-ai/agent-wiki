# Agentics Wiki — Agent Context

This vault uses a structured knowledge schema. Before editing anything, read:

1. [[AGENTS]] — the behavioral contract (managed blocks, ID rules, what agents may/must not do)
2. [[WIKI]] — folder meanings, page types, frontmatter schema, and editorial rules

For the full v1 technical specification: [[AGENT-WIKI-SPEC-v1]]

## Key rules

- Never rewrite human content outside `<!-- AI:GENERATED START/END -->` blocks
- Use stable dotted-namespace IDs for all pages, claims, and evidence
- Update `updatedAt` when changing structured frontmatter content
- Do not treat `reports/` as canonical data — they are generated views
- Do not hand-edit files in `_wiki/cache/` or `_wiki/indexes/`

## Compile pipeline

Run after meaningful vault changes to keep caches fresh:

```bash
python _wiki/skills/compile-wiki/scripts/compile.py
```

## Inbox

New unstructured material lands in `_inbox/` as pointer files. Use the process-new-notes skill to promote items to canonical `source` pages. See [[INBOX]] for the pointer schema.
