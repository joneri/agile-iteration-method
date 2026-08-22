# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_portfolio.py
"""Safe portfolio focus and admission policy for AIM runtime workspaces."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


CONTROL_FILE = "portfolio-control.json"
CONTROL_VERSION = "1.0"
MAX_CONTROL_BYTES = 16_384
MAX_ACTIVE_EPICS = 16
ALLOWED_FIELDS = {
    "controlVersion",
    "maxActiveEpics",
    "focusedEpicId",
    "updatedAt",
}


def _unconfigured() -> dict[str, Any]:
    return {
        "configured": False,
        "valid": True,
        "maxActiveEpics": None,
        "focusedEpicId": None,
        "updatedAt": None,
        "issue": None,
    }


def _invalid(issue: str) -> dict[str, Any]:
    return {
        "configured": True,
        "valid": False,
        "maxActiveEpics": None,
        "focusedEpicId": None,
        "updatedAt": None,
        "issue": issue,
    }


def validate_control_document(value: Any) -> list[str]:
    """Validate the small runtime contract without executing repository code."""

    if not isinstance(value, dict):
        return [f"{CONTROL_FILE} must contain a JSON object."]
    issues: list[str] = []
    extra = sorted(set(value) - ALLOWED_FIELDS)
    if extra:
        issues.append(f"{CONTROL_FILE} contains unsupported fields: {', '.join(extra)}.")
    if value.get("controlVersion") != CONTROL_VERSION:
        issues.append(f"{CONTROL_FILE} must declare controlVersion {CONTROL_VERSION}.")
    maximum = value.get("maxActiveEpics")
    if (
        not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or not 1 <= maximum <= MAX_ACTIVE_EPICS
    ):
        issues.append(
            f"{CONTROL_FILE} maxActiveEpics must be an integer from 1 to {MAX_ACTIVE_EPICS}."
        )
    focused = value.get("focusedEpicId")
    if focused is not None and (
        not isinstance(focused, str)
        or len(focused) > 120
        or re.fullmatch(r"EPIC-[A-Z0-9-]+", focused) is None
    ):
        issues.append(f"{CONTROL_FILE} focusedEpicId must be a canonical EPIC-* id.")
    updated_at = value.get("updatedAt")
    if not isinstance(updated_at, str) or not 1 <= len(updated_at.strip()) <= 64:
        issues.append(f"{CONTROL_FILE} updatedAt must be a non-empty timestamp string.")
    return issues


def load_portfolio_control(aim_root: Path) -> dict[str, Any]:
    """Load optional control state; invalid configured state remains fail-closed."""

    path = aim_root / CONTROL_FILE
    if path.is_symlink():
        return _invalid(f"{CONTROL_FILE} must not be a symbolic link.")
    if not path.is_file():
        return _unconfigured()
    try:
        path.resolve().relative_to(aim_root.resolve())
    except (OSError, ValueError):
        return _invalid(f"{CONTROL_FILE} must resolve inside the .aim directory.")
    try:
        if path.stat().st_size > MAX_CONTROL_BYTES:
            return _invalid(f"{CONTROL_FILE} is larger than {MAX_CONTROL_BYTES} bytes.")
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return _invalid(f"{CONTROL_FILE} could not be read: {exc}.")
    except json.JSONDecodeError as exc:
        return _invalid(f"{CONTROL_FILE} contains invalid JSON at line {exc.lineno}.")
    issues = validate_control_document(value)
    if issues:
        return _invalid(" ".join(issues))
    return {
        "configured": True,
        "valid": True,
        "maxActiveEpics": value["maxActiveEpics"],
        "focusedEpicId": value.get("focusedEpicId"),
        "updatedAt": value["updatedAt"].strip(),
        "issue": None,
    }


def project_portfolio_control(
    aim_root: Path, epics: Iterable[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Project focus and capacity without mutating any workspace."""

    epic_list = list(epics)
    running = [epic["id"] for epic in epic_list if epic.get("lifecycle") == "running"]
    known = {epic["id"] for epic in epic_list}
    control = load_portfolio_control(aim_root)
    warnings: list[str] = []

    if not control["valid"]:
        warnings.append(control["issue"])
        return (
            {
                **control,
                "runningEpics": len(running),
                "availableSlots": None,
                "overCapacity": False,
                "admission": "blocked",
                "focusStatus": "invalid",
            },
            warnings,
        )

    maximum = control["maxActiveEpics"]
    if maximum is None:
        available = None
        over_capacity = False
        admission = "unbounded"
    else:
        available = max(maximum - len(running), 0)
        over_capacity = len(running) > maximum
        admission = "over_capacity" if over_capacity else "full" if available == 0 else "open"

    focused = control["focusedEpicId"]
    if focused is None:
        focus_status = "none"
    elif focused not in known:
        focus_status = "stale"
        warnings.append(
            f"{CONTROL_FILE} focusedEpicId {focused} does not match a visible Epic."
        )
    elif focused in running:
        focus_status = "running"
    else:
        focus_status = "planned_or_closed"

    return (
        {
            **control,
            "runningEpics": len(running),
            "availableSlots": available,
            "overCapacity": over_capacity,
            "admission": admission,
            "focusStatus": focus_status,
        },
        warnings,
    )


def activation_decision(
    control: dict[str, Any], running_epic_ids: Iterable[str], requested_epic_id: str
) -> dict[str, str | bool]:
    """Return the main-thread admission decision for one requested Epic."""

    running = set(running_epic_ids)
    if not control.get("valid", False):
        return {
            "allowed": False,
            "reason": "control_invalid",
            "message": "Repair portfolio-control.json before activating another Epic.",
        }
    if requested_epic_id in running:
        return {
            "allowed": True,
            "reason": "already_running",
            "message": "The requested Epic already owns an active runtime workspace.",
        }
    maximum = control.get("maxActiveEpics")
    if maximum is None:
        return {
            "allowed": True,
            "reason": "legacy_unbounded",
            "message": "No explicit portfolio capacity is configured.",
        }
    if len(running) >= maximum:
        return {
            "allowed": False,
            "reason": "capacity_full",
            "message": (
                f"Portfolio capacity is full ({len(running)}/{maximum}); finish or pause "
                "an Epic, or explicitly raise the capacity."
            ),
        }
    return {
        "allowed": True,
        "reason": "slot_available",
        "message": f"A portfolio slot is available ({len(running)}/{maximum}).",
    }
