---
name: extract-knowledge-primitives
description: "Extract knowledge primitives (entities, concepts, claims, procedures, questions) from source pages. Use this skill when the user says 'extract primitives', 'extract knowledge', 'process sources for structured data', or 'analyze sources'. This skill reads source pages and creates appropriate wiki pages for entities, concepts, claims, procedures (runbooks/workflows), and questions, following the v1 schema. Run this after sources have been processed by the process-new-notes skill."
---

# Extract Knowledge Primitives

This skill guides the workflow for extracting structured knowledge primitives (entities, concepts, claims, and relations) from source pages and creating appropriate wiki pages that follow the Agentics vault v1 schema.

## Overview

**Goal:** Convert free-form source content into structured wiki pages representing:
- **Entities** — durable things (people, organizations, projects, systems, places, events, artifacts)
- **Concepts** — abstract ideas (definitions, methods, frameworks, principles, policies, standards)
- **Claims** — atomic factual propositions with evidence
- **Procedures** — action-oriented instructions (runbooks, workflows, checklists, playbooks)
- **Questions** — unresolved uncertainties and research gaps
- **Relations** — typed connections between primitives

**Principles:**
- Do not invent certainty — extracted claims start `unverified` (confidence: 0.70)
- Preserve source content — extraction adds structure without rewriting
- Stable IDs — primitives are identified with dotted-namespace IDs that don't change
- Avoid duplicates — check vault before creating pages

---

## Step 1: Read the Vault Contract

Before extracting anything, read the vault's agent contract and schema:

1. **[[AGENTS]]** — behavior expectations for agents in this vault
   - Key rule: preserve human content outside managed blocks
   - Key rule: use stable dotted-namespace IDs
   - Key rule: do not invent unsupported certainty
   - Key rule: do not rewrite human-authored content

2. **[[WIKI]]** — editorial schema and page type definitions
   - Page types: source, entity, concept, claim, synthesis, procedure, question
   - Status vocabularies
   - Claim/evidence rules

3. **[[AGENT-WIKI-SPEC-v1]]** — full technical specification
   - Frontmatter fields
   - Claim/evidence structures
   - Relationship predicates
   - ID conventions

These define your contract. Violation of this contract will break the vault.

---

## Step 2: Identify Source Pages Needing Extraction

Scan the `sources/` folder for pages that have not yet been processed for extraction.

A source page **needs extraction** if:
- It has no `extractionStatus` field in frontmatter, OR
- `extractionStatus: unprocessed` (or missing/empty)

A source page **has been extracted** if:
- `extractionStatus: extracted` AND
- `extractedAt:` field is present with a date

Read frontmatter only — do not re-process pages that already have `extractionStatus: extracted`.

If no unprocessed source pages are found, report this to the user and stop.

---

## Step 3: Analyze Each Source Page

For each source page needing extraction, read the full content and analyze it to identify:

### 3a. Extract Entities

**What is an entity?**
A durable thing that is referred to by name and remains (mostly) unchanged over time.

**Examples:**
- `entity.person.john-doe` — a specific person
- `entity.organization.acme-corp` — an organization
- `entity.project.ai-harness` — a project
- `entity.system.kubernetes` — a system or technology
- `entity.product.claude-3` — a product or service
- `entity.place.san-francisco` — a location
- `entity.event.ai-summit-2026` — a named event

**Extraction heuristic:**
Look for proper nouns (capitalized names) that are:
- Specific references (not generic nouns like "company" or "person")
- Mentioned multiple times or as the main subject
- Worth tracking and linking to across the vault

**ID format:** `entity.<entityType>.<slug>`
- `entityType`: `person`, `organization`, `project`, `product`, `system`, `place`, `event`, etc.
- `slug`: kebab-case version of the name (e.g., `john-doe`, `acme-corp`)

**Example entity from source text:**
```
Source mentions: "Acme Corp was founded in 2010 by John Doe."

Extracted entities:
- entity.organization.acme-corp (Acme Corp)
- entity.person.john-doe (John Doe)
```

### 3b. Extract Concepts

**What is a concept?**
An abstract idea, definition, method, framework, or principle that is reusable and applies to multiple contexts.

**Examples:**
- `concept.method.adaptive-reuse` — a reuse methodology
- `concept.principle.chain-of-custody` — a provenance principle
- `concept.workflow.stormwater-inspection` — an operational workflow pattern
- `concept.pattern.cool-roof-retrofit` — a building upgrade pattern
- `concept.framework.service-blueprint` — a planning framework

**Extraction heuristic:**
Look for:
- Defined terms (e.g., "X is..." or "We call X...")
- Techniques or methods described
- Principles or standards
- Taxonomies or classifications
- Frameworks or patterns

**ID format:** `concept.<conceptType>.<slug>`
- `conceptType`: definition, principle, framework, method, policy, standard, pattern, theory, taxonomy, or other
- `slug`: kebab-case descriptor (e.g., `adaptive-reuse`)

**Example concept from source text:**
```
Source mentions: "Adaptive reuse converts existing buildings to new uses while preserving much of the original structure."

Extracted concept:
- concept.method.adaptive-reuse (adaptive reuse methodology)
```

### 3c. Extract Claims

**What is a claim?**
An atomic factual proposition that:
- Makes one assertion (not several)
- Can be true or false
- Should be supported (or unsupported) by evidence

**Examples:**
- `"Acme Corp was founded in 2010"` — historical claim
- `"Structured claims improve vault clarity"` — interpretive claim
- `"Kubernetes uses container orchestration"` — descriptive claim

**Extraction heuristic:**
Look for sentences or statements that:
- Describe facts about entities or concepts
- Make causal or temporal assertions
- State definitions or classifications
- Express interpretations or conclusions

Keep claims **atomic** — break compound statements apart:
- ❌ BAD: "Acme Corp was founded in 2010 and is based in San Francisco"
- ✅ GOOD: 
  - "Acme Corp was founded in 2010"
  - "Acme Corp is based in San Francisco"

**ID format:** `claim.<topic>.<descriptor>`
- `topic`: subject area (e.g., `acme`, `vault`, `kubernetes`)
- `descriptor`: brief slug describing the claim

**Claim type** (from spec: descriptive, historical, causal, interpretive, normative, forecast):
- **historical**: dated events ("X happened on [date]")
- **descriptive**: what something is or does ("X is Y", "X does Z")
- **causal**: why something happened ("X causes Y")
- **interpretive**: what something means or implies
- **normative**: what should be done
- **forecast**: what is expected to happen

**Example claims from source text:**
```
Source mentions: "Acme Corp was founded in 2010 by John Doe. It's a 
leader in AI products. We believe structured data is key to their success."

Extracted claims:
- claim.acme.founded-2010 (historical, unverified)
- claim.acme.founder-is-john-doe (historical, unverified)
- claim.acme.leads-in-ai (interpretive, unverified)
- claim.acme.success-from-structured-data (causal, unverified)
```

### 3d. Extract Procedures

**What is a procedure?**
Action-oriented instructions describing how to do something. Workflows, runbooks, checklists, or playbooks.

**Examples:**
- `procedure.deploy.kubernetes` — how to deploy to Kubernetes
- `procedure.vault.process-inbox` — workflow for processing new notes
- `procedure.claims.extract-from-text` — checklist for extracting claims from text

**Extraction heuristic:**
Look for:
- Step-by-step instructions ("First do X, then do Y")
- Checklists or numbered lists with tasks
- Workflows or processes described
- How-to guides or tutorials
- Commands or configuration instructions

**ID format:** `procedure.<domain>.<slug>`
- `domain`: area of application (deploy, vault, claims, etc.)
- `slug`: brief descriptor

**Example procedure from source text:**
```
Source mentions: "To set up the vault: First, create the directory structure. 
Second, initialize git. Third, add the schema files. Finally, run the compile 
pipeline to validate."

Extracted procedure:
- procedure.vault.setup (workflow with 4 steps)
```

### 3e. Extract Questions

**What is a question?**
An unresolved uncertainty, research gap, or something the source identifies as needing further investigation.

**Examples:**
- `question.entity-deduplication.strategy` — how should duplicate entities be detected/merged?
- `question.claim-confidence.calibration` — how should confidence scores be calibrated?
- `question.vault.scalability` — how will the vault perform at 10,000+ pages?

**Extraction heuristic:**
Look for:
- Explicit questions ("How do we...")
- Uncertainties ("We're not sure whether...")
- Open problems or gaps
- Areas marked as "TODO" or "future work"
- Debates or unresolved disagreements

**ID format:** `question.<domain>.<slug>`
- `domain`: area the question concerns
- `slug`: brief descriptor

**Status options:** open, researching, blocked, resolved, dropped

**Example questions from source text:**
```
Source mentions: "One open question is how to handle contradictions between 
sources. Should we require manual resolution or can we detect patterns 
automatically? This needs more thought."

Extracted question:
- question.contradictions.detection-strategy (open, unresolved)
```

### 3f. Identify Relations

**What is a relation?**
A typed connection between two entities or concepts.

**Common relation predicates (from spec):**
- `is_a` — type relationship
- `part_of` — composition
- `depends_on` — dependency
- `uses` — usage
- `produces` — output
- `founded_by` — founding relationship
- `owned_by` — ownership
- `located_in` — location
- `related_to` — general association
- `supports` — logical support
- `contradicts` — conflict
- `mentions` — references
- `applies_to` — scope
- `derived_from` — derivation

**Extraction heuristic:**
Look for implied relationships in the source:
- Organizational hierarchy (part_of, owned_by)
- Dependencies and interactions (depends_on, uses, produces)
- Locations (located_in)
- Type relationships (is_a)

**Example relations from source text:**
```
Source mentions: "Acme Corp's AI division, led by John Doe, uses 
Kubernetes for infrastructure."

Extracted relations:
- ai-division part_of acme-corp
- john-doe owned_by acme-corp (or: leads acme-corp)
- acme-corp uses kubernetes
```

Relations will be embedded in entity/concept pages or recorded as relation entries.

---

## Step 4: Create Entity Pages

For each extracted entity, create a new file in `entities/` with proper frontmatter.

### Template

```yaml
---
id: entity.<entityType>.<slug>
pageType: entity
title: <Canonical Name>
entityType: <entityType>
canonicalName: <Official Name>
status: active
createdAt: 2026-04-16
updatedAt: 2026-04-16
aliases:
  - <alternate names>
tags:
  - extracted
relatedPages: []
relations: []
---

# <Canonical Name>

[Add a brief human-written summary here, or leave it for managed block generation]

<!-- AI:GENERATED START name=summary -->
A brief auto-generated summary of this entity based on source mentions.
<!-- AI:GENERATED END name=summary -->
```

### Guidelines

- **ID**: Use stable dotted-namespace format: `entity.<entityType>.<slug>`
  - `entityType`: person, organization, project, product, system, place, event, artifact, document, or other
  - `slug`: kebab-case version of the name
  - Example: `entity.organization.acme-corp`

- **title** & **canonicalName**: The official/preferred name of the entity
  - Example: `title: "Acme Corporation"`, `canonicalName: "Acme Corp"`

- **aliases**: Alternate names by which this entity is known
  - Example: `aliases: ["Acme Corp", "ACME"]`

- **tags**: Include `extracted` tag, plus any topical tags
  - Example: `tags: [extracted, ai, industry]`

- **relations**: Add relations to this entity (see Step 7)

**File path**: `entities/<slug>.md`
- Example: `entities/acme-corp.md`

**Important:** 
- Check if this entity already exists before creating (search `entities/` and cache index)
- If entity already exists, do NOT create a duplicate
- If related entity exists, add `relatedPages` links

---

## Step 5: Create Concept Pages

For each extracted concept, create a new file in `concepts/` with proper frontmatter.

### Template

```yaml
---
id: concept.<conceptType>.<slug>
pageType: concept
title: <Concept Name>
conceptType: <type>
status: active
createdAt: 2026-04-16
updatedAt: 2026-04-16
aliases: []
tags:
  - extracted
relatedPages: []
---

# <Concept Name>

[Brief human summary of what this concept is, or leave for generation]

<!-- AI:GENERATED START name=summary -->
Auto-generated definition or explanation of the concept.
<!-- AI:GENERATED END name=summary -->
```

### Guidelines

- **ID**: `concept.<conceptType>.<slug>`
  - Example: `concept.method.adaptive-reuse`

- **conceptType**: method, definition, framework, principle, policy, standard, pattern, theory, etc.

- **title**: The concept name
  - Example: `title: "Structured Claims"`

- **aliases**: Other names for this concept

- **tags**: Include `extracted` tag plus topical tags

**File path**: `concepts/<slug>.md`
- Example: `concepts/structured-claims.md`

**Important:**
- Check for duplicates before creating
- Link related concepts via `relatedPages`

---

## Step 6: Create Claim Pages

For each extracted claim, create a new file in `claims/` with proper frontmatter and evidence.

### Template

```yaml
---
id: claim.<topic>.<descriptor>
pageType: claim
title: <Claim Statement>
claimType: <type>
status: unverified
confidence: 0.70
text: <Exact claim text>
subjectPageId: <entity or concept being claimed about>
sourceIds:
  - <source page ID>
evidence:
  - id: ev.<claim-slug>.01
    sourceId: <source page ID>
    path: <source file path>
    kind: quote
    relation: supports
    weight: 0.70
    note: <What this evidence shows>
    excerpt: "<Exact quote from source>"
    retrievedAt: 2026-04-16
    updatedAt: 2026-04-16
createdAt: 2026-04-16
updatedAt: 2026-04-16
aliases: []
tags:
  - extracted
---

# <Claim Statement>

This claim is extracted from [[<source page ID>]].
```

### Guidelines

- **ID**: `claim.<topic>.<descriptor>`
  - `topic`: subject area (e.g., acme, kubernetes, ai)
  - `descriptor`: kebab-case description
  - Example: `claim.acme.founded-2010`

- **title** & **text**: The actual claim statement
  - Example: `"Acme Corp was founded in 2010"`

- **claimType**: One of: descriptive, historical, causal, interpretive, normative, forecast

- **status**: Always `unverified` for extracted claims
  - Confidence: Always `0.70` (moderate) for extracted claims

- **subjectPageId**: The entity or concept this claim is about
  - Example: `entity.organization.acme-corp`

- **sourceIds**: Array of source page IDs
  - Example: `["source.2026-04-16.acme-homepage"]`

- **evidence**: Array of evidence entries
  - Each entry has id, sourceId, path, kind, relation, weight, note, excerpt, retrievedAt, updatedAt
  - `kind`: quote, summary, measurement, observation, inference, etc.
  - `relation`: supports, weakens, contradicts, context_only
  - `weight`: confidence in this evidence (0.0 - 1.0), typically 0.70-0.80 for extracted

- **tags**: Include `extracted` tag

**File path**: `claims/<descriptor>.md`
- Example: `claims/acme-founded-2010.md`

**Important:**
- Keep evidence entries brief and point back to the source
- Do not duplicate claims that already exist
- Extracted claims are always unverified — agents must add supporting evidence to increase confidence
- The excerpt should be the exact text from the source

---

## Step 7: Create Procedure Pages

For each extracted procedure, create a new file in `procedures/` with proper frontmatter.

### Template

```yaml
---
id: procedure.<domain>.<slug>
pageType: procedure
title: <Procedure Name>
procedureType: <runbook|workflow|checklist|playbook>
status: active
createdAt: 2026-04-16
updatedAt: 2026-04-16
aliases: []
tags:
  - extracted
relatedPages: []
---

# <Procedure Name>

[Brief description of what this procedure is for]

## Steps

1. [Step one]
2. [Step two]
3. [Step three]

<!-- AI:GENERATED START name=summary -->
Auto-generated summary of this procedure.
<!-- AI:GENERATED END name=summary -->
```

### Guidelines

- **ID**: `procedure.<domain>.<slug>`
  - `domain`: area of application (vault, deploy, claims, etc.)
  - `slug`: kebab-case descriptor
  - Example: `procedure.vault.process-inbox`

- **procedureType**: runbook, workflow, checklist, or playbook

- **title**: Name of the procedure

- **Step-by-step content**: Extract the actual steps from the source and present them clearly

- **tags**: Include `extracted` tag

**File path**: `procedures/<slug>.md`
- Example: `procedures/vault-setup.md`

**Important:**
- Keep procedures clear and actionable
- Extract exact steps from source when possible
- Link related procedures or entities via `relatedPages`
- Check for duplicates before creating

---

## Step 8: Create Question Pages

For each extracted question, create a new file in `questions/` with proper frontmatter.

### Template

```yaml
---
id: question.<domain>.<slug>
pageType: question
title: <Question Title>
priority: <low|medium|high|critical>
status: open
openedAt: 2026-04-16
createdAt: 2026-04-16
updatedAt: 2026-04-16
relatedClaims: []
relatedPages: []
aliases: []
tags:
  - extracted
---

# <Question Title>

## The Question

[Clear statement of what is unknown or unresolved]

## Context

[Why this question matters, what prompted it]

## Possible Answers

[If mentioned in source: alternative approaches or solutions being considered]
```

### Guidelines

- **ID**: `question.<domain>.<slug>`
  - `domain`: area the question concerns
  - Example: `question.contradictions.detection-strategy`

- **title**: The question, phrased as a query
  - Example: `"How should contradictions be detected?"`

- **priority**: low, medium, high, or critical
  - Extract from source or infer from importance

- **status**: Always `open` for extracted questions (unless source says it's resolved)
  - Other statuses: researching, blocked, resolved, dropped

- **relatedPages**: Link to related concepts, claims, sources, or procedures

- **relatedClaims**: Link to claims relevant to answering this question

- **tags**: Include `extracted` tag

**File path**: `questions/<slug>.md`
- Example: `questions/entity-deduplication-strategy.md`

**Important:**
- Questions should be specific enough to answer, not vague
- Include context about why the question matters
- Link to related pages/claims
- Mark as `open` — questions are meant to stay open until explicitly resolved
- Resolved questions should remain in vault with `status: resolved`, not be deleted

---

## Step 9: Create/Update Relations

Relations connect entities and concepts together. Add them to the pages being related.

### On Entity Pages

Add a `relations:` section to entity pages:

```yaml
relations:
  - subject: entity.organization.acme-corp
    predicate: founded_by
    object: entity.person.john-doe
    confidence: 0.80
    sourceClaimIds:
      - claim.acme.founder-is-john-doe
  
  - subject: entity.organization.acme-corp
    predicate: uses
    object: entity.system.kubernetes
    confidence: 0.70
    sourceClaimIds: []
```

### On Concept Pages

Link related concepts:

```yaml
relations:
  - subject: concept.method.adaptive-reuse
    predicate: related_to
    object: concept.policy.historic-preservation
    confidence: 0.60
    sourceClaimIds: []
```

### Relation Guidelines

- **subject** & **object**: Page IDs of the related items
- **predicate**: Use controlled predicates from the spec (is_a, part_of, depends_on, uses, produces, founded_by, owned_by, located_in, related_to, supports, contradicts, mentions, applies_to, derived_from)
- **confidence**: 0.0-1.0, typically 0.70-0.80 for extracted relations
- **sourceClaimIds**: Claims that support this relation (if any)

**Important:**
- Relations are directional (A uses B is different from B uses A)
- Document one direction; future agents can add the inverse if needed
- Do not duplicate existing relations

---

## Step 10: Update Source Page with Extraction Metadata

After extracting primitives from a source page, update the source file's frontmatter to record what was extracted:

```yaml
extractionStatus: extracted
extractedAt: 2026-04-16
extractedEntities:
  - entity.organization.acme-corp
  - entity.person.john-doe
extractedConcepts:
  - concept.method.adaptive-reuse
extractedClaims:
  - claim.acme.founded-2010
  - claim.acme.founder-is-john-doe
extractedProcedures:
  - procedure.vault.setup
extractedQuestions:
  - question.entity-dedup.strategy
```

Add these fields to the source page's frontmatter. Do NOT modify any other part of the source file — preserve human notes and content exactly as it is.

---

## Step 11: Run Compile Pipeline

After creating all new pages and updating source metadata, run the compile pipeline to validate and index everything:

```bash
python3 _wiki/skills/compile-wiki/scripts/compile.py
```

This will:
- Validate all new pages against the v1 schema
- Extract claims from your created pages
- Surface any issues (missing IDs, invalid fields, duplicates, etc.)
- Generate reports
- Update caches

**If validation errors occur**, fix the issues and re-run compile.

---

## Step 12: Report to User

After extracting from all source pages and running compile, give a concise summary:

```
Extraction Complete

Processed 3 source pages:
- source.2026-04-16.acme-homepage

Created:
- Entities: 2 (entity.organization.acme-corp, entity.person.john-doe)
- Concepts: 1 (concept.method.adaptive-reuse)
- Claims: 4 (claim.acme.founded-2010, claim.acme.founder-is-john-doe, ...)
- Procedures: 1 (procedure.vault.setup)
- Questions: 1 (question.entity-dedup.strategy)
- Relations: 3

Pages Updated:
- source.2026-04-16.acme-homepage -> marked as extracted

Validation: ✓ All pages passed schema validation
Cache regenerated with 4 new claims, 2 entities, 1 procedure, 1 question
```

---

## Important Rules

### Do's ✅

- ✅ Create stable IDs using dotted-namespace format
- ✅ Check for duplicates before creating pages
- ✅ Keep claims atomic (one proposition per claim)
- ✅ Mark extracted claims as `unverified` with `confidence: 0.70`
- ✅ Reference the source page in evidence
- ✅ Preserve all human content in source pages
- ✅ Include exact excerpts in claim evidence
- ✅ Run compile pipeline after extraction
- ✅ Record extraction metadata on source pages
- ✅ Use wikilinks for internal references

### Don'ts ❌

- ❌ Create duplicate entities/concepts/claims
- ❌ Invent confidence or certainty beyond what the source supports
- ❌ Modify or rewrite human-authored content
- ❌ Create compound claims (multiple assertions in one claim)
- ❌ Forget to add extraction metadata to source pages
- ❌ Use markdown links instead of wikilinks for internal references
- ❌ Mix extraction with human commentary (keep them separate)

---

## Reference: Extraction Checklist

For each source page processed:

- [ ] Read the full source content
- [ ] Identify entities (proper nouns, durable things)
- [ ] Identify concepts (definitions, methods, frameworks)
- [ ] Extract claims (atomic factual statements)
- [ ] Extract procedures (action-oriented instructions, workflows)
- [ ] Extract questions (unresolved issues, research gaps)
- [ ] Identify relations between extracted primitives
- [ ] Create entity pages (with canonical names and aliases)
- [ ] Create concept pages (with definitions)
- [ ] Create claim pages (with evidence from source)
- [ ] Create procedure pages (with step-by-step instructions)
- [ ] Create question pages (with context)
- [ ] Add relations to entity/concept pages
- [ ] Update source page with extractionStatus: extracted + all metadata
- [ ] Run compile pipeline
- [ ] Verify no validation errors
- [ ] Report results to user

---

## Reference: Common Patterns

### Pattern: Company extracted from source

**From source:** "Acme Corp, founded in 2010 by John Doe, is a leader in AI."

```yaml
# entities/acme-corp.md
id: entity.organization.acme-corp
pageType: entity
title: Acme Corporation
entityType: organization
canonicalName: Acme Corp
aliases: [Acme, ACME Corporation]
tags: [extracted, ai, companies]
relations:
  - subject: entity.organization.acme-corp
    predicate: founded_by
    object: entity.person.john-doe
    confidence: 0.80
    sourceClaimIds: [claim.acme.founder-is-john-doe]
```

```yaml
# claims/acme-founded-2010.md
id: claim.acme.founded-2010
pageType: claim
title: Acme Corp was founded in 2010
claimType: historical
status: unverified
confidence: 0.70
text: Acme Corp was founded in 2010
subjectPageId: entity.organization.acme-corp
sourceIds: [source.2026-04-16.acme-homepage]
evidence:
  - id: ev.acme.founded-2010.01
    sourceId: source.2026-04-16.acme-homepage
    path: sources/acme-homepage.md
    kind: quote
    relation: supports
    weight: 0.75
    excerpt: "Acme Corp, founded in 2010 by John Doe"
    retrievedAt: 2026-04-16
    updatedAt: 2026-04-16
```

### Pattern: Concept defined in source

**From source:** "Adaptive reuse converts older buildings into new uses while preserving significant existing structure."

```yaml
# concepts/adaptive-reuse.md
id: concept.method.adaptive-reuse
pageType: concept
title: Adaptive Reuse
conceptType: method
tags: [extracted, architecture]
```

### Pattern: Procedure described in source

**From source:** "To initialize the vault: First, create the directory structure. Second, add the schema files. Third, run compile to validate."

```yaml
# procedures/vault-initialization.md
id: procedure.vault.initialization
pageType: procedure
title: Initialize the Vault
procedureType: workflow
tags: [extracted, setup]
```

Content: Extract the actual steps and present them as a numbered list with clear instructions.

### Pattern: Question/uncertainty in source

**From source:** "An open question is how to detect duplicate entities. Should we use string similarity, or require explicit merges?"

```yaml
# questions/entity-deduplication-strategy.md
id: question.entity.deduplication-strategy
pageType: question
title: How should duplicate entities be detected and merged?
priority: high
status: open
tags: [extracted, open-question]
```

Content: Capture the question clearly, explain why it matters, and if the source mentions alternatives, list them.

---

## Appendix: Frontmatter Templates

See the `templates/` folder for complete YAML templates you can copy and fill in:
- `templates/entity-template.yaml` — template for entity pages
- `templates/concept-template.yaml` — template for concept pages
- `templates/claim-template.yaml` — template for claim pages with evidence
- `templates/procedure-template.yaml` — template for procedure pages
- `templates/question-template.yaml` — template for question pages

These are shell templates to speed up creation. Copy them, fill in the fields, and save to the appropriate folder.

---

## Appendix: When to Extract Each Primitive Type

| Primitive | Extract If | Don't Extract If | Example |
|---|---|---|---|
| **Entity** | Specific proper noun mentioned multiple times | Generic references ("a company", "a person") | "Acme Corp", "John Doe" |
| **Concept** | Definition or abstract idea described | Just mentioned in passing | "Adaptive reuse converts existing buildings to new uses" |
| **Claim** | Atomic factual statement that can be true/false | Opinion not grounded in source, or too vague | "Acme was founded in 2010", "Claude achieves 95% accuracy" |
| **Procedure** | Step-by-step instructions or workflow | Casual mention of a process | "Steps to deploy: 1) ..., 2) ..., 3) ..." |
| **Question** | An open uncertainty or research gap | A resolved issue | "How should contradictions be detected?", "What's the best way to...?" |
