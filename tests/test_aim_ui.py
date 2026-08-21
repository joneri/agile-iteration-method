"""AIM UI read-model and read-only transport tests."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
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

    def test_read_model_links_increment_to_epic_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            board = build_board(self._repo(Path(temporary)))
        self.assertEqual(board["readModelVersion"], "1.0")
        self.assertTrue(board["source"]["readOnly"])
        self.assertEqual(len(board["epics"]), 1)
        epic = board["epics"][0]
        self.assertEqual(epic["id"], "EPIC-TEST-001")
        self.assertEqual(epic["increments"][0]["epicId"], epic["id"])
        self.assertEqual(epic["increments"][0]["column"], "work_in_progress")

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
