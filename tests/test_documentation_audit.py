"""Release checks for short, linked, version-consistent documentation."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_docs import audit  # noqa: E402


class DocumentationAuditTests(unittest.TestCase):
    def _copy(self, temporary: str) -> Path:
        return Path(shutil.copytree(ROOT, Path(temporary) / "repo", ignore=shutil.ignore_patterns(".git", ".aim", "__pycache__", "*.pyc")))

    def test_current_repository_passes(self) -> None:
        self.assertEqual([], audit(ROOT))

    def test_runtime_schema_version_is_documented_separately(self) -> None:
        content = (ROOT / "docs/workflow/version-and-installation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("runtime-state schema version", content)
        self.assertIn("schemas/aim-runtime-state.schema.json", content)

    def test_broken_link_and_version_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            readme = copied / "README.md"
            readme.write_text(readme.read_text() + "\n[missing](docs/nope.md)\n", encoding="utf-8")
            index = copied / "index.html"
            index.write_text(index.read_text().replace('"softwareVersion": "2.9.6"', '"softwareVersion": "2.1.0"'), encoding="utf-8")
            errors = audit(copied)
        self.assertTrue(any("broken link" in error for error in errors))
        self.assertTrue(any("softwareVersion" in error for error in errors))

    def test_mismatched_html_structure_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            index = copied / "index.html"
            index.write_text(index.read_text().replace("</article>", "</div>", 1), encoding="utf-8")
            errors = audit(copied)
        self.assertTrue(any("unexpected" in error for error in errors))

    def test_installation_path_drift_and_internal_jargon_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            onboarding = copied / "docs/workflow/codex-skill-onboarding.md"
            onboarding.write_text(
                onboarding.read_text(encoding="utf-8").replace(
                    "npx skills add joneri/agile-iteration-method",
                    "install the skill somehow",
                    1,
                ),
                encoding="utf-8",
            )
            index = copied / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "Preview before changes",
                    "Collision protection",
                    1,
                ),
                encoding="utf-8",
            )
            errors = audit(copied)
        self.assertTrue(any("installation-path marker" in error for error in errors))
        self.assertTrue(any("internal installer jargon" in error for error in errors))
        self.assertTrue(any("plain-language setup benefit" in error for error in errors))
