#!/usr/bin/env python3
"""Atomically merge normalized AIM planning candidates into portfolio Backlog."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


BACKLOG_VERSION = "1.0"
BACKLOG_FILE = "portfolio-backlog.json"
MAX_BACKLOG_BYTES = 1_048_576
MAX_ITEMS = 256
IMPORT_FIELDS = {"id", "epicId", "epicTitle", "title", "summary", "priority"}
OUTPUT_FIELDS = IMPORT_FIELDS | {"createdAt", "runtimeIncrementId"}


class BacklogError(ValueError):
    """Raised when a backlog request cannot be applied safely."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _bounded_string(
    value: Any, field: str, *, maximum: int, required: bool = True
) -> str:
    if not isinstance(value, str):
        if not required and value is None:
            return ""
        raise BacklogError(f"{field} must be a string.")
    normalized = " ".join(value.split())
    if required and not normalized:
        raise BacklogError(f"{field} must not be empty.")
    if len(normalized) > maximum:
        raise BacklogError(f"{field} must be at most {maximum} characters.")
    return normalized


def _slug(value: str, maximum: int) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-").upper()
    slug = re.sub(r"-+", "-", slug)[:maximum].rstrip("-")
    if not slug:
        raise BacklogError("A stable INC/EPIC id could not be derived from the title.")
    return slug


def _validate_epic_id(value: str) -> str:
    if len(value) > 120 or re.fullmatch(r"EPIC-[A-Z0-9-]+", value) is None:
        raise BacklogError("epicId must be a canonical EPIC-* id.")
    return value


def _validate_candidate_id(value: str) -> str:
    if len(value) > 80 or re.fullmatch(r"INC-[A-Z0-9-]+", value) is None:
        raise BacklogError("id must be a canonical INC-* candidate id.")
    return value


def normalize_import(value: Any, timestamp: str) -> list[dict[str, Any]]:
    """Normalize agent-interpreted input; this function never parses source prose."""

    if not isinstance(value, dict) or set(value) != {"items"}:
        raise BacklogError("input must be an object containing only an items array.")
    raw_items = value["items"]
    if not isinstance(raw_items, list) or not raw_items:
        raise BacklogError("items must be a non-empty array.")
    if len(raw_items) > MAX_ITEMS:
        raise BacklogError(f"items may contain at most {MAX_ITEMS} candidates.")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raise BacklogError(f"items[{index - 1}] must be an object.")
        extra = sorted(set(raw) - IMPORT_FIELDS)
        if extra:
            raise BacklogError(
                f"items[{index - 1}] contains unsupported fields: {', '.join(extra)}."
            )
        epic_title = _bounded_string(
            raw.get("epicTitle"), f"items[{index - 1}].epicTitle", maximum=200
        )
        title = _bounded_string(
            raw.get("title"), f"items[{index - 1}].title", maximum=240
        )
        summary = _bounded_string(
            raw.get("summary", ""),
            f"items[{index - 1}].summary",
            maximum=1000,
            required=False,
        )
        epic_id = raw.get("epicId")
        if epic_id is None:
            epic_id = f"EPIC-{_slug(epic_title, 115)}"
        else:
            epic_id = _validate_epic_id(
                _bounded_string(
                    epic_id, f"items[{index - 1}].epicId", maximum=120
                )
            )
        candidate_id = raw.get("id")
        if candidate_id is None:
            epic_slug = _slug(epic_id.removeprefix("EPIC-"), 36)
            title_budget = 75 - len(epic_slug) - 1
            candidate_id = f"INC-{epic_slug}-{_slug(title, title_budget)}"
        else:
            candidate_id = _validate_candidate_id(
                _bounded_string(candidate_id, f"items[{index - 1}].id", maximum=80)
            )
        if candidate_id in seen:
            raise BacklogError(f"input contains duplicate candidate id {candidate_id}.")
        seen.add(candidate_id)

        priority = raw.get("priority", index)
        if (
            not isinstance(priority, int)
            or isinstance(priority, bool)
            or priority < 1
        ):
            raise BacklogError(
                f"items[{index - 1}].priority must be a positive integer."
            )
        item: dict[str, Any] = {
            "id": candidate_id,
            "epicId": epic_id,
            "epicTitle": epic_title,
            "title": title,
            "priority": priority,
            "createdAt": timestamp,
        }
        if summary:
            item["summary"] = summary
        normalized.append(item)
    return normalized


def validate_backlog(value: Any) -> list[str]:
    """Validate the complete bounded planning file without runtime inference."""

    if not isinstance(value, dict):
        return ["backlog must be a JSON object."]
    issues: list[str] = []
    if set(value) != {"backlogVersion", "updatedAt", "items"}:
        issues.append("backlog must contain only backlogVersion, updatedAt, and items.")
    if value.get("backlogVersion") != BACKLOG_VERSION:
        issues.append(f"backlogVersion must be {BACKLOG_VERSION}.")
    updated_at = value.get("updatedAt")
    if not isinstance(updated_at, str) or not 1 <= len(updated_at) <= 64:
        issues.append("updatedAt must be a non-empty timestamp string.")
    items = value.get("items")
    if not isinstance(items, list):
        issues.append("items must be an array.")
        return issues
    if len(items) > MAX_ITEMS:
        issues.append(f"items may contain at most {MAX_ITEMS} candidates.")
    seen: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{prefix} must be an object.")
            continue
        extra = sorted(set(item) - OUTPUT_FIELDS)
        missing = sorted({"id", "epicId", "epicTitle", "title", "priority", "createdAt"} - set(item))
        if extra:
            issues.append(f"{prefix} contains unsupported fields: {', '.join(extra)}.")
        if missing:
            issues.append(f"{prefix} is missing fields: {', '.join(missing)}.")
            continue
        try:
            candidate_id = _validate_candidate_id(item["id"])
            _validate_epic_id(item["epicId"])
            _bounded_string(item["epicTitle"], f"{prefix}.epicTitle", maximum=200)
            _bounded_string(item["title"], f"{prefix}.title", maximum=240)
            _bounded_string(item.get("summary", ""), f"{prefix}.summary", maximum=1000, required=False)
            _bounded_string(item["createdAt"], f"{prefix}.createdAt", maximum=64)
            runtime_id = item.get("runtimeIncrementId")
            if runtime_id is not None and (
                not isinstance(runtime_id, str)
                or len(runtime_id) > 32
                or re.fullmatch(r"DI-[0-9]+", runtime_id) is None
            ):
                raise BacklogError(f"{prefix}.runtimeIncrementId must be a DI-* id.")
            if (
                not isinstance(item["priority"], int)
                or isinstance(item["priority"], bool)
                or item["priority"] < 1
            ):
                raise BacklogError(f"{prefix}.priority must be a positive integer.")
            if candidate_id in seen:
                raise BacklogError(f"duplicate candidate id {candidate_id}.")
            seen.add(candidate_id)
        except BacklogError as exc:
            issues.append(str(exc))
    return issues


def _load_existing(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise BacklogError(f"{BACKLOG_FILE} must not be a symbolic link.")
    if not path.exists():
        return {"backlogVersion": BACKLOG_VERSION, "updatedAt": "initial", "items": []}
    if not path.is_file():
        raise BacklogError(f"{BACKLOG_FILE} must be a regular file.")
    if path.stat().st_size > MAX_BACKLOG_BYTES:
        raise BacklogError(f"{BACKLOG_FILE} is larger than {MAX_BACKLOG_BYTES} bytes.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BacklogError(f"{BACKLOG_FILE} could not be read as JSON: {exc}.") from exc
    issues = validate_backlog(value)
    if issues:
        raise BacklogError("Existing backlog is invalid: " + " ".join(issues))
    return value


def merge_backlog(repo: Path, imported: list[dict[str, Any]], timestamp: str) -> dict[str, Any]:
    """Merge one normalized batch atomically or leave the existing file unchanged."""

    repo = repo.resolve()
    if not repo.is_dir():
        raise BacklogError(f"repository directory does not exist: {repo}")
    aim_root = repo / ".aim"
    if aim_root.is_symlink():
        raise BacklogError(".aim must not be a symbolic link.")
    path = aim_root / BACKLOG_FILE
    existing = _load_existing(path)
    by_id = {item["id"]: dict(item) for item in existing["items"]}
    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    conflicts: list[str] = []

    for incoming in imported:
        candidate_id = incoming["id"]
        current = by_id.get(candidate_id)
        if current is None:
            by_id[candidate_id] = incoming
            added.append(candidate_id)
            continue
        identity = ("epicId", "epicTitle", "title")
        if any(current.get(field) != incoming.get(field) for field in identity):
            conflicts.append(candidate_id)
            continue
        merged = dict(current)
        for field in ("summary", "priority"):
            if field in incoming:
                merged[field] = incoming[field]
        if merged == current:
            skipped.append(candidate_id)
        else:
            by_id[candidate_id] = merged
            updated.append(candidate_id)

    if conflicts:
        raise BacklogError(
            "candidate id conflicts require review: " + ", ".join(conflicts)
        )
    items = sorted(by_id.values(), key=lambda item: (item["priority"], item["createdAt"], item["id"]))
    output = {"backlogVersion": BACKLOG_VERSION, "updatedAt": timestamp, "items": items}
    issues = validate_backlog(output)
    if issues:
        raise BacklogError("Merged backlog is invalid: " + " ".join(issues))
    encoded = (json.dumps(output, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(encoded) > MAX_BACKLOG_BYTES:
        raise BacklogError(f"merged {BACKLOG_FILE} would exceed {MAX_BACKLOG_BYTES} bytes.")

    aim_root.mkdir(parents=True, exist_ok=True)
    if aim_root.is_symlink() or not aim_root.is_dir():
        raise BacklogError(".aim must be a regular directory, not a symbolic link.")
    try:
        aim_root.resolve().relative_to(repo)
    except ValueError as exc:
        raise BacklogError(".aim must remain inside the repository.") from exc
    if path.is_symlink():
        raise BacklogError(f"{BACKLOG_FILE} must not be a symbolic link.")
    descriptor, temporary = tempfile.mkstemp(prefix=".portfolio-backlog.", suffix=".tmp", dir=aim_root)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {
        "path": str(path),
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "total": len(items),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely merge normalized INC-* candidates into AIM UI Backlog."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path, help="JSON input path; omit to read stdin")
    parser.add_argument("--timestamp", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    timestamp = args.timestamp or _timestamp()
    try:
        source = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        if len(source.encode("utf-8")) > MAX_BACKLOG_BYTES:
            raise BacklogError(f"input is larger than {MAX_BACKLOG_BYTES} bytes.")
        imported = normalize_import(json.loads(source), timestamp)
        result = merge_backlog(args.repo, imported, timestamp)
    except (OSError, json.JSONDecodeError, BacklogError) as exc:
        print(f"AIM Backlog: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "AIM Backlog: "
            f"{len(result['added'])} added · {len(result['updated'])} updated · "
            f"{len(result['skipped'])} skipped · {result['total']} total"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
