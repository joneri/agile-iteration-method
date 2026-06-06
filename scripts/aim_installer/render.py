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


def render_text(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("AIM 2.0 install plan (dry-run)")
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
        lines.append("Apply mode: collisions require --force (backups are kept).")
    else:
        lines.append("This is a dry-run. No files were written. Use --apply to write.")
    return "\n".join(lines)
