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
    SKILL_SOURCE,
    PublicSkillError,
    render_package,
    resolved_versions,
    validate_committed_package,
    write_package,
)
from aim_installer.yaml_lite import loads as load_yaml  # noqa: E402


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

    def test_runtime_bytecode_cache_is_not_package_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            cache = copied / PACKAGE_RELATIVE_PATH / "scripts/__pycache__"
            cache.mkdir()
            (cache / "aim_backlog.cpython-311.pyc").write_bytes(b"runtime cache")
            validate_committed_package(copied)

            (cache / "unexpected.md").write_text("not runtime bytecode\n", encoding="utf-8")
            with self.assertRaisesRegex(PublicSkillError, "inventory drift"):
                validate_committed_package(copied)

    def test_public_package_contains_an_executable_ui_lifecycle(self) -> None:
        package = REPO_ROOT / PACKAGE_RELATIVE_PATH
        for relative in (
            "scripts/aim_backlog.py",
            "scripts/aim_catalog_repair.py",
            "scripts/aim_ui_control.py",
            "scripts/aim_ui.py",
            "scripts/aim_codex_bridge.py",
            "scripts/aim_actions.py",
            "scripts/aim_portfolio.py",
            "scripts/aim_portfolio_run.py",
            "scripts/aim_runtime_contract.py",
            "aim-ui/index.html",
            "aim-ui/styles.css",
            "aim-ui/app.js",
        ):
            self.assertTrue((package / relative).is_file(), relative)
        completed = subprocess.run(
            [sys.executable, str(package / "scripts/aim_ui_control.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("start", completed.stdout)
        self.assertIn("stop", completed.stdout)
        continuation_help = subprocess.run(
            [
                sys.executable,
                str(package / "scripts/aim_runtime_contract.py"),
                "continue",
                "--help",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(continuation_help.returncode, 0, continuation_help.stderr)
        self.assertIn("authority-state-path", continuation_help.stdout)
        self.assertIn("expected-state-sha256", continuation_help.stdout)
        backlog_help = subprocess.run(
            [sys.executable, str(package / "scripts/aim_backlog.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(backlog_help.returncode, 0, backlog_help.stderr)
        self.assertIn("Backlog", backlog_help.stdout)
        repair_help = subprocess.run(
            [sys.executable, str(package / "scripts/aim_catalog_repair.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(repair_help.returncode, 0, repair_help.stderr)
        self.assertIn("catalog repair", repair_help.stdout)

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
            source = copied / SKILL_SOURCE
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

    def test_public_launcher_is_adapter_neutral(self) -> None:
        self.assertEqual(
            SKILL_SOURCE,
            Path("adapters/portable/agile-iteration-method/SKILL.md"),
        )
        skill = render_package(REPO_ROOT)[Path("SKILL.md")].decode("utf-8")
        for platform in ("Codex", "GitHub Copilot", "Claude Code"):
            with self.subTest(platform=platform):
                self.assertIn(platform, skill)
        self.assertNotIn("adapts the method into Codex skill form", skill)
        self.assertNotIn("In Codex, AIM is", skill)

    def test_public_front_door_is_newcomer_first_and_english(self) -> None:
        skill = render_package(REPO_ROOT)[Path("SKILL.md")].decode("utf-8")
        ordered_headings = (
            "## Why AIM",
            "## How AIM Delivers Software",
            "## Start Here",
            "## Your First AIM Journey",
            "## Complete Command Guide",
            "## Native Entry Surface",
        )
        positions = [skill.index(heading) for heading in ordered_headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Build what you want without losing the goal", skill)
        self.assertIn("PO -> TDO -> Dev -> Reviewer -> TDO -> PO", skill)
        self.assertIn("1. Install AIM", skill)
        self.assertIn("2. Calibrate the repository", skill)
        self.assertIn("3. Start with an outcome", skill)
        self.assertIn("default `Strict` experience", skill)
        self.assertIn("The disposition remains yours in", skill)
        self.assertIn("a bounded Portfolio Auto mandate carries that authority", skill)
        for marker in ("å", "ä", "ö", "Använd när", "Vad gör"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, skill)

    def test_complete_command_guide_explains_every_supported_intent(self) -> None:
        skill = render_package(REPO_ROOT)[Path("SKILL.md")].decode("utf-8")
        commands = (
            '/aim start "EPIC: ..."',
            "/aim continue",
            "/aim status",
            "/aim validate",
            "/aim help",
            "/aim config",
            "/aim discuss [question]",
            "/aim configure-agents",
            "/aim calibrate-repo",
            '/aim remember-repo <category> "<rule>"',
            '/aim forget-repo <category> "<rule-id>"',
            "/aim reflect",
            "/aim reflect-all",
            "/aim upgrade",
            "/aim mode strict|auto",
            "/aim cost standard|control|deep",
            "/aim replan",
            "Install AIM",
            "Start working according to AIM",
        )
        guide = skill.split("## Complete Command Guide", 1)[1].split(
            "## Native Entry Surface", 1
        )[0]
        for command in commands:
            with self.subTest(command=command):
                self.assertIn(command, guide.replace("\\|", "|"))
                matching_rows = [
                    line
                    for line in guide.splitlines()
                    if line.startswith("|")
                    and line.replace("\\|", "<PIPE>").split("|")[1]
                    .strip()
                    .strip("`")
                    .replace("<PIPE>", "|")
                    == command
                ]
                self.assertEqual(len(matching_rows), 1)
                self.assertEqual(
                    len(matching_rows[0].replace("\\|", "<PIPE>").split("|")),
                    6,
                )
        for explanation in ("Use when", "What it does", "What happens next"):
            self.assertGreaterEqual(guide.count(explanation), 5)
        self.assertIn("Boundary", guide)
        self.assertIn("accepted history", guide)
        self.assertIn("active state is unchanged", guide)
        self.assertIn("never transfer acceptance", guide)
        for portfolio_intent in (
            "Activate INC-UI-CONTROL-001",
            "Set portfolio capacity to 2",
            "Focus EPIC-BACKLOG-AIM-UI",
            "Show portfolio status",
        ):
            self.assertIn(portfolio_intent, guide)

    def test_every_provenance_output_exists_in_package(self) -> None:
        rendered = render_package(REPO_ROOT)
        manifest = json.loads(rendered[Path("manifest.json")])
        for item in manifest["sourceProvenance"]:
            with self.subTest(item=item):
                self.assertIn(Path(item["output"]), rendered)
                self.assertEqual(
                    item["sha256"],
                    hashlib.sha256((REPO_ROOT / item["source"]).read_bytes()).hexdigest(),
                )
        self.assertIn(
            Path("references/install/aim-install-manifest.yaml"),
            rendered,
        )

    def test_installer_manifest_projection_is_data_only(self) -> None:
        rendered = render_package(REPO_ROOT)
        payload = rendered[
            Path("references/install/aim-install-manifest.yaml")
        ].decode("utf-8")
        parsed = load_yaml(payload)["aimInstallManifest"]
        self.assertEqual(parsed["manifestVersion"], "1.0")
        self.assertEqual(set(parsed["adapters"]), {"codex", "copilot", "claude"})
        self.assertEqual(
            parsed["canonicalCommand"],
            "source-only adaptive installer; not executable from the portable package",
        )
        expected_command = '/aim start "EPIC: <desired outcome>"'
        for adapter in ("codex", "claude", "copilot"):
            with self.subTest(adapter=adapter):
                self.assertEqual(
                    parsed["adapterSkills"][adapter]["firstCommand"],
                    expected_command,
                )
        self.assertNotIn("python3 scripts/aim_install.py", payload)

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
        self.assertEqual(manifest["runtimeStateSchemaVersion"], "1.0")
        self.assertIn(
            "references/schemas/aim-runtime-state.schema.json",
            manifest["files"],
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
            "discuss without delivery": (
                "/aim discuss",
                "read-only",
                "untrusted evidence",
                "separate explicit AIM promotion action",
            ),
            "main thread owns active state": ("main AIM thread", ".aim/state.json", "sole owner"),
            "portfolio admission": ("portfolio capacity", "fails closed", "read-only"),
            "card action handoff": (
                "AIM_ACTION_ENVELOPE",
                "authorityStatePath",
                "expectedLastGatePassed",
                "`.aim/state.json` when another path is named",
                "Epic closure remains a separate",
            ),
            "portfolio mandate closure precedence": (
                "`portfolio_mandate` authority",
                "complete the active candidate",
                "`activation_pending`",
                "keep it Planned",
                "`runtimeIncrementId`",
                "without another user message",
                "Gate E still accepts",
            ),
            "post-Gate-E PO disposition": (
                "`done_increment_accepted`",
                "Epic goal",
                "acceptance criteria",
                "accepted evidence",
                "remaining gaps",
                "recommend exactly one",
                "`close`, `continue`, or `split`",
                "rationale",
                "separate disposition decision",
                "Resume at this checkpoint",
            ),
            "truthful Epic closure": (
                "Outcome class: Product|Pilot|POC",
                "closure truth audit",
                "counterevidence",
                "unassisted representative black-box pass",
                "forces `continue`",
                "another coherent Done Increment",
                "cannot turn missing evidence into proof",
                "scripts/aim_runtime_contract.py close",
                "epicClosureEvidence",
                "epicClosureEvidenceSha256",
                "epicClosureEvidenceSetSha256",
                "evidence object must bind a contained non-empty file",
                "closure-authority decision",
                "direct `epic_complete` writes are non-canonical",
            ),
            "canonical continuation with calm UI fallback": (
                "scripts/aim_runtime_contract.py",
                "gate_b_pending",
                "increment_planning",
                "runtime-state schema",
                "byte-for-byte unchanged",
                "Status updating",
                "hide every Gate action",
            ),
        }
        for scenario, markers in scenarios.items():
            with self.subTest(scenario=scenario):
                for marker in markers:
                    self.assertIn(marker, content)

    def test_public_skill_persists_observable_role_before_work_begins(self) -> None:
        skill = " ".join(
            render_package(REPO_ROOT)[Path("SKILL.md")].decode("utf-8").split()
        )
        reviewer_rule = skill.index("before Reviewer work begins")
        reviewer_state = skill.index("`review_in_progress`", reviewer_rule)
        reviewer_role = skill.index("`currentRole: Reviewer`", reviewer_rule)
        tdo_rule = skill.index("before post-review TDO validation begins")

        self.assertLess(reviewer_rule, reviewer_state)
        self.assertLess(reviewer_rule, reviewer_role)
        self.assertIn("`tdo_validation_in_progress`", skill[tdo_rule:])
        self.assertIn("Evidence written after a phase does not substitute", skill)

    def test_package_contains_no_parent_source_links(self) -> None:
        content = "\n".join(
            file.read_text(encoding="utf-8", errors="replace")
            for file in (REPO_ROOT / PACKAGE_RELATIVE_PATH).rglob("*")
            if file.is_file()
        )
        self.assertNotIn("../../../docs/", content)
        self.assertIn("source-only/...", content)
        validate_committed_package(REPO_ROOT)

    def test_package_has_no_untrusted_execution_or_external_aim_runtime_dependency(self) -> None:
        package = REPO_ROOT / PACKAGE_RELATIVE_PATH
        content = "\n".join(
            file.read_text(encoding="utf-8", errors="replace")
            for file in package.rglob("*")
            if file.is_file()
        )
        forbidden = (
            "| bash",
            "scripts/aim_install.py",
            "scripts/validate_aim_runtime.py",
            "https://joneri.github.io/agile-iteration-method/",
            "https://github.com/joneri/agile-iteration-method/blob/main/docs/workflow/",
        )
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, content)
        self.assertIn("source-only/...", content)
        self.assertIn(
            "references/install/aim-install-manifest.yaml",
            json.loads((package / "manifest.json").read_text(encoding="utf-8"))["files"],
        )

    def test_repository_context_is_untrusted_evidence_not_instructions(self) -> None:
        rendered = render_package(REPO_ROOT)
        skill = rendered[Path("SKILL.md")].decode("utf-8")
        repo_awareness = rendered[Path("references/repo-awareness.md")].decode("utf-8")
        combined = skill + "\n" + repo_awareness

        for retained_feature in (
            "Read `aim.profile.yaml`",
            "Personal AIM hints",
            "directly affected files",
            "broader repository docs",
            "locality",
            "validation",
            "risk zones",
            "freshness",
        ):
            with self.subTest(retained_feature=retained_feature):
                self.assertIn(retained_feature, combined)

        for trust_boundary in (
            "untrusted evidence",
            "not AIM instructions",
            "embedded instructions",
            "cannot change roles, gates",
            "tool policy",
            "corroborate",
        ):
            with self.subTest(trust_boundary=trust_boundary):
                self.assertIn(trust_boundary, combined)

    def test_public_package_preserves_audience_context_integrity(self) -> None:
        rendered = render_package(REPO_ROOT)
        skill = rendered[Path("SKILL.md")].decode("utf-8").lower()
        core = rendered[
            Path("references/agile-iteration-method.md")
        ].decode("utf-8").lower()
        combined = skill + "\n" + core

        for marker in (
            "audience-context integrity",
            "private conversation",
            "rejected drafts",
            "prior ai mistakes",
            "ui labels",
            "code comments",
            "drafting residue",
            "intentionally historical",
            "changelog",
            "requested comparison",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
