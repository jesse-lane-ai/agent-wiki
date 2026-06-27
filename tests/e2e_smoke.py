#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT_FILES = (
    "AGENTS.md",
    "WIKI.md",
    "README.md",
    "ONBOARD.md",
    "INBOX.md",
    "AGENT-WIKI-SPEC-v2.md",
)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_root = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="agent-wiki-e2e-"))
    run_root.mkdir(parents=True, exist_ok=True)

    vault_root = run_root / "vault-wiki"
    workspace_root = run_root / "workspace"
    workspace_wiki = workspace_root / "wiki"

    run([sys.executable, "-m", "agent_wiki.cli", "init", "--type", "vault", "--root", str(vault_root), "--write-config"])
    run([
        sys.executable,
        "-m",
        "agent_wiki.cli",
        "init",
        "--type",
        "workspace",
        "--workspace-root",
        str(workspace_root),
        "--wiki-dir",
        "wiki",
        "--write-config",
    ])

    install_template_files(vault_root)
    install_template_files(workspace_wiki)

    vault_sources = process_vault_sources(vault_root, [Path(path) for path in args.vault_raw])
    workspace_sources = process_workspace_sources(
        workspace_root=workspace_root,
        workspace_wiki=workspace_wiki,
        source_workspace_root=Path(args.workspace_root) if args.workspace_root else None,
        workspace_files=args.workspace_file,
    )

    run([sys.executable, "skills/compile-wiki/scripts/compile.py"], cwd=vault_root)
    run([sys.executable, "skills/compile-wiki/scripts/compile.py"], cwd=workspace_wiki)
    vault_doctor = json.loads(
        run(
            [
                sys.executable,
                "-m",
                "agent_wiki.cli",
                "doctor",
                "--wiki-root",
                str(vault_root),
                "--type",
                "vault",
                "--json",
            ],
            capture=True,
        )
    )
    workspace_doctor = json.loads(
        run(
            [
                sys.executable,
                "-m",
                "agent_wiki.cli",
                "doctor",
                "--wiki-root",
                str(workspace_wiki),
                "--type",
                "workspace",
                "--json",
            ],
            capture=True,
        )
    )

    summary = {
        "runRoot": str(run_root),
        "vault": {
            "root": str(vault_root),
            "doctorIssues": vault_doctor,
            "sourcePages": sorted(str(path.relative_to(vault_root)) for path in (vault_root / "sources").glob("*.md")),
            "rawFiles": sorted(str(path.relative_to(vault_root)) for path in (vault_root / "raw").glob("*") if path.is_file()),
            "inboxRemaining": sorted(str(path.relative_to(vault_root)) for path in (vault_root / "_inbox").glob("*") if path.is_file()),
            "validationIssues": read_json(vault_root / "_system" / "cache" / "validation-issues.json"),
            "promoted": vault_sources,
        },
        "workspace": {
            "root": str(workspace_root),
            "wiki": str(workspace_wiki),
            "doctorIssues": workspace_doctor,
            "sourcePages": sorted(str(path.relative_to(workspace_wiki)) for path in (workspace_wiki / "sources").glob("*.md")),
            "hasInbox": (workspace_wiki / "_inbox").exists(),
            "hasRaw": (workspace_wiki / "raw").exists(),
            "pendingAfter": read_json(run_root / "workspace-pending-after.json"),
            "validationIssues": read_json(workspace_wiki / "_system" / "cache" / "validation-issues.json"),
            "promoted": workspace_sources,
        },
    }
    summary_path = run_root / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run temp-only Agent Wiki e2e smoke tests.")
    parser.add_argument("--vault-raw", action="append", default=[], help="Raw source file to copy into temp vault _inbox. Repeatable.")
    parser.add_argument("--workspace-root", help="Source workspace root used to resolve --workspace-file values.")
    parser.add_argument(
        "--workspace-file",
        action="append",
        default=[],
        help="Workspace-relative file to copy into the temp workspace and promote. Repeatable.",
    )
    parser.add_argument("--output-dir", help="Optional output directory. Defaults to a new /tmp/agent-wiki-e2e-* directory.")
    args = parser.parse_args(argv)
    if not args.vault_raw:
        parser.error("provide at least one --vault-raw file")
    if not args.workspace_root:
        parser.error("provide --workspace-root")
    if not args.workspace_file:
        parser.error("provide at least one --workspace-file")
    return args


def install_template_files(wiki_root: Path) -> None:
    for file_name in TEMPLATE_ROOT_FILES:
        shutil.copy2(REPO_ROOT / file_name, wiki_root / file_name)
    shutil.copytree(REPO_ROOT / "_system" / "scripts", wiki_root / "_system" / "scripts", dirs_exist_ok=True)
    shutil.copytree(REPO_ROOT / "skills", wiki_root / "skills", dirs_exist_ok=True)


def process_vault_sources(vault_root: Path, raw_files: list[Path]) -> list[dict[str, Any]]:
    promoted: list[dict[str, Any]] = []
    for raw_file in raw_files:
        if not raw_file.is_file():
            raise SystemExit(f"Missing vault raw file: {raw_file}")
        inbox_path = vault_root / "_inbox" / raw_file.name
        raw_path = vault_root / "raw" / raw_file.name
        shutil.copy2(raw_file, inbox_path)
        slug = slug_from_raw_name(raw_file.stem)
        source_date = date_from_name(raw_file.name) or today()
        title = title_from_slug(slug)
        result = run(
            [
                sys.executable,
                "_system/scripts/create-page.py",
                "--type",
                "source",
                "--subtype",
                "document",
                "--slug",
                slug,
                "--title",
                title,
                "--source-date",
                source_date,
                "--retrieved-at",
                today(),
                "--origin-path",
                f"raw/{raw_file.name}",
                "--body-file",
                str(inbox_path.relative_to(vault_root)),
                "--no-log",
                "--compact",
            ],
            cwd=vault_root,
            capture=True,
        )
        shutil.move(str(inbox_path), raw_path)
        promoted.append(json.loads(result))
    return promoted


def process_workspace_sources(
    *,
    workspace_root: Path,
    workspace_wiki: Path,
    source_workspace_root: Path | None,
    workspace_files: list[str],
) -> list[dict[str, Any]]:
    if source_workspace_root is None:
        raise SystemExit("--workspace-root is required")
    promoted: list[dict[str, Any]] = []
    for relative in workspace_files:
        source_path = source_workspace_root / relative
        if not source_path.is_file():
            raise SystemExit(f"Missing workspace file: {source_path}")
        temp_path = workspace_root / relative
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, temp_path)

    run(
        [
            sys.executable,
            "-m",
            "agent_wiki.cli",
            "workspace",
            "pending",
            "--workspace-root",
            str(workspace_root),
            "--wiki-dir",
            "wiki",
            "--json",
        ],
        capture=True,
    )

    for relative in workspace_files:
        source_path = workspace_root / relative
        slug = slug_from_workspace_path(relative)
        source_date = today()
        title = title_from_slug(slug)
        result = json.loads(
            run(
                [
                    sys.executable,
                    "_system/scripts/create-page.py",
                    "--type",
                    "source",
                    "--subtype",
                    "document",
                    "--slug",
                    slug,
                    "--title",
                    title,
                    "--source-date",
                    source_date,
                    "--retrieved-at",
                    today(),
                    "--origin-path",
                    relative,
                    "--body-file",
                    str(source_path),
                    "--no-log",
                    "--compact",
                ],
                cwd=workspace_wiki,
                capture=True,
            )
        )
        run(
            [
                sys.executable,
                "-m",
                "agent_wiki.cli",
                "workspace",
                "mark-sourced",
                "--workspace-root",
                str(workspace_root),
                "--wiki-dir",
                "wiki",
                "--path",
                relative,
                "--source-id",
                result["id"],
                "--source-path",
                result["path"],
            ]
        )
        promoted.append(result)

    pending_after = run(
        [
            sys.executable,
            "-m",
            "agent_wiki.cli",
            "workspace",
            "pending",
            "--workspace-root",
            str(workspace_root),
            "--wiki-dir",
            "wiki",
            "--json",
        ],
        capture=True,
    )
    (workspace_root.parent / "workspace-pending-after.json").write_text(pending_after, encoding="utf-8")
    return promoted


def run(args: list[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    proc = subprocess.run(
        args,
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"Command failed ({proc.returncode}): {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    if capture:
        return proc.stdout
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.stdout


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def today() -> str:
    return date.today().isoformat()


def date_from_name(name: str) -> str | None:
    parts = name[:10].split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return name[:10]
    return None


def slug_from_raw_name(stem: str) -> str:
    if date_from_name(stem):
        stem = stem[11:]
    if stem.endswith("-original"):
        stem = stem[: -len("-original")]
    return normalize_slug(stem)


def slug_from_workspace_path(relative: str) -> str:
    path = Path(relative)
    parts = [part for part in path.with_suffix("").parts if part not in {".", ""}]
    return normalize_slug("-".join(parts[-3:]))


def normalize_slug(value: str) -> str:
    cleaned = []
    last_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            last_dash = False
        elif not last_dash:
            cleaned.append("-")
            last_dash = True
    return "".join(cleaned).strip("-") or "source"


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
