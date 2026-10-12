"""Exact-scope legacy removal preserving current evidence and lock identities."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aim_legacy_cleanup as cleanup
from aim_runtime_lock import runtime_lock
from aim_stories import load
import test_aim_stories as story_fixtures


class LegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.fixture = story_fixtures.StoryDeliveryTests("test_complete_mixed_epic_loop_and_independent_epic_closure")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo
        self.put(".aim/state.json", '{"epicId":"EPIC-ROOT"}')
        self.put(".aim/epic.md", "Root legacy Epic")
        self.put(".aim/increments/001.md", "Root increment")
        self.put(".aim/reviews/review-001.md", "Old review")
        for workspace in ("portfolio/EPIC-OLD", "workspaces/old", "runs/declared"):
            self.put(f".aim/{workspace}/state.json", '{"epicId":"EPIC-OLD"}')
            self.put(f".aim/{workspace}/epic.md", "An old Epic")
            self.put(f".aim/{workspace}/decisions/old.md", "Old decision")
        self.put(".aim/ui-portfolio.json", json.dumps({"portfolioVersion": "1.0", "workspaces": [
            {"path": "."}, {"path": "portfolio/EPIC-OLD"}, {"path": "workspaces/old"}, {"path": "runs/declared"}]}))
        self.put(".aim/archive/state-OLD.json", '{}')
        self.put(".aim/archive/2026-01-01-legacy-old/state.json", '{}')
        self.put(".aim/archive/2026-01-01-legacy-old/decisions/old.md", "Archived decision")
        self.put(".aim/archive/personal-note.md", "Keep unknown archive files")
        self.put(".aim/analysis/current-note.md", "Keep all current analysis")
        self.put(".aim/private.txt", "Unknown owner: keep")
        plan_ref = self.put(".aim/portfolio/EPIC-OLD/increments/shared.md", "Current plan still cites this old workspace")
        approval_ref = self.put(".aim/portfolio/EPIC-OLD/decisions/shared.md", "Current approval still cites this old workspace")
        self.fixture.mutate("plan", {"id": "DI-1", "title": "Current delivery", "goal": "Current product", "storyIds": ["US-BUYER"], "planEvidence": [plan_ref]})
        scope = self.fixture.document["deliveries"][0]["scopeSha256"]
        self.fixture.mutate("approve", {"deliveryId": "DI-1", "authority": {"kind": "user", **approval_ref, "scopeSha256": scope}})
        self.shared = [plan_ref["path"], approval_ref["path"]]

    def put(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def snapshot(self):
        return {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}

    def test_preview_is_read_only_exact_and_excludes_current_shared_evidence(self):
        before = self.snapshot()
        plan = cleanup.preview(self.repo)
        self.assertEqual(before, self.snapshot())
        paths = {record["path"] for record in plan["files"]}
        self.assertIn(".aim/state.json", paths)
        self.assertIn(".aim/runs/declared/decisions/old.md", paths)
        self.assertIn(".aim/archive/2026-01-01-legacy-old/state.json", paths)
        for shared in self.shared:
            self.assertNotIn(shared, paths)
            self.assertIn(shared, plan["retainedCurrentRefs"])
        self.assertNotIn(".aim/product-backlog.json", paths)
        self.assertNotIn(".aim/analysis/current-note.md", paths)
        self.assertIn(".aim/private.txt", plan["retainedUnknown"])
        self.assertIn(".aim/archive/personal-note.md", plan["retainedUnknown"])
        self.assertEqual(plan["totalBytes"], sum(len(before[path]) for path in paths))
        self.assertEqual(plan["inventorySha256"], cleanup.preview(self.repo)["inventorySha256"])
        self.assertFalse((self.repo / ".aim/portfolio/EPIC-OLD/.runtime.lock").exists())

    def test_apply_preserves_current_ledger_references_analysis_and_permanent_locks(self):
        ledger_before = (self.repo / ".aim/product-backlog.json").read_bytes()
        root_lock_inode = (self.repo / ".aim/.runtime.lock").stat().st_ino
        child = self.repo / ".aim/portfolio/EPIC-OLD/state.json"
        with runtime_lock(child):
            child_lock_inode = child.with_name(".runtime.lock").stat().st_ino
        plan = cleanup.preview(self.repo)
        result = cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["removedFileCount"], plan["totalFiles"])
        self.assertEqual(result["removedBytes"], plan["totalBytes"])
        self.assertEqual(result["errors"], [])
        self.assertEqual((self.repo / ".aim/product-backlog.json").read_bytes(), ledger_before)
        self.assertEqual((self.repo / ".aim/.runtime.lock").stat().st_ino, root_lock_inode)
        self.assertEqual(child.with_name(".runtime.lock").stat().st_ino, child_lock_inode)
        for shared in self.shared:
            self.assertTrue((self.repo / shared).is_file())
        self.assertTrue((self.repo / ".aim/analysis/current-note.md").is_file())
        self.assertTrue((self.repo / ".aim/archive/personal-note.md").is_file())
        self.assertFalse((self.repo / ".aim/portfolio/EPIC-OLD/state.json").exists())
        load(self.repo)  # Product evidence must still verify after cleanup.
        self.assertFalse(cleanup.detect(self.repo)["legacyDetected"])
        fresh = cleanup.preview(self.repo)
        self.assertFalse(fresh["legacyDetected"])
        again = cleanup.apply(self.repo, fresh["inventorySha256"], confirm=True)
        self.assertEqual(again["removedFileCount"], 0)

    def test_confirmation_and_changed_inventory_reject_without_deletion(self):
        plan = cleanup.preview(self.repo)
        before = self.snapshot()
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "confirmation"):
            cleanup.apply(self.repo, plan["inventorySha256"])
        self.assertEqual(before, self.snapshot())
        self.put(".aim/reviews/arrived.md", "New legacy evidence")
        before = self.snapshot()
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "inventory changed"):
            cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        self.assertEqual(before, self.snapshot())

    def test_current_ledger_change_invalidates_previous_scope(self):
        plan = cleanup.preview(self.repo)
        self.fixture.mutate("import", {"stories": []})
        before = self.snapshot()
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "inventory changed"):
            cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        self.assertEqual(before, self.snapshot())

    def test_busy_workspace_lock_prevents_any_legacy_deletion(self):
        plan = cleanup.preview(self.repo)
        before = self.snapshot()
        with runtime_lock(self.repo / ".aim/workspaces/old/state.json"):
            with self.assertRaises(OSError):
                cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        for relative, contents in before.items():
            self.assertEqual((self.repo / relative).read_bytes(), contents)

    def test_partial_failure_retains_discovery_and_can_resume_only_with_fresh_preview(self):
        plan = cleanup.preview(self.repo)
        original = cleanup._remove_file
        count = 0

        def fail_second(repo, record):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Injected unlink failure")
            return original(repo, record)

        with patch("aim_legacy_cleanup._remove_file", side_effect=fail_second):
            result = cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["removedFileCount"], 1)
        self.assertIn("fresh preview", result["nextAction"])
        self.assertTrue((self.repo / ".aim/ui-portfolio.json").exists())
        self.assertTrue((self.repo / ".aim/portfolio/EPIC-OLD/state.json").exists())
        self.assertTrue(cleanup.detect(self.repo)["legacyDetected"])
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "inventory changed"):
            cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        fresh = cleanup.preview(self.repo)
        finished = cleanup.apply(self.repo, fresh["inventorySha256"], confirm=True)
        self.assertEqual(finished["status"], "complete")
        self.assertFalse(cleanup.detect(self.repo)["legacyDetected"])

    def test_missing_state_and_catalog_still_discover_known_child_remnants(self):
        (self.repo / ".aim/ui-portfolio.json").unlink()
        (self.repo / ".aim/portfolio/EPIC-OLD/state.json").unlink()
        plan = cleanup.preview(self.repo)
        self.assertIn(".aim/portfolio/EPIC-OLD/decisions/old.md", {item["path"] for item in plan["files"]})
        self.assertTrue(cleanup.detect(self.repo)["legacyDetected"])

    def test_corrupt_product_and_unsafe_catalog_fail_closed(self):
        ledger = self.repo / ".aim/product-backlog.json"
        original = ledger.read_bytes()
        ledger.write_text('{"invalid":true}')
        before = self.snapshot()
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "must validate"):
            cleanup.preview(self.repo)
        self.assertEqual(before, self.snapshot())
        ledger.write_bytes(original)
        self.put(".aim/ui-portfolio.json", json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "../outside"}]}))
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "Unsafe"):
            cleanup.preview(self.repo)
        detected = cleanup.detect(self.repo)
        self.assertTrue(detected["legacyDetected"])
        self.assertTrue(detected["warnings"])

    def test_symlink_and_special_files_are_rejected_before_deletion(self):
        outside = self.repo / "outside.txt"
        outside.write_text("Never delete")
        linked = self.repo / ".aim/reviews/link.txt"
        linked.symlink_to(outside)
        with self.assertRaisesRegex(cleanup.LegacyCleanupError, "links"):
            cleanup.preview(self.repo)
        linked.unlink()
        self.assertEqual(outside.read_text(), "Never delete")
        if hasattr(os, "mkfifo"):
            os.mkfifo(linked)
            with self.assertRaisesRegex(cleanup.LegacyCleanupError, "special"):
                cleanup.preview(self.repo)

    def test_nested_json_reference_closure_and_hardlinks_are_preserved(self):
        nested = self.put(".aim/reviews/still-current.md", "Nested current evidence")
        report = self.put(".aim/reviews/current-report.json", json.dumps({"sources": [nested]}))
        alias = self.repo / ".aim/reviews/hardlink.md"
        os.link(self.repo / self.shared[0], alias)
        # Add the report to a valid current plan while retaining all scope data.
        self.fixture.mutate("review", {"deliveryId": "DI-1", "bindings": [self.fixture.binding]})
        self.fixture.mutate("validate", {"deliveryId": "DI-1", "evidence": [report]})
        plan = cleanup.preview(self.repo)
        paths = {item["path"] for item in plan["files"]}
        for path in (nested["path"], report["path"], alias.relative_to(self.repo).as_posix()):
            self.assertNotIn(path, paths)
            self.assertIn(path, plan["retainedCurrentRefs"])
        result = cleanup.apply(self.repo, plan["inventorySha256"], confirm=True)
        self.assertEqual(result["status"], "complete")
        self.assertFalse(cleanup.preview(self.repo)["legacyDetected"])
        self.assertFalse(cleanup.detect(self.repo)["legacyDetected"])

    def test_detect_never_hashes_or_validates_full_product_evidence(self):
        with patch("aim_legacy_cleanup._record", side_effect=AssertionError("No hashing during detection")), \
             patch("aim_legacy_cleanup.load_product", side_effect=AssertionError("No full validation during detection")):
            result = cleanup.detect(self.repo)
        self.assertTrue(result["legacyDetected"])
        self.assertEqual(result["workspaceCount"], 4)

    def test_empty_repository_preview_and_detect_create_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self.assertFalse(cleanup.preview(repo)["legacyDetected"])
            self.assertFalse(cleanup.detect(repo)["legacyDetected"])
            self.assertEqual(list(repo.iterdir()), [])

    def test_cli_preview_and_unconfirmed_apply_do_not_delete(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/aim_legacy_cleanup.py"), "--repo", str(self.repo), "preview"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plan = json.loads(proc.stdout)
        before = self.snapshot()
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/aim_legacy_cleanup.py"), "--repo", str(self.repo), "apply", "--expected-sha256", plan["inventorySha256"]], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stderr)["status"], "rejected")
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
