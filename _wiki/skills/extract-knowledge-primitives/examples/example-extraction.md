# Example Extraction Notes

Canonical extraction examples live in [[AGENT-WIKI-SPEC-v1]]. This file is intentionally limited to extraction judgment notes so schema examples do not drift from the spec.

## Atomic Claims

```text
Source text:
"Acme Corp was founded in 2010 and is based in San Francisco."

Extract:
- claim.historical.acme-founded-2010
- claim.descriptive.acme-based-in-san-francisco

Do not extract:
- One compound claim that combines founding date and headquarters.
```

## Evidence Strength

```text
Source text:
"The company says Claude 4.5 improves code generation accuracy."

Extract:
- The source reports that the company claims Claude 4.5 improves code generation accuracy.

Avoid:
- Treating the company's claim as independently verified performance evidence.
```

## Entity Versus Concept

```text
Source text:
"Riverside Community Garden uses adaptive reuse principles in its greenhouse plan."

Extract entity:
- entity.place.riverside-community-garden

Extract concept:
- concept.principle.adaptive-reuse
```

## Question Extraction

```text
Source text:
"An open question is whether duplicate entities should be merged automatically or reviewed manually."

Extract:
- question.data.entity-merge-review-policy
```

For actual frontmatter shape, allowed fields, ID conventions, relation predicates, and confidence semantics, use [[AGENT-WIKI-SPEC-v1]].
