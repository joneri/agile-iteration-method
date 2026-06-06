"""Focused tests for the AIM guided installer UX and deterministic apply engine."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from aim_installer import apply, guided, render  # noqa: E402


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

    def test_collision_prompt_defaults_to_keep(self) -> None:
        output = io.StringIO()
        decisions = guided.resolve_collisions(
            [{"destination": "existing.md"}],
            input_stream=io.StringIO("\n"),
            output_stream=output,
        )
        self.assertEqual(decisions, {"existing.md": "keep"})
        self.assertIn("[k]eep existing", output.getvalue())


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


if __name__ == "__main__":
    unittest.main()
