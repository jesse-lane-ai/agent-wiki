## First-Run Onboarding

Use this file when setting up a fresh checkout or when a new agent needs to orient itself before editing the vault.

1. Read [[AGENTS]] for the agent behavior contract.
2. Read [[WIKI#4.1 Common runtime schemas]] for the runtime schema and examples; [[WIKI#5 Status vocabularies]] for status enums; [[WIKI#3 Page types]] for page types.
3. Read [[AGENT-WIKI-SPEC-v1]] only when changing project behavior, resolving ambiguity, or when [[WIKI#4.1 Common runtime schemas]] is insufficient.
4. Run the read-only onboarding probe.
5. Ask compact multiple-choice setup questions based on the probe output before writing config, creating folders, creating a virtual environment, or installing packages.
6. Configure local `_system/config.json` from `_system/config.example.json` if local tool policy or conversion backend preferences are needed.
7. Configure `_system/skills/import-link/config.json` before importing external material.
8. Create any missing runtime or content folders required for the task. The compile pipeline creates `_system/cache/`, `_system/indexes/`, `_system/logs/`, `reports/`, and regenerates root `index.md`; operational logging uses `_system/scripts/log.py`; import workflows create `_inbox/`, `_inbox/trash/`, `raw/`, `sources/`, `sources/parts/`, and `_attachments/`.
9. Run the compile pipeline and confirm it reports zero validation issues.
10. Optionally run the `update-overview` skill when the vault needs a human-facing root `overview.md` landing page.

Run the onboarding probe from the vault root:

```bash
python3 _system/scripts/onboard.py --check
```

The probe is read-only. It reports local Python commands, `.venv/` status, `_system/config.json`, `_system/config.example.json`, import-link configuration, required folders, converter command availability, and importable Python converter packages. It does not install packages, create folders, write config, or mutate vault content.

To generate user-friendly setup prompts, run:

```bash
python3 _system/scripts/onboard.py --check --questions
```

Use those prompts when asking the user for setup decisions. The user should be able to reply with compact letter choices such as `1A 2B 3A 4C 5A`. Do not ask long open-ended setup questions unless the user needs to provide a specific path or command.

If the probe cannot run, check Python manually:

```bash
python3 --version
python --version
```

Use whichever command resolves to Python 3.8 or newer. If neither command is available, warn the user that Python 3 must be installed and available on the agent's path before running the vault scripts. If only `python` works, substitute `python` anywhere this repo shows `python3`.

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

---

## Local System Configuration

`_system/config.json` is optional local operational configuration for tool policy and command preferences. It is not canonical vault knowledge, should not contain secrets, and should not be committed. `_system/config.example.json` is the tracked example shape.

Use it when the user wants persistent local preferences such as:

- which Python command to use
- whether inbox conversion is enabled
- automatic conversion backend order
- backend command names
- whether network, OCR, LLM, transcription, or hosted document-intelligence behavior is allowed

Do not write `_system/config.json` until the user has approved the setup choices. Missing config means tools should use conservative local-only defaults. When a local config is needed, use the onboarding config writer so only approved local policy fields are persisted:

```bash
python3 _system/scripts/onboard.py --write-config --python-command python3 --conversion disabled
```

Use `--conversion available-local` only when the user wants inbox conversion enabled with already installed local backends. Use explicit flags such as `--allow-ocr` only when the user has approved that behavior.

---

## Optional Virtual Environment

The compile pipeline does not need third-party Python packages. Optional inbox conversion backends may need Python packages.

If optional packages are installed, prefer a project-local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install markitdown pymupdf4llm
```

Agents must not create `.venv/` or install packages unless the user explicitly asks. If Python or optional packages are missing, warn the user and explain what is needed.

---

## Import Link Configuration

The `import-link` skill needs local setup before first use. Do not assume another user's Obsidian path, browser profile, model, or retrieval tools are valid for this checkout.

Edit `_system/skills/import-link/config.json` before importing. The checked-in file is intentionally not configured for a specific user.

Required first-run edits:

1. Set `configured` to `true`.
2. Set `vaultRoot` to the absolute path where `sources/` and `_attachments/` should be written. For this repo, use the repository root unless the user explicitly wants an external Obsidian vault.
3. Confirm `retrievalModes`.
4. Confirm `attachmentPolicy`.

Default config:

```json
{
  "schemaVersion": 1,
  "configured": false,
  "vaultRoot": null,
  "defaultVaultName": null,
  "retrievalModes": ["manual_paste"],
  "browserProfile": null,
  "youtubeTranscriptTool": null,
  "attachmentPolicy": "copy",
  "sourceDirectory": "sources",
  "attachmentDirectory": "_attachments"
}
```

Config fields:

| Setting | Required | Notes |
|---|---|---|
| `configured` | yes | Must be `true` before import. Leave `false` in shared starter repos. |
| `vaultRoot` | yes | Absolute path to the vault where `sources/` and `_attachments/` should be written. For this repo, use the repository root unless the user explicitly wants an external Obsidian vault. |
| `defaultVaultName` | no | Optional display name for the target vault. |
| `retrievalModes` | yes | Ordered list of available retrieval methods. Use `manual_paste` for no-tool setup. Other values may include `direct_fetch`, `browser_capture`, or `transcript`. |
| `browserProfile` | no | Only needed if browser fallback is available in the user's environment. |
| `youtubeTranscriptTool` | no | Only set if `yt-dlp` or another transcript tool is installed. |
| `attachmentPolicy` | yes | Use `copy` to save imported images/files into `_attachments/`, or `external_link` to leave them remote. |
| `sourceDirectory` | yes | Relative source directory, normally `sources`. |
| `attachmentDirectory` | yes | Relative attachment directory, normally `_attachments`. |

If any required value is unknown, the agent should ask the user before running `import-link`.

The `_inbox/` workflow is handled by [[INBOX]] and the `process-inbox` skill. Raw files dropped into `_inbox/` are promoted into canonical source pages and then moved to `raw/`.

For binary or non-markdown inbox files, `process-inbox` may use configured local conversion backends. Run `_system/scripts/onboard.py --check` first when converter availability is unknown, then ask the user which conversion policy to use before running `_system/scripts/onboard.py --write-config` or installing anything.

Large raw files should be promoted as a short parent source page plus source part pages under `sources/parts/`, not as one giant markdown file.

Source pages use the source status vocabulary from [[WIKI#5 Status vocabularies]]: `unprocessed`, `partitioned`, `processed`, and `archived`.

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
11. Regenerate root `index.md`
12. Generate required reports
13. Add contradiction/question caches
14. Add or refresh root `overview.md` when the vault needs a human-facing landing page

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

- The vault is the container: markdown pages, folders, human notes, and generated artifacts.
- The ontology is the truth model: entities, concepts, sources, claims, evidence, relations, contradictions, questions, and syntheses.
- The compile layer is the bridge: stable machine-facing cache files, the deterministic root page catalog, and generated maintenance reports.
- The overview layer is the human landing page: durable prose that orients readers without replacing canonical evidence or compiled data.

The wiki should separate what exists, what is claimed, what supports it, what conflicts with it, what is unknown, how things connect, and how agents consume it.
