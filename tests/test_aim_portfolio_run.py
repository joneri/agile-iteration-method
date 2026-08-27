"""Portfolio Auto run contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_portfolio_run import (  # noqa: E402
    PortfolioRunError,
    activate_next,
    archive_run,
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

    def _complete_run(self, repo: Path) -> dict[str, Any]:
        run = create_run(repo, "MANDATE-COMPLETE", "t1", "t1")
        for candidate_id, increment_id, stamp in (
            ("INC-FIRST", "DI-001", 2),
            ("INC-SECOND", "DI-002", 5),
        ):
            run = activate_next(repo, run["updatedAt"], f"t{stamp}")
            self._publish_terminal_relation(repo, candidate_id, increment_id)
            run = checkpoint(
                repo,
                run["updatedAt"],
                f"t{stamp + 1}",
                candidate_id,
                "epic_complete",
                "Epic closure",
                "portfolio_mandate",
            )
            run = complete_active(
                repo, run["updatedAt"], f"t{stamp + 2}", candidate_id
            )
        return run

    def _publish_terminal_relation(
        self, repo: Path, candidate_id: str, increment_id: str
    ) -> None:
        aim = repo / ".aim"
        backlog_path = aim / "portfolio-backlog.json"
        backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
        candidate = next(item for item in backlog["items"] if item["id"] == candidate_id)
        candidate["runtimeIncrementId"] = increment_id
        backlog_path.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8")

        workspace_name = candidate["epicId"]
        workspace = aim / "portfolio" / workspace_name
        (workspace / "decisions").mkdir(parents=True)
        decision = workspace / "decisions" / f"{increment_id.lower()}-gate-e.md"
        decision.write_text(
            f"# Gate E — {increment_id}\n\nDecision: Accepted\n\nIncrement: {increment_id}\n",
            encoding="utf-8",
        )
        (workspace / "state.json").write_text(
            json.dumps(
                {
                    "stateSchemaVersion": "1.0",
                    "aimVersion": "2.0",
                    "mode": "Auto",
                    "costProfile": "Deep",
                    "epicId": candidate["epicId"],
                    "epicStatus": "epic_complete",
                    "activeIncrementId": None,
                    "previousIncrementId": increment_id,
                    "previousIncrementStatus": "accepted",
                    "gateEAcceptance": decision.relative_to(repo).as_posix(),
                    "portfolioCandidateId": candidate_id,
                    "currentRole": "PO",
                    "lastGatePassed": "Gate E",
                    "platform": "test",
                    "parallelSupport": {
                        "available": False,
                        "enabled": False,
                        "policy": "sequential_fallback",
                    },
                    "commitMode": "optional",
                    "updatedAt": "2026-08-22T10:04:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        catalog_path = aim / "ui-portfolio.json"
        catalog = (
            json.loads(catalog_path.read_text(encoding="utf-8"))
            if catalog_path.is_file()
            else {"portfolioVersion": "1.0", "workspaces": []}
        )
        relative = workspace.relative_to(aim).as_posix()
        if {"path": relative} not in catalog["workspaces"]:
            catalog["workspaces"].append({"path": relative})
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

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
            projection, warnings = project_portfolio_run(repo / ".aim")
            self.assertEqual(warnings, [])
            self.assertEqual(projection["transitionState"], "activation_pending")
            self.assertEqual(projection["checkpointStatus"], "activation_pending")
            self.assertEqual(projection["candidateEpics"]["INC-FIRST"], "EPIC-FIRST")
            run = checkpoint(
                repo,
                run["updatedAt"],
                "2026-08-22T10:04:00Z",
                "INC-FIRST",
                "epic_complete",
                "Epic closure",
                "portfolio_mandate",
            )
            self._publish_terminal_relation(repo, "INC-FIRST", "DI-001")
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
            self._publish_terminal_relation(repo, "INC-SECOND", "DI-002")
            run = complete_active(
                repo, run["updatedAt"], "2026-08-22T10:08:00Z", "INC-SECOND"
            )

            self.assertEqual(run["status"], "completed")
            self.assertEqual(run["completedCandidateIds"], ["INC-FIRST", "INC-SECOND"])
            projection, warnings = project_portfolio_run(repo / ".aim")
            self.assertEqual(warnings, [])
            self.assertEqual(projection["completed"], 2)
            self.assertEqual(projection["remaining"], 0)
            self.assertEqual(projection["transitionState"], "completed")

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

    def test_checkpoint_rejects_noncanonical_runtime_status_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-CANONICAL", "t1", "t1")
            run = activate_next(repo, "t1", "t2")
            before = (repo / ".aim/portfolio-run.json").read_bytes()

            with self.assertRaisesRegex(PortfolioRunError, "not canonical"):
                checkpoint(
                    repo,
                    "t2",
                    "t3",
                    "INC-FIRST",
                    "validation_in_progress",
                    "Gate D",
                    "portfolio_mandate",
                )

            self.assertEqual((repo / ".aim/portfolio-run.json").read_bytes(), before)

    def test_completion_requires_the_canonical_terminal_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-TERMINAL", "t1", "t1")
            run = activate_next(repo, "t1", "t2")
            run = checkpoint(
                repo,
                "t2",
                "t3",
                "INC-FIRST",
                "epic_complete",
                "Epic closure",
                "portfolio_mandate",
            )
            before = (repo / ".aim/portfolio-run.json").read_bytes()

            with self.assertRaisesRegex(
                PortfolioRunError, "runtimeIncrementId is missing"
            ):
                complete_active(repo, "t3", "t4", "INC-FIRST")

            self.assertEqual((repo / ".aim/portfolio-run.json").read_bytes(), before)
            self._publish_terminal_relation(repo, "INC-FIRST", "DI-001")
            state_path = repo / ".aim/portfolio/EPIC-FIRST/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.pop("gateEAcceptance")
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PortfolioRunError, "gateEAcceptance is missing"):
                complete_active(repo, "t3", "t4", "INC-FIRST")

            state["gateEAcceptance"] = ".aim/portfolio/EPIC-FIRST/decisions/di-001-gate-e.md"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

            state["lastGatePassed"] = "Gate D"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PortfolioRunError, "lastGatePassed is not Gate E"):
                complete_active(repo, "t3", "t4", "INC-FIRST")

            state["lastGatePassed"] = "Gate E"
            state["portfolioCandidateId"] = "INC-WRONG"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                PortfolioRunError, "portfolioCandidateId does not match"
            ):
                complete_active(repo, "t3", "t4", "INC-FIRST")

            state["portfolioCandidateId"] = "INC-FIRST"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            workspace = repo / ".aim/portfolio/EPIC-FIRST"
            saved_workspace = repo / ".aim/portfolio/EPIC-FIRST-saved"
            workspace.rename(saved_workspace)
            workspace.symlink_to(saved_workspace, target_is_directory=True)
            with self.assertRaisesRegex(
                PortfolioRunError,
                "catalog does not resolve exactly one authoritative Epic workspace",
            ):
                complete_active(repo, "t3", "t4", "INC-FIRST")
            workspace.unlink()
            saved_workspace.rename(workspace)

            completed = complete_active(repo, "t3", "t4", "INC-FIRST")
            self.assertEqual(completed["completedCandidateIds"], ["INC-FIRST"])

    def test_snapshot_matches_visible_unactivated_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            path = repo / ".aim/portfolio-backlog.json"
            backlog = json.loads(path.read_text(encoding="utf-8"))
            for index in range(3, 13):
                backlog["items"].append(
                    {
                        "id": f"INC-{index:02d}",
                        "epicId": f"EPIC-{index:02d}",
                        "epicTitle": f"Epic {index}",
                        "title": f"Deliver {index}",
                        "priority": index,
                        "createdAt": f"2026-08-22T10:{index:02d}:00Z",
                        **({"runtimeIncrementId": f"DI-{index:03d}"} if index <= 6 else {}),
                    }
                )
            backlog["items"][0]["runtimeIncrementId"] = "DI-001"
            backlog["items"][1]["runtimeIncrementId"] = "DI-002"
            path.write_text(json.dumps(backlog), encoding="utf-8")

            run = create_run(repo, "MANDATE-VISIBLE", "t1", "t1")

            self.assertEqual(
                [item["candidateId"] for item in run["snapshot"]],
                ["INC-07", "INC-08", "INC-09", "INC-10", "INC-11", "INC-12"],
            )

    def test_invalid_or_fully_activated_backlog_creates_no_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            path = repo / ".aim/portfolio-backlog.json"
            backlog = json.loads(path.read_text(encoding="utf-8"))
            backlog["items"][0]["runtimeIncrementId"] = "not-a-di"
            path.write_text(json.dumps(backlog), encoding="utf-8")
            with self.assertRaisesRegex(PortfolioRunError, "runtimeIncrementId"):
                create_run(repo, "MANDATE-INVALID", "t1", "t1")
            self.assertFalse((repo / ".aim/portfolio-run.json").exists())

            backlog["items"][0]["runtimeIncrementId"] = "DI-001"
            backlog["items"][1]["runtimeIncrementId"] = "DI-002"
            path.write_text(json.dumps(backlog), encoding="utf-8")
            with self.assertRaisesRegex(PortfolioRunError, "no unactivated candidates"):
                create_run(repo, "MANDATE-EMPTY", "t1", "t1")
            self.assertFalse((repo / ".aim/portfolio-run.json").exists())

    def test_run_snapshot_excludes_allocated_epic_and_rechecks_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            aim = repo / ".aim"
            (aim / "increments").mkdir()
            (aim / "decisions").mkdir()
            (aim / "reviews").mkdir()
            state = {
                "stateSchemaVersion": "1.0",
                "aimVersion": "2.0",
                "mode": "Auto",
                "costProfile": "Deep",
                "epicId": "EPIC-FIRST",
                "epicStatus": "epic_complete",
                "activeIncrementId": None,
                "previousIncrementId": "DI-001",
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "platform": "test",
                "parallelSupport": {
                    "available": False,
                    "enabled": False,
                    "policy": "sequential_fallback",
                },
                "commitMode": "optional",
                "updatedAt": "2026-08-22T09:00:00Z",
            }
            (aim / "state.json").write_text(json.dumps(state) + "\n")
            (aim / "epic.md").write_text("# EPIC-FIRST — Existing outcome\n")
            (aim / "increments/001-plan.md").write_text(
                "# DI-001 — Existing\n\nEpic: EPIC-FIRST\n"
            )
            (aim / "ui-portfolio.json").write_text(
                json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "."}]})
                + "\n"
            )

            run = create_run(
                repo,
                "MANDATE-PREFLIGHT",
                "t1",
                "t1",
                expected_backlog_updated_at="2026-08-22T10:00:00Z",
            )
            self.assertEqual(
                [item["candidateId"] for item in run["snapshot"]], ["INC-SECOND"]
            )

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            path = repo / ".aim/portfolio-backlog.json"

            def make_stale() -> None:
                backlog = json.loads(path.read_text())
                backlog["updatedAt"] = "2026-08-22T10:09:00Z"
                path.write_text(json.dumps(backlog) + "\n")

            with self.assertRaisesRegex(
                PortfolioRunError, "changed immediately before run creation"
            ):
                create_run(
                    repo,
                    "MANDATE-STALE-PREFLIGHT",
                    "t1",
                    "t1",
                    before_write_hook=make_stale,
                )
            self.assertFalse((repo / ".aim/portfolio-run.json").exists())

    def test_completed_run_archives_exactly_and_allows_fresh_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = self._complete_run(repo)
            run_path = repo / ".aim/portfolio-run.json"
            original = run_path.read_bytes()

            archived, archived_path = archive_run(repo, run["updatedAt"], "t9")

            self.assertEqual(archived, run)
            self.assertFalse(run_path.exists())
            self.assertEqual((repo / archived_path).read_bytes(), original)

            backlog_path = repo / ".aim/portfolio-backlog.json"
            backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
            backlog["items"][0]["runtimeIncrementId"] = "DI-001"
            backlog["items"][1]["runtimeIncrementId"] = "DI-002"
            backlog["items"].append(
                {
                    "id": "INC-THIRD",
                    "epicId": "EPIC-THIRD",
                    "epicTitle": "Third Epic",
                    "title": "Finish third",
                    "priority": 3,
                    "createdAt": "2026-08-22T10:09:00Z",
                }
            )
            backlog_path.write_text(json.dumps(backlog), encoding="utf-8")
            fresh = create_run(repo, "MANDATE-FRESH", "t10", "t10")
            self.assertEqual(
                [item["candidateId"] for item in fresh["snapshot"]], ["INC-THIRD"]
            )

    def test_archive_rejects_nonterminal_stale_symlink_and_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = create_run(repo, "MANDATE-RUNNING", "t1", "t1")
            with self.assertRaisesRegex(PortfolioRunError, "completed or stopped"):
                archive_run(repo, run["updatedAt"], "t2")
            self.assertTrue((repo / ".aim/portfolio-run.json").exists())

            run = pause_run(repo, run["updatedAt"], "t2", "Operator paused")
            with self.assertRaisesRegex(PortfolioRunError, "completed or stopped"):
                archive_run(repo, run["updatedAt"], "t3")
            self.assertTrue((repo / ".aim/portfolio-run.json").exists())

            run = resume_run(repo, run["updatedAt"], "t3")
            run = stop_run(repo, run["updatedAt"], "t4", "Operator stopped")
            with self.assertRaisesRegex(PortfolioRunError, "changed since it was read"):
                archive_run(repo, "stale", "t5")
            self.assertTrue((repo / ".aim/portfolio-run.json").exists())

            archive_root = repo / ".aim/archive"
            outside = repo / "outside"
            outside.mkdir()
            archive_root.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(PortfolioRunError, "symbolic link"):
                archive_run(repo, run["updatedAt"], "t5")
            self.assertTrue((repo / ".aim/portfolio-run.json").exists())
            archive_root.unlink()

            _, archived_path = archive_run(repo, run["updatedAt"], "t5")
            self.assertTrue(archived_path.startswith(".aim/archive/"))
            (repo / ".aim/portfolio-run.json").write_bytes(
                (repo / archived_path).read_bytes()
            )
            with self.assertRaisesRegex(PortfolioRunError, "already exists"):
                archive_run(repo, run["updatedAt"], "t5")
            self.assertTrue((repo / ".aim/portfolio-run.json").exists())

    def test_archive_rejects_malformed_run_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            create_run(repo, "MANDATE-MALFORMED", "t1", "t1")
            path = repo / ".aim/portfolio-run.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["status"] = {"unexpected": True}
            path.write_text(json.dumps(value), encoding="utf-8")
            before = path.read_bytes()

            with self.assertRaisesRegex(PortfolioRunError, "Invalid Portfolio run"):
                archive_run(repo, "t1", "t2")

            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((repo / ".aim/archive").exists())

    def test_archive_cli_reports_the_contained_evidence_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            run = self._complete_run(repo)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/aim_portfolio_run.py"),
                    "--repo",
                    str(repo),
                    "archive",
                    "--expected-updated-at",
                    run["updatedAt"],
                    "--archived-at",
                    "t9",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["archivedPath"].startswith(".aim/archive/"))
            self.assertTrue((repo / payload["archivedPath"]).is_file())
            self.assertFalse((repo / ".aim/portfolio-run.json").exists())

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
            run = checkpoint(repo, "t2", "t3", "INC-FIRST", "blocked", "Gate E", "user")
            run = skip_active(repo, "t3", "t4", "INC-FIRST")
            self.assertEqual(run["skippedCandidateIds"], ["INC-FIRST"])
            run = stop_run(repo, "t4", "t5", "User stopped the Portfolio")
            self.assertEqual(run["status"], "stopped")
            self.assertEqual(load_run(repo)["pauseReason"], "User stopped the Portfolio")


if __name__ == "__main__":
    unittest.main()
