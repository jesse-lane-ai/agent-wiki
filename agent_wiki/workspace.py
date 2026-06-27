from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from .config import DEFAULT_WORKSPACE_WIKI_DIR, AgentWikiConfig, WorkspaceScanConfig


STATE_PATH = Path("_system/state/workspace-sources.json")


@dataclass(frozen=True)
class WorkspaceFile:
    path: str
    relative_path: str
    modified_at: str
    size: int
    extension: str
    sha256: str
    reason: str
    recommended_source_type: str
    already_sourced: bool
    source_id: str | None = None
    source_path: str | None = None

    def to_agent_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "relativePath": self.relative_path,
            "modifiedAt": self.modified_at,
            "size": self.size,
            "extension": self.extension,
            "sha256": self.sha256,
            "reason": self.reason,
            "recommendedSourceType": self.recommended_source_type,
            "alreadySourced": self.already_sourced,
            "sourceId": self.source_id,
            "sourcePath": self.source_path,
        }


def default_workspace_root(config: AgentWikiConfig, explicit_root: Path | None = None) -> Path:
    if explicit_root is not None:
        return explicit_root.resolve()
    if config.workspace_root is not None:
        return config.workspace_root.resolve()
    if config.wiki_type == "workspace":
        return config.root.resolve()
    return Path.cwd().resolve()


def wiki_root_for_workspace(workspace_root: Path, wiki_dir: str | None = None) -> Path:
    clean_wiki_dir = (wiki_dir or DEFAULT_WORKSPACE_WIKI_DIR).strip().strip("/") or DEFAULT_WORKSPACE_WIKI_DIR
    return (workspace_root / clean_wiki_dir).resolve()


def load_state(wiki_root: Path) -> dict[str, object]:
    path = wiki_root / STATE_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schemaVersion": 1, "files": {}}
    if not isinstance(data, dict):
        return {"schemaVersion": 1, "files": {}}
    if not isinstance(data.get("files"), dict):
        data["files"] = {}
    return data


def write_state(wiki_root: Path, state: dict[str, object]) -> None:
    path = wiki_root / STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scan_workspace(
    workspace_root: Path,
    wiki_root: Path,
    scan_config: WorkspaceScanConfig,
    *,
    since: datetime | None = None,
    state: dict[str, object] | None = None,
) -> list[WorkspaceFile]:
    workspace_root = workspace_root.resolve()
    wiki_root = wiki_root.resolve()
    state = state or {"files": {}}
    files_state = state.get("files") if isinstance(state.get("files"), dict) else {}
    results: list[WorkspaceFile] = []

    for path in iter_candidate_paths(workspace_root, wiki_root, scan_config):
        try:
            stat = path.stat()
        except OSError:
            continue
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        if since is not None and modified < since:
            continue
        rel_path = path.relative_to(workspace_root).as_posix()
        digest = sha256_file(path)
        previous = files_state.get(rel_path) if isinstance(files_state, dict) else None
        previous_hash = previous.get("sha256") if isinstance(previous, dict) else None
        already_sourced = bool(previous.get("sourceId")) if isinstance(previous, dict) else False
        source_id = previous.get("sourceId") if isinstance(previous, dict) else None
        source_path = previous.get("sourcePath") if isinstance(previous, dict) else None
        if previous_hash is None:
            reason = "new"
        elif previous_hash != digest:
            reason = "changed"
        else:
            reason = "unchanged"
        results.append(
            WorkspaceFile(
                path=str(path),
                relative_path=rel_path,
                modified_at=modified.isoformat(),
                size=stat.st_size,
                extension=path.suffix.lower(),
                sha256=digest,
                reason=reason,
                recommended_source_type=recommend_source_type(path),
                already_sourced=already_sourced,
                source_id=str(source_id) if source_id else None,
                source_path=str(source_path) if source_path else None,
            )
        )

    return sorted(results, key=lambda item: item.relative_path)


def update_state_from_scan(wiki_root: Path, files: Iterable[WorkspaceFile], state: dict[str, object]) -> dict[str, object]:
    files_state = state.get("files") if isinstance(state.get("files"), dict) else {}
    now = datetime.now(timezone.utc).isoformat()
    for item in files:
        previous = files_state.get(item.relative_path) if isinstance(files_state, dict) else None
        source_id = previous.get("sourceId") if isinstance(previous, dict) else None
        source_path = previous.get("sourcePath") if isinstance(previous, dict) else None
        files_state[item.relative_path] = {
            "path": item.path,
            "mtime": item.modified_at,
            "size": item.size,
            "sha256": item.sha256,
            "sourceId": source_id,
            "sourcePath": source_path,
            "lastSeenAt": now,
        }
    state["schemaVersion"] = 1
    state["lastScanAt"] = now
    state["files"] = files_state
    write_state(wiki_root, state)
    return state


def mark_sourced(
    wiki_root: Path,
    state: dict[str, object],
    *,
    relative_path: str,
    source_id: str,
    source_path: str,
) -> dict[str, object]:
    files_state = state.get("files") if isinstance(state.get("files"), dict) else {}
    previous = files_state.get(relative_path) if isinstance(files_state, dict) else None
    record = dict(previous) if isinstance(previous, dict) else {}
    record["sourceId"] = source_id
    record["sourcePath"] = source_path
    record["mappedAt"] = datetime.now(timezone.utc).isoformat()
    files_state[relative_path] = record
    state["schemaVersion"] = 1
    state["files"] = files_state
    write_state(wiki_root, state)
    return state


def iter_candidate_paths(workspace_root: Path, wiki_root: Path, scan_config: WorkspaceScanConfig) -> Iterable[Path]:
    excluded_dirs = set(scan_config.exclude_dirs)
    for path in workspace_root.rglob("*"):
        if not path.is_file():
            continue
        if is_relative_to(path, wiki_root):
            continue
        rel_parts = path.relative_to(workspace_root).parts
        if any(part in excluded_dirs for part in rel_parts[:-1]):
            continue
        if any(fnmatch(path.name, pattern) for pattern in scan_config.exclude_file_globs):
            continue
        if path.suffix.lower() not in scan_config.include_extensions:
            continue
        yield path


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def recommend_source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".csv", ".json", ".yaml", ".yml"}:
        return "dataset"
    if suffix in {".md", ".markdown", ".txt", ".docx"}:
        return "document"
    return "other"


def files_to_json(files: Iterable[WorkspaceFile]) -> str:
    return json.dumps([item.to_agent_dict() for item in files], indent=2, sort_keys=True)


def files_to_text(files: Iterable[WorkspaceFile]) -> str:
    rows = list(files)
    if not rows:
        return "No workspace source candidates found."
    lines = []
    for item in rows:
        marker = "sourced" if item.already_sourced else item.reason
        lines.append(f"{marker:9} {item.relative_path} ({item.recommended_source_type}, {item.size} bytes)")
    return "\n".join(lines)
