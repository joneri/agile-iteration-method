#!/usr/bin/env python3
"""Preview or apply one approved AIM Portfolio catalog-history repair.

The helper owns bounded data safety only. It never decides that a repair is
appropriate, approves a Gate, rewrites accepted runtime evidence, or discovers
archive candidates. AIM chat supplies one explicitly reviewed relation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from aim_backlog import validate_backlog


PORTFOLIO_FILE = "ui-portfolio.json"
BACKLOG_FILE = "portfolio-backlog.json"
ARCHIVE_DIR = "archive"
MAX_FILE_BYTES = 1_048_576
MAX_WORKSPACE_FILE_BYTES = 16_777_216
MAX_WORKSPACE_BYTES = 67_108_864
MAX_WORKSPACE_ENTRIES = 4096
EPIC_ID_PATTERN = re.compile(r"EPIC-[A-Z0-9-]+")
CANDIDATE_ID_PATTERN = re.compile(r"INC-[A-Z0-9-]+")
INCREMENT_ID_PATTERN = re.compile(r"DI-[0-9]+")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)


class CatalogRepairError(ValueError):
    """A bounded operator-facing catalog-repair error."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _validate_timestamp(value: str, field: str) -> None:
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise CatalogRepairError(f"{field} must be a second-precision UTC timestamp.")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CatalogRepairError(f"{field} must be a real UTC calendar timestamp.") from exc


def _inside_aim(repo_root: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    if not root.is_dir():
        raise CatalogRepairError("The repository root is not a directory.")
    aim_root = root / ".aim"
    if aim_root.is_symlink():
        raise CatalogRepairError(".aim must not be a symbolic link.")
    if not aim_root.is_dir():
        raise CatalogRepairError("Catalog repair requires an existing .aim directory.")
    resolved = aim_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CatalogRepairError(".aim leaves the repository boundary.") from exc
    return root, resolved


def _read_regular(path: Path, label: str, maximum: int = MAX_FILE_BYTES) -> bytes:
    if path.is_symlink():
        raise CatalogRepairError(f"{label} must not be a symbolic link.")
    if not path.is_file():
        raise CatalogRepairError(f"Missing {label}.")
    if path.stat().st_size > maximum:
        raise CatalogRepairError(f"{label} is larger than {maximum} bytes.")
    return path.read_bytes()


def _json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CatalogRepairError(f"{label} contains invalid JSON at line {exc.lineno}.") from exc
    if not isinstance(value, dict):
        raise CatalogRepairError(f"{label} must contain a JSON object.")
    return value


def _relative_workspace(aim_root: Path, raw: str, index: int) -> Path:
    if raw == ".":
        raise CatalogRepairError("The root .aim workspace cannot be archived by catalog repair.")
    if not isinstance(raw, str) or not raw or len(raw) > 500 or "\\" in raw:
        raise CatalogRepairError(f"Workspace {index} has an invalid POSIX path.")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise CatalogRepairError(f"Workspace {index} contains an absolute, dot, or traversal path.")
    current = aim_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CatalogRepairError(f"Workspace {index} crosses a symbolic link: {raw}.")
    resolved = current.resolve()
    try:
        resolved.relative_to(aim_root)
    except ValueError as exc:
        raise CatalogRepairError(f"Workspace {index} leaves .aim.") from exc
    if not resolved.is_dir():
        raise CatalogRepairError(f"Workspace {index} directory was not found: {raw}.")
    return resolved


def _load_catalog(aim_root: Path) -> tuple[dict[str, Any], bytes, dict[str, Path]]:
    payload = _read_regular(aim_root / PORTFOLIO_FILE, PORTFOLIO_FILE)
    value = _json_object(payload, PORTFOLIO_FILE)
    if set(value) != {"portfolioVersion", "workspaces"} or value.get("portfolioVersion") != "1.0":
        raise CatalogRepairError(f"{PORTFOLIO_FILE} is not a supported Portfolio catalog.")
    items = value.get("workspaces")
    if not isinstance(items, list) or not items:
        raise CatalogRepairError(f"{PORTFOLIO_FILE} must contain at least one workspace.")
    resolved: dict[str, Path] = {}
    seen_paths: set[Path] = set()
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or set(item) != {"path"}:
            raise CatalogRepairError(f"Workspace {index} must contain only path.")
        raw = item.get("path")
        if not isinstance(raw, str) or raw in resolved:
            raise CatalogRepairError(f"Workspace {index} has a missing or duplicate path.")
        if raw == ".":
            candidate = aim_root
        else:
            candidate = _relative_workspace(aim_root, raw, index)
        if candidate in seen_paths:
            raise CatalogRepairError(f"Workspace {index} duplicates an earlier resolved path.")
        resolved[raw] = candidate
        seen_paths.add(candidate)
    return value, payload, resolved


def _load_backlog(aim_root: Path) -> tuple[dict[str, Any], bytes]:
    payload = _read_regular(aim_root / BACKLOG_FILE, BACKLOG_FILE)
    value = _json_object(payload, BACKLOG_FILE)
    issues = validate_backlog(value)
    if issues:
        raise CatalogRepairError(f"Invalid {BACKLOG_FILE}: " + "; ".join(issues))
    return value, payload


def _tree_digest(workspace: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    file_count = 0
    byte_count = 0
    entry_count = 0
    for current, directories, files in os.walk(workspace, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        for name in directories:
            entry_count += 1
            if entry_count > MAX_WORKSPACE_ENTRIES:
                raise CatalogRepairError("Workspace tree has too many entries.")
            path = current_path / name
            if path.is_symlink():
                raise CatalogRepairError(f"Workspace tree contains symbolic link {path}.")
            relative = path.relative_to(workspace).as_posix().encode("utf-8")
            digest.update(b"D\0" + relative + b"\0")
        for name in files:
            entry_count += 1
            if entry_count > MAX_WORKSPACE_ENTRIES:
                raise CatalogRepairError("Workspace tree has too many entries.")
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                raise CatalogRepairError(f"Workspace tree contains unsafe entry {path}.")
            size = path.stat().st_size
            if size > MAX_WORKSPACE_FILE_BYTES:
                raise CatalogRepairError(f"Workspace file is too large for bounded repair: {path}.")
            byte_count += size
            if byte_count > MAX_WORKSPACE_BYTES:
                raise CatalogRepairError("Workspace tree is too large for bounded repair.")
            relative = path.relative_to(workspace).as_posix().encode("utf-8")
            digest.update(b"F\0" + relative + b"\0")
            digest.update(size.to_bytes(8, "big"))
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
            file_count += 1
    return digest.hexdigest(), file_count, byte_count


def _acceptance_file(
    root: Path, aim_root: Path, workspace: Path, raw: str, increment_id: str
) -> tuple[Path, bytes]:
    if not isinstance(raw, str) or not raw.startswith(".aim/") or "\\" in raw:
        raise CatalogRepairError("acceptance-evidence must be a repository-relative .aim POSIX path.")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise CatalogRepairError("acceptance-evidence contains an absolute, dot, or traversal path.")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CatalogRepairError("acceptance-evidence crosses a symbolic link.")
    resolved = current.resolve()
    try:
        resolved.relative_to(workspace / "decisions")
        resolved.relative_to(aim_root)
    except ValueError as exc:
        raise CatalogRepairError("acceptance-evidence must be inside the workspace decisions directory.") from exc
    payload = _read_regular(resolved, "acceptance evidence")
    text = payload.decode("utf-8", errors="replace")
    lowered = text.casefold()
    authority_headings = [
        line.casefold()
        for line in text.splitlines()
        if line.lstrip().startswith("#")
        and increment_id.casefold() in line.casefold()
        and "gate e" in line.casefold()
    ]
    negative_heading = any(
        re.search(r"\b(?:not accepted|rejected|declined|acceptance denied)\b", line)
        is not None
        for line in authority_headings
    )
    negative_decision = re.search(
        r"(?im)^\s*(?:decision|status)\s*:\s*(?:not accepted|rejected|declined|acceptance denied|change requested)\b",
        text,
    )
    accepted_heading = any(
        re.search(r"\baccepted\b", line) is not None for line in authority_headings
    )
    accepted_decision = re.search(
        r"(?im)^\s*(?:decision|status)\s*:\s*accept(?:ed)?\b",
        text,
    )
    if (
        increment_id.casefold() not in lowered
        or "gate e" not in lowered
        or negative_heading
        or negative_decision is not None
        or not (accepted_heading or accepted_decision)
    ):
        raise CatalogRepairError(
            "acceptance evidence must name the runtime Increment, Gate E, and acceptance."
        )
    return resolved, payload


def _archive_paths(aim_root: Path, epic_id: str, candidate_id: str, tree_sha256: str) -> tuple[Path, Path]:
    suffix = tree_sha256[:12]
    epic_slug = epic_id.casefold()
    candidate_slug = candidate_id.casefold()
    archive_root = aim_root / ARCHIVE_DIR
    return (
        archive_root / f"catalog-workspace-{epic_slug}-{suffix}",
        archive_root / f"catalog-repair-{candidate_slug}-{suffix}.json",
    )


def _validate_request(
    candidate_id: str,
    epic_id: str,
    increment_id: str,
    workspace: str,
    acceptance_evidence: str,
    archived_at: str,
) -> None:
    if CANDIDATE_ID_PATTERN.fullmatch(candidate_id) is None or len(candidate_id) > 80:
        raise CatalogRepairError("candidate-id must be a bounded canonical INC-* identity.")
    if EPIC_ID_PATTERN.fullmatch(epic_id) is None or len(epic_id) > 120:
        raise CatalogRepairError("epic-id must be a bounded canonical EPIC-* identity.")
    if INCREMENT_ID_PATTERN.fullmatch(increment_id) is None or len(increment_id) > 32:
        raise CatalogRepairError("increment-id must be a bounded canonical DI-* identity.")
    if not isinstance(workspace, str) or not workspace:
        raise CatalogRepairError("workspace must name one catalogued contained workspace.")
    if not isinstance(acceptance_evidence, str) or not acceptance_evidence:
        raise CatalogRepairError("acceptance-evidence is required.")
    _validate_timestamp(archived_at, "archived-at")


def plan_repair(
    repo_root: Path,
    *,
    candidate_id: str,
    epic_id: str,
    increment_id: str,
    workspace: str,
    acceptance_evidence: str,
    archived_at: str,
) -> dict[str, Any]:
    """Build a no-write repair plan for one explicitly reviewed relation."""

    _validate_request(
        candidate_id, epic_id, increment_id, workspace, acceptance_evidence, archived_at
    )
    root, aim_root = _inside_aim(repo_root)
    catalog, catalog_payload, catalog_workspaces = _load_catalog(aim_root)
    if workspace == ".":
        raise CatalogRepairError("The root .aim workspace cannot be archived by catalog repair.")
    if workspace not in catalog_workspaces:
        raise CatalogRepairError(f"Workspace {workspace} is not in the active Portfolio catalog.")
    workspace_path = catalog_workspaces[workspace]

    backlog, backlog_payload = _load_backlog(aim_root)
    matches = [item for item in backlog["items"] if item.get("id") == candidate_id]
    if len(matches) != 1:
        raise CatalogRepairError(f"Backlog must contain exactly one candidate {candidate_id}.")
    candidate = matches[0]
    if candidate.get("epicId") != epic_id or candidate.get("runtimeIncrementId") != increment_id:
        raise CatalogRepairError("Backlog candidate does not match the reviewed Epic and runtime Increment.")
    related = [
        item
        for item in backlog["items"]
        if item.get("epicId") == epic_id and item.get("runtimeIncrementId") is not None
    ]
    if len(related) != 1:
        raise CatalogRepairError(
            "The Epic has multiple runtime-linked Backlog records; review them as one future bounded repair."
        )

    state_path = workspace_path / "state.json"
    state_payload = _read_regular(state_path, f"{workspace}/state.json")
    state = _json_object(state_payload, f"{workspace}/state.json")
    if state.get("stateSchemaVersion") != "1.0":
        raise CatalogRepairError("Workspace state is not current stateSchemaVersion 1.0.")
    if state.get("epicId") != epic_id:
        raise CatalogRepairError("Workspace state does not own the reviewed Epic.")
    if state.get("epicStatus") != "epic_complete" or state.get("lastGatePassed") != "Gate E":
        raise CatalogRepairError("Only an Epic completed through Gate E can be repaired.")
    if increment_id not in {state.get("activeIncrementId"), state.get("previousIncrementId")}:
        raise CatalogRepairError("Workspace state does not reference the reviewed runtime Increment.")
    if state.get("previousIncrementId") == increment_id and state.get("previousIncrementStatus") != "accepted":
        raise CatalogRepairError("The previous runtime Increment is not marked accepted.")
    updated_at = state.get("updatedAt")
    _validate_timestamp(updated_at, "workspace state updatedAt")

    evidence_path, evidence_payload = _acceptance_file(
        root, aim_root, workspace_path, acceptance_evidence, increment_id
    )
    evidence_relative = evidence_path.relative_to(workspace_path).as_posix()
    state_evidence = state.get("gateEAcceptance")
    if state_evidence is not None and state_evidence != acceptance_evidence:
        raise CatalogRepairError("Explicit acceptance evidence does not match gateEAcceptance in state.")

    tree_sha256, file_count, byte_count = _tree_digest(workspace_path)
    archive_path, audit_path = _archive_paths(
        aim_root, epic_id, candidate_id, tree_sha256
    )
    archive_root = aim_root / ARCHIVE_DIR
    if archive_root.is_symlink() or (archive_root.exists() and not archive_root.is_dir()):
        raise CatalogRepairError(f"{ARCHIVE_DIR} must be a real directory.")
    if archive_path.exists() or archive_path.is_symlink():
        raise CatalogRepairError(f"Archive destination {archive_path.name} already exists.")
    if audit_path.exists() or audit_path.is_symlink():
        raise CatalogRepairError(f"Audit destination {audit_path.name} already exists.")

    next_catalog = dict(catalog)
    next_catalog["workspaces"] = [item for item in catalog["workspaces"] if item["path"] != workspace]
    if not next_catalog["workspaces"]:
        raise CatalogRepairError("Repair cannot leave an empty Portfolio catalog.")
    next_catalog_payload = _json_bytes(next_catalog)
    next_backlog = dict(backlog)
    next_backlog["updatedAt"] = archived_at
    next_backlog["items"] = [item for item in backlog["items"] if item.get("id") != candidate_id]
    next_backlog_payload = _json_bytes(next_backlog)

    archive_relative = archive_path.relative_to(root).as_posix()
    audit_relative = audit_path.relative_to(root).as_posix()
    return {
        "result": "planned",
        "repo": str(root),
        "candidateId": candidate_id,
        "epicId": epic_id,
        "runtimeIncrementId": increment_id,
        "workspace": workspace,
        "stateUpdatedAt": updated_at,
        "acceptanceEvidence": evidence_path.relative_to(root).as_posix(),
        "acceptanceRelativePath": evidence_relative,
        "archivedAcceptanceEvidence": f"{archive_relative}/{evidence_relative}",
        "archivedAt": archived_at,
        "archivePath": archive_relative,
        "auditPath": audit_relative,
        "catalogSha256": _sha256(catalog_payload),
        "backlogSha256": _sha256(backlog_payload),
        "stateSha256": _sha256(state_payload),
        "acceptanceSha256": _sha256(evidence_payload),
        "workspaceTreeSha256": tree_sha256,
        "workspaceFileCount": file_count,
        "workspaceByteCount": byte_count,
        "catalogAfterSha256": _sha256(next_catalog_payload),
        "backlogAfterSha256": _sha256(next_backlog_payload),
        "retiredCandidate": candidate,
        "move": {"from": f".aim/{workspace}", "to": archive_relative},
        "writes": [f".aim/{PORTFOLIO_FILE}", f".aim/{BACKLOG_FILE}", audit_relative],
    }


def _atomic_write(path: Path, payload: bytes, prefix: str) -> None:
    if path.is_symlink():
        raise CatalogRepairError(f"{path.name} must not be a symbolic link.")
    descriptor, temporary = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _changed_payloads(plan: dict[str, Any], catalog: dict[str, Any], backlog: dict[str, Any]) -> tuple[bytes, bytes, bytes]:
    next_catalog = dict(catalog)
    next_catalog["workspaces"] = [
        item for item in catalog["workspaces"] if item["path"] != plan["workspace"]
    ]
    next_backlog = dict(backlog)
    next_backlog["updatedAt"] = plan["archivedAt"]
    next_backlog["items"] = [
        item for item in backlog["items"] if item.get("id") != plan["candidateId"]
    ]
    audit = {
        "repairVersion": "1.0",
        "appliedAt": plan["archivedAt"],
        "candidateId": plan["candidateId"],
        "epicId": plan["epicId"],
        "runtimeIncrementId": plan["runtimeIncrementId"],
        "sourceWorkspace": f".aim/{plan['workspace']}",
        "archivePath": plan["archivePath"],
        "sourceAcceptanceEvidence": plan["acceptanceEvidence"],
        "archivedAcceptanceEvidence": plan["archivedAcceptanceEvidence"],
        "retiredCandidate": plan["retiredCandidate"],
        "evidence": {
            "catalogBeforeSha256": plan["catalogSha256"],
            "catalogAfterSha256": plan["catalogAfterSha256"],
            "backlogBeforeSha256": plan["backlogSha256"],
            "backlogAfterSha256": plan["backlogAfterSha256"],
            "stateSha256": plan["stateSha256"],
            "stateUpdatedAt": plan["stateUpdatedAt"],
            "acceptanceSha256": plan["acceptanceSha256"],
            "workspaceTreeSha256": plan["workspaceTreeSha256"],
            "workspaceFileCount": plan["workspaceFileCount"],
            "workspaceByteCount": plan["workspaceByteCount"],
        },
    }
    return _json_bytes(next_catalog), _json_bytes(next_backlog), _json_bytes(audit)


def apply_repair(
    repo_root: Path,
    *,
    candidate_id: str,
    epic_id: str,
    increment_id: str,
    workspace: str,
    acceptance_evidence: str,
    archived_at: str,
    expected_catalog_sha256: str,
    expected_backlog_sha256: str,
    expected_state_sha256: str,
    expected_acceptance_sha256: str,
    expected_workspace_sha256: str,
    expected_state_updated_at: str,
    fault_at: str | None = None,
    fault_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Apply an exact previewed repair or restore all handled failures."""

    plan = plan_repair(
        repo_root,
        candidate_id=candidate_id,
        epic_id=epic_id,
        increment_id=increment_id,
        workspace=workspace,
        acceptance_evidence=acceptance_evidence,
        archived_at=archived_at,
    )
    expected = {
        "catalogSha256": expected_catalog_sha256,
        "backlogSha256": expected_backlog_sha256,
        "stateSha256": expected_state_sha256,
        "acceptanceSha256": expected_acceptance_sha256,
        "workspaceTreeSha256": expected_workspace_sha256,
        "stateUpdatedAt": expected_state_updated_at,
    }
    for field, value in expected.items():
        if plan[field] != value:
            raise CatalogRepairError(f"{field} changed since preview; reload before applying.")

    root, aim_root = _inside_aim(repo_root)
    catalog_path = aim_root / PORTFOLIO_FILE
    backlog_path = aim_root / BACKLOG_FILE
    workspace_path = aim_root.joinpath(*PurePosixPath(workspace).parts)
    archive_path = root / plan["archivePath"]
    audit_path = root / plan["auditPath"]
    archive_root = aim_root / ARCHIVE_DIR
    original_catalog = _read_regular(catalog_path, PORTFOLIO_FILE)
    original_backlog = _read_regular(backlog_path, BACKLOG_FILE)
    catalog = _json_object(original_catalog, PORTFOLIO_FILE)
    backlog = _json_object(original_backlog, BACKLOG_FILE)
    catalog_payload, backlog_payload, audit_payload = _changed_payloads(plan, catalog, backlog)
    if _sha256(catalog_payload) != plan["catalogAfterSha256"]:
        raise CatalogRepairError("Staged catalog does not match the previewed result.")
    if _sha256(backlog_payload) != plan["backlogAfterSha256"]:
        raise CatalogRepairError("Staged Backlog does not match the previewed result.")

    staging = Path(tempfile.mkdtemp(prefix=".catalog-repair-", dir=aim_root))
    created_archive_root = False
    workspace_archived = False
    catalog_published = False
    backlog_published = False
    audit_published = False

    def checkpoint(name: str) -> None:
        if fault_hook is not None:
            fault_hook(name)
        if fault_at == name:
            raise CatalogRepairError(f"Injected failure at {name}.")

    def source_is_current() -> None:
        current_workspace = _relative_workspace(aim_root, workspace, 1)
        if current_workspace != workspace_path:
            raise CatalogRepairError("Workspace path changed during repair staging.")
        if _sha256(_read_regular(catalog_path, PORTFOLIO_FILE)) != plan["catalogSha256"]:
            raise CatalogRepairError("Portfolio catalog changed during repair staging.")
        if _sha256(_read_regular(backlog_path, BACKLOG_FILE)) != plan["backlogSha256"]:
            raise CatalogRepairError("Portfolio Backlog changed during repair staging.")
        if _sha256(_read_regular(workspace_path / "state.json", "workspace state")) != plan["stateSha256"]:
            raise CatalogRepairError("Workspace state changed during repair staging.")
        _, current_evidence = _acceptance_file(
            root, aim_root, workspace_path, acceptance_evidence, increment_id
        )
        if _sha256(current_evidence) != plan["acceptanceSha256"]:
            raise CatalogRepairError("Acceptance evidence changed during repair staging.")
        tree_sha256, _, _ = _tree_digest(workspace_path)
        if tree_sha256 != plan["workspaceTreeSha256"]:
            raise CatalogRepairError("Workspace tree changed during repair staging.")

    try:
        (staging / "catalog.json").write_bytes(catalog_payload)
        (staging / "backlog.json").write_bytes(backlog_payload)
        (staging / "audit.json").write_bytes(audit_payload)
        checkpoint("after_staging")
        source_is_current()

        if archive_root.is_symlink() or (archive_root.exists() and not archive_root.is_dir()):
            raise CatalogRepairError(f"{ARCHIVE_DIR} changed to an unsafe path during staging.")
        if not archive_root.exists():
            archive_root.mkdir(mode=0o700)
            created_archive_root = True
        if archive_path.exists() or archive_path.is_symlink() or audit_path.exists() or audit_path.is_symlink():
            raise CatalogRepairError("Archive or audit destination appeared during staging.")
        if _relative_workspace(aim_root, workspace, 1) != workspace_path:
            raise CatalogRepairError("Workspace containment changed before archival.")
        os.rename(workspace_path, archive_path)
        workspace_archived = True
        checkpoint("after_workspace_archive")

        _atomic_write(catalog_path, catalog_payload, ".ui-portfolio.repair.")
        catalog_published = True
        checkpoint("after_catalog_publish")
        _atomic_write(backlog_path, backlog_payload, ".portfolio-backlog.repair.")
        backlog_published = True
        checkpoint("after_backlog_publish")
        _atomic_write(audit_path, audit_payload, ".catalog-repair.audit.")
        audit_published = True
        checkpoint("after_audit_publish")

        tree_sha256, file_count, byte_count = _tree_digest(archive_path)
        if (
            tree_sha256 != plan["workspaceTreeSha256"]
            or file_count != plan["workspaceFileCount"]
            or byte_count != plan["workspaceByteCount"]
        ):
            raise CatalogRepairError("Archived workspace verification failed.")
        if workspace_path.exists() or workspace_path.is_symlink():
            raise CatalogRepairError("Source workspace still exists after archival.")
        if catalog_path.read_bytes() != catalog_payload or backlog_path.read_bytes() != backlog_payload:
            raise CatalogRepairError("Published catalog or Backlog bytes did not verify.")
        if audit_path.read_bytes() != audit_payload:
            raise CatalogRepairError("Published catalog-repair audit did not verify.")
        archived_evidence = root / plan["archivedAcceptanceEvidence"]
        if _sha256(_read_regular(archived_evidence, "archived acceptance evidence")) != plan["acceptanceSha256"]:
            raise CatalogRepairError("Archived acceptance evidence did not verify.")
        checkpoint("after_verify")
    except Exception as repair_error:
        rollback_errors: list[str] = []
        if audit_published:
            try:
                audit_path.unlink()
            except Exception as exc:
                rollback_errors.append(f"audit removal failed: {exc}")
        if backlog_published:
            try:
                _atomic_write(backlog_path, original_backlog, ".portfolio-backlog.rollback.")
            except Exception as exc:
                rollback_errors.append(f"Backlog restore failed: {exc}")
        if catalog_published:
            try:
                _atomic_write(catalog_path, original_catalog, ".ui-portfolio.rollback.")
            except Exception as exc:
                rollback_errors.append(f"catalog restore failed: {exc}")
        if workspace_archived:
            try:
                if workspace_path.exists() or workspace_path.is_symlink():
                    raise CatalogRepairError("original workspace path is occupied")
                os.rename(archive_path, workspace_path)
            except Exception as exc:
                rollback_errors.append(f"workspace restore failed: {exc}")
        if staging.is_dir() and not staging.is_symlink():
            shutil.rmtree(staging, ignore_errors=True)
        if created_archive_root:
            try:
                archive_root.rmdir()
            except OSError:
                pass
        if rollback_errors:
            raise CatalogRepairError(
                f"Catalog repair failed ({repair_error}); rollback needs operator attention: "
                + "; ".join(rollback_errors)
            ) from repair_error
        raise

    if staging.is_dir() and not staging.is_symlink():
        shutil.rmtree(staging)
    result = dict(plan)
    result["result"] = "applied"
    result["auditSha256"] = _sha256(audit_payload)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or apply one approved rollback-safe AIM catalog repair."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--epic-id", required=True)
    parser.add_argument("--increment-id", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--acceptance-evidence", required=True)
    parser.add_argument("--archived-at", required=True)
    parser.add_argument("--expected-catalog-sha256")
    parser.add_argument("--expected-backlog-sha256")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-acceptance-sha256")
    parser.add_argument("--expected-workspace-sha256")
    parser.add_argument("--expected-state-updated-at")
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    common = {
        "repo_root": Path(args.repo),
        "candidate_id": args.candidate_id,
        "epic_id": args.epic_id,
        "increment_id": args.increment_id,
        "workspace": args.workspace,
        "acceptance_evidence": args.acceptance_evidence,
        "archived_at": args.archived_at,
    }
    try:
        if args.apply:
            required = {
                "expected_catalog_sha256": args.expected_catalog_sha256,
                "expected_backlog_sha256": args.expected_backlog_sha256,
                "expected_state_sha256": args.expected_state_sha256,
                "expected_acceptance_sha256": args.expected_acceptance_sha256,
                "expected_workspace_sha256": args.expected_workspace_sha256,
                "expected_state_updated_at": args.expected_state_updated_at,
            }
            missing = [name.replace("_", "-") for name, value in required.items() if not value]
            if missing:
                raise CatalogRepairError("Apply requires preview values: " + ", ".join(missing) + ".")
            result = apply_repair(**common, **required)
        else:
            result = plan_repair(**common)
    except (CatalogRepairError, OSError) as exc:
        print(f"AIM catalog repair blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
