"""Generate the content AIM writes for bootstrap/ignore destinations.

Centralized so the planner (classification / idempotence) and the apply step
agree on exactly what AIM would write.
"""

from __future__ import annotations

from pathlib import Path


SHARED_PROFILE_SEED = """\
aimProfile:
  schema: "1"
  status: needs_calibration
  confidence: low
  calibrated: false
  calibrationCommand: /aim calibrate-repo
  note: >-
    Seeded by aim_install.py. This is a bootstrap profile and is NOT calibrated.
    Run /aim calibrate-repo before relying on repo-awareness.
  knowledge:
    technologies: []
    commands: []
    validation: []
    uiTesting: []
    docs: []
"""


def shared_profile_seed() -> str:
    """Return the bootstrap shared profile content (never claims 'ready')."""

    return SHARED_PROFILE_SEED


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
