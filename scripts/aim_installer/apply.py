"""Reviewed apply step with rollback/recovery and idempotent re-runs.

Consumes the plan produced by :mod:`planner`. By default it refuses to overwrite
collisions (reviewed apply, no silent scope broadening); ``--force`` overwrites
after backing up. Any failure mid-apply triggers a full rollback so the target
repository is restored to its pre-apply state.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from . import seed
from .manifest import Manifest


class ApplyRefused(Exception):
    """Raised when apply cannot proceed without explicit user action."""


class ApplyFailed(Exception):
    """Raised after a mid-apply failure has been rolled back."""


class _Journal:
    """Records reversible operations so a failed apply can be undone."""

    def __init__(self) -> None:
        self._created_files: list[Path] = []
        self._created_dirs: list[Path] = []
        self._backups: list[tuple[Path, Path]] = []  # (original, backup)

    def record_created_dir(self, path: Path) -> None:
        self._created_dirs.append(path)

    def record_created_file(self, path: Path) -> None:
        self._created_files.append(path)

    def record_backup(self, original: Path, backup: Path) -> None:
        self._backups.append((original, backup))

    def rollback(self) -> None:
        for path in reversed(self._created_files):
            if path.exists():
                path.unlink()
        for original, backup in reversed(self._backups):
            shutil.copy2(backup, original)
            backup.unlink()
        for path in reversed(self._created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass  # not empty; leave it

    def cleanup_backups(self) -> None:
        for _original, backup in self._backups:
            if backup.exists():
                backup.unlink()


def _ensure_parents(path: Path, journal: _Journal) -> None:
    missing: list[Path] = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir()
        journal.record_created_dir(directory)


def _backup_path(original: Path) -> Path:
    return original.with_name(original.name + ".aim-backup")


def _write_file(dest: Path, data: bytes, journal: _Journal) -> None:
    existed = dest.exists()
    if existed:
        backup = _backup_path(dest)
        shutil.copy2(dest, backup)
        journal.record_backup(dest, backup)
    else:
        _ensure_parents(dest, journal)
    dest.write_bytes(data)
    if not existed:
        journal.record_created_file(dest)


def _desired_bytes(
    action: dict[str, Any],
    source_root: Path,
    target_root: Path,
    manifest: Manifest,
    fragments: list[str],
    mode: str,
) -> bytes:
    category = action["category"]
    if category in ("file", "package"):
        return (source_root / action["source"]).read_bytes()
    if category == "bootstrap":
        return seed.shared_profile_seed(mode).encode("utf-8")
    if category == "ignore":
        existing = seed.read_text_or_none(target_root / ".gitignore")
        return seed.gitignore_with_fragments(existing, fragments).encode("utf-8")
    raise ApplyFailed(f"unknown action category: {category}")


def apply_plan(
    *,
    plan: dict[str, Any],
    source_root: Path,
    target_root: Path,
    manifest: Manifest,
    force: bool,
    collision_decisions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Apply the plan to the target repo with rollback on failure."""

    if plan.get("blockers"):
        raise ApplyRefused(
            "plan has blockers; resolve them before applying: "
            + "; ".join(plan["blockers"])
        )

    collisions = [a for a in plan["actions"] if a["classification"] == "collision"]
    collision_decisions = collision_decisions or {}
    if collisions and not force:
        missing = [
            a["destination"]
            for a in collisions
            if collision_decisions.get(a["destination"]) not in ("keep", "overwrite")
        ]
        if missing:
            raise ApplyRefused(
                "collisions require explicit keep/overwrite decisions: "
                + ", ".join(missing)
            )

    journal = _Journal()
    applied: list[dict[str, str]] = []
    mode = str(plan.get("mode", "team"))
    fragments = plan.get("gitignoreFragments") or (
        manifest.gitignore_fragments or manifest.runtime_exclusions
    )
    try:
        for action in plan["actions"]:
            if action["classification"] == "untouched":
                applied.append({"destination": action["destination"], "result": "untouched"})
                continue
            if (
                action["classification"] == "collision"
                and not force
                and collision_decisions[action["destination"]] == "keep"
            ):
                applied.append({"destination": action["destination"], "result": "kept"})
                continue
            if action.get("scope") == "home":
                dest = Path(action["destination"])
            else:
                dest = target_root / action["destination"]
            data = _desired_bytes(action, source_root, target_root, manifest, fragments, mode)
            _write_file(dest, data, journal)
            applied.append(
                {
                    "destination": action["destination"],
                    "result": action["classification"],
                }
            )
    except Exception as exc:  # noqa: BLE001 - rollback then re-raise as ApplyFailed
        journal.rollback()
        raise ApplyFailed(f"apply failed and was rolled back: {exc}") from exc

    journal.cleanup_backups()
    return {
        "operation": "apply",
        "applied": applied,
        "writtenCount": sum(
            1 for a in applied if a["result"] not in ("untouched", "kept")
        ),
        "untouchedCount": sum(
            1 for a in applied if a["result"] in ("untouched", "kept")
        ),
        "keptCount": sum(1 for a in applied if a["result"] == "kept"),
    }
