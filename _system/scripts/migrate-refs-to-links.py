#!/usr/bin/env python3
"""
One-shot migration: convert bare page-reference IDs in frontmatter to Obsidian
wikilinks so Obsidian actually resolves them.

Only the "soft" reference fields are converted — the ones used for grounding /
display, never for exact-ID resolution in compile.py:

    sourcePages, derivedClaims, relatedPages, relatedClaims

Structural reference fields are intentionally LEFT ALONE because compile.py
matches them by exact ID (wrapping them would break resolution):

    parentSourceId, subjectPageId, sourceIds, sourceParts, evidence[].sourceId

Each bare ID  "source.2026-05-12.transcript.foo"  becomes
    "[[2026-05-12-transcript-foo|source.2026-05-12.transcript.foo]]"
keeping the dotted ID visible as display text while linking to the real file.

Idempotent: already-wrapped [[...]] values are left untouched, so re-running is
safe. Use --dry-run to preview, --write to apply.

    python3 _system/scripts/migrate-refs-to-links.py --dry-run
    python3 _system/scripts/migrate-refs-to-links.py --write
"""

import argparse
import re
import sys
from pathlib import Path

CONVERT_FIELDS = ("sourcePages", "derivedClaims", "relatedPages", "relatedClaims")

# folders that hold pages with frontmatter we care about
PAGE_FOLDERS = ("sources", "entities", "concepts", "claims", "questions", "syntheses")


def id_to_filename(page_id: str) -> str:
    if page_id.startswith("source."):
        return page_id[len("source."):].replace(".", "-") + ".md"
    return page_id.replace(".", "-") + ".md"


def id_to_link_target(page_id: str) -> str:
    return id_to_filename(page_id)[:-len(".md")]


def ref_to_wikilink(value: str) -> str:
    text = value.strip().strip('"').strip("'").strip()
    if not text or text.startswith("[["):
        return text
    return f"[[{id_to_link_target(text)}|{text}]]"


# matches a YAML inline-list line:  key: ["a", "b"]   or   key: [a, b]   or  key: []
INLINE_LIST = re.compile(r"^(\s*)([A-Za-z0-9_]+):\s*\[(.*)\]\s*$")
# matches a block-list item:  - value
BLOCK_ITEM = re.compile(r"^(\s*)-\s+(.*?)\s*$")
KEY_LINE = re.compile(r"^(\s*)([A-Za-z0-9_]+):\s*$")


def split_inline_items(inner: str) -> list[str]:
    """Split an inline YAML list body on top-level commas (no nesting expected here)."""
    inner = inner.strip()
    if not inner:
        return []
    items, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        items.append("".join(buf).strip())
    return [i for i in items if i != ""]


def requote(item: str) -> str:
    """Quote a converted value for inline YAML (wikilinks contain [ ] | so always quote)."""
    return '"' + ref_to_wikilink(item).replace('"', '\\"') + '"'


def migrate_frontmatter(text: str) -> tuple[str, int]:
    """Return (new_text, num_values_changed). Operates only on the frontmatter block."""
    if not text.startswith("---"):
        return text, 0
    end = text.find("\n---", 3)
    if end == -1:
        return text, 0
    fm = text[: end + 4]
    rest = text[end + 4 :]

    lines = fm.splitlines()
    out: list[str] = []
    changed = 0
    i = 0
    active_block_field: str | None = None

    while i < len(lines):
        line = lines[i]

        # inline list:  field: [ ... ]
        m = INLINE_LIST.match(line)
        if m and m.group(2) in CONVERT_FIELDS:
            indent, key, inner = m.group(1), m.group(2), m.group(3)
            items = split_inline_items(inner)
            new_items = []
            for it in items:
                conv = requote(it)
                if conv.strip('"') != it.strip().strip('"').strip("'"):
                    changed += 1
                new_items.append(conv)
            out.append(f"{indent}{key}: [{', '.join(new_items)}]")
            active_block_field = None
            i += 1
            continue

        # block list header:  field:
        km = KEY_LINE.match(line)
        if km:
            active_block_field = km.group(2) if km.group(2) in CONVERT_FIELDS else None
            out.append(line)
            i += 1
            continue

        # block list item under an active field:  - value
        bm = BLOCK_ITEM.match(line)
        if bm and active_block_field is not None:
            indent, val = bm.group(1), bm.group(2)
            conv = ref_to_wikilink(val.strip().strip('"').strip("'"))
            if conv != val.strip().strip('"').strip("'"):
                changed += 1
            out.append(f'{indent}- "{conv}"')
            i += 1
            continue

        # any other key resets block context
        if re.match(r"^\s*[A-Za-z0-9_]+:", line):
            active_block_field = None
        out.append(line)
        i += 1

    return "\n".join(out) + rest, changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="Vault root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true", help="Preview without writing")
    ap.add_argument("--write", action="store_true", help="Apply changes in place")
    args = ap.parse_args()

    if not args.dry_run and not args.write:
        ap.error("specify --dry-run or --write")

    root = Path(args.root).resolve()
    total_files, changed_files, total_vals = 0, 0, 0

    for folder in PAGE_FOLDERS:
        base = root / folder
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            total_files += 1
            original = path.read_text(encoding="utf-8")
            new_text, n = migrate_frontmatter(original)
            if n and new_text != original:
                changed_files += 1
                total_vals += n
                print(f"  {path.relative_to(root)}  (+{n})")
                if args.write:
                    path.write_text(new_text, encoding="utf-8")

    mode = "WROTE" if args.write else "DRY-RUN"
    print(f"\n[{mode}] scanned {total_files} files, "
          f"{changed_files} changed, {total_vals} references converted.")
    if not args.write and changed_files:
        print("Re-run with --write to apply.")


if __name__ == "__main__":
    main()
