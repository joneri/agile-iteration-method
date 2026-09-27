"""Portfolio-aware AIM start transaction regression tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import subprocess
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

    def _append_closed_history(self, repo: Path, count: int) -> None:
        aim = repo / ".aim"
        catalog_path = aim / "ui-portfolio.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        template = json.loads((aim / "state.json").read_text(encoding="utf-8"))
        for index in range(1, count + 1):
            workspace = aim / "workspaces" / f"history-{index:03d}"
            (workspace / "increments").mkdir(parents=True)
            (workspace / "decisions").mkdir()
            (workspace / "reviews").mkdir()
            increment_id = f"DI-{index + 1000}"
            runtime = {
                **template,
                "epicId": f"EPIC-HISTORY-{index:03d}",
                "previousIncrementId": increment_id,
            }
            (workspace / "state.json").write_text(
                json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
            )
            (workspace / "epic.md").write_text(
                f"# EPIC-HISTORY-{index:03d} — Retained outcome\n", encoding="utf-8"
            )
            (workspace / f"increments/{index + 1000}-plan.md").write_text(
                f"# {increment_id} — Retained delivery\n", encoding="utf-8"
            )
            catalog["workspaces"].append(
                {"path": f"workspaces/history-{index:03d}"}
            )
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    def test_fresh_repo_bootstraps_without_root_checkpoint_or_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            plan = plan_start(repo, **self._request())
            self.assertTrue(plan["bootstrapCatalog"])
            self.assertFalse((repo / ".aim").exists())
            request = self._request()
            command = [sys.executable, "-S", str(REPO_ROOT / "scripts/aim_start.py"), "--repo", str(repo)]
            for key, value in request.items():
                command.extend(["--" + key.replace("_", "-"), value])
            result = subprocess.run(command + ["--apply", "--expected-start-sha256", plan["startSha256"]],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["visibleOnBoard"])
            self.assertFalse((repo / ".aim/state.json").exists())
            self.assertEqual(build_board(repo)["health"], "healthy")
            self.assertEqual(len(build_board(repo)["epics"]), 1)

    def _fresh_portfolio(self, repo: Path) -> dict[str, str]:
        from aim_portfolio_run import create_run, activate_next
        (repo / ".aim").mkdir(exist_ok=True)
        (repo / ".aim/portfolio-backlog.json").write_text(json.dumps({
            "backlogVersion": "1.0", "updatedAt": "2026-09-27T10:00:00Z", "items": [{
                "id": "INC-01", "epicId": "EPIC-NEW-001", "epicTitle": "Fresh start",
                "title": "First outcome", "priority": 1, "createdAt": "2026-09-27T10:00:00Z",
            }],
        }))
        create_run(repo, "MANDATE-BOOTSTRAP", "t1", "t1")
        activate_next(repo, "t1", "t2")
        return {**self._request(), "candidate_id": "INC-01"}

    def test_first_portfolio_start_publishes_all_relations_together(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            request = self._fresh_portfolio(repo)
            plan = plan_start(repo, **request)
            result = apply_start(repo, **request, expected_start_sha256=plan["startSha256"])
            self.assertTrue(result["gateAReady"])
            self.assertFalse((repo / ".aim/state.json").exists())
            board = build_board(repo)
            self.assertEqual(board["workspaceDiagnostics"], [])
            self.assertEqual(board["warnings"], [])
            self.assertEqual(board["portfolioRun"]["relationStatus"], "consistent")
            self.assertEqual(board["portfolioRun"]["checkpointStatus"], "gate_a_pending")
            state = json.loads((repo / ".aim/portfolio/EPIC-NEW-001/state.json").read_text())
            self.assertEqual(state["plannedIncrementId"], "DI-002")
            self.assertIsNone(state["activeIncrementId"])
            self.assertEqual(state["portfolioCandidateId"], "INC-01")
            self.assertEqual(board["portfolioRun"]["decisionAuthority"], "none")

    def test_bootstrap_failure_restores_absence_and_existing_roadmap(self) -> None:
        for fault in ("after_staging", "after_workspace_publish", "after_catalog_publish",
                      "after_backlog_publish", "after_run_publish", "after_ready_publish"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary)
                request = self._fresh_portfolio(repo)
                before = {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
                plan = plan_start(repo, **request)
                with self.assertRaisesRegex(AimStartError, fault):
                    apply_start(repo, **request, expected_start_sha256=plan["startSha256"], fault_at=fault)
                after = {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
                self.assertEqual(after, before)
                self.assertFalse((repo / ".aim/portfolio").exists())
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            with self.assertRaises(AimStartError):
                apply_start(repo, **self._request(), fault_at="after_catalog_publish")
            self.assertFalse((repo / ".aim").exists())

    def test_schema_error_is_rejected_before_bootstrap_writes(self) -> None:
        import aim_start
        original = aim_start._workspace_payloads
        def invalid(plan, title, platform):
            payloads = original(plan, title, platform)
            state = json.loads(payloads["state.json"])
            state["plannedIncrementId"] = None
            payloads["state.json"] = json.dumps(state).encode()
            return payloads
        with tempfile.TemporaryDirectory() as temporary, patch.object(aim_start, "_workspace_payloads", side_effect=invalid):
            repo = Path(temporary)
            with self.assertRaisesRegex(AimStartError, "Generated start state is invalid"):
                apply_start(repo, **self._request())
            self.assertFalse((repo / ".aim").exists())

    def test_bootstrap_recovers_index_without_rewriting_existing_root_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            (repo / ".aim/ui-portfolio.json").unlink()
            before = (repo / ".aim/state.json").read_bytes()
            plan = plan_start(repo, **self._request())
            self.assertFalse((repo / ".aim/ui-portfolio.json").exists())
            apply_start(repo, **self._request(), expected_start_sha256=plan["startSha256"])
            self.assertEqual((repo / ".aim/state.json").read_bytes(), before)
            catalog = json.loads((repo / ".aim/ui-portfolio.json").read_text())
            self.assertEqual(catalog["workspaces"], [{"path": "."}, {"path": "portfolio/EPIC-NEW-001"}])

    def test_recovery_preserves_history_and_is_idempotent(self):
        from aim_recovery import ensure_catalog
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._append_closed_history(repo, 2)
            catalog = repo / ".aim/ui-portfolio.json"
            expected = json.loads(catalog.read_text())
            catalog.unlink()
            before = {p: p.read_bytes() for p in (repo / ".aim").rglob("*") if p.is_file()}
            board = build_board(repo)
            self.assertEqual(len(board["epics"]), 3)
            self.assertFalse(catalog.exists(), "UI must remain read-only")
            self.assertEqual(ensure_catalog(repo)["result"], "recovered")
            self.assertEqual(json.loads(catalog.read_text()), expected)
            self.assertEqual(ensure_catalog(repo)["result"], "unchanged")
            self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_recovery_blocks_ambiguous_or_unsafe_work_without_writes(self):
        from aim_recovery import ensure_catalog
        for case in ("duplicate", "missing", "symlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                repo = self._repo(Path(temporary))
                self._append_closed_history(repo, 1)
                catalog = repo / ".aim/ui-portfolio.json"
                catalog.unlink()
                child = repo / ".aim/workspaces/history-001/state.json"
                if case == "duplicate":
                    child.write_bytes((repo / ".aim/state.json").read_bytes())
                elif case == "missing":
                    child.unlink()
                else:
                    child.unlink()
                    child.symlink_to(repo / ".aim/state.json")
                with self.assertRaises((AimStartError, OSError)):
                    ensure_catalog(repo)
                self.assertFalse(catalog.exists())

    def test_packaged_portfolio_start_recovers_history_without_repair_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.unlink()
            before = {p: p.read_bytes() for p in (repo / ".aim").rglob("*") if p.is_file()}
            request = self._fresh_portfolio(repo)
            command = [sys.executable, "-S",
                       str(REPO_ROOT / "skills/agile-iteration-method/scripts/aim_start.py"),
                       "--repo", str(repo)]
            for key, value in request.items():
                command.extend(["--" + key.replace("_", "-"), value])
            preview = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            plan = json.loads(preview.stdout)
            self.assertFalse(catalog.exists())
            result = subprocess.run(command + ["--apply", "--expected-start-sha256", plan["startSha256"]],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["visibleOnBoard"])
            board = build_board(repo)
            self.assertEqual(board["portfolioRun"]["relationStatus"], "consistent")
            self.assertEqual({p: p.read_bytes() for p in before}, before)
            self.assertEqual(len(json.loads(catalog.read_text())["workspaces"]), 2)

    def test_recovery_cli_and_concurrent_catalog_preserve_existing_files(self):
        from aim_recovery import ensure_catalog
        import aim_recovery
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            original = catalog.read_bytes()
            catalog.unlink()
            real_link = aim_recovery.os.link
            def publish_race(source, target):
                catalog.write_bytes(original)
                real_link(source, target)
            with patch.object(aim_recovery.os, "link", side_effect=publish_race):
                with self.assertRaises(FileExistsError):
                    ensure_catalog(repo)
            self.assertEqual(catalog.read_bytes(), original)
            self.assertFalse(list((repo / ".aim").glob(".catalog-recovery-*")))
            catalog.unlink()
            result = subprocess.run([sys.executable, "-S", str(REPO_ROOT / "scripts/aim_recovery.py"),
                                     "--repo", str(repo)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["result"], "recovered")
            catalog.write_text("{broken")
            before = catalog.read_bytes()
            with self.assertRaises(AimStartError):
                ensure_catalog(repo)
            self.assertEqual(catalog.read_bytes(), before)

    def test_recovered_work_counts_for_capacity(self):
        from aim_activation import activation_preflight
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            (repo / ".aim/ui-portfolio.json").unlink()
            state_path = repo / ".aim/state.json"
            state = json.loads(state_path.read_text())
            state.update(epicStatus="increment_in_progress", currentRole="Dev",
                         activeIncrementId="DI-001", lastGatePassed="Gate B")
            state_path.write_text(json.dumps(state))
            (repo / ".aim/portfolio-control.json").write_text(json.dumps({
                "controlVersion": "1.0", "maxActiveEpics": 1,
                "updatedAt": "2026-08-23T10:00:00Z"}))
            result = activation_preflight(repo, epic_id="EPIC-NEW-001")
            self.assertFalse(result["allowed"])
            self.assertEqual(result["code"], "capacity_full")

    def test_recovery_binds_changes_and_rolls_back_new_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.unlink()
            plan = plan_start(repo, **self._request())
            state = repo / ".aim/state.json"
            value = json.loads(state.read_text())
            value["updatedAt"] = "2026-08-23T10:01:00Z"
            state.write_text(json.dumps(value))
            with self.assertRaisesRegex(AimStartError, "changed"):
                apply_start(repo, **self._request(), expected_start_sha256=plan["startSha256"])
            with self.assertRaises(AimStartError):
                apply_start(repo, **self._request(), fault_at="after_catalog_publish")
            self.assertFalse(catalog.exists())
            self.assertEqual(json.loads(state.read_text()), value)
            self.assertFalse((repo / ".aim/portfolio/EPIC-NEW-001").exists())

    def test_changed_mandate_or_new_catalog_during_bootstrap_preserves_inputs(self) -> None:
        for change in ("mandate", "catalog"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary)
                request = self._fresh_portfolio(repo)
                plan = plan_start(repo, **request)
                def mutate(stage):
                    if stage != "after_staging":
                        return
                    if change == "catalog":
                        (repo / ".aim/ui-portfolio.json").write_text("{}")
                    else:
                        path = repo / ".aim/portfolio-run.json"
                        run = json.loads(path.read_text())
                        run["status"] = "paused"
                        run["pauseReason"] = "User paused"
                        path.write_text(json.dumps(run))
                with self.assertRaises(AimStartError):
                    apply_start(repo, **request, expected_start_sha256=plan["startSha256"], fault_hook=mutate)
                self.assertFalse((repo / ".aim/portfolio").exists())
                self.assertFalse((repo / ".aim/state.json").exists())
                if change == "catalog":
                    self.assertEqual((repo / ".aim/ui-portfolio.json").read_text(), "{}")
                else:
                    self.assertEqual(json.loads((repo / ".aim/portfolio-run.json").read_text())["status"], "paused")

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

    def test_invalid_traversal_and_symlink_catalogs_fail_closed(self) -> None:
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


    def test_seventeenth_and_large_history_starts_are_transactionally_admitted(self) -> None:
        for retained_count in (16, 100):
            with self.subTest(retained_count=retained_count), tempfile.TemporaryDirectory() as temporary:
                repo = self._repo(Path(temporary))
                self._append_closed_history(repo, retained_count - 1)
                plan = plan_start(repo, **self._request())

                result = apply_start(
                    repo,
                    **self._request(),
                    expected_catalog_sha256=plan["catalogSha256"],
                )

                catalog = json.loads(
                    (repo / ".aim/ui-portfolio.json").read_text(encoding="utf-8")
                )
                board = build_board(repo)
                self.assertEqual(len(catalog["workspaces"]), retained_count + 1)
                self.assertEqual(board["source"]["retainedWorkspaceCount"], retained_count + 1)
                self.assertTrue(
                    any(item["id"] == "EPIC-HISTORY-001" for item in board["epics"])
                )
                self.assertTrue(result["visibleOnBoard"])
                self.assertTrue(result["gateAReady"])

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
