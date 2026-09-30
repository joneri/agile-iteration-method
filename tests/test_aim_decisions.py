"""Approval behavior, real subprocess CLI, recovery, and concurrent decisions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aim_decisions as decisions
import aim_runtime_contract as runtime
import test_aim_runtime_contract as fixtures
from aim_actions import proposal_action, validate_action_envelope, AimActionError

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = fixtures.AUTHORITY_PATH


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo, self.state_path = fixtures.AimRuntimeContractTests()._repo(Path(self.directory.name))
        self.workspace = self.state_path.parent
        self.audit_path = Path(fixtures.AimRuntimeContractTests()._closure_evidence(self.repo))
        audit = json.loads((self.repo / self.audit_path).read_text())
        audit.pop("authorityEvidence")
        audit.pop("decisionAuthority")
        (self.repo / self.audit_path).write_text(json.dumps(audit))
        (self.workspace / "decisions/epic-closure-authority.md").unlink()
        (self.workspace / "decisions/001-gate-e.md").unlink()
        (self.repo / "product.py").write_text("print('product')\n")
        state = json.loads(self.state_path.read_text())
        state.update(epicStatus="po_approval_pending", activeIncrementId="DI-001", currentRole="PO", lastGatePassed="Gate D")
        for key in ("previousIncrementId", "previousIncrementStatus", "gateEAcceptance"):
            state.pop(key)
        self.state_path.write_text(json.dumps(state))
        self.spec = {
            "proposalId": "delivery-1", "kind": "delivery", "incrementId": "DI-001",
            "summary": "Export is ready; all Epic requirements are verified.",
            "scope": "Export the selected data.", "remainingWork": "None.", "risk": "Local files only.",
            "recommendation": "close", "bindingPaths": ["product.py"],
            "closureEvidence": self.audit_path.relative_to(self.workspace.relative_to(self.repo)).as_posix(),
            "evidence": audit["acceptanceCriteria"][0]["evidence"],
        }

    def proposal(self):
        proposal = decisions.prepare(self.repo, AUTHORITY, self.spec)
        decisions.publish(self.repo, AUTHORITY, proposal)
        return proposal

    def response(self, proposal, selected=None, operation="op-1"):
        return {"operationId": operation, "proposalSha256": decisions.digest(proposal),
                "decisions": selected or proposal["decisions"], "source": "test user message 123",
                "text": "Approve the presented decisions", "updatedAt": "2026-09-30T09:00:00Z"}

    def state(self):
        return json.loads(self.state_path.read_text())

    def test_readiness_is_read_only_and_authority_still_required_for_legacy_close(self):
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        result = decisions.closure_readiness(self.repo, AUTHORITY, self.spec["closureEvidence"])
        self.assertTrue(result["ready"])
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        with self.assertRaises(runtime.RuntimeTransitionError):
            runtime.plan_epic_closure(self.repo, authority_state_path=AUTHORITY, closure_evidence_path=str(self.audit_path), updated_at="now")

    def test_accept_and_close_with_one_response_and_safe_replay(self):
        proposal = self.proposal()
        response = self.response(proposal)
        self.assertEqual(decisions.apply(self.repo, AUTHORITY, response)["result"], "applied")
        self.assertEqual(self.state()["epicStatus"], "epic_complete")
        self.assertEqual(runtime.epic_closure_evidence(self.repo, self.workspace, self.state())[1], [])
        before = self.state_path.read_bytes()
        self.assertEqual(decisions.apply(self.repo, AUTHORITY, response)["result"], "already_applied")
        self.assertEqual(before, self.state_path.read_bytes())
        with self.assertRaisesRegex(runtime.RuntimeTransitionError, "reused"):
            decisions.apply(self.repo, AUTHORITY, {**response, "text": "Different response"})

    def test_partial_acceptance_then_separate_closure_preserves_acceptance(self):
        proposal = self.proposal()
        decisions.apply(self.repo, AUTHORITY, self.response(proposal, ["accept_increment"]))
        self.assertEqual(self.state()["epicStatus"], "done_increment_accepted")
        acceptance = self.state()["gateEAcceptance"]
        self.spec.update(kind="disposition", proposalId="close-2")
        second = self.proposal()
        decisions.apply(self.repo, AUTHORITY, self.response(second, operation="op-2"))
        self.assertEqual(self.state()["gateEAcceptance"], acceptance)
        self.assertEqual(len(self.state()["decisionReceipts"]), 2)

    def test_continuation_plans_without_another_start_request(self):
        self.spec.update(recommendation="continue", remainingWork="Plan filtering for export.")
        proposal = self.proposal()
        result = decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        self.assertEqual(result["next"]["operation"], "plan_increment")
        self.assertIn("Approve the next plan", result["next"]["nextDecision"])
        preview = runtime.plan_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="later")
        runtime.apply_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="later", expected_state_sha256=preview["sourceStateSha256"])
        self.assertFalse(decisions.next_step(self.repo, AUTHORITY)["canExecute"])
        self.assertNotIn("epicDisposition", self.state())

    def test_direction_and_first_plan_are_one_decision(self):
        state = self.state()
        state.update(epicStatus="gate_a_pending", activeIncrementId=None, plannedIncrementId="DI-001", currentRole="PO", lastGatePassed=None)
        self.state_path.write_text(json.dumps(state))
        self.spec.update(kind="start", proposalId="start-1")
        proposal = self.proposal()
        self.assertEqual(proposal["decisions"], ["approve_epic", "approve_increment"])
        with self.assertRaises(runtime.RuntimeTransitionError):
            decisions.apply(self.repo, AUTHORITY, self.response(proposal, ["approve_increment"]))
        decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        self.assertEqual(self.state()["epicStatus"], "increment_in_progress")
        self.assertEqual(self.state()["lastGatePassed"], "Gate B")

    def test_stale_product_and_proofs_require_reverification(self):
        for relative in ("product.py", str(self.workspace.relative_to(self.repo) / "evidence/black-box.json")):
            with self.subTest(relative=relative):
                proposal = self.proposal()
                target = self.repo / relative
                original = target.read_bytes()
                target.write_bytes(original + b" ")
                before = self.state_path.read_bytes()
                with self.assertRaises(ValueError):
                    decisions.apply(self.repo, AUTHORITY, self.response(proposal))
                self.assertEqual(before, self.state_path.read_bytes())
                self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "blocked")
                target.write_bytes(original)

    def test_missing_or_failed_epic_criterion_blocks_readiness(self):
        path = self.repo / self.audit_path
        value = json.loads(path.read_text())
        value["acceptanceCriteria"][0]["status"] = "failed"
        path.write_text(json.dumps(value))
        self.assertFalse(decisions.closure_readiness(self.repo, AUTHORITY, self.spec["closureEvidence"])["ready"])
        with self.assertRaises(runtime.RuntimeTransitionError):
            self.proposal()

    def test_invalid_authority_provenance_does_not_write(self):
        proposal = self.proposal()
        for key in ("source", "text", "decisions"):
            response = self.response(proposal)
            response.pop(key)
            before = self.state_path.read_bytes()
            with self.assertRaises(ValueError):
                decisions.apply(self.repo, AUTHORITY, response)
            self.assertEqual(before, self.state_path.read_bytes())

    def test_each_staging_failure_can_retry_same_response(self):
        original = decisions._immutable
        for failure in range(3):
            with self.subTest(failure=failure):
                proposal = self.proposal()
                response = self.response(proposal)
                calls = [0]
                def fail_after_write(path, payload):
                    original(path, payload)
                    calls[0] += 1
                    if calls[0] == failure + 1:
                        raise OSError("simulated interruption")
                before = self.state_path.read_bytes()
                with patch.object(decisions, "_immutable", side_effect=fail_after_write):
                    with self.assertRaises(OSError):
                        decisions.apply(self.repo, AUTHORITY, response)
                self.assertEqual(before, self.state_path.read_bytes())
        decisions.apply(self.repo, AUTHORITY, response)
        self.assertEqual(self.state()["epicStatus"], "epic_complete")

    def test_interruption_after_state_commit_does_not_duplicate_decisions(self):
        proposal = self.proposal()
        response = self.response(proposal)
        original = runtime._atomic_replace
        def fail_after_commit(path, payload):
            original(path, payload)
            raise OSError("lost acknowledgement")
        with patch.object(runtime, "_atomic_replace", side_effect=fail_after_commit):
            with self.assertRaises(OSError):
                decisions.apply(self.repo, AUTHORITY, response)
        self.assertEqual(decisions.apply(self.repo, AUTHORITY, response)["result"], "already_applied")
        self.assertEqual(len(self.state()["decisionReceipts"]), 1)

    def test_simultaneous_change_cannot_overwrite_committed_approval(self):
        proposal = self.proposal()
        response = self.response(proposal)
        entered, release = threading.Event(), threading.Event()
        errors = []
        original = decisions._immutable
        def delayed(path, payload):
            entered.set()
            self.assertTrue(release.wait(5))
            original(path, payload)
        def worker():
            try:
                decisions.apply(self.repo, AUTHORITY, response)
            except Exception as exc:
                errors.append(exc)
        with patch.object(decisions, "_immutable", side_effect=delayed):
            thread = threading.Thread(target=worker)
            thread.start()
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaises(OSError):
                    decisions.request_change(self.repo, AUTHORITY, decisions.digest(proposal), "Change scope")
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(errors, [])
        with self.assertRaises(ValueError):
            decisions.request_change(self.repo, AUTHORITY, decisions.digest(proposal), "Change scope")
        self.assertEqual(self.state()["epicStatus"], "epic_complete")

    def test_change_first_invalidates_pending_approval(self):
        proposal = self.proposal()
        decisions.request_change(self.repo, AUTHORITY, decisions.digest(proposal), "Keep the Epic open and change export")
        with self.assertRaises(ValueError):
            decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "revise_proposal")

    def test_pause_and_blocker_override_pending_decisions_and_changes(self):
        proposal = self.proposal()
        pending = self.state()
        decisions.request_change(self.repo, AUTHORITY, decisions.digest(proposal), "Revise export columns")
        changed = self.state()
        for source in (pending, changed):
            for status in ("blocked", "epic_paused"):
                for mode in ("Strict", "Auto"):
                    with self.subTest(status=status, mode=mode, change="decisionChange" in source):
                        state = {**source, "epicStatus": status, "mode": mode}
                        self.state_path.write_text(json.dumps(state))
                        before = self.state_path.read_bytes()
                        result = decisions.next_step(self.repo, AUTHORITY)
                        self.assertEqual(result["operation"], "blocked")
                        self.assertFalse(result["canExecute"])
                        self.assertIn(status, result["summary"])
                        self.assertEqual(before, self.state_path.read_bytes())
        self.state_path.write_text(json.dumps(changed))
        self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "revise_proposal")

    def test_accepted_split_is_actionable_after_reload_without_reapproval(self):
        self.spec.update(recommendation="split", remainingWork="Create a separate Epic for the newly requested PDF export.")
        proposal = self.proposal()
        result = decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        expected = result["next"]
        self.assertEqual(expected["operation"], "split_scope")
        self.assertTrue(expected["canExecute"])
        self.assertIn(self.spec["remainingWork"], expected["summary"])
        self.assertIn("original Epic", expected["nextDecision"])
        self.assertIn("implementation", expected["nextDecision"])
        self.assertEqual(self.state()["epicStatus"], "done_increment_accepted")
        before = self.state_path.read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/aim_decisions.py"), "status",
                                 "--repo", str(self.repo), "--authority-state-path", AUTHORITY],
                                text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(before, self.state_path.read_bytes())
        self.spec.update(kind="disposition", proposalId="continue-after-split", recommendation="continue",
                         remainingWork="Plan remaining original export requirements.")
        next_proposal = self.proposal()
        self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "present_decision")
        result = decisions.apply(self.repo, AUTHORITY, self.response(next_proposal, operation="after-split"))
        self.assertEqual(result["next"]["operation"], "plan_increment")
        self.assertEqual(self.state()["epicDisposition"], "continue")

    def test_accepting_only_increment_does_not_authorize_offered_split(self):
        self.spec.update(recommendation="split", remainingWork="Separate new PDF export scope.")
        proposal = self.proposal()
        result = decisions.apply(self.repo, AUTHORITY, self.response(proposal, ["accept_increment"]))
        self.assertNotIn("epicDisposition", self.state())
        self.assertEqual(result["next"]["operation"], "present_decision")
        self.assertFalse(result["next"]["canExecute"])

    def test_v13_is_explicit_and_legacy_cannot_expand_authority(self):
        proposal = self.proposal()
        envelope = proposal_action("approve", proposal, self.state(), proposal["decisions"])
        validate_action_envelope(envelope)
        with self.assertRaises(AimActionError):
            validate_action_envelope({**envelope, "actionVersion": "1.2"})

    def test_cli_status_is_read_only_and_apply_works_without_ui(self):
        proposal = self.proposal()
        response_path = self.repo / "response.json"
        response_path.write_text(json.dumps(self.response(proposal)))
        command = [sys.executable, str(ROOT / "scripts/aim_decisions.py"), "status", "--repo", str(self.repo), "--authority-state-path", AUTHORITY]
        before = self.state_path.read_bytes()
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["operation"], "present_decision")
        self.assertEqual(before, self.state_path.read_bytes())
        command[2] = "apply"
        result = subprocess.run(command + ["--input", str(response_path)], text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["result"], "applied")

    def cli(self, command, value=None):
        """Each call starts a fresh process; user responses are synthetic fixtures."""
        argv = [sys.executable, str(ROOT / "scripts/aim_decisions.py"), command,
                "--repo", str(self.repo), "--authority-state-path", AUTHORITY]
        if value is not None:
            path = self.repo / "cli-input.json"
            path.write_text(json.dumps(value))
            argv.extend(["--input", str(path)])
        result = subprocess.run(argv, text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def cli_offer(self, **changes):
        self.spec.update(changes)
        proposal = self.cli("prepare", self.spec)
        self.cli("publish", proposal)
        self.assertEqual(self.cli("status")["operation"], "present_decision")
        return proposal

    def host_phase(self, status, role, gate, **changes):
        """Fixture host supplies role progress; this does not simulate an actual agent."""
        state = self.state()
        state.update(epicStatus=status, currentRole=role, lastGatePassed=gate, **changes)
        self.state_path.write_text(json.dumps(state))

    def cli_verified_delivery(self):
        self.assertEqual(self.cli("status")["operation"], "implement")
        self.host_phase("review_in_progress", "Reviewer", "Gate C")
        self.assertEqual(self.cli("status")["operation"], "review")
        self.host_phase("tdo_validation_in_progress", "TDO", "Gate D")
        self.assertEqual(self.cli("status")["operation"], "verify")
        self.host_phase("po_approval_pending", "PO", "Gate D")

    def test_headless_single_increment_uses_two_synthetic_approvals(self):
        self.host_phase("gate_a_pending", "PO", None, activeIncrementId=None, plannedIncrementId="DI-001")
        start = self.cli_offer(kind="start", proposalId="start")
        self.cli("apply", self.response(start, operation="start-response"))
        self.cli_verified_delivery()
        delivery = self.cli_offer(kind="delivery", proposalId="delivery", recommendation="close")
        result = self.cli("apply", self.response(delivery, operation="delivery-response"))
        self.assertEqual(result["next"]["operation"], "complete")
        self.assertEqual(self.cli("status")["operation"], "complete")
        self.assertEqual(len(self.state()["decisionReceipts"]), 2)
        self.assertEqual(runtime.epic_closure_evidence(self.repo, self.workspace, self.state())[1], [])

    def test_headless_multiple_increments_change_pause_and_process_restart(self):
        self.host_phase("gate_a_pending", "PO", None, activeIncrementId=None, plannedIncrementId="DI-001")
        start = self.cli_offer(kind="start", proposalId="start", remainingWork="Filtering remains.")
        self.cli("apply", self.response(start, operation="start-response"))
        self.cli_verified_delivery()
        first = self.cli_offer(kind="delivery", proposalId="first-delivery", recommendation="continue")
        self.cli("change", {"proposalSha256": decisions.digest(first), "reason": "Clarify the remaining filter plan."})
        saved = self.state()
        self.host_phase("epic_paused", "PO", "Gate D")
        before = self.state_path.read_bytes()
        self.assertFalse(self.cli("status")["canExecute"])
        self.assertEqual(before, self.state_path.read_bytes())
        # The fixture host explicitly resumes after resolving the pause, not status itself.
        self.state_path.write_text(json.dumps(saved))
        self.assertEqual(self.cli("status")["operation"], "revise_proposal")
        revised = self.cli_offer(proposalId="first-revised", remainingWork="Plan filtering by export date.")
        result = self.cli("apply", self.response(revised, operation="first-response"))
        self.assertEqual(result["next"]["operation"], "plan_increment")
        self.assertEqual(self.cli("status"), result["next"])
        preview = runtime.plan_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="later")
        runtime.apply_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="later", expected_state_sha256=preview["sourceStateSha256"])
        self.assertFalse(self.cli("status")["canExecute"])
        plan = self.cli_offer(kind="plan", incrementId="DI-002", proposalId="next-plan",
                              summary="Add filtering by export date.", remainingWork="None after this Increment.")
        self.assertEqual(plan["decisions"], ["approve_increment"])
        self.cli("apply", self.response(plan, operation="plan-response"))
        self.cli_verified_delivery()
        final = self.cli_offer(kind="delivery", proposalId="final-delivery", recommendation="close")
        self.cli("apply", self.response(final, operation="final-response"))
        self.assertEqual(self.cli("status")["operation"], "complete")
        self.assertEqual(len(self.state()["decisionReceipts"]), 4)
        self.assertIsNotNone(decisions.committed_acceptance(self.repo, self.workspace, self.state(), "DI-001"))
        self.assertIsNotNone(decisions.committed_acceptance(self.repo, self.workspace, self.state(), "DI-002"))

    def test_administrative_refresh_reuses_response_but_product_change_cannot(self):
        proposal = self.proposal()
        response = self.response(proposal)
        state = self.state()
        state["updatedAt"] = "metadata-refresh"
        self.state_path.write_text(json.dumps(state))
        self.proposal()
        renewed = decisions.renew_response(self.repo, AUTHORITY, {"proposal": proposal, "response": response, "reason": "Refreshed administrative timestamp only"})
        self.assertEqual(renewed["source"], response["source"])
        self.assertIn("renewal", renewed)
        (self.repo / "product.py").write_text("print('different product')")
        self.proposal()
        with self.assertRaisesRegex(ValueError, "Delivery or decision changed"):
            decisions.renew_response(self.repo, AUTHORITY, {"proposal": proposal, "response": response, "reason": "Cannot call product edits administrative"})

    def test_next_step_does_not_invent_authority_and_status_does_not_mutate(self):
        for status, role, gate, operation in (
            ("gate_b_pending", "TDO", "Gate A", "present_decision"),
            ("increment_in_progress", "Dev", "Gate B", "implement"),
            ("review_in_progress", "Reviewer", "Gate C", "review"),
            ("tdo_validation_in_progress", "TDO", "Gate D", "verify"),
            ("po_approval_pending", "PO", "Gate D", "present_decision"),
            ("blocked", "TDO", "Gate A", "blocked"),
        ):
            state = self.state()
            state.update(epicStatus=status, currentRole=role, lastGatePassed=gate)
            self.state_path.write_text(json.dumps(state))
            before = self.state_path.read_bytes()
            self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], operation)
            self.assertEqual(before, self.state_path.read_bytes())
        state.update(epicStatus="gate_b_pending", currentRole="TDO", mode="Auto")
        self.state_path.write_text(json.dumps(state))
        self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "revalidate_auto_authority")
        state.update(currentRole="Dev")
        self.state_path.write_text(json.dumps(state))
        self.assertEqual(decisions.next_step(self.repo, AUTHORITY)["operation"], "blocked")

    def test_ui_offers_exact_combined_and_partial_decisions_without_writes(self):
        from aim_ui import build_board
        from aim_codex_bridge import capture_action_target, verify_action_result
        (self.repo / ".aim/ui-portfolio.json").write_text(json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "portfolio/EPIC-TEST"}]}))
        (self.workspace / "reviews").mkdir()
        proposal = self.proposal()
        before = self.state_path.read_bytes()
        board = build_board(self.repo)
        epic = next(item for item in board["epics"] if item["id"] == "EPIC-TEST")
        active = next(item for item in epic["increments"] if item["active"])
        self.assertEqual(active["decisionSummary"]["scope"], self.spec["scope"])
        self.assertEqual([item["label"] for item in active["actions"]], ["Accept delivery and close Epic", "Accept Increment only", "Request change"])
        self.assertEqual(active["actions"][1]["envelope"]["decisions"], ["accept_increment"])
        self.assertEqual(epic["nextStep"]["operation"], "present_decision")
        self.assertEqual(before, self.state_path.read_bytes())
        envelope = active["actions"][0]["envelope"]
        target = capture_action_target(self.repo, envelope)
        decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        result = verify_action_result(self.repo, {"envelope": envelope, "verificationTarget": target, "dispatchAttempted": True})
        self.assertTrue(result["verified"])

    def test_two_simultaneous_approvals_cannot_double_accept(self):
        proposal = self.proposal()
        response = self.response(proposal)
        from aim_runtime_lock import runtime_lock
        with runtime_lock(self.state_path):
            with self.assertRaises(OSError):
                decisions.apply(self.repo, AUTHORITY, response)
        decisions.apply(self.repo, AUTHORITY, response)
        with self.assertRaises(ValueError):
            decisions.apply(self.repo, AUTHORITY, {**response, "operationId": "another-operation"})
        self.assertEqual(len(self.state()["decisionReceipts"]), 1)

    def test_history_survives_next_increment_and_ignores_uncommitted_files(self):
        from aim_ui import build_board
        (self.repo / ".aim/ui-portfolio.json").write_text(json.dumps({"portfolioVersion": "1.0", "workspaces": [{"path": "portfolio/EPIC-TEST"}]}))
        (self.workspace / "reviews").mkdir()
        self.spec.update(recommendation="continue", remainingWork="Filtering")
        proposal = self.proposal()
        response = self.response(proposal)
        with patch.object(runtime, "_atomic_replace", side_effect=OSError("before commit")):
            with self.assertRaises(OSError):
                decisions.apply(self.repo, AUTHORITY, response)
        board = build_board(self.repo)
        card = next(i for i in board["epics"][0]["increments"] if i["id"] == "DI-001")
        self.assertIsNone(card["acceptanceEvidence"])
        decisions.apply(self.repo, AUTHORITY, response)
        preview = runtime.plan_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="next")
        runtime.apply_post_gate_e_continue(self.repo, authority_state_path=AUTHORITY, increment_id="DI-002", updated_at="next", expected_state_sha256=preview["sourceStateSha256"])
        board = build_board(self.repo)
        card = next(i for i in board["epics"][0]["increments"] if i["id"] == "DI-001")
        self.assertEqual(card["runtimeStatus"], "done_increment_accepted")
        self.assertIsNotNone(card["acceptanceEvidence"])

    def test_receipt_tampering_hides_historical_acceptance(self):
        self.spec.update(recommendation="continue", remainingWork="Filtering")
        proposal = self.proposal()
        decisions.apply(self.repo, AUTHORITY, self.response(proposal))
        reference = self.state()["decisionReceipts"][0]
        (self.repo / reference["path"]).write_text('{}')
        with self.assertRaises(ValueError):
            decisions.committed_acceptance(self.repo, self.workspace, self.state(), "DI-001")


if __name__ == "__main__":
    unittest.main()
