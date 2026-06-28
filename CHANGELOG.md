# Changelog

## v2.0.0 - 2026-06-28

### Added

- Rewrote the installable Agent Wiki CLI as an npm/TypeScript package.
- Added npm CLI commands for lifecycle, page scaffolding, onboarding, compile, index rendering, logging, workspace discovery, reference migration, UUID generation, and v1 migration.
- Added `agent-wiki migrate --from v1 --check|--write` to help existing Python-era checkouts upgrade to the v2 layout.
- Added package install dogfood coverage, compile parity coverage, and fresh real-source verification for vault and workspace modes.

### Changed

- `agent-wiki init --with-template` now copies docs, package metadata, config example, and root-level skills without copying Python helper scripts.
- Skill docs and root docs now call npm CLI commands instead of Python helper scripts.
- `INBOX.md` is now a short pointer; durable inbox lifecycle rules live in `WIKI.md`, and operational steps live in `skills/process-inbox/SKILL.md`.

### Removed

- Removed the Python package entrypoint (`agent_wiki/`) and `pyproject.toml`.
- Removed Python helper scripts under `_system/scripts/`, `skills/compile-wiki/scripts/compile.py`, and `skills/import-link/scripts/uuid.py`.

### Compatibility

- This is a breaking distribution/runtime change for Python-era installations.
- Existing canonical wiki content pages are expected to remain compatible. Run `agent-wiki migrate --from v1 --check` before applying the v2 migration.

## v1.4.2 - 2026-06-10

### Added

- Added a migration script for converting existing soft reference fields to Obsidian wikilinks.

### Changed

- Updated page creation so `sourcePages`, `derivedClaims`, `relatedPages`, `relatedClaims`, and local-source `originPath` values are written as aliased wikilinks that target the actual filename stem or raw file path.
- Expanded the migration script to convert extracted primitive lists (`extractedEntities`, `extractedConcepts`, `extractedClaims`, `extractedQuestions`) and `originPath`.
- Clarified which frontmatter reference fields should be wikilinked and which compiler-resolved raw ID fields must stay bare.

### Compatibility

- Backward-compatible with existing v1 vaults.
- Existing vaults can run `agent-wiki migrate-refs-to-links --write` to convert soft reference fields.

## v1.4.1 - 2026-05-28

### Changed

- Cleaned up the root files in the repository.

### Compatibility

- Backward-compatible with existing v1 vaults.
- No migration required.

## v1.4.0 - 2026-05-27

### Added

- Added optional `knownVaults` local configuration support for resolving `obsidian://` cross-vault references.
- Documented cross-vault Obsidian link behavior across the specification, root documentation, and skill instructions.
- Exposed configured known vault names and counts in the onboarding probe output.

### Changed

- Clarified that cross-vault references are read-only resolution aids, not alternate wiki roots or write targets.
- Updated the local configuration template to include the optional `knownVaults` field.

### Compatibility

- Backward-compatible with existing v1 vaults.
- No required migration for existing vaults.
- Existing users can update configuration templates, onboarding scripts, skill instructions, and root documentation to pick up the new cross-vault behavior.
