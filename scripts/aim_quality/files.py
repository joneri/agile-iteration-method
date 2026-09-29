"""Bounded local evidence reads without command execution or symlink traversal."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

MAX_BYTES = 1_000_000


def _read_regular(stream, maximum: int, expected=None) -> bytes:
    metadata = os.fstat(stream.fileno())
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("evidence must be a bounded regular file")
    if expected is not None and (metadata.st_dev, metadata.st_ino) != (expected.st_dev, expected.st_ino):
        raise ValueError("evidence identity changed while opening")
    if metadata.st_size > maximum:
        raise ValueError("evidence exceeds the size limit")
    content = stream.read(metadata.st_size + 1)
    if len(content) != metadata.st_size:
        raise ValueError("evidence changed size while reading")
    return content


def _portable_read(root: Path, path: Path, maximum: int) -> bytes:
    """Identity-checked fallback where directory-relative open is unavailable.

    Check reparse points as well as symbolic links. The opened file must match
    the inspected identity; recheck ancestors before returning any bytes.
    """
    current = root.resolve()
    snapshots = []
    for component in path.parts:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 1024:
            raise ValueError("evidence traverses a link or reparse point")
        snapshots.append((current, metadata))
    if not stat.S_ISREG(snapshots[-1][1].st_mode):
        raise ValueError("evidence must be a bounded regular file")
    descriptor = os.open(current, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        content = _read_regular(stream, maximum, snapshots[-1][1])
    for component, before in snapshots:
        after = component.lstat()
        if (after.st_dev, after.st_ino, after.st_mode) != (before.st_dev, before.st_ino, before.st_mode):
            raise ValueError("evidence path changed while reading")
    return content


def read_evidence(root: Path, relative: str, maximum: int = MAX_BYTES) -> bytes:
    """Read a contained regular file, rejecting symlinks in every component.

    Directory descriptors prevent a concurrently replaced parent from redirecting
    a read outside the selected root. Nonblocking open also rejects FIFOs safely.
    """
    path = Path(relative)
    if not relative or path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("evidence path must be relative and contained")
    if os.open not in os.supports_dir_fd:
        return _portable_read(root, path, maximum)
    descriptor = os.open(root.resolve(), os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                  dir_fd=descriptor)
        with os.fdopen(file_descriptor, "rb") as stream:
            return _read_regular(stream, maximum)
    finally:
        os.close(descriptor)


def fingerprint(root: Path, relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": hashlib.sha256(read_evidence(root, relative)).hexdigest()}
