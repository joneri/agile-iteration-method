"""Focused tests for the AIM guided installer UX and deterministic apply engine."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from aim_installer import apply, guided, planner, render  # noqa: E402
from aim_installer.manifest import load_manifest  # noqa: E402
import aim_install  # noqa: E402


class _UnusedManifest:
    gitignore_fragments: list[str] = []
    runtime_exclusions: list[str] = []


def _collision_plan() -> dict:
    return {
        "blockers": [],
        "mode": "team",
        "gitignoreFragments": [],
        "actions": [
            {
                "category": "file",
                "classification": "collision",
                "source": "payload.md",
                "destination": "payload.md",
                "scope": "repo",
            }
        ],
    }


class GuidedInputTests(unittest.TestCase):
    def test_prompt_target_uses_valid_entered_directory(self) -> None:
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            output = io.StringIO()
            result = guided.prompt_target(
                source_root=Path(source),
                input_stream=io.StringIO(target + "\n"),
                output_stream=output,
            )
            self.assertEqual(result, Path(target).resolve())
            self.assertIn("Target repository", output.getvalue())
            self.assertIn("Tab completes paths", output.getvalue())

    def test_path_completion_returns_directories_with_trailing_separator(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "target repo"
            directory.mkdir()
            matches = guided.path_completion_matches(str(Path(parent) / "target"))
            self.assertIn(str(directory) + "/", matches)

    def test_mode_menu_defaults_to_personal_and_supports_arrows(self) -> None:
        mode_output = io.StringIO()
        default_keys = iter(["enter"])
        mode = guided.prompt_mode(
            ["team", "personal", "enterprise"],
            key_reader=lambda: next(default_keys),
            output_stream=mode_output,
        )
        self.assertEqual(mode, "personal")
        self.assertIn(">   Personal", mode_output.getvalue())

        arrow_keys = iter(["down", "enter"])
        mode = guided.prompt_mode(
            ["personal", "team", "enterprise"],
            key_reader=lambda: next(arrow_keys),
            output_stream=io.StringIO(),
        )
        self.assertEqual(mode, "team")

    def test_adapter_menu_supports_multi_select(self) -> None:
        adapter_output = io.StringIO()
        keys = iter(["down", "space", "down", "space", "enter"])
        adapters = guided.prompt_adapters(
            ["copilot", "codex", "claude"],
            key_reader=lambda: next(keys),
            output_stream=adapter_output,
        )
        self.assertEqual(adapters, ["copilot", "codex", "claude"])
        self.assertIn("Space toggles", adapter_output.getvalue())

    def test_footprint_menu_uses_mode_default(self) -> None:
        output = io.StringIO()
        footprint = guided.prompt_footprint(
            ["local", "profile", "adapters", "full"],
            default="adapters",
            key_reader=lambda: "enter",
            output_stream=output,
        )
        self.assertEqual(footprint, "adapters")
        self.assertIn(">   Adapters", output.getvalue())

    def test_footprint_menu_explains_choices_and_recommends_full(self) -> None:
        output = io.StringIO()
        footprint = guided.prompt_footprint(
            ["local", "profile", "adapters", "full"],
            default="full",
            mode="personal",
            key_reader=lambda: "enter",
            output_stream=output,
        )
        rendered = output.getvalue()
        self.assertEqual(footprint, "full")
        # Footprint is presented as a separate dimension from mode.
        self.assertIn("separate from mode", rendered)
        self.assertIn("Personal mode allows any footprint.", rendered)
        # Full is highlighted, recommended, and listed before the smaller footprints.
        self.assertIn(">   Full (recommended for first install)", rendered)
        self.assertLess(rendered.index("Full (recommended"), rendered.index("Local"))
        # Each footprint explains when it is the reasonable choice.
        self.assertIn("Add or update Codex/Copilot/Claude support only", rendered)
        self.assertIn("Add repo-awareness only", rendered)
        self.assertIn("No repository changes", rendered)

    def test_collision_n_and_enter_keep_existing(self) -> None:
        output = io.StringIO()
        decisions = guided.resolve_collisions(
            [
                {"destination": "one.md"},
                {"destination": "two.md"},
            ],
            input_stream=io.StringIO("n\n\n"),
            output_stream=output,
        )
        self.assertEqual(decisions, {"one.md": "keep", "two.md": "keep"})
        self.assertIn("[y] overwrite", output.getvalue())
        self.assertIn("[n] keep existing", output.getvalue())

    def test_collision_a_overwrites_current_and_all_remaining(self) -> None:
        decisions = guided.resolve_collisions(
            [
                {"destination": "one.md"},
                {"destination": "two.md"},
                {"destination": "three.md"},
            ],
            input_stream=io.StringIO("n\na\n"),
            output_stream=io.StringIO(),
        )
        self.assertEqual(
            decisions,
            {
                "one.md": "keep",
                "two.md": "overwrite",
                "three.md": "overwrite",
            },
        )

    def test_collision_y_overwrites_only_current_file(self) -> None:
        decisions = guided.resolve_collisions(
            [
                {"destination": "one.md"},
                {"destination": "two.md"},
            ],
            input_stream=io.StringIO("y\nn\n"),
            output_stream=io.StringIO(),
        )
        self.assertEqual(
            decisions,
            {"one.md": "overwrite", "two.md": "keep"},
        )

    def test_collision_q_quits(self) -> None:
        with self.assertRaises(KeyboardInterrupt):
            guided.resolve_collisions(
                [{"destination": "existing.md"}],
                input_stream=io.StringIO("q\n"),
                output_stream=io.StringIO(),
            )

    def test_final_apply_confirmation_defaults_to_no(self) -> None:
        output = io.StringIO()
        self.assertFalse(
            guided.confirm_apply(
                input_stream=io.StringIO("\n"),
                output_stream=output,
            )
        )
        self.assertIn("Apply this plan now? [y/N]", output.getvalue())

    def test_final_apply_confirmation_accepts_y(self) -> None:
        self.assertTrue(
            guided.confirm_apply(
                input_stream=io.StringIO("y\n"),
                output_stream=io.StringIO(),
            )
        )


class ApplyDecisionTests(unittest.TestCase):
    def _roots(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        source = base / "source"
        target = base / "target"
        source.mkdir()
        target.mkdir()
        (source / "payload.md").write_text("new\n", encoding="utf-8")
        (target / "payload.md").write_text("old\n", encoding="utf-8")
        return temporary, source, target

    def test_keep_leaves_collision_unchanged(self) -> None:
        temporary, source, target = self._roots()
        with temporary:
            result = apply.apply_plan(
                plan=_collision_plan(),
                source_root=source,
                target_root=target,
                manifest=_UnusedManifest(),
                force=False,
                collision_decisions={"payload.md": "keep"},
            )
            self.assertEqual((target / "payload.md").read_text(), "old\n")
            self.assertEqual(result["keptCount"], 1)
            self.assertEqual(result["writtenCount"], 0)

    def test_overwrite_replaces_collision_and_cleans_backup(self) -> None:
        temporary, source, target = self._roots()
        with temporary:
            result = apply.apply_plan(
                plan=_collision_plan(),
                source_root=source,
                target_root=target,
                manifest=_UnusedManifest(),
                force=False,
                collision_decisions={"payload.md": "overwrite"},
            )
            self.assertEqual((target / "payload.md").read_text(), "new\n")
            self.assertFalse((target / "payload.md.aim-backup").exists())
            self.assertEqual(result["writtenCount"], 1)

    def test_missing_collision_decision_is_refused(self) -> None:
        temporary, source, target = self._roots()
        with temporary, self.assertRaises(apply.ApplyRefused):
            apply.apply_plan(
                plan=_collision_plan(),
                source_root=source,
                target_root=target,
                manifest=_UnusedManifest(),
                force=False,
            )

    def test_force_preserves_non_interactive_overwrite_behavior(self) -> None:
        temporary, source, target = self._roots()
        with temporary:
            result = apply.apply_plan(
                plan=_collision_plan(),
                source_root=source,
                target_root=target,
                manifest=_UnusedManifest(),
                force=True,
            )
            self.assertEqual((target / "payload.md").read_text(), "new\n")
            self.assertEqual(result["writtenCount"], 1)


class RenderTests(unittest.TestCase):
    def _plan(self) -> dict:
        return {
            "operation": "dry-run",
            "target": "/tmp/repo",
            "source": "/tmp/aim",
            "manifestVersion": "0.2",
            "mode": "team",
            "footprint": "adapters",
            "footprintDescription": "Selected adapter packages.",
            "defaultFootprint": "adapters",
            "adapters": ["copilot"],
            "actions": [
                {
                    "classification": "create",
                    "destination": "one.md",
                    "source": "one.md",
                    "reason": "test",
                    "optional": False,
                }
            ],
            "summary": {
                "total": 1,
                "byClassification": {
                    "create": 1,
                    "modify": 0,
                    "untouched": 0,
                    "collision": 0,
                },
            },
            "validator": {"resultClass": "healthy", "exitCode": 0},
            "bootstrap": {
                "status": "needs_calibration",
                "calibrationCommand": "/aim calibrate-repo",
            },
            "rootFileExclusions": [],
            "scopeSummary": {
                "repoActionCount": 1,
                "localActionCount": 0,
                "staysLocal": [],
                "skippedAdapters": [],
                "explicitApproval": [],
            },
            "blockers": [],
        }

    def test_compact_is_default_and_verbose_retains_file_detail(self) -> None:
        plan = self._plan()
        compact = render.render_text(plan)
        verbose = render.render_text(plan, verbose=True)
        self.assertIn("1 actions", compact)
        self.assertNotIn("reason : test", compact)
        self.assertIn("reason : test", verbose)

    def test_guided_preview_points_to_same_session_apply(self) -> None:
        rendered = render.render_text(self._plan(), guided_session=True)
        self.assertIn("Continue below to reviewed apply", rendered)
        self.assertNotIn("Add --apply when ready", rendered)

    def test_json_is_machine_readable_without_color(self) -> None:
        rendered = render.render_json(self._plan())
        self.assertNotIn("\033[", rendered)
        self.assertIn('"operation": "dry-run"', rendered)


class ModeFootprintContractTests(unittest.TestCase):
    def _plan(
        self,
        *,
        mode: str,
        footprint: str | None = None,
        adapters: list[str] | None = None,
    ) -> dict:
        manifest = load_manifest(REPO_ROOT)
        mode_profile = manifest.mode_profile(mode)
        selected = footprint or str(mode_profile["defaultFootprint"])
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as home:
            return planner.compute_plan(
                source_root=REPO_ROOT,
                target_root=Path(target),
                mode=mode,
                footprint=selected,
                footprint_explicit=footprint is not None,
                adapters=adapters or ["copilot", "claude", "codex"],
                manifest=manifest,
                validator_result={"resultClass": "healthy", "exitCode": 0},
                home_root=Path(home),
            )

    def test_personal_default_is_permissive_adapter_setup(self) -> None:
        plan = self._plan(mode="personal")
        destinations = set(plan["scopeSummary"]["repoDestinations"])
        self.assertEqual(plan["footprint"], "adapters")
        self.assertFalse(plan["footprintProfile"]["sharedProfile"])
        self.assertIn(".github/agents/aim.agent.md", destinations)
        self.assertIn(".claude/commands/start-aim.md", destinations)
        self.assertNotIn("aim.profile.yaml", destinations)
        self.assertIn(
            "docs/workflow/agile-iteration-method.md", destinations
        )
        self.assertNotIn("docs/workflow/operating-modes.md", destinations)

    def test_team_default_installs_profile_adapters_and_closure_subset(self) -> None:
        plan = self._plan(mode="team")
        destinations = set(plan["scopeSummary"]["repoDestinations"])
        self.assertEqual(plan["footprint"], "adapters")
        self.assertIn("aim.profile.yaml", destinations)
        self.assertIn(".gitignore", destinations)
        self.assertIn(".github/agents/aim.agent.md", destinations)
        self.assertIn(".claude/commands/start-aim.md", destinations)
        self.assertIn(
            "docs/workflow/adapter-command-contract.md", destinations
        )
        self.assertNotIn("docs/workflow/operating-modes.md", destinations)
        self.assertGreater(plan["scopeSummary"]["localActionCount"], 0)
        self.assertIn(
            "docs/workflow/adapter-command-contract.md",
            plan["adapterClosure"]["requiredRepoDocs"],
        )
        self.assertIn(
            "references/agile-iteration-method.md",
            plan["adapterClosure"]["packageLocalDocs"]["codex"],
        )

    def test_enterprise_default_is_non_invasive(self) -> None:
        plan = self._plan(mode="enterprise")
        self.assertEqual(plan["footprint"], "local")
        self.assertEqual(plan["scopeSummary"]["repoActionCount"], 0)
        self.assertFalse(plan["footprintProfile"]["sharedProfile"])
        self.assertTrue(plan["modeProfile"]["enterpriseSafe"])

    def test_enterprise_profile_uses_exact_canonical_ignore_baseline(self) -> None:
        plan = self._plan(
            mode="enterprise", footprint="profile", adapters=["copilot"]
        )
        self.assertEqual(
            plan["gitignoreFragments"],
            [
                "/.aim",
                "/.aim-local",
                "/aim.local.*",
                "/*.aim.local.md",
                "/*.aim.process.md",
            ],
        )
        self.assertEqual(
            set(plan["scopeSummary"]["repoDestinations"]),
            {"aim.profile.yaml", ".gitignore"},
        )
        self.assertTrue(plan["scopeSummary"]["explicitApproval"])

    def test_adapter_footprint_installs_only_required_contract_subset(self) -> None:
        for footprint in ("local", "profile"):
            plan = self._plan(mode="team", footprint=footprint)
            self.assertFalse(
                any(
                    path.startswith("docs/workflow/")
                    for path in plan["scopeSummary"]["repoDestinations"]
                )
            )
            self.assertFalse(
                any(
                    path.startswith("schemas/")
                    for path in plan["scopeSummary"]["repoDestinations"]
                )
            )
        adapters = self._plan(mode="team", footprint="adapters")
        adapter_docs = {
            path
            for path in adapters["scopeSummary"]["repoDestinations"]
            if path.startswith("docs/workflow/")
        }
        self.assertIn("docs/workflow/agile-iteration-method.md", adapter_docs)
        self.assertIn("docs/workflow/adapter-command-contract.md", adapter_docs)
        self.assertNotIn("docs/workflow/operating-modes.md", adapter_docs)
        self.assertLess(
            len(adapter_docs),
            len(list((REPO_ROOT / "docs/workflow").glob("*.md"))),
        )
        full = self._plan(mode="team", footprint="full")
        self.assertIn(
            "schemas/aim-repo-profile.schema.json",
            full["scopeSummary"]["repoDestinations"],
        )
        self.assertIn(
            "schemas/aim-personal-hints.schema.json",
            full["scopeSummary"]["repoDestinations"],
        )
        self.assertTrue(
            any(
                path.startswith("docs/workflow/")
                for path in full["scopeSummary"]["repoDestinations"]
            )
        )
        self.assertIn(
            "docs/workflow/operating-modes.md",
            full["scopeSummary"]["repoDestinations"],
        )
        self.assertIn(
            "docs/aim/LICENSE", full["scopeSummary"]["repoDestinations"]
        )
        self.assertIn(
            "docs/aim/LICENSE-DOCS", full["scopeSummary"]["repoDestinations"]
        )

    def test_generic_root_files_remain_excluded_for_every_mode(self) -> None:
        for mode in ("personal", "team", "enterprise"):
            plan = self._plan(mode=mode)
            excluded = {entry["path"] for entry in plan["rootFileExclusions"]}
            self.assertEqual(
                {"AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md"},
                excluded,
            )
            destinations = {Path(a["destination"]).name for a in plan["actions"]}
            self.assertTrue(excluded.isdisjoint(destinations))

    def test_local_guidance_does_not_claim_skipped_adapter_is_installed(self) -> None:
        plan = self._plan(
            mode="personal", footprint="local", adapters=["copilot"]
        )
        steps = plan["guidance"]["steps"]
        self.assertTrue(any("was not installed" in step for step in steps))
        self.assertFalse(any("open chat and run" in step for step in steps))
        rendered = render.render_text(plan)
        self.assertIn("keeping or committing it is the solo user's choice", rendered)
        self.assertIn("No files are selected", rendered)

    def test_existing_install_guidance_points_to_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as home:
            copied = Path(target) / ".github" / "agents"
            copied.mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / ".github" / "agents" / "aim.agent.md",
                copied / "aim.agent.md",
            )
            plan = planner.compute_plan(
                source_root=REPO_ROOT,
                target_root=Path(target),
                mode="team",
                footprint="adapters",
                footprint_explicit=True,
                adapters=["copilot"],
                manifest=load_manifest(REPO_ROOT),
                validator_result={"resultClass": "healthy", "exitCode": 0},
                home_root=Path(home),
            )

        self.assertEqual(plan["installState"], "partial")
        guidance = "\n".join(plan["guidance"]["steps"])
        self.assertIn("/aim upgrade", guidance)
        self.assertIn(".aim runtime state", guidance)

    def test_personal_allows_every_footprint(self) -> None:
        expected_repo_writes = {
            "local": False,
            "profile": True,
            "adapters": True,
            "full": True,
        }
        for footprint, has_repo_writes in expected_repo_writes.items():
            plan = self._plan(mode="personal", footprint=footprint)
            self.assertEqual(
                plan["scopeSummary"]["repoActionCount"] > 0,
                has_repo_writes,
            )
        profile = self._plan(mode="personal", footprint="profile")
        self.assertIn(
            "aim.profile.yaml", profile["scopeSummary"]["repoDestinations"]
        )
        full = self._plan(mode="personal", footprint="full")
        self.assertTrue(
            any(
                path.startswith("docs/workflow/")
                for path in full["scopeSummary"]["repoDestinations"]
            )
        )

    def test_validator_blocks_mode_default_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "repo"
            shutil.copytree(
                REPO_ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            manifest_path = copied / "install/aim-install-manifest.yaml"
            content = manifest_path.read_text(encoding="utf-8")
            content = content.replace(
                "team:\n      defaultFootprint: adapters",
                "team:\n      defaultFootprint: local",
                1,
            )
            manifest_path.write_text(content, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(copied / "scripts/validate_aim_runtime.py"),
                    str(copied),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(completed.returncode, 3)
            self.assertIn("Result: contradictory", completed.stdout)
            self.assertIn("Release readiness: FAIL", completed.stdout)
            self.assertIn("mode footprint defaults drifted", completed.stdout)


class CliTests(unittest.TestCase):
    def test_non_interactive_missing_target_fails_without_prompting(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "aim_install.py"),
                "--format",
                "json",
                "--non-interactive",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--target is required", completed.stderr)
        self.assertNotIn("Target repository:", completed.stdout)

    def test_guided_preview_can_apply_without_apply_flag(self) -> None:
        with tempfile.TemporaryDirectory() as target, mock.patch.object(
            guided, "is_interactive", return_value=True
        ), mock.patch.object(
            guided, "prompt_mode", return_value="personal"
        ), mock.patch.object(
            guided, "prompt_footprint", return_value="full"
        ), mock.patch.object(
            guided, "prompt_adapters", return_value=["claude"]
        ), mock.patch.object(
            guided, "confirm_apply", return_value=True
        ):
            result = aim_install.main(
                ["--target", target, "--color", "never"]
            )
            self.assertEqual(result, 0)
            self.assertTrue(
                (Path(target) / "docs/workflow/agile-iteration-method.md").exists()
            )

    def test_guided_non_default_footprint_is_recorded_as_explicit(self) -> None:
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            guided, "is_interactive", return_value=True
        ), mock.patch.object(
            guided, "prompt_mode", return_value="enterprise"
        ), mock.patch.object(
            guided, "prompt_footprint", return_value="profile"
        ), mock.patch.object(
            guided, "prompt_adapters", return_value=["copilot"]
        ), mock.patch.object(
            guided, "confirm_apply", return_value=False
        ), mock.patch(
            "sys.stdout", output
        ):
            target = Path(temporary) / "target"
            target.mkdir()
            plan_path = Path(temporary) / "plan.json"
            result = aim_install.main(
                ["--target", str(target), "--plan-out", str(plan_path)]
            )
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertTrue(plan["footprintExplicit"])
        self.assertTrue(plan["scopeSummary"]["explicitApproval"])

    def test_guided_preview_decline_is_successful_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as target, mock.patch.object(
            guided, "is_interactive", return_value=True
        ), mock.patch.object(
            guided, "prompt_mode", return_value="personal"
        ), mock.patch.object(
            guided, "prompt_footprint", return_value="local"
        ), mock.patch.object(
            guided, "prompt_adapters", return_value=["claude"]
        ), mock.patch.object(
            guided, "confirm_apply", return_value=False
        ):
            result = aim_install.main(
                ["--target", target, "--color", "never"]
            )
            self.assertEqual(result, 0)
            self.assertEqual(list(Path(target).iterdir()), [])

    def test_explicit_dry_run_does_not_offer_same_session_apply(self) -> None:
        with tempfile.TemporaryDirectory() as target, mock.patch.object(
            guided, "is_interactive", return_value=True
        ), mock.patch.object(
            guided, "prompt_mode", return_value="personal"
        ), mock.patch.object(
            guided, "prompt_footprint", return_value="local"
        ), mock.patch.object(
            guided, "prompt_adapters", return_value=["claude"]
        ), mock.patch.object(
            guided, "confirm_apply"
        ) as confirmation:
            result = aim_install.main(
                ["--target", target, "--dry-run", "--color", "never"]
            )
            self.assertEqual(result, 0)
            confirmation.assert_not_called()
            self.assertEqual(list(Path(target).iterdir()), [])

    def test_apply_and_dry_run_are_mutually_exclusive(self) -> None:
        result = aim_install.main(["--apply", "--dry-run", "--non-interactive"])
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
