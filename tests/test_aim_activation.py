"""Shared activation-preflight contract tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_activation import activation_preflight  # noqa: E402


class ActivationPreflightTests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        aim = root / ".aim"
        (aim / "increments").mkdir(parents=True)
        (aim / "decisions").mkdir()
        (aim / "reviews").mkdir()
        state = {
            "stateSchemaVersion": "1.0",
            "aimVersion": "2.0",
            "mode": "Auto",
            "costProfile": "Deep",
            "epicId": "EPIC-ALLOCATED",
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
            "updatedAt": "2026-08-26T01:00:00Z",
        }
        (aim / "state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
        (aim / "epic.md").write_text("# EPIC-ALLOCATED — Existing outcome\n")
        (aim / "increments/001-plan.md").write_text(
            "# DI-001 — Existing delivery\n\nEpic: EPIC-ALLOCATED\n"
        )
        (aim / "ui-portfolio.json").write_text(
            json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "."}]})
            + "\n",
            encoding="utf-8",
        )
        (aim / "portfolio-backlog.json").write_text(
            json.dumps(
                {
                    "backlogVersion": "1.0",
                    "updatedAt": "2026-08-26T02:00:00Z",
                    "items": [
                        {
                            "id": "INC-ALLOCATED",
                            "epicId": "EPIC-ALLOCATED",
                            "epicTitle": "Existing outcome",
                            "title": "Must remain blocked",
                            "priority": 1,
                            "createdAt": "2026-08-26T02:00:00Z",
                        },
                        {
                            "id": "INC-FRESH",
                            "epicId": "EPIC-FRESH",
                            "epicTitle": "Fresh outcome",
                            "title": "May start",
                            "priority": 2,
                            "createdAt": "2026-08-26T02:01:00Z",
                        },
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return root

    def _append_closed_history(self, repo: Path, count: int) -> None:
        aim = repo / ".aim"
        catalog_path = aim / "ui-portfolio.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        template = json.loads((aim / "state.json").read_text(encoding="utf-8"))
        for index in range(1, count + 1):
            workspace = aim / "workspaces" / f"history-{index:03d}"
            workspace.mkdir(parents=True)
            runtime = {
                **template,
                "epicId": f"EPIC-HISTORY-{index:03d}",
                "previousIncrementId": f"DI-{index + 1000}",
            }
            (workspace / "state.json").write_text(
                json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
            )
            catalog["workspaces"].append(
                {"path": f"workspaces/history-{index:03d}"}
            )
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    def test_allocated_identity_is_blocked_and_fresh_identity_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            blocked = activation_preflight(
                repo,
                epic_id="EPIC-ALLOCATED",
                candidate_id="INC-ALLOCATED",
                expected_backlog_updated_at="2026-08-26T02:00:00Z",
                expected_candidate_updated_at="2026-08-26T02:00:00Z",
            )
            allowed = activation_preflight(
                repo,
                epic_id="EPIC-FRESH",
                candidate_id="INC-FRESH",
                expected_backlog_updated_at="2026-08-26T02:00:00Z",
                expected_candidate_updated_at="2026-08-26T02:01:00Z",
            )

        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["code"], "epic_allocated")
        self.assertIn("already allocated", blocked["message"])
        self.assertTrue(allowed["allowed"])

    def test_freshness_replay_capacity_and_collision_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            stale = activation_preflight(
                repo,
                epic_id="EPIC-FRESH",
                candidate_id="INC-FRESH",
                expected_backlog_updated_at="stale",
            )
            self.assertEqual(stale["code"], "backlog_stale")

            backlog_path = repo / ".aim/portfolio-backlog.json"
            backlog = json.loads(backlog_path.read_text())
            backlog["items"][1]["runtimeIncrementId"] = "DI-002"
            backlog_path.write_text(json.dumps(backlog) + "\n")
            replay = activation_preflight(
                repo, epic_id="EPIC-FRESH", candidate_id="INC-FRESH"
            )
            self.assertEqual(replay["code"], "repository_invalid")
            self.assertIn("cannot be replayed", replay["message"])

            backlog["items"][1].pop("runtimeIncrementId")
            backlog_path.write_text(json.dumps(backlog) + "\n")
            state_path = repo / ".aim/state.json"
            state = json.loads(state_path.read_text())
            state["epicStatus"] = "increment_in_progress"
            state_path.write_text(json.dumps(state) + "\n")
            (repo / ".aim/portfolio-control.json").write_text(
                json.dumps(
                    {
                        "controlVersion": "1.0",
                        "maxActiveEpics": 1,
                        "updatedAt": "2026-08-26T02:02:00Z",
                    }
                )
                + "\n"
            )
            full = activation_preflight(repo, epic_id="EPIC-FRESH")
            self.assertEqual(full["code"], "capacity_full")

            state["epicStatus"] = "epic_complete"
            state_path.write_text(json.dumps(state) + "\n")
            target = repo / ".aim/portfolio/EPIC-FRESH"
            target.mkdir(parents=True)
            collision = activation_preflight(repo, epic_id="EPIC-FRESH")
            self.assertEqual(collision["code"], "workspace_collision")

    def test_catalog_traversal_and_symlink_escape_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.write_text(
                json.dumps(
                    {"portfolioVersion": "1.0", "workspaces": [{"path": "../outside"}]}
                )
                + "\n"
            )
            traversal = activation_preflight(repo, epic_id="EPIC-FRESH")
            self.assertEqual(traversal["code"], "repository_invalid")
            self.assertIn("traversal", traversal["message"])

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            outside = repo / "outside"
            outside.mkdir()
            linked = repo / ".aim/workspaces/linked"
            linked.parent.mkdir()
            linked.symlink_to(outside)
            (repo / ".aim/ui-portfolio.json").write_text(
                json.dumps(
                    {
                        "portfolioVersion": "1.0",
                        "workspaces": [{"path": "workspaces/linked"}],
                    }
                )
                + "\n"
            )
            escaped = activation_preflight(repo, epic_id="EPIC-FRESH")
            self.assertEqual(escaped["code"], "repository_invalid")
            self.assertIn("symbolic link", escaped["message"])

    def test_large_closed_history_does_not_consume_activation_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._append_closed_history(repo, 99)
            (repo / ".aim/portfolio-control.json").write_text(
                json.dumps(
                    {
                        "controlVersion": "1.0",
                        "maxActiveEpics": 1,
                        "updatedAt": "2026-08-26T02:02:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            allowed = activation_preflight(repo, epic_id="EPIC-FRESH")

        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["runningEpicIds"], [])
