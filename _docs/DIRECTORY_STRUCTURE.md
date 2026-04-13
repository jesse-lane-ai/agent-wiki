# Agentics Vault: Directory & File Structure

This document provides a human-readable overview of every file and folder in the `agent_wiki` repository. It explains the purpose of each directory and the contents of the root-level configuration and specification files.

## Core Content Directories (The Knowledge Graph)
These folders contain the actual data, relationships, and nodes that make up the vault. Markdown pages inside these folders must adhere strictly to the V1 schema.

- **`sources/`**: Holds `source` pages. Represents information origins (e.g., webpages, PDFs, datasets, transcripts, meeting notes). This is the canonical home for verified facts.
- **`entities/`**: Holds `entity` pages. Represents durable things (e.g., people, organizations, products, projects, systems).
- **`concepts/`**: Holds `concept` pages. Stores abstract ideas such as definitions, frameworks, policies, and principles.
- **`syntheses/`**: Holds `synthesis` pages. Contains cross-source rollups, overview documents, and analyses that aggregate ideas from multiple raw sources.
- **`procedures/`**: Holds `procedure` pages. Action-oriented workflows, playbooks, runbooks, and checklists.
- **`decisions/`**: Holds `decision` pages. Keeps a historical log of schema definitions, resolutions, or architectural choices made over time.
- **`questions/`**: Holds `question` pages. Tracks unresolved uncertainties, research gaps, and active inquiries.
- **`reports/`**: Holds `report` pages. Auto-generated dashboards and maintenance views (e.g., stale pages, open questions, claim health). *Note: These are outputs compiled from the graph, not sources of truth.*

## System & Infrastructure Directories
These folders start with an underscore (`_`) to separate them from the primary ontology. They handle system operations, routing, caches, and raw assets.

- **`_wiki/`**: The compiler core. Contains `compile.py` and the generated `cache/` and `indexes/` directories where the machine-facing artifacts (`pages.json`, `claims.jsonl`, etc.) are written. *Do not hand-edit files inside the cache.*
- **`_inbox/`**: The raw item intake queue. Unstructured or newly added data items land here as minimal pointer files before they are processed, triaged, and codified into official `sources/`.
- **`_attachments/`**: A storage folder for binary assets like PDFs, images, code snippets, or raw files referenced by other wiki pages.
- **`_archive/`**: A dead-letter storage area for deprecated, discarded, or obsolete pages that are no longer actively maintained.
- **`_procedures/`**: System-level procedures tracking meta-workflows specific to managing the vault infrastructure itself.
- **`_views/`**: Designed to hold reusable layout helpers and templates.
- **`_docs/`**: Houses general structural and repository documentation (including this very file).

## Root Configuration & Specifications
The root directory holds the schema definitions, behavior contracts, and entry points for navigating the setup.

- **`index.md`**: The primary entry point and homepage for traversing the vault's structured contents.
- **`README.md`**: High-level repository introduction, getting started guide, and compile-flow instruction.
- **`WIKI.md`**: The human-centric guide to the knowledge graph. Explains the frontmatter schema, available page types, and editorial rules.
- **`AGENTS.md`**: The strict behavioral contract for AI agents. Defines what they can read, write, and rewrite, enforcing the "managed-block" standard to preserve human prose.
- **`AGENT-WIKI-SPEC-v1.md`**: The full technical specification of the V1 ontology. Serves as the ultimate source of truth for schema validation and programmatic operations.
- **`INBOX.md`**: Details the processing lifecycle and exact YAML pointer format for any unstructured items landing in the `_inbox/` directory.
- **`INITIALIZE.md`**: Explains the structural philosophy and suggested build sequence of the vault, detailing what is explicitly in and out of scope for V1.
