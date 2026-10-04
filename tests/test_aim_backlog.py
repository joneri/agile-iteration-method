"""Safe AIM UI Backlog merge tests."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_backlog import BacklogError, MAX_BACKLOG_BYTES, merge_backlog, normalize_import, validate_backlog  # noqa: E402
from aim_activation import _read_backlog  # noqa: E402
from aim_ui import build_board  # noqa: E402
from aim_validator.schema_subset import validate as validate_schema  # noqa: E402


NOW = "2026-08-22T11:00:00Z"


class AimBacklogTests(unittest.TestCase):
    def _research_source(self, proposal_id: str, *, system: str = "rndaim", title: str = "Research intake") -> dict:
        proposal = {"id": proposal_id, "title": title, "evidenceIds": ["R-20261004-002"]}
        canonical = json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return {
            "system": system,
            "proposalId": proposal_id,
            "proposalSha256": hashlib.sha256(canonical).hexdigest(),
            "evidenceIds": proposal["evidenceIds"],
            "sourcePath": "proposals/2026-10-04.json",
        }

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
            before_replay = (repo / ".aim/portfolio-backlog.json").read_bytes()
            skipped = merge_backlog(repo, initial, "2026-08-22T11:01:00Z")
            after_replay = (repo / ".aim/portfolio-backlog.json").read_bytes()
            changed = normalize_import(
                {"items": [{"epicTitle": "Checkout", "title": "Recovery", "summary": "Better"}]},
                "2026-08-22T11:02:00Z",
            )
            updated = merge_backlog(repo, changed, "2026-08-22T11:02:00Z")
            value = json.loads((repo / ".aim/portfolio-backlog.json").read_text())
        self.assertEqual(len(added["added"]), 1)
        self.assertEqual(len(skipped["skipped"]), 1)
        self.assertEqual(before_replay, after_replay)
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

    def test_research_sources_merge_without_runtime_writes_or_duplicate_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            aim = repo / ".aim"
            aim.mkdir()
            (aim / "state.json").write_bytes(b"active runtime sentinel\n")
            (aim / "portfolio-run.json").write_bytes(b"portfolio mandate sentinel\n")
            source = self._research_source("P-20261004-002")
            request = {"items": [{"epicTitle": "Research intake", "title": "Review source",
                                   "sources": [source]}]}
            imported = normalize_import(request, NOW)
            first = merge_backlog(repo, imported, NOW)
            path = aim / "portfolio-backlog.json"
            before = path.read_bytes()
            second = merge_backlog(repo, normalize_import(request, "2026-08-22T12:00:00Z"), "2026-08-22T12:00:00Z")
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(json.loads(before)["updatedAt"], NOW)
            self.assertEqual(len(first["added"]), 1)
            self.assertEqual(len(second["skipped"]), 1)

            another_source = self._research_source("P-20261005-004")
            third = merge_backlog(
                repo,
                normalize_import({"items": [{"epicTitle": "Research intake",
                                             "title": "Review source", "sources": [another_source]}]},
                                 "2026-08-22T13:00:00Z"),
                "2026-08-22T13:00:00Z",
            )
            value = json.loads(path.read_text())
            self.assertEqual(len(third["updated"]), 1)
            schema = json.loads((REPO_ROOT / "schemas/aim-ui-backlog.schema.json").read_text())
            self.assertEqual(validate_schema(value, schema), [])
            self.assertEqual(validate_backlog(value), [])
            self.assertEqual(
                [item["proposalId"] for item in value["items"][0]["sources"]],
                ["P-20261004-002", "P-20261005-004"],
            )
            self.assertEqual((aim / "state.json").read_bytes(), b"active runtime sentinel\n")
            self.assertEqual((aim / "portfolio-run.json").read_bytes(), b"portfolio mandate sentinel\n")
            self.assertEqual(
                sorted(p.name for p in aim.iterdir()),
                ["portfolio-backlog.json", "portfolio-run.json", "state.json"],
            )

    def test_research_source_identity_conflicts_are_atomic_and_system_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            source = self._research_source("P-SHARED")
            first = normalize_import({"items": [{"epicTitle": "One", "title": "First", "sources": [source]}]}, NOW)
            merge_backlog(repo, first, NOW)
            path = repo / ".aim/portfolio-backlog.json"
            before = path.read_bytes()
            changed = {**source, "proposalSha256": "f" * 64}
            for request in (
                {"items": [{"epicTitle": "One", "title": "First", "sources": [changed]}]},
                {"items": [{"epicTitle": "Two", "title": "Other", "sources": [source]}]},
            ):
                with self.assertRaisesRegex(BacklogError, "conflicts require review"):
                    merge_backlog(repo, normalize_import(request, NOW), NOW)
                self.assertEqual(path.read_bytes(), before)

            other_system = self._research_source("P-SHARED", system="other-research")
            merge_backlog(
                repo,
                normalize_import({"items": [{"epicTitle": "Two", "title": "Other", "sources": [other_system]}]}, NOW),
                NOW,
            )
            value = json.loads(path.read_text())
            self.assertEqual(len(value["items"]), 2)
            self.assertEqual({source["system"] for item in value["items"] for source in item["sources"]},
                             {"rndaim", "other-research"})

    def test_rejects_unsafe_research_source_data(self) -> None:
        source = self._research_source("P-20261004-002")
        for unsafe in ({**source, "sourcePath": "../private.json"},
                       {**source, "gate": "Gate B"},
                       {**source, "evidenceIds": ["R-1", "R-1"]}):
            with self.assertRaises(BacklogError):
                normalize_import({"items": [{"epicTitle": "One", "title": "First",
                                             "sources": [unsafe]}]}, NOW)

    def test_schema_rejects_unsafe_source_paths_also_rejected_by_import(self) -> None:
        source = self._research_source("P-20261004-002")
        item = normalize_import({"items": [{"epicTitle": "One", "title": "First",
                                             "sources": [source]}]}, NOW)[0]
        schema = json.loads((REPO_ROOT / "schemas/aim-ui-backlog.schema.json").read_text())
        backlog = {"backlogVersion": "1.0", "updatedAt": NOW, "items": [item]}
        self.assertEqual(validate_schema(backlog, schema), [])
        for unsafe_path in ("../private.json", "/absolute.json", "a//b", "a/./b", "a/../b", "a/"):
            with self.subTest(sourcePath=unsafe_path):
                item["sources"][0]["sourcePath"] = unsafe_path
                self.assertTrue(validate_schema(backlog, schema))
                self.assertTrue(validate_backlog(backlog))

    def test_writer_ui_and_activation_share_backlog_size_limit(self) -> None:
        items = []
        for index in range(128):
            sources = []
            for source_index in range(8):
                sources.append({
                    "system": "rndaim",
                    "proposalId": f"P-{index:03d}-{source_index}",
                    "proposalSha256": "a" * 64,
                    "evidenceIds": [
                        f"R-{index:03d}-{source_index}-{evidence_index:02d}-" + "X" * 16
                        for evidence_index in range(16)
                    ],
                    "sourcePath": "proposals/2026-10-04.json",
                })
            items.append({"epicTitle": f"Epic {index}", "title": f"Candidate {index}",
                          "sources": sources})
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            imported = normalize_import({"items": items}, NOW)
            merge_backlog(repo, imported, NOW)
            path = repo / ".aim/portfolio-backlog.json"
            self.assertGreater(path.stat().st_size, 1_000_000)
            self.assertLessEqual(path.stat().st_size, MAX_BACKLOG_BYTES)
            board = build_board(repo)
            activation_backlog, raw = _read_backlog(repo / ".aim")
            self.assertEqual(len(raw), path.stat().st_size)
            self.assertEqual(len(activation_backlog["items"]), 128)
            self.assertEqual(
                sum(len(epic["planning"]["candidates"]) for epic in board["epics"]
                    if epic["lifecycle"] == "planned"),
                128,
            )

    def test_planned_board_exposes_source_identity_without_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            merge_backlog(
                repo,
                normalize_import({"items": [{"epicTitle": "Research", "title": "Review source",
                                             "sources": [self._research_source("P-20261004-002")]}]}, NOW),
                NOW,
            )
            board = build_board(repo)
        planned = next(epic for epic in board["epics"] if epic["lifecycle"] == "planned")
        self.assertEqual(planned["planning"]["candidates"][0]["sources"][0]["proposalId"], "P-20261004-002")
        self.assertEqual(planned["increments"], [])

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
