"""Requirements-derived oracles for independent cross-Epic Story delivery."""
from __future__ import annotations

import copy
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
from aim_stories import (FILE, StoryError, closure_preview, digest, execute, load,
                         project_story_board, validate_document)
from aim_ui import build_board
from aim_validator.schema_subset import unsupported_keywords


class StoryDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.token = None
        source = self.repo / "app.py"
        source.write_text("def recover(): return True\n")
        self.binding = {"path": "app.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        self.evidence = self.artifact("checks.md", "Independent expected result: both personas can complete their task.\n")
        self.plan_evidence = self.artifact("plan.md", "Files: product.py; boundaries: domain and view; check both personas and failures.\n")
        self.approval = self.artifact("user-approval.md", "Synthetic fixture of an explicit user's combined Gate A/B approval.\n")
        self.acceptance = self.artifact("user-acceptance.md", "Synthetic fixture of an explicit user's final acceptance.\n")
        ac = [{"id": "AC-1", "text": "The user can complete the described outcome."}]
        self.request = {
            "intents": [{"id": "INT-ACCESS", "statement": "Make the service usable by buyers and support."}],
            "epics": [{"id": "EPIC-BUY", "intentId": "INT-ACCESS", "title": "Buying", "outcome": "Buyers recover orders", "acceptanceCriteria": ac},
                      {"id": "EPIC-SUPPORT", "intentId": "INT-ACCESS", "title": "Support", "outcome": "Agents explain order state", "acceptanceCriteria": ac}],
            "stories": [
                {"id": "US-BUYER", "epicId": "EPIC-BUY", "title": "Recover an order", "persona": "Buyer", "need": "See recovery options", "benefit": "Finish buying", "priority": 1, "status": "ready", "acceptanceCriteria": ac},
                {"id": "US-AGENT", "epicId": "EPIC-SUPPORT", "title": "Explain order state", "persona": "Support agent", "need": "See an order timeline", "benefit": "Give a correct answer", "priority": 2, "status": "ready", "acceptanceCriteria": ac},
                {"id": "US-LATER", "epicId": "EPIC-BUY", "title": "Retain a draft", "persona": "Buyer", "need": "Save an unfinished order", "benefit": "Return another day", "priority": 3, "status": "draft", "acceptanceCriteria": ac},
            ],
        }
        self.mutate("import", self.request)

    def artifact(self, name, contents):
        path = self.repo / ".aim" / "evidence" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        return {"path": path.relative_to(self.repo).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def mutate(self, command, request):
        result = execute(self.repo, command, request, self.token)
        self.token = result["storeSha256"]
        self.document = result["document"]
        return result

    def plan(self):
        return self.mutate("plan", {"id": "DI-1", "title": "Recover and explain an order", "goal": "Help both sides resolve an interrupted purchase", "storyIds": ["US-BUYER", "US-AGENT"], "planEvidence": [self.plan_evidence]})

    def authority(self, scope, artifact=None):
        return {"kind": "user", **(artifact or self.approval), "scopeSha256": scope}

    def approve(self):
        self.plan()
        return self.mutate("approve", {"deliveryId": "DI-1", "authority": self.authority(self.document["deliveries"][0]["scopeSha256"])})

    def ready_for_acceptance(self):
        self.approve()
        self.mutate("review", {"deliveryId": "DI-1", "bindings": [self.binding]})
        self.mutate("validate", {"deliveryId": "DI-1", "evidence": [self.evidence]})
        self.mutate("acceptance", {"deliveryId": "DI-1", "evidence": [self.evidence], "criteria": self.criterion_evidence()})

    def criterion_evidence(self):
        return [{"storyId": story, "criterionId": "AC-1", "evidence": [self.evidence]} for story in ("US-BUYER", "US-AGENT")]

    def accept(self):
        self.ready_for_acceptance()
        return self.mutate("accept", {"deliveryId": "DI-1", "authority": self.authority(self.document["deliveries"][0]["acceptanceSha256"], self.acceptance)})

    def unchanged_failure(self, command, request, pattern):
        before = (self.repo / FILE).read_bytes()
        with self.assertRaisesRegex(StoryError, pattern):
            self.mutate(command, request)
        self.assertEqual(before, (self.repo / FILE).read_bytes())

    def test_complete_mixed_epic_loop_and_independent_epic_closure(self):
        original_state = b'{"epicId":"LEGACY","unknown":"keep exactly"}\n'
        (self.repo / ".aim/state.json").write_bytes(original_state)
        self.accept()
        board = project_story_board(self.repo)
        self.assertTrue(board["valid"])
        self.assertEqual([s["id"] for s in board["stories"]], ["US-BUYER", "US-AGENT", "US-LATER"])
        self.assertEqual([s["column"] for s in board["stories"]], ["done", "done", "backlog"])
        self.assertEqual([e["status"] for e in board["epics"]], ["open", "open"])
        self.assertEqual(board["stories"][0]["deliveryIds"], ["DI-1"])
        self.assertTrue(board["stories"][0]["evidence"][0]["url"].startswith("/api/evidence?path="))
        closure = {"epicId": "EPIC-SUPPORT", "criteria": [{"criterionId": "AC-1", "evidence": [self.evidence]}]}
        scope = closure_preview(self.repo, closure)["scopeSha256"]
        self.mutate("close-epic", {**closure, "authority": self.authority(scope, self.acceptance)})
        self.assertEqual(self.document["epics"][1]["status"], "closed")
        with self.assertRaisesRegex(StoryError, "Every Epic Story"):
            closure_preview(self.repo, {**closure, "epicId": "EPIC-BUY"})
        self.assertEqual(original_state, (self.repo / ".aim/state.json").read_bytes())

    def test_all_phase_transitions_move_only_selected_story_cards(self):
        self.plan()
        self.assertEqual([s["column"] for s in project_story_board(self.repo)["stories"]], ["ready", "ready", "backlog"])
        scope = self.document["deliveries"][0]["scopeSha256"]
        self.mutate("approve", {"deliveryId": "DI-1", "authority": self.authority(scope)})
        for phase, command, extra in [("in_progress", None, {}), ("review", "review", {"bindings": [self.binding]}), ("validation", "validate", {"evidence": [self.evidence]}), ("acceptance", "acceptance", {"evidence": [self.evidence], "criteria": self.criterion_evidence()})]:
            if command:
                self.mutate(command, {"deliveryId": "DI-1", **extra})
            self.assertEqual([s["column"] for s in project_story_board(self.repo)["stories"]], [phase, phase, "backlog"])

    def test_requires_exact_user_authority_and_prevents_gate_skips(self):
        self.plan()
        scope = self.document["deliveries"][0]["scopeSha256"]
        self.unchanged_failure("approve", {"deliveryId": "DI-1", "authority": self.authority("0" * 64)}, "stale or different")
        self.unchanged_failure("approve", {"deliveryId": "DI-1", "authority": {**self.authority(scope), "kind": "auto"}}, "user authority")
        self.unchanged_failure("accept", {"deliveryId": "DI-1", "authority": self.authority(scope)}, "Gate E")
        self.unchanged_failure("acceptance", {"deliveryId": "DI-1", "evidence": [self.evidence], "criteria": self.criterion_evidence()}, "TDO")

    def test_frozen_scope_and_overlapping_selection_are_rejected(self):
        self.plan()
        change = copy.deepcopy(self.request["stories"][0])
        change["need"] = "A changed need"
        self.unchanged_failure("refine", {"stories": [change]}, "frozen")
        self.unchanged_failure("plan", {"id": "DI-2", "title": "Other", "goal": "Other value", "storyIds": ["US-BUYER"], "planEvidence": [self.plan_evidence]}, "nonterminal")
        self.mutate("cancel", {"deliveryId": "DI-1", "reason": "Refine scope before approval"})
        change["acceptanceCriteria"] = [{"id": "AC-2", "text": "An improved criterion"}]
        self.mutate("refine", {"stories": [change]})
        self.assertEqual(self.document["stories"][0]["originalAcceptanceCriteria"][0]["id"], "AC-1")
        self.assertEqual(self.document["stories"][0]["acceptanceCriteria"][0]["id"], "AC-2")

    def test_acceptance_requires_complete_unique_criterion_evidence(self):
        self.approve()
        self.mutate("review", {"deliveryId": "DI-1", "bindings": [self.binding]})
        self.mutate("validate", {"deliveryId": "DI-1", "evidence": [self.evidence]})
        for evidence in (self.criterion_evidence()[:1], self.criterion_evidence()[:1] * 2,
                         [{**r, "criterionId": "AC-UNKNOWN"} for r in self.criterion_evidence()]):
            self.unchanged_failure("acceptance", {"deliveryId": "DI-1", "evidence": [self.evidence], "criteria": evidence}, "criterion|Criterion")

    def test_changed_evidence_cannot_be_accepted_and_rework_recovers(self):
        self.ready_for_acceptance()
        scope = self.document["deliveries"][0]["acceptanceSha256"]
        (self.repo / self.evidence["path"]).write_text("Changed result: now failing")
        self.unchanged_failure("accept", {"deliveryId": "DI-1", "authority": self.authority(scope)}, "Evidence changed")
        board = project_story_board(self.repo)
        self.assertFalse(board["valid"])
        self.assertEqual(board["stories"], [])
        self.mutate("rework", {"deliveryId": "DI-1", "reason": "Validation regression"})
        delivery = self.document["deliveries"][0]
        self.assertEqual(delivery["status"], "in_progress")
        self.assertNotIn("acceptanceSha256", delivery)
        self.assertNotIn("reviewEvidence", delivery)
        self.assertEqual(len(delivery["reworkHistory"]), 1)
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_changed_plan_or_user_decision_invalidates_evidence(self):
        self.ready_for_acceptance()
        (self.repo / self.plan_evidence["path"]).write_text("Changed implementation scope")
        self.unchanged_failure("accept", {"deliveryId": "DI-1", "authority": self.authority(self.document["deliveries"][0]["acceptanceSha256"])}, "Evidence changed")

    def test_changed_product_code_rejects_acceptance_and_rework_clears_bindings(self):
        self.ready_for_acceptance()
        (self.repo / "app.py").write_text("def recover(): return False\n")
        self.unchanged_failure("accept", {"deliveryId": "DI-1", "authority": self.authority(self.document["deliveries"][0]["acceptanceSha256"])}, "Evidence changed: app.py")
        self.mutate("rework", {"deliveryId": "DI-1", "reason": "A code change requires fresh review"})
        self.assertNotIn("productBindings", self.document["deliveries"][0])
        self.assertIn("productBindings", self.document["deliveries"][0]["reworkHistory"][0])
        updated = {"path": "app.py", "sha256": hashlib.sha256((self.repo / "app.py").read_bytes()).hexdigest()}
        self.mutate("review", {"deliveryId": "DI-1", "bindings": [updated]})
        self.assertEqual(self.document["deliveries"][0]["productBindings"], [updated])

    def test_later_product_changes_preserve_accepted_history_and_allow_next_delivery(self):
        self.accept()
        (self.repo / "app.py").write_text("def recover(): return 'new implementation'\n")
        self.assertTrue(project_story_board(self.repo)["valid"])
        later = {**self.request["stories"][2], "status": "ready"}
        self.mutate("refine", {"stories": [later]})
        self.mutate("plan", {"id": "DI-2", "title": "Retain draft", "goal": "Return tomorrow", "storyIds": ["US-LATER"], "planEvidence": [self.plan_evidence]})
        self.assertEqual(self.document["stories"][0]["status"], "done")
        self.assertEqual(self.document["deliveries"][1]["status"], "planned")

    def test_active_intent_cannot_drift_away_from_approved_scope(self):
        self.approve()
        self.unchanged_failure("refine", {"intents": [{"id": "INT-ACCESS", "statement": "An unrelated goal"}]}, "frozen")

    def test_accepted_history_allows_epic_and_intent_learning_without_reusing_closure(self):
        self.accept()
        historical = copy.deepcopy(self.document["deliveries"][0])
        closure = {"epicId": "EPIC-SUPPORT", "criteria": [{"criterionId": "AC-1", "evidence": [self.evidence]}]}
        old_closure_hash = closure_preview(self.repo, closure)["scopeSha256"]
        revised_epic = {**self.request["epics"][1], "outcome": "Explain order state and help with refunds",
                        "acceptanceCriteria": [{"id": "AC-1", "text": "Support can explain order and refund state."}]}
        revised_intent = {"id": "INT-ACCESS", "statement": "Help buyers and support resolve purchase and refund problems."}
        self.mutate("refine", {"intents": [revised_intent], "epics": [revised_epic]})
        self.assertEqual(self.document["deliveries"][0], historical)
        self.assertEqual(self.document["epics"][1]["originalAcceptanceCriteria"], self.request["epics"][1]["acceptanceCriteria"])
        self.unchanged_failure("close-epic", {**closure, "authority": self.authority(old_closure_hash)}, "stale or different scope")
        learned_story = {**self.request["stories"][1], "id": "US-REFUND", "title": "Explain a refund", "need": "See refund state"}
        self.mutate("import", {"stories": [learned_story]})
        self.mutate("plan", {"id": "DI-2", "title": "Explain refunds", "goal": "Help users understand refunds", "storyIds": ["US-REFUND"], "planEvidence": [self.plan_evidence]})
        self.assertEqual(self.document["deliveries"][0], historical)
        self.assertEqual(self.document["deliveries"][1]["epics"][0]["revision"], 2)
        self.assertEqual(self.document["deliveries"][1]["intents"][0]["statement"], revised_intent["statement"])
        self.assertEqual(self.document["deliveries"][0]["intents"][0]["statement"], self.request["intents"][0]["statement"])
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_epic_outcome_class_and_non_goals_are_normalized_and_scope_bound(self):
        self.assertEqual(self.document["epics"][0]["outcomeClass"], "Product")
        self.assertEqual(self.document["epics"][0]["nonGoals"], [])
        pilot = {**self.request["epics"][0], "outcomeClass": "Pilot", "nonGoals": ["General availability"]}
        self.mutate("refine", {"epics": [pilot]})
        revision = self.document["epics"][0]["revision"]
        self.mutate("import", {"epics": [self.request["epics"][0]]})
        self.assertEqual(self.document["epics"][0]["revision"], revision)
        self.assertEqual(self.document["epics"][0]["outcomeClass"], "Pilot")
        self.assertEqual(self.document["epics"][0]["nonGoals"], ["General availability"])
        self.unchanged_failure("refine", {"epics": [{**pilot, "outcomeClass": "Demo"}]}, "outcomeClass")
        self.unchanged_failure("refine", {"epics": [{**pilot, "nonGoals": [" "]}]}, "nonGoals")
        self.plan()
        snapshot = self.document["deliveries"][0]["epics"][0]
        self.assertEqual(snapshot["outcomeClass"], "Pilot")
        self.assertEqual(snapshot["nonGoals"], ["General availability"])

    def test_blocked_stale_review_validation_and_acceptance_can_rework(self):
        self.approve()
        for phase in ("review", "validation", "acceptance"):
            with self.subTest(phase=phase):
                binding = {"path": "app.py", "sha256": hashlib.sha256((self.repo / "app.py").read_bytes()).hexdigest()}
                self.mutate("review", {"deliveryId": "DI-1", "bindings": [binding]})
                if phase in {"validation", "acceptance"}:
                    self.mutate("validate", {"deliveryId": "DI-1", "evidence": [self.evidence]})
                if phase == "acceptance":
                    self.mutate("acceptance", {"deliveryId": "DI-1", "evidence": [self.evidence], "criteria": self.criterion_evidence()})
                self.mutate("block", {"deliveryId": "DI-1", "reason": "Found a defect"})
                (self.repo / "app.py").write_text("def recover(): return " + repr(phase) + "\n")
                self.unchanged_failure("unblock", {"deliveryId": "DI-1", "reason": "Code fixed"}, "Evidence changed")
                self.mutate("rework", {"deliveryId": "DI-1", "reason": "Review the fix again"})
                delivery = self.document["deliveries"][0]
                self.assertEqual(delivery["status"], "in_progress")
                self.assertNotIn("blockedFrom", delivery)
                self.assertNotIn("productBindings", delivery)
                self.assertNotIn("acceptanceSha256", delivery)
                self.assertEqual(delivery["reworkHistory"][-1]["from"], phase)
                self.assertEqual(delivery["reworkHistory"][-1]["blockedReason"], "Found a defect")
                self.assertEqual(self.document["stories"][0]["status"], "in_progress")
                self.assertTrue(project_story_board(self.repo)["valid"])

    def test_self_referential_ledger_aliases_fail_before_any_write(self):
        for alias in (".aim/./product-backlog.json", ".aim//product-backlog.json"):
            self.unchanged_failure("plan", {"id": "DI-1", "title": "Plan", "goal": "Goal", "storyIds": ["US-BUYER"],
                                           "planEvidence": [{"path": alias, "sha256": self.token}]}, "canonical")
        self.approve()
        for alias in ("./.aim/product-backlog.json", ".aim/./product-backlog.json", ".aim//product-backlog.json", FILE):
            self.unchanged_failure("review", {"deliveryId": "DI-1", "bindings": [{"path": alias, "sha256": self.token}]}, "canonical|independent artifact")
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_case_insensitive_ledger_aliases_fail_before_any_write(self):
        alias = self.repo / ".aim/PRODUCT-BACKLOG.JSON"
        if not alias.exists() or not alias.samefile(self.repo / FILE):
            self.skipTest("Filesystem is case sensitive")
        self.unchanged_failure("plan", {"id": "DI-1", "title": "Plan", "goal": "Goal", "storyIds": ["US-BUYER"],
                                       "planEvidence": [{"path": ".aim/PRODUCT-BACKLOG.JSON", "sha256": self.token}]}, "file identity")
        self.approve()
        for path in (".aim/PRODUCT-BACKLOG.JSON", ".AIM/product-backlog.json"):
            self.unchanged_failure("review", {"deliveryId": "DI-1", "bindings": [{"path": path, "sha256": self.token}]}, "file identity")
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_hardlink_ledger_aliases_fail_before_any_write(self):
        alias = self.repo / ".aim/evidence/ledger-alias.json"
        os.link(self.repo / FILE, alias)
        reference = {"path": alias.relative_to(self.repo).as_posix(), "sha256": self.token}
        self.unchanged_failure("plan", {"id": "DI-1", "title": "Plan", "goal": "Goal", "storyIds": ["US-BUYER"],
                                       "planEvidence": [reference]}, "file identity")
        self.approve()
        # Atomic commits replaced the original inode; bind an alias to the
        # current ledger again to test product source bindings independently.
        alias.unlink()
        os.link(self.repo / FILE, alias)
        self.unchanged_failure("review", {"deliveryId": "DI-1", "bindings": [{**reference, "sha256": self.token}]}, "file identity")
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_lifecycle_label_alone_cannot_manufacture_acceptance(self):
        self.ready_for_acceptance()
        forged = copy.deepcopy(self.document)
        forged["deliveries"][0]["status"] = "accepted"
        for story in forged["stories"][:2]:
            story["status"] = "done"
        with self.assertRaisesRegex(StoryError, "user acceptance"):
            validate_document(forged)

    def test_confirmed_commit_returns_snapshot_without_followup_read(self):
        original = load
        reads = []

        def only_precommit(*args, **kwargs):
            reads.append(True)
            if len(reads) > 1:
                raise OSError("post-commit read unavailable")
            return original(*args, **kwargs)

        with patch("aim_stories.load", side_effect=only_precommit):
            result = self.mutate("refine", {"stories": []})
        self.assertEqual(len(reads), 1)
        self.assertEqual(result["storeSha256"], hashlib.sha256((self.repo / FILE).read_bytes()).hexdigest())

    def test_block_resume_does_not_discard_original_phase(self):
        self.approve()
        self.mutate("review", {"deliveryId": "DI-1", "bindings": [self.binding]})
        self.mutate("block", {"deliveryId": "DI-1", "reason": "Need the sample account"})
        story = project_story_board(self.repo)["stories"][0]
        self.assertEqual(story["column"], "review")
        self.assertEqual(story["attention"], "Need the sample account")
        self.unchanged_failure("validate", {"deliveryId": "DI-1", "evidence": [self.evidence]}, "Reviewer")
        self.mutate("unblock", {"deliveryId": "DI-1", "reason": "Account is available"})
        self.assertEqual(self.document["deliveries"][0]["status"], "review")

    def test_stale_revision_and_atomic_write_failure_preserve_existing_bytes(self):
        before = (self.repo / FILE).read_bytes()
        with self.assertRaisesRegex(StoryError, "Stale"):
            execute(self.repo, "refine", {"stories": []}, "0" * 64)
        self.assertEqual((self.repo / FILE).read_bytes(), before)
        with patch("aim_stories.os.replace", side_effect=OSError("disk unavailable")):
            with self.assertRaisesRegex(OSError, "disk unavailable"):
                self.mutate("refine", {"stories": []})
        self.assertEqual((self.repo / FILE).read_bytes(), before)
        self.assertEqual(list((self.repo / ".aim").glob(".product-backlog-*")), [])

    def test_symlink_evidence_and_escape_are_rejected(self):
        linked = self.repo / ".aim/evidence/link.md"
        linked.symlink_to(self.repo / self.plan_evidence["path"])
        for reference in ({**self.plan_evidence, "path": ".aim/evidence/link.md"},
                          {**self.plan_evidence, "path": ".aim/../../outside"},
                          {**self.plan_evidence, "path": FILE}):
            self.unchanged_failure("plan", {"id": "DI-1", "title": "Plan", "goal": "Goal", "storyIds": ["US-BUYER"], "planEvidence": [reference]}, "evidence|Evidence")

    def test_invalid_relations_and_authority_fields_never_partially_import(self):
        for change in ({**self.request["stories"][0], "epicId": "EPIC-MISSING"},
                       {**self.request["stories"][0], "status": "done"},
                       {**self.request["stories"][0], "priority": 0},
                       {**self.request["stories"][0], "gate": "Gate E"}):
            self.unchanged_failure("refine", {"stories": [change]}, "unknown Epic|runtime|positive|Unsupported")

    def test_schema_and_public_projection_share_the_validated_contract(self):
        schema = json.loads((ROOT / "schemas/aim-product-backlog.schema.json").read_text())
        self.assertEqual(unsupported_keywords(schema), [])
        validate_document(self.document)
        board = build_board(self.repo)
        self.assertEqual(len(board["storyBoard"]["stories"]), 3)
        self.assertEqual(board["epics"], [])
        self.assertFalse((self.repo / ".aim/state.json").exists())

    def test_legacy_only_and_invalid_store_never_manufacture_stories(self):
        (self.repo / FILE).unlink()
        self.assertEqual(project_story_board(self.repo)["stories"], [])
        (self.repo / FILE).write_text('{"stories":[{"id":"US-FAKE","status":"done"}]}')
        result = project_story_board(self.repo)
        self.assertFalse(result["valid"])
        self.assertEqual(result["stories"], [])

    def test_cli_uses_same_store_and_reports_digest_next_step(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/aim_stories.py"), "--repo", str(self.repo), "status"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["storeSha256"], self.token)
        self.assertEqual(result["nextStep"], [{"operation": "plan"}])
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/aim_stories.py"), "--repo", str(self.repo), "refine", "--expected-sha256", self.token], input=json.dumps({"stories": []}), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotEqual(json.loads(proc.stdout)["storeSha256"], self.token)


if __name__ == "__main__":
    unittest.main()
