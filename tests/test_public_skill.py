"""Generated public Agent Skill contract tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_public_skill import (  # noqa: E402
    GENERATED_NOTICE,
    PACKAGE_RELATIVE_PATH,
    PUBLIC_SKILL_PACKAGE_VERSION,
    PublicSkillError,
    render_package,
    resolved_versions,
    validate_committed_package,
    write_package,
)


class PublicSkillTests(unittest.TestCase):
    def _copy_repo(self, temporary: str) -> Path:
        copied = Path(temporary) / "repo"
        shutil.copytree(
            REPO_ROOT,
            copied,
            ignore=shutil.ignore_patterns(".git", ".aim", "__pycache__", "*.pyc"),
        )
        return copied

    def test_committed_package_matches_canonical_sources(self) -> None:
        validate_committed_package(REPO_ROOT)

    def test_generation_is_byte_identical_in_clean_directories(self) -> None:
        rendered = render_package(REPO_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            write_package(REPO_ROOT, rendered, first)
            write_package(REPO_ROOT, render_package(REPO_ROOT), second)
            first_hashes = {
                file.relative_to(first): hashlib.sha256(file.read_bytes()).hexdigest()
                for file in first.rglob("*")
                if file.is_file()
            }
            second_hashes = {
                file.relative_to(second): hashlib.sha256(file.read_bytes()).hexdigest()
                for file in second.rglob("*")
                if file.is_file()
            }
        self.assertEqual(first_hashes, second_hashes)

    def test_check_mode_is_read_only(self) -> None:
        package = REPO_ROOT / PACKAGE_RELATIVE_PATH
        before = {
            file.relative_to(package): (file.stat().st_mtime_ns, file.read_bytes())
            for file in package.rglob("*")
            if file.is_file()
        }
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/build_public_skill.py"), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        after = {
            file.relative_to(package): (file.stat().st_mtime_ns, file.read_bytes())
            for file in package.rglob("*")
            if file.is_file()
        }
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(before, after)

    def test_canonical_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            canonical = copied / "docs/workflow/adapter-command-contract.md"
            canonical.write_text(
                canonical.read_text(encoding="utf-8") + "\nCanonical drift.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicSkillError, "stale or manually edited"):
                validate_committed_package(copied)

    def test_manual_generated_edit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            generated = copied / PACKAGE_RELATIVE_PATH / "SKILL.md"
            generated.write_text(
                generated.read_text(encoding="utf-8") + "\nManual edit.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicSkillError, "stale or manually edited"):
                validate_committed_package(copied)

    def test_invalid_canonical_frontmatter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            source = copied / "adapters/codex/agile-iteration-method/SKILL.md"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "name: agile-iteration-method",
                    "name:",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicSkillError, "frontmatter 'name' is required"):
                render_package(copied)

    def test_generation_never_mutates_active_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            state = copied / ".aim/state.json"
            state.parent.mkdir()
            sentinel = '{"epicId":"EPIC-SENTINEL","epicStatus":"increment_in_progress"}\n'
            state.write_text(sentinel, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(copied / "scripts/build_public_skill.py")],
                cwd=copied,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(state.read_text(encoding="utf-8"), sentinel)

    def test_generated_files_carry_ownership_notice(self) -> None:
        rendered = render_package(REPO_ROOT)
        compact_notice = GENERATED_NOTICE.replace("\n", " ")
        for path, payload in rendered.items():
            content = payload.decode("utf-8", errors="replace")
            with self.subTest(path=path):
                self.assertTrue(
                    GENERATED_NOTICE in content or compact_notice in content,
                    f"missing generated notice in {path}",
                )

    def test_version_contracts_are_separate_and_current(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / PACKAGE_RELATIVE_PATH / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        canonical = resolved_versions(REPO_ROOT)
        for key, value in canonical.items():
            self.assertEqual(manifest[key], value)
        self.assertEqual(
            manifest["publicSkillPackageVersion"], PUBLIC_SKILL_PACKAGE_VERSION
        )
        self.assertNotEqual(
            manifest["productVersion"], manifest["runtimeContractVersion"]
        )
        self.assertEqual(
            set(manifest["profileSchemaVersions"]),
            {"personalHints", "projectRoles", "repoProfile"},
        )

    def test_required_aim_scenarios_have_semantic_routes(self) -> None:
        package = REPO_ROOT / PACKAGE_RELATIVE_PATH
        content = "\n".join(
            file.read_text(encoding="utf-8", errors="replace")
            for file in package.rglob("*")
            if file.is_file()
        )
        scenarios = {
            "help": ("/aim help", "Recommended next action"),
            "not calibrated": ("Installed but not calibrated", "/aim calibrate-repo"),
            "calibrated without Epic": ("Calibrated but no Epic exists", "/aim start"),
            "Epic not approved": ("Epic exists but is not approved", "Gate A"),
            "approved Epic needs increment": ("TDO", "Done Increment", "Gate B"),
            "Dev completed and review required": ("Gate C", "Reviewer", "Gate D"),
            "scope change": ("scope expansion beyond Gate B", "escalation"),
            "sequential fallback": ("sequential fallback", "without changing the runtime contract"),
            "configure agents": ("/aim configure-agents", "aim.roles.yaml", "selected"),
            "main thread owns active state": ("main AIM thread", ".aim/state.json", "sole owner"),
        }
        for scenario, markers in scenarios.items():
            with self.subTest(scenario=scenario):
                for marker in markers:
                    self.assertIn(marker, content)

    def test_package_contains_no_parent_source_links(self) -> None:
        content = "\n".join(
            file.read_text(encoding="utf-8", errors="replace")
            for file in (REPO_ROOT / PACKAGE_RELATIVE_PATH).rglob("*")
            if file.is_file()
        )
        self.assertNotIn("../../../docs/", content)
        self.assertIn("optional source-repository", content)
        validate_committed_package(REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
