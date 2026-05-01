#!/usr/bin/env python3
"""
Deterministic root page catalog writer for the Agentics vault.

Usage:
    python3 _system/scripts/index.py --write
    python3 _system/scripts/index.py --check
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


PAGES_CACHE = Path("_system/cache/pages.json")
INDEX_PATH = Path("index.md")
LOG_SCRIPT = Path("_system/scripts/log.py")
PAGE_TYPE_ORDER = ["source", "entity", "concept", "claim", "synthesis", "question", "index", "report"]
PAGE_TYPE_LABELS = {
    "source": "Sources",
    "entity": "Entities",
    "concept": "Concepts",
    "claim": "Claims",
    "synthesis": "Syntheses",
    "question": "Questions",
    "index": "Index",
    "report": "Reports",
}


def load_pages(vault_root: Path) -> list[dict[str, Any]]:
    pages_path = vault_root / PAGES_CACHE
    if not pages_path.exists():
        raise FileNotFoundError(f"Missing {PAGES_CACHE}; run compile first.")

    data = json.loads(pages_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError(f"{PAGES_CACHE} must contain a list under `pages`.")
    return [page for page in pages if isinstance(page, dict)]


def markdown_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def catalog_date(pages: list[dict[str, Any]]) -> str:
    dates = [
        str(page.get("updatedAt") or page.get("createdAt") or "")
        for page in pages
        if str(page.get("updatedAt") or page.get("createdAt") or "")
    ]
    return max(dates) if dates else date.today().isoformat()


def sorted_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        pages,
        key=lambda page: (
            str(page.get("pageType", "")),
            str(page.get("title", "")).casefold(),
            str(page.get("path", "")).casefold(),
        ),
    )


def render_table(pages: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Page | Path | Status | Updated |",
        "|---|---|---|---|",
    ]
    for page in sorted_pages(pages):
        title = str(page.get("title", "") or page.get("id", "") or page.get("path", ""))
        path = str(page.get("path", ""))
        status = page.get("status", "")
        updated_at = page.get("updatedAt", "")
        lines.append(
            "| "
            f"{markdown_escape(title)} | "
            f"`{markdown_escape(path)}` | "
            f"{markdown_escape(status)} | "
            f"{markdown_escape(updated_at)} |"
        )
    return lines


def render_index(pages: list[dict[str, Any]]) -> str:
    index_page = next((page for page in pages if page.get("path") == "index.md"), {})
    title = str(index_page.get("title") or "Page Catalog")
    status = str(index_page.get("status") or "active")
    updated_at = str(index_page.get("updatedAt") or catalog_date(pages))
    created_at = str(index_page.get("createdAt") or updated_at)
    aliases = index_page.get("aliases") or []
    tags = index_page.get("tags") or ["meta", "index"]

    lines = [
        "---",
        "id: meta.index",
        "pageType: index",
        f"title: {title}",
        f"status: {status}",
        f"createdAt: {created_at}",
        f"updatedAt: {updated_at}",
        "aliases:",
    ]
    if aliases:
        lines.extend(f"  - {alias}" for alias in aliases)
    else:
        lines[-1] = "aliases: []"
    lines.append("tags:")
    lines.extend(f"  - {tag}" for tag in tags)
    lines.extend([
        "---",
        "",
        "# Page Catalog",
        "",
        "Generated from `_system/cache/pages.json`.",
        "",
        "| Page Type | Count |",
        "|---|---:|",
    ])

    grouped: dict[str, list[dict[str, Any]]] = {}
    for page in pages:
        grouped.setdefault(str(page.get("pageType", "")), []).append(page)

    ordered_types = [page_type for page_type in PAGE_TYPE_ORDER if page_type in grouped]
    ordered_types.extend(sorted(page_type for page_type in grouped if page_type not in PAGE_TYPE_ORDER))

    for page_type in ordered_types:
        label = PAGE_TYPE_LABELS.get(page_type, page_type.title() or "Unknown")
        lines.append(f"| {markdown_escape(label)} | {len(grouped[page_type])} |")

    for page_type in ordered_types:
        label = PAGE_TYPE_LABELS.get(page_type, page_type.title() or "Unknown")
        lines.extend(["", f"## {label}", ""])
        lines.extend(render_table(grouped[page_type]))

    return "\n".join(lines).rstrip() + "\n"


def write_operational_log(vault_root: Path, message: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(vault_root / LOG_SCRIPT),
            "--vault-root",
            str(vault_root),
            "--message",
            message,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the deterministic root page catalog.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite index.md")
    mode.add_argument("--check", action="store_true", help="Fail if index.md is not current")
    parser.add_argument("--vault-root", default=".", help="Path to vault root (default: current directory)")
    parser.add_argument("--no-log", action="store_true", help="Do not write an operational log entry")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    pages = load_pages(vault_root)
    rendered = render_index(pages)
    index_path = vault_root / INDEX_PATH
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    if args.check:
        if existing != rendered:
            print("index.md is out of date")
            raise SystemExit(1)
        print("index.md is current")
        return

    if existing == rendered:
        print("index.md is current")
        return

    index_path.write_text(rendered, encoding="utf-8")
    print("Wrote index.md")
    if not args.no_log:
        write_operational_log(vault_root, f"index: regenerated root page catalog; pages={len(pages)}")


if __name__ == "__main__":
    main()
