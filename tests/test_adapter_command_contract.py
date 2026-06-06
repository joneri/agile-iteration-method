"""Contract tests for AIM adapter command parity."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AdapterCommandContractTests(unittest.TestCase):
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
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_complete_adapter_command_contract_is_healthy(self) -> None:
        completed = self._validate(REPO_ROOT)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("canonical command intents: 13", completed.stdout)

    def test_missing_claude_command_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            (copied / ".claude/commands/status-aim.md").unlink()
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 2)
        self.assertIn(
            "Claude native command surface is missing for /aim status",
            completed.stdout,
        )

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

        self.assertEqual(completed.returncode, 2)
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

        self.assertEqual(completed.returncode, 2)
        self.assertIn(
            "Copilot advertised command behavior is empty or non-actionable",
            completed.stdout,
        )

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
            ".claude/commands/start-aim.md",
            ".claude/commands/continue-aim.md",
            ".claude/commands/status-aim.md",
            ".claude/commands/validate-aim.md",
            ".claude/commands/help-aim.md",
            ".claude/commands/config-aim.md",
            ".claude/commands/calibrate-repo.md",
            ".claude/commands/remember-repo.md",
            ".claude/commands/forget-repo.md",
            ".claude/commands/upgrade-aim.md",
            ".claude/commands/mode-aim.md",
            ".claude/commands/cost-aim.md",
            ".claude/commands/replan-aim.md",
        }
        self.assertTrue(expected.issubset(destinations))


if __name__ == "__main__":
    unittest.main()
