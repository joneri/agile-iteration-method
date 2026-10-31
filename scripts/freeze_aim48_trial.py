#!/usr/bin/env python3
"""Capture cutoff source/evidence without trusting an author's completion flag.

This is an ordinary filesystem copy, not an atomic filesystem snapshot. Changed
files during capture are reported and cannot silently become valid evidence.
It never launches agents, edits candidates, or decides a score.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

OMIT = {".git", "method", "build", ".build", "module-cache", "node_modules", "__pycache__"}


def capture(workspace, destination, *, deadline=None):
    workspace, destination = Path(workspace).resolve(), Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(workspace):
        raise ValueError("Use a fresh capture outside the candidate workspace.")
    if deadline is not None:
        while time.time() < deadline:
            time.sleep(min(1, max(0, deadline - time.time())))
    started = time.time()
    destination.mkdir(parents=True)
    manifest = {"captureStartedAt": datetime.datetime.fromtimestamp(started, datetime.timezone.utc).isoformat(),
                "deadlineUnix": deadline, "files": {}, "changedDuringCapture": [], "skipped": [],
                "limitation": "Non-atomic readonly filesystem capture; neither product acceptance nor GUI proof."}
    for folder, dirs, names in os.walk(workspace, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in OMIT)
        for name in sorted(names):
            source = Path(folder) / name
            relative = source.relative_to(workspace).as_posix()
            if source.is_symlink():
                manifest["skipped"].append({"path": relative, "reason": "symlink"})
                continue
            before = source.stat()
            if before.st_size > 50_000_000 or source.suffix == ".pyc":
                manifest["skipped"].append({"path": relative, "reason": "oversize or cache"})
                continue
            data = source.read_bytes()
            after = source.stat()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            shutil.copymode(source, target)
            changed = (before.st_mtime_ns, before.st_size, before.st_ino) != (after.st_mtime_ns, after.st_size, after.st_ino)
            if changed:
                manifest["changedDuringCapture"].append(relative)
            manifest["files"][relative] = {"sha256": hashlib.sha256(data).hexdigest(),
                                           "bytes": len(data), "mtimeUnix": before.st_mtime,
                                           "modifiedAfterDeadline": deadline is not None and before.st_mtime > deadline}
    manifest["captureFinishedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest["lateModifiedPaths"] = [p for p,v in manifest["files"].items() if v["modifiedAfterDeadline"]]
    (destination / "cutoff-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--deadline", help="UTC ISO datetime; immediate when absent")
    args = p.parse_args()
    deadline = datetime.datetime.fromisoformat(args.deadline).timestamp() if args.deadline else None
    result = capture(args.workspace, args.destination, deadline=deadline)
    print(json.dumps({"captureStartedAt": result["captureStartedAt"], "files": len(result["files"]),
                      "changedDuringCapture": result["changedDuringCapture"], "lateModifiedPaths": result["lateModifiedPaths"]}))


if __name__ == "__main__":
    main()
