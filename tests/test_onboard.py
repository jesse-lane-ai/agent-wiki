from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONBOARD_SCRIPT = REPO_ROOT / "_system" / "scripts" / "onboard.py"


def run_onboard(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ONBOARD_SCRIPT), *args],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )


class OnboardProbeTests(unittest.TestCase):
    def test_check_defaults_to_vault_folder_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = run_onboard(root, "--check")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["wikiType"], "vault")
            self.assertIn("_inbox", report["folders"])
            self.assertIn("_inbox/trash", report["folders"])
            self.assertIn("raw", report["folders"])
            self.assertIn("skills", report["folders"])
            self.assertNotIn("_system/skills", report["folders"])

    def test_check_uses_workspace_folder_expectations_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            system = root / "_system"
            system.mkdir()
            (system / "config.json").write_text(
                json.dumps({"schemaVersion": 1, "wikiType": "workspace"}) + "\n",
                encoding="utf-8",
            )

            result = run_onboard(root, "--check")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["wikiType"], "workspace")
            self.assertNotIn("_inbox", report["folders"])
            self.assertNotIn("_inbox/trash", report["folders"])
            self.assertNotIn("raw", report["folders"])
            self.assertIn("skills", report["folders"])
            self.assertNotIn("_system/skills", report["folders"])

    def test_questions_include_detected_workspace_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            system = root / "_system"
            system.mkdir()
            (system / "config.json").write_text(
                json.dumps({"schemaVersion": 1, "wikiType": "workspace"}) + "\n",
                encoding="utf-8",
            )

            result = run_onboard(root, "--check", "--questions")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Folders (workspace mode", result.stdout)


if __name__ == "__main__":
    unittest.main()
