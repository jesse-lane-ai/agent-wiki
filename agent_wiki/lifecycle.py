from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import CONFIG_PATH, DEFAULT_WORKSPACE_WIKI_DIR, VALID_WIKI_TYPES


CONTENT_FOLDERS: tuple[str, ...] = (
    "sources",
    "sources/parts",
    "entities",
    "concepts",
    "claims",
    "syntheses",
    "questions",
    "_attachments",
    "_archive",
)
VAULT_RUNTIME_FOLDERS: tuple[str, ...] = (
    "_inbox",
    "_inbox/trash",
    "raw",
)
GENERATED_FOLDERS: tuple[str, ...] = (
    "reports",
    "_system/cache",
    "_system/indexes",
    "_system/logs",
    "_system/state",
)
SYSTEM_FOLDERS: tuple[str, ...] = (
    "_system/scripts",
    "skills",
)
REQUIRED_TEMPLATE_FILES: tuple[str, ...] = (
    "AGENTS.md",
    "WIKI.md",
    "README.md",
    "_system/scripts/create-page.py",
    "_system/scripts/onboard.py",
    "skills/compile-wiki/SKILL.md",
    "skills/extract-knowledge-primitives/SKILL.md",
)
TEMPLATE_ROOT_FILES: tuple[str, ...] = (
    "AGENTS.md",
    "WIKI.md",
    "README.md",
    "ONBOARD.md",
    "INBOX.md",
    "AGENT-WIKI-SPEC-v2.md",
)
TEMPLATE_DIRECTORIES: tuple[str, ...] = (
    "_system/scripts",
    "skills",
)
TEMPLATE_OPTIONAL_FILES: tuple[str, ...] = (
    "_system/config.example.json",
)


@dataclass(frozen=True)
class InitResult:
    wiki_type: str
    workspace_root: str | None
    wiki_root: str
    created: tuple[str, ...]
    config_written: bool
    template_copied: tuple[str, ...] = ()


@dataclass(frozen=True)
class DoctorIssue:
    level: str
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


def resolve_init_paths(
    *,
    wiki_type: str,
    root: Path | str | None = None,
    workspace_root: Path | str | None = None,
    wiki_dir: str = DEFAULT_WORKSPACE_WIKI_DIR,
) -> tuple[Path | None, Path]:
    if wiki_type not in VALID_WIKI_TYPES:
        raise ValueError(f"wiki_type must be one of: {', '.join(sorted(VALID_WIKI_TYPES))}")
    clean_wiki_dir = wiki_dir.strip().strip("/") or DEFAULT_WORKSPACE_WIKI_DIR
    if wiki_type == "workspace":
        workspace = Path(workspace_root or root or ".").resolve()
        return workspace, (workspace / clean_wiki_dir).resolve()
    return None, Path(root or ".").resolve()


def init_wiki(
    *,
    wiki_type: str,
    root: Path | str | None = None,
    workspace_root: Path | str | None = None,
    wiki_dir: str = DEFAULT_WORKSPACE_WIKI_DIR,
    write_config: bool = False,
    with_template: bool = False,
    template_root: Path | str | None = None,
) -> InitResult:
    workspace, wiki_root = resolve_init_paths(
        wiki_type=wiki_type,
        root=root,
        workspace_root=workspace_root,
        wiki_dir=wiki_dir,
    )
    created = create_required_folders(wiki_root, include_vault_runtime=wiki_type == "vault")
    config_written = False
    if write_config:
        write_local_config(wiki_root, wiki_type=wiki_type, workspace_root=workspace, wiki_dir=wiki_dir)
        config_written = True
    template_copied: tuple[str, ...] = ()
    if with_template:
        source_root = Path(template_root) if template_root is not None else default_template_root()
        template_copied = tuple(str(path) for path in copy_template_files(source_root=source_root, wiki_root=wiki_root))
    return InitResult(
        wiki_type=wiki_type,
        workspace_root=str(workspace) if workspace else None,
        wiki_root=str(wiki_root),
        created=tuple(str(path) for path in created),
        config_written=config_written,
        template_copied=template_copied,
    )


def create_required_folders(wiki_root: Path, *, include_vault_runtime: bool) -> list[Path]:
    folder_names = list(CONTENT_FOLDERS) + list(GENERATED_FOLDERS) + list(SYSTEM_FOLDERS)
    if include_vault_runtime:
        folder_names.extend(VAULT_RUNTIME_FOLDERS)
    created: list[Path] = []
    for name in folder_names:
        path = wiki_root / name
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    return created


def write_local_config(
    wiki_root: Path,
    *,
    wiki_type: str,
    workspace_root: Path | None,
    wiki_dir: str,
) -> None:
    config_path = wiki_root / CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_json(config_path) or {}
    existing["schemaVersion"] = 1
    existing["wikiType"] = wiki_type
    workspace = existing.get("workspace") if isinstance(existing.get("workspace"), dict) else {}
    workspace["root"] = str(workspace_root) if workspace_root else None
    workspace["wikiDir"] = wiki_dir.strip().strip("/") or DEFAULT_WORKSPACE_WIKI_DIR
    existing["workspace"] = workspace
    config_path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_template_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template_files(*, source_root: Path, wiki_root: Path) -> list[Path]:
    copied: list[Path] = []
    for name in TEMPLATE_ROOT_FILES + TEMPLATE_OPTIONAL_FILES:
        source = source_root / name
        if source.is_file():
            destination = wiki_root / name
            if copy_file_if_missing(source, destination):
                copied.append(destination)
    for name in TEMPLATE_DIRECTORIES:
        source = source_root / name
        if source.is_dir():
            copied.extend(copy_tree_if_missing(source, wiki_root / name))
    return copied


def copy_tree_if_missing(source: Path, destination: Path) -> list[Path]:
    copied: list[Path] = []
    for source_path in sorted(source.rglob("*")):
        if source_path.is_dir():
            continue
        relative = source_path.relative_to(source)
        destination_path = destination / relative
        if should_skip_template_file(relative):
            continue
        if copy_file_if_missing(source_path, destination_path):
            copied.append(destination_path)
    return copied


def should_skip_template_file(relative: Path) -> bool:
    return "__pycache__" in relative.parts or relative.suffix == ".pyc"


def copy_file_if_missing(source: Path, destination: Path) -> bool:
    if destination.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def doctor_wiki(*, wiki_root: Path | str, wiki_type: str | None = None) -> list[DoctorIssue]:
    root = Path(wiki_root).resolve()
    issues: list[DoctorIssue] = []
    if not root.exists():
        return [
            DoctorIssue(
                level="error",
                code="wiki_root_missing",
                message="Wiki root does not exist.",
                path=str(root),
            )
        ]
    if not root.is_dir():
        return [
            DoctorIssue(
                level="error",
                code="wiki_root_not_directory",
                message="Wiki root is not a directory.",
                path=str(root),
            )
        ]

    config = read_json(root / CONFIG_PATH)
    detected_type = wiki_type or detect_wiki_type(config)
    if detected_type not in VALID_WIKI_TYPES:
        issues.append(
            DoctorIssue(
                level="error",
                code="invalid_wiki_type",
                message=f"Invalid wiki type: {detected_type}",
            )
        )

    for folder in required_folders_for_doctor(detected_type):
        path = root / folder
        if not path.is_dir():
            issues.append(
                DoctorIssue(
                    level="error",
                    code="missing_folder",
                    message=f"Required folder is missing: {folder}",
                    path=str(path),
                )
            )

    for file_name in REQUIRED_TEMPLATE_FILES:
        path = root / file_name
        if not path.is_file():
            issues.append(
                DoctorIssue(
                    level="warning",
                    code="missing_template_file",
                    message=f"Template file is missing: {file_name}",
                    path=str(path),
                )
            )

    if config is None:
        issues.append(
            DoctorIssue(
                level="info",
                code="local_config_missing",
                message="_system/config.json is not present; defaults or _system/config.example.json will be used.",
                path=str(root / CONFIG_PATH),
            )
        )
    elif config.get("wikiType") not in VALID_WIKI_TYPES:
        issues.append(
            DoctorIssue(
                level="error",
                code="config_invalid_wiki_type",
                message="_system/config.json has missing or invalid wikiType.",
                path=str(root / CONFIG_PATH),
            )
        )

    return issues


def required_folders_for_doctor(wiki_type: str | None) -> tuple[str, ...]:
    folders: list[str] = list(CONTENT_FOLDERS) + list(GENERATED_FOLDERS) + list(SYSTEM_FOLDERS)
    if wiki_type == "vault":
        folders.extend(VAULT_RUNTIME_FOLDERS)
    return tuple(folders)


def detect_wiki_type(config: dict[str, object] | None) -> str:
    if config and config.get("wikiType") in VALID_WIKI_TYPES:
        return str(config["wikiType"])
    return "vault"


def read_json(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def issues_to_json(issues: Iterable[DoctorIssue]) -> str:
    return json.dumps([issue.to_dict() for issue in issues], indent=2, sort_keys=True)


def issues_to_text(issues: Iterable[DoctorIssue]) -> str:
    rows = list(issues)
    if not rows:
        return "Doctor passed: no issues found."
    return "\n".join(format_issue(issue) for issue in rows)


def format_issue(issue: DoctorIssue) -> str:
    suffix = f" ({issue.path})" if issue.path else ""
    return f"{issue.level.upper():7} {issue.code}: {issue.message}{suffix}"
