"""Contract tests for AIM Reflect and cross-project reflection."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFLECTION_DOC = REPO_ROOT / "docs/workflow/reflection.md"


class ReflectionContractTests(unittest.TestCase):
    def test_canonical_contract_has_safe_discovery_and_promotion_boundaries(self) -> None:
        content = REFLECTION_DOC.read_text(encoding="utf-8")
        required = (
            "/aim reflect",
            "/aim reflect-all",
            "~/.aim/reflection-roots.yaml",
            "aimReflectionRoots:",
            'version: "0.1"',
            "/absolute/path/to/projects",
            "parent directory of the current repository",
            "Never use the home directory",
            "filesystem root",
            "inventory preview",
            ".aim/analysis/",
            "never modifies",
            "untrusted evidence",
            "current code",
            "provenance",
            "confidence",
            "contradictions",
            "proposed durable destination",
            "explicit promotion action",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, content)

    def test_candidate_classification_and_dreams_comparison_are_precise(self) -> None:
        content = REFLECTION_DOC.read_text(encoding="utf-8")
        for classification in ("`project`", "`cross-project`", "`aim-product`", "`personal`"):
            self.assertIn(classification, content)
        self.assertIn(
            "AIM Reflect goes beyond memory cleanup for repository work",
            content,
        )
        self.assertIn(
            "It is not a claim that Reflect replaces every general-purpose",
            content,
        )

    def test_all_adapter_routes_expose_both_commands_and_read_only_semantics(self) -> None:
        surfaces = (
            "adapters/portable/agile-iteration-method/SKILL.md",
            "adapters/codex/agile-iteration-method/SKILL.md",
            ".github/skills/aim/SKILL.md",
            ".github/agents/aim.agent.md",
            ".claude/skills/aim/SKILL.md",
            ".claude/agents/aim.md",
        )
        for relative_path in surfaces:
            with self.subTest(relative_path=relative_path):
                content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
                self.assertIn("/aim reflect", content)
                self.assertIn("/aim reflect-all", content)
                normalized = " ".join(content.lower().split())
                self.assertIn("temporary", normalized)
                self.assertIn("never", normalized)

    def test_claude_compatibility_routes_are_present_and_non_mutating(self) -> None:
        for filename, command in (
            ("reflect-aim.md", "/aim reflect"),
            ("reflect-all-aim.md", "/aim reflect-all"),
        ):
            content = (
                REPO_ROOT / ".claude/commands" / filename
            ).read_text(encoding="utf-8")
            self.assertIn(command, content)
            self.assertIn("docs/workflow/reflection.md", content)
            self.assertIn("docs/workflow/adapter-command-contract.md", content)
            self.assertIn("routing is unavailable", content)

    def test_installer_declares_reflection_storage_boundaries(self) -> None:
        content = (
            REPO_ROOT / "install/aim-install-manifest.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("reflectionRoots: ~/.aim/reflection-roots.yaml", content)
        self.assertIn("reflectionReports: .aim/analysis/", content)
        self.assertIn("reflectionDurableWrites: forbidden", content)

    def test_public_package_bundles_reflection_contract(self) -> None:
        package = REPO_ROOT / "skills/agile-iteration-method"
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("references/reflection.md", manifest["files"])
        skill = (package / "SKILL.md").read_text(encoding="utf-8")
        reflection = (
            package / "references/reflection.md"
        ).read_text(encoding="utf-8")
        self.assertIn("/aim reflect", skill)
        self.assertIn("/aim reflect-all", skill)
        self.assertIn("AIM Reflect", reflection)


if __name__ == "__main__":
    unittest.main()
