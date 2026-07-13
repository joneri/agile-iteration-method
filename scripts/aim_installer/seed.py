"""Generate the content AIM writes for bootstrap/ignore destinations.

Centralized so the planner (classification / idempotence) and the apply step
agree on exactly what AIM would write.
"""

from __future__ import annotations

import json
from pathlib import Path


def shared_profile_seed(mode: str = "standard") -> str:
    """Return the bootstrap shared profile content.

    Matches the canonical `aimRepoProfile` repo-awareness model (see
    `aim.profile.yaml` and `docs/workflow/repo-awareness.md`) but is explicitly
    uncalibrated: `calibration.status: needs_calibration`, `confidence: low`, and
    empty `repoKnowledge` categories. It never claims `ready`.
    """

    sharing = "committed"
    return f"""\
aimRepoProfile:
  profileVersion: "0.2"
  calibration:
    status: needs_calibration
    source: installer-bootstrap
    confidence: low
    openUncertainties:
      - Repository knowledge has not been calibrated yet.
  repoIdentity:
    name: to-be-calibrated
    defaultBranch: to-be-calibrated
  adoption:
    mode: {mode}
    footprint: tiny
    sharing: {sharing}
    profileOwner: repository-maintainers
  storage:
    profileLocation: aim.profile.yaml
    personalHintsLocation: ~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
    workingStateLocation: .aim/
    docsSource: docs/workflow/, docs/features/, docs/architecture/, or repo-configured equivalent
  repoKnowledge:
    technologies: []
    commands: []
    validation: []
    uiTesting: []
    docs: []
    localities: []
    riskZones: []
    habits: []
    avoidByDefault: []
    freshness: []
  note: >-
    Seeded by aim_install.py. This is a bootstrap profile and is NOT calibrated.
    Run /aim calibrate-repo before relying on repo-awareness.
"""


def _package_json_facts(target_root: Path) -> tuple[list[str], list[str]]:
    path = target_root / "package.json"
    if not path.is_file():
        return [], []
    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["JavaScript or TypeScript (package.json detected)"], []

    dependencies: dict[str, object] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            dependencies.update(value)
    scripts = package.get("scripts", {})
    scripts = scripts if isinstance(scripts, dict) else {}

    technologies = ["JavaScript or TypeScript"]
    known = {
        "react": "React",
        "next": "Next.js",
        "vue": "Vue",
        "svelte": "Svelte",
        "@playwright/test": "Playwright",
        "vitest": "Vitest",
        "jest": "Jest",
    }
    for dependency, label in known.items():
        if dependency in dependencies:
            technologies.append(label)

    commands = []
    for script in ("build", "test", "lint", "typecheck"):
        if script in scripts:
            commands.append(f"npm run {script}")
    if "@playwright/test" in dependencies and not any("playwright" in c for c in commands):
        commands.append("npx playwright test")
    return technologies, commands


def project_roles_seed(target_root: Path) -> str:
    """Return a conservative project-role profile from cheap repository evidence.

    Detection only records directly observable technologies and commands. The
    first AIM calibration is responsible for verifying and enriching the role
    profile; the installer never claims that an inferred profile is complete.
    """

    technologies, commands = _package_json_facts(target_root)
    if (target_root / "pyproject.toml").is_file():
        technologies.append("Python")
    if (target_root / "Package.swift").is_file():
        technologies.append("Swift Package Manager")
    if (target_root / "Cargo.toml").is_file():
        technologies.append("Rust")
    if (target_root / "go.mod").is_file():
        technologies.append("Go")
    if not technologies:
        technologies.append("To be verified during /aim calibrate-repo")
    if not commands:
        commands.append("Use aim.profile.yaml after calibration")

    project_technology_lines = "\n".join(
        f"      - {item}" for item in dict.fromkeys(technologies)
    )
    project_command_lines = "\n".join(
        f"      - {item}" for item in dict.fromkeys(commands)
    )
    role_technology_lines = "\n".join(
        f"        - {item}" for item in dict.fromkeys(technologies)
    )
    role_command_lines = "\n".join(
        f"        - {item}" for item in dict.fromkeys(commands)
    )
    return f"""\
aimProjectRoles:
  profileVersion: "0.1"
  status: needs_calibration
  source: installer-detection
  project:
    name: {target_root.name}
    technologies:
{project_technology_lines}
    validation:
{project_command_lines}
  orchestration:
    mainThreadOwnsRuntime: true
    parallelPolicy: explicit-or-adapter-policy
    maxDelegationDepth: 1
    modelPolicy: inherit-supplier-default
  roles:
    po:
      mission: Own user value, Epic intent, acceptance, and continuation decisions.
      expertise:
        - Product outcomes and repository-specific user context
      writeScope: AIM Epic and acceptance decisions only
    tdo:
      mission: Turn the Epic into one coherent end-to-end Done Increment and validate delivery.
      expertise:
        - Architecture, delivery planning, risk, and project validation strategy
      writeScope: AIM increment plans, synthesis, and decision records only
    dev:
      mission: Implement exactly the approved Done Increment with project-native practices.
      expertise:
{role_technology_lines}
      writeScope: Approved implementation files and Dev trace artifacts
    reviewer:
      mission: Independently verify correctness, risk, regression coverage, and acceptance evidence.
      expertise:
{role_technology_lines}
      validation:
{role_command_lines}
      writeScope: Review evidence only; read-only product inspection by default
  customization:
    editable: true
    updateIntent: /aim configure-agents
    refreshAfter: dependency, framework, test-tool, architecture, or policy changes
"""


def personal_hints_seed(repo_fingerprint: str = "to-be-calibrated") -> str:
    """Return an empty Personal hints document matching the public schema."""

    return f"""\
aimPersonalHints:
  hintsVersion: "0.1"
  repoFingerprint: {repo_fingerprint}
  profileOwner: local-user
  hints:
    commands: []
    localities: []
    docs: []
    habits: []
    avoidByDefault: []
    freshness: []
"""



def gitignore_with_fragments(existing: str | None, fragments: list[str]) -> str:
    """Return .gitignore content with all fragments present (idempotent)."""

    lines = existing.splitlines() if existing else []
    present = {line.strip() for line in lines}
    missing = [f for f in fragments if f not in present]
    if not missing:
        return existing if existing is not None else ""
    block = list(lines)
    if block and block[-1].strip() != "":
        block.append("")
    block.append("# AIM runtime state")
    block.extend(missing)
    return "\n".join(block) + "\n"


def read_text_or_none(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
