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
11. Generate required reports
12. Add contradiction/question caches

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

The v1 model is built on three layers:

### The vault is the container
Markdown pages, folders, human notes, and generated blocks.

### The ontology is the truth model
Entities, concepts, sources, claims, evidence, relations, contradictions, questions, syntheses, and procedures.

### The compile layer is the bridge
Stable machine-facing cache files and generated maintenance reports.

That is the v1 contract.

It is strict enough to be machine-usable, but still readable and workable as a markdown-first wiki.

---

## Core principle

The wiki should separate:

- **what exists**  
- **what is claimed**  
- **what supports it**  
- **what conflicts with it**  
- **what is still unknown**  
- **how everything connects**  
- **how agents consume it**

That gives you a wiki that is both:
- readable by humans
- dependable for agents
