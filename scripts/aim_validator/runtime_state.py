"""Read-only compatibility and structural validation for AIM runtime state."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aim_validator.schema_subset import validate as validate_schema


RUNTIME_STATE_SCHEMA_PATH = "schemas/aim-runtime-state.schema.json"
SUPPORTED_STATE_SCHEMA_VERSION = "1.0"
LEGACY_ALIASES = {
    "executionMode": "mode",
    "cost": "costProfile",
    "status": "epicStatus",
    "activeIncrement": "activeIncrementId",
    "role": "currentRole",
    "lastGate": "lastGatePassed",
}


@dataclass(frozen=True)
class RuntimeStateFinding:
    result: str
    rule: str
    action: str


@dataclass(frozen=True)
class RuntimeStateResult:
    classification: str
    raw: dict[str, Any] | None
    normalized: dict[str, Any] | None
    findings: tuple[RuntimeStateFinding, ...]


def load_runtime_state(repo_root: Path) -> RuntimeStateResult:
    """Load and validate state without ever writing the source file."""

    state_path = repo_root / ".aim/state.json"
    if not state_path.is_file():
        return RuntimeStateResult("missing", None, None, ())

    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return RuntimeStateResult(
            "contradictory",
            None,
            None,
            (
                RuntimeStateFinding(
                    "contradictory",
                    f"invalid JSON syntax: {exc.msg}",
                    "Repair .aim/state.json before resume.",
                ),
            ),
        )
    if not isinstance(raw, dict):
        return RuntimeStateResult(
            "contradictory",
            None,
            None,
            (
                RuntimeStateFinding(
                    "contradictory",
                    "runtime state root must be an object",
                    "Replace the root value with the canonical state object.",
                ),
            ),
        )

    normalized = dict(raw)
    findings: list[RuntimeStateFinding] = []
    version = raw.get("stateSchemaVersion")
    if version is None:
        classification = "legacy-compatible"
        normalized["stateSchemaVersion"] = SUPPORTED_STATE_SCHEMA_VERSION
        findings.append(
            RuntimeStateFinding(
                "recoverable",
                "legacy runtime state has no stateSchemaVersion; a read-only normalized view was used",
                "Keep the file unchanged while active; add stateSchemaVersion only through an explicit main-thread migration decision.",
            )
        )
    elif version != SUPPORTED_STATE_SCHEMA_VERSION:
        return RuntimeStateResult(
            "unsupported",
            raw,
            None,
            (
                RuntimeStateFinding(
                    "contradictory",
                    f"unsupported stateSchemaVersion {version!r}",
                    f"Use a runtime that supports the schema or explicitly migrate to {SUPPORTED_STATE_SCHEMA_VERSION}.",
                ),
            ),
        )
    else:
        classification = "current"

    for legacy, canonical in LEGACY_ALIASES.items():
        if legacy not in normalized:
            continue
        if classification == "current":
            classification = "legacy-compatible"
            findings.append(
                RuntimeStateFinding(
                    "recoverable",
                    f"legacy field {legacy} was normalized read-only to {canonical}",
                    "Keep active state unchanged until an explicit main-thread migration decision.",
                )
            )
        if canonical in normalized and normalized[canonical] != normalized[legacy]:
            findings.append(
                RuntimeStateFinding(
                    "contradictory",
                    f"legacy field {legacy} conflicts with canonical field {canonical}",
                    "Resolve the conflict explicitly before resume.",
                )
            )
            continue
        normalized.setdefault(canonical, normalized[legacy])
        normalized.pop(legacy, None)

    schema_path = repo_root / RUNTIME_STATE_SCHEMA_PATH
    if not schema_path.is_file():
        findings.append(
            RuntimeStateFinding(
                "blocked",
                f"runtime-state schema is missing: {RUNTIME_STATE_SCHEMA_PATH}",
                "Restore the canonical schema before validating or resuming state.",
            )
        )
        return RuntimeStateResult(
            "blocked", raw, normalized, tuple(findings)
        )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for issue in validate_schema(normalized, schema):
        findings.append(
            RuntimeStateFinding(
                "contradictory",
                f"runtime-state schema: {issue}",
                "Repair the named canonical field before resume.",
            )
        )

    _check_gate_decision_alignment(repo_root, normalized, findings)
    if any(item.result == "contradictory" for item in findings):
        classification = "contradictory"
    return RuntimeStateResult(
        classification, raw, normalized, tuple(findings)
    )


def _check_gate_decision_alignment(
    repo_root: Path,
    state: dict[str, Any],
    findings: list[RuntimeStateFinding],
) -> None:
    increment_id = state.get("activeIncrementId")
    if not isinstance(increment_id, str):
        return
    match = re.fullmatch(r"(?:DI-)?(\d+)", increment_id)
    if not match:
        return
    suffix = match.group(1).zfill(3)
    decision_path = repo_root / f".aim/decisions/{suffix}-gate-b.md"
    if not decision_path.is_file():
        return
    content = decision_path.read_text(encoding="utf-8", errors="replace")
    for label, field in (("Mode", "mode"), ("Cost profile", "costProfile")):
        decision_match = re.search(rf"^{re.escape(label)}:\s*(.+?)\s*$", content, re.MULTILINE)
        if decision_match and decision_match.group(1) != state.get(field):
            findings.append(
                RuntimeStateFinding(
                    "contradictory",
                    f"{field} in state.json differs from {decision_path.name}",
                    "Align the persisted state with the visible Gate B decision through the main AIM thread.",
                )
            )
