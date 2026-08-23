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
    PUBLIC_ADAPTIVE_SOURCE_COMMAND,
    PUBLIC_DEMO_POSTER_PATH,
    PUBLIC_DEMO_VIDEO_PATH,
    PUBLIC_ORIGIN,
    PUBLIC_SKILL_INSTALL_COMMAND,
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
            install_content = install_script.read_text(encoding="utf-8")
            self.assertIn("retired for security", install_content)
            for marker in ("curl ", "tar ", "scripts/aim_install.py", "| bash"):
                self.assertNotIn(marker, install_content)
            self.assertTrue((output / "LICENSE").is_file())
            self.assertTrue((output / "licenses/LICENSE-DOCS").is_file())
            self.assertGreater((output / PUBLIC_DEMO_VIDEO_PATH).stat().st_size, 1_000_000)
            self.assertGreater((output / PUBLIC_DEMO_POSTER_PATH).stat().st_size, 10_000)
            for relative_path in SCHEMA_RELATIVE_PATHS:
                schema = json.loads(
                    (output / relative_path).read_text(encoding="utf-8")
                )
                self.assertEqual(schema["$id"], expected_schema_id(relative_path))
            manifest = json.loads(
                (output / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["aimVersion"], "2.8.0")
            self.assertEqual(manifest["runtimeContractVersion"], "2.0")
            self.assertEqual(manifest["runtimeStateSchemaVersion"], "1.0")
            self.assertIn(
                "schemas/aim-runtime-state.schema.json",
                [item["path"] for item in manifest["schemas"]],
            )
            self.assertIn(
                "schemas/aim-portfolio-run.schema.json",
                [item["path"] for item in manifest["schemas"]],
            )
            self.assertEqual(manifest["installerManifestVersion"], "1.0")
            self.assertEqual(manifest["aimUi"]["version"], "1")
            self.assertEqual(manifest["aimUi"]["releaseStage"], "beta")
            self.assertEqual(
                manifest["aimUi"]["availability"],
                "public-skill-and-adaptive-installer",
            )
            self.assertEqual(manifest["aimUi"]["chatLaunch"], "/aim ui")
            self.assertTrue(manifest["aimUi"]["readOnly"])
            self.assertTrue(manifest["aimUi"]["multiEpic"])
            self.assertTrue(manifest["aimUi"]["cardActions"])
            self.assertEqual(
                manifest["aimUi"]["portfolioAutoDemo"], PUBLIC_DEMO_VIDEO_PATH
            )
            self.assertEqual(
                manifest["aimUi"]["repoLaunch"], "python3 scripts/aim_ui.py"
            )
            self.assertEqual(manifest["publicOrigin"], PUBLIC_ORIGIN)
            self.assertEqual(
                manifest["install"]["portableSkillCommand"],
                PUBLIC_SKILL_INSTALL_COMMAND,
            )
            self.assertEqual(
                manifest["install"]["adaptiveSourceCommand"],
                PUBLIC_ADAPTIVE_SOURCE_COMMAND,
            )
            self.assertEqual(
                manifest["install"]["remoteBootstrap"]["status"],
                "retired-fail-closed",
            )
            self.assertIn("publication-artifact", manifest["requiredChecks"])

    def test_public_install_choices_are_visible_from_public_sources(self) -> None:
        validate_source(REPO_ROOT)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        index = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
        getting_started = (
            REPO_ROOT / "docs/product/getting-started.md"
        ).read_text(encoding="utf-8")
        platforms = (
            REPO_ROOT / "docs/product/platforms-and-adoption.md"
        ).read_text(encoding="utf-8")

        def collapsed(content: str) -> str:
            return " ".join(content.replace("\\\n", " ").split())

        self.assertIn(PUBLIC_ADAPTIVE_SOURCE_COMMAND, readme)
        self.assertIn(PUBLIC_ADAPTIVE_SOURCE_COMMAND, index)
        self.assertIn(PUBLIC_ADAPTIVE_SOURCE_COMMAND, getting_started)
        self.assertIn(PUBLIC_ADAPTIVE_SOURCE_COMMAND, platforms)
        for content in (readme, index, getting_started, platforms):
            self.assertIn(PUBLIC_SKILL_INSTALL_COMMAND, collapsed(content))
            self.assertNotIn("| bash", content)
        self.assertIn(
            "https://skills.sh/joneri/agile-iteration-method/agile-iteration-method",
            index,
        )
        self.assertIn("## Smarter output from the start", readme)
        self.assertIn("audience-context integrity", readme)
        self.assertIn("Writes for the reader, not its own chat", index)
        self.assertIn("Private conversations, rejected drafts", index)
        self.assertIn('id="ui"', index)
        self.assertIn("docs/product/aim-ui.md", index)
        self.assertIn('alt="AIM 2.8.0 Agile Iteration Method logo"', index)
        self.assertIn('<span class="brand-version">2.8.0</span>', index)
        self.assertIn("Put the backlog in motion.", index)
        self.assertIn("Keep control.", index)
        self.assertIn("github-pages/assets/images/aim-ui-beta-control-room.png", index)
        self.assertIn(PUBLIC_DEMO_VIDEO_PATH, index)
        self.assertIn(PUBLIC_DEMO_POSTER_PATH, index)
        self.assertIn('preload="metadata"', index)
        self.assertNotIn('autoplay', index)
        for command in (
            "/aim upgrade",
            "/aim calibrate-repo",
            "/aim remember-repo",
            "/aim reflect",
            "/aim reflect-all",
        ):
            self.assertIn(command, readme)
            self.assertIn(command, index)
            self.assertIn(command, getting_started)

    def test_brand_artwork_has_release_dimensions_and_version_inventory(self) -> None:
        validate_source(REPO_ROOT)
        inventory = (
            REPO_ROOT / "github-pages/assets/images/README.md"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(inventory.count("AIM 2.8.0"), 3)
        self.assertIn("AIM UI Beta", inventory)

    def test_stale_brand_artwork_version_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            index = copied / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    '<span class="brand-version">2.8.0</span>',
                    '<span class="brand-version">2.7</span>',
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                PublicationError, "brand-version must match VERSION"
            ):
                validate_source(copied)

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

    def test_remote_downloading_bootstrap_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            install_script = copied / "install.sh"
            install_script.write_text(
                install_script.read_text(encoding="utf-8")
                + "\ncurl https://example.invalid/archive.tar.gz\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicationError, "download remote code"):
                validate_source(copied)

    def test_remote_execution_bootstrap_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            install_script = copied / "install.sh"
            install_script.write_text(
                install_script.read_text(encoding="utf-8")
                + "\npython3 scripts/aim_install.py\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicationError, "execute repository code"):
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
            "python3 scripts/build_public_skill.py --check",
            "python3 scripts/validate_public_skill_cli.py --source .",
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
            "REQUESTED_VERSION: ${{ inputs.version }}",
            'version="${REQUESTED_VERSION}"',
            'git rev-parse "${version}^{commit}"',
            "Checked-out source does not match release tag",
        ):
            self.assertIn(marker, release_workflow)
        run_blocks = release_workflow.split("run: |", 1)[1]
        self.assertNotIn("${{ inputs.version }}", run_blocks)
        requested_ref = (
            "${{ github.event_name == 'workflow_dispatch' "
            "&& inputs.version || github.ref }}"
        )
        self.assertIn(
            "release-gate:\n"
            "    uses: ./.github/workflows/release-readiness.yml\n"
            "    with:\n"
            f"      release_ref: {requested_ref}",
            release_workflow,
        )
        self.assertIn(
            "- name: Checkout\n"
            "        uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 0\n"
            f"          ref: {requested_ref}",
            release_workflow,
        )

        readiness_workflow = (
            REPO_ROOT / ".github/workflows/release-readiness.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("release_ref:", readiness_workflow)
        self.assertIn("ref: ${{ inputs.release_ref || github.ref }}", readiness_workflow)

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
