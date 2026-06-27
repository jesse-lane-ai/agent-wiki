from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("_system/config.json")
CONFIG_EXAMPLE_PATH = Path("_system/config.example.json")
DEFAULT_WORKSPACE_WIKI_DIR = "wiki"
VALID_WIKI_TYPES = {"vault", "workspace"}


@dataclass(frozen=True)
class WorkspaceScanConfig:
    include_extensions: tuple[str, ...] = (
        ".md",
        ".markdown",
        ".txt",
        ".pdf",
        ".docx",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
    )
    exclude_dirs: tuple[str, ...] = (
        ".git",
        ".hg",
        ".svn",
        ".obsidian",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
        ".next",
        ".turbo",
        ".cache",
        "_system",
        "reports",
        "target",
        "vendor",
    )
    exclude_file_globs: tuple[str, ...] = (
        "*.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "uv.lock",
        "poetry.lock",
    )


@dataclass(frozen=True)
class AgentWikiConfig:
    wiki_type: str = "vault"
    root: Path = Path(".")
    workspace_root: Path | None = None
    wiki_dir: str = DEFAULT_WORKSPACE_WIKI_DIR
    workspace_scan: WorkspaceScanConfig = field(default_factory=WorkspaceScanConfig)

    @property
    def wiki_root(self) -> Path:
        if self.wiki_type == "workspace":
            if self.workspace_root is None:
                return self.root
            return self.workspace_root / self.wiki_dir
        return self.root


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _tuple_from_config(data: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list):
        return default
    items = tuple(str(item) for item in value if isinstance(item, str) and item)
    return items or default


def load_config(root: Path | str = ".") -> AgentWikiConfig:
    root_path = Path(root).resolve()
    data = _read_json(root_path / CONFIG_PATH) or _read_json(root_path / CONFIG_EXAMPLE_PATH) or {}

    wiki_type = str(data.get("wikiType") or data.get("wiki_type") or "vault")
    if wiki_type not in VALID_WIKI_TYPES:
        wiki_type = "vault"

    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    workspace_root_raw = workspace.get("root") or data.get("workspaceRoot")
    workspace_root = None
    if isinstance(workspace_root_raw, str) and workspace_root_raw:
        workspace_root = Path(workspace_root_raw)
        if not workspace_root.is_absolute():
            workspace_root = root_path / workspace_root
        workspace_root = workspace_root.resolve()

    wiki_dir = workspace.get("wikiDir") or data.get("wikiDir") or DEFAULT_WORKSPACE_WIKI_DIR
    wiki_dir = str(wiki_dir).strip().strip("/") or DEFAULT_WORKSPACE_WIKI_DIR

    scan_data = workspace.get("scan") if isinstance(workspace.get("scan"), dict) else {}
    scan_defaults = WorkspaceScanConfig()
    workspace_scan = WorkspaceScanConfig(
        include_extensions=tuple(
            ext if ext.startswith(".") else f".{ext}"
            for ext in _tuple_from_config(scan_data, "includeExtensions", scan_defaults.include_extensions)
        ),
        exclude_dirs=_tuple_from_config(scan_data, "excludeDirs", scan_defaults.exclude_dirs),
        exclude_file_globs=_tuple_from_config(scan_data, "excludeFileGlobs", scan_defaults.exclude_file_globs),
    )

    return AgentWikiConfig(
        wiki_type=wiki_type,
        root=root_path,
        workspace_root=workspace_root,
        wiki_dir=wiki_dir,
        workspace_scan=workspace_scan,
    )
