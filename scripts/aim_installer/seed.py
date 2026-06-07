"""Generate the content AIM writes for bootstrap/ignore destinations.

Centralized so the planner (classification / idempotence) and the apply step
agree on exactly what AIM would write.
"""

from __future__ import annotations

from pathlib import Path


def shared_profile_seed(mode: str = "team") -> str:
    """Return the bootstrap shared profile content.

    Matches the canonical `aimRepoProfile` repo-awareness model (see
    `aim.profile.yaml` and `docs/workflow/repo-awareness.md`) but is explicitly
    uncalibrated: `calibration.status: needs_calibration`, `confidence: low`, and
    empty `repoKnowledge` categories. It never claims `ready`.
    """

    sharing = "local" if mode == "personal" else "committed"
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
    docsSource: docs/workflow/
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
