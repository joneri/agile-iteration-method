"""Focused trust-boundary tests for AIM UI background Codex dispatch."""

from __future__ import annotations

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
    DispatchManager,
    binding_fingerprint,
    canonical_digest,
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
        self.envelope = {
            "actionVersion": "1.2",
            "action": "approve",
            "epicId": "EPIC-TEST",
            "incrementId": "DI-001",
            "gate": "Gate B",
            "expectedUpdatedAt": "2026-08-29T13:00:00Z",
        }

    def manager(self, factory) -> DispatchManager:
        return DispatchManager(
            self.repo,
            "thread-authoritative",
            ledger_path=self.ledger,
            client_factory=factory,
        )

    def test_success_preserves_model_permissions_and_thread_identity(self) -> None:
        calls: list[tuple[str, dict]] = []
        manager = self.manager(lambda: FakeClient(calls))
        queued = manager.dispatch(self.envelope, "reviewed prompt")
        completed = wait_for(manager, queued["id"], {"completed"})
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
        first = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, first["id"], {"completed"})
        second = manager.dispatch(self.envelope, "reviewed prompt")
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(second["status"], "completed")
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
        first = manager.dispatch(self.envelope, "reviewed prompt")
        wait_for(manager, first["id"], {"rejected"})
        retry = manager.dispatch(self.envelope, "reviewed prompt")
        self.assertEqual(retry["id"], first["id"])
        wait_for(manager, first["id"], {"completed"})
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
        self.assertIn("operator attention", attention["message"])
        self.assertNotIn("item/permissions/requestApproval", [method for method, _ in calls])
        release.set()
        wait_for(manager, queued["id"], {"completed"})

    def test_binding_and_operation_ids_are_opaque_digests(self) -> None:
        self.assertEqual(len(binding_fingerprint("thread-secret")), 64)
        self.assertNotIn("thread", binding_fingerprint("thread-secret"))
        self.assertEqual(canonical_digest(self.envelope), canonical_digest(dict(reversed(list(self.envelope.items())))))


if __name__ == "__main__":
    unittest.main()
