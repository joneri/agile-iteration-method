"""Reviewed apply step with rollback/recovery and idempotent re-runs.

Consumes the plan produced by :mod:`planner`. By default it refuses to overwrite
collisions (reviewed apply, no silent scope broadening); ``--force`` overwrites
after backing up. Any failure mid-apply triggers a full rollback so the target
repository is restored to its pre-apply state.
"""

from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path
from typing import Any

from . import seed
from .manifest import Manifest
from .paths import checked_destination


class ApplyRefused(Exception):
    """Raised when apply cannot proceed without explicit user action."""


class ApplyFailed(Exception):
    """Raised after a mid-apply failure has been rolled back."""


class _Journal:
    """Rollback via pinned parents; random exclusive backups never touch user files."""

    def __init__(self) -> None:
        self.operations = []
        self.directories = []

    def finish(self, rollback: bool = False) -> None:
        errors = []
        for parent, name, backup in reversed(self.operations):
            try:
                if rollback:
                    if backup is None:
                        _unlink(parent, name)
                    else:
                        _replace(parent, backup, name)
                elif backup is not None:
                    _unlink(parent, backup)
            except OSError as exc:
                errors.append(str(exc))
            finally:
                if isinstance(parent, int):
                    os.close(parent)
        for parent, name in reversed(self.directories):
            try:
                if rollback:
                    if isinstance(parent, int):
                        os.rmdir(name, dir_fd=parent)
                    else:
                        (parent / name).rmdir()
            except OSError:
                pass  # Never remove nonempty directories or broaden recovery.
            finally:
                if isinstance(parent, int):
                    os.close(parent)
        if errors:
            raise ApplyFailed("install recovery needs attention; backups retained: " + "; ".join(errors))

    def rollback(self) -> None:
        self.finish(rollback=True)

    def cleanup_backups(self) -> None:
        self.finish()


def _unlink(parent, name):
    if isinstance(parent, int):
        os.unlink(name, dir_fd=parent)
    else:
        (parent / name).unlink()


def _replace(parent, source, destination):
    if isinstance(parent, int):
        os.replace(source, destination, src_dir_fd=parent, dst_dir_fd=parent)
    else:
        os.replace(parent / source, parent / destination)


def _parent_handle(root: Path, dest: Path, journal: _Journal):
    root = root.absolute().parent.resolve() / root.name
    relative = dest.relative_to(root)
    if not root.exists():
        missing = []
        current = root
        while not current.exists():
            missing.append(current)
            current = current.parent
        for directory in reversed(missing):
            directory.mkdir()
            journal.directories.append((directory.parent, directory.name))
    checked_destination(root, dest)
    if os.open not in os.supports_dir_fd:
        # Portable path checks reject static links/reparse points. They do not
        # provide the POSIX descriptor guarantee against concurrent parent moves.
        missing = []
        parent = dest.parent
        while not parent.exists():
            missing.append(parent)
            parent = parent.parent
        for directory in reversed(missing):
            directory.mkdir()
            journal.directories.append((directory.parent, directory.name))
        checked_destination(root, dest)
        return dest.parent
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    current = root
    try:
        for component in relative.parts[:-1]:
            current = current / component
            try:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                os.mkdir(component, dir_fd=fd)
                journal.directories.append((os.dup(fd), component))
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _temporary(parent, data: bytes, mode: int):
    # O_EXCL reserves an unpredictable sibling without clobbering user backups.
    name = ".aim-install-" + secrets.token_hex(16)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = (os.open(name, flags, mode, dir_fd=parent) if isinstance(parent, int)
          else os.open(parent / name, flags, mode))
    try:
        with os.fdopen(fd, "wb") as stream:
            if hasattr(os, "fchmod"):
                os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        _unlink(parent, name)
        raise
    return name


def _write_file(dest: Path, data: bytes, journal: _Journal, root: Path) -> None:
    dest = checked_destination(root, dest)
    parent = _parent_handle(root, dest, journal)
    backup = temporary = None
    owned = False
    try:
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            fd = (os.open(dest.name, flags, dir_fd=parent) if isinstance(parent, int)
                  else os.open(dest, flags))
        except FileNotFoundError:
            original = None
            mode = 0o644
        else:
            with os.fdopen(fd, "rb") as stream:
                metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(metadata.st_mode):
                    raise ApplyRefused("install destination must be a regular file")
                original = stream.read()
                mode = stat.S_IMODE(metadata.st_mode)
        if original is not None:
            backup = _temporary(parent, original, mode)
        temporary = _temporary(parent, data, mode)
        _replace(parent, temporary, dest.name)
        temporary = None
        journal.operations.append((parent, dest.name, backup))
        owned = True
    finally:
        if not owned:
            for name in (temporary, backup):
                if name is not None:
                    _unlink(parent, name)
            if isinstance(parent, int):
                os.close(parent)


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
        if "content" in action:
            return str(action["content"]).encode("utf-8")
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

    # Recheck the entire reviewed plan before any write; force never bypasses
    # destination containment or permits a home action outside the chosen home.
    for action in plan["actions"]:
        root = Path(plan.get("home", str(Path.home()))) if action.get("scope") == "home" else target_root
        destination = Path(action["destination"]) if action.get("scope") == "home" else root / action["destination"]
        try:
            checked_destination(root, destination)
        except ValueError as exc:
            raise ApplyRefused(str(exc)) from exc

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
            root = Path(plan.get("home", str(Path.home()))) if action.get("scope") == "home" else target_root
            _write_file(dest, data, journal, root)
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
