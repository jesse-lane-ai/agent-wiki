# Changelog

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
