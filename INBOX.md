## `_inbox/` Raw Intake

`INBOX.md` is now only a navigation pointer.

For the durable inbox/raw lifecycle rules, read [[WIKI#14 Inbox intake strategy]].

For the operational workflow, run the local `process-inbox` skill:

```text
Read AGENTS.md, then run skills/process-inbox/SKILL.md.
```

The short version:

- `_inbox/` is the active raw drop zone.
- `process-inbox` promotes retained items into canonical `sources/` pages with `agent-wiki create-page`.
- Promoted originals move to `raw/`.
- Failed or discarded items stay in `_inbox/` or move to `_inbox/trash/` only when explicitly discarded.
- `_inbox/` and `raw/` are not canonical evidence; canonical source material lives in `sources/`.
