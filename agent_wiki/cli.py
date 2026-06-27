from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import load_config
from .lifecycle import doctor_wiki, init_wiki, issues_to_json, issues_to_text
from .workspace import (
    WorkspaceFile,
    default_workspace_root,
    files_to_json,
    files_to_text,
    load_state,
    mark_sourced,
    scan_workspace,
    update_state_from_scan,
    wiki_root_for_workspace,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-wiki")
    parser.add_argument("--root", default=".", help="Agent Wiki root or config root.")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="Initialize a vault or workspace wiki folder skeleton.")
    init.add_argument("--type", choices=("vault", "workspace"), required=True, help="Wiki operating mode.")
    init.add_argument("--root", dest="init_root", help="Vault wiki root, or workspace root if --type workspace.")
    init.add_argument("--workspace-root", help="Workspace root for workspace mode.")
    init.add_argument("--wiki-dir", default="wiki", help="Wiki directory inside workspace roots.")
    init.add_argument("--write-config", action="store_true", help="Write local _system/config.json.")
    init.add_argument("--with-template", action="store_true", help="Copy bundled docs, scripts, and skills into the wiki if missing.")
    init.set_defaults(func=cmd_init)

    doctor = subparsers.add_parser("doctor", help="Check wiki folder/config health without mutating files.")
    doctor.add_argument("--wiki-root", help="Wiki root to inspect. Defaults to --root.")
    doctor.add_argument("--type", choices=("vault", "workspace"), help="Expected wiki operating mode.")
    doctor.add_argument("--json", action="store_true", help="Emit JSON issues.")
    doctor.set_defaults(func=cmd_doctor)

    workspace = subparsers.add_parser("workspace", help="Workspace-mode discovery commands.")
    workspace_sub = workspace.add_subparsers(dest="workspace_command")

    scan = workspace_sub.add_parser("scan", help="Scan workspace files outside the wiki directory.")
    add_workspace_args(scan)
    scan.add_argument("--write-state", action="store_true", help="Persist scan metadata to the wiki state file.")
    scan.set_defaults(func=cmd_workspace_scan)

    pending = workspace_sub.add_parser("pending", help="List new or changed workspace files for agent processing.")
    add_workspace_args(pending)
    pending.set_defaults(func=cmd_workspace_pending)

    mark = workspace_sub.add_parser("mark-sourced", help="Record that a workspace file is represented by a source page.")
    mark.add_argument("--workspace-root", help="Workspace root. Defaults to configured workspace root or cwd.")
    mark.add_argument("--wiki-dir", help="Wiki directory inside the workspace. Defaults to configured value or wiki.")
    mark.add_argument("--path", required=True, help="Workspace-relative path to the original file.")
    mark.add_argument("--source-id", required=True, help="Canonical source page ID.")
    mark.add_argument("--source-path", required=True, help="Wiki-relative path to the source page.")
    mark.set_defaults(func=cmd_workspace_mark_sourced)

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    result = init_wiki(
        wiki_type=args.type,
        root=args.init_root or args.root,
        workspace_root=args.workspace_root,
        wiki_dir=args.wiki_dir,
        write_config=args.write_config,
        with_template=args.with_template,
    )
    print(f"Initialized {result.wiki_type} wiki at {result.wiki_root}")
    if result.workspace_root:
        print(f"Workspace root: {result.workspace_root}")
    print(f"Created folders: {len(result.created)}")
    if result.config_written:
        print("Wrote _system/config.json")
    if result.template_copied:
        print(f"Copied template files: {len(result.template_copied)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    wiki_root = Path(args.wiki_root or args.root)
    issues = doctor_wiki(wiki_root=wiki_root, wiki_type=args.type)
    print(issues_to_json(issues) if args.json else issues_to_text(issues))
    return 1 if any(issue.level == "error" for issue in issues) else 0


def add_workspace_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace-root", help="Workspace root to scan. Defaults to configured workspace root or cwd.")
    parser.add_argument("--wiki-dir", help="Wiki directory inside the workspace. Defaults to configured value or wiki.")
    parser.add_argument("--json", action="store_true", help="Emit agent-readable JSON.")
    parser.add_argument("--since-hours", type=float, help="Only include files modified in the last N hours.")


def cmd_workspace_scan(args: argparse.Namespace) -> int:
    files, wiki_root = _workspace_files(args, include_unchanged=True)
    if args.write_state:
        state = load_state(wiki_root)
        update_state_from_scan(wiki_root, files, state)
    print(files_to_json(files) if args.json else files_to_text(files))
    return 0


def cmd_workspace_pending(args: argparse.Namespace) -> int:
    files, _wiki_root = _workspace_files(args, include_unchanged=False)
    print(files_to_json(files) if args.json else files_to_text(files))
    return 0


def cmd_workspace_mark_sourced(args: argparse.Namespace) -> int:
    config = load_config(args.root)
    explicit_workspace_root = Path(args.workspace_root) if args.workspace_root else None
    workspace_root = default_workspace_root(config, explicit_workspace_root)
    wiki_dir = args.wiki_dir or config.wiki_dir
    wiki_root = wiki_root_for_workspace(workspace_root, wiki_dir)
    state = load_state(wiki_root)
    mark_sourced(
        wiki_root,
        state,
        relative_path=args.path,
        source_id=args.source_id,
        source_path=args.source_path,
    )
    print(f"Mapped {args.path} -> {args.source_id}")
    return 0


def _workspace_files(args: argparse.Namespace, *, include_unchanged: bool) -> tuple[list[WorkspaceFile], Path]:
    config = load_config(args.root)
    explicit_workspace_root = Path(args.workspace_root) if args.workspace_root else None
    workspace_root = default_workspace_root(config, explicit_workspace_root)
    wiki_dir = args.wiki_dir or config.wiki_dir
    wiki_root = wiki_root_for_workspace(workspace_root, wiki_dir)
    state = load_state(wiki_root)
    since = _since(args)
    files = scan_workspace(workspace_root, wiki_root, config.workspace_scan, since=since, state=state)
    if not include_unchanged:
        files = [item for item in files if item.reason != "unchanged"]
    return files, wiki_root


def _since(args: argparse.Namespace) -> datetime | None:
    if args.since_hours is None:
        return None
    return datetime.now(timezone.utc) - timedelta(hours=args.since_hours)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
