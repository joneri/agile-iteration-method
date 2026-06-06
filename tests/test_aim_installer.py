"""Focused tests for the AIM guided installer UX and deterministic apply engine."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from aim_installer import apply, guided, render  # noqa: E402
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

    def test_guided_preview_decline_is_successful_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as target, mock.patch.object(
            guided, "is_interactive", return_value=True
        ), mock.patch.object(
            guided, "prompt_mode", return_value="personal"
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
