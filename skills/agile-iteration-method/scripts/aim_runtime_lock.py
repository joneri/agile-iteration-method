# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_runtime_lock.py
"""One process lock per authoritative workspace; never remove the lock inode."""

from contextlib import contextmanager
from functools import wraps
import os
from pathlib import Path
import stat


@contextmanager
def runtime_lock(state_path: Path):
    path = state_path.with_name(".runtime.lock")
    if path.is_symlink():
        raise ValueError("Runtime lock must not be a symbolic link.")
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "r+b") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("Runtime lock must be a regular file.")
        if os.name == "nt":
            import msvcrt
            if not os.fstat(handle.fileno()).st_size:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def serialized_transition(function):
    @wraps(function)
    def wrapped(repo_root, *, authority_state_path, **kwargs):
        from aim_runtime_contract import _authority_state_path
        with runtime_lock(_authority_state_path(repo_root, authority_state_path)):
            return function(repo_root, authority_state_path=authority_state_path, **kwargs)
    return wrapped
