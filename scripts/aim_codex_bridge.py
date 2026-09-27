#!/usr/bin/env python3
"""Dispatch one reviewed AIM action to a bound Codex thread via app-server."""

from __future__ import annotations

import hashlib
import json
import os
import queue
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


class CodexReadTimeout(CodexBridgeError):
    """No event arrived in this interval; the connection may still be healthy."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace(
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
        self.messages: queue.Queue = queue.Queue(maxsize=64)
        self.closed = threading.Event()

    def __enter__(self) -> "AppServerClient":
        self.process = self.process_factory(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.reader = threading.Thread(target=self._read_messages, daemon=True)
        self.reader.start()
        try:
            self.request(
                "initialize",
                {"clientInfo": {"name": "aim_ui", "title": "AIM UI", "version": "1.2.0"}},
            )
            self.notify("initialized", {})
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *_: object) -> None:
        if self.process is None:
            return
        self.closed.set()
        try:
            self.process.terminate()
            self.process.wait(timeout=1.0)
        except (OSError, subprocess.TimeoutExpired):
            try:
                self.process.kill()
                self.process.wait(timeout=1.0)
            except (OSError, subprocess.TimeoutExpired):
                pass
        self.reader.join(timeout=1.0)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()

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

    def _queue_message(self, message: Any) -> None:
        while not self.closed.is_set():
            try:
                self.messages.put(message, timeout=0.1)
                return
            except queue.Full:
                continue

    def _read_messages(self) -> None:
        """One reader owns buffered stdout; selectors cannot see Python's read-ahead."""
        try:
            while not self.closed.is_set() and self.process is not None and self.process.stdout is not None:
                line = self.process.stdout.readline(MAX_MESSAGE_BYTES + 1)
                if not line:
                    self._queue_message(CodexBridgeError("Codex app-server closed before completion."))
                    return
                if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    self._queue_message(CodexBridgeError("Codex app-server response exceeded the safe limit."))
                    return
                self._queue_message(line)
        except (OSError, UnicodeError, ValueError):
            self._queue_message(CodexBridgeError("Codex app-server connection could not be read."))

    def read(self, timeout: float) -> dict[str, Any]:
        if timeout <= 0:
            raise CodexReadTimeout("Codex app-server timed out.")
        if self.process is None or self.process.stdout is None:
            raise CodexBridgeError("Codex app-server is not connected.")
        try:
            line = self.messages.get(timeout=max(0, timeout))
        except queue.Empty as exc:
            raise CodexReadTimeout("Codex app-server timed out.") from exc
        if isinstance(line, Exception):
            raise line
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexBridgeError("Codex app-server returned invalid JSON.") from exc
        if not isinstance(message, dict):
            raise CodexBridgeError("Codex app-server returned an invalid message.")
        return message


def capture_action_target(repo_root: Path, envelope: dict[str, Any]) -> dict[str, Any]:
    """Bind verification to the exact enabled action, before sending anything."""
    from aim_ui import build_board

    for epic in build_board(repo_root)["epics"]:
        actions = list(epic.get("actions", []))
        for increment in epic["increments"]:
            actions.extend(increment.get("actions", []))
        if any(action.get("enabled") is True and action.get("envelope") == envelope
               and action.get("kind") in {"activate", "approve"} for action in actions):
            return {
                "workspace": epic.get("workspace"),
                "plannedIncrementId": epic.get("plannedIncrementId"),
                "existingIncrementIds": [item["id"] for item in epic["increments"]
                                         if not item.get("planned")],
            }
    raise CodexBridgeError("The action has changed. The board will show the current next step.")


def verify_action_result(repo_root: Path, operation: dict[str, Any]) -> dict[str, Any] | None:
    """Observe the requested runtime result; a finished turn is never proof."""
    repo_root = repo_root.resolve()
    from aim_actions import validate_action_envelope
    from aim_runtime_contract import terminal_acceptance, _schema_issues, _runtime_state_schema
    from aim_ui import build_board, _read_json, _validate_state

    envelope = operation.get("envelope")
    target = operation.get("verificationTarget")
    if not isinstance(envelope, dict) or not isinstance(target, dict):
        return None  # Older ledgers cannot acquire invented verification evidence.
    if not operation.get("dispatchAttempted"):
        return None
    try:
        validate_action_envelope(envelope)
        board = build_board(repo_root)
        matches = [epic for epic in board["epics"] if epic["id"] == envelope["epicId"]
                   and epic.get("workspace") is not None]
        if len(matches) != 1:
            return None
        epic = matches[0]
        if epic.get("observationOnly") or epic.get("runtimeStatusDiagnostic"):
            return None
        workspace = epic["workspace"]
        if envelope["action"] != "activate" and workspace != target.get("workspace"):
            return None
        relative = Path(".aim") if workspace == "." else Path(".aim") / workspace
        current = repo_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return None
        state_path = current / "state.json"
        state = _read_json(state_path)
        _validate_state(state)
        if _schema_issues(state, _runtime_state_schema(repo_root)):
            return None
        if state.get("updatedAt") != epic.get("updatedAt"):
            return None
        if state.get("epicId") != envelope["epicId"]:
            return None
        if envelope["action"] != "activate" and state.get("updatedAt") == envelope["expectedUpdatedAt"]:
            return None
        increment_id = envelope.get("incrementId") or target.get("plannedIncrementId")
        kind = envelope["action"]
        gate = envelope.get("gate")
        if kind == "activate":
            from aim_activation import _read_backlog
            backlog, _ = _read_backlog(repo_root / ".aim")
            candidates = [item for item in backlog["items"] if item.get("id") == envelope["candidateId"]
                          and item.get("epicId") == envelope["epicId"]]
            if len(candidates) != 1:
                return None
            candidate = candidates[0]
            increment_id = candidate.get("runtimeIncrementId")
            if not increment_id or increment_id in target.get("existingIncrementIds", []):
                return None
            if state.get("portfolioCandidateId") != envelope["candidateId"]:
                return None
        elif kind != "approve":
            return None
        increment = next((item for item in epic["increments"]
                          if item["id"] == increment_id and not item.get("planned")), None)
        if increment is None:
            return None
        status = state.get("epicStatus")
        accepted = False
        acceptance = None
        if status in {"done_increment_accepted", "epic_complete"}:
            acceptance, issues = terminal_acceptance(repo_root, current, state, increment_id)
            accepted = not issues and state.get("currentRole") == "PO" and state.get("activeIncrementId") is None
        active = state.get("activeIncrementId") == increment_id
        phases = {
            "increment_in_progress": ("Dev", "Gate B"),
            "review_in_progress": ("Reviewer", "Gate C"),
            "tdo_validation_in_progress": ("TDO", "Gate D"),
            "po_approval_pending": ("PO", "Gate D"),
        }
        progressed = active and phases.get(status) == (state.get("currentRole"), state.get("lastGatePassed"))
        gate_a_ready = (state.get("plannedIncrementId") == increment_id
                        and status == "gate_a_pending" and state.get("currentRole") == "PO"
                        and state.get("lastGatePassed") is None)
        gate_b_ready = (active and status == "gate_b_pending"
                        and state.get("currentRole") == "TDO" and state.get("lastGatePassed") == "Gate A")
        if kind == "activate":
            verified = gate_a_ready or gate_b_ready or progressed or accepted
            label = "Start verified: the requested work is on the board."
        elif gate == "Gate A":
            verified = gate_b_ready or progressed or accepted
            label = "Epic approval verified in the workspace."
        elif gate == "Gate B":
            verified = progressed or accepted
            label = "Increment start verified in the workspace."
        else:
            verified = gate == "Gate E" and accepted
            label = "Increment acceptance verified against its decision."
        if not verified:
            return None
        return {
            "verified": True, "checkedAt": utc_now(), "message": label,
            "epicId": envelope["epicId"], "incrementId": increment_id,
            "statePath": state_path.relative_to(repo_root).as_posix(),
            "stateDigest": canonical_digest(state),
            "acceptancePath": acceptance.relative_to(repo_root).as_posix() if acceptance else None,
        }
    except (ValueError, OSError, KeyError, TypeError):
        return None


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
        self.workers: set[str] = set()
        self.last_observed: dict[str, float] = {}

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
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CodexBridgeError("Dispatch ledger is unreadable.") from exc
        if not isinstance(value, dict) or not isinstance(value.get("operations"), dict):
            raise CodexBridgeError("Dispatch ledger has an invalid shape.")
        for key, operation in value["operations"].items():
            if (not isinstance(operation, dict) or operation.get("id") != key
                    or not isinstance(key, str) or len(key) != 64
                    or not isinstance(operation.get("status"), str)
                    or operation.get("result") is not None and not isinstance(operation["result"], dict)):
                raise CodexBridgeError("Saved action status is unreadable.")
            if (isinstance(operation, dict) and operation.get("status") == "completed"
                    and not (operation.get("result") or {}).get("verified")):
                operation.update(status="unverified", message="Earlier action result has not been verified.")
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
        public = {
            key: operation[key]
            for key in (
                "id",
                "status",
                "createdAt",
                "updatedAt",
                "message",
                "turnStatus",
                "result",
            )
            if key in operation
        }

        # Result verification and agent liveness are separate. In particular, a
        # restart can prove activation from files after the owning turn died.
        if (operation.get("status") == "completed"
                and (operation.get("result") or {}).get("verified") is True):
            turn_status = operation.get("turnStatus")
            if turn_status in {"failed", "interrupted"}:
                public["message"] = str(public.get("message") or "Saved result verified.") + " Codex stopped. Continue in the selected task when ready."
            elif turn_status != "completed":
                public["message"] = str(public.get("message") or "Saved result verified.") + " Current agent activity is not confirmed. Open the selected task for current progress."
        return public

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
                existing["bindingFingerprint"] = binding_fingerprint(self.thread_id)
                existing["verificationTarget"] = capture_action_target(self.repo_root, envelope)
                existing["envelope"] = json.loads(json.dumps(envelope))
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
                    "envelope": json.loads(json.dumps(envelope)),
                    "verificationTarget": capture_action_target(self.repo_root, envelope),
                    "bindingFingerprint": binding_fingerprint(self.thread_id),
                    "retryable": False,
                }
                ledger["operations"][operation_id] = operation
                self._write_ledger(ledger)
            self.workers.add(operation_id)
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
        self._schedule_observation(operation)
        with self.lock:
            return self._public(self._read_ledger()["operations"][operation_id])

    def latest(self) -> dict[str, Any] | None:
        """Recover the latest operation from the private ledger, including after restart."""
        with self.lock:
            operations = self._read_ledger()["operations"].values()
            matching = [item for item in operations if isinstance(item, dict)
                        and item.get("bindingFingerprint") == binding_fingerprint(self.thread_id)]
            operation = max(matching, key=lambda item: item.get("createdAt", ""), default=None)
        if operation is None:
            return None
        return self.status(operation["id"])

    def _schedule_observation(self, operation: dict[str, Any]) -> None:
        operation_id = operation["id"]
        with self.lock:
            if (operation_id in self.workers or operation.get("status") in TERMINAL_STATUSES
                    or time.monotonic() - self.last_observed.get(operation_id, float("-inf")) < 5):
                return
            self.workers.add(operation_id)
            self.last_observed[operation_id] = time.monotonic()
            self._update(operation_id, status="checking", message="Checking the saved work result…")
        threading.Thread(target=self._observe, args=(operation_id,), daemon=True).start()

    def _check_result(self, operation_id: str) -> bool:
        with self.lock:
            operation = self._read_ledger()["operations"][operation_id]
        result = verify_action_result(self.repo_root, operation)
        if result is None:
            return False
        self._update(operation_id, status="completed", result=result, message=result["message"])
        return True

    def _observe(self, operation_id: str) -> None:
        """Read-only recovery: never resume or submit a turn from this path."""
        try:
            with self.lock:
                operation = self._read_ledger()["operations"][operation_id]
            if (operation.get("status") in {"queued", "preflight", "checking"}
                    and isinstance(operation.get("envelope"), dict)
                    and isinstance(operation.get("verificationTarget"), dict)
                    and not operation.get("dispatchAttempted")):
                self._update(operation_id, status="rejected", retryable=True,
                             message="The action was not started. You can start it from the board.")
                return
            if self._check_result(operation_id):
                return
            if (operation.get("turnId")
                    and operation.get("turnStatus") not in {"completed", "failed", "interrupted"}
                    and operation.get("bindingFingerprint") == binding_fingerprint(self.thread_id)):
                with self.client_factory() as client:
                    response = client.request("thread/read", {"threadId": self.thread_id, "includeTurns": True})
                thread = response.get("thread") or {}
                if thread.get("id") == self.thread_id:
                    turn = next((turn for turn in thread.get("turns", [])
                                 if turn.get("id") == operation["turnId"]), None)
                    if turn:
                        turn_status = turn.get("status")
                        self._update(operation_id, turnStatus=turn_status)
                        if turn_status == "inProgress":
                            self._update(
                                operation_id,
                                status="attention" if operation.get("attentionRequested") else "running",
                                message=("Codex last requested your answer. Open the selected task to see its current step."
                                         if operation.get("attentionRequested") else
                                         "Codex is working; the result is not verified yet."),
                            )
                            return
                        if self._check_result(operation_id):
                            return
            self._update(
                operation_id, status="unverified",
                message=operation.get("failureMessage") or
                "The requested result is not confirmed yet. AIM is checking; the action will not be sent again.",
            )
        except Exception:
            self._update(operation_id, status="unknown", message="Contact interrupted. The saved work remains visible; AIM will check again.")
        finally:
            with self.lock:
                self.workers.discard(operation_id)
                self.last_observed[operation_id] = time.monotonic()

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
                with self.lock:
                    operation = self._read_ledger()["operations"][operation_id]
                capture_action_target(self.repo_root, operation["envelope"])
                self._update(
                    operation_id, status="starting", dispatchAttempted=True,
                    message="Starting the requested action in Codex…",
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
                self._update(operation_id, turnId=turn_id, turnStatus="inProgress",
                             status="running", message="Codex is working; the result is not verified yet.")
                while True:
                    try:
                        message = client.read(60.0)
                    except CodexReadTimeout:
                        # A model may think or run a tool silently for longer than a
                        # minute. Silence must not terminate its app-server process.
                        continue
                    method = message.get("method")
                    params = message.get("params") or {}
                    if (params.get("threadId") not in {None, self.thread_id}
                            or params.get("turnId") not in {None, turn_id}):
                        continue
                    if method in ATTENTION_METHODS:
                        self._update(
                            operation_id,
                            status="attention",
                            attentionRequested=True,
                            message="Codex needs your answer. Open the selected task to continue.",
                        )
                    if method == "serverRequest/resolved":
                        self._update(
                            operation_id,
                            status="running",
                            attentionRequested=False,
                            message="Codex is working; the result is not verified yet.",
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
                            status="checking",
                            turnStatus=turn_status,
                            message="Codex finished its response. Checking the requested result…",
                        )
                        if not self._check_result(operation_id):
                            self._update(operation_id, status="unverified", message="Codex finished its response, but the requested result is not confirmed yet. AIM will keep checking.")
                        return
                    error = completed.get("error") or {}
                    error_message = str(error.get("message", "")) if isinstance(error, dict) else ""
                    failure_message = (
                        "Codex needs an update to use the selected model. Your work is saved."
                        if "requires a newer version of Codex" in error_message else
                        "Codex stopped before the requested result was confirmed. The saved work remains on the board."
                    )
                    self._update(operation_id, turnStatus=turn_status, status="checking",
                                 failureMessage=failure_message,
                                 message="Codex stopped. Checking the saved result…")
                    if not self._check_result(operation_id):
                        self._update(operation_id, status="unverified", message=failure_message)
                    return
        except Exception as exc:  # fail closed at the background boundary
            message = str(exc) if isinstance(exc, CodexBridgeError) else "Background dispatch failed."
            self._update(
                operation_id,
                status="unknown" if turn_started else "rejected",
                message=("Contact interrupted. AIM will check the saved result without sending the action again." if turn_started else message),
                retryable=not turn_started,
            )
        finally:
            with self.lock:
                self.workers.discard(operation_id)
                self.last_observed[operation_id] = time.monotonic()
