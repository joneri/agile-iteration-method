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

    def test_stable_release_preserves_candidate_history_but_rejects_duplicate_release(self) -> None:
        version = (ROOT / "VERSION").read_text().strip()
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            changelog = copied / "CHANGELOG.md"
            changelog.write_text(changelog.read_text() +
                                 f"\n## 2026-10-17 - AIM release v{version}-rc.99\n", encoding="utf-8")
            self.assertFalse(any("current release must have" in error for error in audit(copied)))
            changelog.write_text(changelog.read_text() +
                                 f"\n## 2026-10-18 - AIM release v{version}\n", encoding="utf-8")
            self.assertTrue(any("current release must have" in error for error in audit(copied)))

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
            index.write_text(index.read_text().replace(f'"softwareVersion": "{(ROOT / "VERSION").read_text().strip()}"', '"softwareVersion": "2.1.0"'), encoding="utf-8")
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

    def test_current_release_claims_do_not_inherit_historical_version(self) -> None:
        version = (ROOT / "VERSION").read_text().strip()
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            press = copied / "github-pages/assets/press/aim-4-press-kit.txt"
            press.write_text(press.read_text().replace(f"Release version: {version}", "Release version: 2.1.0"))
            errors = audit(copied)
        self.assertTrue(any("stale current release claim" in error for error in errors))
        self.assertFalse(any("CHANGELOG.md" in error for error in errors))

    def test_source_routing_and_self_install_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            guide = copied / "docs/workflow/troubleshoot-aim-2.0.md"
            guide.write_text(guide.read_text().replace("adapter-command-contract.md#runtime-source-routing", "adapter-command-contract.md"))
            onboarding = copied / "docs/workflow/codex-skill-onboarding.md"
            onboarding.write_text(onboarding.read_text() + "\nFrom AIM source: python3 scripts/aim_install.py --target . --dry-run\n")
            errors = audit(copied)
        self.assertTrue(any("runtime source routing" in error for error in errors))
        self.assertTrue(any("cannot install into itself" in error for error in errors))

    def test_missing_current_features_and_native_command_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy(temporary)
            overview = copied / "docs/product/what-is-aim.md"
            overview.write_text(overview.read_text().replace("Loop", "Iterations"))
            entry = copied / "docs/workflow/adapter-entry-model.md"
            entry.write_text(entry.read_text().replace("`/aim graph`", "`/aim diagram`"))
            errors = audit(copied)
        self.assertTrue(any("missing current delivery feature 'Loop'" in error for error in errors))
        self.assertTrue(any("incomplete command family; missing graph" in error for error in errors))

    def test_missing_current_surfaces_report_drift_without_crashing(self) -> None:
        for relative in ("docs/workflow/adapter-skill-bootstrap.md",
                         "docs/workflow/adapter-entry-model.md",
                         "docs/product/what-is-aim.md",
                         "github-pages/assets/press/launch-copy-en.txt"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                copied = self._copy(temporary)
                (copied / relative).unlink()
                errors = audit(copied)
                self.assertTrue(any(relative in error and "cannot read required surface" in error for error in errors))
