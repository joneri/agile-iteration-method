#!/usr/bin/env python3
"""Validate AIM runtime or release-facing product state without mutating it."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from aim_installer import closure as installer_closure
from aim_installer import planner as installer_planner
from aim_installer import seed as installer_seed
from aim_installer.manifest import ManifestError, load_manifest
from aim_installer.yaml_lite import YamlLiteError, loads as load_aim_yaml
from aim_docs import audit as audit_documentation
from build_public_skill import PublicSkillError, validate_committed_package
from aim_validator.coherence import evaluate_product_coherence
from aim_validator.profile_contract import (
    PERSONAL_HINTS_SCHEMA_PATH,
    REPO_PROFILE_SCHEMA_PATH,
    SUPPORTED_HINTS_VERSION,
    SUPPORTED_PROFILE_VERSION,
    load_schema,
    parse_and_validate_personal_hints,
    parse_and_validate_repo_profile,
)
from aim_validator.reporting import (
    findings_by_category,
    make_finding,
    release_readiness,
    summarize_result as summarize_typed_result,
    tier_statuses,
)
from aim_validator.runtime_state import (
    RUNTIME_STATE_SCHEMA_PATH,
    SUPPORTED_STATE_SCHEMA_VERSION,
    load_runtime_state,
)
from aim_validator.schema_subset import unsupported_keywords, validate as validate_schema
from aim_portfolio_run import validate_run as validate_portfolio_run


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
ENTERPRISE_MEMORY_PATH = "~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml"

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

DEFAULT_STATIC_MEMORY_DOC_PREFIXES = {
    "docs/architecture/",
    "docs/features/",
    "docs/workflow/",
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
        "docs/product",
        "docs/features",
        "docs/workflow",
    ],
    "adapter_helpers": [
        ".claude",
        ".github/agents",
        ".github/skills",
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
        "docs/product",
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
PUBLIC_PRODUCT_DOC_PATHS = {
    "README.md": [
        "# Agile Iteration Method (AIM) 2.7",
        "## Install",
        "## How AIM works",
        "## What is new in v2.7.0",
        "/aim reflect",
        "/aim reflect-all",
        "goes beyond memory cleanup for repository work",
        "## Smarter output from the start",
        "audience-context integrity",
        "docs/product/features.md",
    ],
    "docs/product/README.md": [
        "public product guide",
        "complete public Agent Skill",
        "adaptive installer",
        "## Documentation Layers",
        "Product docs",
        "Workflow docs",
        "Maintainer docs",
    ],
    "docs/product/what-is-aim.md": [
        "A Delivery System, Not a Coding Assistant",
        "## Quality First",
        "## Repository-Aware",
        "## Memory Without Context Bloat",
        "## Human Controlled",
    ],
    "docs/product/getting-started.md": [
        "## 1. Install AIM",
        "npx skills add joneri/agile-iteration-method",
        "full AIM",
        "## 2. Calibrate the Repository",
        "## 3. Remember Important Project Context",
        "## 4. Reflect on Completed Work",
        "## 5. Start an Epic",
        "## 6. Review Gate A",
        "## 7. Approve the Next Increment",
        "## 8. Build With Confidence",
    ],
    "docs/product/platforms-and-adoption.md": [
        "# Platforms and Project Agents",
        "## Choose an Installation Path",
        "npx skills add joneri/agile-iteration-method",
        "## One Product, Project-Specific Specialists",
        "## Configure or Refresh",
        "## What Stays Shared",
        "## What May Differ",
        "## Storage and Sharing Policy",
    ],
}
SURFACE_MODEL_DOC_PATH = "docs/workflow/repository-surface-classification.md"
REPO_AWARENESS_DOC_PATH = "docs/workflow/repo-awareness.md"
REPO_CALIBRATION_DOC_PATH = "docs/workflow/repo-awareness-calibration.md"
TWO_LAYER_DOC_PATH = "docs/workflow/repo-awareness-two-layer-model.md"
INSTALL_GUIDE_DOC_PATH = "docs/workflow/install-aim-2.0.md"
INSTALL_MANIFEST_PATH = "install/aim-install-manifest.yaml"

ADAPTER_ENTRY_MODEL_DOC_PATH = "docs/workflow/adapter-entry-model.md"
ADAPTER_COMMAND_CONTRACT_DOC_PATH = "docs/workflow/adapter-command-contract.md"
ADAPTER_SKILL_BOOTSTRAP_DOC_PATH = "docs/workflow/adapter-skill-bootstrap.md"
LIGHT_FRONT_DOOR_DOC_PATH = "docs/workflow/light-front-door.md"
PRODUCT_COHERENCE_DOC_PATH = "docs/workflow/product-coherence-validation.md"
REPO_PROFILE_SCHEMA_DOC_PATH = "docs/workflow/repo-profile-schema.md"
RELEASE_PUBLICATION_DOC_PATH = "docs/workflow/release-publication-model.md"
PUBLIC_SKILL_DISTRIBUTION_DOC_PATH = "docs/workflow/version-and-installation.md"
REFLECTION_DOC_PATH = "docs/workflow/reflection.md"
PROJECT_ROLES_SCHEMA_PATH = "schemas/aim-project-roles.schema.json"
PROJECT_ROLES_PATH = "aim.roles.yaml"
AIM_UI_PORTFOLIO_SCHEMA_PATH = "schemas/aim-ui-portfolio.schema.json"
AIM_UI_PORTFOLIO_PATH = ".aim/ui-portfolio.json"
AIM_UI_BACKLOG_SCHEMA_PATH = "schemas/aim-ui-backlog.schema.json"
AIM_UI_BACKLOG_PATH = ".aim/portfolio-backlog.json"
AIM_PORTFOLIO_CONTROL_SCHEMA_PATH = "schemas/aim-portfolio-control.schema.json"
AIM_PORTFOLIO_CONTROL_PATH = ".aim/portfolio-control.json"
AIM_PORTFOLIO_RUN_SCHEMA_PATH = "schemas/aim-portfolio-run.schema.json"
AIM_PORTFOLIO_RUN_PATH = ".aim/portfolio-run.json"

CANONICAL_AIM_COMMANDS = [
    "/aim start",
    "/aim continue",
    "/aim status",
    "/aim validate",
    "/aim help",
    "/aim config",
    "/aim to-backlog",
    "/aim configure-agents",
    "/aim calibrate-repo",
    "/aim remember-repo",
    "/aim forget-repo",
    "/aim reflect",
    "/aim reflect-all",
    "/aim upgrade",
    "/aim mode",
    "/aim cost",
    "/aim replan",
]

CLAUDE_COMMAND_SURFACES = {
    "/aim start": ".claude/commands/start-aim.md",
    "/aim continue": ".claude/commands/continue-aim.md",
    "/aim status": ".claude/commands/status-aim.md",
    "/aim validate": ".claude/commands/validate-aim.md",
    "/aim help": ".claude/commands/help-aim.md",
    "/aim config": ".claude/commands/config-aim.md",
    "/aim to-backlog": ".claude/commands/to-backlog-aim.md",
    "/aim configure-agents": ".claude/commands/configure-agents-aim.md",
    "/aim calibrate-repo": ".claude/commands/calibrate-repo.md",
    "/aim remember-repo": ".claude/commands/remember-repo.md",
    "/aim forget-repo": ".claude/commands/forget-repo.md",
    "/aim reflect": ".claude/commands/reflect-aim.md",
    "/aim reflect-all": ".claude/commands/reflect-all-aim.md",
    "/aim upgrade": ".claude/commands/upgrade-aim.md",
    "/aim mode": ".claude/commands/mode-aim.md",
    "/aim cost": ".claude/commands/cost-aim.md",
    "/aim replan": ".claude/commands/replan-aim.md",
}

COMMAND_FAMILY_SURFACES = {
    "Codex": "adapters/codex/agile-iteration-method/SKILL.md",
    "Claude": ".claude/skills/aim/SKILL.md",
    "GitHub Copilot": ".github/skills/aim/SKILL.md",
}

REQUIRED_ADAPTER_ENTRY_MODEL_MARKERS = [
    "user-facing entry surface",
    "internal helper surface",
    "fallback",
    "skill-led",
    "/aim start",
    "/aim continue",
    "/aim validate",
    "/aim help",
    "/aim calibrate-repo",
    "/aim remember-repo",
    "/aim forget-repo",
    "/aim reflect",
    "/aim reflect-all",
    "/aim status",
    "/aim config",
    "/aim to-backlog",
    "/aim upgrade",
    "/aim mode",
    "/aim cost",
    "/aim replan",
    ADAPTER_COMMAND_CONTRACT_DOC_PATH,
    "Codex",
    "GitHub Copilot",
    "Claude",
    ".claude/commands/",
    ".claude/skills/aim/",
    ".claude/agents/",
    ".github/agents/",
    ".github/skills/aim/",
    ADAPTER_SKILL_BOOTSTRAP_DOC_PATH,
]

ADAPTER_ENTRY_SURFACE_MARKERS = {
    "adapters/codex/agile-iteration-method/SKILL.md": [
        "skill/package-first",
        "references/adapter-entry-model.md",
        "references/adapter-skill-bootstrap.md",
    ],
    ".claude/skills/aim/SKILL.md": ["primary AIM front door", ADAPTER_SKILL_BOOTSTRAP_DOC_PATH],
    ".github/skills/aim/SKILL.md": ["AIM workflow source", ADAPTER_SKILL_BOOTSTRAP_DOC_PATH],
    ".claude/agents/aim.md": ["internal helper surface", "skill-led"],
    ".github/agents/aim.agent.md": ["skill-led", ADAPTER_ENTRY_MODEL_DOC_PATH],
}

REQUIRED_ONBOARDING_DOC_MARKERS = [
    "detects onboarding state first",
    "recommends exactly one next action",
    "You are here",
    "Recommended next action",
    "installed but not calibrated",
    "calibrated but no Epic exists",
    "Epic exists but is not approved",
    "Epic approved",
    "blocked",
    "/aim calibrate-repo",
    '/aim start "EPIC:',
    "do not lead with internal file paths",
    "command inventories",
]

REQUIRED_ONBOARDING_CONTRACT_MARKERS = [
    "onboarding state first",
    "recommend exactly one next action",
    "You are here",
    "Recommended next action",
    "installed but not calibrated",
    "calibrated but no Epic exists",
    "Epic exists but is not approved",
    "Epic approved",
    "blocked",
    "/aim calibrate-repo",
    '/aim start "EPIC:',
    "must not lead with internal file paths",
    "command inventory",
]

ONBOARDING_SURFACES = {
    "adapters/codex/agile-iteration-method/SKILL.md": [
        "detect onboarding state first",
        "recommend exactly one next action",
        "You are here",
        "Recommended next action",
        "installed but not calibrated",
        "calibrated but no Epic exists",
        "Epic exists but is not approved",
        "Epic approved",
        "blocked",
        "/aim calibrate-repo",
        '/aim start "EPIC:',
        "do not lead with internal file paths",
        "command\ninventory",
        "new homes for cats",
    ],
    ".github/skills/aim/SKILL.md": [
        "detect onboarding state first",
        "recommend exactly one next action",
        "You are here",
        "Recommended next action",
        "installed but not calibrated",
        "calibrated but no Epic exists",
        "Epic exists but is not approved",
        "Epic approved",
        "blocked",
        "/aim calibrate-repo",
        '/aim start "EPIC:',
        "do not lead with internal file paths",
        "command inventory",
        "new homeowner",
    ],
    ".claude/skills/aim/SKILL.md": [
        "Detect onboarding state first",
        "recommend exactly one next action",
        "You are here",
        "Recommended next action",
        "installed but not calibrated",
        "calibrated but no Epic exists",
        "an unapproved Epic",
        "an approved Epic",
        "blocked",
        "/aim calibrate-repo",
        '/aim start "EPIC:',
        "Do not lead with internal file paths",
        "command inventory",
        "new homeowner",
    ],
    ".github/prompts/help-aim.prompt.md": [
        "Detect onboarding state first",
        "recommend exactly one next action",
        "You are here",
        "Recommended next action",
        "installed but not calibrated",
        "calibrated but no Epic exists",
        "Epic exists but is not approved",
        "Epic approved",
        "blocked",
        "/aim calibrate-repo",
        '/aim start "EPIC:',
        "Do not lead with internal file paths",
        "command inventory",
        "new homes for cats",
    ],
    ".claude/commands/help-aim.md": [
        "Detect onboarding state first",
        "recommend exactly one next action",
        "You are here",
        "Recommended next action",
        "installed but not calibrated",
        "calibrated but no Epic exists",
        "Epic exists but is not approved",
        "Epic approved",
        "blocked",
        "/aim calibrate-repo",
        '/aim start "EPIC:',
        "Do not lead with internal file paths",
        "command inventory",
    ],
    ".claude/agents/aim.md": [
        "detect onboarding state first",
        "recommend exactly one next action",
        "do not lead with",
        "command inventory",
    ],
}

REMOVED_GENERIC_AIM_ROOT_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
]

REQUIRED_REPO_AWARENESS_MARKERS = [
    "aim.profile.yaml",
    "primary shared repo-awareness source",
    "source of durable repo-awareness",
    "docs/architecture/",
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
    "static memory document",
    "durable repo-awareness reference to `.aim/reviews`",
    "`ready`",
    "`partially_ready`",
    "`needs_calibration`",
    "`authoritative`",
    "`load_when_relevant`",
    "`avoid_by_default`",
    "`stale_or_uncertain`",
]

REQUIRED_REFLECTION_DOC_MARKERS = [
    "/aim reflect",
    "/aim reflect-all",
    ".aim/analysis/",
    "~/.aim/reflection-roots.yaml",
    "aimReflectionRoots:",
    'version: "0.1"',
    "/absolute/path/to/projects",
    "parent directory of the current repository",
    "Never use the home directory",
    "untrusted evidence",
    "current code",
    "provenance",
    "confidence",
    "contradictions",
    "proposed durable destination",
    "explicit promotion action",
    "## Action conclusion",
    "Reflection conclusion:",
    "Recommended next action:",
    "`promote`",
    "`correct`",
    "`remove`",
    "`defer`",
    "`no-action`",
    "No action recommended",
    "safe AIM intents, not shell commands",
    "separate user-owned operation",
    "never modifies",
    "project",
    "cross-project",
    "aim-product",
    "personal",
    "goes beyond memory cleanup for repository work",
]

REQUIRED_TWO_LAYER_MARKERS = [
    "Layer 1: structured profile",
    "Layer 2: static memory and operational documents",
    "docs/features/",
    "docs/workflow/",
    "docs/architecture/",
    "`kind: operational`",
    "`memory`",
    "No durable pointer may target `.aim/`",
    "workTypes",
    "rolesOrGates",
    "risks",
    "commands",
    "calibration",
]

OPERATIONAL_DOC_REQUIRED_HEADINGS = [
    "## Purpose",
    "## Applicability",
    "## Procedure",
    "## Commands",
    "## Evidence",
    "## Blockers",
    "## Edge Cases",
    "## Debugging",
    "## Related Surfaces",
]

PROFILE_PROSE_LIMIT = 240

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
    "footprints:",
    "defaultFootprint: external",
    "defaultFootprint: adapters",
    "externalDocs:",
    "externalRepoAwareness:",
    "footprintProfiles:",
    "embeddedDocs:",
    "repoAdapters:",
    "sharedProfile:",
    "repoIgnore:",
    "homeAdapters:",
    "adapterClosure:",
    "every-required-adapter-document-reference-must-resolve-after-install",
    "strategy: embedded-package",
    "strategy: installed-canonical-subset",
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
    "enterpriseMemory: ~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml",
    "reflectionRoots: ~/.aim/reflection-roots.yaml",
    "reflectionReports: .aim/analysis/",
    "reflectionDurableWrites: forbidden",
    "readyRequiresCalibration: true",
    "calibrationCommand: /aim calibrate-repo",
    "runtimeProfileStorage: forbidden",
    "adapterSkills:",
    "source: .claude/skills/aim/SKILL.md",
    "source: .github/skills/aim/SKILL.md",
    "source: adapters/codex/agile-iteration-method/SKILL.md",
    "scope: user",
    "scope: project",
]

CALIBRATION_ADAPTER_MARKERS = {
    "adapters/codex/agile-iteration-method/SKILL.md": [
        "/aim calibrate-repo",
        "/aim remember-repo",
        "/aim forget-repo",
        ENTERPRISE_MEMORY_PATH,
        PERSONAL_HINTS_PATH,
    ],
    ".github/agents/aim.agent.md": [
        "/aim calibrate-repo",
        "/aim remember-repo",
        "/aim forget-repo",
        ENTERPRISE_MEMORY_PATH,
        PERSONAL_HINTS_PATH,
    ],
    ".claude/commands/calibrate-repo.md": [
        "/aim calibrate-repo",
        ENTERPRISE_MEMORY_PATH,
        PERSONAL_HINTS_PATH,
        "never store stable repo-awareness under `.aim/`",
    ],
    ".claude/commands/remember-repo.md": [
        "/aim remember-repo",
        ENTERPRISE_MEMORY_PATH,
        PERSONAL_HINTS_PATH,
        "Never store stable repository knowledge under `.aim/`",
    ],
    ".claude/commands/forget-repo.md": [
        "/aim forget-repo",
        "Never mutate `.aim/`",
    ],
}

REQUIRED_OPERATING_MODE_MARKERS = [
    "two maintained distribution paths",
    "standard skills CLI",
    "repository-aware setup",
    "Legacy flag mapping",
    "Strict or Auto",
    "Standard, Cost Control, or Deep",
    "AGENTS.md",
    "CLAUDE.md",
    "aim.roles.yaml",
]

ENTERPRISE_IGNORE_MARKERS = [
    "/.aim",
    "/.aim-local",
    "/aim.local.*",
    "/*.aim.local.md",
    "/*.aim.process.md",
]

OPERATING_MODE_VALUES = {
    "standard": "Standard installation policy",
    "personal": "Personal",
    "team": "Team",
    "enterprise": "Enterprise",
}

REQUIRED_DOCUMENTATION_MODEL_MARKERS = [
    "Public product docs",
    "docs/product/",
    "public-facing explanation and onboarding layer",
    "AIM core truth",
    "docs/workflow/agile-iteration-method.md",
    "docs/workflow/operating-modes.md",
    "docs/workflow/repository-surface-classification.md",
    "docs/workflow/cost-control-mode.md",
    "docs/workflow/cost-review-checklist.md",
    "docs/workflow/cost-saving-method.md",
    "docs/workflow/modularity-context-efficiency.md",
    "docs/workflow/repo-awareness-calibration.md",
    "docs/workflow/repo-awareness-two-layer-model.md",
    "docs/workflow/adapter-command-contract.md",
    PRODUCT_COHERENCE_DOC_PATH,
    REPO_PROFILE_SCHEMA_DOC_PATH,
    RELEASE_PUBLICATION_DOC_PATH,
    PUBLIC_SKILL_DISTRIBUTION_DOC_PATH,
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
    "docs/workflow/adapter-command-contract.md": "docs/features/aim-adapter-command-contract.md",
    PRODUCT_COHERENCE_DOC_PATH: "docs/features/aim-product-coherence-validation.md",
    "docs/workflow/documentation-model.md": "docs/features/aim-2-documentation-model.md",
    "docs/workflow/operating-modes.md": "docs/features/aim-2-operating-modes.md",
    "docs/workflow/repository-surface-classification.md": "docs/features/aim-2-repository-surface-classification.md",
    "docs/workflow/repo-profile-and-footprint-model.md": "docs/features/aim-2-repo-profile-and-footprint-model.md",
    "docs/workflow/working-state-boundaries.md": "docs/features/aim-2-working-state-boundaries.md",
    "docs/workflow/cost-control-mode.md": "docs/features/aim-cost-control-mode.md",
    "docs/workflow/modularity-context-efficiency.md": "docs/features/aim-modularity-context-efficiency.md",
    "docs/workflow/profile-source-summary.md": "docs/features/aim-2-profile-source-summary.md",
    "docs/workflow/codex-skill-onboarding.md": "docs/features/aim-codex-bundled-skill-onboarding.md",
    "docs/workflow/light-front-door.md": "docs/features/aim-light-front-door.md",
    "docs/workflow/cost-review-checklist.md": "docs/features/aim-cost-review-checklist.md",
    "docs/workflow/cost-saving-method.md": "docs/features/aim-cost-saving-method.md",
    RELEASE_PUBLICATION_DOC_PATH: "docs/features/aim-release-publication-model.md",
    PUBLIC_SKILL_DISTRIBUTION_DOC_PATH: "docs/features/aim-public-skill-distribution.md",
    REFLECTION_DOC_PATH: "docs/features/aim-reflection.md",
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


def add_issue(
    issues: list[dict[str, object]],
    result: str,
    artifact: str,
    rule: str,
    action: str,
    *,
    tier: str | None = None,
    category: str | None = None,
    release_impact: str | None = None,
    evidence: str | None = None,
) -> None:
    issues.append(
        make_finding(
            result,
            artifact,
            rule,
            action,
            tier=tier,
            category=category,
            release_impact=release_impact,
            evidence=evidence,
        )
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


def summarize_result(issues: list[dict[str, object]]) -> str:
    return summarize_typed_result(issues)


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
    section_indent = (
        len(lines[0]) - len(lines[0].lstrip())
        if lines and lines[0].strip() == "repoKnowledge:"
        else -2
    )
    matched_values = []

    for index, line in enumerate(lines):
        line_indent = len(line) - len(line.lstrip())
        if (
            line.strip() != f"{category_name}:"
            or line_indent != section_indent + 2
        ):
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
    section_indent = (
        len(lines[0]) - len(lines[0].lstrip())
        if lines and lines[0].strip() == "repoKnowledge:"
        else -2
    )
    matched_entries = []

    for index, line in enumerate(lines):
        line_indent = len(line) - len(line.lstrip())
        if (
            line.strip() != f"{category_name}:"
            or line_indent != section_indent + 2
        ):
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
            if (
                child_stripped.startswith("- ")
                and child_indent == category_indent + 2
            ):
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


def find_overlong_profile_scalars(content: str) -> list[str]:
    block = extract_section_block(content, "repoKnowledge")
    if not block:
        return []

    findings = []
    for line in block.splitlines():
        stripped = line.strip()
        normalized = stripped[2:] if stripped.startswith("- ") else stripped
        if ":" not in normalized:
            continue
        key, value = normalized.split(":", 1)
        value = value.strip().strip("\"'")
        if len(value) > PROFILE_PROSE_LIMIT:
            findings.append(f"{key.strip()} ({len(value)} chars)")
    return findings


def missing_case_insensitive_markers(content: str, markers: list[str]) -> list[str]:
    normalized_content = content.lower()
    return [marker for marker in markers if marker.lower() not in normalized_content]


def operational_doc_paths(content: str) -> list[str]:
    paths = []
    for entry in extract_category_entries(content, "docs"):
        path = entry.get("path", "")
        if entry.get("kind") == "operational" and path:
            paths.append(path)
    return paths


def static_memory_doc_prefixes(content: str) -> set[str]:
    prefixes = set(DEFAULT_STATIC_MEMORY_DOC_PREFIXES)
    docs_source_values = extract_profile_section_values(content, "storage")
    for value in docs_source_values:
        if not value.startswith("docsSource:"):
            continue
        for match in re.findall(r"docs/[A-Za-z0-9._/-]+/?", value):
            normalized = match if match.endswith("/") else f"{match}/"
            prefixes.add(normalized)
    return prefixes


def is_static_memory_doc_path(path: str, prefixes: set[str]) -> bool:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized.startswith(".aim/") or normalized == ".aim":
        return False
    return any(normalized.startswith(prefix) for prefix in prefixes)


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
    arguments = sys.argv[1:]
    release_mode = "--release" in arguments
    positional = [argument for argument in arguments if argument != "--release"]
    if len(positional) > 1:
        print("usage: validate_aim_runtime.py [repo] [--release]", file=sys.stderr)
        return 2
    repo_root = Path(positional[0] if positional else ".").resolve()
    checked: list[str] = []
    issues: list[dict[str, object]] = []

    runtime_state_result = load_runtime_state(repo_root)
    checked.append("AIM runtime-state schema contract")
    checked.append(
        f"runtime-state schema: {RUNTIME_STATE_SCHEMA_PATH} ({SUPPORTED_STATE_SCHEMA_VERSION})"
    )
    checked.append(f"runtime-state compatibility: {runtime_state_result.classification}")
    for finding in runtime_state_result.findings:
        add_issue(
            issues,
            finding.result,
            ".aim/state.json",
            finding.rule,
            finding.action,
        )

    checked.append("AIM 2.7 documentation audit")
    for documentation_error in audit_documentation(repo_root):
        add_issue(
            issues,
            "blocked",
            "documentation release surfaces",
            documentation_error,
            "Fix the link, version, feature coverage, front-door length, or website structure before release.",
        )

    checked.append("generated public Agent Skill package")
    try:
        validate_committed_package(repo_root)
    except (OSError, json.JSONDecodeError, PublicSkillError) as exc:
        add_issue(
            issues,
            "contradictory",
            "skills/agile-iteration-method",
            f"generated public skill validation failed: {exc}",
            "Regenerate with python3 scripts/build_public_skill.py and commit the exact deterministic output.",
            tier="Release readiness",
            category="Contradiction",
            release_impact="fail",
        )

    required_repo_files = [
        repo_root / "README.md",
        *[repo_root / path for path in PUBLIC_PRODUCT_DOC_PATHS if path != "README.md"],
        repo_root / "docs/workflow/agile-iteration-method.md",
        repo_root / REPO_AWARENESS_DOC_PATH,
        repo_root / REPO_CALIBRATION_DOC_PATH,
        repo_root / TWO_LAYER_DOC_PATH,
        repo_root / DOCUMENTATION_MODEL_DOC_PATH,
        repo_root / SURFACE_MODEL_DOC_PATH,
        repo_root / ADAPTER_ENTRY_MODEL_DOC_PATH,
        repo_root / PRODUCT_COHERENCE_DOC_PATH,
        repo_root / REPO_PROFILE_SCHEMA_DOC_PATH,
        repo_root / RELEASE_PUBLICATION_DOC_PATH,
        repo_root / PUBLIC_SKILL_DISTRIBUTION_DOC_PATH,
        repo_root / INSTALL_MANIFEST_PATH,
        repo_root / REPO_PROFILE_SCHEMA_PATH,
        repo_root / PERSONAL_HINTS_SCHEMA_PATH,
        repo_root / PROJECT_ROLES_SCHEMA_PATH,
        repo_root / PROJECT_ROLES_PATH,
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

    repo_profile_schema = None
    personal_hints_schema = None
    project_roles_schema = None
    aim_ui_portfolio_schema = None
    aim_ui_backlog_schema = None
    aim_portfolio_control_schema = None
    aim_portfolio_run_schema = None
    for relative_path, schema_name in (
        (REPO_PROFILE_SCHEMA_PATH, "repo profile"),
        (PERSONAL_HINTS_SCHEMA_PATH, "Personal hints"),
        (PROJECT_ROLES_SCHEMA_PATH, "project roles"),
        (AIM_UI_PORTFOLIO_SCHEMA_PATH, "AIM UI portfolio"),
        (AIM_UI_BACKLOG_SCHEMA_PATH, "AIM UI portfolio backlog"),
        (AIM_PORTFOLIO_CONTROL_SCHEMA_PATH, "AIM portfolio control"),
        (AIM_PORTFOLIO_RUN_SCHEMA_PATH, "AIM Portfolio Auto run"),
    ):
        checked.append(f"{schema_name} JSON Schema")
        try:
            loaded_schema = load_schema(repo_root, relative_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            add_issue(
                issues,
                "blocked",
                relative_path,
                f"{schema_name} schema is unavailable or invalid JSON: {exc}",
                "Restore a valid Draft 2020-12 JSON Schema document.",
                tier="Structural",
                category="Error",
                release_impact="fail",
            )
            continue
        if relative_path == REPO_PROFILE_SCHEMA_PATH:
            repo_profile_schema = loaded_schema
        elif relative_path == PERSONAL_HINTS_SCHEMA_PATH:
            personal_hints_schema = loaded_schema
        elif relative_path == PROJECT_ROLES_SCHEMA_PATH:
            project_roles_schema = loaded_schema
        elif relative_path == AIM_UI_PORTFOLIO_SCHEMA_PATH:
            aim_ui_portfolio_schema = loaded_schema
        elif relative_path == AIM_UI_BACKLOG_SCHEMA_PATH:
            aim_ui_backlog_schema = loaded_schema
        elif relative_path == AIM_PORTFOLIO_CONTROL_SCHEMA_PATH:
            aim_portfolio_control_schema = loaded_schema
        else:
            aim_portfolio_run_schema = loaded_schema
        for schema_issue in unsupported_keywords(loaded_schema):
            add_issue(
                issues,
                "blocked",
                relative_path,
                f"{schema_name} schema uses an unsupported internal-validator keyword at {schema_issue.path}",
                "Implement and test the schema keyword before publishing it in an AIM schema.",
                tier="Structural",
                category="Error",
                release_impact="fail",
            )

    checked.append("AIM UI portfolio catalog")
    portfolio_path = repo_root / AIM_UI_PORTFOLIO_PATH
    if aim_ui_portfolio_schema is not None and portfolio_path.is_file():
        try:
            portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            add_issue(
                issues,
                "contradictory",
                AIM_UI_PORTFOLIO_PATH,
                f"AIM UI portfolio is invalid JSON: {exc}",
                "Repair or remove the optional portfolio catalog.",
            )
        else:
            for schema_issue in validate_schema(portfolio, aim_ui_portfolio_schema):
                add_issue(
                    issues,
                    "contradictory",
                    AIM_UI_PORTFOLIO_PATH,
                    f"AIM UI portfolio violates the schema at {schema_issue.path}: {schema_issue.message}",
                    "Align the optional catalog with schemas/aim-ui-portfolio.schema.json.",
                )

    checked.append("AIM UI portfolio backlog")
    backlog_path = repo_root / AIM_UI_BACKLOG_PATH
    if aim_ui_backlog_schema is not None and backlog_path.is_file():
        try:
            backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            add_issue(
                issues,
                "contradictory",
                AIM_UI_BACKLOG_PATH,
                f"AIM UI portfolio backlog is invalid JSON: {exc}",
                "Repair or remove the optional portfolio backlog.",
            )
        else:
            for schema_issue in validate_schema(backlog, aim_ui_backlog_schema):
                add_issue(
                    issues,
                    "contradictory",
                    AIM_UI_BACKLOG_PATH,
                    f"AIM UI portfolio backlog violates the schema at {schema_issue.path}: {schema_issue.message}",
                    "Align the optional planning input with schemas/aim-ui-backlog.schema.json.",
                )
            identifiers = [
                item.get("id")
                for item in backlog.get("items", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            ] if isinstance(backlog, dict) else []
            duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
            if duplicates:
                add_issue(
                    issues,
                    "contradictory",
                    AIM_UI_BACKLOG_PATH,
                    f"AIM UI portfolio backlog contains duplicate ids: {', '.join(duplicates)}",
                    "Give every planned Increment candidate a unique stable id.",
                )
            priorities = [
                item.get("priority")
                for item in backlog.get("items", [])
                if isinstance(item, dict)
            ] if isinstance(backlog, dict) else []
            if any(
                not isinstance(priority, int)
                or isinstance(priority, bool)
                or priority < 1
                for priority in priorities
            ):
                add_issue(
                    issues,
                    "contradictory",
                    AIM_UI_BACKLOG_PATH,
                    "AIM UI portfolio backlog priorities must be positive integers",
                    "Use a positive integer priority for every planned Increment candidate.",
                )

    checked.append("AIM portfolio control")
    control_path = repo_root / AIM_PORTFOLIO_CONTROL_PATH
    if aim_portfolio_control_schema is not None and control_path.is_file():
        try:
            control = json.loads(control_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            add_issue(
                issues,
                "contradictory",
                AIM_PORTFOLIO_CONTROL_PATH,
                f"AIM portfolio control is invalid JSON: {exc}",
                "Repair or remove the optional chat-owned portfolio control.",
            )
        else:
            for schema_issue in validate_schema(control, aim_portfolio_control_schema):
                add_issue(
                    issues,
                    "contradictory",
                    AIM_PORTFOLIO_CONTROL_PATH,
                    f"AIM portfolio control violates the schema at {schema_issue.path}: {schema_issue.message}",
                    "Align the optional control with schemas/aim-portfolio-control.schema.json.",
                )

    checked.append("AIM Portfolio Auto run")
    run_path = repo_root / AIM_PORTFOLIO_RUN_PATH
    if aim_portfolio_run_schema is not None and (run_path.exists() or run_path.is_symlink()):
        if run_path.is_symlink():
            add_issue(
                issues,
                "contradictory",
                AIM_PORTFOLIO_RUN_PATH,
                "AIM Portfolio Auto run must not be a symbolic link",
                "Replace it with a repository-contained regular JSON file.",
            )
        else:
            try:
                portfolio_run = json.loads(run_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                add_issue(
                    issues,
                    "contradictory",
                    AIM_PORTFOLIO_RUN_PATH,
                    f"AIM Portfolio Auto run is invalid JSON: {exc}",
                    "Repair the checkpoint from the authoritative AIM chat before resuming.",
                )
            else:
                for schema_issue in validate_schema(portfolio_run, aim_portfolio_run_schema):
                    add_issue(
                        issues,
                        "contradictory",
                        AIM_PORTFOLIO_RUN_PATH,
                        f"AIM Portfolio Auto run violates the schema at {schema_issue.path}: {schema_issue.message}",
                        "Align it with schemas/aim-portfolio-run.schema.json before resuming.",
                    )
                for semantic_issue in validate_portfolio_run(portfolio_run):
                    add_issue(
                        issues,
                        "contradictory",
                        AIM_PORTFOLIO_RUN_PATH,
                        f"AIM Portfolio Auto run is inconsistent: {semantic_issue}",
                        "Repair the immutable snapshot or checkpoint from the authoritative AIM chat.",
                    )

    checked.append("AIM project role profile")
    if project_roles_schema is not None and (repo_root / PROJECT_ROLES_PATH).is_file():
        try:
            project_roles = load_aim_yaml(
                (repo_root / PROJECT_ROLES_PATH).read_text(encoding="utf-8")
            )
        except (OSError, YamlLiteError, IndexError) as exc:
            add_issue(
                issues,
                "blocked",
                PROJECT_ROLES_PATH,
                f"project role profile is invalid AIM YAML: {exc}",
                "Repair aim.roles.yaml before generating supplier-native agents.",
                tier="Structural",
                category="Error",
                release_impact="fail",
            )
        else:
            for schema_issue in validate_schema(project_roles, project_roles_schema):
                add_issue(
                    issues,
                    "blocked",
                    PROJECT_ROLES_PATH,
                    f"project role profile violates the schema at {schema_issue.path}: {schema_issue.message}",
                    "Align aim.roles.yaml with schemas/aim-project-roles.schema.json.",
                    tier="Behavioral",
                    category="Error",
                    release_impact="fail",
                )

    native_specialists = {
        "Codex": [f".codex/agents/aim-{role}.toml" for role in ("po", "tdo", "dev", "reviewer")],
        "Claude": [f".claude/agents/aim-{role}.md" for role in ("po", "tdo", "dev", "reviewer")],
        "GitHub Copilot": [f".github/agents/aim-{role}.agent.md" for role in ("po", "tdo", "dev", "reviewer")],
    }
    checked.append("supplier-native AIM project specialists")
    for supplier, paths in native_specialists.items():
        for relative_path in paths:
            checked.append(relative_path)
            path = repo_root / relative_path
            if not path.is_file():
                add_issue(
                    issues,
                    "blocked",
                    relative_path,
                    f"{supplier} native AIM specialist is missing",
                    "Restore all four canonical project role specialists.",
                    tier="Behavioral",
                    category="Error",
                    release_impact="fail",
                )
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            missing = [
                marker
                for marker in ("aim.roles.yaml", ".aim/state.json")
                if marker not in content
            ]
            if missing:
                add_issue(
                    issues,
                    "blocked",
                    relative_path,
                    f"{supplier} specialist lacks project-role or runtime-ownership markers: {', '.join(missing)}",
                    "Reference aim.roles.yaml and explicitly deny specialist ownership of .aim/state.json.",
                    tier="Behavioral",
                    category="Error",
                    release_impact="fail",
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

    if release_mode:
        checked.append("release mode: local .aim runtime workspace is optional")
    else:
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

        if relative_path.endswith((".yaml", ".yml")) and repo_profile_schema:
            profile_source = profile_path.read_text(encoding="utf-8", errors="replace")
            _, contract_issues = parse_and_validate_repo_profile(
                profile_source, repo_profile_schema
            )
            for contract_issue in contract_issues:
                is_product_rule = contract_issue.kind == "product"
                add_issue(
                    issues,
                    "blocked",
                    relative_path,
                    f"repo-profile {'product rule' if is_product_rule else 'schema'} violation at {contract_issue.path}: {contract_issue.message}",
                    "Align the profile with the versioned structural schema and AIM repo-awareness product rules.",
                    tier="Product coherence" if is_product_rule else "Structural",
                    category="Contradiction" if is_product_rule else "Error",
                    release_impact="fail",
                )

    if repo_profile_schema:
        checked.append("installer shared-profile schema seeds")
        for mode in ("personal", "team", "enterprise"):
            _, seed_issues = parse_and_validate_repo_profile(
                installer_seed.shared_profile_seed(mode), repo_profile_schema
            )
            for contract_issue in seed_issues:
                add_issue(
                    issues,
                    "blocked",
                    "scripts/aim_installer/seed.py",
                    f"{mode} bootstrap profile violates the repo-profile contract at {contract_issue.path}: {contract_issue.message}",
                    "Align the installer bootstrap seed with the public repo-profile schema and validator product rules.",
                    tier="Behavioral",
                    category="Contradiction",
                    release_impact="fail",
                )

    if personal_hints_schema:
        checked.append("installer Personal-hints schema seed")
        _, seed_issues = parse_and_validate_personal_hints(
            installer_seed.personal_hints_seed(), personal_hints_schema
        )
        for contract_issue in seed_issues:
            add_issue(
                issues,
                "blocked",
                "scripts/aim_installer/seed.py",
                f"Personal hints bootstrap violates its contract at {contract_issue.path}: {contract_issue.message}",
                "Align the Personal hints seed with its public schema and validator product rules.",
                tier="Behavioral",
                category="Contradiction",
                release_impact="fail",
            )

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

    reflection_doc_path = repo_root / REFLECTION_DOC_PATH
    checked.append(REFLECTION_DOC_PATH)
    if reflection_doc_path.is_file():
        reflection_doc_content = reflection_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_reflection_markers = [
            marker
            for marker in REQUIRED_REFLECTION_DOC_MARKERS
            if marker not in reflection_doc_content
        ]
        if missing_reflection_markers:
            add_issue(
                issues,
                "blocked",
                REFLECTION_DOC_PATH,
                "reflection contract is incomplete: "
                + ", ".join(missing_reflection_markers),
                "Restore safe discovery, temporary reports, provenance, current-evidence verification, classification, operator-ready action conclusions, and approval-controlled promotion.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            REFLECTION_DOC_PATH,
            "canonical reflection contract is missing",
            "Restore docs/workflow/reflection.md before exposing Reflect commands.",
        )

    two_layer_doc_path = repo_root / TWO_LAYER_DOC_PATH
    checked.append(TWO_LAYER_DOC_PATH)
    if two_layer_doc_path.is_file():
        two_layer_content = two_layer_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_two_layer_markers = [
            marker
            for marker in REQUIRED_TWO_LAYER_MARKERS
            if marker not in two_layer_content
        ]
        if missing_two_layer_markers:
            add_issue(
                issues,
                "recoverable",
                TWO_LAYER_DOC_PATH,
                f"two-layer repo-awareness model is incomplete: {', '.join(missing_two_layer_markers)}",
                "Restore the structured profile, operational doc, pointer, and trigger contract.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            TWO_LAYER_DOC_PATH,
            "canonical two-layer repo-awareness model is missing",
            "Restore the two-layer model before relying on operational doc pointers.",
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

    checked.append("AIM 2.0 public product documentation")
    for relative_path, required_markers in PUBLIC_PRODUCT_DOC_PATHS.items():
        product_doc_path = repo_root / relative_path
        checked.append(relative_path)
        if not product_doc_path.is_file():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "required public product document is missing",
                "Restore the public product front door or newcomer journey under docs/product/.",
            )
            continue
        product_content = product_doc_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_product_markers = [
            marker for marker in required_markers if marker not in product_content
        ]
        if missing_product_markers:
            add_issue(
                issues,
                "recoverable",
                relative_path,
                f"public product document is incomplete: {', '.join(missing_product_markers)}",
                "Restore the plain-language product, onboarding, platform, and control story without redefining canonical workflow behavior.",
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
        checked.append("AIM 2.0 installer mode/footprint contract")
        try:
            install_manifest = load_manifest(repo_root)
            expected_defaults = {
                "standard": "adapters",
                "personal": "adapters",
                "team": "adapters",
                "enterprise": "external",
            }
            actual_defaults = {
                mode: str(
                    install_manifest.mode_profile(mode).get("defaultFootprint", "")
                )
                for mode in expected_defaults
            }
            if actual_defaults != expected_defaults:
                add_issue(
                    issues,
                    "blocked",
                    INSTALL_MANIFEST_PATH,
                    f"mode footprint defaults drifted: {actual_defaults}",
                    f"Restore the canonical defaults: {expected_defaults}.",
                )

            canonical_enterprise_ignores = [
                "/.aim",
                "/.aim-local",
                "/aim.local.*",
                "/*.aim.local.md",
                "/*.aim.process.md",
            ]
            enterprise_ignores = [
                str(value)
                for value in install_manifest.mode_profile("enterprise").get(
                    "gitignore", []
                )
            ]
            if enterprise_ignores != canonical_enterprise_ignores:
                add_issue(
                    issues,
                    "blocked",
                    INSTALL_MANIFEST_PATH,
                    "Enterprise installer ignore baseline differs from canonical policy",
                    "Use the exact ordered Enterprise ignore baseline from docs/workflow/operating-modes.md.",
                )

            with tempfile.TemporaryDirectory() as target_dir, tempfile.TemporaryDirectory() as home_dir:
                generated_plans = {}
                for mode, footprint in expected_defaults.items():
                    generated_plans[mode] = installer_planner.compute_plan(
                        source_root=repo_root,
                        target_root=Path(target_dir),
                        mode=mode,
                        footprint=footprint,
                        footprint_explicit=False,
                        adapters=["copilot", "claude", "codex"],
                        manifest=install_manifest,
                        validator_result={
                            "resultClass": "healthy",
                            "exitCode": 0,
                        },
                        home_root=Path(home_dir),
                    )

            enterprise_plan = generated_plans["enterprise"]
            enterprise_destinations = set(
                generated_plans["enterprise"]["scopeSummary"]["repoDestinations"]
            )
            enterprise_local_count = enterprise_plan["scopeSummary"][
                "localActionCount"
            ]
            if enterprise_destinations or enterprise_local_count == 0:
                add_issue(
                    issues,
                    "blocked",
                    "scripts/aim_installer/planner.py",
                    "enterprise default footprint is not a zero-repo-write external install",
                    "Keep Enterprise default to the external footprint: install AIM outside the repository and require explicit broader footprint approval for repo files.",
                )

            team_plan = generated_plans["team"]
            team_destinations = set(
                team_plan["scopeSummary"]["repoDestinations"]
            )
            required_adapter_docs: set[str] = set()
            for adapter in ("claude", "copilot"):
                required_adapter_docs.update(
                    installer_closure.required_workflow_docs(
                        repo_root, adapter, include_optional=True
                    )
                )
            team_adapter_docs = {
                path
                for path in team_destinations
                if path.startswith("docs/workflow/")
            }
            if (
                "aim.profile.yaml" not in team_destinations
                or "aim.roles.yaml" not in team_destinations
                or ".gitignore" not in team_destinations
                or team_adapter_docs != required_adapter_docs
            ):
                add_issue(
                    issues,
                    "blocked",
                    "scripts/aim_installer/planner.py",
                    "Team default footprint does not produce the canonical small shared setup",
                    "Plan the shared profile, runtime ignore, selected adapters, and only their closure contracts.",
                )
            personal_plan = generated_plans["personal"]
            personal_destinations = set(
                personal_plan["scopeSummary"]["repoDestinations"]
            )
            personal_adapter_docs = {
                path
                for path in personal_destinations
                if path.startswith("docs/workflow/")
            }
            if (
                "aim.roles.yaml" not in personal_destinations
                or not any(
                    path.startswith((".github/agents/", ".claude/"))
                    for path in personal_destinations
                )
                or personal_adapter_docs != required_adapter_docs
            ):
                add_issue(
                    issues,
                    "blocked",
                    "scripts/aim_installer/planner.py",
                    "Legacy Personal compatibility plan does not provide native project specialists",
                    "Keep the compatibility plan deterministic while installing the shared role profile and selected native adapters.",
                )

            standard_plan = generated_plans["standard"]
            standard_destinations = set(
                standard_plan["scopeSummary"]["repoDestinations"]
            )
            standard_adapter_docs = {
                path
                for path in standard_destinations
                if path.startswith("docs/workflow/")
            }
            required_native_prefixes = (
                ".codex/agents/",
                ".claude/agents/",
                ".github/agents/",
                ".claude/skills/aim/",
                ".github/skills/aim/",
            )
            if (
                "aim.profile.yaml" not in standard_destinations
                or "aim.roles.yaml" not in standard_destinations
                or ".gitignore" not in standard_destinations
                or standard_adapter_docs != required_adapter_docs
                or any(
                    not any(path.startswith(prefix) for path in standard_destinations)
                    for prefix in required_native_prefixes
                )
            ):
                add_issue(
                    issues,
                    "blocked",
                    "scripts/aim_installer/planner.py",
                    "standard installation does not produce all native project specialists",
                    "Plan the role profile, repo profile, runtime ignore, native Codex/Claude/Copilot agents, and closure contracts.",
                )
        except (ManifestError, installer_planner.PlanError, OSError, KeyError) as exc:
            add_issue(
                issues,
                "blocked",
                INSTALL_MANIFEST_PATH,
                f"installer mode/footprint contract could not be validated: {exc}",
                "Repair the manifest and planner so canonical mode plans can be generated deterministically.",
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

    adapter_entry_model_path = repo_root / ADAPTER_ENTRY_MODEL_DOC_PATH
    checked.append(ADAPTER_ENTRY_MODEL_DOC_PATH)
    if adapter_entry_model_path.is_file():
        adapter_entry_model_content = adapter_entry_model_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_entry_model_markers = [
            marker
            for marker in REQUIRED_ADAPTER_ENTRY_MODEL_MARKERS
            if marker not in adapter_entry_model_content
        ]
        if missing_entry_model_markers:
            add_issue(
                issues,
                "recoverable",
                ADAPTER_ENTRY_MODEL_DOC_PATH,
                f"adapter entry model is missing required markers: {', '.join(missing_entry_model_markers)}",
                "Restore the user-facing/internal/fallback surface classes, the canonical command family, and the per-adapter native front doors.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            ADAPTER_ENTRY_MODEL_DOC_PATH,
            "canonical adapter entry model is missing",
            "Restore docs/workflow/adapter-entry-model.md before relying on native adapter entry guidance.",
        )

    skill_bootstrap_path = repo_root / ADAPTER_SKILL_BOOTSTRAP_DOC_PATH
    checked.append(ADAPTER_SKILL_BOOTSTRAP_DOC_PATH)
    if skill_bootstrap_path.is_file():
        skill_bootstrap_content = skill_bootstrap_path.read_text(
            encoding="utf-8", errors="replace"
        )
        required_skill_markers = [
            "skill-led",
            "~/.agents/skills/agile-iteration-method/SKILL.md",
            ".claude/skills/aim/SKILL.md",
            ".github/skills/aim/SKILL.md",
            "aim.roles.yaml",
            "Readiness receipt",
            "AGENTS.md",
            "CLAUDE.md",
        ] + CANONICAL_AIM_COMMANDS
        missing_skill_markers = [
            marker for marker in required_skill_markers
            if marker not in skill_bootstrap_content
        ]
        if missing_skill_markers:
            add_issue(
                issues,
                "blocked",
                ADAPTER_SKILL_BOOTSTRAP_DOC_PATH,
                "adapter skill bootstrap contract is incomplete: "
                + ", ".join(missing_skill_markers),
                "Restore skill discovery, command parity, project-role delegation, readiness receipts, and root-file independence.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            ADAPTER_SKILL_BOOTSTRAP_DOC_PATH,
            "canonical adapter skill bootstrap contract is missing",
            "Restore the bootstrap contract before relying on adapter skill discovery.",
        )

    command_contract_path = repo_root / ADAPTER_COMMAND_CONTRACT_DOC_PATH
    checked.append(ADAPTER_COMMAND_CONTRACT_DOC_PATH)
    if command_contract_path.is_file():
        command_contract_content = command_contract_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_contract_commands = [
            command
            for command in CANONICAL_AIM_COMMANDS
            if command not in command_contract_content
        ]
        required_upgrade_markers = [
            "deterministic installer planner",
            "stale/collision",
            "--dry-run",
            "--apply",
            "--force",
            "rollback",
            ".aim/state.json",
            "never blind",
        ]
        missing_upgrade_markers = [
            marker
            for marker in required_upgrade_markers
            if marker not in command_contract_content
        ]
        if missing_contract_commands or missing_upgrade_markers:
            missing = missing_contract_commands + missing_upgrade_markers
            add_issue(
                issues,
                "blocked",
                ADAPTER_COMMAND_CONTRACT_DOC_PATH,
                f"canonical adapter command contract is incomplete: {', '.join(missing)}",
                "Restore the full command family and reviewed, collision-safe upgrade contract.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            ADAPTER_COMMAND_CONTRACT_DOC_PATH,
            "canonical adapter command contract is missing",
            "Restore the command intent, state-effect, upgrade, and fallback contract.",
        )

    light_front_door_path = repo_root / LIGHT_FRONT_DOOR_DOC_PATH
    checked.append(LIGHT_FRONT_DOOR_DOC_PATH)
    if light_front_door_path.is_file():
        light_front_door_content = light_front_door_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_onboarding_doc_markers = missing_case_insensitive_markers(
            light_front_door_content, REQUIRED_ONBOARDING_DOC_MARKERS
        )
        if missing_onboarding_doc_markers:
            add_issue(
                issues,
                "blocked",
                LIGHT_FRONT_DOOR_DOC_PATH,
                "canonical onboarding front door is incomplete: "
                + ", ".join(missing_onboarding_doc_markers),
                "Restore state-first guidance, one-next-action behavior, progressive disclosure, and realistic start examples.",
            )
    else:
        add_issue(
            issues,
            "blocked",
            LIGHT_FRONT_DOOR_DOC_PATH,
            "canonical onboarding front door is missing",
            "Restore docs/workflow/light-front-door.md before relying on first-run guidance.",
        )

    if command_contract_path.is_file():
        missing_onboarding_contract_markers = missing_case_insensitive_markers(
            command_contract_content, REQUIRED_ONBOARDING_CONTRACT_MARKERS
        )
        if missing_onboarding_contract_markers:
            add_issue(
                issues,
                "blocked",
                ADAPTER_COMMAND_CONTRACT_DOC_PATH,
                "adapter command contract is missing onboarding semantics: "
                + ", ".join(missing_onboarding_contract_markers),
                "Restore state-first guidance, one-next-action behavior, progressive disclosure, and realistic start examples.",
            )

    checked.append("AIM 2.0 first-run onboarding parity")
    for relative_path, required_markers in ONBOARDING_SURFACES.items():
        onboarding_surface_path = repo_root / relative_path
        checked.append(relative_path)
        if not onboarding_surface_path.is_file():
            add_issue(
                issues,
                "blocked",
                relative_path,
                "onboarding adapter surface is missing",
                "Restore the adapter surface or remove it from the onboarding parity contract.",
            )
            continue
        onboarding_surface_content = onboarding_surface_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_onboarding_surface_markers = missing_case_insensitive_markers(
            onboarding_surface_content, required_markers
        )
        if missing_onboarding_surface_markers:
            add_issue(
                issues,
                "blocked",
                relative_path,
                "adapter onboarding guidance drifted: "
                + ", ".join(missing_onboarding_surface_markers),
                "Restore state detection, a single recommended next action, progressive disclosure, and realistic examples.",
            )

    checked.append("AIM 2.0 adapter command parity")
    for adapter_name, relative_path in COMMAND_FAMILY_SURFACES.items():
        surface_path = repo_root / relative_path
        checked.append(relative_path)
        if not surface_path.is_file():
            continue
        content = surface_path.read_text(encoding="utf-8", errors="replace")
        missing_commands = [
            command for command in CANONICAL_AIM_COMMANDS if command not in content
        ]
        missing_surface_markers = [
            marker
            for marker in (
                (
                    "references/adapter-command-contract.md"
                    if adapter_name == "Codex"
                    else ADAPTER_COMMAND_CONTRACT_DOC_PATH
                ),
                "routing is unavailable",
            )
            if marker not in content
        ]
        if missing_commands or missing_surface_markers:
            missing = missing_commands + missing_surface_markers
            add_issue(
                issues,
                "blocked",
                relative_path,
                f"{adapter_name} command coverage drifted: {', '.join(missing)}",
                "Restore every canonical command intent and the adapter's explicit fallback rule.",
            )

    for command, relative_path in CLAUDE_COMMAND_SURFACES.items():
        command_path = repo_root / relative_path
        checked.append(relative_path)
        if not command_path.is_file():
            add_issue(
                issues,
                "blocked",
                relative_path,
                f"Claude legacy compatibility command is missing for {command}",
                "Restore the compatibility command or remove the supported migration claim.",
            )
            continue
        content = command_path.read_text(encoding="utf-8", errors="replace")
        required_markers = [
            command,
            ADAPTER_COMMAND_CONTRACT_DOC_PATH,
            "routing is unavailable",
        ]
        missing_markers = [
            marker for marker in required_markers if marker not in content
        ]
        if missing_markers:
            add_issue(
                issues,
                "blocked",
                relative_path,
                f"Claude command contract is incomplete: {', '.join(missing_markers)}",
                "Map the native command file to the canonical intent and explicit fallback.",
            )

    copilot_path = repo_root / ".github/agents/aim.agent.md"
    if copilot_path.is_file():
        copilot_content = copilot_path.read_text(encoding="utf-8", errors="replace")
        behavior_sections = re.findall(
            r"^## `(/aim [^`]+)` behavior\s*$\n(.*?)(?=^## |\Z)",
            copilot_content,
            flags=re.MULTILINE | re.DOTALL,
        )
        empty_sections = [
            command
            for command, body in behavior_sections
            if len(body.strip().split()) < 15
        ]
        if empty_sections:
            add_issue(
                issues,
                "blocked",
                ".github/agents/aim.agent.md",
                "Copilot advertised command behavior is empty or non-actionable: "
                + ", ".join(empty_sections),
                "Define actionable behavior or remove the unsupported advertised section.",
            )
        upgrade_body = next(
            (
                body.strip()
                for command, body in behavior_sections
                if command == "/aim upgrade"
            ),
            "",
        )
        required_copilot_upgrade_markers = [
            "dry-run",
            "--apply",
            "--force",
            "rollback",
            ".aim/state.json",
        ]
        missing_copilot_upgrade_markers = [
            marker
            for marker in required_copilot_upgrade_markers
            if marker not in upgrade_body
        ]
        if len(upgrade_body.split()) < 40:
            add_issue(
                issues,
                "blocked",
                ".github/agents/aim.agent.md",
                "Copilot /aim upgrade behavior section is empty or non-actionable",
                "Define inspection, stale detection, reviewed apply, collision safety, rollback, and runtime-state exclusions.",
            )
        elif missing_copilot_upgrade_markers:
            add_issue(
                issues,
                "blocked",
                ".github/agents/aim.agent.md",
                "Copilot /aim upgrade behavior is missing safety markers: "
                + ", ".join(missing_copilot_upgrade_markers),
                "Restore the reviewed installer plan, explicit apply/force, rollback, and runtime-state exclusions.",
            )

    stale_version_pattern = re.compile(
        r"""aimVersion["']?\s*[:=]\s*["']?1\.""",
        flags=re.IGNORECASE,
    )
    adapter_files = sorted(
        {
            *(
                path
                for path in (
                    repo_root / "adapters/codex/agile-iteration-method"
                ).rglob("*")
                if path.is_file()
            ),
            *(
                path
                for path in (repo_root / ".github/agents").glob("aim*.agent.md")
                if path.is_file()
            ),
            *(
                path
                for path in (repo_root / ".github/skills/aim").rglob("*")
                if path.is_file()
            ),
            *(
                path
                for path in (repo_root / ".claude").rglob("*.md")
                if path.is_file()
            ),
        },
        key=lambda path: path.as_posix(),
    )
    for adapter_file in adapter_files:
        if not adapter_file.is_file():
            continue
        content = adapter_file.read_text(encoding="utf-8", errors="replace")
        if stale_version_pattern.search(content):
            relative_path = adapter_file.relative_to(repo_root).as_posix()
            add_issue(
                issues,
                "blocked",
                relative_path,
                "AIM 2.0 adapter surface contains a stale AIM 1.x state example",
                'Use the current AIM 2.0 state example, including "aimVersion": "2.0".',
            )

    checked.append("AIM 2.0 adapter native entry surfaces")
    for relative_path, required_markers in ADAPTER_ENTRY_SURFACE_MARKERS.items():
        entry_surface_path = repo_root / relative_path
        checked.append(relative_path)
        if not entry_surface_path.is_file():
            add_issue(
                issues,
                "recoverable",
                relative_path,
                "adapter native entry surface file is missing",
                "Restore the adapter entry surface or remove the unsupported native-entry claim.",
            )
            continue
        entry_surface_content = entry_surface_path.read_text(
            encoding="utf-8", errors="replace"
        )
        missing_surface_entry_markers = [
            marker for marker in required_markers if marker not in entry_surface_content
        ]
        if missing_surface_entry_markers:
            add_issue(
                issues,
                "recoverable",
                relative_path,
                f"adapter native entry surface is unclear: {', '.join(missing_surface_entry_markers)}",
                "Declare the adapter's skill-led front door or secondary helper role and link docs/workflow/adapter-entry-model.md.",
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

            doc_entries = extract_category_entries(profile_content, "docs")
            memory_doc_prefixes = static_memory_doc_prefixes(profile_content)
            for index, doc_entry in enumerate(doc_entries):
                if doc_entry.get("loading") not in DOCUMENT_LOADING_STATES:
                    add_issue(
                        issues,
                        "recoverable",
                        relative_path,
                        f"docs entry {doc_entry.get('id') or index + 1} has an invalid or missing loading state",
                        "Use authoritative, load_when_relevant, avoid_by_default, or stale_or_uncertain.",
                    )
                if doc_entry.get("kind") == "operational":
                    missing_pointer_fields = [
                        field
                        for field in ("path", "when", "calibration")
                        if not doc_entry.get(field)
                    ]
                    missing_pointer_fields.extend(
                        field
                        for field in (
                            "workTypes",
                            "rolesOrGates",
                            "risks",
                            "commands",
                        )
                        if field not in doc_entry
                    )
                    if doc_entry.get("loading") != "load_when_relevant":
                        missing_pointer_fields.append(
                            "loading: load_when_relevant"
                        )
                    operational_path = doc_entry.get("path", "")
                    if not (
                        is_static_memory_doc_path(
                            operational_path, memory_doc_prefixes
                        )
                        and operational_path.endswith(".md")
                    ):
                        missing_pointer_fields.append(
                            "static memory doc path under docs/workflow/, docs/features/, docs/architecture/, or configured docsSource"
                        )
                    if missing_pointer_fields:
                        add_issue(
                            issues,
                            "recoverable",
                            relative_path,
                            f"operational docs entry {doc_entry.get('id') or index + 1} has an incomplete pointer contract: {', '.join(missing_pointer_fields)}",
                            "Add the static memory doc path, concise relevance rule, load_when_relevant state, and structured work, role/gate, risk, command, and calibration triggers.",
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

            overlong_scalars = find_overlong_profile_scalars(profile_content)
            if overlong_scalars:
                add_issue(
                    issues,
                    "recoverable",
                    relative_path,
                    f"structured profile contains prose-heavy scalar values: {', '.join(overlong_scalars)}",
                    f"Keep profile values under {PROFILE_PROSE_LIMIT} characters and move rich policy into an AIM-owned repo operational doc.",
                )

            for operational_path in operational_doc_paths(profile_content):
                operational_doc = repo_root / operational_path
                checked.append(operational_path)
                if not operational_doc.is_file():
                    add_issue(
                        issues,
                        "blocked",
                        operational_path,
                        "profile points to a missing repo operational document",
                        "Create the static memory or operational doc, or remove the pointer.",
                    )
                    continue
                operational_content = operational_doc.read_text(
                    encoding="utf-8", errors="replace"
                )
                missing_headings = [
                    heading
                    for heading in OPERATIONAL_DOC_REQUIRED_HEADINGS
                    if heading not in operational_content
                ]
                if missing_headings:
                    add_issue(
                        issues,
                        "recoverable",
                        operational_path,
                        f"repo operational doc is missing required sections: {', '.join(missing_headings)}",
                        "Keep operational docs practical with applicability, procedure, evidence, blockers, edge cases, debugging, and related surfaces.",
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

    checked.append("AIM 2.0 product coherence")
    coherence_findings, coherence_evidence = evaluate_product_coherence(repo_root)
    issues.extend(coherence_findings)

    result = summarize_result(issues)
    readiness = release_readiness(issues)
    validation_tiers = tier_statuses(issues)
    next_action = {
        "healthy": "Continue or resume the AIM loop normally.",
        "recoverable": "Repair the listed runtime gaps, then re-run the validator before resuming.",
        "blocked": "Restore the required repo/runtime files before continuing the AIM loop.",
        "contradictory": "Stop and reconcile the reported product or runtime contradictions before continuing.",
    }[result]

    print(f"Result: {result}")
    print(f"Release readiness: {readiness}")
    print("Validation tiers:")
    for tier, status in validation_tiers.items():
        print(f"- {tier}: {status}")
    print("Behavioral evidence:")
    for evidence in coherence_evidence:
        print(f"- {evidence}")
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

    print("AIM 2.0 installation policy model:")
    print(f"- canonical doc: {OPERATING_MODE_DOC_PATH}")
    print(
        f"- configured policy: {configured_operating_mode if configured_operating_mode else 'not declared'}"
    )
    print(f"- policy source: {operating_mode_source}")
    if configured_operating_mode == "Enterprise":
        print(f"- Enterprise ignore baseline: {', '.join(ENTERPRISE_IGNORE_MARKERS)}")

    print("AIM 2.0 documentation model:")
    print(f"- canonical doc: {DOCUMENTATION_MODEL_DOC_PATH}")
    print("- core truth: docs/workflow/agile-iteration-method.md")
    print("- public product surface: README.md and docs/product/")
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

    print("AIM 2.0 adapter entry model:")
    print(f"- canonical doc: {ADAPTER_ENTRY_MODEL_DOC_PATH}")
    print(f"- command contract: {ADAPTER_COMMAND_CONTRACT_DOC_PATH}")
    print(f"- canonical command intents: {len(CANONICAL_AIM_COMMANDS)}")
    print(f"- skill bootstrap: {ADAPTER_SKILL_BOOTSTRAP_DOC_PATH}")
    print("- Codex: user skill plus native project agents")
    print("- GitHub Copilot: project skill plus native custom agents")
    print("- Claude: project skill plus native subagents and legacy commands")
    for relative_path in ADAPTER_ENTRY_SURFACE_MARKERS:
        entry_surface_present = (repo_root / relative_path).is_file()
        print(
            f"- entry surface {relative_path}: {'present' if entry_surface_present else 'missing'}"
        )

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

    print("AIM 2.0 repo-profile schema contract:")
    print(f"- repo profile schema: {REPO_PROFILE_SCHEMA_PATH}")
    print(f"- supported profileVersion: {SUPPORTED_PROFILE_VERSION}")
    print(f"- Personal hints schema: {PERSONAL_HINTS_SCHEMA_PATH}")
    print(f"- supported hintsVersion: {SUPPORTED_HINTS_VERSION}")
    print("- authority: schema=structure, validator=product rules, docs=meaning")

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

    categorized = findings_by_category(issues)
    for category, heading in (
        ("Error", "Errors"),
        ("Warning", "Warnings"),
        ("Contradiction", "Contradictions"),
    ):
        print(f"{heading}:")
        category_findings = categorized[category]
        if not category_findings:
            print("- none")
            continue
        for issue in category_findings:
            print(
                f"- [{issue['tier']}] {issue['artifact']}: {issue['rule']}"
            )
            if issue["evidence"]:
                print(f"  Evidence: {issue['evidence']}")

    print("Recommendations:")
    if issues:
        seen_recommendations: set[str] = set()
        for issue in issues:
            recommendation = str(issue["action"])
            if recommendation in seen_recommendations:
                continue
            seen_recommendations.add(recommendation)
            print(f"- {recommendation}")
    else:
        print("- none")

    print(f"Best next action: {next_action}")
    return EXIT_CODES[result]


if __name__ == "__main__":
    raise SystemExit(main())
