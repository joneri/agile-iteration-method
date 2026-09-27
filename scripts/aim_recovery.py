#!/usr/bin/env python3
"""Rebuild a missing workspace index from intact runtime facts.

No checkpoint, approval, plan, or history is rewritten. Discovery is bounded to
the root workspace and immediate children of the two supported workspace roots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

MAX_WORKSPACES = 500


def discover_catalog(aim_root: Path):
    from aim_start import (AimStartError, _read_bytes, _read_state,
                           _validate_declared_state, _allocated_increment_ids,
                           MAX_STATE_BYTES)
    from aim_runtime_contract import _runtime_state_schema, _schema_issues

    if aim_root.is_symlink():
        raise AimStartError("The AIM workspace location is a symbolic link.")
    candidates = [aim_root]
    for name in ("portfolio", "workspaces"):
        parent = aim_root / name
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise AimStartError("The saved workspace locations cannot be resolved safely.")
        if parent.is_dir():
            children = sorted(parent.iterdir())
            if len(children) > MAX_WORKSPACES:
                raise AimStartError("Too many saved workspaces to recover in one bounded operation.")
            candidates.extend(children)
    declared, bindings = [], {}
    epics, increments = set(), set()
    schema = _runtime_state_schema(aim_root.parent)
    for workspace in candidates:
        if workspace.is_symlink() or (workspace.exists() and not workspace.is_dir()):
            raise AimStartError("A saved workspace location cannot be resolved safely.")
        if not workspace.exists():
            continue
        raw = workspace.relative_to(aim_root).as_posix()
        state_path = workspace / "state.json"
        evidence = any((workspace / name).exists() or (workspace / name).is_symlink()
                       for name in ("state.json", "epic.md"))
        for name in ("increments", "decisions", "reviews"):
            directory = workspace / name
            if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
                raise AimStartError("Saved work contains an unsafe artifact location.")
            evidence = evidence or (directory.is_dir() and any(directory.iterdir()))
        if not evidence:
            continue
        state = _read_state(workspace)
        if state is None:
            raise AimStartError("Saved work has no readable checkpoint; its current task is uncertain.")
        _validate_declared_state(raw, state)
        issues = _schema_issues(state, schema)
        if issues:
            raise AimStartError("Saved work has an uncertain checkpoint: " + "; ".join(issues))
        epic = _read_bytes(workspace / "epic.md", maximum=MAX_STATE_BYTES, label="Saved Epic")
        if state["epicId"] not in epic.decode("utf-8"):
            raise AimStartError("The saved task and its Epic description disagree.")
        allocated = _allocated_increment_ids(workspace, state)
        if state["epicId"] in epics or allocated.intersection(increments):
            raise AimStartError("More than one saved workspace claims the same work.")
        epics.add(state["epicId"])
        increments.update(allocated)
        declared.append((raw, workspace))
        bindings[raw] = {
            "state": hashlib.sha256(state_path.read_bytes()).hexdigest(),
            "epic": hashlib.sha256(epic).hexdigest(),
            "increments": sorted(allocated),
        }
    catalog = {"portfolioVersion": "1.0", "workspaces": [{"path": raw} for raw, _ in declared]}
    return catalog, declared, bindings


def ensure_catalog(repo: Path):
    """One automatic attempt; preserve an index that already exists."""
    from aim_start import AimStartError, _inside_aim, _catalog, _json_bytes
    _, aim = _inside_aim(repo)
    target = aim / "ui-portfolio.json"
    if target.exists() or target.is_symlink():
        _catalog(aim)
        return {"result": "unchanged"}
    catalog, declared, bindings = discover_catalog(aim)
    if not declared:
        return {"result": "uninitialized"}
    fd, name = tempfile.mkstemp(prefix=".catalog-recovery-", dir=aim)
    staged = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(catalog))
            stream.flush()
            os.fsync(stream.fileno())
        # Re-read immediately before publication, including discovery membership.
        fresh_catalog, _, fresh_bindings = discover_catalog(aim)
        if (fresh_catalog, fresh_bindings) != (catalog, bindings):
            raise AimStartError("Saved work changed during recovery; refresh once before continuing.")
        # Atomic no-clobber publication. A concurrent catalog always wins.
        os.link(staged, target)
    finally:
        staged.unlink()
    return {"result": "recovered", "workspaceCount": len(declared)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    from aim_start import AimStartError
    try:
        print(json.dumps(ensure_catalog(Path(args.repo))))
        return 0
    except (AimStartError, OSError, ValueError) as exc:
        print(json.dumps({"result": "needs_attention", "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
