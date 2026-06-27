## First-Run Onboarding

Use this file when setting up a fresh Agent Wiki or when a new agent needs to orient itself before editing one.

Start with the lifecycle CLI:

```bash
python3 -m agent_wiki.cli init --type vault --root /path/to/wiki --write-config
python3 -m agent_wiki.cli doctor --wiki-root /path/to/wiki
```

For a project workspace with an embedded wiki:

```bash
python3 -m agent_wiki.cli init --type workspace --workspace-root /path/to/project --wiki-dir wiki --write-config
python3 -m agent_wiki.cli doctor --wiki-root /path/to/project/wiki --type workspace
```

`agent-wiki init` owns folder creation and optional local config creation. `agent-wiki doctor` is the read-only lifecycle check. Use `_system/scripts/onboard.py --check` only after that, when you need a lower-level environment probe for Python, converter commands/packages, import-link config, or setup questions.

Before editing wiki content:

1. Read [[AGENTS]] for the agent behavior contract.
2. Read [[WIKI#4.1 Common runtime schemas]] for the runtime schema and examples; [[WIKI#5 Status vocabularies]] for status enums; [[WIKI#3 Page types]] for page types.
3. Read [[AGENT-WIKI-SPEC-v2]] only when changing project behavior, resolving ambiguity, or when [[WIKI#4.1 Common runtime schemas]] is insufficient.
4. Run `agent-wiki doctor` for the target wiki root.
5. Run `_system/scripts/onboard.py --check` only if local Python/converter/import-link setup is relevant.
6. Configure local `_system/config.json` only through approved setup choices.
7. Configure `_system/skills/import-link/config.json` before importing external material.
8. Run the compile pipeline and confirm it reports zero validation issues.
9. Optionally run the `write-synthesis` skill when the wiki needs a durable cross-source brief, comparison, analysis, summary, or timeline narrative.
10. Optionally run the `update-overview` skill when the wiki needs a human-facing root `overview.md` landing page.

---

## Vault Wiki Onboarding

Vault mode preserves the classic Agent Wiki layout. The wiki root is the working root. It includes the raw inbox lifecycle:

- `_inbox/` is the active drop zone.
- `_inbox/trash/` holds rejected inbox material.
- `raw/` retains original raw captures after promotion.
- `sources/` and `sources/parts/` hold canonical source pages.

Initialize a vault wiki:

```bash
python3 -m agent_wiki.cli init --type vault --root /path/to/wiki --write-config
```

Check it:

```bash
python3 -m agent_wiki.cli doctor --wiki-root /path/to/wiki --type vault
```

Use vault mode when the wiki itself is the primary repository and source material enters through `_inbox/`, `import-link`, or direct source-page creation.

---

## Workspace Wiki Onboarding

Workspace mode embeds the wiki inside an existing project. By default the wiki lives at `workspace/wiki`, and original workspace files stay where they are.

Workspace mode does not require `_inbox/`, `_inbox/trash/`, or `raw/`. Source capture is reference-based:

- `agent-wiki workspace pending` finds candidate workspace files.
- The agent reads selected workspace files in place.
- Canonical `sources/` pages cite workspace-relative `originPath` values.
- `agent-wiki workspace mark-sourced ...` records which workspace files have been captured.

Initialize a workspace wiki:

```bash
python3 -m agent_wiki.cli init --type workspace --workspace-root /path/to/project --wiki-dir wiki --write-config
```

Check it:

```bash
python3 -m agent_wiki.cli doctor --wiki-root /path/to/project/wiki --type workspace
```

Use workspace mode when Agent Wiki is documenting or synthesizing an existing project without moving or owning that project's files.

---

## Environment Probe

Run the lower-level onboarding probe from the wiki root only when environment details matter:

```bash
python3 _system/scripts/onboard.py --check
```

The probe is read-only. It reports OS/platform details, whether `.obsidian/` is present at the wiki root, local Python commands, `.venv/` status, `_system/config.json`, `_system/config.example.json`, import-link configuration, mode-specific required folders, key script availability such as `_system/scripts/create-page.py`, converter command availability, and importable Python converter packages. It does not install packages, create folders, write config, or mutate wiki content.

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

Use whichever command resolves to Python 3.8 or newer. If neither command is available, warn the user that Python 3 must be installed and available on the agent's path before running the wiki scripts. If only `python` works, substitute `python` anywhere this repo shows `python3`.

Compile from the wiki root:

```bash
python3 _system/skills/compile-wiki/scripts/compile.py
```

---

## Local System Configuration

`_system/config.json` is optional local operational configuration for wiki type, workspace mode, tool policy, and command preferences. It is not canonical wiki knowledge, should not contain secrets, and should not be committed. `_system/config.example.json` is the tracked example shape.

Use it when the user wants persistent local preferences such as:

- whether this root is a `vault` or `workspace` wiki
- workspace root and wiki directory
- which Python command to use
- whether inbox conversion is enabled
- automatic conversion backend order
- backend command names
- whether network, OCR, LLM, transcription, or hosted document-intelligence behavior is allowed
- optional `knownVaults` mappings from Obsidian vault names to absolute local paths for resolving `obsidian://` references

Prefer `agent-wiki init --write-config` for initial `wikiType` and workspace settings. Do not write `_system/config.json` until the user has approved the setup choices. Missing config means tools should use conservative local-only defaults and default to vault mode.

When local Python or conversion policy is needed, use the onboarding config writer so only approved local policy fields are persisted:

```bash
python3 _system/scripts/onboard.py --write-config --python-command python3 --conversion disabled
```

Use `--conversion available-local` only when the user wants inbox conversion enabled with already installed local backends. Use explicit flags such as `--allow-ocr` only when the user has approved that behavior.

---

## Optional Obsidian Setup

Obsidian is optional. The wiki can be used as a plain Markdown repository, and onboarding does not require an Obsidian vault to already exist.

After onboarding, if the user wants to use this wiki in Obsidian, recommend opening the wiki root as an Obsidian vault:

1. Open Obsidian.
2. Click the current vault name at the bottom of the file explorer pane, or use Obsidian's vault switcher if the control is not visible.
3. Click "Manage vaults..."
4. Click "Open folder as vault".
5. Navigate to the wiki root.
6. Click "Select Folder".

Obsidian may create a local `.obsidian/` folder. That folder is local application state and should not be committed.

For links to another Obsidian vault, use Obsidian's "Copy Obsidian URL" action and store the result as a standard markdown link using an `obsidian://` URI. Agents must not launch these URIs. They can read the target only when `_system/config.json` includes a matching `knownVaults` entry; otherwise the URI remains an opaque external reference.

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
2. Confirm `retrievalModes`.
3. Confirm `attachmentPolicy`.

Default config:

```json
{
  "schemaVersion": 1,
  "configured": false,
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
| `retrievalModes` | yes | Ordered list of available retrieval methods. Use `manual_paste` for no-tool setup. Other values may include `direct_fetch`, `browser_capture`, or `transcript`. |
| `browserProfile` | no | Only needed if browser fallback is available in the user's environment. |
| `youtubeTranscriptTool` | no | Only set if `yt-dlp` or another transcript tool is installed. |
| `attachmentPolicy` | yes | Use `copy` to save imported images/files into `_attachments/`, or `external_link` to leave them remote. |
| `sourceDirectory` | yes | Relative source directory, normally `sources`. |
| `attachmentDirectory` | yes | Relative attachment directory, normally `_attachments`. |

If any required value is unknown, the agent should ask the user before running `import-link`.

The `_inbox/` workflow is handled by [[INBOX]] and the `process-inbox` skill in vault mode. Raw files dropped into `_inbox/` are promoted into canonical source pages and then moved to `raw/`.

For binary or non-markdown inbox files, `process-inbox` may use configured local conversion backends. Run `_system/scripts/onboard.py --check` first when converter availability is unknown, then ask the user which conversion policy to use before running `_system/scripts/onboard.py --write-config` or installing anything.

Large raw files should be promoted as a short parent source page plus source part pages under `sources/parts/`, not as one giant markdown file.

Source pages use the source status vocabulary from [[WIKI#5 Status vocabularies]]: `unprocessed`, `partitioned`, `processed`, and `archived`.

---

## Recommended v2 Implementation Sequence

1. Create wiki lifecycle commands
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
14. Add or refresh root `overview.md` when the wiki needs a human-facing landing page

---

## Out of Scope for v2

The following are out of scope for strict v2 compliance:

- automatic ontology learning from prose
- autonomous contradiction resolution
- semantic entity merge without explicit operator decision
- probabilistic graph inference beyond explicit claims/relations
- full schema migration framework
- embedded vector index format standardization
- multi-vault federation protocol

---

## Philosophy

The v2 model has four layers:

- The wiki is the container: markdown pages, folders, human notes, and generated artifacts.
- The ontology is the truth model: entities, concepts, sources, claims, evidence, relations, contradictions, questions, and syntheses.
- The compile layer is the bridge: stable machine-facing cache files, the deterministic root page catalog, and generated maintenance reports.
- The overview layer is the human landing page: durable prose that orients readers without replacing canonical evidence or compiled data.

The wiki should separate what exists, what is claimed, what supports it, what conflicts with it, what is unknown, how things connect, and how agents consume it.
