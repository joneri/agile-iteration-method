#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_runtime_contract.py
"""Shared executable AIM runtime-state and Gate E evidence contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


CANONICAL_RUNTIME_STATUSES = {
    "epic_initialized",
    "gate_a_pending",
    "gate_b_pending",
    "increment_in_progress",
    "epic_paused",
    "blocked",
    "review_in_progress",
    "tdo_validation_in_progress",
    "po_approval_pending",
    "done_increment_accepted",
    "epic_complete",
}
PORTFOLIO_CHECKPOINT_STATUSES = CANONICAL_RUNTIME_STATUSES | {"activation_pending"}
TERMINAL_RUNTIME_STATUSES = {"done_increment_accepted", "epic_complete"}
MAX_ACCEPTANCE_DECISION_BYTES = 1_000_000
MAX_INCREMENT_ARTIFACT_BYTES = 1_000_000
MAX_RUNTIME_STATE_BYTES = 1_000_000
INCREMENT_ID_PATTERN = re.compile(r"DI-[0-9]+")


class RuntimeTransitionError(ValueError):
    """A bounded, operator-facing runtime transition error."""


def markdown_field(markdown: str, label: str) -> str | None:
    match = re.search(
        rf"^[ \t]*(?:[-*+]\s+)?{re.escape(label)}:\s*(?:`([^`]+)`|(.+?))\s*$",
        markdown,
        re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return None
    return (match.group(1) or match.group(2)).strip()


def increment_artifact_identity(path: Path, markdown: str) -> tuple[str, str | None]:
    """Resolve one bounded plan artifact's Increment and declared Epic identity."""

    match = re.search(r"\bDI-\d+\b", markdown[:240], re.IGNORECASE)
    if match:
        increment_id = match.group(0).upper()
    else:
        number = re.match(r"(\d+)", path.name)
        increment_id = f"DI-{number.group(1)}" if number else path.stem.upper()
    return increment_id, markdown_field(markdown, "Epic")


def terminal_increment_artifact(
    workspace: Path, epic_id: str, increment_id: str
) -> tuple[Path | None, list[str]]:
    """Require one explicit plan relation before new Portfolio completion."""

    increments = workspace / "increments"
    if increments.is_symlink() or not increments.is_dir():
        return None, ["workspace increments directory is missing or unsafe"]

    matches: list[Path] = []
    unbound = False
    mismatched = False
    for path in sorted(increments.glob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_INCREMENT_ARTIFACT_BYTES:
                continue
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        artifact_increment_id, declared_epic = increment_artifact_identity(path, markdown)
        if artifact_increment_id != increment_id:
            continue
        if declared_epic == epic_id:
            matches.append(path)
        elif declared_epic is None:
            unbound = True
        else:
            mismatched = True

    if len(matches) == 1:
        return matches[0], []
    if len(matches) > 1:
        return None, ["matching runtime Increment plan relation is ambiguous"]
    if unbound:
        return None, [f"matching runtime Increment plan must declare Epic: {epic_id}"]
    if mismatched:
        return None, ["matching runtime Increment plan declares a different Epic"]
    return None, ["matching runtime Increment plan is missing"]


def decision_accepts_increment(path: Path, increment_id: str) -> bool:
    """Return whether one bounded regular Markdown file accepts the Increment."""

    if path.is_symlink() or not path.is_file():
        return False
    try:
        if path.stat().st_size > MAX_ACCEPTANCE_DECISION_BYTES:
            return False
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    decision = markdown_field(content, "Decision") or ""
    status = markdown_field(content, "Status") or ""
    authority_fields = f"{decision}\n{status}"
    if re.search(
        r"\b(?:change requested|pending|rejected|not accepted)\b",
        authority_fields,
        re.IGNORECASE,
    ):
        return False
    heading = content.splitlines()[0] if content.splitlines() else ""
    accepted = any(
        (
            re.search(
                r"\b(?:accept(?:ed)?|approv(?:e|ed))\b",
                authority_fields,
                re.IGNORECASE,
            ),
            markdown_field(content, "Accepted at"),
            re.search(
                r"\bGate E\b.*\bAccepted\b|\bAccepted\b.*\bGate E\b",
                heading,
                re.IGNORECASE,
            ),
            re.search(
                r"^Accepted\s+(?:by|on|under|as part of)\b",
                content,
                re.IGNORECASE | re.MULTILINE,
            ),
        )
    )
    if not accepted:
        return False
    mentioned = {item.upper() for item in re.findall(r"\bDI-\d+\b", content, re.I)}
    return not mentioned or increment_id in mentioned


def terminal_acceptance(
    repo_root: Path,
    workspace: Path,
    state: dict[str, Any],
    increment_id: str,
) -> tuple[Path | None, list[str]]:
    """Resolve the structured terminal acceptance relation and exact failures."""

    issues: list[str] = []
    if state.get("epicStatus") not in TERMINAL_RUNTIME_STATUSES:
        issues.append("workspace status is not terminal")
    if state.get("previousIncrementId") != increment_id:
        issues.append("previousIncrementId does not match the Backlog runtime Increment")
    if state.get("previousIncrementStatus") != "accepted":
        issues.append("previousIncrementStatus is not accepted")
    if state.get("lastGatePassed") != "Gate E":
        issues.append("lastGatePassed is not Gate E")

    raw_path = state.get("gateEAcceptance")
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append("gateEAcceptance is missing")
        return None, issues
    if "\\" in raw_path:
        issues.append("gateEAcceptance does not use POSIX separators")
        return None, issues
    relative = Path(raw_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != ".aim"
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        issues.append("gateEAcceptance is not a contained repository-relative .aim path")
        return None, issues

    current = repo_root.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            issues.append("gateEAcceptance traverses a symbolic link")
            return None, issues
    try:
        decision = (repo_root.resolve() / relative).resolve()
        decision.relative_to(workspace.resolve())
    except (OSError, ValueError):
        issues.append("gateEAcceptance leaves the authoritative workspace")
        return None, issues
    if decision.parent != (workspace / "decisions").resolve():
        issues.append("gateEAcceptance is not in the workspace decisions directory")
        return None, issues
    if not decision_accepts_increment(decision, increment_id):
        issues.append("gateEAcceptance is missing, oversized, mismatched, or not accepted")
        return None, issues
    return decision, issues


def _runtime_state_schema(repo_root: Path) -> dict[str, Any]:
    package_root = Path(__file__).resolve().parents[1]
    candidates = (
        package_root / "schemas/aim-runtime-state.schema.json",
        package_root / "references/schemas/aim-runtime-state.schema.json",
    )
    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink():
            value = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                return value
    raise RuntimeTransitionError(
        f"The trusted runtime-state schema is unavailable beside {Path(__file__).resolve()}."
    )


def _matches_schema_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise RuntimeTransitionError(f"Unsupported runtime schema type {expected!r}.")


def _schema_issues(
    value: Any, schema: dict[str, Any], path: str = "$"
) -> list[str]:
    """Validate the dependency-free subset used by the runtime-state schema."""

    issues: list[str] = []
    if "const" in schema and value != schema["const"]:
        issues.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{path} must be one of {schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_schema_type(value, expected_type):
        return issues + [f"{path} must be a {expected_type}"]
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                issues.append(f"{path} is missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                issues.extend(_schema_issues(child, child_schema, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                issues.append(f"{path}.{key} is not allowed")
    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if minimum is not None and len(value) < minimum:
            issues.append(f"{path} must contain at least {minimum} items")
        if maximum is not None and len(value) > maximum:
            issues.append(f"{path} must contain at most {maximum} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                issues.extend(_schema_issues(child, item_schema, f"{path}[{index}]"))
    if isinstance(value, str):
        minimum = schema.get("minLength")
        maximum = schema.get("maxLength")
        if minimum is not None and len(value) < minimum:
            issues.append(f"{path} must contain at least {minimum} characters")
        if maximum is not None and len(value) > maximum:
            issues.append(f"{path} must contain at most {maximum} characters")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            issues.append(f"{path} must match {pattern!r}")
    return issues


def _authority_state_path(repo_root: Path, raw_path: str) -> Path:
    if "\\" in raw_path or any(part in {"", ".", ".."} for part in raw_path.split("/")):
        raise RuntimeTransitionError(
            "authorityStatePath must be a contained POSIX path without dot or empty segments."
        )
    relative = PurePosixPath(raw_path)
    if (
        relative.is_absolute()
        or len(relative.parts) < 2
        or relative.parts[0] != ".aim"
        or relative.parts[-1] != "state.json"
    ):
        raise RuntimeTransitionError(
            "authorityStatePath must begin with .aim/ and end in state.json."
        )
    root = repo_root.resolve()
    aim_root = root / ".aim"
    if aim_root.is_symlink() or not aim_root.is_dir():
        raise RuntimeTransitionError("The repository has no safe .aim runtime root.")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeTransitionError("authorityStatePath crosses a symbolic link.")
    resolved = current.resolve()
    try:
        resolved.relative_to(aim_root.resolve())
    except ValueError as exc:
        raise RuntimeTransitionError("authorityStatePath leaves the .aim runtime root.") from exc
    if not resolved.is_file():
        raise RuntimeTransitionError("The authoritative state.json was not found.")
    return resolved


def _read_runtime_state(path: Path) -> tuple[bytes, dict[str, Any]]:
    if path.stat().st_size > MAX_RUNTIME_STATE_BYTES:
        raise RuntimeTransitionError("state.json exceeds the runtime size limit.")
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeTransitionError(
            f"state.json contains invalid JSON at line {exc.lineno}."
        ) from exc
    if not isinstance(value, dict):
        raise RuntimeTransitionError("state.json must contain an object.")
    return payload, value


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _atomic_replace(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=".state.continue.", suffix=".tmp", dir=path.parent
    )
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


def plan_post_gate_e_continue(
    repo_root: Path,
    *,
    authority_state_path: str,
    increment_id: str,
    updated_at: str,
) -> dict[str, Any]:
    """Preview one direct, canonical transition back to Gate B."""

    root = repo_root.resolve()
    state_path = _authority_state_path(root, authority_state_path)
    source_payload, source = _read_runtime_state(state_path)
    expected = {
        "stateSchemaVersion": "1.0",
        "epicStatus": "done_increment_accepted",
        "activeIncrementId": None,
        "currentRole": "PO",
        "lastGatePassed": "Gate E",
        "previousIncrementStatus": "accepted",
    }
    mismatches = [
        f"{key} expected {value!r}, found {source.get(key)!r}"
        for key, value in expected.items()
        if source.get(key) != value
    ]
    if mismatches:
        raise RuntimeTransitionError(
            "Post-Gate-E continuation preconditions failed: " + "; ".join(mismatches)
        )
    previous_increment_id = source.get("previousIncrementId")
    if (
        not isinstance(previous_increment_id, str)
        or INCREMENT_ID_PATTERN.fullmatch(previous_increment_id) is None
    ):
        raise RuntimeTransitionError(
            "Post-Gate-E continuation requires canonical accepted Increment history."
        )
    _, acceptance_issues = terminal_acceptance(
        root, state_path.parent, source, previous_increment_id
    )
    if acceptance_issues:
        raise RuntimeTransitionError(
            "Accepted history is invalid: " + "; ".join(acceptance_issues)
        )
    if INCREMENT_ID_PATTERN.fullmatch(increment_id) is None:
        raise RuntimeTransitionError("The next Increment must use a canonical DI-* identity.")
    if increment_id == previous_increment_id:
        raise RuntimeTransitionError("The next Increment must differ from accepted history.")
    if not isinstance(updated_at, str) or not updated_at.strip():
        raise RuntimeTransitionError("updatedAt must be a non-empty timestamp string.")
    workspace = state_path.parent
    plan_path, plan_issues = terminal_increment_artifact(
        workspace, str(source.get("epicId") or ""), increment_id
    )
    if plan_issues:
        raise RuntimeTransitionError("Next Increment plan is invalid: " + "; ".join(plan_issues))

    candidate = dict(source)
    candidate.pop("plannedIncrementId", None)
    candidate.update(
        {
            "epicStatus": "gate_b_pending",
            "activeIncrementId": increment_id,
            "currentRole": "TDO",
            "lastGatePassed": "Gate A",
            "updatedAt": updated_at.strip(),
            "uiDecision": {
                "visibility": "ready",
                "gate": "Gate B",
                "targetId": increment_id,
            },
        }
    )
    schema_issues = _schema_issues(candidate, _runtime_state_schema(root))
    if schema_issues:
        raise RuntimeTransitionError(
            "Candidate state failed schema validation: " + "; ".join(schema_issues)
        )
    if (
        candidate.get("epicStatus") != "gate_b_pending"
        or candidate.get("activeIncrementId") != increment_id
        or candidate.get("currentRole") != "TDO"
        or candidate.get("lastGatePassed") != "Gate A"
    ):
        raise RuntimeTransitionError("Candidate state failed continuation coherence checks.")
    candidate_payload = _json_bytes(candidate)
    return {
        "result": "planned",
        "authorityStatePath": state_path.relative_to(root).as_posix(),
        "epicId": source.get("epicId"),
        "previousIncrementId": source.get("previousIncrementId"),
        "nextIncrementId": increment_id,
        "sourceStateSha256": hashlib.sha256(source_payload).hexdigest(),
        "candidateStateSha256": hashlib.sha256(candidate_payload).hexdigest(),
        "candidate": candidate,
        "incrementPlan": plan_path.relative_to(root).as_posix() if plan_path else None,
    }


def apply_post_gate_e_continue(
    repo_root: Path,
    *,
    authority_state_path: str,
    increment_id: str,
    updated_at: str,
    expected_state_sha256: str,
) -> dict[str, Any]:
    """Validate freshness again, then atomically publish the previewed transition."""

    plan = plan_post_gate_e_continue(
        repo_root,
        authority_state_path=authority_state_path,
        increment_id=increment_id,
        updated_at=updated_at,
    )
    if plan["sourceStateSha256"] != expected_state_sha256:
        raise RuntimeTransitionError(
            "state.json changed since preview; reload before applying continuation."
        )
    state_path = _authority_state_path(repo_root.resolve(), authority_state_path)
    current_payload, _ = _read_runtime_state(state_path)
    if hashlib.sha256(current_payload).hexdigest() != expected_state_sha256:
        raise RuntimeTransitionError(
            "state.json changed immediately before replacement; nothing was written."
        )
    candidate_payload = _json_bytes(plan["candidate"])
    _atomic_replace(state_path, candidate_payload)
    written_payload, written = _read_runtime_state(state_path)
    if (
        hashlib.sha256(written_payload).hexdigest() != plan["candidateStateSha256"]
        or _schema_issues(written, _runtime_state_schema(repo_root.resolve()))
    ):
        raise RuntimeTransitionError("Published state failed post-replacement verification.")
    return {**plan, "result": "applied"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    continuation = subparsers.add_parser(
        "continue", help="Preview or apply one post-Gate-E continuation."
    )
    continuation.add_argument("--repo", type=Path, default=Path.cwd())
    continuation.add_argument("--authority-state-path", required=True)
    continuation.add_argument("--increment-id", required=True)
    continuation.add_argument("--updated-at", required=True)
    continuation.add_argument("--expected-state-sha256")
    continuation.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.apply:
            if not args.expected_state_sha256:
                raise RuntimeTransitionError(
                    "--apply requires --expected-state-sha256 from preview."
                )
            result = apply_post_gate_e_continue(
                args.repo,
                authority_state_path=args.authority_state_path,
                increment_id=args.increment_id,
                updated_at=args.updated_at,
                expected_state_sha256=args.expected_state_sha256,
            )
        else:
            result = plan_post_gate_e_continue(
                args.repo,
                authority_state_path=args.authority_state_path,
                increment_id=args.increment_id,
                updated_at=args.updated_at,
            )
    except (OSError, RuntimeTransitionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"AIM continuation failed: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
