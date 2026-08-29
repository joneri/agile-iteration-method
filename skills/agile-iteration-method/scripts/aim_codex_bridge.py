#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_codex_bridge.py
"""Dispatch one reviewed AIM action to a bound Codex thread via app-server."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import stat
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


MAX_LEDGER_BYTES = 1_000_000
MAX_OPERATIONS = 128
MAX_MESSAGE_BYTES = 1_000_000
TERMINAL_STATUSES = {"completed", "failed", "rejected"}
ATTENTION_METHODS = {
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
    "item/tool/requestUserInput",
    "mcpServer/elicitation/request",
}
DISPATCH_STATE_ENV = "AIM_UI_STATE_DIR"


class CodexBridgeError(RuntimeError):
    """A fail-closed, operator-facing bridge error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def binding_fingerprint(thread_id: str | None) -> str | None:
    if not isinstance(thread_id, str) or not thread_id.strip():
        return None
    return hashlib.sha256(thread_id.strip().encode("utf-8")).hexdigest()


def default_ledger_path(repo_root: Path) -> Path:
    configured = os.environ.get(DISPATCH_STATE_ENV)
    state_root = (
        Path(configured).expanduser().resolve()
        if configured
        else Path.home() / ".aim" / "ui" / "instances"
    )
    repo_key = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:24]
    return state_root / f"{repo_key}.dispatch.json"


class AppServerClient:
    """Small stable-surface JSONL client for one local app-server process."""

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        process_factory: Callable[..., Any] = subprocess.Popen,
        timeout: float = 12.0,
    ):
        self.command = command or ["codex", "app-server", "--listen", "stdio://"]
        self.process_factory = process_factory
        self.timeout = timeout
        self.process: Any = None
        self.next_id = 1

    def __enter__(self) -> "AppServerClient":
        self.process = self.process_factory(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "aim_ui",
                    "title": "AIM UI",
                    "version": "1.2.0",
                }
            },
        )
        self.notify("initialized", {})
        return self

    def __exit__(self, *_: object) -> None:
        if self.process is None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            try:
                self.process.kill()
            except OSError:
                pass

    def _send(self, message: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise CodexBridgeError("Codex app-server is not connected.")
        payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        if len(payload.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise CodexBridgeError("Codex app-server message exceeded the safe limit.")
        try:
            self.process.stdin.write(payload + "\n")
            self.process.stdin.flush()
        except OSError as exc:
            raise CodexBridgeError("Codex app-server connection closed.") from exc

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"method": method, "params": params})

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self._send({"method": method, "id": request_id, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            message = self.read(deadline - time.monotonic())
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message.get("error") or {}
                raise CodexBridgeError(
                    str(error.get("message") or f"Codex rejected {method}.")
                )
            result = message.get("result")
            if not isinstance(result, dict):
                raise CodexBridgeError(f"Codex returned an invalid {method} response.")
            return result

    def read(self, timeout: float) -> dict[str, Any]:
        if timeout <= 0:
            raise CodexBridgeError("Codex app-server timed out.")
        if self.process is None or self.process.stdout is None:
            raise CodexBridgeError("Codex app-server is not connected.")
        selector = selectors.DefaultSelector()
        selector.register(self.process.stdout, selectors.EVENT_READ)
        try:
            ready = selector.select(timeout)
        finally:
            selector.close()
        if not ready:
            raise CodexBridgeError("Codex app-server timed out.")
        line = self.process.stdout.readline()
        if not line:
            raise CodexBridgeError("Codex app-server closed before completion.")
        if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise CodexBridgeError("Codex app-server response exceeded the safe limit.")
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexBridgeError("Codex app-server returned invalid JSON.") from exc
        if not isinstance(message, dict):
            raise CodexBridgeError("Codex app-server returned an invalid message.")
        return message


class DispatchManager:
    """Own idempotency and truthful status for background AIM dispatches."""

    def __init__(
        self,
        repo_root: Path,
        thread_id: str | None,
        *,
        ledger_path: Path,
        client_factory: Callable[[], AppServerClient] = AppServerClient,
    ):
        self.repo_root = repo_root.resolve()
        self.thread_id = thread_id.strip() if isinstance(thread_id, str) else None
        self.ledger_path = ledger_path
        self.client_factory = client_factory
        self.lock = threading.RLock()

    @property
    def is_bound(self) -> bool:
        return bool(self.thread_id)

    def _read_ledger(self) -> dict[str, Any]:
        path = self.ledger_path
        if path.is_symlink():
            raise CodexBridgeError("Dispatch ledger must not be a symlink.")
        if not path.exists():
            return {"version": "1.0", "operations": {}}
        try:
            if path.stat().st_size > MAX_LEDGER_BYTES:
                raise CodexBridgeError("Dispatch ledger exceeded the safe limit.")
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CodexBridgeError("Dispatch ledger is unreadable.") from exc
        if not isinstance(value, dict) or not isinstance(value.get("operations"), dict):
            raise CodexBridgeError("Dispatch ledger has an invalid shape.")
        return value

    def _write_ledger(self, ledger: dict[str, Any]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.ledger_path.is_symlink():
            raise CodexBridgeError("Dispatch ledger must not be a symlink.")
        operations = ledger["operations"]
        if len(operations) > MAX_OPERATIONS:
            ordered = sorted(
                operations.items(), key=lambda item: item[1].get("updatedAt", "")
            )
            for key, operation in ordered:
                if len(operations) <= MAX_OPERATIONS:
                    break
                if operation.get("status") in TERMINAL_STATUSES:
                    operations.pop(key, None)
        temporary = self.ledger_path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temporary, self.ledger_path)

    def _public(self, operation: dict[str, Any]) -> dict[str, Any]:
        return {
            key: operation[key]
            for key in (
                "id",
                "status",
                "createdAt",
                "updatedAt",
                "message",
                "turnStatus",
            )
            if key in operation
        }

    def dispatch(self, envelope: dict[str, Any], prompt: str) -> dict[str, Any]:
        if not self.is_bound:
            raise CodexBridgeError(
                "AIM UI is not bound to a Codex task; restart it from the authoritative AIM task."
            )
        operation_id = canonical_digest(envelope)
        with self.lock:
            ledger = self._read_ledger()
            existing = ledger["operations"].get(operation_id)
            if isinstance(existing, dict):
                if existing.get("status") != "rejected" or existing.get("retryable") is not True:
                    return self._public(existing)
                existing.update(
                    {
                        "status": "queued",
                        "updatedAt": utc_now(),
                        "message": "Queued again after a safe preflight rejection.",
                        "retryable": False,
                    }
                )
                self._write_ledger(ledger)
                operation = existing
            else:
                now = utc_now()
                operation = {
                    "id": operation_id,
                    "status": "queued",
                    "createdAt": now,
                    "updatedAt": now,
                    "message": "Queued for the bound Codex task.",
                    "envelopeDigest": operation_id,
                    "retryable": False,
                }
                ledger["operations"][operation_id] = operation
                self._write_ledger(ledger)
        worker = threading.Thread(
            target=self._run, args=(operation_id, prompt), daemon=True
        )
        worker.start()
        return self._public(operation)

    def status(self, operation_id: str) -> dict[str, Any]:
        if not isinstance(operation_id, str) or len(operation_id) != 64:
            raise CodexBridgeError("Invalid background operation id.")
        with self.lock:
            operation = self._read_ledger()["operations"].get(operation_id)
        if not isinstance(operation, dict):
            raise CodexBridgeError("Background operation was not found.")
        return self._public(operation)

    def _update(self, operation_id: str, **changes: Any) -> None:
        with self.lock:
            ledger = self._read_ledger()
            operation = ledger["operations"].get(operation_id)
            if not isinstance(operation, dict):
                return
            operation.update(changes)
            operation["updatedAt"] = utc_now()
            self._write_ledger(ledger)

    def _run(self, operation_id: str, prompt: str) -> None:
        turn_started = False
        try:
            self._update(
                operation_id,
                status="preflight",
                message="Checking ChatGPT Usage and the bound task.",
            )
            with self.client_factory() as client:
                account = client.request("account/read", {"refreshToken": False})
                if (account.get("account") or {}).get("type") != "chatgpt":
                    raise CodexBridgeError(
                        "Background actions require ChatGPT-managed Codex Usage."
                    )
                read = client.request(
                    "thread/read", {"threadId": self.thread_id, "includeTurns": True}
                )
                thread = read.get("thread") or {}
                if thread.get("id") != self.thread_id:
                    raise CodexBridgeError("The bound Codex task could not be verified.")
                status = thread.get("status") or {}
                turns = thread.get("turns") or []
                if status.get("type") == "active" or any(
                    isinstance(turn, dict) and turn.get("status") == "inProgress"
                    for turn in turns
                ):
                    raise CodexBridgeError(
                        "The bound Codex task is busy; wait for its active turn to finish."
                    )
                client.request("thread/resume", {"threadId": self.thread_id})
                self._update(
                    operation_id,
                    status="running",
                    message="Running in the bound Codex task.",
                )
                # Crossing this boundary can be ambiguous if the process exits after
                # app-server accepts the turn but before the response arrives. Mark it
                # first so an uncertain outcome is never automatically replayed.
                turn_started = True
                started = client.request(
                    "turn/start",
                    {
                        "threadId": self.thread_id,
                        "input": [{"type": "text", "text": prompt}],
                        "clientUserMessageId": operation_id,
                    },
                )
                turn = started.get("turn") or {}
                turn_id = turn.get("id")
                if not isinstance(turn_id, str) or not turn_id:
                    raise CodexBridgeError("Codex did not return a turn id.")
                while True:
                    message = client.read(60.0)
                    method = message.get("method")
                    params = message.get("params") or {}
                    if method in ATTENTION_METHODS:
                        self._update(
                            operation_id,
                            status="attention",
                            message=(
                                "Codex requested operator attention. The unattended "
                                "bridge will not answer and will fail closed."
                            ),
                        )
                    if method == "serverRequest/resolved":
                        self._update(
                            operation_id,
                            status="running",
                            message="Running in the bound Codex task.",
                        )
                    if method != "turn/completed":
                        continue
                    completed = params.get("turn") or {}
                    if completed.get("id") != turn_id:
                        continue
                    turn_status = completed.get("status")
                    if turn_status == "completed":
                        self._update(
                            operation_id,
                            status="completed",
                            turnStatus=turn_status,
                            message="Completed in the bound Codex task.",
                        )
                        return
                    error = completed.get("error") or {}
                    raise CodexBridgeError(
                        str(error.get("message") or f"Codex turn {turn_status}.")
                    )
        except Exception as exc:  # fail closed at the background boundary
            message = str(exc) if isinstance(exc, CodexBridgeError) else "Background dispatch failed."
            self._update(
                operation_id,
                status="failed" if turn_started else "rejected",
                message=message,
                retryable=not turn_started,
            )
