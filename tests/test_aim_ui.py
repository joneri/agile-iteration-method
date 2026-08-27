"""AIM UI read-model and read-only transport tests."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_ui import (  # noqa: E402
    AimUiError,
    AimUiServer,
    STATE_TO_COLUMN,
    build_board,
    resolve_evidence_path,
)
from aim_portfolio_run import (  # noqa: E402
    activate_next,
    checkpoint,
    complete_active,
    create_run,
    snapshot_hash,
)
from aim_validator.schema_subset import unsupported_keywords, validate  # noqa: E402


def state(status: str = "increment_in_progress") -> dict[str, object]:
    return {
        "stateSchemaVersion": "1.0",
        "aimVersion": "2.0",
        "mode": "Auto",
        "costProfile": "Standard",
        "epicId": "EPIC-TEST-001",
        "epicStatus": status,
        "activeIncrementId": "DI-001",
        "currentRole": "Dev",
        "lastGatePassed": "Gate B",
        "platform": "test",
        "parallelSupport": {
            "available": True,
            "enabled": True,
            "policy": "bounded",
        },
        "commitMode": "optional",
        "updatedAt": "2026-08-21T12:00:00Z",
    }


class AimUiTests(unittest.TestCase):
    def _repo(self, root: Path, runtime_state: dict[str, object] | None = None) -> Path:
        aim = root / ".aim"
        (aim / "increments").mkdir(parents=True)
        (aim / "decisions").mkdir()
        (aim / "reviews").mkdir()
        (aim / "state.json").write_text(
            json.dumps(runtime_state or state(), indent=2) + "\n", encoding="utf-8"
        )
        (aim / "epic.md").write_text(
            "# EPIC-TEST-001 — Make delivery visible\n", encoding="utf-8"
        )
        (aim / "increments/001-wip.md").write_text(
            "# DI-001 — See the active work\n\nEpic: EPIC-TEST-001\n",
            encoding="utf-8",
        )
        return root

    def _additional_workspace(
        self,
        repo: Path,
        name: str = "other",
        *,
        epic_id: str = "EPIC-TEST-002",
        increment_id: str = "DI-002",
        status: str = "review_in_progress",
    ) -> Path:
        workspace = repo / ".aim/workspaces" / name
        (workspace / "increments").mkdir(parents=True)
        (workspace / "decisions").mkdir()
        (workspace / "reviews").mkdir()
        runtime = state(status)
        runtime.update(
            {
                "epicId": epic_id,
                "activeIncrementId": increment_id,
                "currentRole": "Reviewer" if status == "review_in_progress" else "Dev",
                "lastGatePassed": "Gate C" if status == "review_in_progress" else "Gate B",
            }
        )
        (workspace / "state.json").write_text(
            json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
        )
        (workspace / "epic.md").write_text(
            f"# {epic_id} — Ship the companion flow\n", encoding="utf-8"
        )
        number = increment_id.removeprefix("DI-")
        (workspace / f"increments/{number}-wip.md").write_text(
            f"# {increment_id} — Validate the other stream\n\nEpic: {epic_id}\n",
            encoding="utf-8",
        )
        return workspace

    def _portfolio(self, repo: Path, *paths: str) -> None:
        (repo / ".aim/ui-portfolio.json").write_text(
            json.dumps(
                {
                    "portfolioVersion": "1.0",
                    "workspaces": [{"path": path} for path in paths],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _backlog(self, repo: Path, items: list[dict[str, object]]) -> None:
        (repo / ".aim/portfolio-backlog.json").write_text(
            json.dumps(
                {
                    "backlogVersion": "1.0",
                    "updatedAt": "2026-08-21T13:00:00Z",
                    "items": items,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _control(
        self, repo: Path, *, maximum: int, focused_epic_id: str | None = None
    ) -> None:
        value: dict[str, object] = {
            "controlVersion": "1.0",
            "maxActiveEpics": maximum,
            "updatedAt": "2026-08-21T13:02:00Z",
        }
        if focused_epic_id:
            value["focusedEpicId"] = focused_epic_id
        (repo / ".aim/portfolio-control.json").write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def test_state_mapping_covers_every_canonical_runtime_state(self) -> None:
        self.assertEqual(
            set(STATE_TO_COLUMN),
            {
                "epic_initialized",
                "gate_a_pending",
                "gate_b_pending",
                "increment_in_progress",
                "review_in_progress",
                "tdo_validation_in_progress",
                "po_approval_pending",
                "done_increment_accepted",
                "epic_paused",
                "blocked",
                "epic_complete",
            },
        )
        self.assertEqual(STATE_TO_COLUMN["gate_b_pending"], "backlog")
        self.assertEqual(STATE_TO_COLUMN["increment_in_progress"], "work_in_progress")
        self.assertEqual(STATE_TO_COLUMN["review_in_progress"], "in_review")
        self.assertEqual(STATE_TO_COLUMN["po_approval_pending"], "ready_for_release")
        self.assertEqual(STATE_TO_COLUMN["epic_complete"], "done")

    def test_portfolio_schema_is_supported_and_accepts_the_documented_shape(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/aim-ui-portfolio.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema["$id"],
            "https://joneri.github.io/agile-iteration-method/schemas/aim-ui-portfolio.schema.json",
        )
        self.assertEqual(unsupported_keywords(schema), [])
        self.assertEqual(
            validate(
                {
                    "portfolioVersion": "1.0",
                    "workspaces": [{"path": "."}, {"path": "workspaces/other"}],
                },
                schema,
            ),
            [],
        )
        large_history = {
            "portfolioVersion": "1.0",
            "workspaces": [{"path": f"workspaces/{index}"} for index in range(101)],
        }
        self.assertEqual(validate(large_history, schema), [])

    def test_portfolio_catalog_payload_and_symlink_remain_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            catalog.write_text(" " * 1_000_001, encoding="utf-8")

            oversized = build_board(repo)

            self.assertEqual(oversized["epics"], [])
            self.assertTrue(
                any("larger than 1000000 bytes" in item for item in oversized["warnings"])
            )

        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            catalog = repo / ".aim/ui-portfolio.json"
            target = repo / "catalog.json"
            target.write_text(
                json.dumps(
                    {"portfolioVersion": "1.0", "workspaces": [{"path": "."}]}
                )
                + "\n",
                encoding="utf-8",
            )
            catalog.symlink_to(target)

            linked = build_board(repo)

            self.assertEqual(linked["epics"], [])
            self.assertTrue(
                any("must not be a symbolic link" in item for item in linked["warnings"])
            )

    def test_backlog_schema_is_supported_and_accepts_planning_only_shape(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/aim-ui-backlog.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(unsupported_keywords(schema), [])
        candidate = {
            "backlogVersion": "1.0",
            "updatedAt": "2026-08-21T13:00:00Z",
            "items": [
                {
                    "id": "INC-UI-001",
                    "epicId": "EPIC-UI",
                    "epicTitle": "AIM UI",
                    "title": "Control concurrency",
                    "summary": "Choose how many Epics may run.",
                    "priority": 1,
                    "createdAt": "2026-08-21T13:00:00Z",
                    "runtimeIncrementId": "DI-010",
                }
            ],
        }
        self.assertEqual(validate(candidate, schema), [])
        candidate["items"][0]["id"] = "DI-010"
        self.assertTrue(any("must match pattern" in issue.message for issue in validate(candidate, schema)))
        candidate["items"][0]["id"] = "INC-" + "X" * 100
        self.assertTrue(any("at most 80" in issue.message for issue in validate(candidate, schema)))

    def test_portfolio_control_schema_is_supported(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/aim-portfolio-control.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(unsupported_keywords(schema), [])
        self.assertEqual(
            validate(
                {
                    "controlVersion": "1.0",
                    "maxActiveEpics": 2,
                    "focusedEpicId": "EPIC-TEST-001",
                    "updatedAt": "2026-08-21T13:02:00Z",
                },
                schema,
            ),
            [],
        )

    def test_portfolio_auto_run_is_projected_with_mandate_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-AUTO-001",
                        "epicId": "EPIC-AUTO",
                        "epicTitle": "Auto Portfolio",
                        "title": "Run the first card",
                        "priority": 1,
                        "createdAt": "2026-08-21T13:00:00Z",
                    },
                    {
                        "id": "INC-AUTO-002",
                        "epicId": "EPIC-AUTO-NEXT",
                        "epicTitle": "Auto Portfolio Next",
                        "title": "Run the second card",
                        "priority": 2,
                        "createdAt": "2026-08-21T13:01:00Z",
                    },
                ],
            )
            run = create_run(
                repo,
                "MANDATE-UI-001",
                "2026-08-21T13:02:00Z",
                "2026-08-21T13:02:00Z",
            )
            activate_next(repo, run["updatedAt"], "2026-08-21T13:03:00Z")
            board = build_board(repo)

        self.assertTrue(board["portfolioRun"]["valid"])
        self.assertEqual(board["portfolioRun"]["activeCandidateId"], "INC-AUTO-001")
        self.assertEqual(board["portfolioRun"]["decisionAuthority"], "portfolio_mandate")
        candidates = {
            item["id"]: item
            for epic in board["epics"]
            for item in epic["planning"]["candidates"]
        }
        self.assertEqual(
            candidates["INC-AUTO-001"]["portfolioState"], "activation_pending"
        )
        self.assertEqual(
            candidates["INC-AUTO-001"]["decisionAuthority"], "portfolio_mandate"
        )
        self.assertEqual(candidates["INC-AUTO-002"]["portfolioState"], "queued")

    def test_portfolio_handoff_preserves_done_and_projects_activation_atomically(self) -> None:
        closed = state("epic_complete")
        closed.update(
            {
                "epicId": "EPIC-FIRST",
                "activeIncrementId": None,
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "portfolioCandidateId": "INC-FIRST",
                "previousIncrementId": "DI-001",
                "previousIncrementStatus": "accepted",
                "gateEAcceptance": ".aim/decisions/001-gate-e.md",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), closed)
            (repo / ".aim/epic.md").write_text(
                "# EPIC-FIRST — Preserve the first outcome\n", encoding="utf-8"
            )
            (repo / ".aim/increments/001-wip.md").write_text(
                "# DI-001 — Accepted first outcome\n\nEpic: EPIC-FIRST\n",
                encoding="utf-8",
            )
            (repo / ".aim/decisions/001-gate-e.md").write_text(
                "# Gate E\n\nIncrement: DI-001\n\nStatus: Accepted\n\n"
                "Accepted at: 2026-08-23T14:00:00Z\n",
                encoding="utf-8",
            )
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-FIRST",
                        "epicId": "EPIC-FIRST",
                        "epicTitle": "Preserve the first outcome",
                        "title": "Accepted first outcome",
                        "priority": 1,
                        "createdAt": "2026-08-23T13:00:00Z",
                    },
                    {
                        "id": "INC-SECOND",
                        "epicId": "EPIC-SECOND",
                        "epicTitle": "Activate the second outcome",
                        "title": "Second runtime",
                        "priority": 2,
                        "createdAt": "2026-08-23T13:01:00Z",
                    },
                ],
            )
            run = create_run(repo, "MANDATE-HANDOFF", "t1", "t1")
            self._portfolio(repo, ".")
            run = activate_next(repo, run["updatedAt"], "t2")
            backlog_path = repo / ".aim/portfolio-backlog.json"
            backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
            backlog["items"][0]["runtimeIncrementId"] = "DI-001"
            backlog_path.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8")
            run = checkpoint(
                repo, run["updatedAt"], "t3", "INC-FIRST", "epic_complete",
                "Epic closure", "portfolio_mandate",
            )
            run = complete_active(repo, run["updatedAt"], "t4", "INC-FIRST")

            with patch("aim_ui.utc_now", return_value="2026-08-23T15:00:00Z"):
                between = build_board(repo)
            self.assertEqual(between["portfolioRun"]["transitionState"], "next_activation_pending")
            self.assertEqual(between["portfolioRun"]["relationStatus"], "recoverable")
            self.assertEqual(between["history"]["closedIncrements"][0]["id"], "DI-001")
            self.assertEqual(between["history"]["recentDeliveries"][0]["id"], "DI-001")
            self.assertFalse(
                next(epic for epic in between["epics"] if epic["id"] == "EPIC-FIRST")
                ["increments"][0]["visibleOnBoard"]
            )

            run = activate_next(repo, run["updatedAt"], "t5")
            with patch("aim_ui.utc_now", return_value="2026-08-23T15:01:00Z"):
                pending = build_board(repo)
                reloaded = build_board(repo)
            self.assertEqual(pending, reloaded)
            self.assertTrue(pending["portfolioRun"]["valid"])
            self.assertEqual(pending["portfolioRun"]["transitionState"], "activation_pending")
            second = next(epic for epic in pending["epics"] if epic["id"] == "EPIC-SECOND")
            self.assertEqual(second["lifecycle"], "planned")
            self.assertEqual(second["increments"], [])
            self.assertEqual(second["planning"]["candidates"][0]["portfolioState"], "activation_pending")
            self.assertFalse(second["actions"][0]["enabled"])
            self.assertEqual(pending["history"]["closedIncrements"][0]["id"], "DI-001")

            workspace = self._additional_workspace(
                repo,
                "second",
                epic_id="EPIC-SECOND",
                increment_id="DI-002",
                status="gate_a_pending",
            )
            runtime = json.loads((workspace / "state.json").read_text(encoding="utf-8"))
            runtime.update(
                {
                    "portfolioCandidateId": "INC-SECOND",
                    "currentRole": "PO",
                    "lastGatePassed": None,
                    "updatedAt": "t6",
                }
            )
            (workspace / "state.json").write_text(
                json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
            )
            self._portfolio(repo, ".", "workspaces/second")
            partial = build_board(repo)
            self.assertFalse(partial["portfolioRun"]["valid"])
            self.assertEqual(partial["portfolioRun"]["relationStatus"], "contradictory")
            self.assertIn("runtimeIncrementId=missing", partial["portfolioRun"]["issue"])
            self.assertEqual(partial["history"]["closedIncrements"][0]["id"], "DI-001")

            backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
            backlog["items"][1]["runtimeIncrementId"] = "DI-002"
            backlog_path.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8")
            checkpoint(repo, "t5", "t6", "INC-SECOND", "gate_a_pending", "Gate A", "portfolio_mandate")
            activated = build_board(repo)
            self.assertTrue(activated["portfolioRun"]["valid"])
            self.assertEqual(activated["portfolioRun"]["relationStatus"], "consistent")
            self.assertEqual(activated["history"]["closedIncrements"][0]["id"], "DI-001")
            second = next(epic for epic in activated["epics"] if epic["id"] == "EPIC-SECOND")
            self.assertEqual(second["activeIncrementId"], "DI-002")

    def test_portfolio_checkpoint_without_required_runtime_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(
                repo,
                [{
                    "id": "INC-MISSING",
                    "epicId": "EPIC-MISSING",
                    "epicTitle": "Missing runtime",
                    "title": "Must not look active",
                    "priority": 1,
                    "createdAt": "2026-08-23T13:00:00Z",
                }],
            )
            run = create_run(repo, "MANDATE-MISSING", "t1", "t1")
            run = activate_next(repo, run["updatedAt"], "t2")
            checkpoint(
                repo, run["updatedAt"], "t3", "INC-MISSING",
                "epic_definition_in_progress", "Gate A", "portfolio_mandate",
            )
            board = build_board(repo)

        self.assertFalse(board["portfolioRun"]["valid"])
        self.assertEqual(board["portfolioRun"]["relationStatus"], "contradictory")
        self.assertTrue(any("INC-MISSING" in warning for warning in board["warnings"]))
        missing = next(epic for epic in board["epics"] if epic["id"] == "EPIC-MISSING")
        self.assertFalse(missing["actions"][0]["enabled"])
        self.assertIn("contradictory", missing["actions"][0]["reason"])

    def test_planned_candidates_project_epics_without_increment_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-DATA-001",
                        "epicId": "EPIC-DATA",
                        "epicTitle": "AIM DATA",
                        "title": "Capture delivery baselines",
                        "priority": 2,
                        "createdAt": "2026-08-21T13:01:00Z",
                    },
                    {
                        "id": "INC-UI-001",
                        "epicId": "EPIC-UI",
                        "epicTitle": "AIM UI",
                        "title": "Control concurrent Epics",
                        "priority": 1,
                        "createdAt": "2026-08-21T13:00:00Z",
                    },
                ],
            )
            board = build_board(repo)

        planned = [epic for epic in board["epics"] if epic["lifecycle"] == "planned"]
        self.assertEqual([epic["id"] for epic in planned], ["EPIC-UI", "EPIC-DATA"])
        self.assertTrue(all(epic["increments"] == [] for epic in planned))
        self.assertEqual(
            [epic["planning"]["nextCandidateId"] for epic in planned],
            ["INC-UI-001", "INC-DATA-001"],
        )
        self.assertTrue(all(epic["actions"][0]["kind"] == "activate" for epic in planned))
        self.assertTrue(all(epic["actions"][0]["label"] == "Start Epic" for epic in planned))
        self.assertTrue(
            all(epic["actions"][0]["envelope"]["action"] == "activate" for epic in planned)
        )
        self.assertTrue(all(epic["actions"][0]["enabled"] for epic in planned))
        self.assertTrue(board["roadmap"]["configured"])
        self.assertEqual(board["roadmap"]["eligibleCount"], 2)
        self.assertEqual(
            [item["candidateId"] for item in board["roadmap"]["snapshot"]],
            ["INC-UI-001", "INC-DATA-001"],
        )
        self.assertEqual(
            board["roadmap"]["auto"]["command"],
            '/aim start "PORTFOLIO" mode:auto',
        )
        self.assertEqual(
            board["roadmap"]["snapshotSha256"],
            snapshot_hash(board["roadmap"]["snapshot"]),
        )
        self.assertFalse(board["roadmap"]["strict"]["supported"])
        self.assertIn("Later Roadmap additions are excluded", board["roadmap"]["snapshotBoundary"])

    def test_full_capacity_disables_planned_activation_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._control(repo, maximum=1, focused_epic_id="EPIC-TEST-001")
            self._backlog(
                repo,
                [{
                    "id": "INC-NEXT-001",
                    "epicId": "EPIC-NEXT",
                    "epicTitle": "Next Epic",
                    "title": "Start next work",
                    "priority": 1,
                    "createdAt": "2026-08-21T13:00:00Z",
                }],
            )
            board = build_board(repo)

        planned = next(epic for epic in board["epics"] if epic["id"] == "EPIC-NEXT")
        action = planned["actions"][0]
        self.assertEqual(action["label"], "Start Epic")
        self.assertFalse(action["enabled"])
        self.assertEqual(action["reason"], "Portfolio capacity is full.")
        self.assertNotIn("href", action)

    def test_gate_b_projects_approve_and_change_without_write_transport(self) -> None:
        runtime = state("gate_b_pending")
        runtime.update({"currentRole": "TDO", "lastGatePassed": "Gate A"})
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary), runtime))

        actions = board["epics"][0]["increments"][0]["actions"]
        self.assertEqual([item["kind"] for item in actions], ["approve", "change"])
        self.assertIn("codex://new?", actions[0]["href"])
        self.assertTrue(actions[1]["requiresInput"])
        self.assertNotIn("href", actions[1])
        self.assertFalse(board["handoff"]["autoSend"])
        self.assertIn("read authorityStatePath exactly relative to the repository root", board["handoff"]["promptPreamble"])
        self.assertTrue(actions[0]["prompt"].startswith(board["handoff"]["promptPreamble"]))
        self.assertEqual(actions[0]["envelope"]["actionVersion"], "1.2")
        self.assertEqual(actions[0]["envelope"]["authorityStatePath"], ".aim/state.json")
        self.assertNotIn("workspace", actions[0]["envelope"])
        self.assertEqual(actions[0]["envelope"]["expectedLastGatePassed"], "Gate A")

        styles = (REPO_ROOT / "aim-ui/styles.css").read_text(encoding="utf-8")
        script = (REPO_ROOT / "aim-ui/app.js").read_text(encoding="utf-8")
        self.assertIn(".change-field[hidden] { display: none; }", styles)
        self.assertIn("state.board?.handoff?.promptPreamble", script)
        self.assertNotIn("re-read current authoritative AIM state", script)

    def test_gate_card_moves_before_explicit_decision_controls_are_published(self) -> None:
        runtime = state("po_approval_pending")
        runtime.update(
            {
                "currentRole": "PO",
                "lastGatePassed": "Gate D",
                "uiDecision": {
                    "visibility": "preparing",
                    "gate": "Gate E",
                    "targetId": "DI-001",
                },
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            preparing = build_board(repo)
            runtime["uiDecision"]["visibility"] = "ready"
            runtime["updatedAt"] = "2026-08-21T12:01:00Z"
            (repo / ".aim/state.json").write_text(
                json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
            )
            ready = build_board(repo)

        preparing_increment = preparing["epics"][0]["increments"][0]
        self.assertEqual(preparing_increment["column"], "ready_for_release")
        self.assertEqual(preparing_increment["actions"], [])
        self.assertIn("finishing the decision handoff", preparing_increment["attention"])
        self.assertEqual(preparing["health"], "healthy")

        ready_increment = ready["epics"][0]["increments"][0]
        self.assertEqual(ready_increment["column"], "ready_for_release")
        self.assertEqual(
            [item["kind"] for item in ready_increment["actions"]],
            ["approve", "change"],
        )
        self.assertEqual(
            ready_increment["actions"][0]["envelope"]["expectedUpdatedAt"],
            "2026-08-21T12:01:00Z",
        )

    def test_mismatched_decision_readiness_fails_closed(self) -> None:
        runtime = state("po_approval_pending")
        runtime.update(
            {
                "currentRole": "PO",
                "lastGatePassed": "Gate D",
                "uiDecision": {
                    "visibility": "ready",
                    "gate": "Gate E",
                    "targetId": "DI-999",
                },
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary), runtime))

        self.assertEqual(board["epics"][0]["increments"][0]["actions"], [])
        self.assertEqual(board["health"], "partial")
        self.assertTrue(any("uiDecision does not match" in item for item in board["warnings"]))

    def test_delivery_board_polling_is_quiet_and_motion_is_meaningful(self) -> None:
        script = (REPO_ROOT / "aim-ui/app.js").read_text(encoding="utf-8")
        styles = (REPO_ROOT / "aim-ui/styles.css").read_text(encoding="utf-8")
        markup = (REPO_ROOT / "aim-ui/index.html").read_text(encoding="utf-8")

        for marker in (
            "semanticBoardSignature",
            "generatedAt: _generatedAt",
            "data-card-key",
            "data-epic-card",
            "data-epic-row",
            "duplicateCards.forEach((card) => card.remove())",
            'card.closest(".lane-cell")?.dataset.column',
            "epicVisibleOnDeliveryBoard",
            "epicsForView(board)",
            "renderFilters(board, viewEpics)",
            "animateCardHandoffs",
            'prefers-reduced-motion: reduce',
            "kanban.scrollLeft = scrollLeft",
            'return epic.lifecycle !== "closed";',
            "renderRecentDeliveries(board)",
            "board.history?.recentDeliveries",
            "renderWorkspaceIntegrity(board)",
            "board.workspaceDiagnostics || []",
        ):
            self.assertIn(marker, script)
        self.assertIn('class="card-control" hidden', markup)
        self.assertLess(markup.index('class="card-actions"'), markup.index('class="action-unavailable"'))
        self.assertIn(".card-control[hidden] { display: none; }", styles)
        self.assertIn(".card-action:focus-visible", styles)
        self.assertIn(".recent-delivery-card:focus-visible", styles)
        self.assertIn('id="recent-deliveries" aria-labelledby="recent-deliveries-title"', markup)
        self.assertIn('id="delivery-dialog" aria-labelledby="delivery-dialog-title"', markup)
        self.assertIn('id="workspace-integrity" aria-labelledby=', markup)
        self.assertIn(".workspace-integrity[hidden] { display: none; }", styles)
        self.assertIn('id="copy-recovery-action"', markup)
        self.assertIn('id="roadmap-panel"', markup)
        self.assertIn("function renderRoadmap", script)
        self.assertIn("review the intent in aim chat", script.lower())
        self.assertIn('id="follow-up-intent" tabindex="0"', markup)
        follow_up = script[script.index("function followUpPrompt"):script.index("function showCompleteHistory")]
        self.assertIn("do not reopen or reuse its identity", follow_up)
        self.assertIn("untrusted repository data", follow_up)
        self.assertIn("Source accepted Increment", follow_up)
        self.assertNotIn("AIM_ACTION_ENVELOPE", follow_up)
        self.assertIn('button.setAttribute("aria-describedby", reasonId)', script)
        self.assertNotIn("ticket-in", styles)
        self.assertNotIn("margin: 14px -15px -15px", styles)

    def test_contradictory_gate_checkpoint_hides_actions_and_warns(self) -> None:
        runtime = state("po_approval_pending")
        runtime.update({"currentRole": "PO", "lastGatePassed": "Gate B"})
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary), runtime))

        increment = board["epics"][0]["increments"][0]
        self.assertEqual(increment["actions"], [])
        self.assertEqual(board["health"], "partial")
        self.assertTrue(any("conflicts with lastGatePassed" in item for item in board["warnings"]))

    def test_delivery_flow_is_default_and_secondary_views_use_tabs(self) -> None:
        markup = (REPO_ROOT / "aim-ui/index.html").read_text(encoding="utf-8")
        script = (REPO_ROOT / "aim-ui/app.js").read_text(encoding="utf-8")
        styles = (REPO_ROOT / "aim-ui/styles.css").read_text(encoding="utf-8")

        self.assertIn('data-view="board" aria-pressed="true">Delivery flow', markup)
        self.assertIn('data-view="portfolio" aria-pressed="false">Portfolio', markup)
        self.assertIn('data-view="data" aria-pressed="false">AIM DATA', markup)
        self.assertIn('data-view="people" aria-pressed="false">People &amp; agents', markup)
        self.assertIn('id="epic-rail" hidden', markup)
        self.assertIn('id="data-panel" aria-labelledby="data-title" hidden', markup)
        self.assertIn('id="people-panel" aria-labelledby="people-title" hidden', markup)
        self.assertIn('view: "board"', script)
        self.assertIn("renderData(board)", script)
        self.assertNotIn("board-view-button", script)
        self.assertNotIn("closed-view-button", script)
        self.assertIn("[hidden] { display: none !important; }", styles)

    def test_gate_a_uses_candidate_identity_for_approve_and_change(self) -> None:
        runtime = state("gate_a_pending")
        runtime.update(
            {"activeIncrementId": None, "currentRole": "PO", "lastGatePassed": None}
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            self._backlog(
                repo,
                [{
                    "id": "INC-TEST-001",
                    "epicId": "EPIC-TEST-001",
                    "epicTitle": "Make delivery visible",
                    "title": "Approve the direction",
                    "priority": 1,
                    "createdAt": "2026-08-21T13:00:00Z",
                }],
            )
            board = build_board(repo)

        candidate = board["epics"][0]["planning"]["candidates"][0]
        actions = board["epics"][0]["actions"]
        self.assertEqual([item["kind"] for item in actions], ["approve", "change"])
        self.assertEqual(actions[0]["envelope"]["candidateId"], "INC-TEST-001")
        self.assertEqual(actions[0]["envelope"]["gate"], "Gate A")
        self.assertEqual(
            actions[0]["envelope"]["authorityStatePath"], ".aim/state.json"
        )
        self.assertIsNone(actions[0]["envelope"]["expectedLastGatePassed"])
        self.assertNotIn("incrementId", actions[0]["envelope"])

    def test_runtime_evidence_suppresses_activated_backlog_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-UI-001",
                        "epicId": "EPIC-TEST-001",
                        "epicTitle": "Make delivery visible",
                        "title": "See the active work",
                        "priority": 1,
                        "createdAt": "2026-08-21T13:00:00Z",
                        "runtimeIncrementId": "DI-001",
                    }
                ],
            )
            board = build_board(repo)

        items = board["epics"][0]["increments"]
        self.assertEqual([item["id"] for item in items], ["DI-001"])
        self.assertEqual(board["health"], "healthy")
        self.assertEqual(board["warnings"], [])

    def test_unresolved_runtime_history_never_becomes_planned_or_activatable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-ARCHIVED-001",
                        "epicId": "EPIC-ARCHIVED",
                        "epicTitle": "Preserved completed work",
                        "title": "Must remain history",
                        "priority": 1,
                        "createdAt": "2026-08-21T13:00:00Z",
                        "runtimeIncrementId": "DI-088",
                    },
                    {
                        "id": "INC-MISMATCHED-001",
                        "epicId": "EPIC-TEST-001",
                        "epicTitle": "Make delivery visible",
                        "title": "Must not attach to the wrong runtime",
                        "priority": 2,
                        "createdAt": "2026-08-21T13:01:00Z",
                        "runtimeIncrementId": "DI-089",
                    },
                    {
                        "id": "INC-PLANNED-001",
                        "epicId": "EPIC-PLANNED",
                        "epicTitle": "Genuinely planned work",
                        "title": "May be activated",
                        "priority": 3,
                        "createdAt": "2026-08-21T13:02:00Z",
                    },
                ],
            )
            board = build_board(repo)

        epic_ids = {epic["id"] for epic in board["epics"]}
        self.assertNotIn("EPIC-ARCHIVED", epic_ids)
        self.assertNotIn(
            "INC-MISMATCHED-001",
            [
                candidate["id"]
                for epic in board["epics"]
                for candidate in epic["planning"]["candidates"]
            ],
        )
        planned = next(epic for epic in board["epics"] if epic["id"] == "EPIC-PLANNED")
        self.assertEqual(planned["lifecycle"], "planned")
        self.assertEqual(planned["actions"][0]["kind"], "activate")
        self.assertTrue(planned["actions"][0]["enabled"])
        self.assertEqual(board["roadmap"]["candidateCount"], 3)
        self.assertEqual(board["roadmap"]["eligibleCount"], 1)
        relations = board["history"]["unresolvedRuntimeRelations"]
        self.assertEqual(
            [item["candidateId"] for item in relations],
            ["INC-ARCHIVED-001", "INC-MISMATCHED-001"],
        )
        self.assertEqual(
            [(item["epicId"], item["runtimeIncrementId"]) for item in relations],
            [("EPIC-ARCHIVED", "DI-088"), ("EPIC-TEST-001", "DI-089")],
        )
        self.assertTrue(all(item["readOnly"] for item in relations))
        self.assertTrue(all(not item["activatable"] for item in relations))
        self.assertTrue(
            all(
                item["candidateId"] in item["reason"]
                and item["epicId"] in item["reason"]
                and item["runtimeIncrementId"] in item["reason"]
                for item in relations
            )
        )
        self.assertEqual(board["health"], "partial")
        self.assertEqual(len(board["warnings"]), 2)

    def test_allocated_epic_is_blocked_consistently_across_action_and_roadmap(self) -> None:
        runtime = state("epic_complete")
        runtime.update(
            {
                "epicId": "EPIC-ALLOCATED",
                "activeIncrementId": None,
                "previousIncrementId": "DI-001",
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            self._portfolio(repo, ".")
            self._backlog(
                repo,
                [
                    {
                        "id": "INC-ALLOCATED",
                        "epicId": "EPIC-ALLOCATED",
                        "epicTitle": "Make delivery visible",
                        "title": "Must remain blocked",
                        "priority": 1,
                        "createdAt": "2026-08-21T13:00:00Z",
                    },
                    {
                        "id": "INC-FRESH",
                        "epicId": "EPIC-FRESH",
                        "epicTitle": "Fresh delivery",
                        "title": "May enter the mandate",
                        "priority": 2,
                        "createdAt": "2026-08-21T13:01:00Z",
                    },
                ],
            )
            catalog_before = (repo / ".aim/ui-portfolio.json").read_bytes()
            backlog_before = (repo / ".aim/portfolio-backlog.json").read_bytes()
            board = build_board(repo)

            self.assertEqual((repo / ".aim/ui-portfolio.json").read_bytes(), catalog_before)
            self.assertEqual((repo / ".aim/portfolio-backlog.json").read_bytes(), backlog_before)

        allocated = next(epic for epic in board["epics"] if epic["id"] == "EPIC-ALLOCATED")
        fresh = next(epic for epic in board["epics"] if epic["id"] == "EPIC-FRESH")
        self.assertFalse(allocated["actions"][0]["enabled"])
        self.assertIn("already allocated", allocated["actions"][0]["reason"])
        self.assertTrue(fresh["actions"][0]["enabled"])
        self.assertEqual(board["roadmap"]["eligibleCount"], 1)
        self.assertEqual(
            [item["candidateId"] for item in board["roadmap"]["snapshot"]],
            ["INC-FRESH"],
        )
        self.assertEqual(
            board["roadmap"]["blocked"][0]["reason"],
            allocated["actions"][0]["reason"],
        )

    def test_gate_a_workspace_has_epic_without_runtime_increment_card(self) -> None:
        runtime = state("gate_a_pending")
        runtime.update(
            {"activeIncrementId": None, "currentRole": "PO", "lastGatePassed": None}
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            (repo / ".aim/increments/001-wip.md").unlink()
            board = build_board(repo)

        self.assertEqual(len(board["epics"]), 1)
        self.assertEqual(board["epics"][0]["increments"], [])

    def test_plan_and_wip_for_one_runtime_increment_project_one_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            (repo / ".aim/increments/001-plan.md").write_text(
                "# DI-001 — Plan title\n\nEpic: EPIC-TEST-001\n",
                encoding="utf-8",
            )
            board = build_board(repo)

        increments = board["epics"][0]["increments"]
        self.assertEqual([item["id"] for item in increments], ["DI-001"])
        self.assertEqual(increments[0]["title"], "See the active work")
        self.assertEqual(
            {item["label"] for item in increments[0]["evidence"]},
            {"Increment plan", "Work log"},
        )

    def test_duplicate_backlog_candidate_is_isolated_without_losing_valid_work(self) -> None:
        candidate = {
            "id": "INC-UI-001",
            "epicId": "EPIC-UI",
            "epicTitle": "AIM UI",
            "title": "Control concurrency",
            "priority": 1,
            "createdAt": "2026-08-21T13:00:00Z",
        }
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._backlog(repo, [candidate, {**candidate, "title": "Duplicate"}])
            board = build_board(repo)

        planned = next(epic for epic in board["epics"] if epic["id"] == "EPIC-UI")
        self.assertEqual(
            [item["id"] for item in planned["planning"]["candidates"]],
            ["INC-UI-001"],
        )
        self.assertEqual(planned["increments"], [])
        self.assertFalse(board["roadmap"]["valid"])
        self.assertFalse(board["roadmap"]["auto"]["supported"])
        self.assertEqual(board["health"], "partial")
        self.assertTrue(any("duplicate id INC-UI-001" in warning for warning in board["warnings"]))

    def test_recent_deliveries_shows_latest_ten_while_closed_history_keeps_every_acceptance(self) -> None:
        runtime = state("gate_b_pending")
        runtime.update({"activeIncrementId": "DI-013", "currentRole": "TDO"})
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/013-wip.md").write_text(
                "# DI-013 — Next work\n\nEpic: EPIC-TEST-001\n", encoding="utf-8"
            )
            for number in range(1, 13):
                (aim / f"increments/{number:03d}-wip.md").write_text(
                    f"# DI-{number:03d} — Accepted {number}\n\nEpic: EPIC-TEST-001\n",
                    encoding="utf-8",
                )
                (aim / f"decisions/{number:03d}-gate-e.md").write_text(
                    f"# Accepted\n\nAccepted at: 2026-08-{number + 1:02d}T12:00:00Z\n",
                    encoding="utf-8",
                )
            board = build_board(repo)

        accepted = board["history"]["closedIncrements"]
        recent = board["history"]["recentDeliveries"]
        self.assertEqual(len(accepted), 12)
        self.assertEqual(board["history"]["recentLimit"], 10)
        self.assertEqual(
            [item["id"] for item in recent],
            [f"DI-{number:03d}" for number in range(12, 2, -1)],
        )
        self.assertTrue(
            all(
                item["visibleOnBoard"] is False
                for item in board["epics"][0]["increments"]
                if item["column"] == "done"
            )
        )
        self.assertEqual(
            [column["id"] for column in board["columns"]],
            ["backlog", "work_in_progress", "in_review", "ready_for_release"],
        )

    def test_delivery_data_uses_explicit_evidence_and_labels_fallbacks(self) -> None:
        runtime = state("gate_b_pending")
        runtime.update({"activeIncrementId": "DI-003", "currentRole": "TDO"})
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/002-wip.md").write_text(
                "# DI-002 — Accepted without a start\n\nEpic: EPIC-TEST-001\n",
                encoding="utf-8",
            )
            (aim / "increments/003-wip.md").write_text(
                "# DI-003 — Next work\n\nEpic: EPIC-TEST-001\n",
                encoding="utf-8",
            )
            (aim / "decisions/001-gate-b.md").write_text(
                "# Gate B\n\nApproved at: 2026-08-10T12:00:00Z\n",
                encoding="utf-8",
            )
            (aim / "decisions/001-gate-e.md").write_text(
                "# Gate E — Accepted\n\nAccepted at: 2026-08-11T12:00:00Z\n",
                encoding="utf-8",
            )
            (aim / "decisions/002-gate-e.md").write_text(
                "# Gate E — Accepted\n\nAccepted at: 2026-08-20T12:00:00Z\n",
                encoding="utf-8",
            )
            with patch("aim_ui.utc_now", return_value="2026-08-23T12:00:00Z"):
                board = build_board(repo)

        data = board["deliveryData"]
        self.assertEqual(data["epics"], {"total": 1, "active": 1, "completed": 0})
        self.assertEqual(data["increments"]["accepted"], 2)
        self.assertEqual(data["throughput"]["last7Days"], 1)
        self.assertEqual(data["throughput"]["last30Days"], 2)
        self.assertEqual(data["elapsed"]["medianHours"], 24.0)
        self.assertEqual(data["elapsed"]["sample"], 1)
        self.assertEqual(data["elapsed"]["excluded"], 1)
        self.assertEqual([item["id"] for item in data["history"]], ["DI-002", "DI-001"])
        self.assertTrue(data["history"][0]["evidencePath"].endswith("002-gate-e.md"))

    def test_delivery_data_excludes_file_time_fallback_from_metrics(self) -> None:
        runtime = state("gate_b_pending")
        runtime.update({"activeIncrementId": "DI-002", "currentRole": "TDO"})
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/002-wip.md").write_text(
                "# DI-002 — Next work\n\nEpic: EPIC-TEST-001\n", encoding="utf-8"
            )
            (aim / "decisions/001-gate-e.md").write_text(
                "# DI-001 Gate E — Accepted\n", encoding="utf-8"
            )
            with patch("aim_ui.utc_now", return_value="2026-08-23T12:00:00Z"):
                board = build_board(repo)

        data = board["deliveryData"]
        self.assertEqual(data["throughput"]["last30Days"], 0)
        self.assertEqual(data["throughput"]["excluded"], 1)
        self.assertEqual(data["history"][0]["timestampStatus"], "file_time_fallback")

    def test_delivery_data_labels_and_excludes_future_acceptance(self) -> None:
        runtime = state("gate_b_pending")
        runtime.update({"activeIncrementId": "DI-002", "currentRole": "TDO"})
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/002-wip.md").write_text(
                "# DI-002 — Next work\n\nEpic: EPIC-TEST-001\n", encoding="utf-8"
            )
            (aim / "decisions/001-gate-b.md").write_text(
                "# Gate B\n\nApproved at: 2026-08-22T12:00:00Z\n", encoding="utf-8"
            )
            (aim / "decisions/001-gate-e.md").write_text(
                "# Gate E — Accepted\n\nAccepted at: 2026-08-24T12:00:00Z\n",
                encoding="utf-8",
            )
            with patch("aim_ui.utc_now", return_value="2026-08-23T12:00:00Z"):
                board = build_board(repo)

        data = board["deliveryData"]
        self.assertEqual(data["throughput"]["last30Days"], 0)
        self.assertEqual(data["throughput"]["timestampSample"], 0)
        self.assertEqual(data["throughput"]["excluded"], 1)
        self.assertEqual(data["elapsed"]["sample"], 0)
        self.assertEqual(data["history"][0]["timestampStatus"], "future_timestamp")

    def test_completed_epic_projects_state_linked_previous_increment_into_done(self) -> None:
        runtime = state("epic_complete")
        runtime.update(
            {
                "activeIncrementId": None,
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "previousIncrementId": "DI-042",
                "previousIncrementStatus": "accepted",
                "gateEAcceptance": ".aim/decisions/2026-08-22-gate-e-user-accepted.md",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/042-wip.md").write_text(
                "# DI-042 — Finish the Portfolio\n\nEpic: EPIC-TEST-001\n",
                encoding="utf-8",
            )
            decision = aim / "decisions/2026-08-22-gate-e-user-accepted.md"
            decision.write_text(
                "# Gate E\n\nIncrement: DI-042\n\nStatus: Accepted\n\n"
                "Accepted at: 2026-08-22T14:00:00Z\n",
                encoding="utf-8",
            )
            board = build_board(repo)

        increments = {item["id"]: item for item in board["epics"][0]["increments"]}
        accepted = increments["DI-042"]
        self.assertEqual(accepted["column"], "done")
        self.assertEqual(accepted["runtimeStatus"], "done_increment_accepted")
        self.assertEqual(accepted["gate"], "Gate E")
        self.assertEqual(accepted["acceptedAt"], "2026-08-22T14:00:00Z")
        self.assertIn(
            ".aim/decisions/2026-08-22-gate-e-user-accepted.md",
            [item["path"] for item in accepted["evidence"]],
        )
        self.assertEqual(increments["DI-001"]["column"], "backlog")
        self.assertEqual(increments["DI-001"]["runtimeStatus"], "gate_b_pending")
        self.assertEqual(board["warnings"], [])

    def test_invalid_state_linked_acceptance_fails_closed_without_legacy_fallback(self) -> None:
        cases = {
            "traversal": ".aim/decisions/../outside.md",
            "missing": ".aim/decisions/missing.md",
            "wrong_workspace": ".aim/other/decisions/accepted.md",
        }
        for label, acceptance_path in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                runtime = state("epic_complete")
                runtime.update(
                    {
                        "activeIncrementId": None,
                        "currentRole": "PO",
                        "lastGatePassed": "Gate E",
                        "previousIncrementId": "DI-042",
                        "previousIncrementStatus": "accepted",
                        "gateEAcceptance": acceptance_path,
                    }
                )
                repo = self._repo(Path(temporary), runtime)
                aim = repo / ".aim"
                (aim / "increments/042-wip.md").write_text(
                    "# DI-042 — Remain unaccepted\n\nEpic: EPIC-TEST-001\n",
                    encoding="utf-8",
                )
                (aim / "decisions/042-gate-e.md").write_text(
                    "# Accepted\n\nIncrement: DI-042\n", encoding="utf-8"
                )
                board = build_board(repo)

            increment = next(
                item for item in board["epics"][0]["increments"] if item["id"] == "DI-042"
            )
            self.assertEqual(increment["column"], "backlog")
            self.assertEqual(increment["runtimeStatus"], "gate_b_pending")
            self.assertTrue(any("acceptance is hidden" in item for item in board["warnings"]))

    def test_structured_unaccepted_history_is_not_promoted_by_epic_completion(self) -> None:
        runtime = state("epic_complete")
        runtime.update(
            {
                "activeIncrementId": None,
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "previousIncrementId": "DI-042",
                "previousIncrementStatus": "rejected",
                "gateEAcceptance": ".aim/decisions/descriptive.md",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/042-wip.md").write_text(
                "# DI-042 — Not accepted\n\nEpic: EPIC-TEST-001\n",
                encoding="utf-8",
            )
            (aim / "decisions/042-gate-e.md").write_text(
                "# Accepted\n\nIncrement: DI-042\n", encoding="utf-8"
            )
            board = build_board(repo)

        increment = next(
            item for item in board["epics"][0]["increments"] if item["id"] == "DI-042"
        )
        self.assertEqual(increment["column"], "backlog")
        self.assertEqual(increment["runtimeStatus"], "gate_b_pending")
        self.assertEqual(board["warnings"], [])

    def test_state_linked_acceptance_rejects_symlink_and_mismatched_decision(self) -> None:
        for label in ("symlink", "mismatch"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                runtime = state("epic_complete")
                runtime.update(
                    {
                        "activeIncrementId": None,
                        "currentRole": "PO",
                        "lastGatePassed": "Gate E",
                        "previousIncrementId": "DI-042",
                        "previousIncrementStatus": "accepted",
                        "gateEAcceptance": ".aim/decisions/descriptive.md",
                    }
                )
                repo = self._repo(Path(temporary), runtime)
                aim = repo / ".aim"
                (aim / "increments/042-wip.md").write_text(
                    "# DI-042 — Remain unaccepted\n\nEpic: EPIC-TEST-001\n",
                    encoding="utf-8",
                )
                decision = aim / "decisions/descriptive.md"
                if label == "symlink":
                    outside = repo / "outside.md"
                    outside.write_text("# Accepted\n\nIncrement: DI-042\n", encoding="utf-8")
                    decision.symlink_to(outside)
                else:
                    decision.write_text(
                        "# Accepted\n\nIncrement: DI-999\n", encoding="utf-8"
                    )
                board = build_board(repo)

            increment = next(
                item for item in board["epics"][0]["increments"] if item["id"] == "DI-042"
            )
            self.assertEqual(increment["column"], "backlog")
            self.assertTrue(any("acceptance is hidden" in item for item in board["warnings"]))

    def test_read_model_links_increment_to_epic_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary)))
        self.assertEqual(board["readModelVersion"], "8.0")
        self.assertEqual(board["source"]["kind"], "single-workspace")
        self.assertTrue(board["source"]["readOnly"])
        self.assertEqual(len(board["epics"]), 1)
        epic = board["epics"][0]
        self.assertEqual(epic["id"], "EPIC-TEST-001")
        self.assertEqual(epic["increments"][0]["epicId"], epic["id"])
        self.assertEqual(epic["increments"][0]["column"], "work_in_progress")
        self.assertEqual(board["control"]["admission"], "unbounded")

    def test_reviewer_phase_projects_active_card_into_in_review(self) -> None:
        reviewer_state = state("review_in_progress")
        reviewer_state.update(
            {
                "currentRole": "Reviewer",
                "lastGatePassed": "Gate C",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary), reviewer_state))

        epic = board["epics"][0]
        increment = epic["increments"][0]
        self.assertEqual(epic["currentRole"], "Reviewer")
        self.assertEqual(increment["runtimeStatus"], "review_in_progress")
        self.assertEqual(increment["canonicalOwner"], "Reviewer")
        self.assertEqual(increment["column"], "in_review")

    def test_control_projects_focus_and_full_capacity_across_two_epics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._additional_workspace(repo)
            self._portfolio(repo, ".", "workspaces/other")
            self._control(repo, maximum=2, focused_epic_id="EPIC-TEST-002")
            board = build_board(repo)

        self.assertEqual(board["health"], "healthy")
        self.assertEqual(board["control"]["runningEpics"], 2)
        self.assertEqual(board["control"]["availableSlots"], 0)
        self.assertEqual(board["control"]["admission"], "full")
        focused = [epic["id"] for epic in board["epics"] if epic["focused"]]
        self.assertEqual(focused, ["EPIC-TEST-002"])

    def test_invalid_control_is_visible_and_blocks_admission_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            (repo / ".aim/portfolio-control.json").write_text(
                '{"controlVersion":"1.0","maxActiveEpics":0,"updatedAt":"now"}',
                encoding="utf-8",
            )
            board = build_board(repo)

        self.assertEqual(board["health"], "partial")
        self.assertEqual(board["control"]["admission"], "blocked")
        self.assertTrue(any("maxActiveEpics" in warning for warning in board["warnings"]))

    def test_portfolio_aggregates_two_independently_active_epics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            other = self._additional_workspace(repo)
            (other / "agent-activity.json").write_text(
                json.dumps(
                    {
                        "activityVersion": "1.0",
                        "agents": [
                            {
                                "id": "other-helper",
                                "task": "Review the companion",
                                "status": "working",
                                "epicId": "EPIC-TEST-002",
                                "incrementId": "DI-002",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self._portfolio(repo, ".", "workspaces/other")
            board = build_board(repo)

        self.assertEqual(board["health"], "healthy")
        self.assertEqual(board["source"]["kind"], "portfolio")
        self.assertEqual(board["source"]["workspaceCount"], 2)
        self.assertEqual(board["source"]["retainedWorkspaceCount"], 2)
        self.assertEqual(board["source"]["activeWorkspaceCount"], 2)
        self.assertEqual(len(board["epics"]), 2)
        self.assertTrue(all(epic["active"] for epic in board["epics"]))
        by_id = {epic["id"]: epic for epic in board["epics"]}
        self.assertEqual(
            by_id["EPIC-TEST-001"]["increments"][0]["column"],
            "work_in_progress",
        )
        self.assertEqual(
            by_id["EPIC-TEST-002"]["increments"][0]["column"], "in_review"
        )
        self.assertEqual(
            by_id["EPIC-TEST-002"]["helperActivity"]["items"][0]["id"],
            "other-helper",
        )

    def test_large_closed_history_remains_visible_without_consuming_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            paths = ["."]
            for index in range(1, 101):
                epic_id = f"EPIC-HISTORY-{index:03d}"
                increment_id = f"DI-{index + 1000}"
                workspace = self._additional_workspace(
                    repo,
                    name=f"history-{index:03d}",
                    epic_id=epic_id,
                    increment_id=increment_id,
                    status="epic_complete",
                )
                runtime_path = workspace / "state.json"
                runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
                runtime.update(
                    {
                        "currentRole": "PO",
                        "lastGatePassed": "Gate E",
                    }
                )
                runtime_path.write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
                paths.append(f"workspaces/history-{index:03d}")
            self._portfolio(repo, *paths)
            self._control(repo, maximum=2)

            board = build_board(repo)

        self.assertEqual(board["source"]["retainedWorkspaceCount"], 101)
        self.assertEqual(board["source"]["activeWorkspaceCount"], 1)
        self.assertEqual(board["control"]["runningEpics"], 1)
        self.assertEqual(board["control"]["availableSlots"], 1)
        self.assertEqual(len(board["epics"]), 101)

    def test_orphaned_root_checkpoint_is_named_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._additional_workspace(repo)
            self._portfolio(repo, "workspaces/other")
            state_path = repo / ".aim/state.json"
            before = state_path.read_bytes()
            board = build_board(repo)
            after = state_path.read_bytes()

        self.assertEqual(before, after)
        self.assertEqual([epic["id"] for epic in board["epics"]], ["EPIC-TEST-002"])
        diagnostic = next(
            item
            for item in board["workspaceDiagnostics"]
            if item["kind"] == "orphaned_invisible_workspace"
        )
        self.assertEqual(diagnostic["epicId"], "EPIC-TEST-001")
        self.assertEqual(diagnostic["statePath"], ".aim/state.json")
        self.assertTrue(diagnostic["readOnly"])
        self.assertIn("not declared", diagnostic["reason"])
        self.assertTrue(any("orphaned/invisible" in item for item in board["warnings"]))

    def test_legacy_checkpoint_names_each_contract_drift_and_is_not_projected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            runtime = json.loads((repo / ".aim/state.json").read_text(encoding="utf-8"))
            runtime.update(
                {
                    "epicStatus": "complete",
                    "activeIncrementId": "INC-LEGACY-037",
                    "lastGatePassed": "E",
                    "currentRole": "PO",
                }
            )
            (repo / ".aim/state.json").write_text(
                json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
            )
            self._portfolio(repo, ".")
            before = (repo / ".aim/state.json").read_bytes()
            board = build_board(repo)
            after = (repo / ".aim/state.json").read_bytes()

        self.assertEqual(after, before)
        self.assertEqual(board["epics"], [])
        diagnostic = board["workspaceDiagnostics"][0]
        joined = " ".join(diagnostic["contractDrift"])
        self.assertIn("epicStatus 'complete'", joined)
        self.assertIn("lastGatePassed 'E'", joined)
        self.assertIn("activeIncrementId 'INC-LEGACY-037'", joined)
        self.assertTrue(diagnostic["checkpoint"]["completed"])
        self.assertEqual(diagnostic["checkpoint"]["contract"], "legacy")
        self.assertEqual(len(diagnostic["checkpoint"]["stateSha256"]), 64)
        self.assertIn("statePath: .aim/state.json", diagnostic["chatIntent"])
        self.assertIn("epicId: EPIC-TEST-001", diagnostic["chatIntent"])
        self.assertIn("expectedUpdatedAt: 2026-08-21T12:00:00Z", diagnostic["chatIntent"])
        self.assertIn("failedContractChecks:", diagnostic["chatIntent"])
        self.assertEqual(board["recovery"]["kind"], "preserved_history")
        self.assertEqual(
            board["recovery"]["recommendedAction"]["label"],
            "Keep as history and create a new Roadmap",
        )

    def test_legacy_active_checkpoint_recommends_reviewed_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            state_path = repo / ".aim/state.json"
            runtime = json.loads(state_path.read_text(encoding="utf-8"))
            runtime["mode"] = "auto"
            state_path.write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
            self._portfolio(repo, ".")
            before = state_path.read_bytes()
            board = build_board(repo)
            after = state_path.read_bytes()

        self.assertEqual(after, before)
        self.assertEqual(board["epics"], [])
        diagnostic = board["workspaceDiagnostics"][0]
        self.assertFalse(diagnostic["checkpoint"]["completed"])
        self.assertEqual(
            diagnostic["recommendedOperation"], "review_and_migrate_checkpoint"
        )
        self.assertEqual(board["recovery"]["kind"], "checkpoint_attention")
        self.assertEqual(
            board["recovery"]["recommendedAction"]["label"],
            "Review and migrate checkpoint in AIM chat",
        )

    def test_one_workspace_moves_without_changing_the_other(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            other = self._additional_workspace(
                repo, status="increment_in_progress"
            )
            self._portfolio(repo, ".", "workspaces/other")
            before = build_board(repo)
            other_state = json.loads((other / "state.json").read_text(encoding="utf-8"))
            other_state.update(
                {
                    "epicStatus": "po_approval_pending",
                    "currentRole": "PO",
                    "lastGatePassed": "Gate D",
                }
            )
            (other / "state.json").write_text(
                json.dumps(other_state, indent=2) + "\n", encoding="utf-8"
            )
            after = build_board(repo)
            other_epic = next(
                epic for epic in after["epics"] if epic["id"] == "EPIC-TEST-002"
            )
            gate_e = other_epic["increments"][0]["actions"][0]["envelope"]

        def positions(board: dict) -> dict[str, str]:
            return {
                epic["id"]: epic["increments"][0]["column"]
                for epic in board["epics"]
            }

        self.assertEqual(positions(before)["EPIC-TEST-001"], "work_in_progress")
        self.assertEqual(positions(after)["EPIC-TEST-001"], "work_in_progress")
        self.assertEqual(
            gate_e["authorityStatePath"], ".aim/workspaces/other/state.json"
        )
        self.assertEqual(gate_e["gate"], "Gate E")
        self.assertEqual(gate_e["expectedLastGatePassed"], "Gate D")
        self.assertEqual(positions(before)["EPIC-TEST-002"], "work_in_progress")
        self.assertEqual(positions(after)["EPIC-TEST-002"], "ready_for_release")

    def test_unsafe_and_missing_workspaces_are_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            outside = repo / "outside-workspace"
            outside.mkdir()
            (repo / ".aim/workspaces").mkdir()
            (repo / ".aim/workspaces/escape").symlink_to(outside, target_is_directory=True)
            self._portfolio(
                repo,
                ".",
                "../outside",
                "/tmp",
                "missing",
                "workspaces/escape",
                ".",
            )
            board = build_board(repo)

        self.assertEqual(board["health"], "partial")
        self.assertEqual([epic["id"] for epic in board["epics"]], ["EPIC-TEST-001"])
        self.assertGreaterEqual(len(board["warnings"]), 5)
        self.assertTrue(any("leaves .aim" in item for item in board["warnings"]))
        self.assertTrue(any("must be relative" in item for item in board["warnings"]))
        self.assertTrue(any("duplicate path" in item for item in board["warnings"]))

    def test_duplicate_epic_id_is_not_projected_twice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            self._additional_workspace(repo, epic_id="EPIC-TEST-001")
            self._portfolio(repo, ".", "workspaces/other")
            board = build_board(repo)

        self.assertEqual(board["health"], "partial")
        self.assertEqual(len(board["epics"]), 1)
        self.assertIn("duplicate Epic id", board["warnings"][0])

    def test_accepted_nonactive_increment_is_done(self) -> None:
        runtime = state("gate_b_pending")
        runtime["activeIncrementId"] = "DI-002"
        runtime["currentRole"] = "TDO"
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/002-wip.md").write_text(
                "# DI-002 — Next slice\n\nEpic: EPIC-TEST-001\n", encoding="utf-8"
            )
            (aim / "decisions/001-gate-e.md").write_text(
                "# DI-001 Gate E — Accepted\n", encoding="utf-8"
            )
            board = build_board(repo)
        items = {item["id"]: item for item in board["epics"][0]["increments"]}
        self.assertEqual(items["DI-001"]["column"], "done")
        self.assertEqual(items["DI-002"]["column"], "backlog")

    def test_change_requested_gate_e_is_not_acceptance_evidence(self) -> None:
        runtime = state("gate_b_pending")
        runtime["activeIncrementId"] = "DI-002"
        runtime["currentRole"] = "TDO"
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), runtime)
            aim = repo / ".aim"
            (aim / "increments/002-wip.md").write_text(
                "# DI-002 — Next slice\n\nEpic: EPIC-TEST-001\n", encoding="utf-8"
            )
            (aim / "decisions/001-gate-e.md").write_text(
                "# Gate E — DI-001\n\n"
                "Decision: Change requested by the user\n\n"
                "Restart after the Increment is accepted and released.\n",
                encoding="utf-8",
            )
            board = build_board(repo)

        items = {item["id"]: item for item in board["epics"][0]["increments"]}
        self.assertEqual(items["DI-001"]["column"], "backlog")
        self.assertIsNone(items["DI-001"]["acceptedAt"])

    def test_helper_activity_is_separate_and_scoped_to_epic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            (repo / ".aim/agent-activity.json").write_text(
                json.dumps(
                    {
                        "activityVersion": "1.0",
                        "updatedAt": "2026-08-21T12:01:00Z",
                        "agents": [
                            {
                                "id": "review-helper",
                                "task": "Check keyboard flow",
                                "status": "working",
                                "canonicalRole": "Reviewer",
                                "epicId": "EPIC-TEST-001",
                                "incrementId": "DI-001",
                            },
                            {
                                "id": "other-epic",
                                "task": "Out of scope",
                                "status": "working",
                                "epicId": "EPIC-OTHER",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            board = build_board(repo)
        activity = board["epics"][0]["helperActivity"]
        self.assertTrue(activity["available"])
        self.assertEqual([item["id"] for item in activity["items"]], ["review-helper"])
        self.assertEqual(activity["items"][0]["canonicalRole"], "Reviewer")

    def test_missing_or_malformed_runtime_returns_safe_degraded_board(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".aim").mkdir()
            board = build_board(root)
            self.assertEqual(board["health"], "degraded")
            self.assertEqual(board["epics"], [])
            (root / ".aim/state.json").write_text("{not json", encoding="utf-8")
            board = build_board(root)
            self.assertIn("invalid JSON", board["warnings"][0])

    def test_evidence_resolution_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            evidence = resolve_evidence_path(repo, ".aim/increments/001-wip.md")
            self.assertTrue(evidence.is_file())
            with self.assertRaises(AimUiError):
                resolve_evidence_path(repo, ".aim/../outside.txt")
            with self.assertRaises(AimUiError):
                resolve_evidence_path(repo, "/etc/passwd")

    def test_http_transport_rejects_writes_without_changing_aim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary))
            before = {
                path.relative_to(repo).as_posix(): path.read_bytes()
                for path in (repo / ".aim").rglob("*")
                if path.is_file()
            }
            server = AimUiServer(("127.0.0.1", 0), repo, REPO_ROOT / "aim-ui")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_address[1]}"
                with urlopen(f"{url}/api/board", timeout=3) as response:
                    payload = json.load(response)
                    self.assertTrue(payload["source"]["readOnly"])
                with urlopen(f"{url}/api/health", timeout=3) as response:
                    health = json.load(response)
                    self.assertEqual(health["protocolVersion"], "1.1")
                    self.assertRegex(health["payloadFingerprint"], r"^[0-9a-f]{64}$")
                request = Request(f"{url}/api/board", data=b"{}", method="POST")
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=3)
                self.assertEqual(error.exception.code, 405)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
            after = {
                path.relative_to(repo).as_posix(): path.read_bytes()
                for path in (repo / ".aim").rglob("*")
                if path.is_file()
            }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
