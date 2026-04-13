## `_inbox/` Pointer Schema

Inbox pointer files are simple tracking records for raw items that landed in `_inbox/` and still need to be processed into canonical `source` pages.
### Folder meaning

- `_inbox/` = active queue
- `_inbox/trash/` = discarded or inactive inbox items
### Required fields

- `id`: unique inbox item ID
- `source`: pointer to the raw item
- `status`: processing state
### Allowed `status` values

- `unprocessed`
- `processing`
- `processed`
- `failed`
- `ignored`
- `trashed`
### Minimal example

```yaml
id: 2026-04-12-inbox-2042925773300908103
source: source/2042925773300908103
status: unprocessed
```
### Trash rule

When an item is confirmed as processed change it's status to `processed` and move it to the trash.

Items moved to `_inbox/trash/` SHOULD use one of these statuses:

- `ignored`
- `failed`
- `trashed`
- `processed`

`trashed` is the clearest status when the file is physically moved into `_inbox/trash/`.
### Notes

- `_inbox` pointer files are not canonical `source` pages.
- The `source` field replaces the old `evidence` field.
- When processing is complete, the item should be turned into a canonical page under `sources/`.
- Items in `_inbox/trash/` are no longer part of the active processing queue.