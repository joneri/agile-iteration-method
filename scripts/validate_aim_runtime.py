#!/usr/bin/env python3
"""Validate the AIM runtime workspace without mutating it."""

from __future__ import annotations

import json
import sys
from pathlib import Path


RESULT_ORDER = {
    "healthy": 0,
    "recoverable": 1,
    "blocked": 2,
    "contradictory": 3,
}

EXIT_CODES = {
    "healthy": 0,
    "recoverable": 1,
    "blocked": 2,
    "contradictory": 3,
}

ALLOWED_STATES = {
    "epic_initialized",
    "gate_a_pending",
    "gate_b_pending",
    "increment_in_progress",
    "review_in_progress",
    "tdo_validation_in_progress",
    "po_approval_pending",
    "done_increment_accepted",
    "epic_paused",
    "blocked",
    "epic_complete",
}

ALLOWED_ROLES = {"PO", "TDO", "Dev", "Reviewer"}
ALLOWED_MODES = {"Strict", "Auto"}
ALLOWED_COST_PROFILES = {"Standard", "Cost Control", "Deep"}
ALLOWED_LAST_GATES = {None, "Gate A", "Gate B", "Gate C", "Gate D", "Gate E"}

EXPECTED_ROLE_BY_STATE = {
    "epic_initialized": "PO",
    "gate_a_pending": "PO",
    "gate_b_pending": "TDO",
    "increment_in_progress": "Dev",
    "review_in_progress": "Reviewer",
    "tdo_validation_in_progress": "TDO",
    "po_approval_pending": "PO",
}


def add_issue(issues: list[dict[str, str]], result: str, artifact: str, rule: str, action: str) -> None:
    issues.append(
        {
            "result": result,
            "artifact": artifact,
            "rule": rule,
            "action": action,
        }
    )


def parse_increment_id(active_increment_id: object) -> tuple[str | None, str | None]:
    if active_increment_id is None:
        return None, None
    if not isinstance(active_increment_id, str):
        return None, "activeIncrementId must be a string like DI-001 or null"
    if not active_increment_id.startswith("DI-"):
        return None, "activeIncrementId must start with DI-"
    suffix = active_increment_id[3:]
    if len(suffix) != 3 or not suffix.isdigit():
        return None, "activeIncrementId must use a three-digit suffix like DI-001"
    return suffix, None


def summarize_result(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "healthy"
    return max(issues, key=lambda issue: RESULT_ORDER[issue["result"]])["result"]


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    checked: list[str] = []
    issues: list[dict[str, str]] = []

    required_repo_files = [
        repo_root / "AGENTS.md",
        repo_root / "docs/workflow/agile-iteration-method.md",
        repo_root / ".github/agents/aim.agent.md",
        repo_root / ".github/agents/aim-planner.agent.md",
        repo_root / ".github/agents/aim-builder.agent.md",
        repo_root / ".github/agents/aim-reviewer.agent.md",
    ]

    required_runtime_paths = [
        repo_root / ".aim",
        repo_root / ".aim/epic.md",
        repo_root / ".aim/state.json",
        repo_root / ".aim/increments",
        repo_root / ".aim/decisions",
        repo_root / ".aim/reviews",
    ]

    for path in required_repo_files:
        checked.append(str(path.relative_to(repo_root)))
        if not path.is_file():
            add_issue(
                issues,
                "blocked",
                str(path.relative_to(repo_root)),
                "required repo-aware AIM file is missing",
                "Restore the canonical AIM repository file before continuing.",
            )

    for path in required_runtime_paths:
        checked.append(str(path.relative_to(repo_root)))
        if path.name == ".aim" or path.is_dir():
            if not path.exists():
                add_issue(
                    issues,
                    "recoverable",
                    str(path.relative_to(repo_root)),
                    "required AIM runtime path is missing",
                    "Recreate the missing runtime path from the official .aim contract.",
                )
        elif not path.is_file():
            add_issue(
                issues,
                "recoverable",
                str(path.relative_to(repo_root)),
                "required AIM runtime artifact is missing",
                "Recreate the missing runtime artifact before relying on resume behavior.",
            )

    state_path = repo_root / ".aim/state.json"
    state = None
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            checked.append(".aim/state.json syntax")
        except json.JSONDecodeError as exc:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"invalid JSON syntax: {exc.msg}",
                "Repair the JSON before the runtime attempts to resume.",
            )

    if isinstance(state, dict):
        aim_version = state.get("aimVersion")
        if not isinstance(aim_version, str):
            add_issue(
                issues,
                "recoverable",
                ".aim/state.json",
                "aimVersion is missing or not a string",
                "Add the active AIM release line to state.json.",
            )

        mode = state.get("mode")
        if mode not in ALLOWED_MODES:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"mode must be one of {sorted(ALLOWED_MODES)}",
                "Set mode to Strict or Auto.",
            )

        cost_profile = state.get("costProfile")
        if cost_profile not in ALLOWED_COST_PROFILES:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"costProfile must be one of {sorted(ALLOWED_COST_PROFILES)}",
                "Set costProfile to Standard, Cost Control, or Deep.",
            )

        epic_status = state.get("epicStatus")
        if epic_status not in ALLOWED_STATES:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"epicStatus must be one of {sorted(ALLOWED_STATES)}",
                "Repair epicStatus to a canonical AIM runtime state.",
            )

        current_role = state.get("currentRole")
        if current_role not in ALLOWED_ROLES:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"currentRole must be one of {sorted(ALLOWED_ROLES)}",
                "Repair currentRole to a canonical AIM role.",
            )

        expected_role = EXPECTED_ROLE_BY_STATE.get(epic_status)
        if expected_role and current_role != expected_role:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"{epic_status} should be owned by {expected_role}, not {current_role}",
                "Align currentRole with the canonical owner for the current state.",
            )

        last_gate = state.get("lastGatePassed")
        if last_gate not in ALLOWED_LAST_GATES:
            add_issue(
                issues,
                "recoverable",
                ".aim/state.json",
                "lastGatePassed is not a canonical AIM gate label",
                "Set lastGatePassed to Gate A-E or null.",
            )

        epic_id = state.get("epicId")
        if not isinstance(epic_id, str) or not epic_id:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                "epicId is missing or invalid",
                "Set epicId to the active Epic identifier.",
            )

        increment_suffix, increment_error = parse_increment_id(state.get("activeIncrementId"))
        if increment_error:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                increment_error,
                "Repair activeIncrementId or set it to null when no increment is active.",
            )

        if epic_status in {"gate_b_pending", "increment_in_progress", "review_in_progress", "tdo_validation_in_progress", "po_approval_pending", "done_increment_accepted"} and increment_suffix is None:
            add_issue(
                issues,
                "contradictory",
                ".aim/state.json",
                f"{epic_status} requires an activeIncrementId",
                "Restore the active increment identifier for the current checkpoint.",
            )

        if epic_status in {"epic_initialized", "gate_a_pending"} and state.get("activeIncrementId") is not None:
            add_issue(
                issues,
                "recoverable",
                ".aim/state.json",
                f"{epic_status} should normally not have an activeIncrementId",
                "Clear activeIncrementId unless this repo has a documented reason to keep it.",
            )

        if increment_suffix:
            increment_file = repo_root / f".aim/increments/{increment_suffix}-wip.md"
            review_file = repo_root / f".aim/reviews/review-{increment_suffix}.md"
            decision_file = repo_root / f".aim/decisions/{increment_suffix}-gate-e.md"

            checked.extend(
                [
                    str(increment_file.relative_to(repo_root)),
                    str(review_file.relative_to(repo_root)),
                    str(decision_file.relative_to(repo_root)),
                ]
            )

            if epic_status in {"review_in_progress", "tdo_validation_in_progress", "po_approval_pending", "done_increment_accepted", "epic_complete"} and not increment_file.is_file():
                add_issue(
                    issues,
                    "recoverable",
                    str(increment_file.relative_to(repo_root)),
                    f"{epic_status} should have an increment artifact",
                    "Restore the increment artifact or lower the runtime state to a consistent earlier step.",
                )

            if epic_status in {"tdo_validation_in_progress", "po_approval_pending", "done_increment_accepted", "epic_complete"} and not review_file.is_file():
                add_issue(
                    issues,
                    "recoverable",
                    str(review_file.relative_to(repo_root)),
                    f"{epic_status} should have a reviewer artifact",
                    "Restore the review artifact or lower the runtime state to a consistent earlier step.",
                )

            if epic_status in {"done_increment_accepted", "epic_complete"} and not decision_file.is_file():
                add_issue(
                    issues,
                    "recoverable",
                    str(decision_file.relative_to(repo_root)),
                    f"{epic_status} should have a Gate E decision artifact",
                    "Restore the Gate E decision artifact or lower the runtime state to a consistent earlier step.",
                )

        epic_doc = repo_root / ".aim/epic.md"
        if epic_doc.is_file():
            checked.append(".aim/epic.md content")
            content = epic_doc.read_text(encoding="utf-8").strip()
            if not content:
                add_issue(
                    issues,
                    "recoverable",
                    ".aim/epic.md",
                    "epic intent artifact is empty",
                    "Restore the active Epic goal, motivation, non-goals, and acceptance criteria.",
                )
            elif isinstance(epic_id, str) and epic_id not in content:
                add_issue(
                    issues,
                    "recoverable",
                    ".aim/epic.md",
                    "epicId in state.json does not appear in epic.md",
                    "Align epic.md with the active epicId or repair state.json.",
                )

        updated_at = state.get("updatedAt")
        if not isinstance(updated_at, str) or not updated_at:
            add_issue(
                issues,
                "recoverable",
                ".aim/state.json",
                "updatedAt is missing or invalid",
                "Record the last runtime update timestamp in ISO-8601 form.",
            )

    result = summarize_result(issues)
    next_action = {
        "healthy": "Continue or resume the AIM loop normally.",
        "recoverable": "Repair the listed runtime gaps, then re-run the validator before resuming.",
        "blocked": "Restore the required repo/runtime files before continuing the AIM loop.",
        "contradictory": "Stop and reconcile the contradictory runtime state before continuing.",
    }[result]

    print(f"Result: {result}")
    print("Checked:")
    for item in checked:
        print(f"- {item}")

    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- [{issue['result']}] {issue['artifact']}: {issue['rule']}")
            print(f"  Next action: {issue['action']}")
    else:
        print("Issues:")
        print("- none")

    print(f"Best next action: {next_action}")
    return EXIT_CODES[result]


if __name__ == "__main__":
    raise SystemExit(main())
