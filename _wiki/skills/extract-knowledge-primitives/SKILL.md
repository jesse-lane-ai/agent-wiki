---
name: extract-knowledge-primitives
description: "Extract knowledge primitives (entities, concepts, claims, questions, and relations) from source pages. Use this skill when the user says 'extract primitives', 'extract knowledge', 'process sources for structured data', or 'analyze sources'. This skill reads source pages with status: unprocessed and creates appropriate wiki pages."
---

# Extract Knowledge Primitives

This skill defines the extraction workflow. It does not own the vault schema.

Canonical schema, allowed enums, ID formats, confidence semantics, and canonical examples live in `AGENT-WIKI-SPEC-v1.md`. The vault behavior contract lives in `AGENTS.md`. The quick editorial guide lives in `WIKI.md`.

If this skill conflicts with `AGENT-WIKI-SPEC-v1.md`, follow `AGENT-WIKI-SPEC-v1.md`.

## Core Principles

- Preserve source content. Add structure without rewriting human-authored prose.
- Use stable IDs. Reuse existing primitives when they already exist.
- Do not invent certainty. New source-extracted claims start `status: unverified` with `confidence: 0.60` unless the canonical spec says otherwise.
- Keep claims atomic. One proposition per claim.
- Treat evidence honestly. An excerpt can show that a source made a statement without proving the statement true.
- Use Obsidian wikilinks for internal vault references.

## Step 1: Read the Contract and Spec

Before extracting anything, read:

1. `AGENTS.md` for behavior rules.
2. `AGENT-WIKI-SPEC-v1.md` for canonical schema, field requirements, ID formats, enums, and canonical examples.
3. `WIKI.md` only as a quick editorial reference.

Do not copy schemas from this skill when creating pages. Use `AGENT-WIKI-SPEC-v1.md` as the source of truth.

## Step 2: Find Source Pages Needing Extraction

Scan `sources/` for source pages that have not yet been processed for extraction.

A source page needs extraction when:

- `status: unprocessed`.

A source page has already been extracted when:

- `status: processed`.

Read frontmatter first. Do not reprocess already extracted source pages unless the user explicitly asks for re-extraction.

If no unprocessed source pages are found, report that and stop.

## Step 3: Analyze Each Source

Read each selected source page in full and identify durable primitives worth adding to the vault.

### Entities

Extract entities when the source names durable things worth tracking across the vault:

- people
- organizations
- projects
- products
- systems
- places
- events
- artifacts
- documents

Prefer entities that are main subjects, repeated, or needed for links, claims, or relations. Do not create entities for generic nouns or passing mentions.

Example judgment:

```text
Source: "Acme Corp was founded in 2010 by John Doe."

Extract:
- entity.organization.acme-corp
- entity.person.john-doe
```

### Concepts

Extract concepts when the source defines or explains reusable abstractions or reusable instructions:

- definitions
- methods
- principles
- frameworks
- policies
- standards
- patterns
- theories
- taxonomies
- workflows
- runbooks
- checklists
- playbooks

Do not create concept pages for terms that are only mentioned in passing.

Example judgment:

```text
Source: "Adaptive reuse converts existing buildings to new uses while preserving much of the original structure."

Extract:
- concept.method.adaptive-reuse
```

### Claims

Extract claims when the source makes an atomic proposition that can be evaluated for support, confidence, freshness, and conflict.

Split compound statements:

```text
Source: "Acme Corp was founded in 2010 and is based in San Francisco."

Extract:
- Acme Corp was founded in 2010.
- Acme Corp is based in San Francisco.
```

Choose `claimType` by meaning:

- `historical`: dated or temporal event
- `descriptive`: what something is, has, or does
- `causal`: cause or mechanism
- `interpretive`: meaning, implication, or judgment
- `normative`: recommendation or what should happen
- `forecast`: expected future outcome

New source-extracted claims should normally be `unverified` with `confidence: 0.60`. The evidence excerpt documents where the claim came from; it does not automatically make the claim supported.

Extract workflow-style concepts when the source contains reusable actionable steps:

- workflows
- runbooks
- checklists
- playbooks
- setup or operating instructions

Represent these as `pageType: concept` in `concepts/`, using the canonical concept schema and an appropriate workflow-oriented `conceptType` from `AGENT-WIKI-SPEC-v1.md`. Preserve the operational sequence. Keep the body concise and source-grounded.

### Questions

Extract questions when the source exposes unresolved uncertainty:

- explicit questions
- research gaps
- known unknowns
- unresolved decisions
- TODOs or future work that should remain visible

Questions should be specific enough to answer. Resolved questions remain in the vault with an updated status; do not delete them.

### Relations

Extract relations when the source establishes a typed connection between primitives:

- type membership
- ownership or authorship
- organizational hierarchy
- dependency or usage
- production or derivation
- location
- logical support or contradiction
- general association

Use predicates from `AGENT-WIKI-SPEC-v1.md`. Relations are directional; record the direction actually supported by the source.

## Step 4: Create or Update Pages

For each primitive, check for an existing page before creating a new one. Search the relevant folder and the compiled cache when available.

Create pages in the folder required by `AGENTS.md`:

- `entities/` for `pageType: entity`
- `concepts/` for `pageType: concept`
- `claims/` for `pageType: claim`
- `questions/` for `pageType: question`

Use the canonical page schemas and examples from `AGENT-WIKI-SPEC-v1.md` Section 10, "Page-Type Specific Frontmatter". Do not use local schema templates or copied frontmatter examples.

When updating an existing page:

- preserve human-authored prose
- update only relevant structured fields
- update `updatedAt` when structured content changes
- avoid duplicate claims, evidence entries, relations, aliases, and links

## Step 5: Add Evidence

Every extracted claim should point back to the source page when possible.

Evidence should include:

- source page ID
- source path
- evidence kind
- evidence relation
- concise note
- exact excerpt when available
- retrieval/update dates required by the spec

Use `relation: supports` only when the evidence directly supports the claim. Use `context_only`, `weakens`, or `contradicts` when that is more accurate.

## Step 6: Update Source Extraction Metadata

After extracting primitives from a source page, update that source page's frontmatter using the fields defined in `AGENT-WIKI-SPEC-v1.md`.

At minimum, record:

- `status: processed`
- `updatedAt`
- IDs of extracted entities, concepts, claims, and questions where applicable

Do not modify the source body unless the user explicitly asks for prose changes.

## Step 7: Report Results

Report a concise summary:

```text
Extraction complete.

Processed:
- source.<id>

Created or updated:
- Entities: ...
- Concepts: ...
- Claims: ...
- Questions: ...
- Relations: ...
```

## Checklist

- [ ] Read `AGENTS.md` and `AGENT-WIKI-SPEC-v1.md`
- [ ] Find unprocessed source pages
- [ ] Read each selected source in full
- [ ] Identify entities, concepts, claims, questions, and relations
- [ ] Check for duplicates before creating pages
- [ ] Use canonical schemas and examples from `AGENT-WIKI-SPEC-v1.md`
- [ ] Mark source-extracted claims `unverified` with `confidence: 0.60`
- [ ] Add source-grounded evidence without overstating support
- [ ] Preserve human-authored prose
- [ ] Update source extraction metadata
- [ ] Report results

## Schema Authority

This skill owns extraction workflow guidance only. Page schemas, allowed enum values, ID formats, and canonical examples live in `AGENT-WIKI-SPEC-v1.md` Section 10, "Page-Type Specific Frontmatter".
