# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_actions.py
"""Pure AIM UI action envelopes and Codex handoff helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


ACTION_VERSION = "1.2"
WORKSPACE_ACTION_VERSION = "1.1"
LEGACY_ACTION_VERSION = "1.0"
SUPPORTED_ACTION_VERSIONS = {
    LEGACY_ACTION_VERSION,
    WORKSPACE_ACTION_VERSION,
    ACTION_VERSION,
}
ACTIONS = {"activate", "approve", "change"}
EPIC_RE = re.compile(r"EPIC-[A-Z0-9-]{1,115}\Z")
INC_RE = re.compile(r"INC-[A-Z0-9-]{1,76}\Z")
DI_RE = re.compile(r"DI-\d{1,12}\Z")
HARD_GATES = {"Gate A", "Gate B", "Gate E"}
GATE_EXPECTATIONS = {
    "Gate A": ("gate_a_pending", None),
    "Gate B": ("gate_b_pending", "Gate A"),
    "Gate E": ("po_approval_pending", "Gate D"),
}
ACTION_PROMPT_PREAMBLE = (
    "Process this user-initiated AIM UI action with $agile-iteration-method. "
    "For a v1.2 gate action, read authorityStatePath exactly relative to the "
    "repository root before reading any other runtime state file; never begin "
    "with .aim/state.json when another path is named, and reject traversal, "
    "symlink escape, or containment failure. Treat "
    "gate as the requested decision point and expectedLastGatePassed as the "
    "raw state checkpoint. Before changing anything and again immediately "
    "before writing, reject any stale identity, status, checkpoint, timestamp, "
    "replay, or portfolio-admission condition. For a v1.1 compatibility gate "
    "action, resolve workspace relative to .aim; a v1.0 envelope has no direct "
    "runtime locator and must use the documented fail-closed compatibility "
    "resolution. Approve at Gate E accepts the Increment only; it does not close "
    "the Epic."
)


class AimActionError(ValueError):
    """A bounded action envelope is invalid or stale."""


def action_envelope(
    action: str,
    *,
    epic_id: str,
    expected_updated_at: str,
    candidate_id: str | None = None,
    increment_id: str | None = None,
    gate: str | None = None,
    expected_status: str | None = None,
    authority_state_path: str | None = None,
    expected_last_gate_passed: str | None = None,
    backlog_updated_at: str | None = None,
) -> dict[str, Any]:
    """Create one canonical, data-only action envelope."""

    value = {
        "actionVersion": ACTION_VERSION,
        "action": action,
        "epicId": epic_id,
        "expectedUpdatedAt": expected_updated_at,
    }
    optional = {
        "candidateId": candidate_id,
        "incrementId": increment_id,
        "gate": gate,
        "expectedStatus": expected_status,
        "authorityStatePath": authority_state_path,
        "backlogUpdatedAt": backlog_updated_at,
    }
    value.update({key: item for key, item in optional.items() if item is not None})
    if action != "activate":
        value["expectedLastGatePassed"] = expected_last_gate_passed
    validate_action_envelope(value)
    return value


def _validate_workspace_selector(value: Any) -> None:
    """Require a bounded POSIX path relative to the repository's `.aim`."""

    if not isinstance(value, str) or not 1 <= len(value) <= 240:
        raise AimActionError("workspace must be a bounded path relative to .aim.")
    if value == ".":
        return
    if value.startswith("/") or "\\" in value or any(ord(char) < 32 for char in value):
        raise AimActionError("workspace must be a POSIX path relative to .aim.")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise AimActionError("workspace must not contain empty, dot, or traversal segments.")


def _validate_authority_state_path(value: Any) -> None:
    """Require an exact state file path contained by repository `.aim`."""

    if not isinstance(value, str) or not 1 <= len(value) <= 320:
        raise AimActionError("authorityStatePath must be a bounded repository-relative path.")
    if value.startswith("/") or "\\" in value or any(ord(char) < 32 for char in value):
        raise AimActionError("authorityStatePath must be a repository-relative POSIX path.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AimActionError(
            "authorityStatePath must not contain empty, dot, or traversal segments."
        )
    if parts[0] != ".aim" or parts[-1] != "state.json":
        raise AimActionError("authorityStatePath must identify a state.json file under .aim.")


def resolve_action_state_path(repo_root: Path, envelope: dict[str, Any]) -> Path:
    """Resolve a v1.2 gate action to one exact state file under `.aim`."""

    validate_action_envelope(envelope)
    if envelope.get("actionVersion") != ACTION_VERSION or envelope.get("action") == "activate":
        raise AimActionError("Only v1.2 gate actions have an authorityStatePath.")
    selector = envelope.get("authorityStatePath")
    _validate_authority_state_path(selector)
    aim_root = (repo_root.resolve() / ".aim").resolve()
    candidate = repo_root.resolve().joinpath(*selector.split("/"))
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(aim_root)
    except (FileNotFoundError, ValueError) as exc:
        raise AimActionError(
            "authorityStatePath is missing or leaves the repository .aim root."
        ) from exc
    if not resolved.is_file():
        raise AimActionError("authorityStatePath is not a file.")
    return resolved


def resolve_action_workspace(repo_root: Path, envelope: dict[str, Any]) -> Path:
    """Resolve a v1.1 gate-action workspace without allowing escape from `.aim`."""

    validate_action_envelope(envelope)
    if (
        envelope.get("actionVersion") != WORKSPACE_ACTION_VERSION
        or envelope.get("action") == "activate"
    ):
        raise AimActionError("Only v1.1 gate actions have a deterministic workspace selector.")
    selector = envelope.get("workspace")
    if not isinstance(selector, str):
        raise AimActionError("This action version has no deterministic workspace selector.")
    aim_root = (repo_root.resolve() / ".aim").resolve()
    candidate = aim_root if selector == "." else aim_root.joinpath(*selector.split("/"))
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(aim_root)
    except (FileNotFoundError, ValueError) as exc:
        raise AimActionError("workspace is missing or leaves the repository .aim root.") from exc
    state_path = resolved / "state.json"
    try:
        state_path.resolve(strict=True).relative_to(aim_root)
    except (FileNotFoundError, ValueError) as exc:
        raise AimActionError("workspace state.json is missing or leaves the .aim root.") from exc
    if not state_path.is_file():
        raise AimActionError("workspace state.json is not a file.")
    return resolved


def validate_action_envelope(value: Any) -> None:
    """Reject malformed or ambiguous action envelopes."""

    if not isinstance(value, dict):
        raise AimActionError("Action envelope must be an object.")
    allowed = {
        "actionVersion", "action", "epicId", "candidateId", "incrementId",
        "gate", "expectedStatus", "expectedUpdatedAt", "backlogUpdatedAt",
        "changeRequest", "workspace", "authorityStatePath", "expectedLastGatePassed",
    }
    extra = sorted(set(value) - allowed)
    if extra:
        raise AimActionError(f"Unsupported action fields: {', '.join(extra)}.")
    version = value.get("actionVersion")
    if version not in SUPPORTED_ACTION_VERSIONS:
        raise AimActionError(
            "actionVersion must be one of "
            f"{', '.join(sorted(SUPPORTED_ACTION_VERSIONS))}."
        )
    action = value.get("action")
    if action not in ACTIONS:
        raise AimActionError("Action must be activate, approve, or change.")
    if version == LEGACY_ACTION_VERSION and any(
        field in value
        for field in ("workspace", "authorityStatePath", "expectedLastGatePassed")
    ):
        raise AimActionError("v1.0 envelopes cannot contain newer locator fields.")
    if not isinstance(value.get("epicId"), str) or not EPIC_RE.fullmatch(value["epicId"]):
        raise AimActionError("epicId must be a canonical EPIC-* id.")
    timestamp = value.get("expectedUpdatedAt")
    if not isinstance(timestamp, str) or not 1 <= len(timestamp) <= 64:
        raise AimActionError("expectedUpdatedAt must be present and bounded.")
    if action == "activate":
        if not isinstance(value.get("candidateId"), str) or not INC_RE.fullmatch(value["candidateId"]):
            raise AimActionError("Activate requires a canonical INC-* candidateId.")
        if "incrementId" in value or "gate" in value:
            raise AimActionError("Activate cannot target a runtime Increment or gate.")
        if not isinstance(value.get("backlogUpdatedAt"), str):
            raise AimActionError("Activate requires backlogUpdatedAt.")
        if any(
            field in value
            for field in ("workspace", "authorityStatePath", "expectedLastGatePassed")
        ):
            raise AimActionError("Activate uses portfolio authority, not a runtime workspace.")
    else:
        if value.get("gate") not in HARD_GATES:
            raise AimActionError("Gate actions require Gate A, Gate B, or Gate E.")
        if value.get("gate") == "Gate A":
            if not isinstance(value.get("candidateId"), str) or not INC_RE.fullmatch(value["candidateId"]):
                raise AimActionError("Gate A actions require a canonical INC-* candidateId.")
            if "incrementId" in value:
                raise AimActionError("Gate A cannot target a runtime Increment.")
        elif not isinstance(value.get("incrementId"), str) or not DI_RE.fullmatch(value["incrementId"]):
            raise AimActionError("Gate B and Gate E require a canonical DI-* incrementId.")
        if not isinstance(value.get("expectedStatus"), str):
            raise AimActionError("Gate actions require expectedStatus.")
        if version == WORKSPACE_ACTION_VERSION:
            _validate_workspace_selector(value.get("workspace"))
            if "authorityStatePath" in value:
                raise AimActionError("v1.1 gate actions cannot contain authorityStatePath.")
        elif version == ACTION_VERSION:
            _validate_authority_state_path(value.get("authorityStatePath"))
            if "workspace" in value:
                raise AimActionError("v1.2 gate actions cannot contain workspace.")
        if version in {WORKSPACE_ACTION_VERSION, ACTION_VERSION}:
            if "expectedLastGatePassed" not in value or value.get(
                "expectedLastGatePassed"
            ) not in {None, "Gate A", "Gate B", "Gate C", "Gate D"}:
                raise AimActionError(
                    f"v{version} gate actions require expectedLastGatePassed from raw state."
                )
            expected_status, expected_checkpoint = GATE_EXPECTATIONS[value["gate"]]
            if value["expectedStatus"] != expected_status:
                raise AimActionError(
                    f"{value['gate']} requires expectedStatus {expected_status}."
                )
            if value["expectedLastGatePassed"] != expected_checkpoint:
                raise AimActionError(
                    f"{value['gate']} requires expectedLastGatePassed "
                    f"{expected_checkpoint!r}."
                )
    request = value.get("changeRequest")
    if request is not None and (
        action != "change" or not isinstance(request, str) or not 1 <= len(request.strip()) <= 2_000
    ):
        raise AimActionError("changeRequest is valid only for Change and must be 1-2000 characters.")


def action_prompt(envelope: dict[str, Any]) -> str:
    """Render a reviewable prompt; the receiving AIM thread still revalidates it."""

    validate_action_envelope(envelope)
    payload = json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True)
    return f"{ACTION_PROMPT_PREAMBLE}\n\nAIM_ACTION_ENVELOPE\n{payload}"


def codex_deep_link(repo_root: Path, envelope: dict[str, Any]) -> str:
    """Open a new Codex composer in this repo; deep links never auto-send."""

    query = urlencode({"prompt": action_prompt(envelope), "path": str(repo_root.resolve())})
    return f"codex://new?{query}"


def validate_against_current(
    envelope: dict[str, Any], current: dict[str, Any], *, admission_allowed: bool = True
) -> list[str]:
    """Compare an envelope with freshly loaded authority before mutation."""

    validate_action_envelope(envelope)
    issues: list[str] = []
    for expected_key, current_key in (
        ("epicId", "epicId"),
        ("candidateId", "candidateId"),
        ("incrementId", "incrementId"),
        ("gate", "gate"),
        ("expectedStatus", "status"),
        ("workspace", "workspace"),
        ("authorityStatePath", "authorityStatePath"),
        ("expectedLastGatePassed", "lastGatePassed"),
        ("expectedUpdatedAt", "updatedAt"),
        ("backlogUpdatedAt", "backlogUpdatedAt"),
    ):
        if expected_key in envelope and envelope[expected_key] != current.get(current_key):
            issues.append(f"{expected_key} is stale or mismatched.")
    if envelope["action"] == "activate" and not admission_allowed:
        issues.append("Portfolio admission is no longer available.")
    return issues
