## `_inbox/` Raw Intake

The `_inbox/` folder is the active drop zone for raw files that still need to be promoted into canonical `source` pages.

**Use the process-inbox skill to process the inbox.**
`_system/skills/process-inbox/SKILL.md`

If inbox files are binary or non-markdown documents and local converter availability is unknown, run the read-only onboarding probe before processing:

```bash
python3 _system/scripts/onboard.py --check
```

Use the probe output to choose a local conversion policy with the user. If the user approves persisting local policy, write `_system/config.json` through the onboarding config writer:

```bash
python3 _system/scripts/onboard.py --write-config --python-command python3 --conversion disabled
```

Do not install packages, create `.venv/`, hand-edit `_system/config.json`, or call network/OCR/LLM/cloud conversion services unless the user explicitly approves that setup.

Process `_inbox/`, write source pages, and move retained raw files relative to the repository root. This project does not route inbox processing to another vault or wiki.

`process-inbox` should use `_system/scripts/create-page.py` to write canonical source pages and source part pages after it has prepared the source body, metadata, retained raw path, and any conversion provenance. The scaffolder validates source frontmatter and paths; it does not convert files, move raw files, choose split points, or decide what metadata means.

### Folder meaning

- `_inbox/` = active raw file queue
- `raw/` = retained original raw files after successful promotion
- `_inbox/trash/` = rejected, discarded, or inactive inbox items

### Intake lifecycle

1. A user or tool drops a raw file into `_inbox/`.
2. `process-inbox` reads the raw file.
3. If retained, `process-inbox` uses `_system/scripts/create-page.py` to create a canonical source page in `sources/` with `status: unprocessed`.
4. If the retained file is large, `process-inbox` uses `_system/scripts/create-page.py` to create a short parent source page in `sources/` and source part pages in `sources/parts/` instead of one giant markdown file.
5. After successful promotion, `process-inbox` moves the original raw file to `raw/`.
6. If a raw file cannot be processed or should be discarded, leave it in `_inbox/` for operator review or move it to `_inbox/trash/` when explicitly discarded.

### Source status

Newly promoted source pages use the source status vocabulary from [[WIKI#5 Status vocabularies]]:

- `unprocessed` = captured as a source page, not yet extracted into knowledge primitives
- `partitioned` = parent source has child source parts that still need extraction
- `processed` = extraction completed
- `archived` = retained but inactive

### Large raw files

Large documents, long transcripts, and other oversized raw files should not be promoted into one huge source body.

Use this shape:

- parent source page: `sources/<yyyy-mm-dd>-<sourceType>-<sourceSlug>.md`
- source part pages: `sources/parts/<yyyy-mm-dd>-<sourceType>-<sourceSlug>-part<nnn>.md`
- retained original: `raw/<yyyy-mm-dd>-<sourceSlug>-original<extension>`

The parent source is the document-level record and manifest. Its body should stay short. Source parts contain the verbatim extracted text for bounded segments and should include stable locators such as page ranges, headings, timestamps, or slide ranges.

Extraction should process source part pages, not the parent source page.

### Boundaries

- `_inbox/` files are not canonical `source` pages.
- `raw/` files are retained originals, not canonical `source` pages.
- Agents MUST NOT treat `_inbox/` or `raw/` files as evidence for claims.
- Canonical source material lives in `sources/`.
- Large-source verbatim text lives in `sources/parts/`.
- Pointer files are not part of the v1.3 intake workflow.
