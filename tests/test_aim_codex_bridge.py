"""Focused trust-boundary tests for AIM UI background Codex dispatch."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_codex_bridge import (  # noqa: E402
    CodexBridgeError,
    CodexReadTimeout,
    AppServerClient,
    DispatchManager,
    binding_fingerprint,
    canonical_digest,
    capture_action_target,
    verify_action_result,
)


class FakeClient:
    def __init__(
        self,
        calls: list[tuple[str, dict]],
        *,
        account_type: str = "chatgpt",
        thread_status: str = "idle",
        turn_status: str = "completed",
        messages: list[dict] | None = None,
    ):
        self.calls = calls
        self.account_type = account_type
        self.thread_status = thread_status
        self.turn_status = turn_status
        self.messages = list(messages or [])

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def request(self, method: str, params: dict) -> dict:
        self.calls.append((method, params))
        if method == "account/read":
            return {"account": {"type": self.account_type}}
        if method == "thread/read":
            return {
                "thread": {
                    "id": params["threadId"],
                    "status": {"type": self.thread_status},
                    "turns": [],
                }
            }
        if method == "thread/resume":
            return {"thread": {"id": params["threadId"]}}
        if method == "turn/start":
            return {"turn": {"id": "turn-test", "status": "inProgress"}}
        raise AssertionError(method)

    def read(self, _timeout: float) -> dict:
        if self.messages:
            return self.messages.pop(0)
        return {
            "method": "turn/completed",
            "params": {
                "turn": {"id": "turn-test", "status": self.turn_status}
            },
        }


def wait_for(manager: DispatchManager, operation_id: str, statuses: set[str]) -> dict:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        operation = manager.status(operation_id)
        if operation["status"] in statuses:
            return operation
        time.sleep(0.01)
    raise AssertionError(f"operation did not reach {statuses}")


class DispatchManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.ledger = self.root / "state" / "dispatch.json"
        aim = self.repo / ".aim"
        for name in ("increments", "decisions", "reviews"):
            (aim / name).mkdir(parents=True)
        (aim / "epic.md").write_text("# EPIC-TEST — Verified work\n")
        (aim / "increments/001-plan.md").write_text("# DI-001 — Work\nEpic: EPIC-TEST\n")
        self.runtime = {
            "stateSchemaVersion": "1.0", "aimVersion": "2.0", "mode": "Auto",
            "costProfile": "Standard", "epicId": "EPIC-TEST", "epicStatus": "gate_b_pending",
            "activeIncrementId": "DI-001", "currentRole": "TDO", "lastGatePassed": "Gate A",
            "platform": "test", "parallelSupport": {"available": False, "enabled": False, "policy": "sequential_fallback"},
            "commitMode": "optional", "updatedAt": "2026-08-29T13:00:00Z",
        }
        self.write_runtime()
        from aim_ui import build_board
        self.envelope = build_board(self.repo)["epics"][0]["increments"][0]["actions"][0]["envelope"]

    def write_runtime(self, **changes) -> None:
        self.runtime.update(changes)
        (self.repo / ".aim/state.json").write_text(json.dumps(self.runtime))

    def start_work(self) -> None:
        self.write_runtime(epicStatus="increment_in_progress", currentRole="Dev",
                           lastGatePassed="Gate B", updatedAt="2026-08-29T13:01:00Z")

    def operation(self) -> dict:
        return {"envelope": self.envelope, "dispatchAttempted": True,
                "verificationTarget": capture_action_target(self.repo, self.envelope)}

    def manager(self, factory) -> DispatchManager:
        return DispatchManager(
            self.repo,
            "thread-authoritative",
            ledger_path=self.ledger,
            client_factory=factory,
        )

    def test_finished_reply_is_unverified_and_preserves_thread_settings(self) -> None:
        calls: list[tuple[str, dict]] = []
        manager = self.manager(lambda: FakeClient(calls))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        completed = wait_for(manager, queued["id"], {"unverified"})
        self.assertEqual(completed["turnStatus"], "completed")
        self.assertEqual(
            [method for method, _ in calls],
            ["account/read", "thread/read", "thread/resume", "turn/start"],
        )
        resume = calls[2][1]
        self.assertEqual(resume, {"threadId": "thread-authoritative"})
        start = calls[3][1]
        self.assertEqual(
            set(start), {"threadId", "input", "clientUserMessageId"}
        )
        self.assertEqual(start["threadId"], "thread-authoritative")
        self.assertEqual(start["input"], [{"type": "text", "text": "reviewed prompt"}])
        self.assertNotIn("model", start)
        self.assertNotIn("approvalPolicy", start)
        self.assertNotIn("sandboxPolicy", start)

    def test_replay_returns_same_operation_without_second_turn(self) -> None:
        calls: list[tuple[str, dict]] = []
        factory_calls = 0

        def factory() -> FakeClient:
            nonlocal factory_calls
            factory_calls += 1
            return FakeClient(calls)

        manager = self.manager(factory)
        manager.last_observed[canonical_digest(self.envelope)] = time.monotonic()
        first = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, first["id"], {"unverified"})
        second = manager.dispatch(self.envelope, "reviewed prompt")
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(second["status"], "unverified")
        self.assertEqual(factory_calls, 1)
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_non_chatgpt_auth_and_busy_thread_fail_closed(self) -> None:
        for account_type, thread_status, fragment in (
            ("apiKey", "idle", "ChatGPT-managed"),
            ("chatgpt", "active", "busy"),
        ):
            with self.subTest(account_type=account_type, status=thread_status):
                ledger = self.root / f"{account_type}-{thread_status}.json"
                manager = DispatchManager(
                    self.repo,
                    "thread-authoritative",
                    ledger_path=ledger,
                    client_factory=lambda: FakeClient(
                        [], account_type=account_type, thread_status=thread_status
                    ),
                )
                queued = manager.dispatch(self.envelope, "reviewed prompt")
                rejected = wait_for(manager, queued["id"], {"rejected", "failed"})
                self.assertIn(fragment, rejected["message"])

    def test_safe_busy_rejection_can_retry_without_duplicate_inflight_turn(self) -> None:
        calls: list[tuple[str, dict]] = []
        attempts = 0

        def factory() -> FakeClient:
            nonlocal attempts
            attempts += 1
            return FakeClient(
                calls, thread_status="active" if attempts == 1 else "idle"
            )

        manager = self.manager(factory)
        manager.last_observed[canonical_digest(self.envelope)] = time.monotonic()
        first = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, first["id"], {"rejected"})
        retry = manager.dispatch(self.envelope, "reviewed prompt")
        self.assertEqual(retry["id"], first["id"])
        wait_for(manager, first["id"], {"unverified"})
        self.assertEqual(attempts, 2)
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_unbound_manager_rejects_before_writing_a_ledger(self) -> None:
        manager = DispatchManager(
            self.repo, None, ledger_path=self.ledger, client_factory=lambda: FakeClient([])
        )
        with self.assertRaisesRegex(CodexBridgeError, "not bound"):
            manager.dispatch(self.envelope, "reviewed prompt")
        self.assertFalse(self.ledger.exists())

    def test_attention_is_truthful_and_never_auto_answered(self) -> None:
        release = threading.Event()

        class AttentionClient(FakeClient):
            def read(self, timeout: float) -> dict:
                if self.messages:
                    return self.messages.pop(0)
                release.wait(timeout)
                return super().read(timeout)

        calls: list[tuple[str, dict]] = []
        manager = self.manager(
            lambda: AttentionClient(
                calls,
                messages=[
                    {
                        "method": "item/permissions/requestApproval",
                        "id": 91,
                        "params": {"threadId": "thread-authoritative"},
                    }
                ],
            )
        )
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        attention = wait_for(manager, queued["id"], {"attention"})
        self.assertIn("needs your answer", attention["message"])
        self.assertNotIn("item/permissions/requestApproval", [method for method, _ in calls])
        release.set()
        wait_for(manager, queued["id"], {"unverified"})

    def test_changed_timestamp_wrong_increment_and_partial_catalog_are_not_success(self) -> None:
        operation = self.operation()
        before = (self.repo / ".aim/state.json").read_bytes()
        self.assertIsNone(verify_action_result(self.repo, operation))
        self.assertEqual(before, (self.repo / ".aim/state.json").read_bytes())
        self.write_runtime(updatedAt="2026-08-29T13:01:00Z")
        self.assertIsNone(verify_action_result(self.repo, operation))
        self.start_work()
        self.write_runtime(activeIncrementId="DI-002")
        self.assertIsNone(verify_action_result(self.repo, operation))
        self.write_runtime(activeIncrementId="DI-001")
        self.assertTrue(verify_action_result(self.repo, operation)["verified"])
        (self.repo / ".aim/ui-portfolio.json").write_text("{")
        self.assertIsNone(verify_action_result(self.repo, operation))

    def test_result_is_verified_only_after_requested_transition(self) -> None:
        outer = self
        class ResultClient(FakeClient):
            def read(self, timeout):
                outer.start_work()
                return super().read(timeout)
        calls = []
        manager = self.manager(lambda: ResultClient(calls))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        result = wait_for(manager, queued["id"], {"completed"})
        self.assertTrue(result["result"]["verified"])
        self.assertEqual(result["result"]["incrementId"], "DI-001")
        self.assertEqual(result["result"]["statePath"], ".aim/state.json")
        self.assertNotIn("turnId", result)

    def test_ambiguous_send_recovers_result_after_restart_without_resubmission(self) -> None:
        calls = []
        class LostResponseClient(FakeClient):
            def request(self, method, params):
                result = super().request(method, params)
                if method == "turn/start":
                    raise CodexBridgeError("Connection lost after send")
                return result
        manager = self.manager(lambda: LostResponseClient(calls))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, queued["id"], {"unknown", "unverified"})
        self.start_work()
        recovered = self.manager(lambda: FakeClient(calls))
        self.assertEqual(recovered.latest()["id"], queued["id"])
        result = wait_for(recovered, queued["id"], {"completed"})
        self.assertTrue(result["result"]["verified"])
        recovered.dispatch(self.envelope, "must not send again")
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_verified_result_does_not_imply_live_agent_after_restart(self) -> None:
        manager = self.manager(lambda: FakeClient([]))
        for status, phrase in (("inProgress", "not confirmed"), ("interrupted", "Codex stopped"), ("failed", "Codex stopped")):
            operation = {"status": "completed", "turnStatus": status,
                         "message": "Start verified: the requested work is on the board.",
                         "result": {"verified": True}}
            public = manager._public(operation)
            self.assertIn(phrase, public["message"])
            self.assertTrue(public["result"]["verified"])
            self.assertEqual(operation["message"], "Start verified: the requested work is on the board.")
        operation["turnStatus"] = "completed"
        self.assertEqual(manager._public(operation)["message"], operation["message"])

    def test_restart_observes_saved_turn_read_only(self) -> None:
        operation = self.operation()
        operation.update(id=canonical_digest(self.envelope), status="running", turnId="saved-turn",
                         bindingFingerprint=binding_fingerprint("thread-authoritative"), createdAt="t1")
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(json.dumps({"version": "1.0", "operations": {operation["id"]: operation}}))
        calls = []
        class ObserveClient(FakeClient):
            def request(self, method, params):
                result = super().request(method, params)
                result["thread"]["turns"] = [{"id": "saved-turn", "status": "inProgress"}]
                return result
        manager = self.manager(lambda: ObserveClient(calls))
        manager.latest()
        deadline = time.monotonic() + 2
        while not calls and time.monotonic() < deadline:
            time.sleep(0.01)
        while manager.workers and time.monotonic() < deadline:
            time.sleep(0.01)
        result = wait_for(manager, operation["id"], {"running"})
        self.assertEqual(result["turnStatus"], "inProgress")
        self.assertEqual([method for method, _ in calls], ["thread/read"])

    def test_gate_e_requires_real_matching_acceptance(self) -> None:
        from aim_ui import build_board
        self.write_runtime(epicStatus="po_approval_pending", currentRole="PO", lastGatePassed="Gate D")
        self.envelope = build_board(self.repo)["epics"][0]["increments"][0]["actions"][0]["envelope"]
        operation = self.operation()
        self.write_runtime(epicStatus="done_increment_accepted", activeIncrementId=None,
                           previousIncrementId="DI-001", previousIncrementStatus="accepted",
                           lastGatePassed="Gate E", updatedAt="2026-08-29T13:01:00Z",
                           gateEAcceptance=".aim/decisions/001-accepted.md")
        self.assertIsNone(verify_action_result(self.repo, operation))
        decision = self.repo / ".aim/decisions/001-accepted.md"
        decision.write_text("# DI-002\nDecision: accepted\n")
        self.assertIsNone(verify_action_result(self.repo, operation))
        decision.write_text("# DI-001\nDecision: accepted\n")
        self.assertTrue(verify_action_result(self.repo, operation)["verified"])

    def test_start_checks_backlog_link_and_gate_a_checks_reserved_increment(self) -> None:
        from aim_ui import build_board
        from aim_start import plan_start, apply_start
        repo = self.root / "fresh"
        (repo / ".aim").mkdir(parents=True)
        backlog_path = repo / ".aim/portfolio-backlog.json"
        backlog = {"backlogVersion": "1.0", "updatedAt": "2026-08-29T13:00:00Z", "items": [{
            "id": "INC-01", "epicId": "EPIC-NEW", "epicTitle": "Start", "title": "Work",
            "priority": 1, "createdAt": "2026-08-29T13:00:00Z"}]}
        backlog_path.write_text(json.dumps(backlog))
        envelope = build_board(repo)["epics"][0]["actions"][0]["envelope"]
        operation = {"envelope": envelope, "dispatchAttempted": True,
                     "verificationTarget": capture_action_target(repo, envelope)}
        request = dict(epic_id="EPIC-NEW", increment_id="DI-002", title="Start", mode="Auto",
                       cost_profile="Standard", updated_at="2026-08-29T13:01:00Z", candidate_id="INC-01")
        plan = plan_start(repo, **request)
        apply_start(repo, **request, expected_start_sha256=plan["startSha256"])
        self.assertTrue(verify_action_result(repo, operation)["verified"])
        saved = backlog_path.read_bytes()
        backlog_path.write_text(json.dumps(backlog))
        self.assertIsNone(verify_action_result(repo, operation))
        backlog_path.write_bytes(saved)
        path = repo / ".aim/portfolio/EPIC-NEW/state.json"
        runtime = json.loads(path.read_text())
        runtime["uiDecision"] = {"visibility": "ready", "gate": "Gate A", "targetId": "INC-01"}
        path.write_text(json.dumps(runtime))
        runtime["uiDecision"]["targetId"] = "EPIC-NEW"
        path.write_text(json.dumps(runtime))
        epic = build_board(repo)["epics"][0]
        envelope = epic["actions"][0]["envelope"]
        operation = {"envelope": envelope, "dispatchAttempted": True,
                     "verificationTarget": capture_action_target(repo, envelope)}
        runtime.pop("plannedIncrementId")
        runtime.pop("uiDecision")
        runtime.update(epicStatus="gate_b_pending", currentRole="TDO", lastGatePassed="Gate A",
                       activeIncrementId="DI-002", updatedAt="2026-08-29T13:02:00Z")
        path.write_text(json.dumps(runtime))
        self.assertTrue(verify_action_result(repo, operation)["verified"])

    def test_legacy_completion_cannot_claim_verified_success(self) -> None:
        operation_id = canonical_digest(self.envelope)
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(json.dumps({"version": "1.0", "operations": {operation_id: {
            "id": operation_id, "status": "completed", "createdAt": "old",
            "message": "Completed in the bound Codex task.",
        }}}))
        manager = self.manager(lambda: self.fail("Legacy status must not submit or observe an invented turn"))
        manager.last_observed[operation_id] = time.monotonic()
        self.assertEqual(manager.status(operation_id)["status"], "unverified")
        self.assertIsNone(manager.latest())  # Older records have no task binding.

    def test_wrong_role_cannot_verify_and_observation_never_writes_runtime(self) -> None:
        operation = self.operation()
        self.start_work()
        self.write_runtime(currentRole="PO")
        before = {p: p.read_bytes() for p in (self.repo / ".aim").rglob("*") if p.is_file()}
        self.assertIsNone(verify_action_result(self.repo, operation))
        after = {p: p.read_bytes() for p in (self.repo / ".aim").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_interrupted_turn_keeps_actual_turn_status_without_false_success(self) -> None:
        manager = self.manager(lambda: FakeClient([], turn_status="interrupted"))
        operation = manager.dispatch(self.envelope, "reviewed prompt")
        result = wait_for(manager, operation["id"], {"unverified"})
        self.assertEqual(result["turnStatus"], "interrupted")
        self.assertNotIn("result", result)

    def test_finished_turn_rechecks_local_result_without_reopening_codex(self) -> None:
        manager = self.manager(lambda: FakeClient([]))
        operation = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, operation["id"], {"unverified"})
        recovered = self.manager(lambda: self.fail("Finished turns must not reopen Codex"))
        recovered.latest()
        wait_for(recovered, operation["id"], {"unverified"})
        self.start_work()
        recovered.last_observed.clear()
        result = wait_for(recovered, operation["id"], {"completed"})
        self.assertTrue(result["result"]["verified"])

    def test_restart_before_send_allows_explicit_retry_only(self) -> None:
        operation = self.operation()
        operation.pop("dispatchAttempted")
        operation.update(id=canonical_digest(self.envelope), status="queued", createdAt="old",
                         bindingFingerprint=binding_fingerprint("thread-authoritative"))
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text(json.dumps({"version": "1.0", "operations": {operation["id"]: operation}}))
        calls = []
        manager = self.manager(lambda: FakeClient(calls))
        manager.latest()
        wait_for(manager, operation["id"], {"rejected"})
        self.assertEqual(calls, [])
        manager.dispatch(self.envelope, "explicit retry")
        wait_for(manager, operation["id"], {"unverified"})
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_real_cli_version_failure_survives_recovery_without_raw_error_or_replay(self) -> None:
        event = {"method": "turn/completed", "params": {"turn": {
            "id": "turn-test", "status": "failed", "error": {"message": json.dumps({
                "type": "error", "status": 400, "error": {"type": "invalid_request_error",
                "message": "The selected model requires a newer version of Codex. Please upgrade."}})}}}}
        calls = []
        manager = self.manager(lambda: FakeClient(calls, messages=[event]))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        result = wait_for(manager, queued["id"], {"unverified"})
        self.assertEqual(result["turnStatus"], "failed")
        self.assertEqual(result["message"], "Codex needs an update to use the selected model. Your work is saved.")
        recovered = self.manager(lambda: self.fail("A failed turn must not be reopened or replayed"))
        recovered.latest()
        result = wait_for(recovered, queued["id"], {"unverified"})
        self.assertEqual(result["turnStatus"], "failed")
        self.assertIn("needs an update", result["message"])
        self.assertNotIn("invalid_request_error", result["message"])
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_quiet_live_turn_is_not_aborted_or_redispatched(self) -> None:
        outer = self
        class QuietClient(FakeClient):
            quiet = True
            def read(self, timeout):
                if self.quiet:
                    self.quiet = False
                    raise CodexReadTimeout("No event this interval")
                outer.start_work()
                return super().read(timeout)
        calls = []
        manager = self.manager(lambda: QuietClient(calls))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        result = wait_for(manager, queued["id"], {"completed"})
        self.assertTrue(result["result"]["verified"])
        self.assertEqual(sum(method == "turn/start" for method, _ in calls), 1)

    def test_real_pipe_reader_drains_bursts_and_survives_quiet_intervals(self) -> None:
        script = """import sys,json,time
for line in sys.stdin:
    msg=json.loads(line)
    if msg.get('method')=='initialize':
        print(json.dumps({'id':msg['id'],'result':{}}),flush=True)
    elif msg.get('method')=='initialized':
        print(json.dumps({'method':'first'}))
        print(json.dumps({'method':'second'}),flush=True)
    elif msg.get('method')=='after-quiet':
        print(json.dumps({'method':'third'}),flush=True)
"""
        with AppServerClient(command=[sys.executable, "-u", "-c", script]) as client:
            self.assertEqual(client.read(1)["method"], "first")
            self.assertEqual(client.read(1)["method"], "second")
            with self.assertRaises(CodexReadTimeout):
                client.read(0.01)
            self.assertIsNone(client.process.poll())
            client.notify("after-quiet", {})
            self.assertEqual(client.read(1)["method"], "third")
        self.assertIsNotNone(client.process.poll())

    def test_binding_and_operation_ids_are_opaque_digests(self) -> None:
        self.assertEqual(len(binding_fingerprint("thread-secret")), 64)
        self.assertNotIn("thread", binding_fingerprint("thread-secret"))
        self.assertEqual(canonical_digest(self.envelope), canonical_digest(dict(reversed(list(self.envelope.items())))))


if __name__ == "__main__":
    unittest.main()
