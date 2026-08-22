"""Portfolio Auto run contract tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_portfolio_run import (  # noqa: E402
    PortfolioRunError,
    activate_next,
    checkpoint,
    complete_active,
    create_run,
    load_run,
    pause_run,
    project_portfolio_run,
    resume_run,
    skip_active,
    stop_run,
)
from aim_validator.schema_subset import unsupported_keywords, validate  # noqa: E402


class PortfolioRunTests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        aim = root / ".aim"
        aim.mkdir()
        (aim / "portfolio-backlog.json").write_text(
            json.dumps(
                {
                    "backlogVersion": "1.0",
                    "updatedAt": "2026-08-22T10:00:00Z",
                    "items": [
                        {
                            "id": "INC-SECOND",
                            "epicId": "EPIC-SECOND",
                            "epicTitle": "Second Epic",
                            "title": "Finish second",
                            "priority": 2,
                            "createdAt": "2026-08-22T10:01:00Z",
                        },
                        {
                            "id": "INC-FIRST",
                            "epicId": "EPIC-FIRST",
                            "epicTitle": "First Epic",
                            "title": "Finish first",
                            "priority": 1,
                            "createdAt": "2026-08-22T10:00:00Z",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return root

    def test_schema_is_supported(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/aim-portfolio-run.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(unsupported_keywords(schema), [])

    def test_two_candidates_complete_in_snapshot_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(
                repo,
                "MANDATE-TEST-001",
                "2026-08-22T10:02:00Z",
                "2026-08-22T10:02:00Z",
            )
            self.assertEqual(
                [item["candidateId"] for item in run["snapshot"]],
                ["INC-FIRST", "INC-SECOND"],
            )
            schema = json.loads(
                (REPO_ROOT / "schemas/aim-portfolio-run.schema.json").read_text()
            )
            self.assertEqual(validate(run, schema), [])

            run = activate_next(repo, run["updatedAt"], "2026-08-22T10:03:00Z")
            self.assertEqual(run["activeCandidateId"], "INC-FIRST")
            self.assertEqual(run["checkpoint"]["decisionAuthority"], "portfolio_mandate")
            run = checkpoint(
                repo,
                run["updatedAt"],
                "2026-08-22T10:04:00Z",
                "INC-FIRST",
                "epic_complete",
                "Epic closure",
                "portfolio_mandate",
            )
            run = complete_active(
                repo, run["updatedAt"], "2026-08-22T10:05:00Z", "INC-FIRST"
            )
            self.assertEqual(run["status"], "running")
            run = activate_next(repo, run["updatedAt"], "2026-08-22T10:06:00Z")
            self.assertEqual(run["activeCandidateId"], "INC-SECOND")
            run = checkpoint(
                repo,
                run["updatedAt"],
                "2026-08-22T10:07:00Z",
                "INC-SECOND",
                "epic_complete",
                "Epic closure",
                "portfolio_mandate",
            )
            run = complete_active(
                repo, run["updatedAt"], "2026-08-22T10:08:00Z", "INC-SECOND"
            )

            self.assertEqual(run["status"], "completed")
            self.assertEqual(run["completedCandidateIds"], ["INC-FIRST", "INC-SECOND"])
            projection, warnings = project_portfolio_run(repo / ".aim")
            self.assertEqual(warnings, [])
            self.assertEqual(projection["completed"], 2)
            self.assertEqual(projection["remaining"], 0)

    def test_pause_resume_preserves_active_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-TEST-002", "t1", "t1")
            run = activate_next(repo, "t1", "t2")
            checkpoint_before = run["checkpoint"]
            run = pause_run(repo, "t2", "t3", "Validation needs operator input")
            self.assertEqual(run["status"], "paused")
            with self.assertRaisesRegex(PortfolioRunError, "Only a running Portfolio"):
                activate_next(repo, "t3", "t4")
            run = resume_run(repo, "t3", "t4")
            self.assertEqual(run["status"], "running")
            self.assertEqual(run["checkpoint"], checkpoint_before)
            self.assertNotIn("pauseReason", run)

    def test_stale_and_tampered_state_fail_closed_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-TEST-003", "t1", "t1")
            path = repo / ".aim/portfolio-run.json"
            before = path.read_bytes()
            with self.assertRaisesRegex(PortfolioRunError, "changed since it was read"):
                activate_next(repo, "stale", "t2")
            self.assertEqual(path.read_bytes(), before)

            value = load_run(repo)
            value["snapshot"][0]["title"] = "Expanded work"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(PortfolioRunError, "mandate hash"):
                load_run(repo)

    def test_type_corrupt_state_reports_a_safe_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            create_run(repo, "MANDATE-TEST-TYPES", "t1", "t1")
            path = repo / ".aim/portfolio-run.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["status"] = {"unexpected": True}
            value["completedCandidateIds"] = [{"unexpected": True}]
            path.write_text(json.dumps(value), encoding="utf-8")

            with self.assertRaisesRegex(PortfolioRunError, "status is unsupported"):
                load_run(repo)
            projection, warnings = project_portfolio_run(repo / ".aim")
            self.assertFalse(projection["valid"])
            self.assertIn("completedCandidateIds", warnings[0])

    def test_existing_run_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            create_run(repo, "MANDATE-TEST-004", "t1", "t1")
            with self.assertRaisesRegex(PortfolioRunError, "already exists"):
                create_run(repo, "MANDATE-TEST-004", "t1", "t1")

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            outside = repo / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            (repo / ".aim/portfolio-run.json").symlink_to(outside)
            projection, warnings = project_portfolio_run(repo / ".aim")
            self.assertFalse(projection["valid"])
            self.assertIn("symbolic link", warnings[0])

    def test_skip_requires_user_authority_and_stop_is_durable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-TEST-005", "t1", "t1")
            run = activate_next(repo, "t1", "t2")
            with self.assertRaisesRegex(PortfolioRunError, "explicit user authority"):
                skip_active(repo, "t2", "t3", "INC-FIRST")
            run = checkpoint(
                repo, "t2", "t3", "INC-FIRST", "skip_requested", "Gate E", "user"
            )
            run = skip_active(repo, "t3", "t4", "INC-FIRST")
            self.assertEqual(run["skippedCandidateIds"], ["INC-FIRST"])
            run = stop_run(repo, "t4", "t5", "User stopped the Portfolio")
            self.assertEqual(run["status"], "stopped")
            self.assertEqual(load_run(repo)["pauseReason"], "User stopped the Portfolio")


if __name__ == "__main__":
    unittest.main()
