"""Adversarial tests for AIM product-coherence validation."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ProductCoherenceValidatorTests(unittest.TestCase):
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

    def test_healthy_means_all_tiers_pass(self) -> None:
        completed = self._validate(REPO_ROOT)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("Result: healthy", completed.stdout)
        self.assertIn("Release readiness: PASS", completed.stdout)
        for tier in (
            "Structural",
            "Behavioral",
            "Product coherence",
            "Release readiness",
        ):
            self.assertIn(f"- {tier}: PASS", completed.stdout)
        for heading in (
            "Errors:",
            "Warnings:",
            "Contradictions:",
            "Recommendations:",
        ):
            self.assertIn(heading, completed.stdout)

    def test_documented_enterprise_contradiction_fails_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            mode_doc = copied / "docs/workflow/operating-modes.md"
            mode_doc.write_text(
                mode_doc.read_text(encoding="utf-8")
                + "\nEnterprise AIM defaults to broad repository mutation.\n",
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Result: contradictory", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "Enterprise is documented as broad or repo-writing by default",
            completed.stdout,
        )

    def test_standard_install_plan_drift_is_a_product_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            manifest = copied / "install/aim-install-manifest.yaml"
            content = manifest.read_text(encoding="utf-8")
            manifest.write_text(
                content.replace(
                    "standard:\n      defaultFootprint: adapters",
                    "standard:\n      defaultFootprint: local",
                    1,
                ),
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "standard install does not produce the documented native project-agent setup",
            completed.stdout,
        )

    def test_public_upgrade_claim_requires_codex_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            skill = copied / "adapters/codex/agile-iteration-method/SKILL.md"
            content = skill.read_text(encoding="utf-8")
            content = content.replace("- `/aim upgrade`\n", "", 1)
            content = content.replace("--dry-run", "--preview")
            skill.write_text(content, encoding="utf-8")
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn("public /aim upgrade claim ↔ Codex", completed.stdout)

    def test_noncritical_warning_is_conditional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            (copied / "AGENTS.md").write_text(
                "Repository-owned instructions.\n", encoding="utf-8"
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 1)
        self.assertIn("Result: recoverable", completed.stdout)
        self.assertIn("Release readiness: CONDITIONAL", completed.stdout)
        self.assertIn("Warnings:", completed.stdout)
        self.assertIn("Contradictions:\n- none", completed.stdout)

    def test_stale_unreleased_claim_fails_release_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            guide = copied / "docs/workflow/agile-iteration-method.md"
            guide.write_text(
                guide.read_text(encoding="utf-8")
                + "\nAIM 2.0 is not released as a final runtime yet.\n",
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn(
            "canonical workflow docs say the runtime is not released",
            completed.stdout,
        )

    def test_stale_public_skill_fails_release_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self._copy_repo(temporary)
            canonical = copied / "docs/workflow/adapter-command-contract.md"
            canonical.write_text(
                canonical.read_text(encoding="utf-8") + "\nUnpackaged drift.\n",
                encoding="utf-8",
            )
            completed = self._validate(copied)

        self.assertEqual(completed.returncode, 3)
        self.assertIn("Release readiness: FAIL", completed.stdout)
        self.assertIn("generated public skill validation failed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
