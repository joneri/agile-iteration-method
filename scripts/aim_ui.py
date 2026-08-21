#!/usr/bin/env python3
"""Serve AIM's local runtime workspace as a read-only browser control room."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


READ_MODEL_VERSION = "1.0"
DEFAULT_REFRESH_MS = 2_000
KANBAN_COLUMNS = (
    ("backlog", "Backlog"),
    ("work_in_progress", "Work in progress"),
    ("in_review", "In review"),
    ("ready_for_release", "Ready for release"),
    ("done", "Done"),
)
STATE_TO_COLUMN = {
    "epic_initialized": "backlog",
    "gate_a_pending": "backlog",
    "gate_b_pending": "backlog",
    "increment_in_progress": "work_in_progress",
    "epic_paused": "work_in_progress",
    "blocked": "work_in_progress",
    "review_in_progress": "in_review",
    "tdo_validation_in_progress": "in_review",
    "po_approval_pending": "ready_for_release",
    "done_increment_accepted": "done",
    "epic_complete": "done",
}
STATE_TO_OWNER = {
    "epic_initialized": "PO",
    "gate_a_pending": "PO",
    "gate_b_pending": "TDO",
    "increment_in_progress": "Dev",
    "epic_paused": "TDO",
    "blocked": "TDO",
    "review_in_progress": "Reviewer",
    "tdo_validation_in_progress": "TDO",
    "po_approval_pending": "PO",
    "done_increment_accepted": "PO",
    "epic_complete": "PO",
}
AGENT_STATUSES = {"working", "waiting", "completed", "failed"}
CANONICAL_ROLES = ("PO", "TDO", "Dev", "Reviewer")


class AimUiError(ValueError):
    """A safe, operator-facing AIM UI input error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AimUiError(f"Missing {path.name}.") from exc
    except json.JSONDecodeError as exc:
        raise AimUiError(f"{path.name} contains invalid JSON at line {exc.lineno}.") from exc
    if not isinstance(value, dict):
        raise AimUiError(f"{path.name} must contain a JSON object.")
    return value


def _read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise AimUiError(f"Could not read {path.name}.") from exc


def _heading(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(?:[^—\n]+—\s*)?(.+?)\s*$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def _field(markdown: str, label: str) -> str | None:
    match = re.search(
        rf"^{re.escape(label)}:\s*(?:`([^`]+)`|(.+?))\s*$",
        markdown,
        re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return None
    return (match.group(1) or match.group(2)).strip()


def _increment_id(path: Path, markdown: str) -> str:
    match = re.search(r"\bDI-\d+\b", markdown[:240], re.IGNORECASE)
    if match:
        return match.group(0).upper()
    number = re.match(r"(\d+)", path.name)
    return f"DI-{number.group(1)}" if number else path.stem.upper()


def _decision_is_accepted(aim_root: Path, increment_id: str) -> bool:
    number = increment_id.removeprefix("DI-")
    decisions = aim_root / "decisions"
    if not decisions.is_dir():
        return False
    for path in decisions.glob(f"{number}-gate-e.md"):
        content = _read_markdown(path)
        if re.search(r"\bAccepted\b|\baccept(?:ed)? by the PO\b", content, re.I):
            return True
    return False


def _evidence(aim_root: Path, increment_id: str, plan_path: Path) -> list[dict[str, str]]:
    number = increment_id.removeprefix("DI-")
    candidates: list[tuple[str, Path]] = [("Increment plan", plan_path)]
    review = aim_root / "reviews" / f"review-{number}.md"
    if review.is_file():
        candidates.append(("Review", review))
    decisions = aim_root / "decisions"
    if decisions.is_dir():
        for path in sorted(decisions.glob(f"{number}-gate-*.md")):
            candidates.append((path.stem.replace("-", " ").title(), path))
    result = []
    for label, path in candidates:
        if path.is_file():
            result.append(
                {
                    "label": label,
                    "path": path.relative_to(aim_root.parent).as_posix(),
                }
            )
    return result


def _load_agents(aim_root: Path, epic_id: str) -> dict[str, Any]:
    path = aim_root / "agent-activity.json"
    if not path.is_file():
        return {
            "available": False,
            "updatedAt": None,
            "items": [],
            "message": "No helper-agent activity has been recorded for this AIM run.",
        }
    try:
        activity = _read_json(path)
    except AimUiError as exc:
        return {
            "available": False,
            "updatedAt": None,
            "items": [],
            "message": str(exc),
        }
    raw_agents = activity.get("agents", [])
    if not isinstance(raw_agents, list):
        return {
            "available": False,
            "updatedAt": activity.get("updatedAt"),
            "items": [],
            "message": "agent-activity.json must contain an agents array.",
        }
    items = []
    warnings = []
    for index, raw in enumerate(raw_agents):
        if not isinstance(raw, dict):
            warnings.append(f"Ignored helper entry {index + 1}: expected an object.")
            continue
        agent_epic = raw.get("epicId", epic_id)
        if agent_epic != epic_id:
            continue
        status = raw.get("status")
        if status not in AGENT_STATUSES:
            warnings.append(f"Ignored helper entry {index + 1}: unsupported status.")
            continue
        identifier = raw.get("id")
        task = raw.get("task")
        if not isinstance(identifier, str) or not identifier.strip():
            warnings.append(f"Ignored helper entry {index + 1}: missing id.")
            continue
        if not isinstance(task, str) or not task.strip():
            warnings.append(f"Ignored helper entry {index + 1}: missing task.")
            continue
        role = raw.get("canonicalRole")
        items.append(
            {
                "id": identifier.strip(),
                "task": task.strip(),
                "status": status,
                "canonicalRole": role if role in CANONICAL_ROLES else None,
                "incrementId": raw.get("incrementId"),
                "spawnedAt": raw.get("spawnedAt"),
                "updatedAt": raw.get("updatedAt"),
            }
        )
    message = "; ".join(warnings) if warnings else None
    return {
        "available": True,
        "updatedAt": activity.get("updatedAt"),
        "items": items,
        "message": message,
    }


def _validate_state(state: dict[str, Any]) -> None:
    required = (
        "epicId",
        "epicStatus",
        "mode",
        "costProfile",
        "currentRole",
        "updatedAt",
    )
    missing = [key for key in required if not state.get(key)]
    if missing:
        raise AimUiError(f"state.json is missing: {', '.join(missing)}.")
    if state["mode"] not in {"Strict", "Auto"}:
        raise AimUiError("state.json has an unsupported mode.")
    if state["currentRole"] not in CANONICAL_ROLES:
        raise AimUiError("state.json has an unsupported currentRole.")
    if state["epicStatus"] not in STATE_TO_COLUMN:
        raise AimUiError("state.json has an unsupported epicStatus.")


def build_board(repo_root: Path) -> dict[str, Any]:
    """Build a safe UI projection without mutating the repository."""

    repo_root = repo_root.resolve()
    aim_root = repo_root / ".aim"
    warnings: list[str] = []
    base = {
        "readModelVersion": READ_MODEL_VERSION,
        "generatedAt": utc_now(),
        "source": {
            "kind": "local-aim-workspace",
            "readOnly": True,
            "refreshMs": DEFAULT_REFRESH_MS,
        },
        "columns": [{"id": item[0], "label": item[1]} for item in KANBAN_COLUMNS],
        "epics": [],
        "warnings": warnings,
    }
    try:
        state = _read_json(aim_root / "state.json")
        _validate_state(state)
        epic_markdown = _read_markdown(aim_root / "epic.md")
    except AimUiError as exc:
        warnings.append(str(exc))
        base["health"] = "degraded"
        return base

    epic_id = str(state["epicId"])
    active_id = state.get("activeIncrementId")
    increment_items: list[dict[str, Any]] = []
    increments_root = aim_root / "increments"
    if increments_root.is_dir():
        for path in sorted(increments_root.glob("*.md")):
            markdown = _read_markdown(path)
            increment_id = _increment_id(path, markdown)
            declared_epic = _field(markdown, "Epic")
            is_active = increment_id == active_id
            if declared_epic != epic_id and not (is_active and declared_epic is None):
                continue
            accepted = _decision_is_accepted(aim_root, increment_id)
            runtime_status = state["epicStatus"] if is_active else (
                "done_increment_accepted" if accepted else "gate_b_pending"
            )
            column = STATE_TO_COLUMN[runtime_status]
            owner = state["currentRole"] if is_active else STATE_TO_OWNER[runtime_status]
            attention = None
            if is_active and runtime_status == "blocked":
                attention = "AIM is blocked and needs operator input."
            elif is_active and runtime_status == "po_approval_pending":
                attention = "PO acceptance is required."
            increment_items.append(
                {
                    "id": increment_id,
                    "epicId": epic_id,
                    "title": _heading(markdown, increment_id),
                    "column": column,
                    "runtimeStatus": runtime_status,
                    "canonicalOwner": owner,
                    "gate": state.get("lastGatePassed") if is_active else "Gate E",
                    "mode": state["mode"],
                    "costProfile": state["costProfile"],
                    "updatedAt": state["updatedAt"] if is_active else None,
                    "active": is_active,
                    "attention": attention,
                    "evidence": _evidence(aim_root, increment_id, path),
                }
            )

    epic = {
        "id": epic_id,
        "title": _heading(epic_markdown, epic_id),
        "active": state["epicStatus"] != "epic_complete",
        "runtimeStatus": state["epicStatus"],
        "mode": state["mode"],
        "costProfile": state["costProfile"],
        "currentRole": state["currentRole"],
        "lastGatePassed": state.get("lastGatePassed"),
        "updatedAt": state["updatedAt"],
        "increments": increment_items,
        "canonicalRoles": [
            {"name": role, "active": role == state["currentRole"]}
            for role in CANONICAL_ROLES
        ],
        "helperActivity": _load_agents(aim_root, epic_id),
    }
    base["epics"] = [epic]
    base["health"] = "healthy"
    return base


def resolve_evidence_path(repo_root: Path, requested: str) -> Path:
    """Resolve a requested evidence path strictly inside the repo's .aim root."""

    repo_root = repo_root.resolve()
    aim_root = (repo_root / ".aim").resolve()
    relative = Path(unquote(requested))
    if relative.is_absolute() or not relative.parts or relative.parts[0] != ".aim":
        raise AimUiError("Evidence paths must stay inside .aim.")
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(aim_root)
    except ValueError as exc:
        raise AimUiError("Evidence path leaves the .aim workspace.") from exc
    if not candidate.is_file():
        raise AimUiError("Evidence file was not found.")
    return candidate


class AimUiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], repo_root: Path, ui_root: Path):
        self.repo_root = repo_root.resolve()
        self.ui_root = ui_root.resolve()
        super().__init__(address, AimUiHandler)


class AimUiHandler(BaseHTTPRequestHandler):
    server: AimUiServer

    def log_message(self, format: str, *args: object) -> None:
        print(f"AIM UI: {format % args}")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: HTTPStatus, value: Any) -> None:
        self._send(
            status,
            (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/board":
            self._json(HTTPStatus.OK, build_board(self.server.repo_root))
            return
        if parsed.path == "/api/evidence":
            requested = parse_qs(parsed.query).get("path", [""])[0]
            try:
                evidence = resolve_evidence_path(self.server.repo_root, requested)
                body = evidence.read_bytes()
            except (AimUiError, OSError) as exc:
                self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                return
            self._send(HTTPStatus.OK, body, "text/plain; charset=utf-8")
            return
        requested = "index.html" if parsed.path == "/" else unquote(parsed.path.lstrip("/"))
        if not requested or Path(requested).is_absolute():
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
            return
        candidate = (self.server.ui_root / requested).resolve()
        try:
            candidate.relative_to(self.server.ui_root)
        except ValueError:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
            return
        if not candidate.is_file():
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript"}:
            content_type += "; charset=utf-8"
        self._send(HTTPStatus.OK, candidate.read_bytes(), content_type)

    def _reject_write(self) -> None:
        self._json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"error": "AIM UI is read-only; this method is not available."},
        )

    do_POST = _reject_write
    do_PUT = _reject_write
    do_PATCH = _reject_write
    do_DELETE = _reject_write


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="AIM repository root")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback)")
    parser.add_argument("--port", type=int, default=4177, help="HTTP port (default: 4177)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser tab")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo.resolve()
    ui_root = Path(__file__).resolve().parents[1] / "aim-ui"
    if not (repo_root / ".aim").is_dir():
        raise SystemExit(f"No .aim workspace found at {repo_root}")
    if not ui_root.is_dir():
        raise SystemExit(f"AIM UI assets are missing at {ui_root}")
    server = AimUiServer((args.host, args.port), repo_root, ui_root)
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}/"
    print(f"AIM UI is reading {repo_root / '.aim'}")
    print(f"Open {url}")
    print("Read-only: GET and HEAD only. Press Ctrl-C to stop.")
    if not args.no_browser:
        threading.Timer(0.25, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAIM UI stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
