#!/usr/bin/env python3
"""Serve AIM's local runtime workspace as a read-only browser control room."""

from __future__ import annotations

import argparse
import hashlib
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
from aim_portfolio_run import project_portfolio_run, snapshot_hash

READ_MODEL_VERSION = "8.0"
PORTFOLIO_VERSION = "1.0"
PORTFOLIO_FILE = "ui-portfolio.json"
BACKLOG_VERSION = "1.0"
BACKLOG_FILE = "portfolio-backlog.json"
MAX_PORTFOLIO_WORKSPACES = 16
MAX_BACKLOG_ITEMS = 256
MAX_BACKLOG_BYTES = 1_000_000
MAX_ACCEPTANCE_DECISION_BYTES = 1_000_000
MAX_GATE_B_DECISION_BYTES = 1_000_000
RECENT_DELIVERIES_LIMIT = 10
DEFAULT_REFRESH_MS = 2_000
KANBAN_COLUMNS = (
    ("backlog", "Backlog"),
    ("work_in_progress", "Work in progress"),
    ("in_review", "In review"),
    ("ready_for_release", "Ready for release"),
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
CANONICAL_GATES = {None, "Gate A", "Gate B", "Gate C", "Gate D", "Gate E"}


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


def _decision_accepts_increment(path: Path, increment_id: str) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        if path.stat().st_size > MAX_ACCEPTANCE_DECISION_BYTES:
            return False
    except OSError:
        return False
    content = _read_markdown(path)
    decision = _field(content, "Decision") or ""
    status = _field(content, "Status") or ""
    authority_fields = f"{decision}\n{status}"
    if re.search(r"\b(?:change requested|pending|rejected|not accepted)\b", authority_fields, re.I):
        return False
    heading = content.splitlines()[0] if content.splitlines() else ""
    accepted = any(
        (
            re.search(r"\b(?:accept(?:ed)?|approv(?:e|ed))\b", authority_fields, re.I),
            _field(content, "Accepted at"),
            re.search(r"\bGate E\b.*\bAccepted\b|\bAccepted\b.*\bGate E\b", heading, re.I),
            re.search(r"^Accepted\s+(?:by|on|under|as part of)\b", content, re.I | re.M),
        )
    )
    if not accepted:
        return False
    mentioned = {item.upper() for item in re.findall(r"\bDI-\d+\b", content, re.I)}
    return not mentioned or increment_id in mentioned


def _legacy_acceptance_decision(aim_root: Path, increment_id: str) -> Path | None:
    number = increment_id.removeprefix("DI-")
    decisions = aim_root / "decisions"
    if not decisions.is_dir():
        return None
    for path in decisions.glob(f"{number}-gate-e.md"):
        if _decision_accepts_increment(path, increment_id):
            return path
    return None


def _state_acceptance_decision(
    repo_root: Path,
    aim_root: Path,
    state: dict[str, Any],
    increment_id: str,
) -> tuple[Path | None, bool, str | None]:
    """Resolve optional structured acceptance; bool marks authoritative applicability."""

    previous_id = state.get("previousIncrementId")
    if previous_id != increment_id:
        return None, False, None
    if state.get("previousIncrementStatus") != "accepted":
        return None, True, None
    if state.get("epicStatus") not in {"done_increment_accepted", "epic_complete"}:
        return None, True, "accepted previous Increment requires a terminal-compatible Epic status"
    if state.get("lastGatePassed") != "Gate E":
        return None, True, "accepted previous Increment requires lastGatePassed Gate E"

    raw_path = state.get("gateEAcceptance")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, True, "accepted previous Increment requires gateEAcceptance"
    if "\\" in raw_path:
        return None, True, "gateEAcceptance must use repository-relative POSIX separators"
    relative = Path(raw_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != ".aim"
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        return None, True, "gateEAcceptance must be a contained repository-relative .aim path"

    lexical = repo_root / relative
    current = repo_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, True, "gateEAcceptance must not traverse a symbolic link"
    try:
        decision = lexical.resolve()
        decision.relative_to(aim_root.resolve())
    except (OSError, ValueError):
        return None, True, "gateEAcceptance leaves the authoritative Epic workspace"
    if decision.parent != (aim_root / "decisions").resolve():
        return None, True, "gateEAcceptance must name a file in the workspace decisions directory"
    if not _decision_accepts_increment(decision, increment_id):
        return None, True, "gateEAcceptance is missing, oversized, mismatched, or not accepted"
    return decision, True, None


def _acceptance_decision(
    repo_root: Path,
    aim_root: Path,
    state: dict[str, Any],
    increment_id: str,
    warnings: list[str],
) -> Path | None:
    decision, authoritative, issue = _state_acceptance_decision(
        repo_root, aim_root, state, increment_id
    )
    if issue:
        warnings.append(f"{state['epicId']} {increment_id}: {issue}; acceptance is hidden.")
    if authoritative:
        return decision
    return _legacy_acceptance_decision(aim_root, increment_id)


def _accepted_at(decision: Path) -> str:
    content = _read_markdown(decision)
    declared = _field(content, "Accepted at") or _field(content, "acceptedAt")
    parsed = _parse_timestamp(declared)
    if parsed is not None:
        return _timestamp_text(parsed)
    return datetime.fromtimestamp(
        decision.stat().st_mtime, timezone.utc
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an explicit timezone-aware timestamp without inventing a zone."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _gate_b_started_at(aim_root: Path, increment_id: str) -> str | None:
    """Return the earliest explicit Gate B timestamp from bounded local evidence."""

    decisions = aim_root / "decisions"
    if not decisions.is_dir():
        return None
    number = increment_id.removeprefix("DI-")
    timestamps: list[datetime] = []
    for path in sorted(decisions.glob(f"{number}*gate-b.md")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_GATE_B_DECISION_BYTES:
                continue
        except OSError:
            continue
        content = _read_markdown(path)
        declared = _field(content, "Approved at") or _field(content, "Timestamp")
        if declared is None:
            match = re.search(
                r"^\s*-\s*(?:Approved at|Timestamp):\s*(.+?)\s*$",
                content,
                re.MULTILINE | re.IGNORECASE,
            )
            declared = match.group(1).strip() if match else None
        parsed = _parse_timestamp(declared)
        if parsed is not None:
            timestamps.append(parsed)
    return _timestamp_text(min(timestamps)) if timestamps else None


def _increment_sort_key(item: dict[str, Any]) -> tuple[float, int, str, str]:
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
    return (
        timestamp,
        number,
        str(item.get("epicId", "")),
        str(item.get("id", "")),
    )


def _delivery_data(
    epics: list[dict[str, Any]], accepted: list[dict[str, Any]], generated_at: str
) -> dict[str, Any]:
    """Derive auditable delivery outcomes from already-validated workspaces."""

    runtime_epics = [epic for epic in epics if epic["lifecycle"] in {"running", "closed"}]
    anchor = _parse_timestamp(generated_at) or datetime.now(timezone.utc)
    seven_days = anchor.timestamp() - 7 * 24 * 60 * 60
    thirty_days = anchor.timestamp() - 30 * 24 * 60 * 60
    throughput_7 = 0
    throughput_30 = 0
    elapsed_hours: list[float] = []
    history: list[dict[str, Any]] = []
    eligible_acceptances = 0

    for item in accepted:
        accepted_raw = item.get("deliveryAcceptedAt")
        accepted_at = _parse_timestamp(accepted_raw)
        started_at = _parse_timestamp(item.get("deliveryStartedAt"))
        elapsed = None
        timestamp_status = "file_time_fallback"
        if accepted_at is not None and accepted_at <= anchor:
            eligible_acceptances += 1
            timestamp_status = "recorded"
            accepted_epoch = accepted_at.timestamp()
            if seven_days <= accepted_epoch <= anchor.timestamp():
                throughput_7 += 1
            if thirty_days <= accepted_epoch <= anchor.timestamp():
                throughput_30 += 1
            if started_at is not None and started_at <= accepted_at:
                elapsed = round((accepted_at - started_at).total_seconds() / 3600, 1)
                elapsed_hours.append(elapsed)
        elif accepted_at is not None:
            timestamp_status = "future_timestamp"
        history.append(
            {
                "id": item["id"],
                "epicId": item["epicId"],
                "epicTitle": item["epicTitle"],
                "title": item["title"],
                "acceptedAt": accepted_raw or item.get("acceptedAt"),
                "timestampStatus": timestamp_status,
                "startedAt": item.get("deliveryStartedAt"),
                "elapsedHours": elapsed,
                "evidencePath": item.get("acceptanceEvidence"),
            }
        )

    ordered = sorted(elapsed_hours)
    median = None
    if ordered:
        middle = len(ordered) // 2
        median = (
            ordered[middle]
            if len(ordered) % 2
            else round((ordered[middle - 1] + ordered[middle]) / 2, 1)
        )
    return {
        "generatedAt": generated_at,
        "epics": {
            "total": len(runtime_epics),
            "active": sum(epic["lifecycle"] == "running" for epic in runtime_epics),
            "completed": sum(epic["lifecycle"] == "closed" for epic in runtime_epics),
        },
        "increments": {"accepted": len(accepted)},
        "throughput": {
            "last7Days": throughput_7,
            "last30Days": throughput_30,
            "timestampSample": eligible_acceptances,
            "excluded": len(accepted) - eligible_acceptances,
        },
        "elapsed": {
            "status": "available" if ordered else "unavailable",
            "medianHours": median,
            "sample": len(ordered),
            "excluded": len(accepted) - len(ordered),
        },
        "history": history,
        "definitions": {
            "throughput": "Accepted Increments with an explicit Gate E timestamp in the trailing UTC window.",
            "elapsed": "Median time from an explicit Gate B approval timestamp to explicit Gate E acceptance.",
            "history": "Validated accepted Increments, newest first; fallback file times are labeled and excluded from metrics.",
        },
    }


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
    target: dict[str, Any],
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

    expected = {"gate": gate, "targetId": target["id"]}
    if any(marker.get(key) != value for key, value in expected.items()):
        warnings.append(
            f"{epic['id']}: uiDecision does not match {gate} for {target['id']}; "
            "gate actions are hidden."
        )
        return False

    visibility = marker.get("visibility")
    if visibility == "preparing":
        target["attention"] = (
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
    portfolio_run: dict[str, Any],
    backlog_updated_at: str,
    warnings: list[str],
) -> None:
    for epic in epics:
        epic["actions"] = []
        authority_state_path = (
            ".aim/state.json"
            if epic["workspace"] == "."
            else f".aim/{epic['workspace']}/state.json"
        )
        planning = epic.get("planning") or {}
        candidates = planning.get("candidates") or []
        if candidates:
            candidate = candidates[0]
            if epic["active"] and epic["runtimeStatus"] == "gate_a_pending":
                if epic["lastGatePassed"] != GATE_EXPECTATIONS["Gate A"][1]:
                    warnings.append(
                        f"{epic['id']}: gate_a_pending conflicts with lastGatePassed; "
                        "gate actions are hidden."
                    )
                elif _gate_actions_are_ready(epic, epic, "Gate A", warnings):
                    for kind, label in (("approve", "Approve"), ("change", "Request change")):
                        envelope = action_envelope(
                            kind,
                            epic_id=epic["id"],
                            candidate_id=candidate["id"],
                            gate="Gate A",
                            expected_status="gate_a_pending",
                            expected_updated_at=epic["updatedAt"],
                            authority_state_path=authority_state_path,
                            expected_last_gate_passed=epic["lastGatePassed"],
                        )
                        epic["actions"].append(
                            _action_descriptor(
                                repo_root, label, envelope, requires_input=kind == "change"
                            )
                        )
            elif not epic["active"]:
                envelope = action_envelope(
                    "activate",
                    epic_id=epic["id"],
                    candidate_id=candidate["id"],
                    expected_updated_at=candidate["createdAt"],
                    backlog_updated_at=backlog_updated_at,
                )
                portfolio_state = candidate.get("portfolioState")
                run_blocks_activation = (
                    portfolio_run.get("configured")
                    and portfolio_run.get("status") in {"running", "paused"}
                    and portfolio_state in {
                        "queued", "active", "activation_pending", "contradictory"
                    }
                )
                enabled = (
                    epic["lifecycle"] == "planned"
                    and not run_blocks_activation
                    and control["admission"] in {"open", "unbounded"}
                )
                reason = (
                    "Portfolio Auto has selected this candidate; resume activation in AIM chat."
                    if portfolio_state == "activation_pending"
                    else "Portfolio Auto state is contradictory; repair it in AIM chat."
                    if portfolio_state == "contradictory"
                    else "Portfolio Auto owns the approved snapshot order."
                    if run_blocks_activation
                    else
                    "Portfolio capacity is full." if control["admission"] == "full"
                    else "The portfolio is over capacity." if control["admission"] == "over_capacity"
                    else "Portfolio admission is blocked." if control["admission"] == "blocked"
                    else None
                )
                epic["actions"].append(
                    _action_descriptor(repo_root, "Start Epic", envelope, enabled=enabled, reason=reason)
                )

        for increment in epic["increments"]:
            increment["actions"] = []
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
    repo_root: Path,
    aim_root: Path,
    increment_id: str,
    increment_paths: list[Path],
    acceptance_decision: Path | None = None,
) -> list[dict[str, str]]:
    number = increment_id.removeprefix("DI-")
    candidates: list[tuple[str, Path]] = []
    for path in increment_paths:
        label = "Work log" if path.stem.endswith("-wip") else "Increment plan"
        candidates.append((label, path))
    review = aim_root / "reviews" / f"review-{number}.md"
    if review.is_file():
        candidates.append(("Review", review))
    decisions = aim_root / "decisions"
    if decisions.is_dir():
        for path in sorted(decisions.glob(f"{number}-gate-*.md")):
            candidates.append((path.stem.replace("-", " ").title(), path))
    if acceptance_decision is not None and all(
        path.resolve() != acceptance_decision.resolve() for _, path in candidates
    ):
        candidates.append(("Gate E acceptance", acceptance_decision))
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
    if state.get("stateSchemaVersion") != "1.0":
        raise AimUiError("state.json is not the current stateSchemaVersion 1.0 contract.")
    if state.get("lastGatePassed") not in CANONICAL_GATES:
        raise AimUiError("state.json has a non-canonical lastGatePassed value.")
    for field in ("activeIncrementId", "plannedIncrementId", "previousIncrementId"):
        identifier = state.get(field)
        if identifier is not None and (
            not isinstance(identifier, str) or re.fullmatch(r"DI-[0-9]+", identifier) is None
        ):
            raise AimUiError(f"state.json has a non-canonical {field} value.")


def _contract_drift(state: dict[str, Any]) -> list[str]:
    """Name legacy values without normalizing or authorizing them."""

    drift: list[str] = []
    if state.get("stateSchemaVersion") != "1.0":
        drift.append(
            f"stateSchemaVersion {state.get('stateSchemaVersion')!r} is not current 1.0"
        )
    status = state.get("epicStatus")
    if status not in STATE_TO_COLUMN:
        drift.append(f"epicStatus {status!r} is not a canonical runtime status")
    gate = state.get("lastGatePassed")
    if gate not in CANONICAL_GATES:
        drift.append(f"lastGatePassed {gate!r} is not a canonical Gate A-E label")
    for field in ("activeIncrementId", "plannedIncrementId", "previousIncrementId"):
        identifier = state.get(field)
        if identifier is not None and (
            not isinstance(identifier, str) or re.fullmatch(r"DI-[0-9]+", identifier) is None
        ):
            drift.append(f"{field} {identifier!r} is not a canonical DI-* identity")
    return drift


def _workspace_diagnostic(
    repo_root: Path,
    workspace: Path,
    *,
    kind: str,
    reason: str,
    epic_id: str | None = None,
    drift: list[str] | None = None,
) -> dict[str, Any]:
    state_path = workspace / "state.json"
    state: dict[str, Any] = {}
    fingerprint = None
    try:
        state_bytes = state_path.read_bytes()
        fingerprint = hashlib.sha256(state_bytes).hexdigest()
        parsed_state = json.loads(state_bytes)
        if isinstance(parsed_state, dict):
            state = parsed_state
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    status = state.get("epicStatus") or state.get("status")
    role = state.get("currentRole") or state.get("role")
    updated_at = state.get("updatedAt")
    status_text = str(status or "unknown")
    completed = status_text.lower() in {
        "complete",
        "completed",
        "epic_complete",
        "done",
        "accepted",
    }
    operation = (
        "review_and_repair_portfolio_catalog"
        if kind == "invalid_portfolio_catalog"
        else "keep_completed_checkpoint_as_history_and_create_roadmap"
        if completed
        else "review_and_migrate_checkpoint"
    )
    relative_state = state_path.relative_to(repo_root).as_posix()
    exact_drift = drift or []
    epic_identity = epic_id or "Unknown Epic"
    handoff = "\n".join(
        (
            "AIM_RECOVERY_REQUEST",
            f"requestedOperation: {operation}",
            f"statePath: {relative_state}",
            f"epicId: {epic_identity}",
            f"detectedStatus: {status_text}",
            f"detectedRole: {role or 'unknown'}",
            f"expectedUpdatedAt: {updated_at or 'unknown'}",
            f"expectedStateSha256: {fingerprint or 'unavailable'}",
            "failedContractChecks: " + json.dumps(exact_drift, ensure_ascii=False),
            "Preserve the checkpoint and present a reviewed, explicit plan before any migration or catalog write.",
        )
    )
    return {
        "kind": kind,
        "severity": "error",
        "epicId": epic_id or "Unknown Epic",
        "statePath": relative_state,
        "reason": reason,
        "contractDrift": exact_drift,
        "checkpoint": {
            "status": status_text,
            "role": role,
            "updatedAt": updated_at,
            "stateSha256": fingerprint,
            "completed": completed,
            "contract": "legacy" if exact_drift else "current",
        },
        "readOnly": True,
        "recommendedOperation": operation,
        "chatIntent": handoff,
        "nextAction": (
            "Review the checkpoint in AIM chat and choose an explicit migration or "
            "catalog repair; AIM UI will not modify it."
        ),
    }


def _roadmap_projection(
    aim_root: Path,
    backlog_items: list[dict[str, Any]],
    backlog_updated_at: str,
    valid: bool,
) -> dict[str, Any]:
    eligible = [item for item in backlog_items if not item.get("runtimeIncrementId")]
    snapshot_payload = [
        {
            "candidateId": item["id"],
            "epicId": item["epicId"],
            "epicTitle": item["epicTitle"],
            "title": item["title"],
            "priority": item["priority"],
            "createdAt": item["createdAt"],
        }
        for item in eligible
    ]
    snapshot_digest = snapshot_hash(snapshot_payload)
    configured = (aim_root / BACKLOG_FILE).is_file()
    command = '/aim start "PORTFOLIO" mode:auto'
    return {
        "configured": configured,
        "valid": valid,
        "status": "invalid" if not valid else "ready" if eligible else "empty",
        "candidateCount": len(backlog_items),
        "eligibleCount": len(eligible),
        "updatedAt": backlog_updated_at if configured else None,
        "snapshotSha256": snapshot_digest,
        "snapshot": snapshot_payload,
        "auto": {
            "supported": valid and bool(eligible),
            "command": command,
            "chatIntent": "\n".join(
                (
                    command,
                    f"Expected Roadmap snapshot: {snapshot_digest}",
                    f"Included candidates: {', '.join(item['id'] for item in eligible) or 'none'}",
                    "Preview this immutable snapshot and request one explicit bounded mandate before execution.",
                )
            ),
        },
        "strict": {
            "supported": False,
            "explanation": (
                "Portfolio Strict is not a defined multi-Epic start contract. "
                "Strict remains available for ordinary single-Epic execution."
            ),
        },
        "snapshotBoundary": (
            "The mandate includes only this previewed order. Later Roadmap additions are excluded."
        ),
        "pauseBoundary": (
            "AIM pauses on scope, trust, safety, validation, concurrency, or contradictory-state escalation."
        ),
    }


def _recovery_projection(
    source_kind: str,
    diagnostics: list[dict[str, Any]],
    roadmap: dict[str, Any],
) -> dict[str, Any] | None:
    if diagnostics:
        catalog_only = all(
            item["kind"] == "invalid_portfolio_catalog" for item in diagnostics
        )
        completed = all(item["checkpoint"]["completed"] for item in diagnostics)
        combined_handoff = "\n\n".join(item["chatIntent"] for item in diagnostics)
        recommended = (
            {
                "label": "Review and repair the Portfolio catalog in AIM chat",
                "intent": combined_handoff,
            }
            if catalog_only
            else
            {
                "label": "Keep as history and create a new Roadmap",
                "intent": combined_handoff,
            }
            if completed
            else {
                "label": "Review and migrate checkpoint in AIM chat",
                "intent": combined_handoff,
            }
        )
        alternatives = [
            {
                "label": "Create or merge a Roadmap in AIM chat",
                "intent": "/aim to-backlog",
            },
            {
                "label": "Copy diagnostic report",
                "intent": combined_handoff,
            },
        ]
        if roadmap["configured"]:
            alternatives.insert(
                0, {"label": "Open existing Roadmap", "intent": "/aim ui"}
            )
        return {
            "kind": (
                "catalog_attention"
                if catalog_only
                else "preserved_history"
                if completed
                else "checkpoint_attention"
            ),
            "title": (
                "AIM found a board setup that needs review"
                if catalog_only
                else "AIM found earlier work, but it isn’t connected to a current board"
            ),
            "message": (
                "AIM preserved the checkpoint and will not guess, rewrite, or register it. "
                "Choose a reviewed action in AIM chat."
            ),
            "recommendedAction": recommended,
            "alternatives": alternatives,
            "found": {
                "checkpointCount": len(diagnostics),
                "history": (
                    "unknown"
                    if catalog_only
                    else "completed"
                    if completed
                    else "active or incomplete"
                ),
                "contract": "legacy or outside the current catalog",
                "checkpointUpdated": diagnostics[0]["checkpoint"]["updatedAt"] or "unknown",
                "roadmap": "available" if roadmap["configured"] else "not created",
                "portfolioCatalog": "present" if source_kind == "portfolio" else "not configured",
            },
            "technicalDetails": diagnostics,
            "readOnly": True,
        }
    if source_kind == "uninitialized":
        return {
            "kind": "empty_repository",
            "title": "AIM is ready for a Roadmap",
            "message": (
                "This repository has no AIM runtime. Calibrate it first, then add Epics "
                "by pasting them or naming one repository source in AIM chat."
            ),
            "recommendedAction": {
                "label": "Calibrate this repository",
                "intent": "/aim calibrate-repo",
            },
            "alternatives": [
                {"label": "Create a Roadmap", "intent": "/aim to-backlog"}
            ],
            "found": {
                "checkpointCount": 0,
                "history": "none",
                "contract": "not initialized",
                "roadmap": "not created",
                "portfolioCatalog": "not configured",
            },
            "technicalDetails": [],
            "readOnly": True,
        }
    return None


def _workspace_roots(
    repo_root: Path, aim_root: Path, warnings: list[str]
) -> tuple[str, list[Path], list[dict[str, Any]]]:
    """Resolve declared Epic workspaces strictly inside the repository .aim root."""

    if not aim_root.is_dir():
        return "uninitialized", [], []

    diagnostics: list[dict[str, Any]] = []

    portfolio_path = aim_root / PORTFOLIO_FILE
    if not portfolio_path.is_file():
        return "single-workspace", [aim_root], diagnostics
    try:
        portfolio = _read_json(portfolio_path)
    except AimUiError as exc:
        warnings.append(str(exc))
        diagnostics.append(
            _workspace_diagnostic(
                repo_root,
                aim_root,
                kind="invalid_portfolio_catalog",
                reason=str(exc),
            )
        )
        return "portfolio", [], diagnostics
    if portfolio.get("portfolioVersion") != PORTFOLIO_VERSION:
        warnings.append(
            f"{PORTFOLIO_FILE} must declare portfolioVersion {PORTFOLIO_VERSION}."
        )
        diagnostics.append(
            _workspace_diagnostic(
                repo_root,
                aim_root,
                kind="invalid_portfolio_catalog",
                reason=warnings[-1],
            )
        )
        return "portfolio", [], diagnostics
    declared = portfolio.get("workspaces")
    if not isinstance(declared, list) or not declared:
        warnings.append(f"{PORTFOLIO_FILE} must contain a non-empty workspaces array.")
        diagnostics.append(
            _workspace_diagnostic(
                repo_root,
                aim_root,
                kind="invalid_portfolio_catalog",
                reason=warnings[-1],
            )
        )
        return "portfolio", [], diagnostics
    if len(declared) > MAX_PORTFOLIO_WORKSPACES:
        warnings.append(
            f"{PORTFOLIO_FILE} declares more than {MAX_PORTFOLIO_WORKSPACES} workspaces."
        )
        diagnostics.append(
            _workspace_diagnostic(
                repo_root,
                aim_root,
                kind="invalid_portfolio_catalog",
                reason=warnings[-1],
            )
        )
        return "portfolio", [], diagnostics

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

    declared_paths = set(roots)
    candidates = [aim_root]
    for parent_name in ("portfolio", "workspaces"):
        parent = aim_root / parent_name
        if parent.is_dir() and not parent.is_symlink():
            candidates.extend(
                child.resolve()
                for child in parent.iterdir()
                if child.is_dir() and not child.is_symlink()
            )
    seen_candidates: set[Path] = set()
    for candidate in candidates:
        if candidate in seen_candidates or not (candidate / "state.json").is_file():
            continue
        seen_candidates.add(candidate)
        try:
            state = _read_json(candidate / "state.json")
        except AimUiError as exc:
            state = {}
            drift = [str(exc)]
        else:
            drift = _contract_drift(state)
        epic_id = state.get("epicId") if isinstance(state.get("epicId"), str) else None
        if candidate not in declared_paths:
            reason = (
                f"{(candidate / 'state.json').relative_to(repo_root).as_posix()} is not "
                f"declared in .aim/{PORTFOLIO_FILE}; the active Portfolio board cannot project it."
            )
            diagnostic = _workspace_diagnostic(
                repo_root,
                candidate,
                kind="orphaned_invisible_workspace",
                reason=reason,
                epic_id=epic_id,
                drift=drift,
            )
            diagnostics.append(diagnostic)
            warnings.append(
                f"{diagnostic['epicId']}: orphaned/invisible workspace at "
                f"{diagnostic['statePath']}. {reason}"
            )
        elif drift:
            diagnostic = _workspace_diagnostic(
                repo_root,
                candidate,
                kind="legacy_contract_drift",
                reason="The declared checkpoint does not match the current runtime contract.",
                epic_id=epic_id,
                drift=drift,
            )
            diagnostics.append(diagnostic)
            warnings.append(
                f"{diagnostic['epicId']}: contract drift at {diagnostic['statePath']}: "
                + "; ".join(drift)
            )
    return "portfolio", roots, diagnostics


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


def _project_epic(
    repo_root: Path, aim_root: Path, warnings: list[str]
) -> dict[str, Any]:
    state = _read_json(aim_root / "state.json")
    _validate_state(state)
    epic_markdown = _read_markdown(aim_root / "epic.md")

    epic_id = str(state["epicId"])
    active_id = state.get("activeIncrementId")
    planned_id = state.get("plannedIncrementId")
    increment_items: list[dict[str, Any]] = []
    increments_root = aim_root / "increments"
    if increments_root.is_dir():
        grouped_paths: dict[str, list[tuple[Path, str]]] = {}
        for path in sorted(increments_root.glob("*.md")):
            markdown = _read_markdown(path)
            increment_id = _increment_id(path, markdown)
            declared_epic = _field(markdown, "Epic")
            is_active = increment_id == active_id
            if declared_epic != epic_id and not (is_active and declared_epic is None):
                continue
            grouped_paths.setdefault(increment_id, []).append((path, markdown))

        for increment_id, artifacts in grouped_paths.items():
            is_active = increment_id == active_id
            is_reserved = (
                increment_id == planned_id
                and active_id is None
                and state["epicStatus"] == "gate_a_pending"
            )
            primary_path, primary_markdown = max(
                artifacts,
                key=lambda item: (
                    item[0].stem.endswith("-wip"),
                    item[0].stem.endswith("-plan"),
                    item[0].name,
                ),
            )
            acceptance_decision = _acceptance_decision(
                repo_root, aim_root, state, increment_id, warnings
            )
            accepted = acceptance_decision is not None
            declared_acceptance = (
                _field(_read_markdown(acceptance_decision), "Accepted at")
                if acceptance_decision is not None
                else None
            )
            delivery_accepted_at = (
                _timestamp_text(parsed_acceptance)
                if (parsed_acceptance := _parse_timestamp(declared_acceptance)) is not None
                else None
            )
            runtime_status = (
                state["epicStatus"]
                if is_active or is_reserved
                else "done_increment_accepted" if accepted else "gate_b_pending"
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
                    "title": _heading(primary_markdown, increment_id),
                    "column": column,
                    "runtimeStatus": runtime_status,
                    "canonicalOwner": owner,
                    "gate": state.get("lastGatePassed") if is_active else "Gate E",
                    "mode": state["mode"],
                    "costProfile": state["costProfile"],
                    "updatedAt": state["updatedAt"] if is_active else None,
                    "acceptedAt": _accepted_at(acceptance_decision) if acceptance_decision else None,
                    "deliveryStartedAt": _gate_b_started_at(aim_root, increment_id),
                    "deliveryAcceptedAt": delivery_accepted_at,
                    "acceptanceEvidence": (
                        acceptance_decision.relative_to(repo_root).as_posix()
                        if acceptance_decision is not None
                        else None
                    ),
                    "active": is_active,
                    "identityReserved": is_reserved,
                    "planned": False,
                    "priority": None,
                    "summary": None,
                    "attention": attention,
                    "evidence": _evidence(
                        repo_root,
                        aim_root,
                        increment_id,
                        [path for path, _ in artifacts],
                        acceptance_decision,
                    ),
                }
            )

    return {
        "id": epic_id,
        "title": _heading(epic_markdown, epic_id),
        "workspace": aim_root.relative_to((repo_root / ".aim").resolve()).as_posix(),
        "active": state["epicStatus"] != "epic_complete",
        "lifecycle": "closed" if state["epicStatus"] == "epic_complete" else "running",
        "runtimeStatus": state["epicStatus"],
        "activeIncrementId": active_id,
        "plannedIncrementId": planned_id,
        "portfolioCandidateId": state.get("portfolioCandidateId"),
        "mode": state["mode"],
        "costProfile": state["costProfile"],
        "currentRole": state["currentRole"],
        "lastGatePassed": state.get("lastGatePassed"),
        "updatedAt": state["updatedAt"],
        "attention": None,
        "actions": [],
        "planning": {"candidateCount": 0, "candidates": [], "nextCandidateId": None},
        "uiDecision": state.get("uiDecision"),
        "increments": increment_items,
        "canonicalRoles": [
            {"name": role, "active": role == state["currentRole"]}
            for role in CANONICAL_ROLES
        ],
        "helperActivity": _load_agents(aim_root, epic_id),
    }


def _reconcile_portfolio_run(
    epics: list[dict[str, Any]],
    backlog_items: list[dict[str, Any]],
    portfolio_run: dict[str, Any],
    warnings: list[str],
) -> None:
    """Fail closed when a Portfolio checkpoint disagrees with canonical runtime state."""

    if not portfolio_run.get("configured") or not portfolio_run.get("valid"):
        return

    epic_by_id = {epic["id"]: epic for epic in epics if epic.get("workspace")}
    backlog_by_id = {item["id"]: item for item in backlog_items}
    candidate_epics = portfolio_run.get("candidateEpics", {})
    candidate_states = portfolio_run.get("candidateStates", {})
    issues: list[str] = []

    for candidate_id, candidate_state in candidate_states.items():
        expected_epic_id = candidate_epics.get(candidate_id)
        backlog = backlog_by_id.get(candidate_id)
        runtime_id = backlog.get("runtimeIncrementId") if backlog else None
        epic = epic_by_id.get(expected_epic_id)

        if candidate_state == "completed":
            increment = next(
                (item for item in (epic or {}).get("increments", []) if item["id"] == runtime_id),
                None,
            )
            if not (
                backlog
                and runtime_id
                and epic
                and epic.get("portfolioCandidateId") == candidate_id
                and epic.get("lifecycle") == "closed"
                and increment
                and increment.get("column") == "done"
                and increment.get("acceptanceEvidence")
            ):
                issues.append(
                    f"Completed Portfolio candidate {candidate_id} does not resolve to a "
                    "closed catalogued workspace, matching runtimeIncrementId, and accepted Gate E evidence."
                )

    active_id = portfolio_run.get("activeCandidateId")
    if active_id:
        expected_epic_id = candidate_epics.get(active_id)
        backlog = backlog_by_id.get(active_id)
        runtime_id = backlog.get("runtimeIncrementId") if backlog else None
        epic = epic_by_id.get(expected_epic_id)
        checkpoint_status = portfolio_run.get("checkpointStatus")

        if not epic and not runtime_id and checkpoint_status == "activation_pending":
            portfolio_run["relationStatus"] = "recoverable"
            portfolio_run["transitionState"] = "activation_pending"
            portfolio_run["guidance"] = (
                f"{active_id} remains Planned until its workspace, state, and runtimeIncrementId "
                "have been created and validated. AIM chat may resume activation."
            )
            candidate_states[active_id] = "activation_pending"
        elif not epic or not runtime_id:
            issues.append(
                f"Portfolio active candidate {active_id} checkpoint {checkpoint_status or 'unknown'} "
                "requires both a catalogued workspace and Backlog runtimeIncrementId; "
                f"workspace={'present' if epic else 'missing'}, runtimeIncrementId={'present' if runtime_id else 'missing'}."
            )
        else:
            increment_ids = {item["id"] for item in epic["increments"]}
            relation_ok = (
                epic.get("portfolioCandidateId") == active_id
                and runtime_id in increment_ids
                and epic.get("activeIncrementId") == runtime_id
                and epic.get("lifecycle") == "running"
                and checkpoint_status == epic.get("runtimeStatus")
            )
            if relation_ok:
                portfolio_run["relationStatus"] = "consistent"
                portfolio_run["transitionState"] = "runtime_active"
                candidate_states[active_id] = "active"
            else:
                issues.append(
                    f"Portfolio active candidate {active_id} disagrees with workspace {expected_epic_id}: "
                    f"candidate={epic.get('portfolioCandidateId') or 'missing'}, "
                    f"runtimeIncrementId={runtime_id}, activeIncrementId={epic.get('activeIncrementId') or 'missing'}, "
                    f"checkpoint={checkpoint_status or 'unknown'}, workspaceStatus={epic.get('runtimeStatus') or 'unknown'}."
                )
    elif portfolio_run.get("transitionState") == "next_activation_pending":
        portfolio_run["relationStatus"] = "recoverable"
        portfolio_run["guidance"] = (
            "The completed outcome is preserved. AIM chat may deterministically activate "
            "the next queued Portfolio candidate."
        )
    else:
        portfolio_run["relationStatus"] = "consistent"

    if issues:
        if active_id:
            candidate_states[active_id] = "contradictory"
        portfolio_run["valid"] = False
        portfolio_run["relationStatus"] = "contradictory"
        portfolio_run["transitionState"] = "contradictory"
        portfolio_run["issue"] = " ".join(issues)
        warnings.extend(issues)


def build_board(repo_root: Path) -> dict[str, Any]:
    """Build a safe multi-Epic UI projection without mutating the repository."""

    repo_root = repo_root.resolve()
    aim_root = (repo_root / ".aim").resolve()
    warnings: list[str] = []
    source_kind, workspaces, workspace_diagnostics = _workspace_roots(
        repo_root, aim_root, warnings
    )
    generated_at = utc_now()
    base = {
        "readModelVersion": READ_MODEL_VERSION,
        "generatedAt": generated_at,
        "source": {
            "kind": source_kind,
            "readOnly": True,
            "refreshMs": DEFAULT_REFRESH_MS,
            "workspaceCount": len(workspaces),
        },
        "columns": [{"id": item[0], "label": item[1]} for item in KANBAN_COLUMNS],
        "epics": [],
        "workspaceDiagnostics": workspace_diagnostics,
        "recovery": None,
        "roadmap": None,
        "history": {
            "recentLimit": RECENT_DELIVERIES_LIMIT,
            "acceptedCount": 0,
            "recentDeliveries": [],
            "closedIncrements": [],
        },
        "deliveryData": None,
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
            epic = _project_epic(repo_root, workspace, warnings)
        except AimUiError as exc:
            warnings.append(f"Workspace {index + 1}: {exc}")
            state = {}
            try:
                state = _read_json(workspace / "state.json")
            except AimUiError:
                pass
            state_path = workspace / "state.json"
            if not any(
                item["statePath"] == state_path.relative_to(repo_root).as_posix()
                for item in workspace_diagnostics
            ):
                workspace_diagnostics.append(
                    _workspace_diagnostic(
                        repo_root,
                        workspace,
                        kind="invalid_declared_workspace",
                        reason=str(exc),
                        epic_id=(
                            state.get("epicId")
                            if isinstance(state.get("epicId"), str)
                            else None
                        ),
                        drift=_contract_drift(state) if state else [str(exc)],
                    )
                )
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
    backlog_warning_start = len(warnings)
    backlog_items = _load_backlog(aim_root, warnings)
    backlog_valid = len(warnings) == backlog_warning_start
    backlog_runtime_candidates = {
        (item["epicId"], item["runtimeIncrementId"]): item["id"]
        for item in backlog_items
        if item["runtimeIncrementId"]
    }
    unresolved_runtime_relations: list[dict[str, Any]] = []
    backlog_updated_at = "unknown"
    if (aim_root / BACKLOG_FILE).is_file():
        try:
            backlog_updated_at = str(_read_json(aim_root / BACKLOG_FILE).get("updatedAt") or "unknown")
        except AimUiError:
            pass
    base["roadmap"] = _roadmap_projection(
        aim_root, backlog_items, backlog_updated_at, backlog_valid
    )
    base["recovery"] = _recovery_projection(
        source_kind, workspace_diagnostics, base["roadmap"]
    )
    for candidate in backlog_items:
        key = (
            candidate["epicId"],
            candidate["runtimeIncrementId"] or candidate["id"],
        )
        if key in runtime_keys:
            continue
        runtime_increment_id = candidate["runtimeIncrementId"]
        if runtime_increment_id:
            reason = (
                f"Preserved history needs review: Backlog candidate {candidate['id']} "
                f"for {candidate['epicId']} references {runtime_increment_id}, but no "
                "active Portfolio workspace contains that Epic and Increment relation. "
                "AIM UI kept it out of Planned work and disabled activation."
            )
            unresolved_runtime_relations.append(
                {
                    "candidateId": candidate["id"],
                    "epicId": candidate["epicId"],
                    "runtimeIncrementId": runtime_increment_id,
                    "reason": reason,
                    "readOnly": True,
                    "activatable": False,
                }
            )
            warnings.append(reason)
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
                "activeIncrementId": None,
                "portfolioCandidateId": None,
                "mode": "Planning",
                "costProfile": None,
                "currentRole": None,
                "lastGatePassed": None,
                "updatedAt": candidate["createdAt"],
                "attention": None,
                "actions": [],
                "planning": {"candidateCount": 0, "candidates": [], "nextCandidateId": None},
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
        epic["planning"]["candidates"].append(candidate)
        epic["planning"]["candidateCount"] = len(epic["planning"]["candidates"])
        epic["planning"]["nextCandidateId"] = epic["planning"]["candidates"][0]["id"]

    control, control_warnings = project_portfolio_control(aim_root, base["epics"])
    warnings.extend(control_warnings)
    base["control"] = control
    portfolio_run, run_warnings = project_portfolio_run(aim_root)
    warnings.extend(run_warnings)
    base["portfolioRun"] = portfolio_run
    candidate_states = portfolio_run.get("candidateStates", {})
    _reconcile_portfolio_run(base["epics"], backlog_items, portfolio_run, warnings)
    for epic in base["epics"]:
        for candidate in epic.get("planning", {}).get("candidates", []):
            candidate["portfolioState"] = candidate_states.get(candidate["id"])
            candidate["decisionAuthority"] = (
                portfolio_run.get("decisionAuthority")
                if candidate["id"] == portfolio_run.get("activeCandidateId")
                else None
            )
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
    _attach_actions(
        repo_root, base["epics"], control, portfolio_run, backlog_updated_at, warnings
    )
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
    for epic in base["epics"]:
        for item in epic["increments"]:
            item["visibleOnBoard"] = item["column"] != "done"
    base["history"] = {
        "recentLimit": RECENT_DELIVERIES_LIMIT,
        "acceptedCount": len(accepted),
        "recentDeliveries": accepted[:RECENT_DELIVERIES_LIMIT],
        "closedIncrements": accepted,
        "unresolvedRuntimeRelations": unresolved_runtime_relations,
    }
    base["deliveryData"] = _delivery_data(base["epics"], accepted, generated_at)
    base["health"] = (
        "degraded"
        if not base["epics"]
        else "partial"
        if warnings or workspace_diagnostics
        else "healthy"
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
