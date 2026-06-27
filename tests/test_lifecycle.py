from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_wiki.lifecycle import doctor_wiki, init_wiki


class LifecycleTests(unittest.TestCase):
    def test_init_vault_creates_expected_folders_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"

            result = init_wiki(wiki_type="vault", root=root, write_config=True)

            self.assertEqual(result.wiki_type, "vault")
            self.assertTrue((root / "sources" / "parts").is_dir())
            self.assertTrue((root / "_inbox" / "trash").is_dir())
            self.assertTrue((root / "raw").is_dir())
            config = json.loads((root / "_system" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["wikiType"], "vault")

    def test_init_workspace_creates_wiki_inside_workspace_without_raw_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "project"

            result = init_wiki(wiki_type="workspace", workspace_root=workspace, wiki_dir="wiki", write_config=True)

            wiki = workspace / "wiki"
            self.assertEqual(result.workspace_root, str(workspace.resolve()))
            self.assertTrue((wiki / "sources" / "parts").is_dir())
            self.assertFalse((wiki / "_inbox").exists())
            self.assertFalse((wiki / "raw").exists())
            config = json.loads((wiki / "_system" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["wikiType"], "workspace")
            self.assertEqual(config["workspace"]["wikiDir"], "wiki")

    def test_doctor_reports_missing_template_files_as_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            init_wiki(wiki_type="vault", root=root)

            issues = doctor_wiki(wiki_root=root, wiki_type="vault")

            self.assertFalse(any(issue.level == "error" for issue in issues))
            self.assertTrue(any(issue.code == "missing_template_file" for issue in issues))

    def test_doctor_reports_missing_required_folder_as_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            init_wiki(wiki_type="vault", root=root)
            (root / "sources" / "parts").rmdir()
            (root / "sources").rmdir()

            issues = doctor_wiki(wiki_root=root, wiki_type="vault")

            self.assertTrue(any(issue.level == "error" and issue.code == "missing_folder" for issue in issues))


if __name__ == "__main__":
    unittest.main()
