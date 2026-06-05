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

OPTIONAL_REPO_PROFILE_PATHS = [
    "aim.profile.md",
    "aim.profile.json",
    "aim.profile.yaml",
    "aim.profile.yml",
    ".aim/profile.md",
    ".aim/profile.json",
    ".aim/profile.yaml",
    ".aim/profile.yml",
    ".aim/repo-profile.md",
    ".aim/repo-profile.json",
    ".aim/repo-profile.yaml",
    ".aim/repo-profile.yml",
]

TEAM_REPO_PROFILE_PATHS = {
    "aim.profile.md",
    "aim.profile.json",
    "aim.profile.yaml",
    "aim.profile.yml",
}

PERSONAL_REPO_PROFILE_PATHS = {
    ".aim/profile.md",
    ".aim/profile.json",
    ".aim/profile.yaml",
    ".aim/profile.yml",
    ".aim/repo-profile.md",
    ".aim/repo-profile.json",
    ".aim/repo-profile.yaml",
    ".aim/repo-profile.yml",
}

PROFILE_FORBIDDEN_WORKING_STATE_MARKERS = {
    "activeEpic",
    "activeIncrementId",
    "acceptanceState",
    "currentRole",
    "doneIncrementAccepted",
    "epicComplete",
    "epicId",
    "epicStatus",
    "gateStatus",
    "lastGatePassed",
    "poApproval",
    "reviewInProgress",
}

PROFILE_REPO_INTELLIGENCE_MARKERS = {
    "aimRepoProfile",
    "profileVersion",
    "repoIdentity",
    "adoption",
    "footprint",
    "sharing",
    "commands",
    "build",
    "test",
    "lint",
    "validate",
    "conventions",
    "ownership",
    "risk",
    "riskZones",
    "highRiskAreas",
    "locality",
    "packageBoundaries",
    "freshness",
    "refreshTriggers",
    "context",
    "knownContextHogs",
    "cost",
    "scanDepth",
}

PROFILE_SUMMARY_FACTS = {
    "commands": ("commands", "validate", "build", "test", "lint", "typecheck"),
    "locality": ("locality", "primaryAreas", "packageBoundaries", "nearestMetadata"),
    "risk zones": ("risk", "riskZones", "highRiskAreas", "escalation"),
    "short docs": ("shortAuthoritativeDocs", "docsSource", "nearest-workflow-or-feature-doc"),
    "freshness": ("freshness", "refreshTriggers", "revalidate"),
    "avoid-by-default context": ("avoidByDefault", "knownContextHogs"),
    "cost": ("cost", "scanDepth", "startupBudget", "reviewDepth"),
}

AIM_2_MIGRATION_CLASSIFICATION = {
    "runtime": [
        "scripts/validate_aim_runtime.py",
    ],
    "repo_profile": [
        "AGENTS.md",
        "aim.profile.md",
        "aim.profile.json",
        "aim.profile.yaml",
        "aim.profile.yml",
        ".aim/profile.md",
        ".aim/profile.json",
        ".aim/profile.yaml",
        ".aim/profile.yml",
        ".aim/repo-profile.md",
        ".aim/repo-profile.json",
        ".aim/repo-profile.yaml",
        ".aim/repo-profile.yml",
    ],
    "working_state": [
        ".aim/epic.md",
        ".aim/state.json",
        ".aim/increments",
        ".aim/decisions",
        ".aim/reviews",
        ".aim/handoffs",
        ".aim/logs",
        ".aim/archive",
        ".aim/runtime-context.md",
        ".aim/analysis",
    ],
    "docs": [
        "README.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "CONTRIBUTORS.md",
        "LICENSE",
        "docs/LICENSE-DOCS",
        "docs/features",
        "docs/workflow",
    ],
    "adapter_helpers": [
        "CLAUDE.md",
        ".claude",
        ".github/agents",
        ".github/prompts",
        "adapters/codex/agile-iteration-method/SKILL.md",
    ],
}

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


def find_profile_state_markers(content: str) -> list[str]:
    markers = []
    for marker in sorted(PROFILE_FORBIDDEN_WORKING_STATE_MARKERS):
        patterns = (f'"{marker}"', f"'{marker}'", f"{marker}:", f"{marker} =")
        if any(pattern in content for pattern in patterns):
            markers.append(marker)
    return markers


def find_profile_intelligence_markers(content: str) -> list[str]:
    found = []
    normalized_content = content.lower()
    for marker in sorted(PROFILE_REPO_INTELLIGENCE_MARKERS):
        if marker.lower() in normalized_content:
            found.append(marker)
    return found


def find_summary_facts(content: str) -> list[str]:
    found = []
    normalized_content = content.lower()
    for fact, markers in PROFILE_SUMMARY_FACTS.items():
        if any(marker.lower() in normalized_content for marker in markers):
            found.append(fact)
    return found


def extract_profile_list(content: str, section_name: str) -> list[str]:
    lines = content.splitlines()
    section_indent = None
    values = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped != f"{section_name}:":
            continue

        section_indent = len(line) - len(line.lstrip())
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue

            child_indent = len(child_line) - len(child_line.lstrip())
            if child_indent <= section_indent and not child_stripped.startswith("- "):
                break
            if child_stripped.startswith("- "):
                values.append(child_stripped[2:])

        break

    return values


def extract_profile_section_values(content: str, section_name: str) -> list[str]:
    lines = content.splitlines()
    section_indent = None
    values = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped != f"{section_name}:":
            continue

        section_indent = len(line) - len(line.lstrip())
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue

            child_indent = len(child_line) - len(child_line.lstrip())
            if child_indent <= section_indent:
                break
            if child_stripped.startswith("- "):
                values.append(child_stripped[2:])
            elif ":" in child_stripped:
                key, value = child_stripped.split(":", 1)
                value = value.strip()
                values.append(f"{key.strip()}: {value}" if value else key.strip())

        break

    return values


def first_existing_value(values_by_profile: dict[str, list[str]], fallback: str) -> str:
    for values in values_by_profile.values():
        if values:
            return ", ".join(values[:3])
    return fallback


def build_profile_source_summary(repo_root: Path, repo_profile_readiness: dict[str, object]) -> dict[str, str]:
    profile_paths = repo_profile_readiness["profile_paths"]
    readiness_status = str(repo_profile_readiness["status"])
    intelligence_marker_findings = repo_profile_readiness["intelligence_marker_findings"]

    if not profile_paths:
        return {
            "source": "none",
            "layering": "no profile source; use locality-first discovery",
            "reused_facts": "none",
            "selected_locality": "directly affected files or nearest metadata",
            "avoided_context": "none until enough local evidence exists",
            "expansion_reason": "missing profile",
            "cheap_validation_first": "nearest relevant validation command",
        }

    team_profile_paths = repo_profile_readiness["team_profile_paths"]
    personal_profile_paths = repo_profile_readiness["personal_profile_paths"]
    ordered_profile_paths = [
        *personal_profile_paths,
        *team_profile_paths,
        *[path for path in profile_paths if path not in personal_profile_paths and path not in team_profile_paths],
    ]
    if personal_profile_paths and team_profile_paths:
        layering = "personal/local profile narrows startup; team profile remains shared baseline"
    elif personal_profile_paths:
        layering = "personal/local profile only"
    elif team_profile_paths:
        layering = "team profile baseline"
    else:
        layering = "profile source discovered"

    source_parts = []
    if personal_profile_paths:
        source_parts.append(f"personal/local: {', '.join(personal_profile_paths)}")
    if team_profile_paths:
        source_parts.append(f"team: {', '.join(team_profile_paths)}")
    source = "; ".join(source_parts) if source_parts else ", ".join(profile_paths)

    facts = []
    locality_by_profile = {}
    validation_by_profile = {}
    avoid_by_profile = {}
    short_docs_by_profile = {}
    for relative_path in ordered_profile_paths:
        content = (repo_root / relative_path).read_text(encoding="utf-8", errors="replace")
        for fact in find_summary_facts(content):
            if fact not in facts:
                facts.append(fact)
        locality_by_profile[relative_path] = extract_profile_list(content, "primaryAreas")
        validation_by_profile[relative_path] = extract_profile_section_values(content, "commands")
        avoid_by_profile[relative_path] = extract_profile_list(content, "avoidByDefault")
        short_docs_by_profile[relative_path] = extract_profile_list(content, "shortAuthoritativeDocs")

    if not facts and intelligence_marker_findings:
        facts = sorted({marker for markers in intelligence_marker_findings.values() for marker in markers})

    avoided_context_values = []
    for values in avoid_by_profile.values():
        avoided_context_values.extend(values)
    if not avoided_context_values:
        for values in short_docs_by_profile.values():
            if values:
                avoided_context_values.append("broader docs outside profile shortAuthoritativeDocs")
                break

    expansion_reason = "none"
    if readiness_status != "profile_ready":
        expansion_reason = readiness_status

    return {
        "source": f"{source} ({readiness_status})",
        "layering": layering,
        "reused_facts": ", ".join(facts) if facts else "profile presence only",
        "selected_locality": first_existing_value(locality_by_profile, "directly affected files or nearest metadata"),
        "avoided_context": ", ".join(avoided_context_values[:3]) if avoided_context_values else "broad docs and repo-wide scan until risk or missing evidence requires them",
        "expansion_reason": expansion_reason,
        "cheap_validation_first": first_existing_value(validation_by_profile, "nearest relevant validation command"),
    }


def collect_repo_profile_readiness(repo_root: Path) -> dict[str, object]:
    profile_paths = []
    team_profile_paths = []
    personal_profile_paths = []
    state_marker_findings = {}
    intelligence_marker_findings = {}

    for relative_path in OPTIONAL_REPO_PROFILE_PATHS:
        profile_path = repo_root / relative_path
        if not profile_path.is_file():
            continue

        content = profile_path.read_text(encoding="utf-8", errors="replace")
        state_markers = find_profile_state_markers(content)
        intelligence_markers = find_profile_intelligence_markers(content)
        profile_paths.append(relative_path)
        if relative_path in TEAM_REPO_PROFILE_PATHS:
            team_profile_paths.append(relative_path)
        if relative_path in PERSONAL_REPO_PROFILE_PATHS:
            personal_profile_paths.append(relative_path)
        if state_markers:
            state_marker_findings[relative_path] = state_markers
        if intelligence_markers:
            intelligence_marker_findings[relative_path] = intelligence_markers

    if not profile_paths:
        return {
            "status": "not_ready",
            "profile_paths": [],
            "team_profile_paths": [],
            "personal_profile_paths": [],
            "summary": "No AIM 2.0 repo profile artifact found; AGENTS.md can bridge current runtime behavior, but reusable Personal/Team profile reuse is not ready yet.",
            "state_marker_findings": {},
            "intelligence_marker_findings": {},
        }

    if state_marker_findings:
        return {
            "status": "repair_profile",
            "profile_paths": profile_paths,
            "team_profile_paths": team_profile_paths,
            "personal_profile_paths": personal_profile_paths,
            "summary": "Profile artifact exists but appears to contain active AIM working state.",
            "state_marker_findings": state_marker_findings,
            "intelligence_marker_findings": intelligence_marker_findings,
        }

    if not intelligence_marker_findings:
        return {
            "status": "incomplete_profile",
            "profile_paths": profile_paths,
            "team_profile_paths": team_profile_paths,
            "personal_profile_paths": personal_profile_paths,
            "summary": "Profile artifact exists but does not expose recognizable repo intelligence yet.",
            "state_marker_findings": {},
            "intelligence_marker_findings": {},
        }

    return {
        "status": "profile_ready",
        "profile_paths": profile_paths,
        "team_profile_paths": team_profile_paths,
        "personal_profile_paths": personal_profile_paths,
        "summary": "Reusable AIM 2.0 repo profile artifact found with repo-intelligence markers and no active working-state markers.",
        "state_marker_findings": {},
        "intelligence_marker_findings": intelligence_marker_findings,
    }


def collect_migration_classification(repo_root: Path) -> dict[str, list[str]]:
    classification: dict[str, list[str]] = {}
    for category, paths in AIM_2_MIGRATION_CLASSIFICATION.items():
        existing_paths = []
        for relative_path in paths:
            path = repo_root / relative_path
            if path.exists():
                existing_paths.append(relative_path)
        classification[category] = existing_paths
    return classification


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

    checked.append("optional AIM 2.0 repo profile paths")
    for relative_path in OPTIONAL_REPO_PROFILE_PATHS:
        profile_path = repo_root / relative_path
        if not profile_path.is_file():
            continue

        checked.append(relative_path)

    checked.append("AIM 2.0 migration classification")
    migration_classification = collect_migration_classification(repo_root)

    checked.append("AIM 2.0 repo profile readiness")
    repo_profile_readiness = collect_repo_profile_readiness(repo_root)
    profile_source_summary = build_profile_source_summary(repo_root, repo_profile_readiness)
    readiness_status = repo_profile_readiness["status"]
    if readiness_status == "repair_profile":
        for relative_path, markers in repo_profile_readiness["state_marker_findings"].items():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                f"repo profile readiness is blocked by active working-state markers: {', '.join(markers)}",
                "Move active Epic, gate, role, increment, review, or acceptance state back to .aim working-state artifacts before reusing this profile.",
            )
    elif readiness_status == "incomplete_profile":
        for relative_path in repo_profile_readiness["profile_paths"]:
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "repo profile artifact exists but does not contain recognizable repo-intelligence sections",
                "Add reusable repo identity, commands, locality, ownership, risk, freshness, or cost fields before relying on profile reuse.",
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

    print("AIM 2.0 migration classification:")
    for category in ["runtime", "repo_profile", "working_state", "docs", "adapter_helpers"]:
        paths = migration_classification.get(category, [])
        if paths:
            print(f"- {category}: {', '.join(paths)}")
        else:
            print(f"- {category}: none")

    print("AIM 2.0 repo profile readiness:")
    print(f"- status: {readiness_status}")
    print(f"- summary: {repo_profile_readiness['summary']}")
    profile_paths = repo_profile_readiness["profile_paths"]
    if profile_paths:
        print(f"- profiles: {', '.join(profile_paths)}")
    else:
        print("- profiles: none")
    team_profile_paths = repo_profile_readiness["team_profile_paths"]
    personal_profile_paths = repo_profile_readiness["personal_profile_paths"]
    if team_profile_paths:
        print(f"- team profiles: {', '.join(team_profile_paths)}")
    else:
        print("- team profiles: none")
    if personal_profile_paths:
        print(f"- personal/local profiles: {', '.join(personal_profile_paths)}")
    else:
        print("- personal/local profiles: none")
    intelligence_marker_findings = repo_profile_readiness["intelligence_marker_findings"]
    if intelligence_marker_findings:
        for relative_path, markers in intelligence_marker_findings.items():
            print(f"- repo intelligence in {relative_path}: {', '.join(markers)}")

    print("AIM 2.0 profile-source summary:")
    print(f"- Profile source: {profile_source_summary['source']}")
    print(f"- Layering: {profile_source_summary['layering']}")
    print(f"- Reused facts: {profile_source_summary['reused_facts']}")
    print(f"- Selected locality: {profile_source_summary['selected_locality']}")
    print(f"- Avoided context: {profile_source_summary['avoided_context']}")
    print(f"- Expansion reason: {profile_source_summary['expansion_reason']}")
    print(f"- Cheap validation first: {profile_source_summary['cheap_validation_first']}")

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
