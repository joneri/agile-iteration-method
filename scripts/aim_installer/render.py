"""Render the install plan as human-readable text or machine-readable JSON."""

from __future__ import annotations

import json
from typing import Any


_CLASS_GLYPH = {
    "create": "+",
    "modify": "~",
    "untouched": "=",
    "collision": "!",
}


def render_json(plan: dict[str, Any]) -> str:
    return json.dumps(plan, indent=2, sort_keys=False)


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def render_compact_text(plan: dict[str, Any], *, color: bool = False) -> str:
    """Render the normal-user summary without dumping every planned action."""

    summary = plan.get("summary", {})
    counts = summary.get("byClassification", {})
    collisions = [a for a in plan["actions"] if a["classification"] == "collision"]
    blockers = plan.get("blockers", [])
    operation = "Apply" if plan.get("operation") == "apply" else "Preview"

    lines = [
        _paint(f"AIM 2.0 installer · {operation}", "1;36", color),
        f"Target    {plan['target']}",
        f"Mode      {plan['mode']}",
        f"Adapters  {', '.join(plan['adapters']) or '(none)'}",
        "",
        (
            f"{summary.get('total', 0)} actions · "
            f"{counts.get('create', 0)} create · "
            f"{counts.get('modify', 0)} update · "
            f"{counts.get('untouched', 0)} current · "
            f"{counts.get('collision', 0)} need attention"
        ),
    ]

    if collisions:
        lines.extend(["", _paint("Needs your decision", "1;33", color)])
        lines.extend(f"  ! {action['destination']}" for action in collisions)
    if blockers:
        lines.extend(["", _paint("Blocked", "1;31", color)])
        lines.extend(f"  x {blocker}" for blocker in blockers)

    validator = plan.get("validator", {})
    lines.append("")
    lines.append(
        "Source validation  "
        + _paint(str(validator.get("resultClass", "unknown")), "32", color)
    )
    if plan.get("operation") == "apply":
        if collisions:
            lines.append("Next  resolve each collision, then apply")
        elif blockers:
            lines.append("Next  resolve blockers before applying")
        else:
            lines.append("Next  apply this plan")
    else:
        lines.append("No files were written. Add --apply when ready.")
        lines.append("Use --verbose for every file action or --format json for automation.")
    return "\n".join(lines)


def render_verbose_text(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    operation = "apply" if plan.get("operation") == "apply" else "dry-run"
    lines.append(f"AIM 2.0 install plan ({operation})")
    lines.append("=" * 32)
    lines.append(f"Manifest version : {plan['manifestVersion']}")
    lines.append(f"Mode             : {plan['mode']}")
    lines.append(f"Adapters         : {', '.join(plan['adapters']) or '(none)'}")
    lines.append(f"Source           : {plan['source']}")
    lines.append(f"Target           : {plan['target']}")

    validator = plan.get("validator", {})
    lines.append(
        "Validator        : "
        f"{validator.get('resultClass', 'unknown')} "
        f"(exit {validator.get('exitCode')})"
    )

    bootstrap = plan.get("bootstrap", {})
    lines.append(
        "Bootstrap        : "
        f"{bootstrap.get('status')} -> {bootstrap.get('calibrationCommand')}"
    )

    lines.append("")
    lines.append("Planned actions:")
    if not plan["actions"]:
        lines.append("  (none)")
    for action in plan["actions"]:
        glyph = _CLASS_GLYPH.get(action["classification"], "?")
        optional = " [optional]" if action["optional"] else ""
        lines.append(
            f"  {glyph} {action['classification']:<9} "
            f"{action['destination']}{optional}"
        )
        src = action["source"] if action["source"] else "(generated)"
        lines.append(f"      from   : {src}")
        lines.append(f"      reason : {action['reason']}")

    summary = plan.get("summary", {})
    by_class = summary.get("byClassification", {})
    lines.append("")
    lines.append("Summary:")
    lines.append(f"  total      : {summary.get('total', 0)}")
    lines.append(
        "  by class   : "
        + ", ".join(f"{k}={v}" for k, v in by_class.items())
    )

    excluded = plan.get("rootFileExclusions", [])
    if excluded:
        lines.append("")
        lines.append("Root files excluded (never touched):")
        for entry in excluded:
            lines.append(f"  - {entry['path']}: {entry['reason']}")

    collisions = [a for a in plan["actions"] if a["classification"] == "collision"]
    if collisions:
        lines.append("")
        lines.append("Collisions need explicit review before apply:")
        for action in collisions:
            lines.append(f"  ! {action['destination']}")

    blockers = plan.get("blockers", [])
    if blockers:
        lines.append("")
        lines.append("Blockers:")
        for blocker in blockers:
            lines.append(f"  x {blocker}")

    guidance = plan.get("guidance")
    if guidance:
        lines.append("")
        lines.append(
            f"Install state: {guidance['installState']} "
            f"(intent: {guidance['operationIntent']})"
        )
        lines.append("Next steps:")
        for step in guidance["steps"]:
            lines.append(f"  - {step}")

    lines.append("")
    if plan.get("operation") == "apply":
        lines.append(
            "Apply mode: unresolved collisions require decisions or --force; "
            "writes are rollback-protected."
        )
    else:
        lines.append("This is a dry-run. No files were written. Use --apply to write.")
    return "\n".join(lines)


def render_text(
    plan: dict[str, Any], *, verbose: bool = False, color: bool = False
) -> str:
    if verbose:
        return render_verbose_text(plan)
    return render_compact_text(plan, color=color)
