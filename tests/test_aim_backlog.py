"""Safe AIM UI Backlog merge tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_backlog import BacklogError, merge_backlog, normalize_import  # noqa: E402
from aim_ui import build_board  # noqa: E402


NOW = "2026-08-22T11:00:00Z"


class AimBacklogTests(unittest.TestCase):
    def test_generates_stable_ids_and_source_order_priorities(self) -> None:
        request = {
            "items": [
                {"epicTitle": "Checkout recovery", "title": "Explain delayed payment"},
                {"epicTitle": "Onboarding", "title": "Show the first useful step"},
            ]
        }
        first = normalize_import(request, NOW)
        second = normalize_import(request, "2026-08-23T00:00:00Z")
        self.assertEqual(
            [item["id"] for item in first],
            [
                "INC-CHECKOUT-RECOVERY-EXPLAIN-DELAYED-PAYMENT",
                "INC-ONBOARDING-SHOW-THE-FIRST-USEFUL-STEP",
            ],
        )
        self.assertEqual([item["priority"] for item in first], [1, 2])
        self.assertEqual(
            [item["id"] for item in first], [item["id"] for item in second]
        )

    def test_generated_ids_remain_bounded_for_long_titles(self) -> None:
        item = normalize_import(
            {"items": [{"epicTitle": "Epic title " * 18, "title": "Increment title " * 15}]},
            NOW,
        )[0]
        self.assertLessEqual(len(item["epicId"]), 120)
        self.assertLessEqual(len(item["id"]), 80)

    def test_merges_idempotently_and_updates_related_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            initial = normalize_import(
                {"items": [{"epicTitle": "Checkout", "title": "Recovery", "summary": "First"}]},
                NOW,
            )
            added = merge_backlog(repo, initial, NOW)
            skipped = merge_backlog(repo, initial, "2026-08-22T11:01:00Z")
            changed = normalize_import(
                {"items": [{"epicTitle": "Checkout", "title": "Recovery", "summary": "Better"}]},
                "2026-08-22T11:02:00Z",
            )
            updated = merge_backlog(repo, changed, "2026-08-22T11:02:00Z")
            value = json.loads((repo / ".aim/portfolio-backlog.json").read_text())
        self.assertEqual(len(added["added"]), 1)
        self.assertEqual(len(skipped["skipped"]), 1)
        self.assertEqual(len(updated["updated"]), 1)
        self.assertEqual(value["items"][0]["summary"], "Better")
        self.assertEqual(value["items"][0]["createdAt"], NOW)

    def test_conflict_is_atomic_and_preserves_existing_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            first = normalize_import(
                {"items": [{"id": "INC-SHARED-001", "epicTitle": "One", "title": "First"}]},
                NOW,
            )
            merge_backlog(repo, first, NOW)
            path = repo / ".aim/portfolio-backlog.json"
            before = path.read_bytes()
            conflicting = normalize_import(
                {"items": [{"id": "INC-SHARED-001", "epicTitle": "Two", "title": "Other"}]},
                "2026-08-22T11:03:00Z",
            )
            with self.assertRaisesRegex(BacklogError, "conflicts require review"):
                merge_backlog(repo, conflicting, "2026-08-22T11:03:00Z")
            after = path.read_bytes()
        self.assertEqual(before, after)

    def test_rejects_authority_fields_and_duplicate_input(self) -> None:
        with self.assertRaisesRegex(BacklogError, "unsupported fields: gate"):
            normalize_import(
                {"items": [{"epicTitle": "One", "title": "First", "gate": "Gate B"}]},
                NOW,
            )
        with self.assertRaisesRegex(BacklogError, "positive integer"):
            normalize_import(
                {"items": [{"epicTitle": "One", "title": "First", "priority": 0}]},
                NOW,
            )

    def test_related_update_without_summary_preserves_existing_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            merge_backlog(
                repo,
                normalize_import(
                    {"items": [{"epicTitle": "One", "title": "First", "summary": "Keep me"}]},
                    NOW,
                ),
                NOW,
            )
            merge_backlog(
                repo,
                normalize_import(
                    {"items": [{"epicTitle": "One", "title": "First"}]},
                    "2026-08-22T11:05:00Z",
                ),
                "2026-08-22T11:05:00Z",
            )
            value = json.loads(
                (repo / ".aim/portfolio-backlog.json").read_text(encoding="utf-8")
            )
        self.assertEqual(value["items"][0]["summary"], "Keep me")
        with self.assertRaisesRegex(BacklogError, "duplicate candidate id"):
            normalize_import(
                {
                    "items": [
                        {"id": "INC-ONE", "epicTitle": "One", "title": "First"},
                        {"id": "INC-ONE", "epicTitle": "One", "title": "First"},
                    ]
                },
                NOW,
            )

    def test_rejects_symlinked_aim_without_writing_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            outside = root / "outside"
            repo.mkdir()
            outside.mkdir()
            (repo / ".aim").symlink_to(outside, target_is_directory=True)
            imported = normalize_import(
                {"items": [{"epicTitle": "One", "title": "First"}]}, NOW
            )
            with self.assertRaisesRegex(BacklogError, "must not be a symbolic link"):
                merge_backlog(repo, imported, NOW)
            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_symlinked_backlog_without_changing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            aim_root = repo / ".aim"
            aim_root.mkdir(parents=True)
            outside = root / "outside.json"
            outside.write_text("untouched\n", encoding="utf-8")
            (aim_root / "portfolio-backlog.json").symlink_to(outside)
            imported = normalize_import(
                {"items": [{"epicTitle": "One", "title": "First"}]}, NOW
            )
            with self.assertRaisesRegex(BacklogError, "must not be a symbolic link"):
                merge_backlog(repo, imported, NOW)
            self.assertEqual(outside.read_text(encoding="utf-8"), "untouched\n")

    def test_imported_candidates_are_visible_as_stationary_epics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            imported = normalize_import(
                {
                    "items": [
                        {"epicTitle": "Checkout", "title": "Recover payment"},
                        {"epicTitle": "Onboarding", "title": "Explain first step"},
                    ]
                },
                NOW,
            )
            merge_backlog(repo, imported, NOW)
            board = build_board(repo)
        self.assertEqual(len(board["epics"]), 2)
        self.assertTrue(all(epic["increments"] == [] for epic in board["epics"]))
        self.assertTrue(all(epic["lifecycle"] == "planned" for epic in board["epics"]))
        self.assertTrue(
            all(epic["planning"]["candidateCount"] == 1 for epic in board["epics"])
        )

    def test_cli_reads_stdin_and_creates_planning_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/aim_backlog.py"),
                    "--repo",
                    str(repo),
                    "--timestamp",
                    NOW,
                    "--format",
                    "json",
                ],
                input=json.dumps(
                    {"items": [{"epicTitle": "One", "title": "First"}]}
                ),
                capture_output=True,
                text=True,
                timeout=10,
            )
            result = json.loads(completed.stdout)
            files = sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(result["added"]), 1)
        self.assertEqual(files, [".aim/portfolio-backlog.json"])


if __name__ == "__main__":
    unittest.main()
