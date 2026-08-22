#!/usr/bin/env python3
"""Validate and checkpoint a chat-owned AIM Portfolio Auto run.

This helper is deliberately data-only. It cannot activate an agent, approve a
Gate, or mutate a canonical Epic workspace; the main AIM chat owns those acts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


RUN_FILE = "portfolio-run.json"
BACKLOG_FILE = "portfolio-backlog.json"
RUN_VERSION = "1.0"
MAX_RUN_BYTES = 1_000_000
RUN_STATUSES = {"running", "paused", "completed", "stopped"}
GATES = {"Gate A", "Gate B", "Gate C", "Gate D", "Gate E", "Epic closure"}
AUTHORITIES = {"portfolio_mandate", "user", "none"}
ALLOWED_FIELDS = {
    "runVersion", "runId", "mode", "status", "mandate", "snapshot",
    "activeCandidateId", "completedCandidateIds", "skippedCandidateIds",
    "checkpoint", "pauseReason", "updatedAt",
}


class PortfolioRunError(ValueError):
    """A safe operator-facing Portfolio run error."""


def _inside_aim(repo_root: Path) -> Path:
    root = repo_root.resolve()
    aim_root = root / ".aim"
    if aim_root.is_symlink():
        raise PortfolioRunError(".aim must not be a symbolic link.")
    if not aim_root.is_dir():
        raise PortfolioRunError("The repository has no .aim directory.")
    return aim_root.resolve()


def _read_object(path: Path, *, maximum: int = MAX_RUN_BYTES) -> dict[str, Any]:
    if path.is_symlink():
        raise PortfolioRunError(f"{path.name} must not be a symbolic link.")
    if not path.is_file():
        raise PortfolioRunError(f"Missing {path.name}.")
    if path.stat().st_size > maximum:
        raise PortfolioRunError(f"{path.name} is larger than {maximum} bytes.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PortfolioRunError(
            f"{path.name} contains invalid JSON at line {exc.lineno}."
        ) from exc
    if not isinstance(value, dict):
        raise PortfolioRunError(f"{path.name} must contain a JSON object.")
    return value


def _snapshot(backlog: dict[str, Any]) -> list[dict[str, Any]]:
    if backlog.get("backlogVersion") != "1.0" or not isinstance(backlog.get("items"), list):
        raise PortfolioRunError("portfolio-backlog.json is not a supported Backlog contract.")
    if not 1 <= len(backlog["items"]) <= 256:
        raise PortfolioRunError("The Backlog must contain 1 to 256 candidates.")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(backlog["items"]):
        if not isinstance(raw, dict):
            raise PortfolioRunError(f"Backlog item {index + 1} must be an object.")
        required = ("id", "epicId", "epicTitle", "title", "priority", "createdAt")
        if any(field not in raw for field in required):
            raise PortfolioRunError(f"Backlog item {index + 1} is missing required fields.")
        candidate_id = raw["id"]
        if not isinstance(candidate_id, str) or re.fullmatch(r"INC-[A-Z0-9-]+", candidate_id) is None:
            raise PortfolioRunError(f"Backlog item {index + 1} has an invalid candidate id.")
        if candidate_id in seen:
            raise PortfolioRunError(f"Backlog contains duplicate candidate {candidate_id}.")
        values = {key: raw[key] for key in ("epicId", "epicTitle", "title", "createdAt")}
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise PortfolioRunError(f"Backlog item {index + 1} has invalid text fields.")
        limits = {"epicId": 120, "epicTitle": 200, "title": 240, "createdAt": 64}
        if len(candidate_id) > 80 or any(len(values[key]) > limit for key, limit in limits.items()):
            raise PortfolioRunError(f"Backlog item {index + 1} exceeds a field limit.")
        priority = raw["priority"]
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
            raise PortfolioRunError(f"Backlog item {index + 1} has invalid priority.")
        seen.add(candidate_id)
        result.append({
            "candidateId": candidate_id,
            "epicId": values["epicId"].strip(),
            "epicTitle": values["epicTitle"].strip(),
            "title": values["title"].strip(),
            "priority": priority,
            "createdAt": values["createdAt"].strip(),
        })
    if not result:
        raise PortfolioRunError("The Backlog contains no candidates to snapshot.")
    return sorted(result, key=lambda item: (item["priority"], item["createdAt"], item["candidateId"]))


def snapshot_hash(snapshot: list[dict[str, Any]]) -> str:
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_run(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return [f"{RUN_FILE} must contain a JSON object."]
    issues: list[str] = []
    extra = sorted(set(value) - ALLOWED_FIELDS)
    if extra:
        issues.append(f"unsupported fields: {', '.join(extra)}")
    if value.get("runVersion") != RUN_VERSION:
        issues.append(f"runVersion must be {RUN_VERSION}")
    if not isinstance(value.get("runId"), str) or len(value.get("runId", "")) > 120 or re.fullmatch(r"PORTFOLIO-[A-Z0-9-]+", value.get("runId", "")) is None:
        issues.append("runId must be a canonical PORTFOLIO-* id")
    if value.get("mode") != "Auto":
        issues.append("mode must be Auto")
    status_value = value.get("status")
    if not isinstance(status_value, str) or status_value not in RUN_STATUSES:
        issues.append("status is unsupported")
    mandate = value.get("mandate")
    if not isinstance(mandate, dict) or set(mandate) != {"id", "approvedAt", "approvedBy", "snapshotHash"}:
        issues.append("mandate has an invalid shape")
    else:
        if not isinstance(mandate["id"], str) or len(mandate["id"]) > 120 or re.fullmatch(r"MANDATE-[A-Z0-9-]+", mandate["id"]) is None:
            issues.append("mandate id is invalid")
        if mandate["approvedBy"] != "user":
            issues.append("mandate must be approved by the user")
        if not isinstance(mandate["approvedAt"], str) or not 1 <= len(mandate["approvedAt"].strip()) <= 64:
            issues.append("mandate approvedAt is invalid")
        if not isinstance(mandate["snapshotHash"], str) or re.fullmatch(r"[a-f0-9]{64}", mandate["snapshotHash"]) is None:
            issues.append("mandate snapshotHash is invalid")
    snapshot = value.get("snapshot")
    ids: list[str] = []
    if not isinstance(snapshot, list) or not 1 <= len(snapshot) <= 256:
        issues.append("snapshot must contain 1 to 256 candidates")
    else:
        expected_fields = {"candidateId", "epicId", "epicTitle", "title", "priority", "createdAt"}
        for index, item in enumerate(snapshot):
            if not isinstance(item, dict) or set(item) != expected_fields:
                issues.append(f"snapshot item {index + 1} has an invalid shape")
                continue
            identifier = item.get("candidateId")
            if not isinstance(identifier, str) or re.fullmatch(r"INC-[A-Z0-9-]+", identifier) is None:
                issues.append(f"snapshot item {index + 1} has an invalid id")
            else:
                ids.append(identifier)
                if len(identifier) > 80:
                    issues.append(f"snapshot item {index + 1} id is too long")
            for field, limit in (("epicId", 120), ("epicTitle", 200), ("title", 240), ("createdAt", 64)):
                text = item.get(field)
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= limit:
                    issues.append(f"snapshot item {index + 1} {field} is invalid")
            priority = item.get("priority")
            if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
                issues.append(f"snapshot item {index + 1} priority is invalid")
        if len(ids) != len(set(ids)):
            issues.append("snapshot candidate ids must be unique")
        if isinstance(mandate, dict) and snapshot_hash(snapshot) != mandate.get("snapshotHash"):
            issues.append("snapshot does not match the approved mandate hash")
    known = set(ids)
    completed = value.get("completedCandidateIds")
    skipped = value.get("skippedCandidateIds")
    valid_collections = True
    for label, collection in (("completedCandidateIds", completed), ("skippedCandidateIds", skipped)):
        if not isinstance(collection, list) or any(not isinstance(item, str) for item in collection):
            issues.append(f"{label} must be an array of candidate ids")
            valid_collections = False
        elif len(collection) != len(set(collection)):
            issues.append(f"{label} must be a unique array")
        elif any(len(item) > 80 or re.fullmatch(r"INC-[A-Z0-9-]+", item) is None for item in collection):
            issues.append(f"{label} contains an invalid candidate id")
        elif any(item not in known for item in collection):
            issues.append(f"{label} contains a candidate outside the snapshot")
    if valid_collections and set(completed) & set(skipped):
        issues.append("completed and skipped candidates must not overlap")
    active = value.get("activeCandidateId")
    if active is not None and (
        not isinstance(active, str)
        or len(active) > 80
        or re.fullmatch(r"INC-[A-Z0-9-]+", active) is None
        or active not in known
    ):
        issues.append("activeCandidateId is outside the snapshot")
    if isinstance(active, str) and isinstance(completed, list) and active in completed:
        issues.append("activeCandidateId is already completed")
    checkpoint = value.get("checkpoint")
    if checkpoint is not None:
        expected = {"candidateId", "epicStatus", "gate", "decisionAuthority", "updatedAt"}
        if not isinstance(checkpoint, dict) or set(checkpoint) != expected:
            issues.append("checkpoint has an invalid shape")
        elif checkpoint.get("candidateId") != active:
            issues.append("checkpoint must belong to the active candidate")
        else:
            epic_status = checkpoint.get("epicStatus")
            checkpoint_updated_at = checkpoint.get("updatedAt")
            if not isinstance(epic_status, str) or not 1 <= len(epic_status.strip()) <= 80:
                issues.append("checkpoint epicStatus is invalid")
            if not isinstance(checkpoint_updated_at, str) or not 1 <= len(checkpoint_updated_at.strip()) <= 64:
                issues.append("checkpoint updatedAt is invalid")
            if not isinstance(checkpoint.get("gate"), str) or checkpoint.get("gate") not in GATES:
                issues.append("checkpoint gate is unsupported")
            if not isinstance(checkpoint.get("decisionAuthority"), str) or checkpoint.get("decisionAuthority") not in AUTHORITIES:
                issues.append("checkpoint decisionAuthority is unsupported")
    status = status_value
    if status == "running" and "pauseReason" in value:
        issues.append("a running Portfolio must not retain pauseReason")
    pause_reason = value.get("pauseReason")
    if status == "paused" and not isinstance(pause_reason, str):
        issues.append("a paused Portfolio requires pauseReason")
    if pause_reason is not None and (not isinstance(pause_reason, str) or not 1 <= len(pause_reason.strip()) <= 1000):
        issues.append("pauseReason is invalid")
    if status == "completed" and active is not None:
        issues.append("a completed Portfolio cannot have an active candidate")
    if status == "completed" and valid_collections and set(completed) | set(skipped) != known:
        issues.append("a completed Portfolio must account for every snapshot candidate")
    if not isinstance(value.get("updatedAt"), str) or not 1 <= len(value.get("updatedAt", "").strip()) <= 64:
        issues.append("updatedAt is invalid")
    return issues


def _write_atomic(path: Path, value: dict[str, Any]) -> None:
    if path.is_symlink():
        raise PortfolioRunError(f"{path.name} must not be a symbolic link.")
    descriptor, temporary = tempfile.mkstemp(prefix=".portfolio-run.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def create_run(repo_root: Path, mandate_id: str, approved_at: str, updated_at: str) -> dict[str, Any]:
    aim_root = _inside_aim(repo_root)
    run_path = aim_root / RUN_FILE
    if run_path.exists() or run_path.is_symlink():
        raise PortfolioRunError(f"{RUN_FILE} already exists; resume, stop, or archive it explicitly.")
    if re.fullmatch(r"MANDATE-[A-Z0-9-]+", mandate_id) is None:
        raise PortfolioRunError("mandate id must be a canonical MANDATE-* id.")
    snapshot = _snapshot(_read_object(aim_root / BACKLOG_FILE))
    digest = snapshot_hash(snapshot)
    value = {
        "runVersion": RUN_VERSION,
        "runId": f"PORTFOLIO-{digest[:12].upper()}",
        "mode": "Auto",
        "status": "running",
        "mandate": {"id": mandate_id, "approvedAt": approved_at, "approvedBy": "user", "snapshotHash": digest},
        "snapshot": snapshot,
        "completedCandidateIds": [],
        "skippedCandidateIds": [],
        "updatedAt": updated_at,
    }
    issues = validate_run(value)
    if issues:
        raise PortfolioRunError("Invalid Portfolio run: " + "; ".join(issues))
    _write_atomic(run_path, value)
    return value


def load_run(repo_root: Path) -> dict[str, Any]:
    value = _read_object(_inside_aim(repo_root) / RUN_FILE)
    issues = validate_run(value)
    if issues:
        raise PortfolioRunError("Invalid Portfolio run: " + "; ".join(issues))
    return value


def _mutate(repo_root: Path, expected_updated_at: str, updated_at: str, change: Any) -> dict[str, Any]:
    aim_root = _inside_aim(repo_root)
    path = aim_root / RUN_FILE
    value = _read_object(path)
    issues = validate_run(value)
    if issues:
        raise PortfolioRunError("Invalid Portfolio run: " + "; ".join(issues))
    if value["updatedAt"] != expected_updated_at:
        raise PortfolioRunError("Portfolio run changed since it was read; reload before writing.")
    changed = change(dict(value))
    changed["updatedAt"] = updated_at
    issues = validate_run(changed)
    if issues:
        raise PortfolioRunError("Invalid Portfolio transition: " + "; ".join(issues))
    _write_atomic(path, changed)
    return changed


def activate_next(repo_root: Path, expected_updated_at: str, updated_at: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "running":
            raise PortfolioRunError("Only a running Portfolio can activate its next candidate.")
        if value.get("activeCandidateId"):
            raise PortfolioRunError("Finish the active candidate before activating another.")
        accounted = set(value["completedCandidateIds"]) | set(value["skippedCandidateIds"])
        next_item = next((item for item in value["snapshot"] if item["candidateId"] not in accounted), None)
        if next_item is None:
            raise PortfolioRunError("No unaccounted candidate remains.")
        value["activeCandidateId"] = next_item["candidateId"]
        value["checkpoint"] = {
            "candidateId": next_item["candidateId"], "epicStatus": "activation_pending",
            "gate": "Gate A", "decisionAuthority": "portfolio_mandate", "updatedAt": updated_at,
        }
        return value
    return _mutate(repo_root, expected_updated_at, updated_at, change)


def checkpoint(repo_root: Path, expected_updated_at: str, updated_at: str, candidate_id: str, epic_status: str, gate: str, authority: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "running" or value.get("activeCandidateId") != candidate_id:
            raise PortfolioRunError("Checkpoint must target the active candidate of a running Portfolio.")
        if gate not in GATES or authority not in AUTHORITIES:
            raise PortfolioRunError("Checkpoint gate or decision authority is unsupported.")
        value["checkpoint"] = {"candidateId": candidate_id, "epicStatus": epic_status, "gate": gate, "decisionAuthority": authority, "updatedAt": updated_at}
        return value
    return _mutate(repo_root, expected_updated_at, updated_at, change)


def complete_active(repo_root: Path, expected_updated_at: str, updated_at: str, candidate_id: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "running" or value.get("activeCandidateId") != candidate_id:
            raise PortfolioRunError("Only the active candidate of a running Portfolio can complete.")
        if value.get("checkpoint", {}).get("gate") != "Epic closure":
            raise PortfolioRunError("Record an Epic closure checkpoint before completion.")
        value["completedCandidateIds"] = [*value["completedCandidateIds"], candidate_id]
        value.pop("activeCandidateId", None)
        value.pop("checkpoint", None)
        accounted = set(value["completedCandidateIds"]) | set(value["skippedCandidateIds"])
        if len(accounted) == len(value["snapshot"]):
            value["status"] = "completed"
        return value
    return _mutate(repo_root, expected_updated_at, updated_at, change)


def skip_active(repo_root: Path, expected_updated_at: str, updated_at: str, candidate_id: str) -> dict[str, Any]:
    """Account for a user-directed skip; the Portfolio mandate alone cannot call this."""

    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "running" or value.get("activeCandidateId") != candidate_id:
            raise PortfolioRunError("Only the active candidate of a running Portfolio can be skipped.")
        if value.get("checkpoint", {}).get("decisionAuthority") != "user":
            raise PortfolioRunError("Skipping requires a checkpoint with explicit user authority.")
        value["skippedCandidateIds"] = [*value["skippedCandidateIds"], candidate_id]
        value.pop("activeCandidateId", None)
        value.pop("checkpoint", None)
        accounted = set(value["completedCandidateIds"]) | set(value["skippedCandidateIds"])
        if len(accounted) == len(value["snapshot"]):
            value["status"] = "completed"
        return value

    return _mutate(repo_root, expected_updated_at, updated_at, change)


def pause_run(repo_root: Path, expected_updated_at: str, updated_at: str, reason: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "running" or not reason.strip():
            raise PortfolioRunError("Only a running Portfolio can pause with a reason.")
        value["status"] = "paused"
        value["pauseReason"] = reason.strip()
        return value
    return _mutate(repo_root, expected_updated_at, updated_at, change)


def resume_run(repo_root: Path, expected_updated_at: str, updated_at: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] != "paused":
            raise PortfolioRunError("Only a paused Portfolio can resume.")
        value["status"] = "running"
        value.pop("pauseReason", None)
        return value
    return _mutate(repo_root, expected_updated_at, updated_at, change)


def stop_run(repo_root: Path, expected_updated_at: str, updated_at: str, reason: str) -> dict[str, Any]:
    def change(value: dict[str, Any]) -> dict[str, Any]:
        if value["status"] not in {"running", "paused"} or not reason.strip():
            raise PortfolioRunError("Only a running or paused Portfolio can stop with a reason.")
        value["status"] = "stopped"
        value["pauseReason"] = reason.strip()
        return value

    return _mutate(repo_root, expected_updated_at, updated_at, change)


def project_portfolio_run(aim_root: Path) -> tuple[dict[str, Any], list[str]]:
    path = aim_root / RUN_FILE
    if not path.exists() and not path.is_symlink():
        return ({"configured": False, "valid": True, "status": "not_started", "total": 0, "completed": 0, "remaining": 0}, [])
    try:
        value = _read_object(path)
    except PortfolioRunError as exc:
        return ({"configured": True, "valid": False, "status": "invalid", "total": None, "completed": None, "remaining": None, "issue": str(exc)}, [str(exc)])
    issues = validate_run(value)
    if issues:
        message = "Invalid portfolio-run.json: " + "; ".join(issues)
        return ({"configured": True, "valid": False, "status": "invalid", "total": None, "completed": None, "remaining": None, "issue": message}, [message])
    accounted = len(value["completedCandidateIds"]) + len(value["skippedCandidateIds"])
    checkpoint_value = value.get("checkpoint") or {}
    completed_ids = set(value["completedCandidateIds"])
    skipped_ids = set(value["skippedCandidateIds"])
    active_id = value.get("activeCandidateId")
    return ({
        "configured": True, "valid": True, "runId": value["runId"], "status": value["status"],
        "mandateId": value["mandate"]["id"], "total": len(value["snapshot"]),
        "completed": len(value["completedCandidateIds"]), "skipped": len(value["skippedCandidateIds"]),
        "remaining": len(value["snapshot"]) - accounted, "activeCandidateId": active_id,
        "gate": checkpoint_value.get("gate"), "decisionAuthority": checkpoint_value.get("decisionAuthority"),
        "pauseReason": value.get("pauseReason"), "updatedAt": value["updatedAt"],
        "candidateStates": {
            item["candidateId"]: (
                "completed" if item["candidateId"] in completed_ids else
                "skipped" if item["candidateId"] in skipped_ids else
                "active" if item["candidateId"] == active_id else "queued"
            )
            for item in value["snapshot"]
        },
    }, [])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Checkpoint an AIM Portfolio Auto run without performing agent work.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--mandate-id", required=True)
    start.add_argument("--approved-at", required=True)
    start.add_argument("--updated-at", required=True)
    for name in ("activate-next", "complete", "skip", "pause", "resume", "stop"):
        command = commands.add_parser(name)
        command.add_argument("--expected-updated-at", required=True)
        command.add_argument("--updated-at", required=True)
        if name in {"complete", "skip"}: command.add_argument("--candidate-id", required=True)
        if name in {"pause", "stop"}: command.add_argument("--reason", required=True)
    mark = commands.add_parser("checkpoint")
    mark.add_argument("--expected-updated-at", required=True); mark.add_argument("--updated-at", required=True)
    mark.add_argument("--candidate-id", required=True); mark.add_argument("--epic-status", required=True)
    mark.add_argument("--gate", required=True, choices=sorted(GATES)); mark.add_argument("--authority", required=True, choices=sorted(AUTHORITIES))
    commands.add_parser("status")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "start": value = create_run(args.repo, args.mandate_id, args.approved_at, args.updated_at)
        elif args.command == "activate-next": value = activate_next(args.repo, args.expected_updated_at, args.updated_at)
        elif args.command == "checkpoint": value = checkpoint(args.repo, args.expected_updated_at, args.updated_at, args.candidate_id, args.epic_status, args.gate, args.authority)
        elif args.command == "complete": value = complete_active(args.repo, args.expected_updated_at, args.updated_at, args.candidate_id)
        elif args.command == "skip": value = skip_active(args.repo, args.expected_updated_at, args.updated_at, args.candidate_id)
        elif args.command == "pause": value = pause_run(args.repo, args.expected_updated_at, args.updated_at, args.reason)
        elif args.command == "resume": value = resume_run(args.repo, args.expected_updated_at, args.updated_at)
        elif args.command == "stop": value = stop_run(args.repo, args.expected_updated_at, args.updated_at, args.reason)
        else: value = load_run(args.repo)
    except PortfolioRunError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "run": value}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
