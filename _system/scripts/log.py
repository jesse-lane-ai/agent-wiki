#!/usr/bin/env python3
"""
Operational log writer for the Agentics vault.

Usage:
    python3 _system/scripts/log.py --message "<message>"
"""

import argparse
from datetime import datetime
from pathlib import Path


LOG_PATH = Path("_system/logs/log.md")


def write_log(message: str, vault_root: Path) -> Path:
    message = message.strip()
    if not message:
        raise ValueError("--message cannot be empty")

    log_path = vault_root / LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    entry = f"## {timestamp}\n\n{message}\n"

    existing = ""
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8").lstrip()

    content = entry if not existing else f"{entry}\n{existing}"
    log_path.write_text(content, encoding="utf-8")
    return log_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write an operational log entry.")
    parser.add_argument("--message", required=True, help="Concise operational log message")
    parser.add_argument("--vault-root", default=".", help="Path to vault root (default: current directory)")
    args = parser.parse_args()

    log_path = write_log(args.message, Path(args.vault_root).resolve())
    print(f"Wrote operational log: {log_path.relative_to(Path(args.vault_root).resolve())}")


if __name__ == "__main__":
    main()
