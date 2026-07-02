# WIKI.md

Human-readable schema and editorial guide for Agent Wiki.
Spec version: v2
Last updated: 2026-05-02

---

## 1. What this wiki is

This wiki is a structured knowledge base designed to be useful for both humans and AI agents.

This file is the compact runtime schema and editorial guide for ordinary wiki operations. User agents should prefer this file for page schemas, status enums, ID formats, evidence rules, and common examples.

The full project and development contract lives in [[AGENT-WIKI-SPEC-v2]]. Use the full spec when changing project behavior, scripts, skills, configuration policy, validation behavior, or when this file is insufficient. If this file conflicts with the full spec, the full spec remains canonical until the conflict is resolved.

It separates:
- **things** from **ideas**
- **claims** from **evidence**
- **sources** from **summaries**
- **facts** from **interpretations**
- **human-edited content** from **compiled/generated artifacts**
- **page structure** from **compiled machine caches**

---

## 1.1 Documentation layers

| File | Use |
|---|---|
| [[AGENTS]] | Agent behavior contract: preservation, logging, linking, generated files, and editing boundaries |
| [[WIKI#4.1 Common runtime schemas]] | Compact runtime schema and editorial reference for ordinary vault work |
| [[INBOX]] | Short pointer to inbox rules and the `process-inbox` skill |
| [[ONBOARD]] | First-run setup and local environment workflow |
| [[AGENT-WIKI-SPEC-v2]] | Full project/development contract and detailed implementation reference |

Agents should load the smallest document that answers the task. Routine source import, inbox processing, extraction, overview, and compile work should not require loading the full spec unless there is ambiguity.

---

## 2. Folder meanings

Current vault structure:

```text
<vault>/
  AGENTS.md
  AGENT-WIKI-SPEC-v2.md
  INBOX.md
  ONBOARD.md
  README.md
  WIKI.md
  index.md
  overview.md

  sources/
    parts/
  entities/
  concepts/
  claims/
  syntheses/
  questions/
  reports/
  skills/

  _inbox/
  raw/
  _attachments/
  _archive/
  _system/
    config.example.json
    cache/
    indexes/
    logs/
```

Fresh template checkouts may omit empty content and runtime folders. Initialization, import, and compile workflows create missing folders as needed.

| Folder | What goes here |
|---|---|
| `sources/` | Canonical source pages: webpages, PDFs, articles, transcripts, meeting notes, datasets |
| `sources/parts/` | Source part pages for large partitioned sources |
| `entities/` | Durable things: people, orgs, projects, products, systems, places, events, artifacts |
| `concepts/` | Abstract ideas and reusable instructions: definitions, methods, frameworks, workflows, runbooks, checklists |
| `claims/` | Standalone claim pages: individual atomic propositions with their own evidence and provenance |
| `syntheses/` | Maintained cross-source interpretations: overviews, analyses, comparisons, briefs, timelines |
| `questions/` | Unresolved uncertainties and research gaps |
| `reports/` | Generated maintenance views and dashboards |
| `skills/` | Agent skill definitions and supporting skill files |
| `_attachments/` | Attachments referenced by source or other pages (created on init, may be empty) |
| `_archive/` | Archived content no longer actively maintained (created on init, may be empty) |
| `_system/` | Machine-generated runtime and compile artifacts (do not hand-edit) |
| `_inbox/` | Raw intake queue for unprocessed items |
| `raw/` | Retained original raw files after inbox promotion |

Workspace-mode wikis use the same internal structure, but the wiki root is usually `workspace/wiki`. Source candidates can live outside the wiki directory and be discovered by the CLI, while deliberate captures can still land in the wiki's `_inbox/`. They become canonical evidence only after an agent creates `source` pages inside `wiki/sources/`.

`_system/config.json` is optional local operational configuration for tool policy and command preferences. It is not canonical vault knowledge, should not contain secrets, and should not be committed. `_system/config.example.json` is the tracked example shape. Optional `knownVaults` entries may map Obsidian vault names to absolute local paths so agents can resolve `obsidian://` cross-vault references for reading only.

Use `agent-wiki onboard --check --wiki-root PATH` for deterministic first-run onboarding and local setup probes. The command emits structured JSON for automation. Use `agent-wiki onboard --check --questions --wiki-root PATH` when an agent needs compact multiple-choice setup prompts for the user. Use `agent-wiki onboard --write-config` only after the user approves the exact local setup choices to persist.

Use `agent-wiki create-page` to scaffold new canonical pages from caller-supplied metadata and body content. It supports `source`, `entity`, `concept`, `claim`, `question`, and `synthesis` pages, including whole source pages, large-source parent manifests, source part pages, caller-supplied claim evidence records, and synthesis scope. It validates required frontmatter, IDs, filenames, duplicate IDs, target paths, subtype/status enums, required body content, supplied evidence shape, and required synthesis scope. It covers required schema fields, but does not automatically fill every optional recommended field such as `owner`, `summary`, `freshness`, or page-level `confidence`.

Each wiki root remains a single Agent Wiki. In vault mode, the repository or selected root is the wiki root. In workspace mode, the wiki root is usually `workspace/wiki`. The CLI may track multiple local Agent Wiki roots through the machine-local registry at `~/.config/agent-wiki/registry.json`. Registry entries are named Agent Wiki roots and can be selected with `agent-wiki --wiki NAME <command>`. The registry is local operator state, not canonical wiki knowledge, and should not be stored inside a wiki.

Use `agent-wiki list` to list registered wikis and paths. Use `agent-wiki check --all` for a light read-only registry health check across all registered wikis. Use `agent-wiki check --all --full` when compile and index validation should also run. Obsidian setup is optional and means opening the wiki root as an Obsidian vault; it does not change where skills or scripts write content. `knownVaults` does not create alternate write roots.

Use `agent-wiki schedule prompt process-inbox`, `agent-wiki schedule prompt extract-primitives`, and `agent-wiki schedule prompt update-overview` to print scheduled-agent prompts from the registry. These prompts are meant for external scheduled-task harnesses and remain skill-based; the CLI does not execute those workflows. By default they target all registered wikis. Pass wiki names or `--wiki NAME` to target a subset. Scheduled agents should log failures for one wiki and continue to the next.

---

## 3. Page types

Every authored page has a `pageType` in its frontmatter.

| `pageType`  | Folder        | Purpose                               |
| ----------- | ------------- | ------------------------------------- |
| `source`    | `sources/`    | Information origin                    |
| `entity`    | `entities/`   | Durable thing                         |
| `concept`   | `concepts/`   | Abstract idea, definition, or reusable instruction |
| `claim`     | `claims/`     | Standalone atomic proposition         |
| `synthesis` | `syntheses/`  | Cross-source rollup or interpretation |
| `question`  | `questions/`  | Open question or research gap         |
| `report`    | `reports/`    | Generated view or dashboard           |
| `index`     | `index.md`    | Deterministic root page catalog       |
| `overview`  | `overview.md` | Human-facing vault landing page       |

---

## 4. Required frontmatter

Every authored page (except purely generated reports and the generated root catalog) should include:

```yaml
id: <pageType>.<primitiveSubtype>.<slug>
pageType: <pageType>
title: <title>
status: <status>
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Recommended additional fields:

```yaml
canonicalName: <canonicalName>
owner:
summary:
sourcePages: []
relatedPages: []
confidence:
freshness:
```

---

## 4.1 Common runtime schemas

These compact templates cover routine agent work. Omit optional fields only when they do not apply or cannot be inferred without guessing.

### Source

```yaml
id: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
pageType: source
title: <title>
status: unprocessed
sourceType: <sourceType>
sourceRole: whole
originUrl:
originPath:
publishedAt:
retrievedAt: YYYY-MM-DD
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
attachments: []
```

For large sources, use a short parent source and child part pages:

```yaml
id: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
pageType: source
title: <title>
status: partitioned
sourceType: <sourceType>
sourceRole: parent
sourceParts:
  - sources/parts/<yyyy-mm-dd>-<sourceType>-<sourceSlug>-part001.md
originUrl:
originPath:
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

```yaml
id: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>.part001
pageType: source
title: <title> - Part 1
status: unprocessed
sourceType: <sourceType>
sourceRole: part
parentSourceId: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
partIndex: 1
partCount: <count>
locator: <page range, heading path, timestamp range, slide range, or section range>
originUrl:
originPath:
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

When conversion produced the Markdown source body, add available provenance:

```yaml
convertedAt: YYYY-MM-DD
conversionTool: <tool>
conversionToolVersion: <version>
conversionBackend: <backend>
conversionWarnings: []
```

### Entity

```yaml
id: entity.<entityType>.<entitySlug>
pageType: entity
title: <title>
entityType: <entityType>
canonicalName: <canonicalName>
status: active
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Add a substantive Markdown body after the frontmatter. Describe the entity, why it matters in the vault, important aliases or identifiers, and known uncertainty.

### Concept

```yaml
id: concept.<conceptType>.<conceptSlug>
pageType: concept
title: <title>
conceptType: <conceptType>
status: active
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Add a substantive Markdown body after the frontmatter. Explain the concept, its boundaries, source-grounded examples or steps, and important distinctions.

### Claim Page

```yaml
id: claim.<claimType>.<claimSlug>
pageType: claim
title: <title>
claimType: <claimType>
status: unverified
confidence: 0.60
text: <one atomic proposition>
subjectPageId:
sourceIds: []
evidence: []
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Add a substantive Markdown body after the frontmatter. Restate the atomic proposition in prose, summarize the evidence posture, and note caveats or uncertainty.

### Synthesis

```yaml
id: synthesis.<synthesisType>.<synthesisSlug>
pageType: synthesis
title: <title>
synthesisType: <synthesisType>
scope: <scope>
status: active
sourcePages: []
derivedClaims: []
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Add a substantive Markdown body after the frontmatter. Provide maintained narrative interpretation, scope, source basis, current conclusions, and open tensions.

Create synthesis pages when the user needs durable cross-source interpretation, such as a summary, overview, analysis, timeline, brief, or comparison. Do not use synthesis pages for a single atomic proposition, raw captured material, unresolved questions, deterministic reports, or whole-vault landing prose. List source basis in `sourcePages` when sources are used, list tracked claim dependencies in `derivedClaims` when claim pages are used, and preserve uncertainty or contradictions in the body prose.

### Embedded Claim

```yaml
claims:
  - id: claim.<claimType>.<claimSlug>
    text: <one atomic proposition>
    status: unverified
    confidence: 0.60
    claimType: <claimType>
    relatedClaimIds: []
    evidence: []
    createdAt: YYYY-MM-DD
    updatedAt: YYYY-MM-DD
```

### Evidence Entry

```yaml
evidence:
  - id: evidence.<kind>.<relation>.<stable-suffix>
    sourceId: source.<yyyy-mm-dd>.<sourceType>.<sourceSlug>
    path: sources/<source-file>.md
    lines:
    kind: quote
    relation: context_only
    weight: 0.60
    note:
    excerpt:
    retrievedAt: YYYY-MM-DD
    updatedAt: YYYY-MM-DD
```

### Question

```yaml
id: question.<domain>.<questionSlug>
pageType: question
title: <question>
priority: medium
status: open
relatedClaims: []
relatedPages: []
openedAt: YYYY-MM-DD
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

Add a substantive Markdown body after the frontmatter. Explain why the question exists, what is already known, what remains unresolved, and what would count as resolution.

### Relation

```yaml
relations:
  - subject: <subject-id>
    predicate: <predicate>
    object: <object-id>
    confidence: 0.60
    sourceClaimIds: []
```

### Overview

```yaml
id: meta.overview
pageType: overview
title: Vault Overview
status: active
createdAt: YYYY-MM-DD
updatedAt: YYYY-MM-DD
aliases: []
tags: []
```

---

## 4.2 Authored page bodies

New `entity`, `concept`, `claim`, `question`, and `synthesis` pages must include a substantive Markdown body after frontmatter.

The body should be detailed, human-facing prose that explains what the page represents, why it matters, and how the structured fields should be understood. It should not be a placeholder, a one-line restatement of the title, or only a machine-readable metadata dump.

Agents should use `agent-wiki create-page` for new page files when a skill creates canonical `source`, `entity`, `concept`, `claim`, `question`, or `synthesis` pages. The script is a scaffolder only; the calling skill or agent remains responsible for the actual source capture, body prose, evidence judgment, relationships, source partitioning decisions, synthesis judgment, and optional fields that require judgment. For claim pages, pass already-selected evidence to the scaffolder so it can render spec-shaped block YAML. For synthesis pages, pass an explicit `--scope` and any known `--source-page` or `--derived-claim` values.

Agents must preserve existing human-authored body prose unless the operator explicitly asks for a rewrite.

## 5. Status vocabularies

### General page status

| Status | Meaning |
|---|---|
| `active` | Maintained page |
| `draft` | Incomplete page |
| `archived` | No longer maintained |
| `deprecated` | Superseded or no longer valid |

### Source status

| Status | Meaning |
|---|---|
| `unprocessed` | Captured as a source page, not yet extracted into knowledge primitives |
| `partitioned` | Parent source has child source parts that still need extraction |
| `processed` | Extraction completed |
| `archived` | Retained but inactive |

### Question status

| Status | Meaning |
|---|---|
| `open` | Unresolved, actively tracked |
| `researching` | Actively being investigated |
| `blocked` | Cannot proceed without external input |
| `resolved` | Answer found and recorded |
| `dropped` | No longer relevant or pursued |


---

## 6. Claim rules

Claims are first-class records that can be evaluated, tracked, and compiled.

A claim should express **one proposition**, not several glued together.

### Claim status

| Status | Meaning |
|---|---|
| `supported` | Has strong, direct evidence |
| `weakly_supported` | Has some evidence but not strong |
| `inferred` | Derived logically, not directly evidenced |
| `unverified` | Not yet checked against sources |
| `contested` | Active disagreement exists |
| `contradicted` | Evidence directly contradicts it |
| `deprecated` | No longer applicable |

### Confidence

`confidence` is a float from `0.0` to `1.0`.

| Range | Meaning |
|---|---|
| `0.0 – 0.49` | Low confidence — should appear in low-confidence reports |
| `0.50 – 0.74` | Moderate confidence |
| `0.75 – 0.89` | High confidence |
| `0.90 – 1.0` | Very high confidence |

### Claim types

| Type | Meaning |
|---|---|
| `descriptive` | What something is or does |
| `historical` | What happened at a point in time |
| `causal` | Why something happened |
| `interpretive` | What something means |
| `normative` | What should be done |
| `forecast` | What is expected to happen |

---

## 7. Evidence rules

Evidence attaches provenance and support semantics to a claim.

### Evidence kinds

| Kind | Meaning |
|---|---|
| `quote` | Direct quotation from a source |
| `summary` | Summarized content from a source |
| `measurement` | Quantitative data point |
| `observation` | Direct observation record |
| `screenshot` | Visual capture |
| `transcript` | Spoken record |
| `inference` | Derived from other evidence |

### Evidence relations

| Relation | Meaning |
|---|---|
| `supports` | Strengthens the claim |
| `weakens` | Reduces confidence in the claim |
| `contradicts` | Directly conflicts with the claim |
| `context_only` | Provides context but not direct support |

`context_only` evidence is NOT counted as support during compile scoring.

---

## 8. Relationship predicates

The v2 controlled predicate set:

| Predicate | Meaning |
|---|---|
| `is_a` | Type relationship |
| `part_of` | Composition |
| `depends_on` | Dependency |
| `uses` | Usage relationship |
| `produces` | Output relationship |
| `founded_by` | Founding relationship |
| `owned_by` | Ownership |
| `located_in` | Location |
| `related_to` | General association |
| `supports` | Supports another object |
| `contradicts` | Conflicts with another object |
| `mentions` | References without strong relation |
| `applies_to` | Scope or applicability |
| `derived_from` | Derived or based on |

---

## 9. Generated content

Generated structured knowledge should live in frontmatter fields, claim/evidence/relation records, cache files, indexes, reports, or the deterministic root `index.md` catalog.

Agents should preserve human-authored page prose unless explicitly asked to rewrite it. Page body prose is ordinary markdown.

`index.md` is generated as the root page catalog. Do not place durable manual prose there; use root documentation files such as [[overview]], [[README]], [[WIKI#1.1 Documentation layers]], [[ONBOARD]], or [[AGENTS]] instead.

`overview.md` is durable AI-maintained orientation prose. It should summarize the vault for a human reader, but it is not primary evidence and should not replace canonical source, claim, evidence, or page metadata records.

---

## 10. Compile outputs

The compile pipeline reads the vault, emits machine-readable caches to `_system/cache/`, and regenerates the root `index.md` page catalog.

Run with:

```bash
agent-wiki compile
```

Required outputs:
- `pages.json` — normalized page index
- `claims.jsonl` — all extracted claims
- `relations.jsonl` — all extracted relations
- `agent-digest.json` — high-signal agent context

Recommended outputs:
- `contradictions.json`, `questions.json`
- `timeline-events.json`, `source-index.json`

Catalog output:
- `index.md` — deterministic root-level page catalog rendered from `_system/cache/pages.json`

---

## 11. Reports

Reports in `reports/` are generated views. They are NOT authoritative.

| Report | Purpose |
|---|---|
| `open-questions.md` | All open question pages |
| `contradictions.md` | Tracked claim conflicts |
| `low-confidence.md` | Claims with confidence below 0.50 |
| `claim-health.md` | Evidence gap and staleness overview |
| `stale-pages.md` | Pages not updated recently |

Do not treat reports as primary data — they derive from page frontmatter and caches.

---

## 12. Source types

| Type | Meaning |
|---|---|
| `webpage` | Web page |
| `article` | Published article |
| `document` | Generic long-form document |
| `pdf` | PDF document |
| `transcript` | Conversation or meeting transcript |
| `email` | Email thread |
| `meeting-notes` | Meeting notes |
| `dataset` | Structured data |
| `screenshot` | Visual capture |
| `bridge` | Bridge page pointing to an external source |
| `import` | Raw imported file |
| `other` | Other source type |

---

## 12.1 Entity and concept types

### Entity types

| Type | Meaning |
|---|---|
| `person` | Person |
| `organization` | Organization |
| `project` | Project |
| `product` | Product |
| `system` | System |
| `place` | Place |
| `event` | Event |
| `artifact` | Artifact |
| `document` | Document as a thing |
| `other` | Other entity |

### Concept types

| Type | Meaning |
|---|---|
| `definition` | Definition |
| `principle` | Principle |
| `framework` | Framework |
| `method` | Method |
| `policy` | Policy |
| `standard` | Standard |
| `pattern` | Pattern |
| `workflow` | Workflow |
| `runbook` | Runbook |
| `checklist` | Checklist |
| `playbook` | Playbook |
| `theory` | Theory |
| `taxonomy` | Taxonomy |
| `other` | Other concept |

---

## 13. Large sources

Large sources should not become one giant markdown file when that would make extraction or evidence citation unreliable.

For long documents, transcripts, or captures, use:

- a short parent source page in `sources/`
- source part pages in `sources/parts/`
- a retained original file in `raw/` when the material came through `_inbox/`

The parent source is the document-level record and manifest. It should use `sourceRole: parent`, usually `status: partitioned`, and an ordered `sourceParts` list. The parent body should stay short.

Each source part is a canonical source page for a bounded segment. It should use `sourceRole: part`, `parentSourceId`, `partIndex`, `partCount`, and a stable `locator` such as a page range, section path, timestamp range, or slide range.

Extraction should run against source parts, not the parent source page. Evidence should cite the most specific source part and locator available.

---

## 14. Inbox intake strategy

The `_inbox/` folder is the raw item intake queue. New unprocessed material should land here first.

Raw inbox items are promoted into canonical `source` pages by the `process-inbox` skill. This section owns the durable lifecycle rules; the skill owns the exact operational commands.

### Intake lifecycle

1. Raw item arrives in `_inbox/`
2. `process-inbox` reads the raw item
3. If retained: `process-inbox` uses `agent-wiki create-page` to write a canonical `source` page under `sources/` with `status: unprocessed`, or a large-source parent plus source parts
4. The original raw file moves to `raw/`
5. If discarded: the raw file moves to `_inbox/trash/`

### `_inbox/` is not canonical

- Inbox raw files are NOT `source` pages.
- Files in `raw/` are retained originals, not canonical source records.
- Agents MUST NOT treat `_inbox/` or `raw/` items as authoritative source records.
- Agents SHOULD process inbox items by converting them into proper `source` pages.

### Workspace files are not canonical

In workspace mode, files outside the wiki directory are discovery inputs. They may be project notes, docs, datasets, exports, or other artifacts worth promoting.

Agents SHOULD use:

```bash
agent-wiki workspace pending --json
```

to get a deterministic worklist of new or changed files. The agent then decides which files deserve canonical source pages.

Original workspace files MUST stay in place. A workspace source page SHOULD point back to the original file with `originPath`, using the workspace-relative path. The `process-workspace-sources` skill owns this workflow.

---

## 15. Internal linking convention

All internal links within the vault use Obsidian-style wikilinks.

| Format | Use |
|---|---|
| `[[page-slug]]` | Link to a page |
| `[[page-slug\|Display Text]]` | Link with custom display text |
| `[[page-slug#section]]` | Link to a section |

Standard markdown links are only used for external URLs and `obsidian://` cross-vault references. Cross-vault Obsidian links are not wikilinks; they use the `obsidian://open?vault=<vault-name>&file=<url-encoded-path>` URI form. Agents resolve them only through local `_system/config.json` `knownVaults`; if no mapping exists, treat the URI as an opaque external reference.

---

## 16. Editorial principles

- Claims should be atomic — one proposition per claim.
- Important assertions should be in frontmatter, not buried in prose, if they matter for agents.
- Questions should remain open until explicitly resolved.
- Human-authored notes should be preserved unless explicitly changed by the operator.
- Reports are views, not truth sources.
- Inbox items MUST be processed into canonical source pages before being treated as evidence.
