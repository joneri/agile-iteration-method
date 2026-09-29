"""CLI profile readiness distinguishes reported status from validated coverage."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aim_installer.seed import shared_profile_seed
from validate_aim_runtime import collect_repo_profile_readiness, build_profile_source_summary


class ValidatorReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.path = self.repo / "aim.profile.yaml"

    def write_profile(self, scope="", *, knowledge=True):
        source = shared_profile_seed().replace(
            "    status: needs_calibration", "    status: ready" + scope
        )
        if knowledge:
            source = source.replace(
                "    localities: []",
                "    localities:\n      - id: frontend\n        paths:\n          - app/",
            )
        self.path.write_text(source)
        return source

    def test_legacy_status_is_preserved_with_unspecified_coverage(self):
        self.write_profile()
        readiness = collect_repo_profile_readiness(self.repo)
        self.assertEqual(readiness["status"], "ready")
        self.assertTrue(readiness["profile_contract_valid"])
        self.assertFalse(readiness["repository_ready"])
        self.assertIn("unspecified", readiness["summary"])
        self.assertIn("clarify calibration scope", readiness["calibration_next_action"])
        summary = build_profile_source_summary(self.repo, readiness)
        self.assertIn("coverage: unspecified", summary["source"])

    def test_locality_scope_preserves_status_and_names_coverage(self):
        self.write_profile("\n    scope:\n      kind: localities\n      localityIds:\n        - frontend")
        readiness = collect_repo_profile_readiness(self.repo)
        self.assertEqual(readiness["status"], "ready")
        self.assertFalse(readiness["repository_ready"])
        self.assertIn("localities: frontend", readiness["coverage_summary"])
        self.assertIn("continue within localities: frontend", readiness["calibration_next_action"])

    def test_bootstrap_ready_cannot_claim_repository_coverage(self):
        self.write_profile("\n    scope:\n      kind: repository", knowledge=False)
        readiness = collect_repo_profile_readiness(self.repo)
        self.assertEqual(readiness["status"], "ready")
        self.assertFalse(readiness["repository_ready"])
        self.assertFalse(readiness["has_knowledge"])
        self.assertIn("no repository knowledge", readiness["coverage_summary"])
        self.assertIn("/aim calibrate-repo", readiness["calibration_next_action"])

    def test_explicit_repository_scope_is_a_declaration_not_semantic_proof(self):
        self.write_profile("\n    scope:\n      kind: repository")
        readiness = collect_repo_profile_readiness(self.repo)
        self.assertTrue(readiness["repository_ready"])
        self.assertFalse(readiness["semantic_truth_verified"])
        self.assertEqual(readiness["coverage_summary"], "repository (declared scope)")

    def test_invalid_product_contract_cannot_produce_ready_coverage(self):
        source = self.write_profile("\n    scope:\n      kind: repository")
        self.path.write_text(source.replace("- app/", "- .aim/state.json"))
        readiness = collect_repo_profile_readiness(self.repo)
        self.assertEqual(readiness["status"], "needs_calibration")
        self.assertFalse(readiness["profile_contract_valid"])
        self.assertFalse(readiness["repository_ready"])
        self.assertTrue(any("durable repo-awareness" in issue for issue in readiness["coverage_diagnostics"]))

    def test_cli_prints_scope_and_does_not_claim_no_calibration_action(self):
        copied = self.repo / "source"
        shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        original = (copied / "aim.profile.yaml").read_text()
        # Use an existing locality from the source profile, through the actual parser.
        from aim_quality.profiles import read_repo_profile
        document, issues = read_repo_profile(copied)
        self.assertEqual(issues, [])
        locality_id = document["aimRepoProfile"]["repoKnowledge"]["localities"][0]["id"]
        cases = (
            (original, "unspecified", "clarify calibration scope"),
            (original.replace("    status: ready", "    status: ready\n    scope:\n      kind: localities\n      localityIds:\n        - " + locality_id, 1),
             "localities: " + locality_id, "continue within localities: " + locality_id),
            (shared_profile_seed().replace("status: needs_calibration", "status: ready"),
             "not established (profile contains no repository knowledge)", "run /aim calibrate-repo"),
        )
        for source, coverage, action in cases:
            with self.subTest(coverage=coverage):
                (copied / "aim.profile.yaml").write_text(source)
                result = subprocess.run(
                    [sys.executable, str(copied / "scripts/validate_aim_runtime.py"), str(copied), "--release"],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn("- status: ready", result.stdout)
                self.assertIn("- calibration coverage: " + coverage, result.stdout)
                self.assertIn("- repository-ready declaration: not established", result.stdout)
                self.assertIn("- Repo-awareness: reported ready; coverage: " + coverage, result.stdout)
                self.assertIn("- Next calibration action: " + action, result.stdout)
                self.assertNotIn("- Next calibration action: none\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
