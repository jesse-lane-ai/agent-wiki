---
name: extract-knowledge-primitives
description: "Extract knowledge primitives (entities, concepts, claims, questions, and relations) from source pages. Use this skill when the user says 'extract primitives', 'extract knowledge', 'process sources for structured data', or 'analyze sources'. This skill reads source pages with status: unprocessed and creates appropriate wiki pages."
---

# Extract Knowledge Primitives

This skill defines the extraction workflow. It does not own the vault schema or synthesis prose workflow.

Runtime schema and common examples live in `WIKI.md` Section 4.1. Status enums live in `WIKI.md` Sections 5 and 6. Evidence rules live in `WIKI.md` Section 7. Relationship predicates live in `WIKI.md` Section 8. Entity and concept type enums live in `WIKI.md` Section 12.1. The vault behavior contract lives in `AGENTS.md`. The full project/development contract lives in `AGENT-WIKI-SPEC-v1.md`.

Use `AGENT-WIKI-SPEC-v1.md` only when changing project behavior, resolving ambiguity, or when `WIKI.md` Sections 4.1, 5, 6, 7, 8, or 12.1 do not contain enough detail. If this skill or those `WIKI.md` sections conflict with `AGENT-WIKI-SPEC-v1.md`, follow `AGENT-WIKI-SPEC-v1.md`.

Authored body requirements for newly created `entity`, `concept`, `claim`, `question`, and `synthesis` pages live in `AGENT-WIKI-SPEC-v1.md` Section 7.10.
Deterministic page scaffolding lives in `AGENT-WIKI-SPEC-v1.md` Section 6.6. Use `_system/scripts/create-page.py` when creating new primitive page files.

## Core Principles

- Preserve source content. Add structure without rewriting human-authored prose.
- Use stable IDs. Reuse existing primitives when they already exist.
- Do not invent certainty. New source-extracted claims start `status: unverified` with `confidence: 0.60` unless the canonical spec says otherwise.
- Keep claims atomic. One proposition per claim.
- Treat evidence honestly. An excerpt can show that a source made a statement without proving the statement true.
- Use Obsidian wikilinks for internal vault references.

## Step 1: Read the Contract and Runtime Reference

Before extracting anything, read:

1. `AGENTS.md` for behavior rules.
2. `WIKI.md` Sections 4.1, 5, 6, 7, 8, and 12.1 for runtime schema, field requirements, ID formats, enums, and common examples.

Read `AGENT-WIKI-SPEC-v1.md` only when changing the project itself, resolving ambiguity, or when `WIKI.md` Sections 4.1, 5, 6, 7, 8, or 12.1 are insufficient.

Do not copy schemas from this skill when creating pages. Use `WIKI.md` Section 4.1 as the routine source of truth for ordinary vault schemas.
Use `_system/scripts/create-page.py` for new page files so IDs, filenames, required frontmatter, and body requirements stay deterministic.

## Step 2: Find Source Pages Needing Extraction

Scan `sources/` for source pages that have not yet been processed for extraction.

A source page needs extraction when:

- `status: unprocessed`.
- `sourceRole` is absent, `whole`, or `part`.

A source page has already been extracted when:

- `status: processed`.

Large source parent pages are manifests and metadata records. Do not extract primitives from pages with `sourceRole: parent`; extract from their child source part pages instead.

Read frontmatter first. Do not reprocess already extracted source pages unless the user explicitly asks for re-extraction.

If no unprocessed source pages are found, report that and stop.

## Step 3: Analyze Each Source

Read each selected source page in full and identify durable primitives worth adding to the vault.

For source parts, preserve the parent source context. Evidence should cite the source part page and include the part's `locator` when available.

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

Represent these as `pageType: concept` in `concepts/`, using the concept schema in `WIKI.md` Section 4.1 and an appropriate workflow-oriented `conceptType` from `WIKI.md` Section 12.1. Preserve the operational sequence. Keep the body concise and source-grounded.

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

Use predicates from `WIKI.md` Section 8. Relations are directional; record the direction actually supported by the source.

## Step 4: Create or Update Pages

For each primitive, check for an existing page before creating a new one. Search the relevant folder and the compiled cache when available.

Create new page files with `_system/scripts/create-page.py --no-log`. This skill writes one extraction batch log entry after all primitive creation and source metadata updates succeed.

Create pages in the folder required by `AGENTS.md`:

- `entities/` for `pageType: entity`
- `concepts/` for `pageType: concept`
- `claims/` for `pageType: claim`
- `questions/` for `pageType: question`

Use the runtime page schemas and examples from `WIKI.md` Section 4.1. Do not use local schema templates or copied frontmatter examples.

When creating a new `entity`, `concept`, `claim`, or `question` page, write a substantive Markdown body after the frontmatter. The body must be human-facing prose, not only frontmatter, a placeholder, or a one-line title restatement.

Do not create `synthesis` pages as part of routine primitive extraction. If the extraction reveals a need for durable cross-source interpretation, comparison, brief, or timeline narrative, report that a synthesis may be useful and use the `write-synthesis` skill when the operator asks for it.

Prepare the body prose in a temporary Markdown file outside the vault, then call the scaffolder. Examples:

```bash
python3 _system/scripts/create-page.py \
  --type entity \
  --subtype organization \
  --slug acme-corp \
  --title "Acme Corp" \
  --body-file <prepared-body.md> \
  --source-page <sourceId> \
  --no-log
```

```bash
python3 _system/scripts/create-page.py \
  --type concept \
  --subtype workflow \
  --slug adaptive-reuse-review \
  --title "Adaptive Reuse Review" \
  --body-file <prepared-body.md> \
  --source-page <sourceId> \
  --no-log
```

```bash
python3 _system/scripts/create-page.py \
  --type claim \
  --subtype historical \
  --slug acme-founded-2010 \
  --title "Acme Corp was founded in 2010" \
  --claim-text "Acme Corp was founded in 2010." \
  --confidence 0.60 \
  --source-id <sourceId> \
  --evidence "id=evidence.quote.supports.acme-founded-2010;sourceId=<sourceId>;path=<sourcePath>;kind=quote;relation=context_only;weight=0.60;excerpt=<short-excerpt>;updatedAt=<yyyy-mm-dd>;locatorText=<locator>" \
  --body-file <prepared-body.md> \
  --no-log
```

```bash
python3 _system/scripts/create-page.py \
  --type question \
  --subtype acquisition \
  --slug acme-founder-identity \
  --title "Who founded Acme Corp?" \
  --body-file <prepared-body.md> \
  --related-page <pageId> \
  --no-log
```

For claim pages, pass source-grounded evidence records to the scaffolder with repeatable `--evidence` flags so the page is created with block YAML evidence frontmatter. Use `relation: supports` only when the source directly supports the claim; otherwise prefer `context_only`, `weakens`, or `contradicts`.

After creating a page with the scaffolder, immediately add any extraction-specific structured fields the scaffolder does not own, such as embedded relations, extracted primitive lists, or richer source references. Preserve the body prose written by the scaffolder and update `updatedAt` when structured content changes.

Use the body to explain the primitive in source-grounded context:

- `entity` pages: describe the entity, why it matters in the vault, important aliases or identifiers, and known uncertainty.
- `concept` pages: explain the concept, its boundaries, source-grounded examples or steps, and any important distinctions.
- `claim` pages: restate the atomic proposition in prose, summarize the evidence posture, and note caveats or uncertainty.
- `question` pages: explain why the question exists, what is already known, what remains unresolved, and what would count as resolution.

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
- source locator when available, especially for source parts
- evidence kind
- evidence relation
- concise note
- exact excerpt when available
- retrieval/update dates required by the spec

Use `relation: supports` only when the evidence directly supports the claim. Use `context_only`, `weakens`, or `contradicts` when that is more accurate.

## Step 6: Update Source Extraction Metadata

After extracting primitives from a source page, update that source page's frontmatter using the fields defined in `WIKI.md` Section 4.1 and source statuses from `WIKI.md` Section 5.

At minimum, record:

- `status: processed`
- `updatedAt`
- IDs of extracted entities, concepts, claims, and questions where applicable

When processing source parts, update each processed part to `status: processed`. After all parts for a parent source are processed, update the parent source from `status: partitioned` to `status: processed` and update its `updatedAt`.

Do not modify the source body unless the user explicitly asks for prose changes.

## Step 7: Log the Extraction Batch

After successfully extracting primitives and updating source metadata, write one operational log entry for the batch:

```bash
python3 _system/scripts/log.py --message "extract-knowledge-primitives: processed <sourceCount> sources; entities=<count> concepts=<count> claims=<count> questions=<count> relations=<count>"
```

Do not write a log entry when no source pages were processed.

## Step 8: Report Results

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

- [ ] Read `AGENTS.md` and `WIKI.md` Sections 4.1, 5, 6, 7, 8, and 12.1
- [ ] Find unprocessed source pages and source parts
- [ ] Skip `sourceRole: parent` pages during extraction
- [ ] Read each selected source in full
- [ ] Identify entities, concepts, claims, questions, and relations
- [ ] Defer durable cross-source interpretation to the `write-synthesis` skill
- [ ] Check for duplicates before creating pages
- [ ] Use `_system/scripts/create-page.py --no-log` for newly created primitive page files
- [ ] Use runtime schemas and examples from `WIKI.md` Section 4.1
- [ ] Write substantive Markdown body prose for every new entity, concept, claim, and question page
- [ ] Mark source-extracted claims `unverified` with `confidence: 0.60`
- [ ] Add source-grounded evidence without overstating support
- [ ] Include source part locators in evidence when available
- [ ] Preserve human-authored prose
- [ ] Update source extraction metadata
- [ ] Write one operational log entry for the extraction batch
- [ ] Report results

## Schema Authority

This skill owns extraction workflow guidance only. Runtime page schemas, ID formats, and common examples live in `WIKI.md` Section 4.1. Allowed enum values live in `WIKI.md` Sections 5, 6, 7, 8, 12, and 12.1. Use `AGENT-WIKI-SPEC-v1.md` only for project changes, ambiguity, or missing detail.
