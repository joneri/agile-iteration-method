#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_ui.py
"""Serve AIM's local runtime workspace as a read-only browser control room."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from aim_actions import (
    ACTION_PROMPT_PREAMBLE,
    GATE_EXPECTATIONS,
    action_envelope,
    action_prompt,
    codex_deep_link,
)
from aim_portfolio import project_portfolio_control
from aim_portfolio_run import project_portfolio_run

READ_MODEL_VERSION = "5.0"
PORTFOLIO_VERSION = "1.0"
PORTFOLIO_FILE = "ui-portfolio.json"
BACKLOG_VERSION = "1.0"
BACKLOG_FILE = "portfolio-backlog.json"
MAX_PORTFOLIO_WORKSPACES = 16
MAX_BACKLOG_ITEMS = 256
MAX_BACKLOG_BYTES = 1_000_000
VISIBLE_DONE_LIMIT = 3
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


def _accepted_at(aim_root: Path, increment_id: str) -> str | None:
    number = increment_id.removeprefix("DI-")
    decisions = aim_root / "decisions"
    if not decisions.is_dir():
        return None
    decision = decisions / f"{number}-gate-e.md"
    if not decision.is_file():
        return None
    content = _read_markdown(decision)
    declared = _field(content, "Accepted at") or _field(content, "acceptedAt")
    if declared:
        return declared
    return datetime.fromtimestamp(
        decision.stat().st_mtime, timezone.utc
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _increment_sort_key(item: dict[str, Any]) -> tuple[float, int, str]:
    raw_timestamp = item.get("acceptedAt") or item.get("updatedAt")
    timestamp = 0.0
    if isinstance(raw_timestamp, str):
        try:
            parsed = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            timestamp = parsed.timestamp()
        except ValueError:
            timestamp = 0.0
    match = re.search(r"(\d+)$", str(item.get("id", "")))
    number = int(match.group(1)) if match else -1
    return (timestamp, number, str(item.get("id", "")))


def _action_descriptor(
    repo_root: Path,
    label: str,
    envelope: dict[str, str],
    *,
    enabled: bool = True,
    reason: str | None = None,
    requires_input: bool = False,
) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "kind": envelope["action"],
        "label": label,
        "enabled": enabled,
        "reason": reason,
        "requiresInput": requires_input,
        "envelope": envelope,
    }
    if enabled and not requires_input:
        descriptor["prompt"] = action_prompt(envelope)
        descriptor["href"] = codex_deep_link(repo_root, envelope)
    return descriptor


def _gate_actions_are_ready(
    epic: dict[str, Any],
    increment: dict[str, Any],
    gate: str,
    warnings: list[str],
) -> bool:
    """Keep legacy actions visible, while honoring explicit AIM handoff readiness."""

    marker = epic.get("uiDecision")
    if marker is None:
        return True
    if not isinstance(marker, dict):
        warnings.append(f"{epic['id']}: uiDecision must be an object; gate actions are hidden.")
        return False

    expected = {"gate": gate, "targetId": increment["id"]}
    if any(marker.get(key) != value for key, value in expected.items()):
        warnings.append(
            f"{epic['id']}: uiDecision does not match {gate} for {increment['id']}; "
            "gate actions are hidden."
        )
        return False

    visibility = marker.get("visibility")
    if visibility == "preparing":
        increment["attention"] = (
            "AIM is finishing the decision handoff. Controls will appear when it is ready."
        )
        return False
    if visibility == "ready":
        return True

    warnings.append(
        f"{epic['id']}: uiDecision visibility must be preparing or ready; "
        "gate actions are hidden."
    )
    return False


def _attach_actions(
    repo_root: Path,
    epics: list[dict[str, Any]],
    control: dict[str, Any],
    backlog_updated_at: str,
    warnings: list[str],
) -> None:
    for epic in epics:
        authority_state_path = (
            ".aim/state.json"
            if epic["workspace"] == "."
            else f".aim/{epic['workspace']}/state.json"
        )
        for increment in epic["increments"]:
            increment["actions"] = []
            if increment["planned"]:
                if epic["active"] and epic["runtimeStatus"] == "gate_a_pending":
                    if epic["lastGatePassed"] != GATE_EXPECTATIONS["Gate A"][1]:
                        warnings.append(
                            f"{epic['id']}: gate_a_pending conflicts with lastGatePassed; "
                            "gate actions are hidden."
                        )
                        continue
                    if not _gate_actions_are_ready(epic, increment, "Gate A", warnings):
                        continue
                    for kind, label in (("approve", "Approve"), ("change", "Request change")):
                        envelope = action_envelope(
                            kind,
                            epic_id=epic["id"],
                            candidate_id=increment["id"],
                            gate="Gate A",
                            expected_status="gate_a_pending",
                            expected_updated_at=epic["updatedAt"],
                            authority_state_path=authority_state_path,
                            expected_last_gate_passed=epic["lastGatePassed"],
                        )
                        increment["actions"].append(
                            _action_descriptor(
                                repo_root,
                                label,
                                envelope,
                                requires_input=kind == "change",
                            )
                        )
                    continue
                envelope = action_envelope(
                    "activate",
                    epic_id=epic["id"],
                    candidate_id=increment["id"],
                    expected_updated_at=increment["updatedAt"],
                    backlog_updated_at=backlog_updated_at,
                )
                enabled = epic["lifecycle"] == "planned" and control["admission"] in {
                    "open",
                    "unbounded",
                }
                if epic["lifecycle"] == "closed":
                    reason = "This planned work belongs to a closed Epic and must be reframed in AIM chat."
                elif epic["lifecycle"] == "running":
                    reason = "This Epic already has active runtime work."
                elif control["admission"] == "full":
                    reason = "Portfolio capacity is full."
                elif control["admission"] == "over_capacity":
                    reason = "The portfolio is over capacity."
                elif control["admission"] == "blocked":
                    reason = "Portfolio admission is blocked."
                else:
                    reason = None
                increment["actions"].append(
                    _action_descriptor(
                        repo_root, "Activate", envelope, enabled=enabled, reason=reason
                    )
                )
                continue

            if not increment["active"]:
                continue
            status = increment["runtimeStatus"]
            gate = "Gate B" if status == "gate_b_pending" else "Gate E" if status == "po_approval_pending" else None
            if gate is None:
                continue
            if epic["lastGatePassed"] != GATE_EXPECTATIONS[gate][1]:
                warnings.append(
                    f"{epic['id']}: {status} conflicts with lastGatePassed; "
                    "gate actions are hidden."
                )
                continue
            if not _gate_actions_are_ready(epic, increment, gate, warnings):
                continue
            for kind, label in (("approve", "Approve"), ("change", "Request change")):
                envelope = action_envelope(
                    kind,
                    epic_id=epic["id"],
                    increment_id=increment["id"],
                    gate=gate,
                    expected_status=status,
                    expected_updated_at=increment["updatedAt"],
                    authority_state_path=authority_state_path,
                    expected_last_gate_passed=epic["lastGatePassed"],
                )
                increment["actions"].append(
                    _action_descriptor(
                        repo_root,
                        label,
                        envelope,
                        requires_input=kind == "change",
                    )
                )


def _evidence(
    repo_root: Path, aim_root: Path, increment_id: str, plan_path: Path
) -> list[dict[str, str]]:
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
                    "path": path.relative_to(repo_root).as_posix(),
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


def _workspace_roots(aim_root: Path, warnings: list[str]) -> tuple[str, list[Path]]:
    """Resolve declared Epic workspaces strictly inside the repository .aim root."""

    if not aim_root.is_dir():
        return "uninitialized", []

    portfolio_path = aim_root / PORTFOLIO_FILE
    if not portfolio_path.is_file():
        return "single-workspace", [aim_root]
    try:
        portfolio = _read_json(portfolio_path)
    except AimUiError as exc:
        warnings.append(str(exc))
        return "portfolio", []
    if portfolio.get("portfolioVersion") != PORTFOLIO_VERSION:
        warnings.append(
            f"{PORTFOLIO_FILE} must declare portfolioVersion {PORTFOLIO_VERSION}."
        )
        return "portfolio", []
    declared = portfolio.get("workspaces")
    if not isinstance(declared, list) or not declared:
        warnings.append(f"{PORTFOLIO_FILE} must contain a non-empty workspaces array.")
        return "portfolio", []
    if len(declared) > MAX_PORTFOLIO_WORKSPACES:
        warnings.append(
            f"{PORTFOLIO_FILE} declares more than {MAX_PORTFOLIO_WORKSPACES} workspaces."
        )
        return "portfolio", []

    roots: list[Path] = []
    seen: set[Path] = set()
    for index, item in enumerate(declared):
        raw = item.get("path") if isinstance(item, dict) else None
        if not isinstance(raw, str) or not raw.strip():
            warnings.append(f"Ignored workspace {index + 1}: missing path.")
            continue
        relative = Path(raw.strip())
        if relative.is_absolute():
            warnings.append(f"Ignored workspace {index + 1}: path must be relative to .aim.")
            continue
        candidate = (aim_root / relative).resolve()
        try:
            candidate.relative_to(aim_root)
        except ValueError:
            warnings.append(f"Ignored workspace {index + 1}: path leaves .aim.")
            continue
        if candidate in seen:
            warnings.append(f"Ignored workspace {index + 1}: duplicate path.")
            continue
        seen.add(candidate)
        if not candidate.is_dir():
            warnings.append(f"Ignored workspace {index + 1}: directory was not found.")
            continue
        roots.append(candidate)
    return "portfolio", roots


def _load_backlog(aim_root: Path, warnings: list[str]) -> list[dict[str, Any]]:
    """Read bounded chat-owned planning input without treating it as runtime state."""

    path = aim_root / BACKLOG_FILE
    if not path.is_file():
        return []
    if path.stat().st_size > MAX_BACKLOG_BYTES:
        warnings.append(f"{BACKLOG_FILE} is larger than {MAX_BACKLOG_BYTES} bytes.")
        return []
    try:
        backlog = _read_json(path)
    except AimUiError as exc:
        warnings.append(str(exc))
        return []
    if backlog.get("backlogVersion") != BACKLOG_VERSION:
        warnings.append(f"{BACKLOG_FILE} must declare backlogVersion {BACKLOG_VERSION}.")
        return []
    raw_items = backlog.get("items")
    if not isinstance(raw_items, list):
        warnings.append(f"{BACKLOG_FILE} must contain an items array.")
        return []
    if len(raw_items) > MAX_BACKLOG_ITEMS:
        warnings.append(f"{BACKLOG_FILE} contains more than {MAX_BACKLOG_ITEMS} items.")
        return []

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            warnings.append(f"Ignored backlog item {index + 1}: expected an object.")
            continue
        required = ("id", "epicId", "epicTitle", "title", "priority", "createdAt")
        if any(not raw.get(field) for field in required):
            warnings.append(f"Ignored backlog item {index + 1}: required fields are missing.")
            continue
        identifier = raw["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"INC-[A-Z0-9-]+", identifier):
            warnings.append(f"Ignored backlog item {index + 1}: invalid id.")
            continue
        if len(identifier) > 80:
            warnings.append(f"Ignored backlog item {index + 1}: id is too long.")
            continue
        if identifier in seen:
            warnings.append(f"Ignored backlog item {index + 1}: duplicate id {identifier}.")
            continue
        if not all(isinstance(raw[field], str) and raw[field].strip() for field in ("epicId", "epicTitle", "title", "createdAt")):
            warnings.append(f"Ignored backlog item {index + 1}: text fields must be non-empty strings.")
            continue
        limits = {"epicId": 120, "epicTitle": 200, "title": 240, "createdAt": 64}
        if any(len(raw[field]) > limit for field, limit in limits.items()):
            warnings.append(f"Ignored backlog item {index + 1}: a text field is too long.")
            continue
        if not isinstance(raw["priority"], int) or isinstance(raw["priority"], bool) or raw["priority"] < 1:
            warnings.append(f"Ignored backlog item {index + 1}: priority must be a positive integer.")
            continue
        summary = raw.get("summary")
        if summary is not None and not isinstance(summary, str):
            warnings.append(f"Ignored backlog item {index + 1}: summary must be a string.")
            continue
        if isinstance(summary, str) and len(summary) > 1000:
            warnings.append(f"Ignored backlog item {index + 1}: summary is too long.")
            continue
        runtime_increment_id = raw.get("runtimeIncrementId")
        if runtime_increment_id is not None and (
            not isinstance(runtime_increment_id, str)
            or not re.fullmatch(r"DI-\d+", runtime_increment_id)
            or len(runtime_increment_id) > 32
        ):
            warnings.append(f"Ignored backlog item {index + 1}: invalid runtimeIncrementId.")
            continue
        seen.add(identifier)
        items.append(
            {
                "id": identifier,
                "epicId": raw["epicId"].strip(),
                "epicTitle": raw["epicTitle"].strip(),
                "title": raw["title"].strip(),
                "summary": summary.strip() if isinstance(summary, str) else None,
                "priority": raw["priority"],
                "createdAt": raw["createdAt"].strip(),
                "runtimeIncrementId": runtime_increment_id,
            }
        )
    return sorted(items, key=lambda item: (item["priority"], item["createdAt"], item["id"]))


def _project_epic(repo_root: Path, aim_root: Path) -> dict[str, Any]:
    state = _read_json(aim_root / "state.json")
    _validate_state(state)
    epic_markdown = _read_markdown(aim_root / "epic.md")

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
                    "acceptedAt": _accepted_at(aim_root, increment_id) if accepted else None,
                    "active": is_active,
                    "planned": False,
                    "priority": None,
                    "summary": None,
                    "attention": attention,
                    "evidence": _evidence(repo_root, aim_root, increment_id, path),
                }
            )

    return {
        "id": epic_id,
        "title": _heading(epic_markdown, epic_id),
        "workspace": aim_root.relative_to((repo_root / ".aim").resolve()).as_posix(),
        "active": state["epicStatus"] != "epic_complete",
        "lifecycle": "closed" if state["epicStatus"] == "epic_complete" else "running",
        "runtimeStatus": state["epicStatus"],
        "mode": state["mode"],
        "costProfile": state["costProfile"],
        "currentRole": state["currentRole"],
        "lastGatePassed": state.get("lastGatePassed"),
        "updatedAt": state["updatedAt"],
        "uiDecision": state.get("uiDecision"),
        "increments": increment_items,
        "canonicalRoles": [
            {"name": role, "active": role == state["currentRole"]}
            for role in CANONICAL_ROLES
        ],
        "helperActivity": _load_agents(aim_root, epic_id),
    }


def build_board(repo_root: Path) -> dict[str, Any]:
    """Build a safe multi-Epic UI projection without mutating the repository."""

    repo_root = repo_root.resolve()
    aim_root = (repo_root / ".aim").resolve()
    warnings: list[str] = []
    source_kind, workspaces = _workspace_roots(aim_root, warnings)
    base = {
        "readModelVersion": READ_MODEL_VERSION,
        "generatedAt": utc_now(),
        "source": {
            "kind": source_kind,
            "readOnly": True,
            "refreshMs": DEFAULT_REFRESH_MS,
            "workspaceCount": len(workspaces),
        },
        "columns": [{"id": item[0], "label": item[1]} for item in KANBAN_COLUMNS],
        "epics": [],
        "history": {
            "doneLimit": VISIBLE_DONE_LIMIT,
            "acceptedCount": 0,
            "closedIncrements": [],
        },
        "control": None,
        "portfolioRun": None,
        "warnings": warnings,
        "onboarding": (
            {
                "state": "not_initialized",
                "message": "AIM UI is ready. This repository has no AIM runtime yet.",
                "nextAction": "/aim calibrate-repo",
            }
            if source_kind == "uninitialized"
            else None
        ),
    }
    seen_epics: set[str] = set()
    for index, workspace in enumerate(workspaces):
        try:
            epic = _project_epic(repo_root, workspace)
        except AimUiError as exc:
            warnings.append(f"Workspace {index + 1}: {exc}")
            continue
        if epic["id"] in seen_epics:
            warnings.append(f"Workspace {index + 1}: duplicate Epic id {epic['id']}.")
            continue
        seen_epics.add(epic["id"])
        base["epics"].append(epic)

    runtime_keys = {
        (epic["id"], item["id"])
        for epic in base["epics"]
        for item in epic["increments"]
    }
    backlog_items = _load_backlog(aim_root, warnings)
    backlog_runtime_candidates = {
        (item["epicId"], item["runtimeIncrementId"]): item["id"]
        for item in backlog_items
        if item["runtimeIncrementId"]
    }
    backlog_updated_at = "unknown"
    if (aim_root / BACKLOG_FILE).is_file():
        try:
            backlog_updated_at = str(_read_json(aim_root / BACKLOG_FILE).get("updatedAt") or "unknown")
        except AimUiError:
            pass
    for candidate in backlog_items:
        key = (
            candidate["epicId"],
            candidate["runtimeIncrementId"] or candidate["id"],
        )
        if key in runtime_keys:
            continue
        epic = next((item for item in base["epics"] if item["id"] == candidate["epicId"]), None)
        if epic is None:
            epic = {
                "id": candidate["epicId"],
                "title": candidate["epicTitle"],
                "workspace": None,
                "active": False,
                "lifecycle": "planned",
                "runtimeStatus": "planned",
                "mode": "Planning",
                "costProfile": None,
                "currentRole": None,
                "lastGatePassed": None,
                "updatedAt": candidate["createdAt"],
                "uiDecision": None,
                "increments": [],
                "canonicalRoles": [
                    {"name": role, "active": False} for role in CANONICAL_ROLES
                ],
                "helperActivity": {
                    "available": False,
                    "updatedAt": None,
                    "items": [],
                    "message": "This Epic is planned; no runtime agents are active.",
                },
                "focused": False,
            }
            base["epics"].append(epic)
        elif epic["title"] != candidate["epicTitle"]:
            warnings.append(
                f"Backlog item {candidate['id']} uses a different title for {candidate['epicId']}; runtime identity wins."
            )
        epic["increments"].append(
            {
                "id": candidate["id"],
                "epicId": candidate["epicId"],
                "title": candidate["title"],
                "summary": candidate["summary"],
                "column": "backlog",
                "runtimeStatus": "planned",
                "canonicalOwner": "TDO",
                "gate": "Not approved",
                "mode": "Planning",
                "costProfile": None,
                "updatedAt": candidate["createdAt"],
                "acceptedAt": None,
                "active": False,
                "planned": True,
                "priority": candidate["priority"],
                "attention": None,
                "evidence": [],
            }
        )

    control, control_warnings = project_portfolio_control(aim_root, base["epics"])
    warnings.extend(control_warnings)
    base["control"] = control
    portfolio_run, run_warnings = project_portfolio_run(aim_root)
    warnings.extend(run_warnings)
    base["portfolioRun"] = portfolio_run
    candidate_states = portfolio_run.get("candidateStates", {})
    for epic in base["epics"]:
        for increment in epic["increments"]:
            candidate_id = (
                increment["id"]
                if increment["planned"]
                else backlog_runtime_candidates.get((epic["id"], increment["id"]))
            )
            increment["portfolioCandidateId"] = candidate_id
            increment["portfolioState"] = candidate_states.get(candidate_id)
            increment["decisionAuthority"] = (
                portfolio_run.get("decisionAuthority")
                if candidate_id == portfolio_run.get("activeCandidateId")
                else None
            )
    for epic in base["epics"]:
        epic["focused"] = epic["id"] == control["focusedEpicId"]
    _attach_actions(repo_root, base["epics"], control, backlog_updated_at, warnings)
    for epic in base["epics"]:
        epic.pop("uiDecision", None)
    base["handoff"] = {
        "method": "codex_deep_link",
        "autoSend": False,
        "fallback": "copy",
        "workspacePath": str(repo_root.resolve()),
        "promptPreamble": ACTION_PROMPT_PREAMBLE,
    }

    accepted: list[dict[str, Any]] = []
    for epic in base["epics"]:
        epic["increments"].sort(
            key=lambda item: (
                item["column"] != "backlog",
                item.get("priority") or 10**9,
                item["id"],
            )
        )
        for item in epic["increments"]:
            if item["column"] == "done":
                accepted.append({**item, "epicTitle": epic["title"]})
    accepted.sort(key=_increment_sort_key, reverse=True)
    visible_done = {(item["epicId"], item["id"]) for item in accepted[:VISIBLE_DONE_LIMIT]}
    for epic in base["epics"]:
        for item in epic["increments"]:
            item["visibleOnBoard"] = item["column"] != "done" or (item["epicId"], item["id"]) in visible_done
    base["history"] = {
        "doneLimit": VISIBLE_DONE_LIMIT,
        "acceptedCount": len(accepted),
        "closedIncrements": accepted,
    }
    base["health"] = (
        "degraded" if not base["epics"] else "partial" if warnings else "healthy"
    )
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

    def __init__(
        self,
        address: tuple[str, int],
        repo_root: Path,
        ui_root: Path,
        instance_id: str | None = None,
        quiet: bool = False,
    ):
        self.repo_root = repo_root.resolve()
        self.ui_root = ui_root.resolve()
        self.instance_id = instance_id
        self.quiet = quiet
        super().__init__(address, AimUiHandler)


class AimUiHandler(BaseHTTPRequestHandler):
    server: AimUiServer

    def log_message(self, format: str, *args: object) -> None:
        if not self.server.quiet:
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
        if parsed.path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "repo": str(self.server.repo_root),
                    "pid": os.getpid(),
                    "instanceId": self.server.instance_id,
                    "readOnly": True,
                },
            )
            return
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
    parser.add_argument("--quiet", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--instance-id", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo.resolve()
    ui_root = Path(__file__).resolve().parents[1] / "aim-ui"
    if not repo_root.is_dir():
        raise SystemExit(f"Repository directory was not found at {repo_root}")
    if not ui_root.is_dir():
        raise SystemExit(f"AIM UI assets are missing at {ui_root}")
    server = AimUiServer(
        (args.host, args.port), repo_root, ui_root, args.instance_id, args.quiet
    )
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}/"
    if not args.quiet:
        print(f"AIM UI is reading {repo_root / '.aim'}")
        print(f"Open {url}")
        print("Read-only: GET and HEAD only. Press Ctrl-C to stop.")
    if not args.no_browser:
        threading.Timer(0.25, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nAIM UI stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
