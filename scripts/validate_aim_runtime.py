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
]

TEAM_REPO_PROFILE_PATHS = {
    "aim.profile.md",
    "aim.profile.json",
    "aim.profile.yaml",
    "aim.profile.yml",
}

PERSONAL_REPO_PROFILE_PATHS: set[str] = set()

FORBIDDEN_RUNTIME_PROFILE_PATHS = [
    ".aim/profile.md",
    ".aim/profile.json",
    ".aim/profile.yaml",
    ".aim/profile.yml",
    ".aim/repo-profile.md",
    ".aim/repo-profile.json",
    ".aim/repo-profile.yaml",
    ".aim/repo-profile.yml",
]

PERSONAL_HINTS_PATH = "~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml"

CALIBRATION_STATUSES = {"ready", "partially_ready", "needs_calibration"}
CALIBRATION_CONFIDENCE_VALUES = {"high", "medium", "low"}
REPO_KNOWLEDGE_CATEGORIES = {
    "technologies",
    "commands",
    "validation",
    "uiTesting",
    "docs",
    "localities",
    "riskZones",
    "habits",
    "avoidByDefault",
    "freshness",
}
DOCUMENT_LOADING_STATES = {
    "authoritative",
    "load_when_relevant",
    "avoid_by_default",
    "stale_or_uncertain",
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
        "aim.profile.md",
        "aim.profile.json",
        "aim.profile.yaml",
        "aim.profile.yml",
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
        "CHANGELOG.md",
        "CONTRIBUTORS.md",
        "LICENSE",
        "docs/LICENSE-DOCS",
        "docs/features",
        "docs/workflow",
    ],
    "adapter_helpers": [
        ".claude",
        ".github/agents",
        ".github/prompts",
        "adapters/codex/agile-iteration-method/SKILL.md",
    ],
    "source_repo_maintainer_only": [
        "CONTRIBUTING.md",
    ],
}

SURFACE_BOUNDARY_CLASSIFICATION = {
    "static_product": [
        "README.md",
        "docs/workflow",
        "adapters",
        "scripts/validate_aim_runtime.py",
        "examples",
    ],
    "repo_aware_collision_prone": [
        "aim.profile.yaml",
        ".github/agents",
        ".github/prompts",
        ".claude",
        ".gitignore",
    ],
    "source_repo_maintainer_only": [
        "CONTRIBUTING.md",
    ],
    "generic_root_files_outside_aim": [
        "AGENTS.md",
        "CLAUDE.md",
    ],
    "runtime_working_state": [
        ".aim",
        ".aim/epic.md",
        ".aim/state.json",
        ".aim/increments",
        ".aim/decisions",
        ".aim/reviews",
    ],
    "support_reference_docs": [
        "docs/features",
    ],
    "local_generated_never_ship": [
        ".DS_Store",
    ],
}

REQUIRED_SURFACE_MODEL_MARKERS = [
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "README.md",
    "aim.profile.yaml",
    ".aim/",
    ".github/",
    ".claude/",
    "docs/workflow/",
    "docs/features/",
    "adapters/",
    "scripts/",
    "examples/",
    "May create",
    "May modify",
    "May overwrite",
    "Must never touch",
]

OPERATING_MODE_DOC_PATH = "docs/workflow/operating-modes.md"
DOCUMENTATION_MODEL_DOC_PATH = "docs/workflow/documentation-model.md"
SURFACE_MODEL_DOC_PATH = "docs/workflow/repository-surface-classification.md"
REPO_AWARENESS_DOC_PATH = "docs/workflow/repo-awareness.md"
REPO_CALIBRATION_DOC_PATH = "docs/workflow/repo-awareness-calibration.md"
INSTALL_GUIDE_DOC_PATH = "docs/workflow/install-aim-2.0.md"
INSTALL_MANIFEST_PATH = "install/aim-install-manifest.yaml"

REMOVED_GENERIC_AIM_ROOT_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
]

REQUIRED_REPO_AWARENESS_MARKERS = [
    "aim.profile.yaml",
    "primary shared repo-awareness source",
    "Generic root files",
    "outside the AIM architecture",
    "optional and secondary",
    "Codex",
    "Copilot",
    "Claude",
]

REQUIRED_CALIBRATION_DOC_MARKERS = [
    "/aim calibrate-repo",
    "/aim remember-repo",
    "/aim forget-repo",
    "aim.profile.yaml",
    PERSONAL_HINTS_PATH,
    "`.aim/` is runtime state only",
    "`ready`",
    "`partially_ready`",
    "`needs_calibration`",
    "`authoritative`",
    "`load_when_relevant`",
    "`avoid_by_default`",
    "`stale_or_uncertain`",
]

CONTRIBUTING_EXCLUSION_MARKERS = {
    REPO_AWARENESS_DOC_PATH: [
        "AIM source repository",
        "must never copy, create, modify, require, or read `CONTRIBUTING.md`",
    ],
    INSTALL_GUIDE_DOC_PATH: [
        "source-repository-only maintainer file",
        "must never copy, create, modify, require, or read it",
        "installer manifest",
        "explicitly exclude `CONTRIBUTING.md`",
    ],
    DOCUMENTATION_MODEL_DOC_PATH: [
        "source-repository-only",
        "must never copy, create, modify, require, or read it in a target repository",
        "exclude from every installer manifest",
    ],
    SURFACE_MODEL_DOC_PATH: [
        "source-repository-only",
        "never copy, create, modify, require, or read a target repo's `CONTRIBUTING.md`",
        "exclude `CONTRIBUTING.md` from every installer manifest",
    ],
}

REQUIRED_INSTALL_MANIFEST_MARKERS = [
    "targetExclusions:",
    "path: CONTRIBUTING.md",
    "AIM-source-repository-maintainer-only",
    "copy: forbidden",
    "create: forbidden",
    "modify: forbidden",
    "require: forbidden",
    "read: forbidden",
    "repoAwarenessBootstrap:",
    "personalHints: ~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml",
    "readyRequiresCalibration: true",
    "calibrationCommand: /aim calibrate-repo",
    "runtimeProfileStorage: forbidden",
]

CALIBRATION_ADAPTER_MARKERS = {
    "adapters/codex/agile-iteration-method/SKILL.md": [
        "/aim calibrate-repo",
        "/aim remember-repo",
        "/aim forget-repo",
        PERSONAL_HINTS_PATH,
    ],
    ".github/agents/aim.agent.md": [
        "/aim calibrate-repo",
        "/aim remember-repo",
        "/aim forget-repo",
        PERSONAL_HINTS_PATH,
    ],
    ".claude/commands/calibrate-repo.md": [
        "/aim calibrate-repo",
        PERSONAL_HINTS_PATH,
        "never store stable repo-awareness under `.aim/`",
    ],
    ".claude/commands/remember-repo.md": [
        "/aim remember-repo",
        PERSONAL_HINTS_PATH,
        "Never store stable repository knowledge under `.aim/`",
    ],
    ".claude/commands/forget-repo.md": [
        "/aim forget-repo",
        "Never mutate `.aim/`",
    ],
}

REQUIRED_OPERATING_MODE_MARKERS = [
    "Personal AIM",
    "Team AIM",
    "Enterprise AIM",
    "permissive",
    "shared AIM understanding",
    "safe and isolated by default",
    "AGENTS.md",
    "CLAUDE.md",
    "Enterprise ignore baseline",
]

ENTERPRISE_IGNORE_MARKERS = [
    "/.aim",
    "/.aim-local",
    "/aim.local.*",
    "/*.aim.local.md",
    "/*.aim.process.md",
]

OPERATING_MODE_VALUES = {
    "personal": "Personal",
    "team": "Team",
    "enterprise": "Enterprise",
}

REQUIRED_DOCUMENTATION_MODEL_MARKERS = [
    "AIM core truth",
    "docs/workflow/agile-iteration-method.md",
    "docs/workflow/operating-modes.md",
    "docs/workflow/repository-surface-classification.md",
    "docs/workflow/cost-control-mode.md",
    "docs/workflow/cost-review-checklist.md",
    "docs/workflow/cost-saving-method.md",
    "docs/workflow/modularity-context-efficiency.md",
    "docs/workflow/repo-awareness-calibration.md",
    "docs/features/",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    ".aim/",
    "outside AIM architecture",
    "Runtime state",
    "Shipped AIM product docs",
    "Behavior-defining AIM documents belong here",
]

PROMOTED_CANONICAL_DOC_PATHS = {
    "docs/workflow/documentation-model.md": "docs/features/aim-2-documentation-model.md",
    "docs/workflow/operating-modes.md": "docs/features/aim-2-operating-modes.md",
    "docs/workflow/repository-surface-classification.md": "docs/features/aim-2-repository-surface-classification.md",
    "docs/workflow/repo-profile-and-footprint-model.md": "docs/features/aim-2-repo-profile-and-footprint-model.md",
    "docs/workflow/working-state-boundaries.md": "docs/features/aim-2-working-state-boundaries.md",
    "docs/workflow/cost-control-mode.md": "docs/features/aim-cost-control-mode.md",
    "docs/workflow/modularity-context-efficiency.md": "docs/features/aim-modularity-context-efficiency.md",
    "docs/workflow/personal-local-profile-storage.md": "docs/features/aim-2-personal-local-profile-storage.md",
    "docs/workflow/profile-source-summary.md": "docs/features/aim-2-profile-source-summary.md",
    "docs/workflow/team-profile-artifact.md": "docs/features/aim-2-tiny-team-profile-example.md",
    "docs/workflow/codex-skill-onboarding.md": "docs/features/aim-codex-bundled-skill-onboarding.md",
    "docs/workflow/light-front-door.md": "docs/features/aim-light-front-door.md",
    "docs/workflow/cost-review-checklist.md": "docs/features/aim-cost-review-checklist.md",
    "docs/workflow/cost-saving-method.md": "docs/features/aim-cost-saving-method.md",
}

FEATURE_SUPPORT_ROLE_MARKERS = {
    "docs/features/aim-cost-comparison.md": "non-canonical reference comparison",
    "docs/features/aim-github-copilot-cost-reduction-playbook.md": "vendor-specific onboarding playbook",
    "docs/features/aim-vendor-cost-baseline-june-2026.md": "date-stamped external-vendor reference",
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


def extract_profile_scalar(content: str, section_name: str, key_name: str) -> str | None:
    lines = content.splitlines()
    section_indent = None

    for index, line in enumerate(lines):
        if line.strip() != f"{section_name}:":
            continue

        section_indent = len(line) - len(line.lstrip())
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue
            child_indent = len(child_line) - len(child_line.lstrip())
            if child_indent <= section_indent:
                break
            if child_stripped.startswith(f"{key_name}:"):
                return child_stripped.split(":", 1)[1].strip().strip("\"'")
        break

    return None


def extract_direct_child_keys(content: str, section_name: str) -> set[str]:
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() != f"{section_name}:":
            continue

        section_indent = len(line) - len(line.lstrip())
        child_indent = None
        keys = set()
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue
            current_indent = len(child_line) - len(child_line.lstrip())
            if current_indent <= section_indent:
                break
            if child_indent is None:
                child_indent = current_indent
            if current_indent == child_indent and ":" in child_stripped:
                keys.add(child_stripped.split(":", 1)[0])
        return keys

    return set()


def extract_loading_states(content: str) -> set[str]:
    states = set()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("loading:"):
            states.add(stripped.split(":", 1)[1].strip().strip("\"'"))
    return states


def extract_section_block(content: str, section_name: str) -> str | None:
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != f"{section_name}:":
            continue
        section_indent = len(line) - len(line.lstrip())
        block = [line]
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if child_stripped:
                child_indent = len(child_line) - len(child_line.lstrip())
                if child_indent <= section_indent:
                    break
            block.append(child_line)
        return "\n".join(block)
    return None


def extract_repo_knowledge_values(
    content: str, category_name: str, value_keys: tuple[str, ...]
) -> list[str]:
    scoped_content = extract_section_block(content, "repoKnowledge") or content
    lines = scoped_content.splitlines()
    matched_values = []

    for index, line in enumerate(lines):
        if line.strip() != f"{category_name}:":
            continue

        category_indent = len(line) - len(line.lstrip())
        values = []
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue
            child_indent = len(child_line) - len(child_line.lstrip())
            if child_indent <= category_indent:
                break
            normalized_child = (
                child_stripped[2:]
                if child_stripped.startswith("- ")
                else child_stripped
            )
            for key_name in value_keys:
                if normalized_child.startswith(f"{key_name}:"):
                    value = normalized_child.split(":", 1)[1].strip().strip("\"'")
                    if value and value not in values:
                        values.append(value)
                    break
        matched_values = values

    return matched_values


def extract_category_entries(content: str, category_name: str) -> list[dict[str, str]]:
    scoped_content = extract_section_block(content, "repoKnowledge") or content
    lines = scoped_content.splitlines()
    matched_entries = []

    for index, line in enumerate(lines):
        if line.strip() != f"{category_name}:":
            continue

        category_indent = len(line) - len(line.lstrip())
        entries = []
        current_entry = None
        for child_line in lines[index + 1 :]:
            child_stripped = child_line.strip()
            if not child_stripped:
                continue
            child_indent = len(child_line) - len(child_line.lstrip())
            if child_indent <= category_indent:
                break
            if child_stripped.startswith("- "):
                current_entry = {}
                entries.append(current_entry)
                first_field = child_stripped[2:]
                if ":" in first_field:
                    key, value = first_field.split(":", 1)
                    current_entry[key.strip()] = value.strip().strip("\"'")
                continue
            if current_entry is not None and ":" in child_stripped:
                key, value = child_stripped.split(":", 1)
                current_entry[key.strip()] = value.strip().strip("\"'")
        matched_entries = entries

    return matched_entries


def extract_all_scalar_values(content: str, key_name: str) -> list[str]:
    values = []
    for line in content.splitlines():
        stripped = line.strip()
        normalized = stripped[2:] if stripped.startswith("- ") else stripped
        if normalized.startswith(f"{key_name}:"):
            values.append(normalized.split(":", 1)[1].strip().strip("\"'"))
    return values


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
    if readiness_status != "ready":
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
    calibration_status = None
    calibration_confidence = None

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
        if relative_path in TEAM_REPO_PROFILE_PATHS:
            calibration_status = extract_profile_scalar(content, "calibration", "status")
            calibration_confidence = extract_profile_scalar(content, "calibration", "confidence")

    if not profile_paths:
        return {
            "status": "needs_calibration",
            "profile_paths": [],
            "team_profile_paths": [],
            "personal_profile_paths": [],
            "summary": "No AIM 2.0 repo profile artifact found; use current repository evidence until a Personal or Team profile is available.",
            "state_marker_findings": {},
            "intelligence_marker_findings": {},
            "calibration_confidence": None,
        }

    if state_marker_findings:
        return {
            "status": "needs_calibration",
            "profile_paths": profile_paths,
            "team_profile_paths": team_profile_paths,
            "personal_profile_paths": personal_profile_paths,
            "summary": "Profile artifact exists but appears to contain active AIM working state.",
            "state_marker_findings": state_marker_findings,
            "intelligence_marker_findings": intelligence_marker_findings,
            "calibration_confidence": calibration_confidence,
        }

    if not intelligence_marker_findings:
        return {
            "status": "needs_calibration",
            "profile_paths": profile_paths,
            "team_profile_paths": team_profile_paths,
            "personal_profile_paths": personal_profile_paths,
            "summary": "Profile artifact exists but does not expose recognizable repo intelligence yet.",
            "state_marker_findings": {},
            "intelligence_marker_findings": {},
            "calibration_confidence": calibration_confidence,
        }

    effective_status = (
        calibration_status if calibration_status in CALIBRATION_STATUSES else "partially_ready"
    )
    return {
        "status": effective_status,
        "profile_paths": profile_paths,
        "team_profile_paths": team_profile_paths,
        "personal_profile_paths": personal_profile_paths,
        "summary": f"Reusable AIM 2.0 repo-awareness profile found with calibration status {effective_status}.",
        "state_marker_findings": {},
        "intelligence_marker_findings": intelligence_marker_findings,
        "calibration_confidence": calibration_confidence,
    }


def detect_operating_mode(repo_root: Path, profile_paths: list[str]) -> tuple[str | None, str]:
    for relative_path in profile_paths:
        content = (repo_root / relative_path).read_text(encoding="utf-8", errors="replace")
        normalized_content = content.lower()
        for raw_mode, display_mode in OPERATING_MODE_VALUES.items():
            mode_patterns = (
                f"mode: {raw_mode}",
                f"mode: \"{raw_mode}\"",
                f"mode: '{raw_mode}'",
            )
            if any(pattern in normalized_content for pattern in mode_patterns):
                return display_mode, relative_path
    return None, "none"


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


def collect_surface_boundary_classification(repo_root: Path) -> dict[str, list[str]]:
    classification: dict[str, list[str]] = {}
    for category, paths in SURFACE_BOUNDARY_CLASSIFICATION.items():
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
        repo_root / "docs/workflow/agile-iteration-method.md",
        repo_root / REPO_AWARENESS_DOC_PATH,
        repo_root / REPO_CALIBRATION_DOC_PATH,
        repo_root / DOCUMENTATION_MODEL_DOC_PATH,
        repo_root / SURFACE_MODEL_DOC_PATH,
        repo_root / INSTALL_MANIFEST_PATH,
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
                "required canonical AIM product file is missing",
                "Restore the canonical AIM-owned workflow file before continuing.",
            )

    checked.append("AIM 2.0 generic root-file independence")
    for relative_path in REMOVED_GENERIC_AIM_ROOT_PATHS:
        generic_root_path = repo_root / relative_path
        checked.append(relative_path)
        if generic_root_path.exists():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "generic root file remains in the AIM product surface",
                "Remove the AIM-owned root file; keep AIM behavior in canonical workflow docs and adapter mechanics in AIM-owned adapter paths.",
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

    checked.append("AIM 2.0 runtime/profile storage separation")
    for relative_path in FORBIDDEN_RUNTIME_PROFILE_PATHS:
        forbidden_profile_path = repo_root / relative_path
        checked.append(relative_path)
        if forbidden_profile_path.exists():
            add_issue(
                issues,
                "blocked",
                relative_path,
                "stable repo-awareness is stored under .aim runtime state",
                f"Move personal hints to {PERSONAL_HINTS_PATH} and keep .aim runtime-only.",
            )

    checked.append("AIM 2.0 migration classification")
    migration_classification = collect_migration_classification(repo_root)

    checked.append("AIM 2.0 surface boundary classification")
    surface_boundary_classification = collect_surface_boundary_classification(repo_root)

    surface_model_path = repo_root / SURFACE_MODEL_DOC_PATH
    checked.append(str(surface_model_path.relative_to(repo_root)))
    if surface_model_path.is_file():
        surface_model_content = surface_model_path.read_text(encoding="utf-8", errors="replace")
        missing_surface_markers = [
            marker for marker in REQUIRED_SURFACE_MODEL_MARKERS if marker not in surface_model_content
        ]
        if missing_surface_markers:
            add_issue(
                issues,
                "recoverable",
                str(surface_model_path.relative_to(repo_root)),
                f"surface classification model is missing required markers: {', '.join(missing_surface_markers)}",
                "Update the surface matrix so installer-facing boundary rules cover all required AIM 2.0 surfaces.",
            )
    else:
        add_issue(
            issues,
            "recoverable",
            str(surface_model_path.relative_to(repo_root)),
            "surface classification model is missing",
            "Restore docs/workflow/repository-surface-classification.md before relying on installer boundary guidance.",
        )

    repo_awareness_doc_path = repo_root / REPO_AWARENESS_DOC_PATH
    checked.append(REPO_AWARENESS_DOC_PATH)
    if repo_awareness_doc_path.is_file():
        repo_awareness_content = repo_awareness_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_repo_awareness_markers = [
            marker
            for marker in REQUIRED_REPO_AWARENESS_MARKERS
            if marker not in repo_awareness_content
        ]
        if missing_repo_awareness_markers:
            add_issue(
                issues,
                "recoverable",
                REPO_AWARENESS_DOC_PATH,
                f"repo-awareness model is missing required markers: {', '.join(missing_repo_awareness_markers)}",
                "Restore the primary shared profile, root-file independence, optional adapter policy, and native adapter continuity rules.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            REPO_AWARENESS_DOC_PATH,
            "canonical repo-awareness model is missing",
            "Restore docs/workflow/repo-awareness.md before relying on AIM repo-aware behavior.",
        )

    calibration_doc_path = repo_root / REPO_CALIBRATION_DOC_PATH
    checked.append(REPO_CALIBRATION_DOC_PATH)
    if calibration_doc_path.is_file():
        calibration_doc_content = calibration_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_calibration_markers = [
            marker
            for marker in REQUIRED_CALIBRATION_DOC_MARKERS
            if marker not in calibration_doc_content
        ]
        if missing_calibration_markers:
            add_issue(
                issues,
                "recoverable",
                REPO_CALIBRATION_DOC_PATH,
                f"calibration contract is missing required markers: {', '.join(missing_calibration_markers)}",
                "Restore calibration commands, storage boundaries, readiness states, and document-loading vocabulary.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            REPO_CALIBRATION_DOC_PATH,
            "canonical repo-awareness calibration contract is missing",
            "Restore the calibration contract before using persistent repo memory.",
        )

    checked.append("AIM 2.0 promoted canonical documentation paths")
    for canonical_path, old_feature_path in PROMOTED_CANONICAL_DOC_PATHS.items():
        checked.append(canonical_path)
        if not (repo_root / canonical_path).is_file():
            add_issue(
                issues,
                "recoverable",
                canonical_path,
                "promoted canonical AIM behavior doc is missing from docs/workflow",
                "Restore the behavior-defining AIM doc under docs/workflow rather than docs/features.",
            )
        if (repo_root / old_feature_path).exists():
            checked.append(old_feature_path)
            add_issue(
                issues,
                "recoverable",
                old_feature_path,
                "promoted behavior-defining AIM doc still exists under docs/features",
                "Move behavior-defining AIM docs into docs/workflow so docs/features remains support/reference by default.",
            )

    checked.append("AIM 2.0 CONTRIBUTING.md target-install exclusion")
    for relative_path, required_markers in CONTRIBUTING_EXCLUSION_MARKERS.items():
        exclusion_doc_path = repo_root / relative_path
        checked.append(relative_path)
        if not exclusion_doc_path.is_file():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "CONTRIBUTING.md exclusion contract cannot be verified because the canonical document is missing",
                "Restore the canonical document and its source-repository-only CONTRIBUTING.md rule.",
            )
            continue
        exclusion_content = exclusion_doc_path.read_text(encoding="utf-8", errors="replace")
        missing_exclusion_markers = [
            marker for marker in required_markers if marker not in exclusion_content
        ]
        if missing_exclusion_markers:
            add_issue(
                issues,
                "recoverable",
                relative_path,
                f"CONTRIBUTING.md target-install exclusion is incomplete: {', '.join(missing_exclusion_markers)}",
                "State that CONTRIBUTING.md is source-repository-only and must never be copied, created, modified, required, or read in target repositories or installer manifests.",
            )

    install_manifest_path = repo_root / INSTALL_MANIFEST_PATH
    checked.append(INSTALL_MANIFEST_PATH)
    if install_manifest_path.is_file():
        install_manifest_content = install_manifest_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_manifest_markers = [
            marker
            for marker in REQUIRED_INSTALL_MANIFEST_MARKERS
            if marker not in install_manifest_content
        ]
        if missing_manifest_markers:
            add_issue(
                issues,
                "blocked",
                INSTALL_MANIFEST_PATH,
                f"installer manifest does not fully exclude CONTRIBUTING.md: {', '.join(missing_manifest_markers)}",
                "Restore the forbidden copy/create/modify/require/read operations for the source-repository-only file.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            INSTALL_MANIFEST_PATH,
            "canonical installer boundary manifest is missing",
            "Restore the manifest before installer work relies on package boundaries.",
        )

    checked.append("AIM 2.0 calibration adapter entrypoints")
    for relative_path, required_markers in CALIBRATION_ADAPTER_MARKERS.items():
        adapter_path = repo_root / relative_path
        checked.append(relative_path)
        if not adapter_path.is_file():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "calibration adapter entrypoint is missing",
                "Restore the adapter entrypoint or remove the unsupported adapter claim.",
            )
            continue
        adapter_content = adapter_path.read_text(encoding="utf-8", errors="replace")
        missing_adapter_markers = [
            marker for marker in required_markers if marker not in adapter_content
        ]
        if missing_adapter_markers:
            add_issue(
                issues,
                "recoverable",
                relative_path,
                f"calibration adapter contract is incomplete: {', '.join(missing_adapter_markers)}",
                "Align the adapter with canonical calibrate, remember, forget, local-hints, and runtime-boundary behavior.",
            )

    checked.append("AIM 2.0 feature support/reference roles")
    for support_path, role_marker in FEATURE_SUPPORT_ROLE_MARKERS.items():
        checked.append(support_path)
        support_doc_path = repo_root / support_path
        if not support_doc_path.is_file():
            add_issue(
                issues,
                "recoverable",
                support_path,
                "declared AIM support/reference doc is missing",
                "Restore the support/reference doc or remove it from the documented feature inventory.",
            )
            continue
        support_content = support_doc_path.read_text(encoding="utf-8", errors="replace")
        if role_marker not in support_content:
            add_issue(
                issues,
                "recoverable",
                support_path,
                f"support/reference role marker is missing: {role_marker}",
                "State the file's exact non-canonical role or promote it into docs/workflow if it defines AIM behavior.",
            )

    operating_mode_doc_path = repo_root / OPERATING_MODE_DOC_PATH
    checked.append(OPERATING_MODE_DOC_PATH)
    if operating_mode_doc_path.is_file():
        operating_mode_doc_content = operating_mode_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_operating_mode_markers = [
            marker
            for marker in REQUIRED_OPERATING_MODE_MARKERS
            if marker not in operating_mode_doc_content
        ]
        if missing_operating_mode_markers:
            add_issue(
                issues,
                "recoverable",
                OPERATING_MODE_DOC_PATH,
                f"operating mode model is missing required markers: {', '.join(missing_operating_mode_markers)}",
                "Update the canonical operating mode model so Personal, Team, and Enterprise behavior remains enforceable.",
            )
    else:
        add_issue(
            issues,
            "recoverable",
            OPERATING_MODE_DOC_PATH,
            "canonical operating mode model is missing",
            "Create docs/workflow/operating-modes.md before relying on mode-aware installation behavior.",
        )

    documentation_model_doc_path = repo_root / DOCUMENTATION_MODEL_DOC_PATH
    checked.append(DOCUMENTATION_MODEL_DOC_PATH)
    if documentation_model_doc_path.is_file():
        documentation_model_content = documentation_model_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_documentation_model_markers = [
            marker
            for marker in REQUIRED_DOCUMENTATION_MODEL_MARKERS
            if marker not in documentation_model_content
        ]
        if missing_documentation_model_markers:
            add_issue(
                issues,
                "recoverable",
                DOCUMENTATION_MODEL_DOC_PATH,
                f"documentation model is missing required markers: {', '.join(missing_documentation_model_markers)}",
                "Update the documentation source-of-truth model so canonical, repo-local, runtime, and maintainer surfaces stay distinct.",
            )
    else:
        add_issue(
            issues,
            "recoverable",
            DOCUMENTATION_MODEL_DOC_PATH,
            "canonical documentation model is missing",
            "Create docs/workflow/documentation-model.md before relying on documentation source-of-truth guidance.",
        )

    checked.append("AIM 2.0 repo profile readiness")
    repo_profile_readiness = collect_repo_profile_readiness(repo_root)
    profile_source_summary = build_profile_source_summary(repo_root, repo_profile_readiness)
    configured_operating_mode, operating_mode_source = detect_operating_mode(
        repo_root, repo_profile_readiness["profile_paths"]
    )
    readiness_status = repo_profile_readiness["status"]
    calibration_summary = {
        "technologies": [],
        "commands": [],
        "localities": [],
        "docs": [],
        "rules": [],
        "uncertainties": [],
    }
    for relative_path, markers in repo_profile_readiness["state_marker_findings"].items():
        add_issue(
            issues,
            "blocked",
            relative_path,
            f"repo-awareness contains runtime-state markers: {', '.join(markers)}",
            "Move active Epic, gate, role, increment, review, or acceptance state back to .aim runtime artifacts.",
        )

    for relative_path in repo_profile_readiness["profile_paths"]:
        profile_content = (repo_root / relative_path).read_text(
            encoding="utf-8", errors="replace"
        )
        calibration_status = extract_profile_scalar(profile_content, "calibration", "status")
        calibration_confidence = extract_profile_scalar(
            profile_content, "calibration", "confidence"
        )
        if relative_path in TEAM_REPO_PROFILE_PATHS:
            if calibration_status not in CALIBRATION_STATUSES:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"calibration status must be one of {sorted(CALIBRATION_STATUSES)}",
                    "Set calibration.status to ready, partially_ready, or needs_calibration.",
                )
            if calibration_confidence not in CALIBRATION_CONFIDENCE_VALUES:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"calibration confidence must be one of {sorted(CALIBRATION_CONFIDENCE_VALUES)}",
                    "Set calibration.confidence to high, medium, or low.",
                )

            knowledge_categories = extract_direct_child_keys(
                profile_content, "repoKnowledge"
            )
            missing_categories = sorted(
                REPO_KNOWLEDGE_CATEGORIES - knowledge_categories
            )
            unknown_categories = sorted(
                knowledge_categories - REPO_KNOWLEDGE_CATEGORIES
            )
            if missing_categories:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"repoKnowledge is missing structured categories: {', '.join(missing_categories)}",
                    "Add the missing categories, using empty lists when no calibrated facts exist yet.",
                )
            if unknown_categories:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"repoKnowledge contains unknown categories: {', '.join(unknown_categories)}",
                    "Map remembered rules into the canonical structured categories.",
                )

            for category_name in sorted(REPO_KNOWLEDGE_CATEGORIES):
                entries = extract_category_entries(profile_content, category_name)
                missing_ids = [
                    str(index + 1)
                    for index, entry in enumerate(entries)
                    if not entry.get("id")
                ]
                if missing_ids:
                    add_issue(
                        issues,
                        "recoverable",
                        relative_path,
                        f"{category_name} entries are missing stable IDs at positions: {', '.join(missing_ids)}",
                        "Give every remembered repo-awareness entry a stable id.",
                    )

            for index, doc_entry in enumerate(
                extract_category_entries(profile_content, "docs")
            ):
                if doc_entry.get("loading") not in DOCUMENT_LOADING_STATES:
                    add_issue(
                        issues,
                        "recoverable",
                        relative_path,
                        f"docs entry {doc_entry.get('id') or index + 1} has an invalid or missing loading state",
                        "Use authoritative, load_when_relevant, avoid_by_default, or stale_or_uncertain.",
                    )

            invalid_confidence_values = sorted(
                {
                    value
                    for value in extract_all_scalar_values(
                        profile_content, "confidence"
                    )
                    if value not in CALIBRATION_CONFIDENCE_VALUES
                }
            )
            if invalid_confidence_values:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"invalid confidence values: {', '.join(invalid_confidence_values)}",
                    "Use high, medium, or low confidence.",
                )

            loading_states = extract_loading_states(profile_content)
            invalid_loading_states = sorted(
                loading_states - DOCUMENT_LOADING_STATES
            )
            if invalid_loading_states:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"invalid document loading states: {', '.join(invalid_loading_states)}",
                    "Use authoritative, load_when_relevant, avoid_by_default, or stale_or_uncertain.",
                )
            calibration_summary["technologies"] = extract_repo_knowledge_values(
                profile_content, "technologies", ("value", "id")
            )
            calibration_summary["commands"] = extract_repo_knowledge_values(
                profile_content, "commands", ("command", "id")
            )
            calibration_summary["localities"] = extract_repo_knowledge_values(
                profile_content, "localities", ("path", "id")
            )
            calibration_summary["docs"] = extract_repo_knowledge_values(
                profile_content, "docs", ("path", "id")
            )
            calibration_summary["rules"] = [
                *extract_repo_knowledge_values(
                    profile_content, "habits", ("id", "rule")
                ),
                *extract_repo_knowledge_values(
                    profile_content, "avoidByDefault", ("id", "rule")
                ),
            ]
            uncertainties = extract_profile_scalar(
                profile_content, "calibration", "openUncertainties"
            )
            calibration_summary["uncertainties"] = (
                [] if uncertainties in {None, "[]"} else [uncertainties]
            )

    if configured_operating_mode == "Enterprise":
        gitignore_path = repo_root / ".gitignore"
        checked.append(".gitignore Enterprise ignore baseline")
        if gitignore_path.is_file():
            gitignore_content = gitignore_path.read_text(encoding="utf-8", errors="replace")
            missing_ignore_markers = [
                marker for marker in ENTERPRISE_IGNORE_MARKERS if marker not in gitignore_content
            ]
            if missing_ignore_markers:
                add_issue(
                    issues,
                    "recoverable",
                    ".gitignore",
                    f"Enterprise mode is missing required AIM-internal ignore markers: {', '.join(missing_ignore_markers)}",
                    "Add the Enterprise AIM ignore baseline or explicitly document why this repo promotes those AIM internals.",
                )
        else:
            add_issue(
                issues,
                "recoverable",
                ".gitignore",
                "Enterprise mode requires an ignore surface for AIM-internal artifacts",
                "Create .gitignore with the Enterprise AIM ignore baseline or document an equivalent repo policy.",
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
    for category in [
        "runtime",
        "repo_profile",
        "working_state",
        "docs",
        "adapter_helpers",
        "source_repo_maintainer_only",
    ]:
        paths = migration_classification.get(category, [])
        if paths:
            print(f"- {category}: {', '.join(paths)}")
        else:
            print(f"- {category}: none")

    print("AIM 2.0 surface boundary classification:")
    for category in [
        "static_product",
        "repo_aware_collision_prone",
        "source_repo_maintainer_only",
        "generic_root_files_outside_aim",
        "runtime_working_state",
        "support_reference_docs",
        "local_generated_never_ship",
    ]:
        paths = surface_boundary_classification.get(category, [])
        if paths:
            print(f"- {category}: {', '.join(paths)}")
        else:
            print(f"- {category}: none")

    print("AIM 2.0 operating mode model:")
    print(f"- canonical doc: {OPERATING_MODE_DOC_PATH}")
    print(
        f"- configured mode: {configured_operating_mode if configured_operating_mode else 'not declared'}"
    )
    print(f"- mode source: {operating_mode_source}")
    if configured_operating_mode == "Enterprise":
        print(f"- Enterprise ignore baseline: {', '.join(ENTERPRISE_IGNORE_MARKERS)}")

    print("AIM 2.0 documentation model:")
    print(f"- canonical doc: {DOCUMENTATION_MODEL_DOC_PATH}")
    print("- core truth: docs/workflow/agile-iteration-method.md")
    print("- canonical behavior surface: docs/workflow/")
    print("- support/reference surface: docs/features/")
    print("- primary shared repo-awareness: aim.profile.yaml")
    print("- generic root files: outside AIM architecture")
    print("- adapter policy: optional, secondary, and active-adapter-only")
    print("- CONTRIBUTING.md: AIM source-repository-only; excluded from all target installs and manifests")
    print(f"- installer boundary manifest: {INSTALL_MANIFEST_PATH}")
    print("- runtime state: .aim/ is not documentation truth")
    print("- promoted behavior docs:")
    for canonical_path in PROMOTED_CANONICAL_DOC_PATHS:
        print(f"  - {canonical_path}")
    print("- retained support/reference docs:")
    for support_path, role_marker in FEATURE_SUPPORT_ROLE_MARKERS.items():
        print(f"  - {support_path}: {role_marker}")

    print("AIM 2.0 repo profile readiness:")
    print(f"- status: {readiness_status}")
    print(f"- summary: {repo_profile_readiness['summary']}")
    print(
        f"- calibration confidence: {repo_profile_readiness.get('calibration_confidence') or 'not declared'}"
    )
    print(f"- personal hints path: {PERSONAL_HINTS_PATH}")
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

    print("AIM 2.0 calibration summary:")
    print(f"- Repo-awareness: {readiness_status}")
    print(
        f"- Technologies: {', '.join(calibration_summary['technologies'][:4]) or 'none'}"
    )
    print(f"- Commands: {', '.join(calibration_summary['commands'][:4]) or 'none'}")
    print(
        f"- Selected localities: {', '.join(calibration_summary['localities'][:4]) or 'none'}"
    )
    print(f"- Docs by need: {', '.join(calibration_summary['docs'][:4]) or 'none'}")
    print(
        f"- Remembered rules: {', '.join(calibration_summary['rules'][:6]) or 'none'}"
    )
    print(
        f"- Open uncertainties: {', '.join(calibration_summary['uncertainties']) or 'none'}"
    )
    print(
        "- Next calibration action: none"
        if readiness_status == "ready"
        else "- Next calibration action: run /aim calibrate-repo"
    )

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
