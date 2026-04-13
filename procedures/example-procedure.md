---
id: procedure.example.onboard-new-source
pageType: procedure
title: Onboard a New Source
procedureType: workflow
status: active
createdAt: 2026-04-13
updatedAt: 2026-04-13
aliases: []
tags:
  - example
---

# Onboard a New Source

This is an example procedure page representing action-oriented instructions.

## Steps

1. Drop the raw file into `_inbox/` and create a pointer file with `status: UNPROCESSED`
2. Run the process-new-notes skill to promote it to a canonical `source` page
3. Run the compile pipeline to update the caches
