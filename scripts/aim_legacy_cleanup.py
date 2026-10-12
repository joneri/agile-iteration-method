#!/usr/bin/env python3
"""Preview and explicitly apply bounded legacy cleanup without archiving.

Only the caller can supply deletion authorization. Preview never writes. Apply
recomputes the inventory under runtime locks and reports partial deletion rather
than pretending that a multi-file cleanup is an atomic transaction.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from aim_quality.files import read_evidence
from aim_runtime_lock import runtime_lock
from aim_stories import FILE as PRODUCT_FILE, load as load_product

MAX_ENTRIES = 20_000
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_CATALOG_BYTES = 1_000_000
MAX_REFERENCE_JSON_BYTES = 8 * 1024 * 1024
ROOT_FILES = frozenset({
    "state.json", "epic.md", "plan.md", "runtime-context.md", "agents.json",
    "ui-portfolio.json", "portfolio-backlog.json", "portfolio-control.json", "portfolio-run.json",
})
WORKSPACE_FILES = frozenset({"state.json", "epic.md", "plan.md", "runtime-context.md", "agents.json"})
OWNED_DIRS = frozenset({"increments", "decisions", "reviews", "handoffs", "logs"})
WORKSPACE_DIRS = OWNED_DIRS | {"evidence"}
LOCK_NAME = ".runtime.lock"


class LegacyCleanupError(ValueError):
    """Cleanup cannot safely use the proposed scope."""


def _require(condition, message):
    if not condition:
        raise LegacyCleanupError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _canonical(relative):
    _require(isinstance(relative, str) and relative and len(relative) <= 2000 and "\\" not in relative,
             "Expected a bounded canonical relative path.")
    path = Path(relative)
    _require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == relative,
             f"Unsafe or noncanonical path: {relative}")
    return path


def _metadata(repo, relative, *, missing=False):
    path = _canonical(relative)
    current = repo
    try:
        for part in path.parts:
            current = current / part
            value = current.lstat()
            _require(not stat.S_ISLNK(value.st_mode) and not (getattr(value, "st_file_attributes", 0) & 1024),
                     f"Cleanup refuses links or reparse points: {relative}")
        _require(stat.S_ISDIR(value.st_mode) or stat.S_ISREG(value.st_mode), f"Cleanup refuses special files: {relative}")
        return value
    except FileNotFoundError:
        if missing:
            return None
        raise LegacyCleanupError(f"Cleanup path disappeared: {relative}")


def _record(repo, relative, metadata):
    record = {"path": relative, "device": metadata.st_dev, "inode": metadata.st_ino, "mode": metadata.st_mode}
    if stat.S_ISREG(metadata.st_mode):
        _require(metadata.st_size <= MAX_FILE_BYTES, f"Legacy file exceeds size bound: {relative}")
        try:
            payload = read_evidence(repo, relative, MAX_FILE_BYTES)
        except (OSError, ValueError) as exc:
            raise LegacyCleanupError(f"Cannot safely inventory {relative}: {exc}") from exc
        after = _metadata(repo, relative)
        _require((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) ==
                 (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns),
                 f"File changed while inventorying: {relative}")
        record.update(size=len(payload), sha256=hashlib.sha256(payload).hexdigest(), modifiedNs=after.st_mtime_ns)
    return record


def _children(repo, relative):
    children = []
    with os.scandir(repo / relative) as stream:
        for entry in stream:
            _require(len(children) < MAX_ENTRIES, "Directory exceeds cleanup entry limit.")
            children.append(Path(entry.path))
    return sorted(children)


def _path_references(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if isinstance(item.get("path"), str):
                yield item["path"]
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


def _reference_closure(repo, document):
    """Bounded path closure shared by authoritative preview and cheap detection."""
    protected = {PRODUCT_FILE}
    pending = list(_path_references(document))
    visited = set()
    json_bytes = 0
    while pending:
        relative = pending.pop()
        candidate = Path(relative)
        if candidate.is_absolute():
            # Evidence may attribute an external source. Classify lexically:
            # resolving or reading it would exceed this cleanup's repository scope.
            _require(len(relative) <= 2000 and "\\" not in relative
                     and ".." not in candidate.parts and candidate.as_posix() == relative,
                     f"Unsafe or noncanonical evidence path: {relative}")
            try:
                relative = candidate.relative_to(repo).as_posix()
            except ValueError:
                continue
        path = _canonical(relative)
        if not path.parts or path.parts[0] != ".aim" or relative in visited:
            continue
        visited.add(relative)
        _require(len(visited) <= MAX_ENTRIES, "Current evidence references exceed cleanup bounds.")
        protected.add(relative)
        metadata = _metadata(repo, relative, missing=True)
        if metadata is None or not stat.S_ISREG(metadata.st_mode) or path.suffix.lower() != ".json":
            continue
        json_bytes += metadata.st_size
        _require(json_bytes <= MAX_REFERENCE_JSON_BYTES, "Current JSON evidence closure exceeds the bounded read budget.")
        try:
            value = json.loads(read_evidence(repo, relative, MAX_FILE_BYTES))
        except (ValueError, OSError, UnicodeError):
            # The ledger validated the authoritative evidence. A historical
            # non-JSON report is still protected, but supplies no JSON closure.
            continue
        pending.extend(_path_references(value))
    return protected


def _product_protection(repo):
    """Protect all ledger references, including retained attempts and JSON chains."""
    try:
        document, product_hash = load_product(repo)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise LegacyCleanupError(f"Current product backlog must validate before cleanup: {exc}") from exc
    return _reference_closure(repo, document), product_hash


def _workspace_path(repo, raw):
    if raw == ".":
        return ".aim"
    path = _canonical(raw)
    _require(path.parts[0] not in {"analysis", "archive", "increments", "decisions", "reviews", "logs", "evidence"},
             f"Catalog workspace overlaps protected or shared data: {raw}")
    relative = ".aim/" + raw
    metadata = _metadata(repo, relative, missing=True)
    _require(metadata is None or stat.S_ISDIR(metadata.st_mode), f"Workspace is not a directory: {raw}")
    return relative


def _discover_workspaces(repo):
    workspaces = set()
    root_state = _metadata(repo, ".aim/state.json", missing=True)
    if root_state is not None:
        _require(stat.S_ISREG(root_state.st_mode), "Root legacy state must be a regular file.")
        workspaces.add(".aim")
    catalog_meta = _metadata(repo, ".aim/ui-portfolio.json", missing=True)
    if catalog_meta is not None:
        try:
            catalog = json.loads(read_evidence(repo, ".aim/ui-portfolio.json", MAX_CATALOG_BYTES))
        except (OSError, ValueError) as exc:
            raise LegacyCleanupError(f"Legacy workspace catalog cannot be safely read: {exc}") from exc
        _require(isinstance(catalog, dict) and catalog.get("portfolioVersion") == "1.0"
                 and set(catalog) == {"portfolioVersion", "workspaces"}
                 and isinstance(catalog["workspaces"], list) and len(catalog["workspaces"]) <= 256,
                 "Legacy workspace catalog is unsupported or malformed.")
        for item in catalog["workspaces"]:
            _require(isinstance(item, dict) and set(item) == {"path"}, "Malformed workspace declaration.")
            relative = _workspace_path(repo, item["path"])
            if _metadata(repo, relative, missing=True) is not None:
                workspaces.add(relative)
    for parent in (".aim/portfolio", ".aim/workspaces"):
        metadata = _metadata(repo, parent, missing=True)
        if metadata is None:
            continue
        _require(stat.S_ISDIR(metadata.st_mode), f"Workspace container is not a directory: {parent}")
        children = _children(repo, parent)
        for child in children:
            relative = child.relative_to(repo).as_posix()
            metadata = _metadata(repo, relative)
            if stat.S_ISDIR(metadata.st_mode):
                names = {entry.name for entry in _children(repo, relative)}
                if names & (WORKSPACE_FILES | WORKSPACE_DIRS):
                    workspaces.add(relative)
    return sorted(workspaces)


def _legacy_archive_name(name, directory):
    if directory:
        return bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-legacy-[A-Za-z0-9_-]+", name))
    return bool(re.fullmatch(r"(?:epic-[A-Za-z0-9-]+\.md|state-[A-Za-z0-9-]+\.json|portfolio-run-[A-Za-z0-9-]+\.json|catalog-repair-[A-Za-z0-9-]+\.json)", name))


def detect(repo):
    """Lightweight, non-authoritative UI offer; no fingerprints or mutations.

    Reads bounded catalog/ledger JSON only. It does not verify acceptance or
    claim that deletion is safe: preview must still validate the full scope.
    """
    repo = Path(repo).resolve()
    result = {"legacyDetected": False, "workspaceCount": 0, "warnings": []}
    try:
        if _metadata(repo, ".aim", missing=True) is None:
            return result
        protected = {PRODUCT_FILE}
        if _metadata(repo, PRODUCT_FILE, missing=True) is not None:
            try:
                product = json.loads(read_evidence(repo, PRODUCT_FILE, MAX_CATALOG_BYTES))
                protected = _reference_closure(repo, product)
            except (OSError, ValueError, UnicodeError) as exc:
                result["warnings"].append(f"Current references need full preview validation: {exc}")
        protected_identities = set()
        for relative in protected:
            metadata = _metadata(repo, relative, missing=True)
            if metadata is not None:
                protected_identities.add((metadata.st_dev, metadata.st_ino))
        inspected = 0

        def remnants(relative):
            nonlocal inspected
            inspected += 1
            _require(inspected <= MAX_ENTRIES, "Legacy detection exceeds entry bound; use a reviewed preview.")
            if Path(relative).name == LOCK_NAME or any(relative == item or relative.startswith(item + "/") for item in protected):
                return False
            metadata = _metadata(repo, relative, missing=True)
            if metadata is None:
                return False
            if (metadata.st_dev, metadata.st_ino) in protected_identities:
                return False
            if stat.S_ISREG(metadata.st_mode):
                return True
            return any(remnants(child.relative_to(repo).as_posix()) for child in _children(repo, relative))

        def workspace_has_data(relative, root=False):
            names = (ROOT_FILES | OWNED_DIRS) if root else (WORKSPACE_FILES | WORKSPACE_DIRS)
            return any(remnants(relative + "/" + name) for name in sorted(names))

        workspaces = _discover_workspaces(repo)
        result["workspaceCount"] = sum(workspace_has_data(path) for path in workspaces if path != ".aim")
        root_has_data = workspace_has_data(".aim", root=True)
        if ".aim" in workspaces and root_has_data:
            result["workspaceCount"] += 1
        result["legacyDetected"] = root_has_data or result["workspaceCount"] > 0
        archive = _metadata(repo, ".aim/archive", missing=True)
        if archive is not None:
            for child in _children(repo, ".aim/archive"):
                relative = child.relative_to(repo).as_posix()
                metadata = _metadata(repo, relative)
                if _legacy_archive_name(child.name, stat.S_ISDIR(metadata.st_mode)) and remnants(relative):
                    result["legacyDetected"] = True
                    break
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["legacyDetected"] = True
        result["warnings"].append(str(exc))
    return result


def preview(repo):
    """Return an exact bounded deletion inventory without creating any files."""
    repo = Path(repo).resolve()
    _require(repo.is_dir(), "Repository directory does not exist.")
    protected, product_hash = _product_protection(repo)
    aim_meta = _metadata(repo, ".aim", missing=True)
    _require(aim_meta is None or stat.S_ISDIR(aim_meta.st_mode), ".aim must be a directory.")
    workspaces = set(_discover_workspaces(repo)) if aim_meta is not None else set()
    files = {}
    directories = {}
    retained = set()
    unknown = set()
    protected_identities = set()
    protected_records = []
    protected_bytes = 0
    for relative in sorted(protected):
        metadata = _metadata(repo, relative, missing=True)
        if metadata is not None:
            if stat.S_ISREG(metadata.st_mode):
                protected_bytes += metadata.st_size
                _require(protected_bytes <= MAX_TOTAL_BYTES, "Protected evidence exceeds cleanup byte bounds.")
            record = _record(repo, relative, metadata)
            protected_records.append(record)
            protected_identities.add((metadata.st_dev, metadata.st_ino))
    entry_count = 0
    total_bytes = 0

    def inventory(relative):
        nonlocal entry_count, total_bytes
        metadata = _metadata(repo, relative, missing=True)
        if metadata is None:
            return
        entry_count += 1
        _require(entry_count <= MAX_ENTRIES, "Legacy inventory exceeds entry limit.")
        if Path(relative).name == LOCK_NAME:
            _require(stat.S_ISREG(metadata.st_mode), "Runtime lock must be a regular file.")
            workspaces.add(Path(relative).parent.as_posix())
            return
        shared = any(relative == value or relative.startswith(value + "/") for value in protected)
        if shared or (metadata.st_dev, metadata.st_ino) in protected_identities:
            retained.add(relative)
            return
        if stat.S_ISDIR(metadata.st_mode):
            directories[relative] = _record(repo, relative, metadata)
            for child in _children(repo, relative):
                inventory(child.relative_to(repo).as_posix())
        else:
            record = _record(repo, relative, metadata)
            files[relative] = record
            if Path(relative).name == "state.json":
                workspaces.add(Path(relative).parent.as_posix())
            total_bytes += record["size"]
            _require(total_bytes <= MAX_TOTAL_BYTES, "Legacy inventory exceeds byte limit.")

    def known_workspace(relative, root=False):
        metadata = _metadata(repo, relative, missing=True)
        if metadata is None:
            return
        owned_files = ROOT_FILES if root else WORKSPACE_FILES
        owned_dirs = OWNED_DIRS if root else WORKSPACE_DIRS
        for child in _children(repo, relative):
            name = child.name
            child_relative = child.relative_to(repo).as_posix()
            _metadata(repo, child_relative)
            if name == LOCK_NAME:
                _metadata(repo, child_relative)
                continue
            if name in owned_files or name in owned_dirs:
                child_meta = _metadata(repo, child_relative)
                _require(stat.S_ISREG(child_meta.st_mode) if name in owned_files else stat.S_ISDIR(child_meta.st_mode),
                         f"Legacy entry has an unexpected type: {child_relative}")
                inventory(child_relative)
            elif name not in {"analysis", "product-backlog.json", "portfolio", "workspaces", "archive"}:
                unknown.add(child_relative)
        if not root:
            directories[relative] = _record(repo, relative, metadata)

    if aim_meta is not None:
        known_workspace(".aim", root=True)
        for workspace in sorted(workspaces):
            if workspace != ".aim":
                known_workspace(workspace)
        archive = _metadata(repo, ".aim/archive", missing=True)
        if archive is not None:
            _require(stat.S_ISDIR(archive.st_mode), "Legacy archive is not a directory.")
            for child in _children(repo, ".aim/archive"):
                relative = child.relative_to(repo).as_posix()
                metadata = _metadata(repo, relative)
                if _legacy_archive_name(child.name, stat.S_ISDIR(metadata.st_mode)):
                    inventory(relative)
                else:
                    unknown.add(relative)
            directories[".aim/archive"] = _record(repo, ".aim/archive", archive)
    # Keep discovery markers until ordinary files have been removed, so a
    # partial failure remains discoverable through the next fresh preview.
    file_records = sorted(files.values(), key=lambda item: (
        2 if item["path"] == ".aim/ui-portfolio.json" else 1 if Path(item["path"]).name == "state.json" else 0,
        item["path"],
    ))
    directory_records = [directories[key] for key in sorted(directories, key=lambda value: (-len(Path(value).parts), value))]
    protected_names = sorted(record["path"] for record in protected_records)
    workspaces = sorted(workspaces)
    scope = {"repo": str(repo), "workspaces": workspaces, "files": file_records, "directories": directory_records,
             "protected": protected_records, "productSha256": product_hash, "retainedUnknown": sorted(unknown)}
    return {
        "version": 1, "repo": str(repo), "inventorySha256": _digest(scope), "legacyDetected": bool(file_records),
        "workspaces": workspaces, "files": file_records, "directories": directory_records,
        "retainedCurrentRefs": sorted(set(protected_names) | retained), "retainedUnknown": sorted(unknown),
        "totalFiles": len(file_records), "totalBytes": sum(item["size"] for item in file_records),
        "warnings": (["Unrecognized files are retained; cleanup does not guess their ownership."] if unknown else []),
    }


@contextmanager
def _parent_descriptor(repo, relative):
    path = _canonical(relative)
    _require(path.parts[0] == ".aim" and len(path.parts) > 1, "Deletion must remain below .aim.")
    _require(os.open in os.supports_dir_fd and os.unlink in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW"),
             "This platform lacks safe directory-relative cleanup; no files were removed.")
    descriptor = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, path.name
    finally:
        os.close(descriptor)


def _remove_file(repo, record):
    with _parent_descriptor(repo, record["path"]) as (parent, name):
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        _require(stat.S_ISREG(current.st_mode) and
                 (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) ==
                 (record["device"], record["inode"], record["size"], record["modifiedNs"]),
                 f"File changed after cleanup validation: {record['path']}")
        os.unlink(name, dir_fd=parent)


def _remove_directory(repo, record):
    with _parent_descriptor(repo, record["path"]) as (parent, name):
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        _require(stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino) == (record["device"], record["inode"]),
                 f"Directory changed after cleanup validation: {record['path']}")
        try:
            os.rmdir(name, dir_fd=parent)
            return True
        except OSError as exc:
            if exc.errno in {errno.ENOTEMPTY, errno.EEXIST}:
                return False  # Shared current evidence, unknown files or permanent lock inode.
            raise


def apply(repo, expected_inventory_sha256, *, confirm=False):
    """Delete only a freshly matched inventory under every affected runtime lock."""
    _require(confirm is True, "Permanent legacy deletion requires explicit confirmation.")
    _require(isinstance(expected_inventory_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", expected_inventory_sha256),
             "Apply requires the exact preview inventory SHA-256.")
    repo = Path(repo).resolve()
    initial = preview(repo)
    _require(initial["inventorySha256"] == expected_inventory_sha256, "Cleanup inventory changed; obtain and review a fresh preview.")
    result = {"status": "complete", "removedFiles": [], "removedFileCount": 0, "removedBytes": 0,
              "removedDirectories": [], "retainedCurrentRefs": initial["retainedCurrentRefs"], "errors": [],
              "nextAction": "Preview again to inspect any remaining legacy data."}
    if not initial["legacyDetected"]:
        return result
    with ExitStack() as locks:
        locks.enter_context(runtime_lock(repo / ".aim/state.json"))
        for workspace in initial["workspaces"]:
            if workspace != ".aim":
                locks.enter_context(runtime_lock(repo / workspace / "state.json"))
        current = preview(repo)
        _require(current["inventorySha256"] == expected_inventory_sha256,
                 "Cleanup inventory changed while acquiring locks; obtain and review a fresh preview.")
        for record in current["files"]:
            try:
                _remove_file(repo, record)
            except (OSError, ValueError) as exc:
                result["status"] = "partial"
                result["errors"].append({"path": record["path"], "message": str(exc)})
                result["nextAction"] = "Deletion stopped after a failure. Obtain a fresh preview; do not replay the old scope."
                return result
            result["removedFiles"].append(record["path"])
            result["removedFileCount"] += 1
            result["removedBytes"] += record["size"]
        for record in current["directories"]:
            try:
                if _remove_directory(repo, record):
                    result["removedDirectories"].append(record["path"])
            except (OSError, ValueError) as exc:
                result["status"] = "partial"
                result["errors"].append({"path": record["path"], "message": str(exc)})
                result["nextAction"] = "File deletion completed with directory cleanup errors. Obtain a fresh preview."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("command", choices=("preview", "apply"))
    parser.add_argument("--expected-sha256")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = preview(args.repo) if args.command == "preview" else apply(args.repo, args.expected_sha256, confirm=args.confirm)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "partial" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc), "removedFileCount": 0}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
