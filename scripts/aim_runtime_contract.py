#!/usr/bin/env python3
"""Shared executable AIM runtime-state and Gate E evidence contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


CANONICAL_RUNTIME_STATUSES = {
    "epic_initialized",
    "gate_a_pending",
    "gate_b_pending",
    "increment_in_progress",
    "epic_paused",
    "blocked",
    "review_in_progress",
    "tdo_validation_in_progress",
    "po_approval_pending",
    "done_increment_accepted",
    "epic_complete",
}
PORTFOLIO_CHECKPOINT_STATUSES = CANONICAL_RUNTIME_STATUSES | {"activation_pending"}
TERMINAL_RUNTIME_STATUSES = {"done_increment_accepted", "epic_complete"}
MAX_ACCEPTANCE_DECISION_BYTES = 1_000_000


def markdown_field(markdown: str, label: str) -> str | None:
    match = re.search(
        rf"^{re.escape(label)}:\s*(?:`([^`]+)`|(.+?))\s*$",
        markdown,
        re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return None
    return (match.group(1) or match.group(2)).strip()


def decision_accepts_increment(path: Path, increment_id: str) -> bool:
    """Return whether one bounded regular Markdown file accepts the Increment."""

    if path.is_symlink() or not path.is_file():
        return False
    try:
        if path.stat().st_size > MAX_ACCEPTANCE_DECISION_BYTES:
            return False
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    decision = markdown_field(content, "Decision") or ""
    status = markdown_field(content, "Status") or ""
    authority_fields = f"{decision}\n{status}"
    if re.search(
        r"\b(?:change requested|pending|rejected|not accepted)\b",
        authority_fields,
        re.IGNORECASE,
    ):
        return False
    heading = content.splitlines()[0] if content.splitlines() else ""
    accepted = any(
        (
            re.search(
                r"\b(?:accept(?:ed)?|approv(?:e|ed))\b",
                authority_fields,
                re.IGNORECASE,
            ),
            markdown_field(content, "Accepted at"),
            re.search(
                r"\bGate E\b.*\bAccepted\b|\bAccepted\b.*\bGate E\b",
                heading,
                re.IGNORECASE,
            ),
            re.search(
                r"^Accepted\s+(?:by|on|under|as part of)\b",
                content,
                re.IGNORECASE | re.MULTILINE,
            ),
        )
    )
    if not accepted:
        return False
    mentioned = {item.upper() for item in re.findall(r"\bDI-\d+\b", content, re.I)}
    return not mentioned or increment_id in mentioned


def terminal_acceptance(
    repo_root: Path,
    workspace: Path,
    state: dict[str, Any],
    increment_id: str,
) -> tuple[Path | None, list[str]]:
    """Resolve the structured terminal acceptance relation and exact failures."""

    issues: list[str] = []
    if state.get("epicStatus") not in TERMINAL_RUNTIME_STATUSES:
        issues.append("workspace status is not terminal")
    if state.get("previousIncrementId") != increment_id:
        issues.append("previousIncrementId does not match the Backlog runtime Increment")
    if state.get("previousIncrementStatus") != "accepted":
        issues.append("previousIncrementStatus is not accepted")
    if state.get("lastGatePassed") != "Gate E":
        issues.append("lastGatePassed is not Gate E")

    raw_path = state.get("gateEAcceptance")
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append("gateEAcceptance is missing")
        return None, issues
    if "\\" in raw_path:
        issues.append("gateEAcceptance does not use POSIX separators")
        return None, issues
    relative = Path(raw_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != ".aim"
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        issues.append("gateEAcceptance is not a contained repository-relative .aim path")
        return None, issues

    current = repo_root.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            issues.append("gateEAcceptance traverses a symbolic link")
            return None, issues
    try:
        decision = (repo_root.resolve() / relative).resolve()
        decision.relative_to(workspace.resolve())
    except (OSError, ValueError):
        issues.append("gateEAcceptance leaves the authoritative workspace")
        return None, issues
    if decision.parent != (workspace / "decisions").resolve():
        issues.append("gateEAcceptance is not in the workspace decisions directory")
        return None, issues
    if not decision_accepts_increment(decision, increment_id):
        issues.append("gateEAcceptance is missing, oversized, mismatched, or not accepted")
        return None, issues
    return decision, issues
