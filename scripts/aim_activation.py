"""Shared repository-bound activation preflight for AIM Portfolio work."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Iterable

from aim_portfolio import activation_decision, load_portfolio_control


BACKLOG_FILE = "portfolio-backlog.json"
MAX_BACKLOG_BYTES = 1_000_000
MAX_CATALOG_BYTES = 1_000_000
MAX_STATE_BYTES = 1_000_000
CANDIDATE_PATTERN = re.compile(r"INC-[A-Z0-9-]+")
EPIC_PATTERN = re.compile(r"EPIC-[A-Z0-9-]+")
INCREMENT_PATTERN = re.compile(r"DI-[0-9]+")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
)
CURRENT_STATUSES = {
    "epic_initialized",
    "gate_a_pending",
    "gate_b_pending",
    "increment_in_progress",
    "review_in_progress",
    "tdo_validation_in_progress",
    "po_approval_pending",
    "done_increment_accepted",
    "epic_paused",
    "blocked",
    "epic_complete",
}
CURRENT_GATES = {None, "Gate A", "Gate B", "Gate C", "Gate D", "Gate E"}
CURRENT_ROLES = {"PO", "TDO", "Dev", "Reviewer"}
REQUIRED_STATE_FIELDS = {
    "stateSchemaVersion",
    "aimVersion",
    "mode",
    "costProfile",
    "epicId",
    "epicStatus",
    "activeIncrementId",
    "currentRole",
    "lastGatePassed",
    "platform",
    "parallelSupport",
    "commitMode",
    "updatedAt",
}


class ActivationPreflightError(ValueError):
    """A bounded operator-facing activation input error."""


def _inside_aim(repo_root: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    aim_root = root / ".aim"
    if aim_root.is_symlink() or not aim_root.is_dir():
        raise ActivationPreflightError("Activation requires a contained .aim directory.")
    resolved = aim_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ActivationPreflightError(".aim leaves the repository boundary.") from exc
    return root, resolved


def _read_bytes(path: Path, *, maximum: int, label: str) -> bytes:
    if path.is_symlink():
        raise ActivationPreflightError(f"{label} must not be a symbolic link.")
    if not path.is_file():
        raise ActivationPreflightError(f"Missing {label}.")
    if path.stat().st_size > maximum:
        raise ActivationPreflightError(f"{label} is larger than {maximum} bytes.")
    return path.read_bytes()


def _contained_workspace(aim_root: Path, raw: str, index: int) -> Path:
    if raw == ".":
        return aim_root
    if "\\" in raw:
        raise ActivationPreflightError(
            f"Workspace {index} uses a backslash; use a POSIX path."
        )
    relative = PurePosixPath(raw)
    if relative.is_absolute() or not relative.parts:
        raise ActivationPreflightError(f"Workspace {index} must be relative to .aim.")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise ActivationPreflightError(
            f"Workspace {index} contains a dot or traversal segment."
        )
    candidate = aim_root.joinpath(*relative.parts)
    current = aim_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ActivationPreflightError(
                f"Workspace {index} crosses symbolic link {raw}."
            )
    resolved = candidate.resolve()
    try:
        resolved.relative_to(aim_root)
    except ValueError as exc:
        raise ActivationPreflightError(f"Workspace {index} leaves .aim.") from exc
    if not resolved.is_dir():
        raise ActivationPreflightError(
            f"Workspace {index} directory was not found: {raw}."
        )
    return resolved


def _catalog(aim_root: Path) -> tuple[dict[str, Any], bytes, list[tuple[str, Path]]]:
    payload = _read_bytes(
        aim_root / "ui-portfolio.json",
        maximum=MAX_CATALOG_BYTES,
        label="ui-portfolio.json",
    )
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ActivationPreflightError(
            f"ui-portfolio.json contains invalid JSON at line {exc.lineno}."
        ) from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"portfolioVersion", "workspaces"}
        or value.get("portfolioVersion") != "1.0"
        or not isinstance(value.get("workspaces"), list)
        or not value["workspaces"]
    ):
        raise ActivationPreflightError("ui-portfolio.json is not a supported catalog.")
    declared: list[tuple[str, Path]] = []
    seen_raw: set[str] = set()
    seen_paths: set[Path] = set()
    for index, item in enumerate(value["workspaces"], 1):
        if not isinstance(item, dict) or set(item) != {"path"}:
            raise ActivationPreflightError(f"Workspace {index} must contain only path.")
        raw = item.get("path")
        if not isinstance(raw, str) or not raw or len(raw) > 500:
            raise ActivationPreflightError(f"Workspace {index} has an invalid path.")
        workspace = _contained_workspace(aim_root, raw, index)
        if raw in seen_raw or workspace in seen_paths:
            raise ActivationPreflightError(
                f"Workspace {index} duplicates an earlier path."
            )
        seen_raw.add(raw)
        seen_paths.add(workspace)
        declared.append((raw, workspace))
    return value, payload, declared


def _read_state(workspace: Path) -> dict[str, Any] | None:
    path = workspace / "state.json"
    if not path.exists():
        return None
    payload = _read_bytes(path, maximum=MAX_STATE_BYTES, label=str(path))
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ActivationPreflightError(
            f"{path} contains invalid JSON at line {exc.lineno}."
        ) from exc
    if not isinstance(value, dict):
        raise ActivationPreflightError(f"{path} must contain a JSON object.")
    return value


def _validate_declared_state(raw: str, state: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_STATE_FIELDS.difference(state))
    if missing:
        raise ActivationPreflightError(
            f"Declared workspace {raw} is missing required runtime fields: "
            + ", ".join(missing)
            + "."
        )
    if state.get("stateSchemaVersion") != "1.0":
        raise ActivationPreflightError(
            f"Declared workspace {raw} is not current stateSchemaVersion 1.0."
        )
    if not isinstance(state.get("epicId"), str) or EPIC_PATTERN.fullmatch(state["epicId"]) is None:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical Epic identity."
        )
    if state.get("epicStatus") not in CURRENT_STATUSES:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical Epic status."
        )
    if state.get("currentRole") not in CURRENT_ROLES:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical current role."
        )
    if state.get("lastGatePassed") not in CURRENT_GATES:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical Gate checkpoint."
        )
    if state.get("mode") not in {"Strict", "Auto"}:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical AIM mode."
        )
    if state.get("costProfile") not in {"Standard", "Cost Control", "Deep"}:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical cost profile."
        )
    if not isinstance(state.get("aimVersion"), str) or not state["aimVersion"]:
        raise ActivationPreflightError(f"Declared workspace {raw} has no AIM version.")
    if not isinstance(state.get("platform"), str) or not state["platform"]:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has no platform identity."
        )
    if not isinstance(state.get("commitMode"), str) or not state["commitMode"]:
        raise ActivationPreflightError(f"Declared workspace {raw} has no commit mode.")
    parallel = state.get("parallelSupport")
    if (
        not isinstance(parallel, dict)
        or not {"available", "enabled", "policy"}.issubset(parallel)
        or not isinstance(parallel.get("available"), bool)
        or not isinstance(parallel.get("enabled"), bool)
        or not isinstance(parallel.get("policy"), str)
        or not parallel["policy"]
    ):
        raise ActivationPreflightError(
            f"Declared workspace {raw} has invalid parallel support."
        )
    for field in ("activeIncrementId", "plannedIncrementId", "previousIncrementId"):
        identifier = state.get(field)
        if identifier is not None and (
            not isinstance(identifier, str)
            or INCREMENT_PATTERN.fullmatch(identifier) is None
        ):
            raise ActivationPreflightError(
                f"Declared workspace {raw} has a non-canonical {field}."
            )
    updated_at = state.get("updatedAt")
    if not isinstance(updated_at, str) or TIMESTAMP_PATTERN.fullmatch(updated_at) is None:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has a non-canonical timestamp."
        )
    try:
        datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ActivationPreflightError(
            f"Declared workspace {raw} has an impossible runtime timestamp."
        ) from exc


def _portfolio_parent(aim_root: Path) -> Path:
    parent = aim_root / "portfolio"
    if parent.is_symlink():
        raise ActivationPreflightError(".aim/portfolio must not be a symbolic link.")
    if parent.exists() and not parent.is_dir():
        raise ActivationPreflightError(".aim/portfolio is not a directory.")
    if parent.exists():
        try:
            parent.resolve().relative_to(aim_root)
        except ValueError as exc:
            raise ActivationPreflightError(
                ".aim/portfolio leaves the .aim boundary."
            ) from exc
    return parent


def _blocked(code: str, message: str) -> dict[str, Any]:
    return {"allowed": False, "code": code, "message": message}


def _read_backlog(aim_root: Path) -> tuple[dict[str, Any], bytes]:
    path = aim_root / BACKLOG_FILE
    if path.is_symlink():
        raise ActivationPreflightError(f"{BACKLOG_FILE} must not be a symbolic link.")
    if not path.is_file():
        raise ActivationPreflightError(f"Missing {BACKLOG_FILE}.")
    if path.stat().st_size > MAX_BACKLOG_BYTES:
        raise ActivationPreflightError(f"{BACKLOG_FILE} is larger than {MAX_BACKLOG_BYTES} bytes.")
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ActivationPreflightError(
            f"{BACKLOG_FILE} contains invalid JSON at line {exc.lineno}."
        ) from exc
    if (
        not isinstance(value, dict)
        or value.get("backlogVersion") != "1.0"
        or not isinstance(value.get("updatedAt"), str)
        or not value["updatedAt"].strip()
        or not isinstance(value.get("items"), list)
    ):
        raise ActivationPreflightError(f"{BACKLOG_FILE} is not a supported Backlog contract.")
    return value, payload


def _candidate(
    backlog: dict[str, Any], candidate_id: str, epic_id: str
) -> dict[str, Any]:
    if CANDIDATE_PATTERN.fullmatch(candidate_id) is None or len(candidate_id) > 80:
        raise ActivationPreflightError("Candidate identity is not a bounded canonical INC-* id.")
    matches = [
        item
        for item in backlog["items"]
        if isinstance(item, dict) and item.get("id") == candidate_id
    ]
    if len(matches) != 1:
        raise ActivationPreflightError(
            f"Backlog candidate {candidate_id} must appear exactly once before activation."
        )
    candidate = matches[0]
    if candidate.get("epicId") != epic_id:
        raise ActivationPreflightError(
            f"Backlog candidate {candidate_id} no longer targets Epic {epic_id}."
        )
    if candidate.get("runtimeIncrementId") is not None:
        raise ActivationPreflightError(
            f"Backlog candidate {candidate_id} already has runtime authority and cannot be replayed."
        )
    return candidate


def activation_preflight(
    repo_root: Path,
    *,
    epic_id: str,
    candidate_id: str | None = None,
    expected_backlog_updated_at: str | None = None,
    expected_candidate_updated_at: str | None = None,
    expected_catalog_sha256: str | None = None,
    expected_backlog_sha256: str | None = None,
) -> dict[str, Any]:
    """Return one stable, read-only admission result for a new Epic runtime."""

    if EPIC_PATTERN.fullmatch(epic_id) is None or len(epic_id) > 120:
        return _blocked("identity_invalid", "Epic identity is not a bounded canonical EPIC-* id.")
    try:
        root, aim_root = _inside_aim(repo_root)
        catalog_path = aim_root / "ui-portfolio.json"
        if catalog_path.exists() or catalog_path.is_symlink():
            catalog, catalog_payload, declared = _catalog(aim_root)
            catalog_sha: str | None = hashlib.sha256(catalog_payload).hexdigest()
        else:
            catalog = {"portfolioVersion": "1.0", "workspaces": []}
            declared = []
            catalog_sha = None
        if expected_catalog_sha256 is not None and catalog_sha != expected_catalog_sha256:
            return _blocked(
                "catalog_stale",
                "Portfolio catalog changed since activation preflight; reload before writing.",
            )
        allocated: dict[str, str] = {}
        running: list[str] = []
        for raw, workspace in declared:
            state = _read_state(workspace)
            if state is None:
                return _blocked(
                    "catalog_invalid",
                    f"Declared workspace {raw} has no state.json; repair the catalog first.",
                )
            _validate_declared_state(raw, state)
            existing_epic = state["epicId"]
            if existing_epic in allocated:
                return _blocked(
                    "identity_ambiguous",
                    f"Epic identity {existing_epic} is duplicated in {allocated[existing_epic]} and {raw}.",
                )
            allocated[existing_epic] = raw
            if state["epicStatus"] != "epic_complete":
                running.append(existing_epic)

        if epic_id in allocated:
            return _blocked(
                "epic_allocated",
                f"Epic identity {epic_id} is already allocated in {allocated[epic_id]}.",
            )

        portfolio_parent = _portfolio_parent(aim_root)
        target = portfolio_parent / epic_id
        if target.exists() or target.is_symlink():
            return _blocked(
                "workspace_collision",
                f"Workspace collision at .aim/portfolio/{epic_id}.",
            )

        control = load_portfolio_control(aim_root)
        admission = activation_decision(control, running, epic_id)
        if not admission["allowed"]:
            return _blocked(str(admission["reason"]), str(admission["message"]))

        result: dict[str, Any] = {
            "allowed": True,
            "code": str(admission["reason"]),
            "message": str(admission["message"]),
            "repo": str(root),
            "catalogSha256": catalog_sha,
            "runningEpicIds": sorted(running),
        }
        if candidate_id is not None:
            backlog, backlog_payload = _read_backlog(aim_root)
            backlog_sha = hashlib.sha256(backlog_payload).hexdigest()
            if expected_backlog_sha256 is not None and backlog_sha != expected_backlog_sha256:
                return _blocked(
                    "backlog_stale",
                    "Portfolio Backlog changed since activation preflight; reload before writing.",
                )
            backlog_updated_at = backlog["updatedAt"].strip()
            if (
                expected_backlog_updated_at is not None
                and backlog_updated_at != expected_backlog_updated_at
            ):
                return _blocked(
                    "backlog_stale",
                    "Portfolio Backlog timestamp changed since activation preflight.",
                )
            candidate = _candidate(backlog, candidate_id, epic_id)
            candidate_updated_at = candidate.get("updatedAt", candidate.get("createdAt"))
            if (
                expected_candidate_updated_at is not None
                and candidate_updated_at != expected_candidate_updated_at
            ):
                return _blocked(
                    "candidate_stale",
                    f"Backlog candidate {candidate_id} changed since activation preflight.",
                )
            result.update(
                {
                    "candidateId": candidate_id,
                    "backlogUpdatedAt": backlog_updated_at,
                    "backlogSha256": backlog_sha,
                    "candidateUpdatedAt": candidate_updated_at,
                }
            )
        return result
    except (ActivationPreflightError, OSError) as exc:
        return _blocked("repository_invalid", str(exc))


def candidate_preflights(
    repo_root: Path,
    candidates: Iterable[dict[str, Any]],
    *,
    backlog_updated_at: str,
) -> dict[str, dict[str, Any]]:
    """Evaluate normalized Backlog candidates through the same repository boundary."""

    results: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = candidate.get("id", candidate.get("candidateId"))
        if not isinstance(candidate_id, str):
            continue
        if candidate.get("runtimeIncrementId") is not None:
            continue
        results[candidate_id] = activation_preflight(
            repo_root,
            epic_id=candidate["epicId"],
            candidate_id=candidate_id,
            expected_backlog_updated_at=backlog_updated_at,
            expected_candidate_updated_at=candidate.get("updatedAt", candidate["createdAt"]),
        )
    return results
