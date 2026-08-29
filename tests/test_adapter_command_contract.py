"""Contract tests for AIM adapter command parity."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])(docs/workflow/[A-Za-z0-9._/-]+\.md)"
)
PACKAGE_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])(references/[A-Za-z0-9._/-]+\.md)"
)


class AdapterCommandContractTests(unittest.TestCase):
    def test_reviewed_catalog_repair_is_shared_and_package_owned(self) -> None:
        surfaces = (
            "docs/workflow/adapter-command-contract.md",
            "docs/workflow/agile-iteration-method.md",
            "docs/workflow/working-state-boundaries.md",
            "docs/product/aim-ui.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".github/prompts/repair-catalog-aim.prompt.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/repair-catalog-aim.md",
            "install/aim-install-manifest.yaml",
        )
        combined = "\n".join(
            (REPO_ROOT / relative).read_text(encoding="utf-8")
            for relative in surfaces
        ).lower()
        for marker in (
            "/aim repair-catalog",
            "scripts/aim_catalog_repair.py",
            "runtime-linked",
            "explicit",
            "rollback",
            "read-only",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), combined)

    def _copy_repo(self, temporary: str) -> Path:
        copied = Path(temporary) / "repo"
        shutil.copytree(
            REPO_ROOT,
            copied,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return copied

    def _validate(self, repo: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(repo / "scripts/validate_aim_runtime.py"),
                str(repo),
                "--release",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_complete_adapter_command_contract_is_healthy(self) -> None:
        completed = self._validate(REPO_ROOT)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("canonical command intents: 18", completed.stdout)

    def test_portfolio_chat_intents_preserve_main_thread_ownership(self) -> None:
        canonical = (REPO_ROOT / "docs/workflow/adapter-command-contract.md").read_text(
            encoding="utf-8"
        )
        portable = (
            REPO_ROOT / "adapters/portable/agile-iteration-method/SKILL.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "Activate INC-UI-CONTROL-001",
            "Set portfolio capacity to 2",
            "Focus EPIC-BACKLOG-AIM-UI",
            "Show portfolio status",
            "main AIM thread",
            "fails closed",
            "read-only",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, canonical + portable)

    def test_ui_is_a_first_class_cross_adapter_command(self) -> None:
        surfaces = (
            "docs/workflow/adapter-command-contract.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".github/prompts/ui-aim.prompt.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/ui-aim.md",
        )
        for relative in surfaces:
            content = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(surface=relative):
                self.assertIn("/aim ui", content)
                self.assertIn("loopback", content.lower())
        canonical = (REPO_ROOT / surfaces[0]).read_text(encoding="utf-8")
        for intent in ("start", "open", "status", "stop"):
            self.assertIn(intent, canonical)

    def test_to_backlog_is_a_first_class_cross_adapter_command(self) -> None:
        surfaces = (
            "docs/workflow/adapter-command-contract.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".github/prompts/to-backlog-aim.prompt.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/to-backlog-aim.md",
        )
        for relative in surfaces:
            content = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(surface=relative):
                self.assertIn("/aim to-backlog", content)
        combined = "\n".join(
            (REPO_ROOT / relative).read_text(encoding="utf-8") for relative in surfaces
        )
        for marker in (
            "untrusted evidence",
            "scripts/aim_backlog.py",
            "portfolio-backlog.json",
            "never activate",
            "AIM UI",
        ):
            self.assertIn(marker, combined)

    def test_portfolio_auto_start_is_a_first_class_cross_adapter_contract(self) -> None:
        surfaces = (
            "docs/workflow/adapter-command-contract.md",
            "docs/workflow/agile-iteration-method.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".github/prompts/start-aim.prompt.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/start-aim.md",
        )
        combined = "\n".join(
            (REPO_ROOT / relative).read_text(encoding="utf-8")
            for relative in surfaces
        )
        for marker in (
            '/aim start "PORTFOLIO" mode:auto',
            "immutable",
            "portfolio mandate",
            "scripts/aim_portfolio_run.py",
            ".aim/portfolio-run.json",
            "main AIM thread",
            "/aim continue",
            "fail closed",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), combined.lower())

    def test_portfolio_mandate_closes_and_hands_off_atomically_without_user_stop(self) -> None:
        runtime_surfaces = (
            "docs/workflow/agile-iteration-method.md",
            "docs/workflow/adapter-command-contract.md",
            "docs/workflow/working-state-boundaries.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".claude/skills/aim/SKILL.md",
        )
        for relative in runtime_surfaces:
            content = " ".join(
                (REPO_ROOT / relative).read_text(encoding="utf-8").split()
            ).lower().replace("-", " ")
            with self.subTest(surface=relative):
                self.assertIn("gate e", content)
                self.assertIn("epic closure", content)
                self.assertIn("portfolio_mandate", content)
                self.assertRegex(
                    content,
                    r"(?:completes? the active candidate|completing the (?:active )?candidate)",
                )
                self.assertIn("activation_pending", content)
                self.assertIn("planned", content)
                self.assertIn("runtimeincrementid", content)
                self.assertRegex(
                    content,
                    r"(?:without another user message|no additional user message)",
                )

        contract = (REPO_ROOT / "docs/workflow/adapter-command-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Gate E accepts the Increment only", contract)
        self.assertIn("requires the user", contract)
        self.assertIn("no Gate E action envelope may itself", contract)
        portable = (
            REPO_ROOT / "adapters/portable/agile-iteration-method/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("Final Epic acceptance always remains yours", portable)
        self.assertIn("followed by a separate Epic continuation", portable)

        for relative in (
            ".github/prompts/start-aim.prompt.md",
            ".claude/commands/start-aim.md",
        ):
            content = " ".join(
                (REPO_ROOT / relative).read_text(encoding="utf-8").split()
            ).lower().replace("-", " ")
            with self.subTest(start_surface=relative):
                self.assertIn("epic closure", content)
                self.assertIn("activation_pending", content)
                self.assertIn("planned", content)
                self.assertIn("runtimeincrementid", content)
                self.assertIn("without another user message", content)

    def test_po_recommends_one_restart_safe_epic_disposition_after_gate_e(self) -> None:
        runtime_surfaces = (
            "docs/workflow/agile-iteration-method.md",
            "docs/workflow/adapter-command-contract.md",
            "docs/workflow/working-state-boundaries.md",
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/agents/aim.md",
        )
        for relative in runtime_surfaces:
            content = " ".join(
                (REPO_ROOT / relative).read_text(encoding="utf-8").split()
            ).lower().replace("-", " ")
            with self.subTest(surface=relative):
                for marker in (
                    "done_increment_accepted",
                    "epic goal",
                    "acceptance criteria",
                    "accepted evidence",
                    "non goals",
                    "remaining gaps",
                    "recommend exactly one",
                    "rationale",
                    "resume",
                ):
                    self.assertIn(marker, content)
                self.assertRegex(
                    content,
                    r"`close`, `continue`, or `split`|close, continue, or split",
                )
                self.assertRegex(content, r"(?:must not|never) merely")
                self.assertRegex(content, r"ordinary .*user")

        continue_surface = " ".join(
            (REPO_ROOT / ".claude/commands/continue-aim.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn("done_increment_accepted", continue_surface)
        self.assertIn("recommend exactly one", continue_surface)
        self.assertIn("before any mutation", continue_surface)

        portfolio = (REPO_ROOT / "docs/workflow/adapter-command-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("recommendation is recorded before", portfolio)
        self.assertIn("mandate", portfolio)

        for relative in (
            ".codex/agents/aim-po.toml",
            ".github/agents/aim-po.agent.md",
            ".claude/agents/aim-po.md",
        ):
            content = " ".join(
                (REPO_ROOT / relative).read_text(encoding="utf-8").split()
            ).lower().replace("-", " ")
            with self.subTest(po_specialist=relative):
                self.assertIn("done_increment_accepted", content)
                self.assertIn("accepted evidence", content)
                self.assertIn("remaining gaps", content)
                self.assertIn("recommend exactly one", content)
                self.assertIn("rationale", content)
                self.assertRegex(content, r"(?:must not|never) merely")
                self.assertIn("ordinary user", content)

    def test_start_surfaces_preserve_versioned_cost_selection(self) -> None:
        surfaces = (
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/prompts/start-aim.prompt.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/start-aim.md",
        )
        for relative_path in surfaces:
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(surface=relative_path):
                self.assertIn("stateSchemaVersion", content)
                self.assertIn("read-only", content)
                self.assertIn("cost profile", content.lower())

    def test_status_reports_current_product_release_separately_from_runtime(self) -> None:
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "2.9.5")

        status_surfaces = {
            "canonical": REPO_ROOT / "docs/workflow/adapter-command-contract.md",
            "portable": REPO_ROOT / "adapters/portable/agile-iteration-method/SKILL.md",
            "copilot": REPO_ROOT / ".github/agents/aim.agent.md",
            "claude": REPO_ROOT / ".claude/commands/status-aim.md",
        }
        for surface, path in status_surfaces.items():
            with self.subTest(surface=surface):
                content = " ".join(path.read_text(encoding="utf-8").split())
                self.assertIn("product release", content)
                self.assertIn("VERSION", content)
                self.assertIn("runtime contract", content)
                self.assertIn("aimVersion", content)
                self.assertIn("separately", content)

        state_example = (REPO_ROOT / ".github/agents/aim.agent.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('"aimVersion": "2.0"', state_example)

    def test_missing_claude_command_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            (copied / ".claude/commands/status-aim.md").unlink()
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Result: contradictory", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "Claude legacy compatibility command is missing for /aim status",
            completed.stdout,
        )

    def test_missing_primary_supplier_skill_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            (copied / ".github/skills/aim/SKILL.md").unlink()
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Result: blocked", completed.stdout)
        self.assertIn("onboarding adapter surface is missing", completed.stdout)

    def test_stale_adapter_version_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            copilot = copied / ".github/agents/aim.agent.md"
            content = copilot.read_text(encoding="utf-8")
            copilot.write_text(
                content.replace(
                    '"aimVersion": "2.0"',
                    '"aimVersion": "1.6"',
                    1,
                ),
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Result: contradictory", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn("stale AIM 1.x state example", completed.stdout)

    def test_empty_copilot_upgrade_section_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            copilot = copied / ".github/agents/aim.agent.md"
            content = copilot.read_text(encoding="utf-8")
            start = content.index("## `/aim upgrade` behavior")
            end = content.index("## Interaction model expectations", start)
            copilot.write_text(
                content[:start]
                + "## `/aim upgrade` behavior\n\nSupported packaged upgrade path:\n\n"
                + content[end:],
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Result: contradictory", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "Copilot advertised command behavior is empty or non-actionable",
            completed.stdout,
        )

    def test_onboarding_guidance_drift_is_contradictory_until_regenerated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            portable = copied / "adapters/portable/agile-iteration-method/SKILL.md"
            content = portable.read_text(encoding="utf-8")
            portable.write_text(
                content.replace(
                    "recommend exactly one next action",
                    "show the available AIM commands",
                    1,
                ),
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Result: contradictory", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn("generated public skill validation failed", completed.stdout)

    def test_codex_adapter_install_contains_state_first_onboarding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "repo"
            home = base / "home"
            target.mkdir()
            home.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/aim_install.py"),
                    "--target",
                    str(target),
                    "--home",
                    str(home),
                    "--mode",
                    "personal",
                    "--footprint",
                    "adapters",
                    "--adapter",
                    "codex",
                    "--apply",
                    "--format",
                    "json",
                    "--non-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            plan = json.loads(completed.stdout)
            skill_destination = next(
                destination
                for destination in plan["scopeSummary"]["localDestinations"]
                if destination.endswith("/.agents/skills/agile-iteration-method/SKILL.md")
            )
            content = Path(skill_destination).read_text(encoding="utf-8")
        self.assertIn("Detect onboarding state first", content)
        self.assertIn("recommend exactly one next action", content)
        self.assertIn("You are here", content)
        self.assertIn("do not lead with internal file paths", content)
        self.assertIn("new homes for cats", content)

    def test_claude_adapter_plan_packages_complete_command_family(self) -> None:
        with tempfile.TemporaryDirectory() as target:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/aim_install.py"),
                    "--target",
                    target,
                    "--mode",
                    "personal",
                    "--footprint",
                    "adapters",
                    "--adapter",
                    "claude",
                    "--format",
                    "json",
                    "--non-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        plan = json.loads(completed.stdout)
        destinations = set(plan["scopeSummary"]["repoDestinations"])
        expected = {
            ".claude/skills/aim/SKILL.md",
            ".claude/commands/start-aim.md",
            ".claude/commands/continue-aim.md",
            ".claude/commands/status-aim.md",
            ".claude/commands/validate-aim.md",
            ".claude/commands/help-aim.md",
            ".claude/commands/config-aim.md",
            ".claude/commands/to-backlog-aim.md",
            ".claude/commands/repair-catalog-aim.md",
            ".claude/commands/calibrate-repo.md",
            ".claude/commands/remember-repo.md",
            ".claude/commands/forget-repo.md",
            ".claude/commands/reflect-aim.md",
            ".claude/commands/reflect-all-aim.md",
            ".claude/commands/upgrade-aim.md",
            ".claude/commands/mode-aim.md",
            ".claude/commands/cost-aim.md",
            ".claude/commands/replan-aim.md",
        }
        self.assertTrue(expected.issubset(destinations))

    def test_clean_room_adapter_installs_resolve_required_references(self) -> None:
        for adapter in ("codex", "claude", "copilot"):
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                target = base / "repo"
                home = base / "home"
                target.mkdir()
                home.mkdir()
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "scripts/aim_install.py"),
                        "--target",
                        str(target),
                        "--home",
                        str(home),
                        "--mode",
                        "personal",
                        "--footprint",
                        "adapters",
                        "--adapter",
                        adapter,
                        "--apply",
                        "--format",
                        "json",
                        "--non-interactive",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

                if adapter == "codex":
                    package_root = (
                        home / ".agents/skills/agile-iteration-method"
                    )
                    surfaces = [package_root / "SKILL.md"]
                elif adapter == "claude":
                    package_root = target
                    surfaces = sorted((target / ".claude").rglob("*.md"))
                else:
                    package_root = target
                    surfaces = [
                        *sorted((target / ".github/agents").glob("aim*.agent.md")),
                        *sorted((target / ".github/prompts").glob("*.prompt.md")),
                    ]

                for surface in surfaces:
                    content = surface.read_text(encoding="utf-8")
                    for reference in WORKFLOW_REFERENCE_RE.findall(content):
                        self.assertTrue(
                            (target / reference).is_file(),
                            f"{adapter}: {surface} -> {reference}",
                        )
                    for reference in PACKAGE_REFERENCE_RE.findall(content):
                        self.assertTrue(
                            (package_root / reference).is_file(),
                            f"{adapter}: {surface} -> {reference}",
                        )

    def test_validator_blocks_missing_adapter_closure_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            command = copied / ".claude/commands/status-aim.md"
            command.write_text(
                command.read_text(encoding="utf-8")
                + "\nFollow `docs/workflow/missing-required-contract.md`.\n",
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "required adapter contract is missing",
            completed.stdout,
        )

    def test_card_action_envelopes_remain_intent_not_authority(self) -> None:
        contract = (REPO_ROOT / "docs/workflow/adapter-command-contract.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "Targeted AIM UI action envelopes",
            "never auto-send or execute",
            "user intent, not authority",
            "changed admission",
            "expectedLastGatePassed",
            "portfolio discovery yields exactly",
            "Epic closure remains a separate explicit",
        ):
            self.assertIn(marker, contract)


if __name__ == "__main__":
    unittest.main()
