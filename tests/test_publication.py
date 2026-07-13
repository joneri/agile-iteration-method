"""Release-publication contract tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_publication import (  # noqa: E402
    PUBLIC_INSTALL_COMMAND,
    PUBLIC_ORIGIN,
    PublicationError,
    SCHEMA_RELATIVE_PATHS,
    build_artifact,
    expected_schema_id,
    validate_artifact,
    validate_source,
)


class PublicationContractTests(unittest.TestCase):
    def _copy_repo(self, temporary: str) -> Path:
        copied = Path(temporary) / "repo"
        shutil.copytree(
            REPO_ROOT,
            copied,
            ignore=shutil.ignore_patterns(".git", ".aim", "__pycache__", "*.pyc"),
        )
        return copied

    def test_publication_artifact_contains_schemas_and_licenses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(REPO_ROOT, output)
            validate_artifact(output)

            install_script = output / "install.sh"
            self.assertTrue(install_script.is_file())
            self.assertTrue(install_script.stat().st_mode & 0o111)
            self.assertIn(
                "archive/${AIM_REF}.tar.gz",
                install_script.read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                'set -- --target "$AIM_TARGET"',
                install_script.read_text(encoding="utf-8"),
            )
            self.assertTrue((output / "LICENSE").is_file())
            self.assertTrue((output / "licenses/LICENSE-DOCS").is_file())
            for relative_path in SCHEMA_RELATIVE_PATHS:
                schema = json.loads(
                    (output / relative_path).read_text(encoding="utf-8")
                )
                self.assertEqual(schema["$id"], expected_schema_id(relative_path))
            manifest = json.loads(
                (output / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["aimVersion"], "2.2.0")
            self.assertEqual(manifest["runtimeContractVersion"], "2.0")
            self.assertEqual(manifest["installerManifestVersion"], "0.7")
            self.assertEqual(manifest["publicOrigin"], PUBLIC_ORIGIN)
            self.assertEqual(manifest["install"]["command"], PUBLIC_INSTALL_COMMAND)
            self.assertEqual(manifest["install"]["defaultRef"], "main")
            self.assertIn("publication-artifact", manifest["requiredChecks"])

    def test_public_install_command_is_visible_from_public_sources(self) -> None:
        validate_source(REPO_ROOT)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        index = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
        getting_started = (
            REPO_ROOT / "docs/product/getting-started.md"
        ).read_text(encoding="utf-8")

        self.assertIn(PUBLIC_INSTALL_COMMAND, readme)
        self.assertIn(PUBLIC_INSTALL_COMMAND, index)
        self.assertIn(PUBLIC_INSTALL_COMMAND, getting_started)
        for command in ("/aim upgrade", "/aim calibrate-repo", "/aim remember-repo"):
            self.assertIn(command, readme)
            self.assertIn(command, index)
            self.assertIn(command, getting_started)

    def test_schema_id_drift_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            schema_path = copied / SCHEMA_RELATIVE_PATHS[0]
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["$id"] = "https://example.invalid/profile.schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            with self.assertRaisesRegex(PublicationError, r"\$id must be"):
                validate_source(copied)

    def test_missing_public_source_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            (copied / "robots.txt").unlink()
            with self.assertRaisesRegex(PublicationError, "robots.txt"):
                validate_source(copied)

    def test_tag_only_install_bootstrap_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            install_script = copied / "install.sh"
            content = install_script.read_text(encoding="utf-8")
            install_script.write_text(
                content.replace(
                    'AIM_REF="${AIM_REF:-${AIM_VERSION:-main}}"',
                    'AIM_VERSION="${AIM_VERSION:-v2.0}"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicationError, "default branch"):
                validate_source(copied)

    def test_bootstrap_forcing_current_directory_target_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            install_script = copied / "install.sh"
            content = install_script.read_text(encoding="utf-8")
            install_script.write_text(
                content.replace(
                    'if ! has_arg "--source" "$@"; then',
                    'set -- --target "$AIM_TARGET" "$@"\nif ! has_arg "--source" "$@"; then',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicationError, "current directory target"):
                validate_source(copied)

    def test_incomplete_assembled_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(REPO_ROOT, output)
            (output / SCHEMA_RELATIVE_PATHS[1]).unlink()
            with self.assertRaisesRegex(PublicationError, "incomplete"):
                validate_artifact(output)

    def test_builder_refuses_nonempty_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            output.mkdir()
            (output / "keep.txt").write_text("do not delete\n", encoding="utf-8")
            with self.assertRaisesRegex(PublicationError, "nonempty"):
                build_artifact(REPO_ROOT, output)
            self.assertEqual(
                (output / "keep.txt").read_text(encoding="utf-8"),
                "do not delete\n",
            )

    def test_pages_workflow_depends_on_reusable_release_gate(self) -> None:
        pages = (REPO_ROOT / ".github/workflows/publish-pages.yml").read_text(
            encoding="utf-8"
        )
        release = (
            REPO_ROOT / ".github/workflows/release-readiness.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/release-readiness.yml", pages)
        self.assertIn("needs: release-gate", pages)
        self.assertIn(
            "python3 scripts/validate_publication.py --output site", pages
        )
        for marker in (
            "workflow_call:",
            "workflow_dispatch:",
            "python3 -m compileall -q scripts tests",
            "python3 -m unittest discover -s tests -v",
            "python3 scripts/audit_documentation.py .",
            "python3 scripts/validate_aim_runtime.py . --release",
            "python3 scripts/validate_publication.py --output site",
            "include-hidden-files: true",
        ):
            self.assertIn(marker, release)

    def test_release_workflow_publishes_versioned_assets_after_gate(self) -> None:
        release_workflow = (
            REPO_ROOT / ".github/workflows/release.yml"
        ).read_text(encoding="utf-8")
        for marker in (
            'tags:',
            '- "v*"',
            "uses: ./.github/workflows/release-readiness.yml",
            "needs: release-gate",
            "python3 scripts/validate_publication.py --output site",
            "aim-pages-${version}.tar.gz",
            "aim-install-${version}.sh",
            "aim-release-manifest-${version}.json",
            "gh release create",
            "gh release upload",
            "--verify-tag",
            'declared="v$(tr -d',
        ):
            self.assertIn(marker, release_workflow)

    def test_release_validator_passes_without_local_runtime_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(copied / "scripts/validate_aim_runtime.py"),
                    str(copied),
                    "--release",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("release mode: local .aim runtime workspace is optional", completed.stdout)
        self.assertIn("Release readiness: PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
