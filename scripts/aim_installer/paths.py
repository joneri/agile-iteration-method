"""Destination boundaries shared by install preview and apply."""
from __future__ import annotations

import os
import stat
from pathlib import Path


class UnsafeDestination(ValueError):
    """An installation path cannot be safely inspected or written."""


def checked_destination(root: Path, destination: Path) -> Path:
    """Reject traversal, links, reparse points and nonregular destinations.

    The caller resolves the selected root before planning. Neither that root
    nor its children may redirect the installation. Apply additionally anchors writes with open
    directory descriptors on platforms supporting directory-relative operations.
    """
    root = root.absolute()
    destination = destination.absolute()
    try:
        relative = destination.relative_to(root)
    except ValueError as exc:
        raise UnsafeDestination(f"destination is outside selected root: {destination}") from exc
    if not relative.parts or '..' in relative.parts:
        raise UnsafeDestination(f"invalid install destination: {destination}")
    # Resolve system aliases above the selected root, but never follow a link
    # replacing the selected root itself between preview and apply.
    canonical_root = root.parent.resolve() / root.name
    try:
        metadata = canonical_root.lstat()
    except FileNotFoundError:
        pass  # A new fake home/root may be created by the existing installer flow.
    else:
        if not stat.S_ISDIR(metadata.st_mode) or getattr(metadata, 'st_file_attributes', 0) & 1024:
            raise UnsafeDestination(f"selected install root is not a regular directory: {root}")
    current = canonical_root
    for index, component in enumerate(relative.parts):
        current = current / component
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, 'st_file_attributes', 0) & 1024:
            raise UnsafeDestination(f"install destination traverses a link or reparse point: {current}")
        expected = stat.S_ISREG if index == len(relative.parts)-1 else stat.S_ISDIR
        if not expected(metadata.st_mode):
            raise UnsafeDestination(f"install destination has an unsupported file type: {current}")
    return canonical_root / relative
