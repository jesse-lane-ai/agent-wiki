from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_wiki.config import WorkspaceScanConfig
from agent_wiki.workspace import load_state, mark_sourced, scan_workspace, update_state_from_scan


class WorkspaceScanTests(unittest.TestCase):
    def test_scan_excludes_wiki_and_code_heavy_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wiki = root / "wiki"
            (root / "docs").mkdir()
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "_system" / "cache").mkdir(parents=True)
            wiki.mkdir()
            (root / "docs" / "research.md").write_text("research", encoding="utf-8")
            (wiki / "sources.md").write_text("canonical", encoding="utf-8")
            (root / "app.py").write_text("print('skip')", encoding="utf-8")
            (root / "node_modules" / "pkg" / "readme.md").write_text("skip", encoding="utf-8")
            (root / "_system" / "cache" / "pages.json").write_text("{}", encoding="utf-8")

            files = scan_workspace(root, wiki, WorkspaceScanConfig())

            self.assertEqual([item.relative_path for item in files], ["docs/research.md"])
            self.assertEqual(files[0].recommended_source_type, "document")
            self.assertEqual(files[0].reason, "new")

    def test_pending_detects_changed_files_from_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wiki = root / "wiki"
            wiki.mkdir()
            source = root / "notes.md"
            source.write_text("first", encoding="utf-8")

            state = load_state(wiki)
            first_scan = scan_workspace(root, wiki, WorkspaceScanConfig(), state=state)
            update_state_from_scan(wiki, first_scan, state)

            source.write_text("second", encoding="utf-8")
            changed_scan = scan_workspace(root, wiki, WorkspaceScanConfig(), state=load_state(wiki))

            self.assertEqual(len(changed_scan), 1)
            self.assertEqual(changed_scan[0].reason, "changed")

    def test_state_preserves_source_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wiki = root / "wiki"
            state_path = wiki / "_system" / "state" / "workspace-sources.json"
            source = root / "memo.txt"
            source.write_text("memo", encoding="utf-8")
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "files": {
                            "memo.txt": {
                                "sha256": "old",
                                "sourceId": "source.2026-06-26.document.memo",
                                "sourcePath": "sources/2026-06-26-document-memo.md",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            files = scan_workspace(root, wiki, WorkspaceScanConfig(), state=load_state(wiki))

            self.assertTrue(files[0].already_sourced)
            self.assertEqual(files[0].source_id, "source.2026-06-26.document.memo")

    def test_mark_sourced_records_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            state = load_state(wiki)

            mark_sourced(
                wiki,
                state,
                relative_path="docs/research.md",
                source_id="source.2026-06-26.document.research",
                source_path="sources/2026-06-26-document-research.md",
            )

            stored = load_state(wiki)
            record = stored["files"]["docs/research.md"]
            self.assertEqual(record["sourceId"], "source.2026-06-26.document.research")
            self.assertEqual(record["sourcePath"], "sources/2026-06-26-document-research.md")


if __name__ == "__main__":
    unittest.main()
