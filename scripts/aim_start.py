#!/usr/bin/env python3
"""Plan and publish one Portfolio-visible AIM Epic start.

The helper owns data safety only. It cannot approve a Gate, run an agent,
migrate an existing workspace, or make legacy state authoritative.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable


PORTFOLIO_FILE = "ui-portfolio.json"
PORTFOLIO_VERSION = "1.0"
MAX_PORTFOLIO_BYTES = 1_000_000
MAX_STATE_BYTES = 1_000_000
EPIC_ID_PATTERN = re.compile(r"EPIC-[A-Z0-9-]+")
INCREMENT_ID_PATTERN = re.compile(r"DI-[0-9]+")
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


class AimStartError(ValueError):
    """A bounded operator-facing Portfolio start error."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _inside_aim(repo_root: Path) -> tuple[Path, Path]:
    root = repo_root.resolve()
    if not root.is_dir():
        raise AimStartError("The repository root is not a directory.")
    aim_root = root / ".aim"
    if aim_root.is_symlink():
        raise AimStartError(".aim must not be a symbolic link.")
    if aim_root.exists() and not aim_root.is_dir():
        raise AimStartError(".aim is not a directory.")
    resolved = aim_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AimStartError(".aim leaves the repository boundary.") from exc
    return root, resolved


def _read_bytes(path: Path, *, maximum: int, label: str) -> bytes:
    if path.is_symlink():
        raise AimStartError(f"{label} must not be a symbolic link.")
    if not path.is_file():
        raise AimStartError(f"Missing {label}.")
    if path.stat().st_size > maximum:
        raise AimStartError(f"{label} is larger than {maximum} bytes.")
    return path.read_bytes()


def _contained_workspace(aim_root: Path, raw: str, index: int) -> Path:
    if raw == ".":
        return aim_root
    if "\\" in raw:
        raise AimStartError(f"Workspace {index} uses a backslash; use a POSIX path.")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or not relative.parts:
        raise AimStartError(f"Workspace {index} must be relative to .aim.")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise AimStartError(f"Workspace {index} contains a dot or traversal segment.")
    candidate = aim_root.joinpath(*relative.parts)
    current = aim_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AimStartError(f"Workspace {index} crosses symbolic link {raw}.")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(aim_root)
    except ValueError as exc:
        raise AimStartError(f"Workspace {index} leaves .aim.") from exc
    if not resolved.is_dir():
        raise AimStartError(f"Workspace {index} directory was not found: {raw}.")
    return resolved


def _catalog(aim_root: Path) -> tuple[dict[str, Any], bytes, list[tuple[str, Path]]]:
    path = aim_root / PORTFOLIO_FILE
    if not path.exists() and not path.is_symlink():
        # A missing catalog is normal only before runtime work exists. Never
        # hide or silently register earlier work while bootstrapping a board.
        evidence = any((aim_root / name).exists() or (aim_root / name).is_symlink()
                       for name in ("state.json", "epic.md"))
        for name in ("increments", "decisions", "reviews", "portfolio", "workspaces"):
            directory = aim_root / name
            evidence = evidence or directory.is_symlink() or (directory.is_dir() and any(directory.iterdir()))
        if evidence:
            raise AimStartError("Existing runtime work needs a reviewed catalog; it cannot be replaced by a new bootstrap.")
        return {"portfolioVersion": PORTFOLIO_VERSION, "workspaces": []}, b"", []
    payload = _read_bytes(
        path, maximum=MAX_PORTFOLIO_BYTES, label=PORTFOLIO_FILE
    )
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AimStartError(
            f"{PORTFOLIO_FILE} contains invalid JSON at line {exc.lineno}."
        ) from exc
    if not isinstance(value, dict) or set(value) != {"portfolioVersion", "workspaces"}:
        raise AimStartError(
            f"{PORTFOLIO_FILE} must contain only portfolioVersion and workspaces."
        )
    if value.get("portfolioVersion") != PORTFOLIO_VERSION:
        raise AimStartError(
            f"{PORTFOLIO_FILE} must declare portfolioVersion {PORTFOLIO_VERSION}."
        )
    items = value.get("workspaces")
    if not isinstance(items, list) or not items:
        raise AimStartError(f"{PORTFOLIO_FILE} must contain at least one workspace.")
    resolved: list[tuple[str, Path]] = []
    seen_raw: set[str] = set()
    seen_paths: set[Path] = set()
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or set(item) != {"path"}:
            raise AimStartError(f"Workspace {index} must contain only path.")
        raw = item.get("path")
        if not isinstance(raw, str) or not raw or len(raw) > 500:
            raise AimStartError(f"Workspace {index} has an invalid path.")
        candidate = _contained_workspace(aim_root, raw, index)
        if raw in seen_raw or candidate in seen_paths:
            raise AimStartError(f"Workspace {index} duplicates an earlier path.")
        seen_raw.add(raw)
        seen_paths.add(candidate)
        resolved.append((raw, candidate))
    return value, payload, resolved


def _read_state(workspace: Path) -> dict[str, Any] | None:
    path = workspace / "state.json"
    if not path.exists():
        return None
    payload = _read_bytes(path, maximum=MAX_STATE_BYTES, label=str(path))
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AimStartError(f"{path} contains invalid JSON at line {exc.lineno}.") from exc
    if not isinstance(value, dict):
        raise AimStartError(f"{path} must contain a JSON object.")
    return value


def _validate_declared_state(raw: str, state: dict[str, Any]) -> None:
    """Reject a catalog checkpoint that is not current start authority."""

    missing = sorted(REQUIRED_STATE_FIELDS.difference(state))
    if missing:
        raise AimStartError(
            f"Declared workspace {raw} is missing required runtime fields: "
            + ", ".join(missing)
            + "."
        )
    epic_id = state.get("epicId")
    if not isinstance(epic_id, str) or EPIC_ID_PATTERN.fullmatch(epic_id) is None:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical Epic identity.")
    if state.get("stateSchemaVersion") != "1.0":
        raise AimStartError(
            f"Declared workspace {raw} is not current stateSchemaVersion 1.0."
        )
    if state.get("epicStatus") not in CURRENT_STATUSES:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical Epic status.")
    if state.get("currentRole") not in CURRENT_ROLES:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical current role.")
    if state.get("lastGatePassed") not in CURRENT_GATES:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical Gate checkpoint.")
    if state.get("mode") not in {"Strict", "Auto"}:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical AIM mode.")
    if state.get("costProfile") not in {"Standard", "Cost Control", "Deep"}:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical cost profile.")
    updated_at = state.get("updatedAt")
    if not isinstance(updated_at, str) or TIMESTAMP_PATTERN.fullmatch(updated_at) is None:
        raise AimStartError(f"Declared workspace {raw} has a non-canonical timestamp.")
    try:
        datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise AimStartError(
            f"Declared workspace {raw} has an impossible runtime timestamp."
        ) from exc
    if not isinstance(state.get("aimVersion"), str) or not state["aimVersion"]:
        raise AimStartError(f"Declared workspace {raw} has no AIM version.")
    if not isinstance(state.get("platform"), str) or not state["platform"]:
        raise AimStartError(f"Declared workspace {raw} has no platform identity.")
    if not isinstance(state.get("commitMode"), str) or not state["commitMode"]:
        raise AimStartError(f"Declared workspace {raw} has no commit mode.")
    parallel = state.get("parallelSupport")
    if (
        not isinstance(parallel, dict)
        or not {"available", "enabled", "policy"}.issubset(parallel)
        or not isinstance(parallel.get("available"), bool)
        or not isinstance(parallel.get("enabled"), bool)
        or not isinstance(parallel.get("policy"), str)
        or not parallel["policy"]
    ):
        raise AimStartError(f"Declared workspace {raw} has invalid parallel support.")
    for field in ("activeIncrementId", "plannedIncrementId", "previousIncrementId"):
        identifier = state.get(field)
        if identifier is not None and (
            not isinstance(identifier, str)
            or INCREMENT_ID_PATTERN.fullmatch(identifier) is None
        ):
            raise AimStartError(
                f"Declared workspace {raw} has a non-canonical {field}."
            )


def _portfolio_parent(aim_root: Path) -> Path:
    parent = aim_root / "portfolio"
    if parent.is_symlink():
        raise AimStartError(".aim/portfolio must not be a symbolic link.")
    if parent.exists() and not parent.is_dir():
        raise AimStartError(".aim/portfolio is not a directory.")
    if parent.exists():
        try:
            parent.resolve().relative_to(aim_root)
        except ValueError as exc:
            raise AimStartError(".aim/portfolio leaves the .aim boundary.") from exc
    return parent


def _allocated_increment_ids(workspace: Path, state: dict[str, Any]) -> set[str]:
    identifiers = {
        value
        for key in ("activeIncrementId", "plannedIncrementId", "previousIncrementId")
        if isinstance((value := state.get(key)), str)
        and INCREMENT_ID_PATTERN.fullmatch(value)
    }
    increments = workspace / "increments"
    if increments.is_dir() and not increments.is_symlink():
        for path in increments.glob("*.md"):
            if path.is_symlink() or not path.is_file():
                continue
            match = re.search(r"\bDI-[0-9]+\b", path.read_text(encoding="utf-8", errors="replace")[:300])
            if match:
                identifiers.add(match.group(0))
    return identifiers


def _validate_request(
    epic_id: str,
    increment_id: str,
    title: str,
    mode: str,
    cost_profile: str,
    updated_at: str,
    platform: str,
) -> None:
    if EPIC_ID_PATTERN.fullmatch(epic_id) is None or len(epic_id) > 120:
        raise AimStartError("epic-id must be a bounded canonical EPIC-* identity.")
    if INCREMENT_ID_PATTERN.fullmatch(increment_id) is None or len(increment_id) > 32:
        raise AimStartError("increment-id must be a bounded canonical DI-* identity.")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 240:
        raise AimStartError("title must contain 1 to 240 characters.")
    if mode not in {"Strict", "Auto"}:
        raise AimStartError("mode must be Strict or Auto.")
    if cost_profile not in {"Standard", "Cost Control", "Deep"}:
        raise AimStartError("cost-profile is unsupported.")
    if TIMESTAMP_PATTERN.fullmatch(updated_at) is None:
        raise AimStartError("updated-at must be a second-precision UTC timestamp.")
    try:
        datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise AimStartError("updated-at must be a real UTC calendar timestamp.") from exc
    if not isinstance(platform, str) or not 1 <= len(platform.strip()) <= 64:
        raise AimStartError("platform must contain 1 to 64 characters.")


def plan_start(
    repo_root: Path,
    *,
    epic_id: str,
    increment_id: str,
    title: str,
    mode: str,
    cost_profile: str,
    updated_at: str,
    platform: str = "codex",
    candidate_id: str | None = None,
) -> dict[str, Any]:
    """Build a no-write Portfolio start plan, including first-run bootstrap."""

    _validate_request(
        epic_id, increment_id, title, mode, cost_profile, updated_at, platform
    )
    from aim_activation import activation_preflight

    admission = activation_preflight(repo_root, epic_id=epic_id, candidate_id=candidate_id)
    if not admission["allowed"]:
        raise AimStartError(admission["message"])
    root, aim_root = _inside_aim(repo_root)
    catalog, payload, declared = _catalog(aim_root)
    relative_workspace = f"portfolio/{epic_id}"
    final_workspace = aim_root / "portfolio" / epic_id
    if final_workspace.exists() or final_workspace.is_symlink():
        raise AimStartError(f"Workspace collision at .aim/{relative_workspace}.")
    _portfolio_parent(aim_root)

    seen_epics: dict[str, str] = {}
    seen_increments: dict[str, str] = {}
    for raw, workspace in declared:
        state = _read_state(workspace)
        if state is None:
            raise AimStartError(
                f"Declared workspace {raw} has no state.json; repair the catalog first."
            )
        _validate_declared_state(raw, state)
        existing_epic = state["epicId"]
        if existing_epic in seen_epics:
            raise AimStartError(
                f"Epic identity {existing_epic} is duplicated in {seen_epics[existing_epic]} and {raw}."
            )
        seen_epics[existing_epic] = raw
        if state.get("epicId") == epic_id:
            raise AimStartError(f"Epic identity {epic_id} is already allocated in {raw}.")
        allocated = _allocated_increment_ids(workspace, state)
        for existing_increment in allocated:
            if existing_increment in seen_increments:
                raise AimStartError(
                    f"Increment identity {existing_increment} is duplicated in "
                    f"{seen_increments[existing_increment]} and {raw}."
                )
            seen_increments[existing_increment] = raw
        if increment_id in allocated:
            raise AimStartError(
                f"Increment identity {increment_id} is already allocated in {raw}."
            )

    links = _start_links(root, candidate_id, epic_id, increment_id, updated_at)
    plan = {
        "result": "planned",
        "repo": str(root),
        "portfolio": f".aim/{PORTFOLIO_FILE}",
        "catalogSha256": _sha256(payload),
        "bootstrapCatalog": not payload,
        "candidateId": candidate_id,
        "links": links,
        "epicId": epic_id,
        "plannedIncrementId": increment_id,
        "workspace": relative_workspace,
        "mode": mode,
        "costProfile": cost_profile,
        "updatedAt": updated_at,
        "writes": [
            f".aim/{relative_workspace}/epic.md",
            f".aim/{relative_workspace}/state.json",
            f".aim/{relative_workspace}/increments/{increment_id.removeprefix('DI-')}-plan.md",
            f".aim/{PORTFOLIO_FILE}",
        ],
    }
    if links is not None:
        plan["writes"].append(".aim/portfolio-backlog.json")
        if links["run"] is not None:
            plan["writes"].append(".aim/portfolio-run.json")
    plan["startSha256"] = _sha256(_json_bytes({**plan, "title": title, "platform": platform}))
    # Validate the generated state with the packaged, dependency-free schema
    # implementation before any repository file or directory is written.
    from aim_runtime_contract import _runtime_state_schema, _schema_issues
    state = json.loads(_workspace_payloads(plan, title, platform)["state.json"])
    issues = _schema_issues(state, _runtime_state_schema(root))
    if issues:
        raise AimStartError("Generated start state is invalid: " + "; ".join(issues))
    return plan


def _start_links(root: Path, candidate_id: str | None, epic_id: str, increment_id: str, updated_at: str) -> dict[str, Any] | None:
    if candidate_id is None:
        return None
    from aim_activation import _read_backlog, _candidate
    from aim_portfolio_run import load_run, PortfolioRunError

    backlog, payload = _read_backlog(root / ".aim")
    candidate = _candidate(backlog, candidate_id, epic_id)
    if any(item.get("runtimeIncrementId") == increment_id for item in backlog["items"]):
        raise AimStartError("The reserved Increment is already linked to a Roadmap candidate.")
    run_path = root / ".aim/portfolio-run.json"
    run = None
    run_digest = None
    if run_path.exists() or run_path.is_symlink():
        try:
            run = load_run(root)
        except PortfolioRunError as exc:
            raise AimStartError(str(exc)) from exc
        if run["status"] != "running" or run.get("activeCandidateId") != candidate_id or run.get("checkpoint", {}).get("epicStatus") != "activation_pending":
            raise AimStartError("Portfolio start must target its selected activation_pending candidate.")
        snapshot = next(item for item in run["snapshot"] if item["candidateId"] == candidate_id)
        if any(candidate.get(key) != snapshot[key] for key in ("epicId", "epicTitle", "title", "priority", "createdAt")):
            raise AimStartError("The selected Roadmap candidate changed since mandate approval.")
        run_digest = _sha256(run_path.read_bytes())
        run["checkpoint"] = {"candidateId": candidate_id, "epicStatus": "gate_a_pending",
                             "gate": "Gate A", "decisionAuthority": "none", "updatedAt": updated_at}
        run["updatedAt"] = updated_at
    candidate["runtimeIncrementId"] = increment_id
    backlog["updatedAt"] = updated_at
    return {"backlog": backlog, "backlogSha256": _sha256(payload), "run": run, "runSha256": run_digest}


def _atomic_write(path: Path, payload: bytes, prefix: str) -> None:
    if path.is_symlink():
        raise AimStartError(f"{path.name} must not be a symbolic link.")
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


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _workspace_payloads(plan: dict[str, Any], title: str, platform: str) -> dict[str, bytes]:
    increment_number = plan["plannedIncrementId"].removeprefix("DI-")
    state = {
        "stateSchemaVersion": "1.0",
        "aimVersion": "2.0",
        "mode": plan["mode"],
        "costProfile": plan["costProfile"],
        "epicId": plan["epicId"],
        "epicStatus": "gate_a_pending",
        "activeIncrementId": None,
        "plannedIncrementId": plan["plannedIncrementId"],
        "currentRole": "PO",
        "lastGatePassed": None,
        "platform": platform,
        "parallelSupport": {
            "available": False,
            "enabled": False,
            "policy": "sequential_fallback",
        },
        "commitMode": "optional",
        "updatedAt": plan["updatedAt"],
        "uiDecision": {
            "visibility": "preparing",
            "gate": "Gate A",
            "targetId": plan["epicId"],
        },
    }
    if plan.get("candidateId"):
        state["portfolioCandidateId"] = plan["candidateId"]
    epic = (
        f"# {plan['epicId']} — {title.strip()}\n\n"
        "Role: PO\n\n"
        f"Mode: {plan['mode']}\n\n"
        f"Cost profile: {plan['costProfile']}\n\n"
        "## Status\n\nGate A pending. No implementation has started.\n"
    ).encode("utf-8")
    increment = (
        f"# {plan['plannedIncrementId']} — Initial Done Increment\n\n"
        f"Epic: {plan['epicId']}\n\n"
        "Status: Identity reserved by Portfolio-aware start. Gate B defines and "
        "approves the delivery scope.\n"
    ).encode("utf-8")
    return {
        "state.json": _json_bytes(state),
        "epic.md": epic,
        f"increments/{increment_number}-plan.md": increment,
    }


def _verify_board(repo_root: Path, plan: dict[str, Any], *, ready: bool) -> None:
    from aim_ui import build_board

    board = build_board(repo_root)
    matches = [item for item in board["epics"] if item["id"] == plan["epicId"]]
    if len(matches) != 1:
        raise AimStartError(
            f"AIM UI projection did not contain exactly one {plan['epicId']}."
        )
    epic = matches[0]
    if epic.get("workspace") != plan["workspace"]:
        raise AimStartError("AIM UI projected the new Epic from the wrong workspace.")
    if epic.get("runtimeStatus") != "gate_a_pending":
        raise AimStartError("AIM UI did not project the new Epic at Gate A.")
    increments = [
        item for item in epic.get("increments", [])
        if item.get("id") == plan["plannedIncrementId"]
    ]
    if len(increments) != 1 or increments[0].get("runtimeStatus") != "gate_a_pending":
        raise AimStartError("AIM UI did not project the reserved DI identity at Gate A.")
    if plan.get("candidateId"):
        if epic.get("portfolioCandidateId") != plan["candidateId"] or increments[0].get("portfolioCandidateId") != plan["candidateId"]:
            raise AimStartError("The new workspace and Roadmap candidate are not linked on the board.")
        if plan["links"]["run"] is not None and board["portfolioRun"].get("relationStatus") != "consistent":
            raise AimStartError("The new workspace and Portfolio checkpoint do not agree.")
    if ready:
        state_path = repo_root / ".aim" / plan["workspace"] / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("uiDecision", {}).get("visibility") != "ready":
            raise AimStartError("The new workspace did not retain the ready Gate A handoff.")


def apply_start(
    repo_root: Path,
    *,
    epic_id: str,
    increment_id: str,
    title: str,
    mode: str,
    cost_profile: str,
    updated_at: str,
    platform: str = "codex",
    expected_catalog_sha256: str | None = None,
    candidate_id: str | None = None,
    expected_start_sha256: str | None = None,
    fault_at: str | None = None,
    fault_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Publish one new workspace and catalog entry, rolling back bounded failures."""

    plan = plan_start(
        repo_root,
        epic_id=epic_id,
        increment_id=increment_id,
        title=title,
        mode=mode,
        cost_profile=cost_profile,
        updated_at=updated_at,
        platform=platform,
        candidate_id=candidate_id,
    )
    if candidate_id is not None and expected_start_sha256 != plan["startSha256"]:
        raise AimStartError("Start inputs changed or preview is missing; preview again before applying.")
    if expected_start_sha256 is not None and expected_start_sha256 != plan["startSha256"]:
        raise AimStartError("Start inputs changed since preview; nothing was written.")
    if expected_catalog_sha256 is not None and plan["catalogSha256"] != expected_catalog_sha256:
        raise AimStartError("Portfolio catalog changed since preview; reload before applying.")
    root, aim_root = _inside_aim(repo_root)
    catalog_path = aim_root / PORTFOLIO_FILE
    _, original_catalog, _ = _catalog(aim_root)
    if _sha256(original_catalog) != plan["catalogSha256"]:
        raise AimStartError("Portfolio catalog changed before staging; no files were written.")

    created_aim_root = not aim_root.exists()
    if created_aim_root:
        aim_root.mkdir()
    staging = Path(tempfile.mkdtemp(prefix=f".{epic_id}.start-", dir=aim_root))
    final = aim_root / plan["workspace"]
    portfolio_root = _portfolio_parent(aim_root)
    created_portfolio_root = False
    workspace_published = False
    catalog_published = False
    original_links: dict[Path, bytes] = {}
    written_links: list[Path] = []

    def checkpoint(name: str) -> None:
        if fault_hook is not None:
            fault_hook(name)
        if fault_at == name:
            raise AimStartError(f"Injected failure at {name}.")

    try:
        payloads = _workspace_payloads(plan, title, platform)
        for relative, payload in payloads.items():
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        (staging / "decisions").mkdir()
        (staging / "reviews").mkdir()
        checkpoint("after_staging")

        if plan["bootstrapCatalog"]:
            if catalog_path.exists() or catalog_path.is_symlink():
                raise AimStartError("Portfolio catalog appeared during staging; no files were published.")
            current_catalog = b""
        else:
            current_catalog = _read_bytes(catalog_path, maximum=MAX_PORTFOLIO_BYTES, label=PORTFOLIO_FILE)
        # Recheck admission, capacity, and any Roadmap/mandate bindings at the
        # publication boundary. Ignore only this transaction's staging folder.
        current_plan = plan_start(root, epic_id=epic_id, increment_id=increment_id,
                                  title=title, mode=mode, cost_profile=cost_profile,
                                  updated_at=updated_at, platform=platform, candidate_id=candidate_id)
        if current_plan["startSha256"] != plan["startSha256"]:
            raise AimStartError("Start inputs changed during staging; no files were published.")
        if current_catalog != original_catalog:
            raise AimStartError("Portfolio catalog changed during staging; no files were published.")
        if final.exists() or final.is_symlink():
            raise AimStartError("Workspace appeared during staging; no files were published.")

        portfolio_root = _portfolio_parent(aim_root)
        if not portfolio_root.exists():
            portfolio_root.mkdir()
            created_portfolio_root = True
        portfolio_root = _portfolio_parent(aim_root)
        if final.parent != portfolio_root:
            raise AimStartError("Portfolio publication target changed after preview.")
        os.replace(staging, final)
        workspace_published = True
        checkpoint("after_workspace_publish")

        catalog = json.loads(original_catalog) if original_catalog else {"portfolioVersion": PORTFOLIO_VERSION, "workspaces": []}
        catalog["workspaces"].append({"path": plan["workspace"]})
        _atomic_write(catalog_path, _json_bytes(catalog), ".ui-portfolio.start.")
        catalog_published = True
        checkpoint("after_catalog_publish")

        if plan["links"] is not None:
            for name, key in (("portfolio-backlog.json", "backlog"), ("portfolio-run.json", "run")):
                value = plan["links"][key]
                if value is None:
                    continue
                path = aim_root / name
                original_links[path] = _read_bytes(path, maximum=1_000_000, label=name)
                if _sha256(original_links[path]) != plan["links"][f"{key}Sha256"]:
                    raise AimStartError(f"{name} changed before publication.")
                _atomic_write(path, _json_bytes(value), ".start-link.")
                written_links.append(path)
                checkpoint(f"after_{key}_publish")
        _verify_board(root, plan, ready=False)
        state_path = final / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["uiDecision"]["visibility"] = "ready"
        _atomic_write(state_path, _json_bytes(state), ".state.start.")
        checkpoint("after_ready_publish")
        _verify_board(root, plan, ready=True)
    except Exception as start_error:
        rollback_errors: list[str] = []
        for path in reversed(written_links):
            try:
                _atomic_write(path, original_links[path], ".start-link.rollback.")
            except Exception as exc:
                rollback_errors.append(f"{path.name} restore failed: {exc}")
        if catalog_published:
            try:
                if original_catalog:
                    _atomic_write(catalog_path, original_catalog, ".ui-portfolio.rollback.")
                else:
                    catalog_path.unlink()
            except Exception as exc:
                rollback_errors.append(f"catalog restore failed: {exc}")
        if workspace_published and final.is_dir() and not final.is_symlink():
            try:
                shutil.rmtree(final)
            except Exception as exc:
                rollback_errors.append(f"workspace removal failed: {exc}")
        if staging.is_dir() and not staging.is_symlink():
            try:
                shutil.rmtree(staging)
            except Exception as exc:
                rollback_errors.append(f"staging removal failed: {exc}")
        if created_portfolio_root:
            try:
                portfolio_root.rmdir()
            except OSError:
                pass
        if created_aim_root:
            try:
                aim_root.rmdir()
            except OSError:
                pass
        if rollback_errors:
            raise AimStartError(
                f"Start failed ({start_error}); rollback needs operator attention: "
                + "; ".join(rollback_errors)
            ) from start_error
        raise

    result = dict(plan)
    result.update({"result": "applied", "visibleOnBoard": True, "gateAReady": True})
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or apply one transaction-safe Portfolio-aware AIM start."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--epic-id", required=True)
    parser.add_argument("--increment-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mode", choices=("Strict", "Auto"), default="Strict")
    parser.add_argument(
        "--cost-profile",
        choices=("Standard", "Cost Control", "Deep"),
        default="Standard",
    )
    parser.add_argument("--updated-at", required=True)
    parser.add_argument("--platform", default="codex")
    parser.add_argument("--expected-catalog-sha256")
    parser.add_argument("--candidate-id")
    parser.add_argument("--expected-start-sha256")
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        common = {
            "epic_id": args.epic_id,
            "increment_id": args.increment_id,
            "title": args.title,
            "mode": args.mode,
            "cost_profile": args.cost_profile,
            "updated_at": args.updated_at,
            "platform": args.platform,
            "candidate_id": args.candidate_id,
        }
        result = (
            apply_start(
                Path(args.repo),
                **common,
                expected_catalog_sha256=args.expected_catalog_sha256,
                expected_start_sha256=args.expected_start_sha256,
            )
            if args.apply
            else plan_start(Path(args.repo), **common)
        )
    except (AimStartError, OSError, json.JSONDecodeError) as exc:
        print(f"AIM start blocked: {exc}", file=os.sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
