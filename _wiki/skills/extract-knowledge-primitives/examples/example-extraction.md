# Example: Extracting Knowledge Primitives from a Source

## Before: Raw Source Page

**File:** `sources/claude-ai-announcement.md`

```yaml
---
id: source.2026-04-15.claude-ai-announcement
pageType: source
title: Anthropic Announces Claude 4.5
status: processed
sourceType: article
originUrl: https://example.com/claude-45-announcement
publishedAt: 2026-04-01
retrievedAt: 2026-04-15
createdAt: 2026-04-15
updatedAt: 2026-04-15
aliases: []
tags:
  - ai
  - anthropic
attachments: []
---

# Anthropic Announces Claude 4.5

Anthropic, founded by Darian Amodei and Daniela Amodei in 2021, has announced 
Claude 4.5, the latest version of its AI assistant. Claude 4.5 is built on a 
new architecture that uses transformers and reinforcement learning from human feedback (RLHF).

The company says Claude 4.5 improves on Claude 4.0 in three key areas: reasoning 
speed, code generation accuracy, and safety. The model achieves 95% accuracy on 
standard benchmarks, up from 92% in the previous version.

Darian Amodei stated: "We believe that AI safety is the most important 
challenge in AI development. Claude 4.5 represents a significant step forward 
in building safe, interpretable systems."

The Claude API will be available starting April 15, 2026. Pricing is 
$0.003 per 1K input tokens and $0.015 per 1K output tokens.
```

---

## After: Extracted Primitives

Based on the source above, an agent would extract the following:

### Extracted Entity: Anthropic

**File:** `entities/anthropic.md`

```yaml
---
id: entity.organization.anthropic
pageType: entity
title: Anthropic
entityType: organization
canonicalName: Anthropic
status: active
createdAt: 2026-04-15
updatedAt: 2026-04-15
aliases:
  - Anthropic Inc
tags:
  - extracted
  - ai
  - companies
relatedPages:
  - entity.person.darian-amodei
  - entity.person.daniela-amodei
  - entity.product.claude-ai
relations:
  - subject: entity.organization.anthropic
    predicate: founded_by
    object: entity.person.darian-amodei
    confidence: 0.85
    sourceClaimIds:
      - claim.anthropic.founded-by-darian-amodei
  - subject: entity.organization.anthropic
    predicate: produces
    object: entity.product.claude-ai
    confidence: 0.90
    sourceClaimIds:
      - claim.anthropic.produces-claude
---

# Anthropic

AI safety research company focused on building safe, interpretable AI systems.
```

### Extracted Entity: Claude (Product)

**File:** `entities/claude-product.md`

```yaml
---
id: entity.product.claude-ai
pageType: entity
title: Claude
entityType: product
canonicalName: Claude
status: active
createdAt: 2026-04-15
updatedAt: 2026-04-15
aliases:
  - Claude AI
  - Claude API
tags:
  - extracted
  - ai
relatedPages:
  - entity.organization.anthropic
relations:
  - subject: entity.product.claude-ai
    predicate: owned_by
    object: entity.organization.anthropic
    confidence: 0.90
    sourceClaimIds: []
---

# Claude

AI assistant developed by Anthropic, available via API and web interface.
```

### Extracted Entity: People

**File:** `entities/darian-amodei.md`

```yaml
---
id: entity.person.darian-amodei
pageType: entity
title: Darian Amodei
entityType: person
canonicalName: Darian Amodei
status: active
createdAt: 2026-04-15
updatedAt: 2026-04-15
aliases: []
tags:
  - extracted
relatedPages:
  - entity.organization.anthropic
---

# Darian Amodei

CEO and co-founder of Anthropic.
```

### Extracted Concept: RLHF (Reinforcement Learning from Human Feedback)

**File:** `concepts/reinforcement-learning-from-human-feedback.md`

```yaml
---
id: concept.method.rlhf
pageType: concept
title: Reinforcement Learning from Human Feedback
conceptType: method
status: active
createdAt: 2026-04-15
updatedAt: 2026-04-15
aliases:
  - RLHF
tags:
  - extracted
  - ai
  - ml-techniques
---

# Reinforcement Learning from Human Feedback (RLHF)

A machine learning technique where models are trained using feedback from humans,
rather than automated reward signals. Used to improve alignment and safety of AI systems.
```

### Extracted Claims

**File:** `claims/anthropic-founded-2021.md`

```yaml
---
id: claim.anthropic.founded-2021
pageType: claim
title: Anthropic was founded in 2021
claimType: historical
status: unverified
confidence: 0.70
text: Anthropic was founded in 2021
subjectPageId: entity.organization.anthropic
sourceIds:
  - source.2026-04-15.claude-ai-announcement
evidence:
  - id: ev.anthropic.founded-2021.01
    sourceId: source.2026-04-15.claude-ai-announcement
    path: sources/claude-ai-announcement.md
    kind: quote
    relation: supports
    weight: 0.75
    excerpt: "Anthropic, founded by Darian Amodei and Daniela Amodei in 2021"
    retrievedAt: 2026-04-15
    updatedAt: 2026-04-15
createdAt: 2026-04-15
updatedAt: 2026-04-15
tags:
  - extracted
---

# Anthropic was founded in 2021

Extracted from [[2026-04-15-claude-ai-announcement|Claude Announcement]].
```

**File:** `claims/claude-45-improves-on-claude-40.md`

```yaml
---
id: claim.claude.45-improves-40
pageType: claim
title: Claude 4.5 improves on Claude 4.0 in reasoning speed, code generation accuracy, and safety
claimType: descriptive
status: unverified
confidence: 0.70
text: Claude 4.5 improves on Claude 4.0 in reasoning speed, code generation accuracy, and safety
subjectPageId: entity.product.claude-ai
sourceIds:
  - source.2026-04-15.claude-ai-announcement
evidence:
  - id: ev.claude.45-improves.01
    sourceId: source.2026-04-15.claude-ai-announcement
    path: sources/claude-ai-announcement.md
    kind: quote
    relation: supports
    weight: 0.75
    excerpt: "Claude 4.5 improves on Claude 4.0 in three key areas: reasoning speed, code generation accuracy, and safety"
    retrievedAt: 2026-04-15
    updatedAt: 2026-04-15
createdAt: 2026-04-15
updatedAt: 2026-04-15
tags:
  - extracted
---

# Claude 4.5 improves on Claude 4.0

Extracted from [[2026-04-15-claude-ai-announcement|Claude Announcement]].
```

**File:** `claims/claude-45-accuracy.md`

```yaml
---
id: claim.claude.45-95-percent-accuracy
pageType: claim
title: Claude 4.5 achieves 95% accuracy on standard benchmarks
claimType: descriptive
status: unverified
confidence: 0.70
text: Claude 4.5 achieves 95% accuracy on standard benchmarks
subjectPageId: entity.product.claude-ai
sourceIds:
  - source.2026-04-15.claude-ai-announcement
evidence:
  - id: ev.claude.45-accuracy.01
    sourceId: source.2026-04-15.claude-ai-announcement
    path: sources/claude-ai-announcement.md
    kind: quote
    relation: supports
    weight: 0.75
    excerpt: "The model achieves 95% accuracy on standard benchmarks, up from 92% in the previous version"
    retrievedAt: 2026-04-15
    updatedAt: 2026-04-15
createdAt: 2026-04-15
updatedAt: 2026-04-15
tags:
  - extracted
---

# Claude 4.5 achieves 95% accuracy on standard benchmarks

Extracted from [[2026-04-15-claude-ai-announcement|Claude Announcement]].
```

---

## Updated Source Page

The original source page is updated with extraction metadata:

```yaml
---
id: source.2026-04-15.claude-ai-announcement
pageType: source
title: Anthropic Announces Claude 4.5
status: processed
sourceType: article
originUrl: https://example.com/claude-45-announcement
publishedAt: 2026-04-01
retrievedAt: 2026-04-15
createdAt: 2026-04-15
updatedAt: 2026-04-15
extractionStatus: extracted
extractedAt: 2026-04-15
extractedEntities:
  - entity.organization.anthropic
  - entity.product.claude-ai
  - entity.person.darian-amodei
  - entity.person.daniela-amodei
extractedConcepts:
  - concept.method.rlhf
extractedClaims:
  - claim.anthropic.founded-2021
  - claim.claude.45-improves-40
  - claim.claude.45-95-percent-accuracy
  - claim.anthropic.safety-priority
aliases: []
tags:
  - ai
  - anthropic
attachments: []
---

[Original content preserved exactly as-is...]
```

---

## Summary

This example shows:
1. **Entities extracted:** Anthropic (organization), Claude (product), Darian Amodei (person), Daniela Amodei (person)
2. **Concepts extracted:** RLHF (technique)
3. **Claims extracted:** 4 atomic propositions with evidence pointing back to the source
4. **Relations:** Ownership, founding, product relationships
5. **Metadata:** Source page marked as extracted with list of created primitives

All created pages follow the v1 schema, use stable IDs, and have claims marked `unverified` with `confidence: 0.70`. Evidence points back to the source page with exact excerpts.

The compile pipeline would then validate all these pages, extract the claims, and update the caches and reports.
