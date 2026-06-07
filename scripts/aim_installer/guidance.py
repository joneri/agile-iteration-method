"""Install-state detection and post-install guidance (FR10, FR11).

Both are pure functions over a computed plan dict, so they stay decoupled from
plan computation and are easy to test.
"""

from __future__ import annotations

from typing import Any


_START_COMMANDS = {
    "copilot": 'Copilot: open chat and run  /aim start "EPIC: ..."',
    "claude": 'Claude: run  /aim start "EPIC: ..."  (.claude/commands installed)',
    "codex": "Codex: invoke the agile-iteration-method skill, then start an Epic",
}


def detect_install_state(actions: list[dict[str, Any]]) -> str:
    """Classify the target's current install state from plan actions."""

    classes = {a["classification"] for a in actions}
    if not classes:
        return "empty"
    if classes <= {"untouched"}:
        return "up-to-date"
    if "collision" in classes:
        return "drifted"
    if classes <= {"create"}:
        return "fresh"
    return "partial"


def _operation_intent(state: str) -> str:
    return {
        "fresh": "install",
        "partial": "update",
        "drifted": "reconfigure-or-refresh",
        "up-to-date": "none",
        "empty": "install",
    }.get(state, "update")


def build_guidance(plan: dict[str, Any]) -> dict[str, Any]:
    """Produce post-install guidance tailored to state, mode, and adapters."""

    state = detect_install_state(plan["actions"])
    intent = _operation_intent(state)
    command = "python3 scripts/aim_install.py"
    target = plan["target"]
    steps: list[str] = []

    if state in ("fresh", "partial"):
        steps.append(
            f"Apply the plan: {command} --target {target} "
            f"--mode {plan['mode']} --footprint {plan['footprint']} --apply"
        )
        if state == "partial":
            steps.append(
                "Existing AIM files were detected. Prefer /aim upgrade when "
                "using packaged AIM commands; it runs this reviewed installer "
                "refresh and preserves active .aim runtime state."
            )
    elif state == "empty":
        steps.append(
            "No files are selected for installation. Use explicit AIM intent, "
            "select Codex for a local package, or choose a broader footprint."
        )
    elif state == "drifted":
        steps.append(
            "Some installed files differ from the AIM source (see stalePackages / "
            "collisions). Refresh with --apply --force (rollback-protected), or "
            "keep your local edits by leaving them as-is."
        )
        steps.append(
            "For an existing AIM 1.x or drifted AIM install, /aim upgrade is the "
            "normal packaged command before start, continue, or calibration; it "
            "must not silently replace active .aim runtime state."
        )
    else:  # up-to-date
        steps.append("Install is current; no apply needed.")

    steps.append(
        "Reconfigure later by re-running with different --mode / --footprint / "
        "--adapter; "
        "update or repair by re-running with --apply (use --force to overwrite drift)."
    )

    skipped_adapters = set(plan.get("scopeSummary", {}).get("skippedAdapters", []))
    for adapter in plan["adapters"]:
        if adapter in skipped_adapters:
            steps.append(
                f"{adapter.title()} repo package was not installed by the "
                f"{plan['footprint']} footprint; use explicit AIM intent or "
                "choose the adapters/full footprint."
            )
            continue
        start = _START_COMMANDS.get(adapter)
        if start:
            steps.append("Start AIM — " + start)

    steps.append(
        "Calibrate repo knowledge: /aim calibrate-repo  "
        "(bootstrap is NOT 'ready' until you calibrate)."
    )
    steps.append(
        'Capture knowledge: /aim remember-repo <category> "<rule>"  '
        "(remove with /aim forget-repo)."
    )

    return {
        "installState": state,
        "operationIntent": intent,
        "steps": steps,
    }
