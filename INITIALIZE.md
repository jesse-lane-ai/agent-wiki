## First-Run Initialization

Use this file when setting up a fresh checkout or when a new agent needs to orient itself before editing the vault.

1. Read [[AGENTS]] for the agent behavior contract.
2. Read [[WIKI]] for the human-facing schema guide.
3. Read [[AGENT-WIKI-SPEC-v1]] for the canonical technical specification.
4. Confirm the required folders exist: `sources/`, `entities/`, `concepts/`, `claims/`, `syntheses/`, `procedures/`, `questions/`, `reports/`, `_inbox/`, `_attachments/`, `_archive/`, `_views/`, and `_wiki/`.
5. Configure `import-note` before importing external material.
6. Run the compile pipeline and confirm it reports zero validation issues.

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

---

## Import Note Configuration

The `import-note` skill needs local setup before first use. Do not assume another user's Obsidian path, browser profile, model, or retrieval tools are valid for this checkout.

Set or confirm these values before importing:

| Setting | Required | Notes |
|---|---|---|
| `vaultRoot` | yes | Absolute path to the vault where `_inbox/`, `sources/`, and `_attachments/` should be written. For this repo, use the repository root unless the user explicitly wants an external Obsidian vault. |
| `defaultVaultName` | no | Optional display name for the target vault. |
| `retrievalMode` | yes | Choose available retrieval methods, such as direct fetch, browser capture, manual content paste, or transcript extraction. |
| `browserProfile` | no | Only needed if browser fallback is available in the user's environment. |
| `youtubeTranscriptTool` | no | Only set if `yt-dlp` or another transcript tool is installed. |
| `attachmentPolicy` | yes | Decide whether imported images/files are copied into `_attachments/` or linked externally. |

If any required value is unknown, the agent should ask the user before running `import-note`.

The inbox pointer lifecycle uses uppercase statuses: `UNPROCESSED`, `PROCESSING`, `PROCESSED`, `FAILED`, `IGNORED`, and `TRASHED`.

Source pages use the source status vocabulary from [[AGENT-WIKI-SPEC-v1]]: `unprocessed`, `processed`, and `archived`.

---

## Recommended v1 Implementation Sequence

1. Create vault skeleton
2. Add universal frontmatter handling
3. Add page-type-specific validation
4. Implement claim extraction
5. Implement evidence normalization
6. Implement relation extraction
7. Emit `pages.json`
8. Emit `claims.jsonl`
9. Emit `relations.jsonl`
10. Emit `agent-digest.json`
11. Generate required reports
12. Add contradiction/question caches

---

## Out of Scope for v1

The following are out of scope for strict v1 compliance:

- automatic ontology learning from prose
- autonomous contradiction resolution
- semantic entity merge without explicit operator decision
- probabilistic graph inference beyond explicit claims/relations
- full schema migration framework
- embedded vector index format standardization
- multi-vault federation protocol

---

## Philosophy

The v1 model has three layers:

- The vault is the container: markdown pages, folders, human notes, and generated blocks.
- The ontology is the truth model: entities, concepts, sources, claims, evidence, relations, contradictions, questions, syntheses, and procedures.
- The compile layer is the bridge: stable machine-facing cache files and generated maintenance reports.

The wiki should separate what exists, what is claimed, what supports it, what conflicts with it, what is unknown, how things connect, and how agents consume it.
