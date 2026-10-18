"""Release-publication contract tests."""

from __future__ import annotations

import json
import os
import textwrap
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_publication import (  # noqa: E402
    PUBLIC_ADAPTIVE_SOURCE_COMMAND,
    PUBLIC_CAMPAIGN_IMAGE_PATH,
    PUBLIC_ORIGIN,
    PUBLIC_EVALUATION_PATH,
    PUBLIC_PRODUCT_CAPTURES,
    PUBLIC_PRESS_KIT_PATH,
    PUBLIC_PRESS_MEMBERS,
    PUBLIC_SITE_ASSETS,
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
            for retired in (
                "github-pages/assets/images/aim-3-autonomy-logo.png",
                "github-pages/assets/images/aim-ui-beta-control-room.png",
                "github-pages/assets/images/portfolio-auto-demo-poster.jpg",
                "github-pages/assets/video/portfolio-auto-demo.mp4",
            ):
                self.assertFalse((output / retired).exists(), retired)
            for relative_path in SCHEMA_RELATIVE_PATHS:
                schema = json.loads(
                    (output / relative_path).read_text(encoding="utf-8")
                )
                self.assertEqual(schema["$id"], expected_schema_id(relative_path))
            manifest = json.loads(
                (output / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["aimVersion"], (REPO_ROOT / "VERSION").read_text().strip())
            self.assertEqual({item["path"] for item in manifest["schemas"]},
                             {p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "schemas").glob("*.schema.json")})
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
            self.assertEqual(manifest["aimUi"]["defaultBoard"], "increment")
            self.assertEqual(
                manifest["aimUi"]["availability"],
                "public-skill-and-adaptive-installer",
            )
            self.assertEqual(manifest["aimUi"]["chatLaunch"], "/aim ui")
            self.assertTrue(manifest["aimUi"]["readOnly"])
            self.assertTrue(manifest["aimUi"]["multiEpic"])
            self.assertTrue(manifest["aimUi"]["cardActions"])
            self.assertNotIn("portfolioAutoDemo", manifest["aimUi"])
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
        for identifier in ("ui", "method", "evidence", "start"):
            self.assertIn(f'id="{identifier}"', index)
        self.assertIn("docs/product/aim-ui.md", index)
        self.assertIn(f'src="{PUBLIC_CAMPAIGN_IMAGE_PATH}"', index)
        version = (REPO_ROOT / "VERSION").read_text().strip()
        self.assertIn('<span class="brand-version">Latest</span>', index)
        self.assertIn(f'"softwareVersion": "{version}"', index)
        for capture in PUBLIC_PRODUCT_CAPTURES:
            self.assertIn(f'src="{capture}"', index)
        evidence = json.loads((REPO_ROOT / PUBLIC_EVALUATION_PATH).read_text())
        self.assertIn(f'data-evidence-version="{evidence["latestEvaluatedVersion"]}"', index)
        self.assertNotIn("aim-ui-beta-control-room.png", index)
        self.assertNotIn("portfolio-auto-demo", index)
        self.assertNotIn("aim-ui-beta-control-room.png", readme)
        for command in (
            "/aim upgrade",
            "/aim calibrate-repo",
            "/aim remember-repo",
        ):
            self.assertIn(command, readme)
            self.assertIn(command, index)
            self.assertIn(command, getting_started)
        for content in (readme, index, getting_started):
            self.assertIn("retired compatibility aliases", collapsed(content))
            self.assertNotIn("/aim reflect", content)

    def test_brand_artwork_has_release_dimensions_and_versionless_inventory(self) -> None:
        validate_source(REPO_ROOT)
        inventory = (
            REPO_ROOT / "github-pages/assets/images/README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Brand artwork version policy: versionless", inventory)
        self.assertIn("contain no product version", inventory)
        self.assertIn("aim-4-logo.png", inventory)
        self.assertIn("aim-control-board.png", inventory)

    def test_changed_aim_4_campaign_artwork_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            artwork = copied / PUBLIC_CAMPAIGN_IMAGE_PATH
            payload = bytearray(artwork.read_bytes())
            payload[-1] ^= 1
            artwork.write_bytes(payload)

            with self.assertRaisesRegex(PublicationError, "press kit does not match|campaign artwork changed"):
                validate_source(copied)

    def test_single_installation_has_terminal_and_self_contained_agent_routes(self) -> None:
        import html
        import re
        index = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
        setup = index[index.index('<header class="hero-intro"'):index.index("</header>")]
        self.assertIn('id="terminal-install"', setup)
        self.assertIn('id="agent-install"', setup)
        self.assertIn('data-copy="terminal-command"', setup)
        self.assertIn('data-copy="agent-prompt"', setup)
        self.assertIn(PUBLIC_SKILL_INSTALL_COMMAND, setup)
        self.assertEqual(index.count('id="terminal-install"'), 1)
        self.assertEqual(index.count('id="agent-install"'), 1)
        prompt = (REPO_ROOT / "github-pages/assets/aim-install-agent.txt").read_text().strip()
        displayed = re.search(r'<code id="agent-prompt">(.*?)</code>', setup, re.S)
        self.assertIsNotNone(displayed)
        self.assertEqual(html.unescape(displayed.group(1)), prompt)
        self.assertIn(PUBLIC_SKILL_INSTALL_COMMAND, prompt)
        for instruction in ("project scope", "/aim calibrate-repo", "outcome", "session restart"):
            self.assertIn(instruction, prompt)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(REPO_ROOT, output)
            self.assertEqual((output / "github-pages/assets/aim-install-agent.txt").read_text().strip(), prompt)

    def test_press_downloads_match_their_sources(self) -> None:
        validate_source(REPO_ROOT)
        with zipfile.ZipFile(REPO_ROOT / PUBLIC_PRESS_KIT_PATH) as archive:
            self.assertEqual(set(archive.namelist()), PUBLIC_PRESS_MEMBERS)
            self.assertEqual(archive.read("aim-4-logo.png"), (REPO_ROOT / PUBLIC_CAMPAIGN_IMAGE_PATH).read_bytes())
            self.assertIn(b"Agile Iteration Method (AIM)", archive.read("aim-4-press-kit.txt"))

    def test_missing_install_script_blocks_assembled_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(REPO_ROOT, output)
            (output / PUBLIC_SITE_ASSETS[1]).unlink()
            with self.assertRaisesRegex(PublicationError, "interactive site asset is missing"):
                validate_artifact(output)

    def test_missing_press_member_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            archive_path = copied / PUBLIC_PRESS_KIT_PATH
            with zipfile.ZipFile(archive_path) as archive:
                members = {name: archive.read(name) for name in archive.namelist() if name != "logo-generation.txt"}
            with zipfile.ZipFile(archive_path, "w") as archive:
                for name, content in members.items():
                    archive.writestr(name, content)
            with self.assertRaisesRegex(PublicationError, "missing, unexpected or corrupt"):
                validate_source(copied)

    def test_unlabelled_capture_stale_comparison_and_broken_section_link_are_rejected(self) -> None:
        evidence = json.loads((REPO_ROOT / PUBLIC_EVALUATION_PATH).read_text())
        evaluated = evidence["latestEvaluatedVersion"]
        reference = evidence["referenceVersion"]
        for before, after, expected in (
            ('data-product-capture="example"', 'data-product-capture="live"', "example caption"),
            ('Actual AIM UI 4.1.0 · Desktop Kanban board with example project data.', 'Actual AIM UI 4.1.0 · Live project.', "example caption"),
            (f'data-evidence-version="{evaluated}"', 'data-evidence-version="unassessed"', "tested AIM version"),
            (reference, "unattributed-reference", "tested AIM version"),
            ('href="#start"', 'href="#missing"', "broken section link"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                copied = self._copy_repo(temporary)
                index = copied / "index.html"
                content = index.read_text(encoding="utf-8")
                self.assertIn(before, content, "The negative-case mutation must match current markup")
                index.write_text(content.replace(before, after), encoding="utf-8")
                with self.assertRaisesRegex(PublicationError, expected):
                    validate_source(copied)

    def test_missing_product_capture_blocks_assembled_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(REPO_ROOT, output)
            (output / PUBLIC_PRODUCT_CAPTURES[0]).unlink()
            with self.assertRaisesRegex(PublicationError, "AIM UI capture is missing"):
                validate_artifact(output)

    def test_product_capture_requires_accessible_description(self) -> None:
        import re
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            page = copied / "index.html"
            markup = page.read_text()
            markup, count = re.subn(
                r'(<img src="' + re.escape(PUBLIC_PRODUCT_CAPTURES[0]) + r'"[^>]*?alt=")[^"]*',
                r'\1', markup,
            )
            self.assertEqual(count, 1)
            page.write_text(markup)
            with self.assertRaisesRegex(PublicationError, "alt text"):
                validate_source(copied)

    def test_missing_versionless_artwork_policy_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            inventory = copied / "github-pages/assets/images/README.md"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    "Brand artwork version policy: versionless",
                    "Brand artwork version policy: unspecified",
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PublicationError, "declare the artwork versionless"):
                validate_source(copied)

    def test_changed_brand_artwork_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            artwork = copied / "AIM_OG.png"
            payload = bytearray(artwork.read_bytes())
            payload[-1] ^= 1
            artwork.write_bytes(payload)

            with self.assertRaisesRegex(
                PublicationError,
                "differs from the approved versionless source",
            ):
                validate_source(copied)

    def test_stale_brand_artwork_version_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            index = copied / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    f'"softwareVersion": "{(REPO_ROOT / "VERSION").read_text().strip()}"',
                    '"softwareVersion": "2.7"',
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                PublicationError, "softwareVersion must match VERSION"
            ):
                validate_source(copied)

    def test_public_evaluation_headline_must_match_its_measured_row(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            path = copied / PUBLIC_EVALUATION_PATH
            evidence = json.loads(path.read_text())
            evidence["latestProductScore"] = 100
            path.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(PublicationError, "headline score differs"):
                validate_source(copied)

    def test_evaluation_rejects_boolean_nonfinite_and_out_of_range_scores(self) -> None:
        from aim_publication import _evaluation_contract
        original = json.loads((REPO_ROOT / PUBLIC_EVALUATION_PATH).read_text())
        for invalid in (True, False, float("nan"), float("inf"), -1, 101):
            with self.subTest(score=invalid), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / PUBLIC_EVALUATION_PATH
                path.parent.mkdir(parents=True)
                evidence = json.loads(json.dumps(original))
                for prefix, version_key in (("latest", "latestEvaluatedVersion"), ("reference", "referenceVersion")):
                    evidence[prefix + "ProductScore"] = invalid
                    next(row for row in evidence["rows"] if row["version"] == evidence[version_key])["score"] = invalid
                path.write_text(json.dumps(evidence))
                with self.assertRaisesRegex(PublicationError, "finite numbers"):
                    _evaluation_contract(root)

    def test_release_prerelease_flags_with_stubbed_github_cli(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text()
        block = workflow.split("      - name: Publish GitHub Release", 1)[1].split("run: |", 1)[1]
        block = textwrap.dedent(block)
        stub = '''gh() {
          printf '%s\n' "$*" >> "$AIM_RELEASE_TEST_LOG"
          if [[ "$1 $2" == "release view" ]]; then return "$AIM_RELEASE_TEST_EXISTS"; fi
        }
'''
        for version in ("v4.4.0-rc.12", "v4.4.0"):
            for existing in (0, 1):
                with self.subTest(version=version, existing=existing), tempfile.TemporaryDirectory() as temporary:
                    log = Path(temporary) / "commands.txt"
                    env = dict(os.environ, AIM_RELEASE_TEST_LOG=str(log), AIM_RELEASE_TEST_EXISTS=str(existing))
                    result = subprocess.run(["bash", "-c", stub + block.replace("${{ steps.version.outputs.version }}", version)],
                                            env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    commands = log.read_text().splitlines()
                    mutations = [line for line in commands if line.startswith(("release create", "release edit"))]
                    if "-" in version:
                        self.assertTrue(mutations)
                        self.assertTrue(all("--prerelease" in line and "--latest=false" in line for line in mutations))
                    else:
                        self.assertTrue(mutations)
                        self.assertTrue(all("--prerelease=false" in line and "--latest" in line
                                            and "--latest=false" not in line for line in mutations))

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
