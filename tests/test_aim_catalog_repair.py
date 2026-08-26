"""Regression tests for approved Portfolio catalog-history repair."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_catalog_repair import (  # noqa: E402
    CatalogRepairError,
    apply_repair,
    plan_repair,
)


class AimCatalogRepairTests(unittest.TestCase):
    def _repo(self, root: Path, *, canonical: bool = False) -> Path:
        aim = root / ".aim"
        workspace = aim / "workspaces/legacy"
        (workspace / "increments").mkdir(parents=True)
        (workspace / "decisions").mkdir()
        (workspace / "reviews").mkdir()
        (aim / "decisions").mkdir()
        (aim / "increments").mkdir()
        (aim / "reviews").mkdir()

        evidence = workspace / "decisions/2026-08-25-user-accepted.md"
        evidence.write_text(
            "# DI-088 Gate E — Accepted\n\nDecision: Accept DI-088 as Done.\n",
            encoding="utf-8",
        )
        state = {
            "stateSchemaVersion": "1.0",
            "aimVersion": "2.0",
            "mode": "Strict",
            "costProfile": "Deep",
            "epicId": "EPIC-BACKLOG-AIM-UI",
            "epicStatus": "epic_complete",
            "activeIncrementId": "DI-088",
            "currentRole": "PO",
            "lastGatePassed": "Gate E",
            "platform": "test",
            "parallelSupport": {
                "available": False,
                "enabled": False,
                "policy": "sequential_fallback",
            },
            "commitMode": "optional",
            "updatedAt": "2026-08-25T10:00:00Z",
        }
        if canonical:
            state["activeIncrementId"] = None
            state["previousIncrementId"] = "DI-088"
            state["previousIncrementStatus"] = "accepted"
            state["gateEAcceptance"] = (
                ".aim/workspaces/legacy/decisions/2026-08-25-user-accepted.md"
            )
        (workspace / "state.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        (workspace / "epic.md").write_text(
            "# EPIC-BACKLOG-AIM-UI — Portfolio control\n", encoding="utf-8"
        )
        (workspace / "increments/088-wip.md").write_text(
            "# DI-088 — Control concurrent Epics\n", encoding="utf-8"
        )
        (workspace / "reviews/review-088.md").write_text(
            "# DI-088 Review\n\nNo blocking findings.\n", encoding="utf-8"
        )
        (aim / "ui-portfolio.json").write_text(
            json.dumps(
                {
                    "portfolioVersion": "1.0",
                    "workspaces": [{"path": "."}, {"path": "workspaces/legacy"}],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (aim / "portfolio-backlog.json").write_text(
            json.dumps(
                {
                    "backlogVersion": "1.0",
                    "updatedAt": "2026-08-25T09:00:00Z",
                    "items": [
                        {
                            "id": "INC-UI-CONTROL-001",
                            "epicId": "EPIC-BACKLOG-AIM-UI",
                            "epicTitle": "AIM UI — Portfolio control",
                            "title": "Control concurrent Epics from AIM chat",
                            "summary": "Choose focus and capacity.",
                            "priority": 1,
                            "createdAt": "2026-08-21T17:45:00Z",
                            "runtimeIncrementId": "DI-088",
                        },
                        {
                            "id": "INC-NEXT-001",
                            "epicId": "EPIC-NEXT",
                            "epicTitle": "Next Epic",
                            "title": "Deliver next behavior",
                            "priority": 2,
                            "createdAt": "2026-08-25T09:00:00Z",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return root

    def _request(self) -> dict[str, str]:
        return {
            "candidate_id": "INC-UI-CONTROL-001",
            "epic_id": "EPIC-BACKLOG-AIM-UI",
            "increment_id": "DI-088",
            "workspace": "workspaces/legacy",
            "acceptance_evidence": (
                ".aim/workspaces/legacy/decisions/2026-08-25-user-accepted.md"
            ),
            "archived_at": "2026-08-25T11:00:00Z",
        }

    def _expected(self, plan: dict[str, object]) -> dict[str, str]:
        return {
            "expected_catalog_sha256": str(plan["catalogSha256"]),
            "expected_backlog_sha256": str(plan["backlogSha256"]),
            "expected_state_sha256": str(plan["stateSha256"]),
            "expected_acceptance_sha256": str(plan["acceptanceSha256"]),
            "expected_workspace_sha256": str(plan["workspaceTreeSha256"]),
            "expected_state_updated_at": str(plan["stateUpdatedAt"]),
        }

    def _tree(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }

    def test_preview_is_no_write_and_apply_retires_the_exact_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            aim = repo / ".aim"
            source = aim / "workspaces/legacy"
            catalog = aim / "ui-portfolio.json"
            backlog = aim / "portfolio-backlog.json"
            before_catalog = catalog.read_bytes()
            before_backlog = backlog.read_bytes()
            before_workspace = self._tree(source)

            plan = plan_repair(repo, **self._request())
            self.assertEqual(plan["result"], "planned")
            self.assertEqual(catalog.read_bytes(), before_catalog)
            self.assertEqual(backlog.read_bytes(), before_backlog)
            self.assertEqual(self._tree(source), before_workspace)

            result = apply_repair(repo, **self._request(), **self._expected(plan))
            self.assertEqual(result["result"], "applied")
            self.assertFalse(source.exists())
            archive = repo / str(result["archivePath"])
            self.assertEqual(self._tree(archive), before_workspace)
            self.assertNotIn(
                {"path": "workspaces/legacy"},
                json.loads(catalog.read_text(encoding="utf-8"))["workspaces"],
            )
            remaining = json.loads(backlog.read_text(encoding="utf-8"))["items"]
            self.assertEqual([item["id"] for item in remaining], ["INC-NEXT-001"])
            audit = json.loads((repo / str(result["auditPath"])).read_text(encoding="utf-8"))
            self.assertEqual(audit["retiredCandidate"]["id"], "INC-UI-CONTROL-001")
            self.assertEqual(audit["evidence"]["workspaceTreeSha256"], plan["workspaceTreeSha256"])
            self.assertTrue(
                (repo / audit["archivedAcceptanceEvidence"]).is_file()
            )
            self.assertEqual(list(aim.glob(".catalog-repair-*")), [])
            self.assertEqual(list(aim.glob("*.tmp")), [])

    def test_current_state_linked_acceptance_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), canonical=True)
            evidence = repo / self._request()["acceptance_evidence"]
            evidence.write_text(
                evidence.read_text(encoding="utf-8")
                + "\nA prior change requested checkpoint was resolved before acceptance.\n",
                encoding="utf-8",
            )
            plan = plan_repair(repo, **self._request())
            self.assertEqual(plan["stateUpdatedAt"], "2026-08-25T10:00:00Z")
            self.assertTrue(plan["acceptanceEvidence"].endswith("user-accepted.md"))

    def test_every_publication_failure_restores_exact_pre_state(self) -> None:
        for fault in (
            "after_staging",
            "after_workspace_archive",
            "after_catalog_publish",
            "after_backlog_publish",
            "after_audit_publish",
            "after_verify",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                repo = self._repo(Path(temporary))
                aim = repo / ".aim"
                source = aim / "workspaces/legacy"
                catalog = aim / "ui-portfolio.json"
                backlog = aim / "portfolio-backlog.json"
                before_catalog = catalog.read_bytes()
                before_backlog = backlog.read_bytes()
                before_workspace = self._tree(source)
                plan = plan_repair(repo, **self._request())

                with self.assertRaisesRegex(CatalogRepairError, fault):
                    apply_repair(
                        repo,
                        **self._request(),
                        **self._expected(plan),
                        fault_at=fault,
                    )
                self.assertEqual(catalog.read_bytes(), before_catalog)
                self.assertEqual(backlog.read_bytes(), before_backlog)
                self.assertEqual(self._tree(source), before_workspace)
                self.assertFalse((repo / str(plan["archivePath"])).exists())
                self.assertFalse((repo / str(plan["auditPath"])).exists())
                self.assertEqual(list(aim.glob(".catalog-repair-*")), [])

    def test_stale_preview_blocks_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            plan = plan_repair(repo, **self._request())
            backlog = repo / ".aim/portfolio-backlog.json"
            value = json.loads(backlog.read_text(encoding="utf-8"))
            value["updatedAt"] = "2026-08-25T10:30:00Z"
            backlog.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            changed = backlog.read_bytes()

            with self.assertRaisesRegex(CatalogRepairError, "changed since preview"):
                apply_repair(repo, **self._request(), **self._expected(plan))
            self.assertEqual(backlog.read_bytes(), changed)
            self.assertTrue((repo / ".aim/workspaces/legacy").is_dir())

    def test_incomplete_mismatched_or_ambiguous_authority_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            state_path = repo / ".aim/workspaces/legacy/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["epicStatus"] = "increment_in_progress"
            state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogRepairError, "completed through Gate E"):
                plan_repair(repo, **self._request())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            evidence = repo / self._request()["acceptance_evidence"]
            evidence.write_text("# DI-999 Gate E — Accepted\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogRepairError, "must name the runtime Increment"):
                plan_repair(repo, **self._request())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            evidence = repo / self._request()["acceptance_evidence"]
            evidence.write_text(
                "# DI-088 Gate E — Not accepted\n\nDecision: change requested.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CatalogRepairError, "acceptance evidence"):
                plan_repair(repo, **self._request())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            backlog = repo / ".aim/portfolio-backlog.json"
            value = json.loads(backlog.read_text(encoding="utf-8"))
            duplicate = dict(value["items"][0])
            duplicate["id"] = "INC-UI-CONTROL-002"
            value["items"].append(duplicate)
            backlog.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogRepairError, "multiple runtime-linked"):
                plan_repair(repo, **self._request())

    def test_root_traversal_and_symlink_workspaces_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            request = self._request()
            request["workspace"] = "."
            with self.assertRaisesRegex(CatalogRepairError, "root .aim"):
                plan_repair(repo, **request)

        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            repo = self._repo(Path(temporary))
            source = repo / ".aim/workspaces/legacy"
            for path in sorted(source.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            source.rmdir()
            source.symlink_to(Path(outside), target_is_directory=True)
            with self.assertRaisesRegex(CatalogRepairError, "symbolic link"):
                plan_repair(repo, **self._request())

    def test_workspace_symlink_swap_during_staging_publishes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            repo = self._repo(Path(temporary))
            aim = repo / ".aim"
            source = aim / "workspaces/legacy"
            saved = aim / "workspaces/legacy-saved"
            catalog = aim / "ui-portfolio.json"
            backlog = aim / "portfolio-backlog.json"
            before_catalog = catalog.read_bytes()
            before_backlog = backlog.read_bytes()
            plan = plan_repair(repo, **self._request())

            def swap(checkpoint: str) -> None:
                if checkpoint == "after_staging":
                    source.rename(saved)
                    source.symlink_to(Path(outside), target_is_directory=True)

            with self.assertRaisesRegex(CatalogRepairError, "symbolic link"):
                apply_repair(
                    repo,
                    **self._request(),
                    **self._expected(plan),
                    fault_hook=swap,
                )
            self.assertEqual(catalog.read_bytes(), before_catalog)
            self.assertEqual(backlog.read_bytes(), before_backlog)
            self.assertFalse((repo / str(plan["archivePath"])).exists())
            self.assertFalse((repo / str(plan["auditPath"])).exists())
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
