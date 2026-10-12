"""Product-only control-room projection, independent of legacy workspace data."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aim_stories
from aim_stories import FILE, project_story_board
from aim_ui import build_board
from aim_ui_product import MAX_DISCUSSION_SOURCES, project_product_context
import aim_ui_product
import test_aim_stories as story_fixtures
import test_aim_ui as legacy_fixtures

NOW = "2026-10-12T12:00:00Z"


class ProductControlRoomTests(unittest.TestCase):
    def setUp(self):
        self.fixture = story_fixtures.StoryDeliveryTests("test_complete_mixed_epic_loop_and_independent_epic_closure")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo

    def context(self, snapshot=None):
        return project_product_context(self.repo, snapshot or project_story_board(self.repo), NOW)

    def test_current_only_catalog_is_initialized_and_measured_without_legacy(self):
        with patch("aim_ui.utc_now", return_value=NOW):
            board = build_board(self.repo)
        product = board["productContext"]
        self.assertIsNone(board["onboarding"])
        self.assertEqual(board["health"], "healthy")
        self.assertEqual(board["epics"], [])
        self.assertEqual(product["counts"], {"intents": 1, "epics": 2, "openEpics": 2, "closedEpics": 0,
                                              "stories": 3, "readyStories": 2, "doneStories": 0, "acceptedDeliveries": 0})
        self.assertEqual(product["source"], FILE)
        self.assertEqual(product["storeSha256"], board["storyBoard"]["storeSha256"])
        self.assertIsNone(product["currentRole"])
        self.assertFalse(any(role["current"] for role in product["roles"]))
        self.assertEqual(product["data"]["stories"], {"total": 3, "ready": 2, "done": 0})
        self.assertEqual(board["deliveryData"]["epics"]["total"], 0)

    def test_checkpoint_roles_follow_cross_epic_delivery_and_blocked_phase(self):
        self.fixture.plan()
        self.assertEqual(self.context()["currentRole"], "TDO")
        scope = self.fixture.document["deliveries"][0]["scopeSha256"]
        self.fixture.mutate("approve", {"deliveryId": "DI-1", "authority": self.fixture.authority(scope)})
        self.assertEqual(self.context()["currentRole"], "Dev")
        self.fixture.mutate("review", {"deliveryId": "DI-1", "bindings": [self.fixture.binding]})
        self.fixture.mutate("block", {"deliveryId": "DI-1", "reason": "Need a sample account"})
        context = self.context()
        self.assertEqual(context["currentRole"], "Reviewer")
        self.assertEqual(context["activeDeliveryId"], "DI-1")
        self.assertEqual([r["id"] for r in context["roles"] if r["current"]], ["Reviewer"])
        self.assertEqual(context["activity"]["status"], "unrecorded")
        self.assertIn("not agent presence", context["activity"]["message"])
        self.fixture.mutate("unblock", {"deliveryId": "DI-1", "reason": "Account ready"})
        self.fixture.mutate("validate", {"deliveryId": "DI-1", "evidence": [self.fixture.evidence]})
        self.assertEqual(self.context()["currentRole"], "TDO")
        self.fixture.mutate("acceptance", {"deliveryId": "DI-1", "evidence": [self.fixture.evidence], "criteria": self.fixture.criterion_evidence()})
        self.assertEqual(self.context()["currentRole"], "PO")

    def test_cross_epic_acceptance_counts_once_and_preserves_exact_scope(self):
        with patch("aim_stories.now", return_value="2026-10-10T12:00:00Z"):
            self.fixture.accept()
        context = self.context()
        self.assertEqual(context["counts"]["doneStories"], 2)
        self.assertEqual(context["counts"]["acceptedDeliveries"], 1)
        self.assertEqual(context["counts"]["openEpics"], 2)
        self.assertIsNone(context["activeDeliveryId"])
        self.assertIsNone(context["currentRole"])
        data = context["data"]
        self.assertEqual(data["throughput"], {"last7Days": 1, "last30Days": 1, "timestampSample": 1, "excluded": 0})
        self.assertEqual(data["elapsed"], {"status": "unavailable", "medianHours": None, "sample": 0, "excluded": 1})
        row = data["history"][0]
        self.assertEqual(row["epicId"], "EPIC-BUY, EPIC-SUPPORT")
        self.assertEqual(row["epicTitle"], "Buying, Support")
        self.assertEqual(row["storyIds"], ["US-BUYER", "US-AGENT"])
        self.assertEqual(row["timestampStatus"], "recorded")
        self.assertEqual(row["evidencePath"], self.fixture.acceptance["path"])
        self.assertIsNone(row["elapsedHours"])

    def test_timestamp_windows_use_explicit_aware_time_and_exclude_missing_or_future(self):
        self.fixture.accept()
        snapshot = project_story_board(self.repo)
        cases = [
            ("2026-10-05T12:00:00Z", "recorded", 1, 1, 0),
            ("2026-10-05T11:59:59Z", "recorded", 0, 1, 0),
            ("2026-09-12T12:00:00Z", "recorded", 0, 1, 0),
            ("2026-09-12T11:59:59Z", "recorded", 0, 0, 0),
            ("2026-10-12T14:00:00+02:00", "recorded", 1, 1, 0),
            ("2026-10-12T12:00:01Z", "future_timestamp", 0, 0, 1),
            ("2026-10-12T12:00:00", "missing_timestamp", 0, 0, 1),
            ("not recorded", "missing_timestamp", 0, 0, 1),
            (None, "missing_timestamp", 0, 0, 1),
        ]
        for timestamp, status, seven, thirty, excluded in cases:
            with self.subTest(timestamp=timestamp):
                current = copy.deepcopy(snapshot)
                if timestamp is None:
                    current["deliveries"][0].pop("acceptedAt", None)
                else:
                    current["deliveries"][0]["acceptedAt"] = timestamp
                data = self.context(current)["data"]
                self.assertEqual(data["history"][0]["timestampStatus"], status)
                self.assertEqual(data["throughput"]["last7Days"], seven)
                self.assertEqual(data["throughput"]["last30Days"], thirty)
                self.assertEqual(data["throughput"]["excluded"], excluded)
                self.assertIsNone(data["elapsed"]["medianHours"])
                self.assertEqual(data["increments"]["accepted"], 1)

    def test_validated_ledger_extreme_offsets_do_not_crash_board(self):
        self.fixture.accept()
        path = self.repo / FILE
        for timestamp in ("0001-01-01T00:00:00+14:00", "9999-12-31T23:59:59-14:00"):
            with self.subTest(timestamp=timestamp):
                document = json.loads(path.read_text())
                document["deliveries"][0]["acceptedAt"] = timestamp
                path.write_text(json.dumps(document))
                with patch("aim_ui.utc_now", return_value=NOW):
                    board = build_board(self.repo)
                self.assertTrue(board["storyBoard"]["valid"])
                self.assertEqual(board["health"], "healthy")
                data = board["productContext"]["data"]
                self.assertEqual(data["increments"]["accepted"], 1)
                self.assertEqual(data["throughput"], {"last7Days": 0, "last30Days": 0, "timestampSample": 0, "excluded": 1})
                self.assertEqual(data["history"][0]["timestampStatus"], "missing_timestamp")

    def test_discussion_includes_current_ledger_profile_acceptance_and_read_only_boundary(self):
        self.fixture.accept()
        (self.repo / "aim.profile.yaml").write_text("aimRepoProfile: {}\n")
        discussion = self.context()["discussion"]
        paths = [source["path"] for source in discussion["sources"]]
        self.assertIn(FILE, paths)
        self.assertIn("aim.profile.yaml", paths)
        self.assertIn(self.fixture.acceptance["path"], paths)
        self.assertEqual(discussion["counts"], {"intents": 1, "epics": 2, "stories": 3, "acceptedDeliveries": 1})
        self.assertEqual(discussion["mode"], "read_only")
        self.assertIn("untrusted evidence", discussion["promptPreamble"])
        self.assertIn("Reload and revalidate", discussion["promptPreamble"])
        self.assertIn("final acceptance", discussion["boundary"])
        self.assertEqual(discussion["recentDeliveries"][0]["storyIds"], ["US-BUYER", "US-AGENT"])

    def test_discussion_sources_are_bounded_and_never_include_product_source_bindings(self):
        self.fixture.approve()
        many = [self.fixture.artifact(f"plan-{i}.md", "Bounded planning evidence") for i in range(30)]
        snapshot = project_story_board(self.repo)
        # Feed a validated-shape projection with many plan references to test
        # manifest bounds independently of the delivery transition code.
        snapshot["deliveries"][0]["planEvidence"] = many
        before = json.dumps(snapshot, sort_keys=True)
        with patch("aim_stories.load", side_effect=AssertionError("Projection must not reload the ledger")):
            context = self.context(snapshot)
        self.assertLessEqual(len(context["discussion"]["sources"]), MAX_DISCUSSION_SOURCES)
        self.assertNotIn("app.py", [item["path"] for item in context["discussion"]["sources"]])
        self.assertEqual(before, json.dumps(snapshot, sort_keys=True))

    def test_profile_symlink_and_unsafe_manifest_paths_are_not_exposed(self):
        self.fixture.accept()
        (self.repo / "aim.profile.yaml").symlink_to(self.repo / "app.py")
        snapshot = project_story_board(self.repo)
        snapshot["deliveries"][0]["acceptance"]["path"] = "../../outside.md"
        paths = [source["path"] for source in self.context(snapshot)["discussion"]["sources"]]
        self.assertNotIn("aim.profile.yaml", paths)
        self.assertNotIn("../../outside.md", paths)

    def test_build_board_validates_product_ledger_once(self):
        original = aim_stories.load
        with patch("aim_stories.load", wraps=original) as loader:
            board = build_board(self.repo)
        self.assertEqual(loader.call_count, 1)
        self.assertEqual(board["productContext"]["counts"]["stories"], 3)

    def test_maximum_story_backlog_has_constant_optional_source_checks(self):
        additional = [{**self.fixture.request["stories"][0], "id": f"US-MAX-{index}", "priority": index}
                      for index in range(4, 257)]
        self.fixture.mutate("import", {"stories": additional})
        snapshot = project_story_board(self.repo)
        with patch("aim_ui_product._known_regular_file", wraps=aim_ui_product._known_regular_file) as check:
            result = self.context(snapshot)
        self.assertEqual(result["counts"]["stories"], 256)
        self.assertEqual(result["counts"]["readyStories"], 255)
        self.assertEqual(check.call_count, 2)
        self.assertLessEqual(len(result["discussion"]["sources"]), MAX_DISCUSSION_SOURCES)

    def test_invalid_ledger_is_visible_without_success_counts_or_legacy_fallback(self):
        (self.repo / FILE).write_text('{"broken": true}')
        board = build_board(self.repo)
        product = board["productContext"]
        self.assertTrue(product["configured"])
        self.assertFalse(product["valid"])
        self.assertIsNone(product["counts"])
        self.assertIsNone(product["data"])
        self.assertIsNone(product["currentRole"])
        self.assertTrue(product["issues"])
        self.assertEqual(board["health"], "degraded")
        self.assertEqual(board["onboarding"]["state"], "product_repair_required")
        self.assertIn("repair", product["discussion"]["summary"])
        self.assertEqual(product["discussion"]["recentDeliveries"], [])
        self.assertIsNone(product["discussion"]["counts"])

    def test_missing_ledger_retains_new_product_onboarding_without_invented_metrics(self):
        (self.repo / FILE).unlink()
        board = build_board(self.repo)
        product = board["productContext"]
        self.assertFalse(product["configured"])
        self.assertTrue(product["valid"])
        self.assertIsNone(product["counts"])
        self.assertIsNone(product["data"])
        self.assertEqual(board["onboarding"]["state"], "not_initialized")
        self.assertIn("Describe an intent", product["discussion"]["summary"])
        self.assertNotIn(FILE, [item["path"] for item in product["discussion"]["sources"]])

    def test_mixed_legacy_history_remains_separate_from_current_product(self):
        old = legacy_fixtures.AimUiTests("test_accepted_nonactive_increment_is_done")
        runtime = legacy_fixtures.state("gate_b_pending")
        runtime.update(activeIncrementId="DI-002", currentRole="TDO")
        old._repo(self.repo, runtime)
        (self.repo / ".aim/increments/002-wip.md").write_text("# DI-002 — Next\n\nEpic: EPIC-TEST-001\n")
        (self.repo / ".aim/decisions/001-gate-e.md").write_text("# DI-001 Gate E — Accepted\n")
        board = build_board(self.repo)
        self.assertEqual(board["history"]["acceptedCount"], 1)
        self.assertEqual(board["productContext"]["counts"]["acceptedDeliveries"], 0)
        self.assertEqual(board["productContext"]["data"]["history"], [])
        self.fixture.accept()
        board = build_board(self.repo)
        self.assertEqual(board["history"]["acceptedCount"], 1)
        self.assertEqual(board["productContext"]["counts"]["acceptedDeliveries"], 1)
        self.assertEqual(board["productContext"]["counts"]["epics"], 2)
        self.assertEqual(board["deliveryData"]["epics"]["total"], 1)
        paths = [source["path"] for source in board["productContext"]["discussion"]["sources"]]
        self.assertNotIn(".aim/state.json", paths)
        self.assertNotIn(".aim/decisions/001-gate-e.md", paths)


if __name__ == "__main__":
    unittest.main()
