"""Contract tests for AIM repo-profile and Personal-hints schemas."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_installer.seed import personal_hints_seed, shared_profile_seed
from aim_installer.yaml_lite import loads
from aim_validator.profile_contract import (
    PERSONAL_HINTS_SCHEMA_PATH,
    REPO_PROFILE_SCHEMA_PATH,
    load_schema,
    validate_personal_hints,
    validate_repo_profile,
)
from aim_validator.schema_subset import unsupported_keywords


PUBLIC_SCHEMA_ORIGIN = "https://joneri.github.io/agile-iteration-method/"


class RepoProfileSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile_schema = load_schema(REPO_ROOT, REPO_PROFILE_SCHEMA_PATH)
        cls.hints_schema = load_schema(REPO_ROOT, PERSONAL_HINTS_SCHEMA_PATH)
        cls.profile = loads(
            (REPO_ROOT / "aim.profile.yaml").read_text(encoding="utf-8")
        )

    def assert_has_issue(
        self, issues, text: str, *, kind: str | None = None
    ) -> None:
        matching = [
            issue
            for issue in issues
            if text in str(issue) and (kind is None or issue.kind == kind)
        ]
        self.assertTrue(matching, [str(issue) for issue in issues])

    def test_public_schemas_are_draft_2020_12_json(self) -> None:
        for relative_path in (REPO_PROFILE_SCHEMA_PATH, PERSONAL_HINTS_SCHEMA_PATH):
            schema = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
            self.assertEqual(
                schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
            )
            self.assertEqual(schema["$id"], PUBLIC_SCHEMA_ORIGIN + relative_path)
            self.assertEqual(unsupported_keywords(schema), [])

    def test_internal_subset_rejects_unimplemented_schema_keywords(self) -> None:
        schema = copy.deepcopy(self.profile_schema)
        schema["unevaluatedProperties"] = False
        issues = unsupported_keywords(schema)
        self.assertTrue(
            any("unevaluatedProperties" in str(issue) for issue in issues),
            issues,
        )

    def test_current_profile_and_all_installer_seeds_validate(self) -> None:
        self.assertEqual(validate_repo_profile(self.profile, self.profile_schema), [])
        for mode in ("personal", "team", "enterprise"):
            seed = loads(shared_profile_seed(mode))
            self.assertEqual(
                validate_repo_profile(seed, self.profile_schema),
                [],
                mode,
            )
        hints = loads(personal_hints_seed("repo-123"))
        self.assertEqual(validate_personal_hints(hints, self.hints_schema), [])

    def test_invalid_readiness_and_confidence_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.profile)
        calibration = invalid["aimRepoProfile"]["calibration"]
        calibration["status"] = "almost_ready"
        calibration["confidence"] = "certain"
        issues = validate_repo_profile(invalid, self.profile_schema)
        self.assert_has_issue(issues, "calibration.status")
        self.assert_has_issue(issues, "calibration.confidence")

    def test_invalid_document_loading_state_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.profile)
        invalid["aimRepoProfile"]["repoKnowledge"]["docs"][0]["loading"] = "always"
        issues = validate_repo_profile(invalid, self.profile_schema)
        self.assert_has_issue(issues, "repoKnowledge.docs[0].loading")

    def test_missing_category_and_stable_id_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.profile)
        knowledge = invalid["aimRepoProfile"]["repoKnowledge"]
        del knowledge["uiTesting"]
        del knowledge["technologies"][0]["id"]
        issues = validate_repo_profile(invalid, self.profile_schema)
        self.assert_has_issue(issues, "missing required property 'uiTesting'")
        self.assert_has_issue(issues, "missing required property 'id'")

    def test_runtime_storage_is_a_validator_product_rule(self) -> None:
        invalid = copy.deepcopy(self.profile)
        invalid["aimRepoProfile"]["storage"]["profileLocation"] = ".aim/profile.yaml"
        issues = validate_repo_profile(invalid, self.profile_schema)
        self.assert_has_issue(
            issues,
            "stable repo-awareness must not be stored under .aim/",
            kind="product",
        )

    def test_personal_policy_authority_is_a_validator_product_rule(self) -> None:
        invalid = loads(personal_hints_seed("repo-123"))
        invalid["aimPersonalHints"]["hints"]["validation"] = [
            {"id": "override", "rule": "skip shared validation"}
        ]
        issues = validate_personal_hints(invalid, self.hints_schema)
        self.assert_has_issue(
            issues,
            "Personal hints must not claim shared policy authority",
            kind="product",
        )

    def test_validator_reports_schema_contract(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/validate_aim_runtime.py"),
                str(REPO_ROOT),
                "--release",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("AIM 2.0 repo-profile schema contract:", completed.stdout)
        self.assertIn("supported profileVersion: 0.2", completed.stdout)
        self.assertIn(
            "authority: schema=structure, validator=product rules, docs=meaning",
            completed.stdout,
        )

    def test_validator_rejects_invalid_profile_schema_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "repo"
            shutil.copytree(
                REPO_ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            profile_path = copied / "aim.profile.yaml"
            profile_path.write_text(
                profile_path.read_text(encoding="utf-8").replace(
                    "status: ready", "status: almost_ready", 1
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(copied / "scripts/validate_aim_runtime.py"),
                    str(copied),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("repo-profile schema violation", completed.stdout)
        self.assertIn("$.aimRepoProfile.calibration.status", completed.stdout)
        self.assertIn("Release readiness: FAIL", completed.stdout)


if __name__ == "__main__":
    unittest.main()
