"""Scoped readiness uses the same profile consumer as the shipped validator."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aim_installer.seed import shared_profile_seed
from aim_quality.profiles import check_profiles, read_repo_profile
from aim_ui import build_board


class CalibrationScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.path = self.repo / "aim.profile.yaml"

    def write_profile(self, scope="", *, knowledge=True, status="ready"):
        source = shared_profile_seed().replace(
            "    status: needs_calibration", f"    status: {status}" + scope
        )
        if knowledge:
            source = source.replace(
                "    localities: []",
                "    localities:\n      - id: frontend\n        paths:\n          - app/",
            )
        self.path.write_text(source)
        return source

    def test_explicit_repository_coverage_projects_ready_without_writes(self):
        self.write_profile("\n    scope:\n      kind: repository")
        before = self.path.read_bytes()
        self.assertTrue(check_profiles(self.repo, "repo")["valid"])
        board = build_board(self.repo)
        self.assertTrue(board["source"]["calibrated"])
        self.assertFalse(board["source"]["calibration"]["semanticTruthVerified"])
        self.assertIn("for repository", board["onboarding"]["message"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse((self.repo / ".aim").exists())

    def test_scoped_ready_names_localities_and_allows_next_discussion(self):
        self.write_profile("\n    scope:\n      kind: localities\n      localityIds:\n        - frontend")
        document, issues = read_repo_profile(self.repo)
        self.assertEqual(issues, [])
        self.assertEqual(document["aimRepoProfile"]["calibration"]["scope"]["localityIds"], ["frontend"])
        board = build_board(self.repo)
        self.assertFalse(board["source"]["calibrated"])
        self.assertTrue(board["source"]["calibration"]["configured"])
        self.assertIn("localities: frontend", board["onboarding"]["message"])
        self.assertIn("localities: frontend", board["recovery"]["message"])
        self.assertTrue(board["onboarding"]["nextAction"].startswith("/aim discuss"))
        self.assertTrue(board["recovery"]["recommendedAction"]["intent"].startswith("/aim discuss"))

    def test_legacy_ready_remains_parseable_but_does_not_imply_repository_scope(self):
        self.write_profile()
        self.assertTrue(check_profiles(self.repo, "repo")["valid"])
        board = build_board(self.repo)
        self.assertFalse(board["source"]["calibrated"])
        self.assertEqual(board["source"]["calibration"]["scope"], {"kind": "unspecified"})
        self.assertIn("unspecified scope", board["onboarding"]["message"])
        self.assertTrue(board["onboarding"]["nextAction"].startswith("/aim discuss"))

    def test_ready_bootstrap_does_not_establish_coverage_even_with_explicit_scope(self):
        for scope in ("", "\n    scope:\n      kind: repository"):
            with self.subTest(scope=scope):
                self.write_profile(scope, knowledge=False)
                self.assertTrue(check_profiles(self.repo, "repo")["valid"])
                board = build_board(self.repo)
                self.assertFalse(board["source"]["calibrated"])
                self.assertFalse(board["source"]["calibration"]["hasKnowledge"])
                self.assertEqual(board["onboarding"]["nextAction"], "/aim calibrate-repo")

    def test_partial_scope_is_not_repository_ready_or_forced_to_restart(self):
        self.write_profile("\n    scope:\n      kind: repository", status="partially_ready")
        board = build_board(self.repo)
        self.assertFalse(board["source"]["calibrated"])
        self.assertIn("partially ready", board["onboarding"]["message"])
        self.assertTrue(board["onboarding"]["nextAction"].startswith("/aim discuss"))

    def test_invalid_scope_is_rejected_by_consumer_and_cannot_claim_ui_readiness(self):
        cases = (
            "    scope: repository",
            "    scope:\n      kind: unknown",
            "    scope:\n      kind: localities",
            "    scope:\n      kind: localities\n      localityIds: []",
            "    scope:\n      kind: localities\n      localityIds:\n        - missing",
            "    scope:\n      kind: localities\n      localityIds:\n        - frontend\n        - frontend",
            "    scope:\n      kind: localities\n      localityIds:\n        - false",
            "    scope:\n      kind: repository\n      localityIds:\n        - frontend",
            "    scope:\n      kind: repository\n      invented: yes",
        )
        for scope in cases:
            with self.subTest(scope=scope):
                self.write_profile("\n" + scope)
                result = check_profiles(self.repo, "repo")
                self.assertFalse(result["valid"], result)
                self.assertTrue(any("calibration.scope" in item["error"] for item in result["diagnostics"]))
                board = build_board(self.repo)
                self.assertFalse(board["source"]["calibrated"])
                self.assertTrue(board["source"]["calibration"]["diagnostics"])

    def test_product_rules_apply_to_durable_runtime_references(self):
        source = self.write_profile("\n    scope:\n      kind: repository")
        for invalid in (
            source.replace("profileLocation: aim.profile.yaml", "profileLocation: .aim/profile.yaml"),
            source.replace("- app/", "- .aim/state.json"),
        ):
            with self.subTest(invalid=invalid):
                self.path.write_text(invalid)
                result = check_profiles(self.repo, "repo")
                self.assertFalse(result["valid"])
                self.assertTrue(any("repo-awareness" in item["error"] for item in result["diagnostics"]))
                self.assertFalse(build_board(self.repo)["source"]["calibrated"])

    def test_incomplete_regex_ready_document_is_not_a_valid_profile(self):
        self.path.write_text("aimRepoProfile:\n  calibration:\n    status: ready\n")
        self.assertFalse(check_profiles(self.repo, "repo")["valid"])
        self.assertFalse(build_board(self.repo)["source"]["calibrated"])

    def test_optional_knowledge_metadata_is_typed_without_being_required(self):
        source = self.write_profile()
        self.path.write_text(source.replace(
            "      - id: frontend",
            "      - id: frontend\n        appliesTo:\n          - frontend\n        expectedUse: Review app changes\n        recheckWhen:\n          - app changes",
        ))
        self.assertTrue(check_profiles(self.repo, "repo")["valid"])
        self.path.write_text(self.path.read_text().replace("expectedUse: Review app changes", "expectedUse: false"))
        self.assertFalse(check_profiles(self.repo, "repo")["valid"])


if __name__ == "__main__":
    unittest.main()
