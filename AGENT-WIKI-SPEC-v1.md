
# Agentic Wiki v1 Specification

Version: 1.2
Last Updated: 2026-04-30

---

## 1. Purpose

This specification defines the **v1 format, rules, and runtime expectations** for an ai agent compatible wiki vault.

The goal of the system is to make the wiki useful for both:

- **humans**, who need readable pages, durable notes, summaries, and workflows
- **agents**, who need stable structure, normalized records, explicit claims, and machine-facing cache artifacts

This spec merges two requirements:

1. a **knowledge ontology** that distinguishes entities, concepts, sources, claims, evidence, relationships, contradictions, and questions
2. a **practical vault architecture** that works as a markdown-first knowledge system with compile-time normalization

This document defines the v1 contract for:

- folder layout
- page types
- frontmatter fields
- structured claims and evidence
- relationship representation
- compile output files
- dashboard generation
- freshness and health rules
- minimum validation rules

---

## 2. Design Principles

The wiki must separate:

- **things** from **ideas**
- **claims** from **evidence**
- **sources** from **summaries**
- **facts** from **interpretations**
- **confidence** from **certainty theater**
- **human-edited content** from **compiled/generated artifacts**
- **page structure** from **compiled machine caches**

The wiki is intended to act as:

- a human-readable knowledge base
- a belief-tracking layer
- an agent-friendly context substrate
- a source-traceable research system
- a maintenance surface for contradictions, stale content, and open questions

---

## 3. Normative Language

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as requirement levels.

- **MUST**: required for v1 compliance
- **SHOULD**: strongly recommended unless there is a justified reason not to
- **MAY**: optional

---

## 4. Scope of v1

v1 is intentionally constrained.

v1 includes:

- page typing
- structured claims
- structured evidence
- aliases
- relations
- generated reports
- machine-facing compile outputs

v1 does **not** require:

- a dedicated top-level timeline folder
- full contradiction pages as primary authoring surfaces
- a separate metrics/state object system
- automatic semantic deduplication
- ontology inference beyond explicit page metadata and claims

Those can be added in v2.

---

## 5. Knowledge Model

The system recognizes the following knowledge object types.

### 5.1 Primary object types

#### Entity
A durable thing in the world or system.

Examples:
- person
- organization
- project
- product
- system
- place
- event
- artifact
- document-as-thing

#### Concept
An abstract idea, reusable pattern, definition, method, workflow, runbook, checklist, or operational playbook.

Examples:
- principle
- method
- workflow pattern
- theory
- policy
- standard
- abstraction
- taxonomy definition
- runbook
- checklist
- workflow
- playbook

#### Source
An origin of information.

Examples:
- PDF
- webpage
- article
- transcript
- meeting notes
- email
- dataset
- screenshot
- raw imported file
- source bridge page

#### Claim
A statement that can be evaluated for support, confidence, freshness, and conflict.

#### Evidence
A bounded support, challenge, or context record attached to a claim.

#### Relationship
A typed connection between two objects.

#### Contradiction
A tracked conflict between claims, sources, definitions, dates, or interpretations.

#### Question
An unresolved uncertainty or research gap.


### 5.2 Secondary object types

#### Synthesis
A maintained summary, overview, comparison, timeline, or analysis derived from other pages or sources.

#### Timeline Event
A dated event record represented inside an entity page, synthesis page, or compiled cache.

#### Alias
An alternate name for a page/object.

#### Metric / State
Optional quantitative or stateful information. Not a required first-class authored page type in v1.

---

## 6. Vault Layout

A v1-compliant vault MUST use the following top-level structure.

```text
<vault>/
  AGENTS.md
  WIKI.md
  index.md
  INBOX.md

  sources/
  entities/
  concepts/
  claims/
  syntheses/
  questions/
  reports/

  _attachments/
  _archive/

  _wiki/
    cache/
    indexes/
    logs/
    skills/
```

Fresh template repositories MAY omit empty runtime/content directories. Initialization tooling and workflows SHOULD create missing directories when they are needed.

### 6.1 Required top-level files

#### `AGENTS.md`
MUST describe how agents are expected to behave in the vault.

Typical contents:
- editing conventions
- generated artifact rules
- compile expectations
- page ownership expectations
- naming conventions
- what agents may or may not rewrite

#### `WIKI.md`
MUST describe the wiki schema and editorial rules in human-readable form.

Typical contents:
- folder meanings
- page types
- claim/evidence rules
- confidence meanings
- status vocabularies
- report meanings

#### `index.md`
SHOULD be the human-facing landing page.

#### `INBOX.md`
MAY be used as an intake or triage surface for new notes, unresolved imports, and uncategorized material. Documents the `_inbox/` folder pointer schema — the intake queue for raw items that have not yet been processed into canonical `source` pages.

### 6.1.1 Optional top-level files

#### `log.md`
MAY be used as a human-readable operational changelog for meaningful vault changes. It is not a source of canonical knowledge.

### 6.2 Required directories

#### `sources/`
Stores raw material and source-backed source pages.

#### `entities/`
Stores durable thing pages.

#### `concepts/`
Stores concept pages, including workflow, runbook, checklist, and playbook concepts.

#### `claims/`
Stores standalone claim pages representing atomic propositions with dedicated evidence tracking.

#### `syntheses/`
Stores maintained rollups, analyses, comparisons, summaries, and timeline-style syntheses.

#### `questions/`
Stores open question pages.


#### `reports/`
Stores generated dashboard pages and maintenance views.

#### `_attachments/`
Stores binary assets and attachments referenced by source pages or other pages (PDFs, images, raw files). Created on vault initialization; MAY be empty.

#### `_archive/`
Stores deprecated or no-longer-maintained pages that have been removed from active content folders. Created on vault initialization; MAY be empty.

#### `_wiki/`
Stores machine-generated runtime and compile artifacts, and the `skills/` directory for agent skill definitions.

Sub-directories:
- `cache/` — compiled artifact outputs (do not hand-edit)
- `indexes/` — generated index files (do not hand-edit)
- `logs/` — compile run logs (do not hand-edit)
- `skills/` — agent skill definitions; human-authored and NOT treated as vault content by the compile pipeline

The compile pipeline reads from the vault and writes to `cache/`, `indexes/`, and `logs/`. The `skills/` directory is not a compile output and is not scanned for page frontmatter.

Each skill SHOULD live in its own sub-directory under `skills/`, containing at minimum an instruction file and any supporting scripts. Example layout:

```text
_wiki/skills/
  compile-wiki/
    instructions.md
    scripts/
      compile.py
  process-new-notes/
    instructions.md
```

---

## 7. Folder Semantics

### 7.1 `sources/`

`source` pages represent verbatim source material. They are created by the `import-note` skill.

A `source` page SHOULD include:
- verbatim content (text and images)
- source metadata
- attachments (images, pdfs, etc.)
- retrieval information

A page in `sources/` MUST have `pageType: source`.

### 7.2 `entities/`

An `entity` page represents a durable thing.

Typical entity kinds:
- person
- organization
- project
- product
- system
- place
- event
- artifact

A page in `entities/` MUST have `pageType: entity`.

### 7.3 `concepts/`

A `concept` page represents a definition, method, abstraction, policy, standard, workflow, runbook, checklist, or operational playbook.

A page in `concepts/` MUST have `pageType: concept`.

### 7.4 `syntheses/`

A `synthesis` page represents maintained cross-source interpretation or rollup.

Examples:
- overview
- analysis
- comparison
- brief
- timeline
- summary

A page in `syntheses/` MUST have `pageType: synthesis`.

### 7.5 `questions/`

A `question` page represents an unresolved issue.

A page in `questions/` MUST have `pageType: question`.



### 7.6 `claims/`

A `claim` page represents a standalone atomic proposition that tracks its own evidence independent of any one source.

A page in `claims/` MUST have `pageType: claim`.

### 7.7 `reports/`

A `report` page is generated and SHOULD NOT be treated as an authoritative source of truth.

A page in `reports/` MUST have `pageType: report` if it includes frontmatter.

Reports are views over compiled or source page data.

### 7.8 `index.md`

`index.md` is the human-facing landing page for the vault.

It SHOULD have `pageType: index`. It MUST NOT be typed as `report` — it is not a generated view.

The `index` page type is reserved for vault-level navigation and orientation pages. There is typically only one `index` page per vault.

---

## 8. Page Identity and Naming

Each page MUST have a stable `id`.

### 8.1 Requirements
- `id` MUST be globally unique within the vault.
  - *Note: Duplicate IDs will not self-repair. The compiler flags collisions in the console and logs the offending file paths in `_wiki/logs/`. In the compiled indexes, the last processed file with the duplicate ID will overwrite previous entries.*
- `id` SHOULD be stable over time
- `id` SHOULD NOT depend on the page filename alone
- `id` SHOULD use dotted lowercase namespace-style format
  - *Exception for Source Pages:* Source pages use the format `source.<yyyy-mm-dd>.<source-slug>` to balance semantic density with chronological sorting and collision prevention.

Examples:
- `entity.place.riverside-community-garden`
- `concept.watershed-management`
- `source.2026-04-12.urban-tree-canopy`
- `synthesis.overview.coastal-resilience`
- `question.accessibility.evacuation-routing`

#### Rationale: Dotted Namespaces vs. UUIDs

While UUIDs guarantee mathematical uniqueness without central coordination, the dotted lowercase namespace format prioritizes **semantic density** and **agent ergonomics**:
- **Context at a Glance:** Humans and agents can immediately infer what an ID points to without needing to resolve the node.
- **Token Efficiency:** Descriptive IDs like `synthesis.overview.coastal-resilience` provide rich metadata at a low token cost.
- **Collision Prevention:** Scoping IDs by `<pageType>.<namespace>.<slug>` prevents common naming collisions in a flat namespace.

### 8.2 Filenames
Filenames MAY change. IDs SHOULD remain stable.

### 8.3 Canonical names
Entities and concepts SHOULD include `canonicalName`.

### 8.4 Internal linking convention

All internal references within the vault MUST use Obsidian-style wikilinks.

```md
[[page-slug]]
[[page-slug|Display Text]]
[[page-slug#section-heading]]
```

Standard markdown links (`[text](path)`) MUST NOT be used for internal vault references. They MAY be used for external URLs only.

This convention applies to:
- page body content
- skill instruction files
- root-level docs (`AGENTS.md`, `WIKI.md`, `INBOX.md`, `CLAUDE.md`, etc.)
- `relatedPages`, `relatedClaims`, and similar string reference fields in frontmatter

Rationale: wikilinks decouple references from file system paths, survive renames, and are resolved natively by Obsidian and compatible tooling.

### 8.5 Attachment IDs

Attachments (binary assets like images, PDFs, etc.) stored in `_attachments/` do not use frontmatter IDs. Instead, their **filename** acts as their unique identifier for internal linking (e.g., via Obsidian wikilinks).

To prevent silent overwrites in the flat `_attachments/` directory, attachment IDs MUST use the following pattern:
`yyyy-mm-dd-<source-slug>-<UUID>-<index>.<ext>`

- `yyyy-mm-dd`: The date of capture.
- `<source-slug>`: The same 4-word summary as the source file.
- `<UUID>`: A unique identifier generated specifically for the attachment.
- `<index>`: An incremental index (starting at 1) for sources containing multiple attachments.

---

## 9. Required Universal Frontmatter

Every authored page except purely generated disposable report pages SHOULD include frontmatter.

Minimum universal frontmatter:

```yaml
id: entity.place.riverside-community-garden
pageType: entity
title: Riverside Community Garden
status: active
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: []
tags: []
```

### 9.1 Universal fields

#### `id`
Type: string  
Required: yes

#### `pageType`
Type: enum  
Required: yes

Allowed values:
- `source`
- `entity`
- `concept`
- `claim`
- `synthesis`
- `question`
- `report`
- `index`

#### `title`
Type: string  
Required: yes

#### `status`
Type: string  
Required: yes  
Interpretation depends partly on page type.

#### `createdAt`
Type: date (`YYYY-MM-DD`)  
Required: yes

#### `updatedAt`
Type: date (`YYYY-MM-DD`)  
Required: yes

#### `aliases`
Type: string[]  
Required: yes, but MAY be empty

#### `tags`
Type: string[]  
Required: yes, but MAY be empty

### 9.2 Recommended universal fields

```yaml
canonicalName: <Canonical Name>
owner:
summary:
sourcePages: []
relatedPages: []
confidence:
freshness:
```

These are optional in v1, but strongly recommended where applicable.

---

## 10. Page-Type Specific Frontmatter

This section defines the pure schema templates for each page type, followed by a concrete example.

### 10.1 Source pages

**Schema:**
```yaml
id: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
pageType: source
title: <title>
status: <status>
sourceType: <sourceType>
originUrl: <url>
publishedAt: <yyyy-mm-dd>
retrievedAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
createdAt: <yyyy-mm-dd>
aliases: []
tags: []
attachments: []
```

**Example:**
```yaml
id: source.2026-04-28.urban-tree-canopy
pageType: source
title: Urban Tree Canopy Assessment
status: processed
sourceType: pdf
originUrl: https://example.com/reports/urban-tree-canopy.pdf
publishedAt: 2026-04-25
retrievedAt: 2026-04-28
updatedAt: 2026-04-28
createdAt: 2026-04-28
aliases: []
tags: [urban-planning, tree-canopy]
attachments: []
```

#### `status`

Allowed values:
- `unprocessed`
- `processed`
- `archived`

#### `sourceType`

Allowed values:
- `webpage`
- `article`
- `pdf`
- `transcript`
- `email`
- `meeting-notes`
- `dataset`
- `screenshot`
- `bridge`
- `import`
- `other`

### 10.2 Entity pages

**Schema:**
```yaml
id: entity.<entityType>.<entitySlug>
pageType: entity
title: <title>
entityType: <entityType>
canonicalName: <canonicalName>
status: active
createdAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
aliases: []
tags: []
```

**Example:**
```yaml
id: entity.place.riverside-community-garden
pageType: entity
title: Riverside Community Garden
entityType: place
canonicalName: Riverside Community Garden
status: active
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: [riverside-garden]
tags: [urban-agriculture]
```

#### `entityType`
Allowed values:
- `person`
- `organization`
- `project`
- `product`
- `system`
- `place`
- `event`
- `artifact`
- `document`
- `other`

### 10.3 Concept pages

**Schema:**
```yaml
id: concept.<conceptType>.<conceptSlug>
pageType: concept
title: <title>
conceptType: <conceptType>
status: active
createdAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
aliases: []
tags: []
```

**Example:**
```yaml
id: concept.method.adaptive-reuse
pageType: concept
title: Adaptive Reuse
conceptType: method
status: active
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: [building-reuse]
tags: [architecture]
```

#### `conceptType`
Allowed values:
- `definition`
- `principle`
- `framework`
- `method`
- `policy`
- `standard`
- `pattern`
- `workflow`
- `runbook`
- `checklist`
- `playbook`
- `theory`
- `taxonomy`
- `other`

### 10.4 Synthesis pages

**Schema:**
```yaml
id: synthesis.<synthesisType>.<synthesisSlug>
pageType: synthesis
title: <title>
synthesisType: <synthesisType>
scope: <scope>
status: active
sourcePages: []
derivedClaims: []
createdAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
aliases: []
tags: []
```

**Example:**
```yaml
id: synthesis.overview.coastal-resilience
pageType: synthesis
title: Coastal Resilience Overview
synthesisType: overview
scope: coastal flood mitigation
status: active
sourcePages: ["[[source.2026-04-12.webpage.tidal-flood-map]]"]
derivedClaims: ["[[claim.descriptive.high-tide-risk]]"]
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: []
tags: [climate-resilience]
```

#### `synthesisType`
Allowed values:
- `summary`
- `overview`
- `analysis`
- `timeline`
- `brief`
- `comparison`

### 10.5 Question pages

Questions are first-class authored pages in v1.

They represent known unknowns, unresolved research tasks, or ambiguity the system should not erase.

#### Question rules

- Questions MUST have stable IDs.
- Questions MUST link related pages or claims.
- Resolved questions MUST remain in the vault with updated status, not be deleted.

**Schema:**
```yaml
id: question.<domain>.<questionSlug>
pageType: question
title: <title>
priority: <priority>
status: open
relatedClaims: []
relatedPages: []
openedAt: <yyyy-mm-dd>
createdAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
aliases: []
tags: []
```

**Example:**
```yaml
id: question.accessibility.evacuation-routing
pageType: question
title: Which evacuation routes are accessible during high-water events?
priority: high
status: open
relatedClaims: []
relatedPages: []
openedAt: 2026-04-12
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: []
tags: [emergency-planning]
```

#### `priority`
Allowed values:
- `low`
- `medium`
- `high`
- `critical`

#### `status`
Allowed values for question pages:
- `open`
- `researching`
- `blocked`
- `resolved`
- `dropped`

### 10.7 Claim pages

See also: Section 11. Structured Claims.

**Schema:**
```yaml
id: claim.<claimType>.<claimSlug>
pageType: claim
title: <title>
claimType: <claimType>
status: <status>
confidence: <float>
text: <text>
subjectPageId: <page-id>
sourceIds: []
evidence: []
createdAt: <yyyy-mm-dd>
updatedAt: <yyyy-mm-dd>
aliases: []
tags: []
```

**Example:**
```yaml
id: claim.historical.library-reopened-2024
pageType: claim
title: Northside Library reopened in 2024
claimType: historical
status: supported
confidence: 0.90
text: Northside Library reopened to the public in 2024 after seismic upgrades were completed.
subjectPageId: entity.place.northside-library
sourceIds:
  - source.2026-04-12.library-renovation-notice
evidence: []
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: []
tags: []
```

---

## 11. Structured Claims

Claims are a primary **pagetype** in the system. They are authored as top-level, standalone files in the `claims/` directory. 

For v1, Standalone Claim Pages are the normative shape. However, pages MAY also contain zero or more embedded claims in their frontmatter under the `claims:` key for convenience. Both formats are parsed identically by the compile pipeline.

### 11.1 Claim shape

**Schema:**
```yaml
claims:
  - id: claim.<claimType>.<claimSlug>
    text: <text>
    status: <status>
    confidence: <float>
    claimType: <claimType>
    relatedClaimIds: []
    evidence:
      - id: <evidenceId>
        sourceId: <sourceId>
        path: <sourcePath>
        lines: <lineRange>
        kind: <kind>
        relation: <relation>
        weight: <float>
        note: <note>
        excerpt: <text>
        retrievedAt: <yyyy-mm-dd>
        updatedAt: <yyyy-mm-dd>
    createdAt: <yyyy-mm-dd>
    updatedAt: <yyyy-mm-dd>
    validFrom: <yyyy-mm-dd>
    validTo: <yyyy-mm-dd>
```

**Example:**
```yaml
claims:
  - id: claim.descriptive.school-energy-retrofit
    text: The Lincoln Middle School heat-pump retrofit reduced annual building energy use by 18 percent.
    status: supported
    confidence: 0.91
    claimType: descriptive
    relatedClaimIds: []
    evidence:
      - id: evidence.quote.supports.a1b2c3d4
        sourceId: source.2026-04-12.webpage.school-energy-audit
        path: sources/2026-04-12.webpage.school-energy-audit.md
        lines: 55-79
        kind: quote
        relation: supports
        weight: 0.86
        note: The audit compares normalized energy use before and after the retrofit.
        excerpt: "Weather-normalized annual energy consumption fell by 18 percent after commissioning."
        retrievedAt: 2026-04-12
        updatedAt: 2026-04-12
    createdAt: 2026-04-12
    updatedAt: 2026-04-12
    validFrom: 2026-04-12
    validTo:
```

### 11.2 Required claim fields

#### `id`
Type: string  
Required: yes  
Must be globally unique.

#### `text`
Type: string  
Required: yes

#### `status`
Type: enum  
Required: yes

Allowed values:
- `supported`
- `weakly_supported`
- `inferred`
- `unverified`
- `contested`
- `contradicted`
- `deprecated`

#### `confidence`
Type: number  
Required: yes  
Range: `0.0` to `1.0`

#### `claimType`
Type: enum  
Required: yes

Allowed values:
- `descriptive`
- `historical`
- `causal`
- `interpretive`
- `normative`
- `forecast`

#### `evidence`
Type: array  
Required: yes, but MAY be empty in draft states

#### `createdAt`
Type: date  
Required: yes

#### `updatedAt`
Type: date  
Required: yes

### 11.3 Optional claim fields

- `relatedClaimIds: string[]`
- `validFrom: date | null`
- `validTo: date | null`
- `tags: string[]`
- `note: string`

### 11.4 Claim rules

- Claim IDs MUST be stable.
- Claim IDs MUST be unique across the vault.
- Claims SHOULD be atomic and not overloaded.
- A claim SHOULD express one proposition, not several glued together.
- A claim MAY be attached to entity, concept, source, synthesis, or question pages when appropriate.
- Pages SHOULD NOT hide all important assertions in prose if those assertions matter for machine use.

---

## 12. Evidence

Evidence entries attach provenance and support semantics to a claim.

### 12.1 Evidence shape

**Schema:**
```yaml
evidence:
  - id: evidence.<kind>.<relation>.<uuid>
    sourceId: <source-id>
    path: <source-path>
    lines: <line-range>
    kind: <kind>
    relation: <relation>
    weight: <float>
    note: <note>
    excerpt: <text>
    retrievedAt: <yyyy-mm-dd>
    updatedAt: <yyyy-mm-dd>
```

**Example:**
```yaml
evidence:
  - id: evidence.quote.supports.a1b2c3d4
    sourceId: source.2026-04-28.article.urban-tree-canopy
    path: sources/2026-04-28.article.urban-tree-canopy.md
    lines: 10-18
    kind: quote
    relation: supports
    weight: 0.82
    note: Direct statement from the canopy assessment
    excerpt: "..."
    retrievedAt: 2026-04-12
    updatedAt: 2026-04-12
```

### 12.2 Required evidence fields

#### `id`
Type: string  
Required: yes

#### `sourceId`
Type: string  
Required: yes  
Must reference an existing source page ID when possible.

#### `path`
Type: string  
Required: yes  
Path to the supporting page or source page.

#### `kind`
Type: enum  
Required: yes

Allowed values:
- `quote`
- `summary`
- `measurement`
- `observation`
- `screenshot`
- `transcript`
- `inference`

#### `relation`
Type: enum  
Required: yes

Allowed values:
- `supports`
- `weakens`
- `contradicts`
- `context_only`

#### `weight`
Type: number  
Required: yes  
Range: `0.0` to `1.0`

#### `updatedAt`
Type: date  
Required: yes

### 12.3 Optional evidence fields

- `lines: string`
- `note: string`
- `excerpt: string`
- `retrievedAt: date`
- `locatorText: string`

### 12.4 Evidence rules

- Evidence MUST not imply stronger support than it actually provides.
- `context_only` evidence MUST NOT be treated as direct support during compile scoring.
- Evidence SHOULD point back to a source page, not only to a synthesis page, whenever possible.
- Claims SHOULD have at least one evidence item to avoid appearing in evidence-gap reports.
- Evidence entries MAY represent negative evidence using `weakens` or `contradicts`.

---

## 13. Relationships

Relationships are explicit machine-readable edges between objects.

Relationships MAY be authored in page frontmatter under `relations:`.

### 13.1 Relationship shape

**Schema:**
```yaml
relations:
  - subject: <subject-id>
    predicate: <predicate>
    object: <object-id>
    confidence: <float>
    sourceClaimIds: []
```

**Example:**
```yaml
relations:
  - subject: entity.place.lincoln-middle-school
    predicate: uses
    object: entity.system.ground-source-heat-pump
    confidence: 0.88
    sourceClaimIds: ["[[claim.descriptive.school-energy-retrofit]]"]
```

### 13.2 Required relationship fields

#### `subject`
Type: string  
Required: yes

#### `predicate`
Type: enum/string  
Required: yes

#### `object`
Type: string  
Required: yes

#### `confidence`
Type: number  
Required: yes  
Range: `0.0` to `1.0`

### 13.3 Optional relationship fields

- `sourceClaimIds: string[]`
- `note: string`
- `updatedAt: date`

### 13.4 Recommended predicates

v1 SHOULD use a controlled predicate set:

- `is_a`
- `part_of`
- `depends_on`
- `uses`
- `produces`
- `founded_by`
- `owned_by`
- `located_in`
- `related_to`
- `supports`
- `contradicts`
- `mentions`
- `applies_to`
- `derived_from`

### 13.5 Relationship rules

- Relationship IDs are optional in v1, but compiled output MAY assign normalized IDs.
- Relationships SHOULD be grounded by source claims where possible.
- Freeform predicates SHOULD be avoided in v1.

---

## 14. Contradictions

v1 tracks contradictions primarily through compiled outputs and reports.

Contradictions MAY also be represented in page content.

v1 does not require contradiction pages, but the compiler MUST be able to surface contradiction records.

### 14.1 Compiled contradiction shape

**Schema:**
```yaml
id: contradiction.<contradictionType>.<contradictionSlug>
type: <type>
status: <status>
summary: <summary>
claimIds: []
sourceIds: []
resolution: <resolution>
updatedAt: <yyyy-mm-dd>
```

**Example:**
```yaml
id: contradiction.interpretation-conflict.ferry-ridership
type: interpretation_conflict
status: open
summary: Two claims disagree on whether weekend ferry ridership has recovered to pre-closure levels.
claimIds:
  - claim.descriptive.ferry-ridership-recovered
  - claim.descriptive.ferry-ridership-still-depressed
sourceIds:
  - source.2026-04-20.ferry-ridership-dashboard
resolution:
updatedAt: 2026-04-29
```

### 14.2 Required fields

- `id`
- `type`
- `status`
- `summary`
- `claimIds`
- `updatedAt`

### 14.3 Allowed contradiction types

- `direct-conflict`
- `date-conflict`
- `scope-conflict`
- `definition-conflict`
- `interpretation-conflict`

### 14.4 Allowed contradiction status values

- `open`
- `under-review`
- `resolved`
- `dismissed`

### 14.5 Detection strategy

**Explicit detection (compiled from flags):**
- Claims with `status: contradicted`
- Evidence entries with `relation: contradicts`

**Semantic conflict detection (cross-claim analysis):**

The compiler SHOULD also detect implicit conflicts by comparing claims that share the same `subjectPageId`.

- **Date conflict** (`type: date-conflict`): Two or more `claimType: historical` claims on the same subject that have different `date` field values and are both in an active (non-deprecated, non-contradicted) status.
- **Scope conflict** (`type: scope-conflict`): Claims with `status: contested` coexisting with claims of `status: supported` or `weakly-supported` on the same subject, indicating active unresolved disagreement.

Semantic contradiction detection operates on structured fields only. It does not perform natural-language text comparison.

---

## 15. Timelines

Timelines represent dated events and temporal changes tied to pages in the wiki. They exist to support chronology, historical tracking, date-based retrieval, and temporal conflict detection.

Timeline data does not require a top-level `timelines/` folder in v1. It is represented through page-level `timeline:` records, synthesis pages with `synthesisType: timeline`, and compiled timeline cache output.
### 15.1 Structure

Timeline entries MUST be represented under a `timeline:` field.

**Schema:**

```yaml
timeline:
  - id: tl.<slug>.<index>
    date: <yyyy-mm-dd>
    endDate: <yyyy-mm-dd>
    text: <text>
    eventType: <eventType>
    status: <status>
    confidence: <float>
    relatedClaims: []
    sourceIds: []
    updatedAt: <yyyy-mm-dd>
```

**Example:**

```yaml
timeline:
  - id: tl.riverside-garden.001
    date: 2026-04-12
    endDate:
    text: Riverside Community Garden opened its spring seedling exchange.
    eventType: community-event
    status: supported
    confidence: 0.90
    relatedClaims:
      - "[[claim.historical.seedling-exchange-opened]]"
    sourceIds:
      - source.2026-04-12.webpage.garden-newsletter
    updatedAt: 2026-04-12
```

### 15.2 Required and Optional Fields

**Required fields:**
- `id`
- `date`
- `text`

**Optional fields:**
- `endDate`
- `eventType`
- `status`
- `confidence`
- `relatedClaims`
- `sourceIds`
- `relatedPages`
- `note`
- `createdAt`
- `updatedAt`

### 15.3 Placement and Semantics

Timeline entries MAY appear on any authored page type when that page is the natural owner of the event, including entity, concept, source, synthesis, and question pages.

A timeline entry SHALL be authored on the page that most naturally owns the event. It SHOULD reference related claims and source IDs when the event matters for reasoning, retrieval, or contradiction analysis.
  
For a single-point event, use `date`. For a bounded range, use both `date` and `endDate`.

A synthesis page that acts as a dedicated chronology SHALL use:

```yaml
pageType: synthesis
synthesisType: timeline
```

### 15.4 Compile and Validation

The compile pipeline SHOULD extract timeline entries into:

```text
_wiki/cache/timeline-events.json
```

This cache is used for chronological queries, filtering, timeline reports, and temporal conflict detection.

A v1 validator SHOULD check:
- every timeline entry has an `id`
- every timeline entry has a valid `date`
- every timeline entry has `text`
- timeline IDs are unique
- `endDate`, if present, is not earlier than `date`
- referenced claim IDs and source IDs exist when possible

The compiler SHOULD flag timeline conflicts when multiple entries appear to describe the same event but disagree on date, range, or ordering.

---

## 16. Aliases

Entities and concepts SHOULD include aliases when relevant.

**Example:**
```yaml
canonicalName: Riverside Community Garden
aliases:
  - riverside-garden
  - river-garden
```

Alias support exists to improve:
- search
- deduplication
- matching
- claim linking
- prompt grounding

---

## 17. Authoritative Sources of Truth

The system has multiple layers with different authorities.

### 17.1 Authoritative layers

Primary truth sources:
1. page frontmatter
2. authored page content where structured references exist
3. compiled caches derived from the above

### 17.2 Non-authoritative layers

These are views, not truth sources:
- `reports/`
- `log.md`
- `_wiki/logs/`
- ad hoc dashboard summaries
- search indexes
- prompt supplements that do not round-trip back to pages

### 17.3 Rule
Compiled outputs SHALL reflect page truth.  
Reports SHALL reflect compiled or page truth.  
Reports SHALL NOT silently become the canonical data layer.

---

## 18. Compile Pipeline

The compile step reads the authored wiki and emits stable machine-facing artifacts.

### 18.1 Compile goals

The compile pipeline exists so agents and runtime code do not need to scrape arbitrary markdown.

It MUST:
- normalize page metadata
- extract claims
- extract evidence
- extract relations
- compute health signals
- emit stable cache files
- generate reports

### 18.2 Minimum v1 compile outputs

The following files MUST be emitted under `_wiki/cache/`:

- `agent-digest.json`
- `claims.jsonl`
- `pages.json`
- `relations.jsonl`

The following files SHOULD also be emitted:

- `contradictions.json`
- `questions.json`
- `timeline-events.json`
- `source-index.json`

### 18.3 Required cache files

#### `agent-digest.json`
Purpose:
- compact high-signal prompt supplement
- runtime context pack
- first-pass retrieval layer

This file SHOULD contain:
- key page summaries
- important claims
- notable open questions
- notable contradictions
- high-priority entity/concept summaries

#### `claims.jsonl`
Purpose:
- claim-level retrieval
- fast lookup by claim ID
- status/confidence filtering
- backlinks to owning pages

Each line SHOULD contain:
- normalized claim record
- owning page ID
- page path
- evidence summary
- freshness info if available

#### `pages.json`
Purpose:
- normalized metadata index for all pages

Each page record SHOULD include:
- `id`
- `pageType`
- `title`
- `path`
- `status`
- `updatedAt`
- `aliases`
- `tags`
- page-type-specific metadata
- counts for claims/relations/questions if available

#### `relations.jsonl`
Purpose:
- graph edge retrieval
- relationship traversal
- cheap graph context generation

Each line SHOULD contain:
- normalized subject
- predicate
- object
- page source
- source claim IDs if present
- confidence

### 18.4 Recommended cache files

#### `contradictions.json`
Conflict registry.

#### `questions.json`
Open question registry.

#### `timeline-events.json`
Chronological event index.

#### `source-index.json`
Source metadata registry.

### 18.5 Agent digest limits

The `agent-digest.json` output truncates content to keep the file compact for use as a prompt supplement. Implementations SHOULD define these as named constants so they can be tuned as vault size grows.

| Constant | Default | Description |
|---|---|---|
| `MAX_DIGEST_KEY_PAGES` | `50` | Max entity/concept pages included |
| `MAX_DIGEST_CLAIMS` | `30` | Max top supported claims included |
| `MAX_DIGEST_QUESTIONS` | `20` | Max open question pages included |
| `MAX_DIGEST_CONTRADICTIONS` | `10` | Max open contradictions included |

Implementations MUST NOT silently discard high-value pages due to truncation without surfacing the total counts in `vaultStats`. Operators SHOULD increase limits if `vaultStats` shows totals significantly exceeding the defaults.

---

## 19. Search and Indexes

The compiler MAY emit additional indexes under `_wiki/indexes/`.

Examples:
- alias index
- tag index
- page type index
- stale page index
- path-to-id index
- id-to-path index

These indexes are implementation details and not normative v1 authored data.

---

## 20. Reports

Reports are generated maintenance views.

### 20.1 Required reports

When dashboard generation is enabled, the system SHOULD generate:

- `reports/open-questions.md`
- `reports/contradictions.md`
- `reports/low-confidence.md`
- `reports/claim-health.md`
- `reports/stale-pages.md`

### 20.2 Recommended additional reports

- `reports/orphaned-claims.md`
- `reports/evidence-gaps.md`
- `reports/relationship-gaps.md`
- `reports/timeline-conflicts.md`

#### 20.3 Report rules

- Reports SHOULD be fully regenerable.
- Reports SHOULD NOT be treated as primary truth.
- Compiler-generated reports SHOULD be treated as fully replaceable generated files.
- Reports SHOULD identify the compile timestamp.

---

## 21. Logs

Logs capture operational history. They do not replace page frontmatter, structured claims, evidence, or compile caches.

### 21.1 Log locations

- `_wiki/logs/` stores generated compile and runtime logs. These files SHOULD be written by tooling and MUST NOT be hand-edited.
- `log.md`, if present, is a human-readable changelog for meaningful vault changes.

### 21.2 Log authority

Logs are non-authoritative operational records. Agents and tooling MUST NOT treat log entries as primary evidence for claims unless the relevant material is promoted into a canonical `source` page.

### 21.3 `log.md` entries

When used, `log.md` entries SHOULD be append-only and concise. Each entry SHOULD include:

- date
- actor or tool, when known
- changed area
- short reason or outcome

Trivial report/cache regeneration does not need a `log.md` entry unless it records a meaningful vault change or operational incident.

---

## 22. Health Rules

The system SHOULD compute health signals at compile time.

### 22.1 Low confidence

A claim SHOULD be considered low confidence when:
- `confidence < 0.50`
- or status is `weakly_supported`, `unverified`, or `contested`

Exact threshold MAY be configurable, but SHOULD be stable.

#### 22.2 Evidence gaps

A claim SHOULD appear in evidence-gap reporting when:
- it has zero evidence entries
- or only `context_only` evidence exists

### 22.3 Staleness

A page or claim MAY be considered stale when:
- `updatedAt` exceeds configured freshness expectations
- or linked source retrieval dates are old
- or evidence is old relative to domain expectations

v1 does not prescribe one universal stale threshold because domains vary.

#### 22.4 Contradictions

A contradiction SHOULD be surfaced when:
- two claims with overlapping scope conflict materially
- evidence relations include `contradicts`
- a claim status is `contradicted`
- multiple source-backed dates or definitions disagree

---

## 23. Freshness Model

Freshness SHOULD be tracked at multiple levels when possible.

### 23.1 Recommended fields
- page `updatedAt`
- claim `updatedAt`
- evidence `updatedAt`
- source `publishedAt`
- source `retrievedAt`

#### 23.2 Rule
A recently edited page is not automatically a fresh page.  
Compile SHOULD distinguish between recent edits and recent underlying evidence.

---

## 24. Validation Rules

A v1 validator SHOULD check the following.

### 24.1 Required validation
- every page has a valid `pageType`
- every page has a unique `id`
- required frontmatter fields are present
- claims have unique IDs
- claims have required fields
- confidence fields are numeric and in range
- evidence entries have required fields
- relation entries have required fields
- question pages use allowed status enums
- pages are stored in folders consistent with `pageType`

#### 24.2 Recommended validation
- source IDs referenced by evidence exist
- related page references exist
- claim IDs referenced by relationships exist when provided
- aliases do not duplicate canonical title unnecessarily

---

## 25. Human Editing Expectations

Humans MAY:
- add prose
- add notes and commentary
- create new pages
- update frontmatter
- add or revise claims manually
- add questions

Humans SHOULD NOT:
- directly hand-edit cache files
- treat reports as canonical data
- bypass IDs for important pages
- mix unrelated claims into one compound claim

---

## 26. Agent Editing Expectations

Agents MUST:
- preserve human-authored content unless explicitly directed otherwise
- use stable IDs when generating claims or pages
- update `updatedAt` when meaningfully changing structured content
- avoid inventing unsupported certainty
- update `log.md` when making meaningful changes to the vault, if `log.md` is present or requested by the operator

Agents SHOULD:
- create question pages for unresolved important unknowns
- attach evidence to claims where possible
- reuse canonical IDs instead of duplicating objects

Agents MUST NOT:
- silently rewrite human commentary unless explicitly directed otherwise
- delete unresolved uncertainty by omission
- convert weak evidence into strong support semantics
- treat reports as primary truth records

---

## 27. Example Minimal Entity Page

```md
---
id: entity.place.riverside-community-garden
pageType: entity
title: Riverside Community Garden
entityType: place
canonicalName: Riverside Community Garden
status: active
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases:
  - riverside-garden
tags:
  - urban-agriculture
  - community
claims:
  - id: claim.descriptive.garden-weekly-produce-donations
    text: Riverside Community Garden donates a portion of its weekly produce harvest to the neighborhood food pantry.
    status: supported
    confidence: 0.91
    claimType: descriptive
    relatedClaimIds: []
    evidence:
      - id: evidence.quote.supports.a1b2c3d4
        sourceId: source.2026-04-12.webpage.garden-newsletter
        path: sources/2026-04-12.webpage.garden-newsletter.md
        lines: 55-79
        kind: quote
        relation: supports
        weight: 0.86
        note: The newsletter describes the weekly donation arrangement.
        excerpt: "Each Friday harvest includes a pantry donation box."
        retrievedAt: 2026-04-12
        updatedAt: 2026-04-12
    createdAt: 2026-04-12
    updatedAt: 2026-04-12
relations:
  - subject: entity.place.riverside-community-garden
    predicate: supports
    object: entity.organization.neighborhood-food-pantry
    confidence: 0.88
    sourceClaimIds:
      - "[[claim.descriptive.garden-weekly-produce-donations]]"
---

# Riverside Community Garden

Riverside Community Garden is a neighborhood garden that coordinates volunteer planting, harvest tracking, and weekly produce donations.

```

---

## 28. Example Question Page

```md
---
id: question.maintenance.flood-sensor-calibration
pageType: question
title: Which flood sensors need calibration before storm season?
priority: high
status: open
relatedClaims:
  - "[[claim.descriptive.sensor-readings-drifted]]"
relatedPages:
  - "[[coastal-resilience-overview]]"
openedAt: 2026-04-12
createdAt: 2026-04-12
updatedAt: 2026-04-12
aliases: []
tags:
  - flood-monitoring
  - open-question
---

# Which flood sensors need calibration before storm season?

## Context
This question exists because several river gauge readings drifted from manual spot checks during the spring inspection.

## Current concern
We need to identify which sensors require calibration before they are used for storm-season alerting.
```

---

## 29. Compatibility Notes

v1 implementations MAY add fields beyond this spec, provided they do not break:

- required fields
- required enum values
- compile output expectations

Unknown fields MUST be preserved by conforming tooling when possible.
