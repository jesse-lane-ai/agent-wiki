## `_inbox/` Raw Intake

The `_inbox/` folder is the active drop zone for raw files that still need to be promoted into canonical `source` pages.

**Use the process-inbox skill to process the inbox.**
`_wiki/skills/process-inbox/SKILL.md`

### Folder meaning

- `_inbox/` = active raw file queue
- `raw/` = retained original raw files after successful promotion
- `_inbox/trash/` = rejected, discarded, or inactive inbox items

### Intake lifecycle

1. A user or tool drops a raw file into `_inbox/`.
2. `process-inbox` reads the raw file.
3. If retained, `process-inbox` creates a canonical source page in `sources/` with `status: unprocessed`.
4. After successful promotion, `process-inbox` moves the original raw file to `raw/`.
5. If a raw file cannot be processed or should be discarded, leave it in `_inbox/` for operator review or move it to `_inbox/trash/` when explicitly discarded.

### Source status

Newly promoted source pages use the source status vocabulary from [[AGENT-WIKI-SPEC-v1]]:

- `unprocessed` = captured as a source page, not yet extracted into knowledge primitives
- `processed` = extraction completed
- `archived` = retained but inactive

### Boundaries

- `_inbox/` files are not canonical `source` pages.
- `raw/` files are retained originals, not canonical `source` pages.
- Agents MUST NOT treat `_inbox/` or `raw/` files as evidence for claims.
- Canonical source material lives in `sources/`.
- Pointer files are not part of the v1.3 intake workflow.
