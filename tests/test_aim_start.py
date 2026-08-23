"""Portfolio-aware AIM start transaction regression tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_start import AimStartError, apply_start, plan_start  # noqa: E402
from aim_ui import build_board  # noqa: E402
from validate_aim_runtime import audit_portfolio_workspace_integrity  # noqa: E402


class AimStartTests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        aim = root / ".aim"
        (aim / "increments").mkdir(parents=True)
        (aim / "decisions").mkdir()
        (aim / "reviews").mkdir()
        state = {
            "stateSchemaVersion": "1.0",
            "aimVersion": "2.0",
            "mode": "Auto",
            "costProfile": "Standard",
            "epicId": "EPIC-EXISTING",
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
            "updatedAt": "2026-08-23T10:00:00Z",
        }
        (aim / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        (aim / "epic.md").write_text("# EPIC-EXISTING — Existing history\n", encoding="utf-8")
        (aim / "increments/001-plan.md").write_text(
            "# DI-001 — Existing Increment\n\nEpic: EPIC-EXISTING\n", encoding="utf-8"
        )
        (aim / "ui-portfolio.json").write_text(
            json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "."}]}, indent=2) + "\n",
            encoding="utf-8",
        )
        return root

    def _request(self) -> dict[str, str]:
        return {
            "epic_id": "EPIC-NEW-001",
            "increment_id": "DI-002",
            "title": "Visible Portfolio start",
            "mode": "Auto",
            "cost_profile": "Deep",
            "updated_at": "2026-08-23T11:00:00Z",
            "platform": "test",
        }

    def test_preview_is_no_write_and_apply_is_visible_with_current_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            root_state = repo / ".aim/state.json"
            before_catalog = catalog.read_bytes()
            before_root = root_state.read_bytes()

            plan = plan_start(repo, **self._request())
            self.assertEqual(plan["result"], "planned")
            self.assertEqual(catalog.read_bytes(), before_catalog)
            self.assertEqual(root_state.read_bytes(), before_root)
            self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())

            result = apply_start(
                repo,
                **self._request(),
                expected_catalog_sha256=plan["catalogSha256"],
            )
            self.assertTrue(result["visibleOnBoard"])
            self.assertTrue(result["gateAReady"])
            self.assertEqual(root_state.read_bytes(), before_root)

            workspace = repo / ".aim/portfolio/EPIC-NEW-001"
            state = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stateSchemaVersion"], "1.0")
            self.assertEqual(state["epicStatus"], "gate_a_pending")
            self.assertIsNone(state["activeIncrementId"])
            self.assertEqual(state["plannedIncrementId"], "DI-002")
            self.assertIsNone(state["lastGatePassed"])
            self.assertEqual(state["uiDecision"]["visibility"], "ready")

            board = build_board(repo)
            epic = next(item for item in board["epics"] if item["id"] == "EPIC-NEW-001")
            self.assertEqual(epic["workspace"], "portfolio/EPIC-NEW-001")
            self.assertEqual(epic["plannedIncrementId"], "DI-002")
            increment = next(item for item in epic["increments"] if item["id"] == "DI-002")
            self.assertEqual(increment["runtimeStatus"], "gate_a_pending")
            self.assertTrue(increment["identityReserved"])
            self.assertEqual(list((repo / ".aim").rglob("*.tmp")), [])
            self.assertEqual(list((repo / ".aim").glob(".EPIC-NEW-001.start-*")), [])

    def test_every_bounded_publication_failure_rolls_back_catalog_and_workspace(self) -> None:
        for fault in (
            "after_staging",
            "after_workspace_publish",
            "after_catalog_publish",
            "after_ready_publish",
        ):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                repo = self._repo(Path(temporary))
                catalog = repo / ".aim/ui-portfolio.json"
                root_state = repo / ".aim/state.json"
                before_catalog = catalog.read_bytes()
                before_root = root_state.read_bytes()
                with self.assertRaisesRegex(AimStartError, fault):
                    apply_start(repo, **self._request(), fault_at=fault)
                self.assertEqual(catalog.read_bytes(), before_catalog)
                self.assertEqual(root_state.read_bytes(), before_root)
                self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())
                self.assertEqual(list((repo / ".aim").glob(".EPIC-NEW-001.start-*")), [])

    def test_stale_preview_and_identity_collisions_fail_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            plan = plan_start(repo, **self._request())
            catalog = repo / ".aim/ui-portfolio.json"
            changed = json.loads(catalog.read_text(encoding="utf-8"))
            changed["workspaces"].append({"path": "missing"})
            catalog.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(AimStartError):
                apply_start(
                    repo,
                    **self._request(),
                    expected_catalog_sha256=plan["catalogSha256"],
                )
            self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            request = self._request()
            request["increment_id"] = "DI-001"
            with self.assertRaisesRegex(AimStartError, "already allocated"):
                plan_start(repo, **request)
            request = self._request()
            request["epic_id"] = "EPIC-EXISTING"
            with self.assertRaisesRegex(AimStartError, "already allocated"):
                plan_start(repo, **request)

    def test_legacy_or_duplicate_declared_authority_blocks_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            state_path = repo / ".aim/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["lastGatePassed"] = "E"
            state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(AimStartError, "Gate checkpoint"):
                plan_start(repo, **self._request())
            self.assertEqual(state_path.read_bytes(), before)
            self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            state_path = repo / ".aim/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            del state["activeIncrementId"]
            state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AimStartError, "missing required runtime fields"):
                plan_start(repo, **self._request())
            self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            duplicate = repo / ".aim/workspaces/duplicate"
            duplicate.mkdir(parents=True)
            (duplicate / "state.json").write_bytes((repo / ".aim/state.json").read_bytes())
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.write_text(
                json.dumps(
                    {
                        "portfolioVersion": "1.0",
                        "workspaces": [{"path": "."}, {"path": "workspaces/duplicate"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            before = catalog.read_bytes()
            with self.assertRaisesRegex(AimStartError, "Epic identity .* duplicated"):
                plan_start(repo, **self._request())
            self.assertEqual(catalog.read_bytes(), before)

    def test_portfolio_parent_symlink_swap_during_staging_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            before = catalog.read_bytes()

            def swap_parent(checkpoint: str) -> None:
                if checkpoint == "after_staging":
                    (repo / ".aim/portfolio").symlink_to(Path(outside), target_is_directory=True)

            with self.assertRaisesRegex(AimStartError, "symbolic link"):
                apply_start(repo, **self._request(), fault_hook=swap_parent)
            self.assertEqual(catalog.read_bytes(), before)
            self.assertFalse((Path(outside) / "EPIC-NEW-001").exists())
            self.assertEqual(list((repo / ".aim").glob(".EPIC-NEW-001.start-*")), [])

    def test_invalid_traversal_capacity_and_symlink_catalogs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.write_text(
                json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "../escape"}]}) + "\n",
                encoding="utf-8",
            )
            before = catalog.read_bytes()
            with self.assertRaisesRegex(AimStartError, "traversal"):
                plan_start(repo, **self._request())
            self.assertEqual(catalog.read_bytes(), before)

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            target = repo / "catalog.json"
            target.write_bytes(catalog.read_bytes())
            catalog.unlink()
            catalog.symlink_to(target)
            with self.assertRaisesRegex(AimStartError, "symbolic link"):
                plan_start(repo, **self._request())

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            workspaces = [{"path": "."}]
            for index in range(1, 16):
                workspace = repo / ".aim/workspaces" / str(index)
                workspace.mkdir(parents=True)
                (workspace / "state.json").write_text(
                    json.dumps({"epicId": f"EPIC-{index}"}) + "\n", encoding="utf-8"
                )
                workspaces.append({"path": f"workspaces/{index}"})
            (repo / ".aim/ui-portfolio.json").write_text(
                json.dumps({"portfolioVersion": "1.0", "workspaces": workspaces}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AimStartError, "capacity is full"):
                plan_start(repo, **self._request())

    def test_validator_names_orphan_and_every_legacy_contract_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            other = repo / ".aim/workspaces/other"
            other.mkdir(parents=True)
            (other / "state.json").write_text(
                json.dumps({"epicId": "EPIC-OTHER"}) + "\n", encoding="utf-8"
            )
            portfolio = {
                "portfolioVersion": "1.0",
                "workspaces": [{"path": "workspaces/other"}],
            }
            state_path = repo / ".aim/state.json"
            legacy = json.loads(state_path.read_text(encoding="utf-8"))
            legacy.update(
                {
                    "epicId": "EPIC-ORPHAN",
                    "epicStatus": "complete",
                    "activeIncrementId": "INC-LEGACY-037",
                    "lastGatePassed": "E",
                }
            )
            state_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            checked: list[str] = []
            issues: list[dict[str, object]] = []
            audit_portfolio_workspace_integrity(repo, portfolio, checked, issues)
            after = state_path.read_bytes()

        self.assertEqual(after, before)
        rules = " ".join(str(item["rule"]) for item in issues)
        self.assertIn("orphaned/invisible workspace", rules)
        self.assertIn("EPIC-ORPHAN", rules)
        self.assertIn("epicStatus 'complete'", rules)
        self.assertIn("lastGatePassed 'E'", rules)
        self.assertIn("activeIncrementId 'INC-LEGACY-037'", rules)


if __name__ == "__main__":
    unittest.main()
