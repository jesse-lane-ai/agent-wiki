#!/usr/bin/env python3
"""
Read-only onboarding probe for the Agentics vault.

Usage:
    python3 _system/scripts/onboard.py --check
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SYSTEM_CONFIG = Path("_system/config.json")
IMPORT_LINK_CONFIG = Path("_system/skills/import-link/config.json")
PYTHON_CANDIDATES = ["python3", "python", ".venv/bin/python"]
CLI_CONVERTERS = ["markitdown", "marker", "arxiv2md"]
PYTHON_PACKAGES = ["pymupdf4llm", "markitdown", "marker"]
REQUIRED_FOLDERS = [
    "sources",
    "sources/parts",
    "entities",
    "concepts",
    "claims",
    "syntheses",
    "questions",
    "reports",
    "_inbox",
    "_inbox/trash",
    "raw",
    "_attachments",
    "_archive",
    "_system/cache",
    "_system/indexes",
    "_system/logs",
    "_system/scripts",
    "_system/skills",
]


def run_command(args: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return None


def command_path(command: str, vault_root: Path) -> str | None:
    if "/" in command:
        path = vault_root / command
        return str(path) if path.exists() else None
    return shutil.which(command)


def probe_python(command: str, vault_root: Path) -> dict[str, Any]:
    path = command_path(command, vault_root)
    result: dict[str, Any] = {
        "command": command,
        "available": path is not None,
        "path": path,
        "version": None,
        "packages": {},
    }
    if path is None:
        return result

    version_proc = run_command([path, "--version"])
    if version_proc is not None:
        version_text = (version_proc.stdout or version_proc.stderr).strip()
        result["version"] = version_text or None

    for package in PYTHON_PACKAGES:
        result["packages"][package] = probe_python_package(path, package)

    return result


def probe_python_package(python_path: str, package: str) -> dict[str, Any]:
    code = (
        "import importlib.metadata as m, importlib.util as u, json, sys; "
        f"name={package!r}; "
        "spec=u.find_spec(name); "
        "version=None; "
        "\nif spec is not None:\n"
        "    try:\n"
        "        version=m.version(name)\n"
        "    except m.PackageNotFoundError:\n"
        "        version=None\n"
        "print(json.dumps({'available': spec is not None, 'version': version}))"
    )
    proc = run_command([python_path, "-c", code])
    if proc is None or proc.returncode != 0:
        return {"available": False, "version": None}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"available": False, "version": None}
    return {
        "available": bool(data.get("available")),
        "version": data.get("version"),
    }


def probe_cli(command: str) -> dict[str, Any]:
    path = shutil.which(command)
    result: dict[str, Any] = {
        "command": command,
        "available": path is not None,
        "path": path,
        "version": None,
    }
    if path is None:
        return result

    for version_args in ([path, "--version"], [path, "version"]):
        proc = run_command(version_args)
        if proc is not None and proc.returncode == 0:
            version_text = (proc.stdout or proc.stderr).strip()
            result["version"] = version_text.splitlines()[0] if version_text else None
            break
    return result


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def probe_config(vault_root: Path) -> dict[str, Any]:
    config_path = vault_root / SYSTEM_CONFIG
    data = read_json(config_path) if config_path.exists() else None
    return {
        "path": str(SYSTEM_CONFIG),
        "exists": config_path.exists(),
        "readable": data is not None if config_path.exists() else False,
        "schemaVersion": data.get("schemaVersion") if data else None,
        "pythonCommand": data.get("pythonCommand") if data else None,
        "conversionEnabled": data.get("conversion", {}).get("enabled") if data else None,
        "defaultBackend": data.get("conversion", {}).get("defaultBackend") if data else None,
        "backendOrder": data.get("conversion", {}).get("backendOrder") if data else None,
    }


def probe_import_link_config(vault_root: Path) -> dict[str, Any]:
    config_path = vault_root / IMPORT_LINK_CONFIG
    data = read_json(config_path) if config_path.exists() else None
    return {
        "path": str(IMPORT_LINK_CONFIG),
        "exists": config_path.exists(),
        "readable": data is not None if config_path.exists() else False,
        "configured": bool(data.get("configured")) if data else False,
        "retrievalModes": data.get("retrievalModes") if data else None,
        "attachmentPolicy": data.get("attachmentPolicy") if data else None,
    }


def probe_folders(vault_root: Path) -> dict[str, dict[str, Any]]:
    return {
        folder: {
            "exists": (vault_root / folder).is_dir(),
            "path": folder,
        }
        for folder in REQUIRED_FOLDERS
    }


def build_report(vault_root: Path) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "vaultRoot": str(vault_root),
        "mode": "check",
        "mutating": False,
        "python": {command: probe_python(command, vault_root) for command in PYTHON_CANDIDATES},
        "virtualenv": {
            "path": ".venv",
            "exists": (vault_root / ".venv").is_dir(),
            "pythonExists": (vault_root / ".venv/bin/python").exists(),
        },
        "config": probe_config(vault_root),
        "importLink": probe_import_link_config(vault_root),
        "folders": probe_folders(vault_root),
        "conversion": {
            "cli": {command: probe_cli(command) for command in CLI_CONVERTERS},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a read-only onboarding probe.")
    parser.add_argument("--check", action="store_true", required=True, help="Inspect local setup without mutating files")
    parser.add_argument("--vault-root", default=".", help="Path to vault root (default: current directory)")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    report = build_report(vault_root)
    indent = None if args.compact else 2
    json.dump(report, sys.stdout, indent=indent, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
