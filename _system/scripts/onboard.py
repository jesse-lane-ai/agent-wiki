#!/usr/bin/env python3
"""
Onboarding probe and local config writer for the Agentics vault.

Usage:
    python3 _system/scripts/onboard.py --check
    python3 _system/scripts/onboard.py --check --questions
    python3 _system/scripts/onboard.py --write-config --python-command python3 --conversion disabled
"""

import argparse
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SYSTEM_CONFIG = Path("_system/config.json")
SYSTEM_CONFIG_EXAMPLE = Path("_system/config.example.json")
IMPORT_LINK_CONFIG = Path("_system/skills/import-link/config.json")
PYTHON_CANDIDATES = ["python3", "python", ".venv/bin/python"]
CLI_CONVERTERS = ["markitdown", "marker", "arxiv2md"]
PYTHON_PACKAGES = ["pymupdf4llm", "markitdown", "marker"]
SAFETY_FLAGS = {
    "allow_network": "allowNetwork",
    "allow_ocr": "allowOcr",
    "allow_llm": "allowLlm",
    "allow_transcription": "allowTranscription",
    "allow_hosted_document_intelligence": "allowHostedDocumentIntelligence",
}
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


def default_config() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "pythonCommand": None,
        "conversion": {
            "enabled": False,
            "defaultBackend": "auto",
            "backendOrder": ["pymupdf4llm", "markitdown"],
            "allowNetwork": False,
            "allowOcr": False,
            "allowLlm": False,
            "allowTranscription": False,
            "allowHostedDocumentIntelligence": False,
            "backends": {
                "pymupdf4llm": {
                    "enabled": True,
                    "command": None,
                    "formats": ["pdf"],
                },
                "markitdown": {
                    "enabled": True,
                    "command": "markitdown",
                    "formats": ["pdf", "docx", "pptx", "xlsx", "html", "csv", "json", "xml", "epub"],
                },
                "arxiv2md": {
                    "enabled": False,
                    "command": None,
                    "formats": ["pdf"],
                },
                "marker": {
                    "enabled": False,
                    "command": None,
                    "formats": ["pdf"],
                },
            },
        },
    }


def run_command(args: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return None


def command_path(command: str, wiki_root: Path) -> str | None:
    if "/" in command:
        path = wiki_root / command
        return str(path) if path.exists() else None
    return shutil.which(command)


def probe_python(command: str, wiki_root: Path) -> dict[str, Any]:
    path = command_path(command, wiki_root)
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


def detect_obsidian(wiki_root: Path) -> dict[str, Any]:
    current_marker = wiki_root / ".obsidian"
    return {
        "currentRootHasObsidian": current_marker.is_dir(),
        "currentRootMarker": ".obsidian" if current_marker.is_dir() else None,
    }


def probe_platform() -> dict[str, Any]:
    return {
        "osName": os.name,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "pathSeparator": os.sep,
    }


def load_config_base(wiki_root: Path) -> dict[str, Any]:
    config_path = wiki_root / SYSTEM_CONFIG
    example_path = wiki_root / SYSTEM_CONFIG_EXAMPLE
    for path in (config_path, example_path):
        if path.exists():
            data = read_json(path)
            if data is None:
                raise SystemExit(f"Cannot read JSON config base: {path}")
            return copy.deepcopy(data)
    return default_config()


def probe_config(wiki_root: Path) -> dict[str, Any]:
    config_path = wiki_root / SYSTEM_CONFIG
    example_path = wiki_root / SYSTEM_CONFIG_EXAMPLE
    data = read_json(config_path) if config_path.exists() else None
    example_data = read_json(example_path) if example_path.exists() else None
    return {
        "path": str(SYSTEM_CONFIG),
        "exists": config_path.exists(),
        "readable": data is not None if config_path.exists() else False,
        "examplePath": str(SYSTEM_CONFIG_EXAMPLE),
        "exampleExists": example_path.exists(),
        "exampleReadable": example_data is not None if example_path.exists() else False,
        "schemaVersion": data.get("schemaVersion") if data else None,
        "pythonCommand": data.get("pythonCommand") if data else None,
        "conversionEnabled": data.get("conversion", {}).get("enabled") if data else None,
        "defaultBackend": data.get("conversion", {}).get("defaultBackend") if data else None,
        "backendOrder": data.get("conversion", {}).get("backendOrder") if data else None,
    }


def probe_import_link_config(wiki_root: Path) -> dict[str, Any]:
    config_path = wiki_root / IMPORT_LINK_CONFIG
    data = read_json(config_path) if config_path.exists() else None
    return {
        "path": str(IMPORT_LINK_CONFIG),
        "exists": config_path.exists(),
        "readable": data is not None if config_path.exists() else False,
        "configured": bool(data.get("configured")) if data else False,
        "retrievalModes": data.get("retrievalModes") if data else None,
        "attachmentPolicy": data.get("attachmentPolicy") if data else None,
    }


def probe_folders(wiki_root: Path) -> dict[str, dict[str, Any]]:
    return {
        folder: {
            "exists": (wiki_root / folder).is_dir(),
            "path": folder,
        }
        for folder in REQUIRED_FOLDERS
    }


def build_report(wiki_root: Path) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "wikiRoot": str(wiki_root),
        "mode": "check",
        "mutating": False,
        "platform": probe_platform(),
        "obsidian": detect_obsidian(wiki_root),
        "python": {command: probe_python(command, wiki_root) for command in PYTHON_CANDIDATES},
        "virtualenv": {
            "path": ".venv",
            "exists": (wiki_root / ".venv").is_dir(),
            "pythonExists": (wiki_root / ".venv/bin/python").exists(),
        },
        "config": probe_config(wiki_root),
        "importLink": probe_import_link_config(wiki_root),
        "folders": probe_folders(wiki_root),
        "conversion": {
            "cli": {command: probe_cli(command) for command in CLI_CONVERTERS},
        },
    }


def available_python_commands(report: dict[str, Any]) -> list[str]:
    return [
        command
        for command, data in report["python"].items()
        if data.get("available")
    ]


def preferred_python_command(report: dict[str, Any]) -> str | None:
    for command in (".venv/bin/python", "python3", "python"):
        if report["python"].get(command, {}).get("available"):
            return command
    return None


def any_converter_available(report: dict[str, Any]) -> bool:
    if any(data.get("available") for data in report["conversion"]["cli"].values()):
        return True
    for python_data in report["python"].values():
        packages = python_data.get("packages", {})
        if any(package.get("available") for package in packages.values()):
            return True
    return False


def missing_folder_names(report: dict[str, Any]) -> list[str]:
    return [
        folder
        for folder, data in report["folders"].items()
        if not data.get("exists")
    ]


def build_setup_questions(report: dict[str, Any]) -> str:
    missing_folders = missing_folder_names(report)
    python_commands = available_python_commands(report)
    preferred_python = preferred_python_command(report)
    has_config = bool(report["config"].get("exists"))
    has_venv = bool(report["virtualenv"].get("exists"))
    has_converters = any_converter_available(report)
    import_link_configured = bool(report["importLink"].get("configured"))
    obsidian = report["obsidian"]

    lines = [
        "Setup questions",
        "",
        "Reply with letters, for example: 1A 2B 3A 4A 5B",
        "",
    ]

    if missing_folders:
        folder_summary = f"{len(missing_folders)} missing"
    else:
        folder_summary = "all present"
    lines.extend([
        f"1. Folders ({folder_summary})",
        "   A. Create missing folders now. Recommended when you want the wiki ready for imports and compile runs.",
        "   B. Leave them for workflows to create later. Use this for a minimal checkout.",
        "   C. Skip folder setup for now.",
        "",
    ])

    if preferred_python:
        python_label = preferred_python
    elif python_commands:
        python_label = python_commands[0]
    else:
        python_label = "not found"
    lines.extend([
        f"2. Python and _system/config.json ({python_label})",
        "   A. Create local _system/config.json from the example with the detected Python command. Recommended when you want repeatable local runs.",
        "   B. Leave _system/config.json absent. Tools will use conservative defaults.",
        "   C. Use a different Python command. Reply with the command after the choice.",
        "",
    ])

    obsidian_label = "present at repo root" if obsidian.get("currentRootHasObsidian") else "not detected"
    lines.extend([
        f"3. Obsidian ({obsidian_label})",
        "   A. Skip Obsidian setup. Recommended when you use this as a plain markdown wiki.",
        "   B. Open this repo root as an Obsidian vault after onboarding.",
        "",
    ])

    venv_status = "present" if has_venv else "not present"
    converter_status = "available" if has_converters else "not installed"
    lines.extend([
        f"4. Inbox conversion (.venv {venv_status}, converters {converter_status})",
        "   A. Keep conversion disabled for now. Recommended when you only use markdown or pasted text.",
        "   B. Enable only converters already available on this machine.",
        "   C. Create .venv and install optional converters. This requires explicit install approval.",
        "",
    ])

    import_status = "configured" if import_link_configured else "not configured"
    lines.extend([
        f"5. import-link ({import_status})",
        "   A. Configure import-link for this wiki root.",
        "   B. Configure only manual_paste for now. Use this when links will be pasted by the user.",
        "   C. Skip import-link setup for now.",
        "",
    ])

    config_status = "present" if has_config else "absent"
    lines.extend([
        f"6. Compile after setup (_system/config.json {config_status})",
        "   A. Run compile after approved setup changes. Recommended if files were created or config changed.",
        "   B. Do not run compile now.",
        "",
    ])

    return "\n".join(lines)


def parse_backend_order(raw_values: list[str] | None) -> list[str] | None:
    if not raw_values:
        return None
    values: list[str] = []
    for raw_value in raw_values:
        for value in raw_value.split(","):
            stripped = value.strip()
            if stripped:
                values.append(stripped)
    return values or None


def write_config(args: argparse.Namespace) -> dict[str, Any]:
    wiki_root = Path.cwd().resolve()
    config_path = wiki_root / SYSTEM_CONFIG
    config = load_config_base(wiki_root)
    written_fields: list[str] = []

    config["schemaVersion"] = config.get("schemaVersion") or 1

    if args.python_command is not None:
        config["pythonCommand"] = args.python_command
        written_fields.append("pythonCommand")

    conversion = config.setdefault("conversion", {})
    if not isinstance(conversion, dict):
        conversion = {}
        config["conversion"] = conversion

    if args.conversion == "disabled":
        conversion["enabled"] = False
        written_fields.append("conversion.enabled")
    elif args.conversion in {"available-local", "custom"}:
        conversion["enabled"] = True
        written_fields.append("conversion.enabled")

    if args.default_backend is not None:
        conversion["defaultBackend"] = args.default_backend
        written_fields.append("conversion.defaultBackend")

    backend_order = parse_backend_order(args.backend_order)
    if backend_order is not None:
        conversion["backendOrder"] = backend_order
        written_fields.append("conversion.backendOrder")

    for arg_name, field_name in SAFETY_FLAGS.items():
        approved_value = bool(getattr(args, arg_name))
        if conversion.get(field_name) != approved_value:
            conversion[field_name] = approved_value
            written_fields.append(f"conversion.{field_name}")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    return {
        "schemaVersion": 1,
        "mode": "write-config",
        "mutating": True,
        "path": str(SYSTEM_CONFIG),
        "written": True,
        "writtenFields": written_fields,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run onboarding checks or write approved local config.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Inspect local setup without mutating files")
    mode.add_argument("--write-config", action="store_true", help="Create or update local _system/config.json")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    parser.add_argument("--questions", action="store_true", help="Print human-friendly setup questions instead of JSON")
    parser.add_argument("--python-command", help="Preferred Python command to persist in local config")
    parser.add_argument("--conversion", choices=["disabled", "available-local", "custom"], help="Inbox conversion policy")
    parser.add_argument("--default-backend", help="Default conversion backend")
    parser.add_argument("--backend-order", nargs="+", help="Conversion backend order as space-separated or comma-separated values")
    parser.add_argument("--allow-network", action="store_true", help="Allow network behavior for conversion")
    parser.add_argument("--allow-ocr", action="store_true", help="Allow OCR behavior for conversion")
    parser.add_argument("--allow-llm", action="store_true", help="Allow LLM behavior for conversion")
    parser.add_argument("--allow-transcription", action="store_true", help="Allow transcription behavior for conversion")
    parser.add_argument("--allow-hosted-document-intelligence", action="store_true", help="Allow hosted document-intelligence behavior for conversion")
    args = parser.parse_args()

    if args.check and (
        args.python_command
        or args.conversion
        or args.default_backend
        or args.backend_order
        or any(getattr(args, flag) for flag in SAFETY_FLAGS)
    ):
        parser.error("config-writing flags require --write-config")

    if args.write_config:
        if args.questions:
            parser.error("--questions can only be used with --check")
        if (
            args.python_command is None
            and args.conversion is None
        ):
            parser.error("--write-config requires at least one config field flag")
        result = write_config(args)
        json.dump(result, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
        sys.stdout.write("\n")
        return

    wiki_root = Path.cwd().resolve()
    report = build_report(wiki_root)
    if args.questions:
        sys.stdout.write(build_setup_questions(report))
        sys.stdout.write("\n")
        return

    indent = None if args.compact else 2
    json.dump(report, sys.stdout, indent=indent, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
