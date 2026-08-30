#!/usr/bin/env python3
"""Shared executable AIM runtime-state, Gate E, and truthful closure contract."""

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
MAX_CLOSURE_EVIDENCE_BYTES = 1_000_000
MAX_REFERENCED_EVIDENCE_BYTES = 1_000_000
INCREMENT_ID_PATTERN = re.compile(r"DI-[0-9]+")
OUTCOME_CLASSES = {"product", "pilot", "poc"}
EVIDENCE_KINDS = {
    "authority_decision",
    "black_box_result",
    "external_receipt",
    "negative_test",
    "review",
    "test_log",
    "user_observation",
}
BLACK_BOX_PERFORMERS = {"external_observer", "reviewer", "user"}
CRITERION_EVIDENCE_KINDS = {
    "black_box_result",
    "external_receipt",
    "review",
    "test_log",
    "user_observation",
}
REPRESENTATIVE_EVIDENCE_KINDS = {
    "black_box_result",
    "external_receipt",
    "user_observation",
}


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


def epic_acceptance_criterion_ids(markdown: str) -> tuple[list[str], list[str]]:
    """Extract stable criterion identities from the canonical Epic section."""

    section = re.search(
        r"^## Acceptance criteria\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        markdown,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if not section:
        return [], ["epic.md has no Acceptance criteria section"]
    identities: list[str] = []
    for line in section.group("body").splitlines():
        explicit = re.match(
            r"^[ \t]{0,3}(?:[-*+]\s+)?(?:\*\*|__)?"
            r"(AC-[A-Z0-9-]+)\s*(?::|—|-)",
            line,
            re.IGNORECASE,
        )
        numbered = re.match(r"^[ \t]{0,3}(\d+)\.\s+", line)
        if explicit:
            identities.append(explicit.group(1).upper())
        elif numbered:
            identities.append(f"AC-{numbered.group(1)}")
    if not identities:
        return [], ["epic.md has no identifiable acceptance criteria"]
    if len(identities) != len(set(identities)):
        return identities, ["epic.md contains duplicate acceptance-criterion ids"]
    return identities, []


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


def _contained_decision_path(
    repo_root: Path, workspace: Path, raw_path: Any, field: str
) -> tuple[Path | None, list[str]]:
    """Resolve one regular, contained decision artifact without trusting its name."""

    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, [f"{field} is missing"]
    if "\\" in raw_path:
        return None, [f"{field} does not use POSIX separators"]
    relative = PurePosixPath(raw_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != ".aim"
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        return None, [f"{field} is not a contained repository-relative .aim path"]
    current = repo_root.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, [f"{field} traverses a symbolic link"]
    try:
        resolved = current.resolve()
        resolved.relative_to(workspace.resolve())
    except (OSError, ValueError):
        return None, [f"{field} leaves the authoritative workspace"]
    if resolved.parent != (workspace / "decisions").resolve():
        return None, [f"{field} is not in the workspace decisions directory"]
    if resolved.is_symlink() or not resolved.is_file():
        return None, [f"{field} is missing or unsafe"]
    return resolved, []


def _evidence_reference_issues(
    workspace: Path, references: Any, label: str
) -> tuple[list[str], list[dict[str, Any]]]:
    """Verify hash-bound, non-empty evidence files inside the Epic workspace."""

    if not isinstance(references, list) or not references:
        return [f"{label} has no concrete evidence"], []
    issues: list[str] = []
    manifests: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in references:
        if not isinstance(raw, dict):
            issues.append(f"{label} evidence must use path, sha256, and kind")
            continue
        raw_path = raw.get("path")
        expected_sha256 = raw.get("sha256")
        kind = raw.get("kind")
        if (
            not isinstance(raw_path, str)
            or not raw_path.strip()
            or "\\" in raw_path
        ):
            issues.append(f"{label} contains an invalid evidence path")
            continue
        if raw_path in seen:
            issues.append(f"{label} duplicates evidence path {raw_path}")
            continue
        seen.add(raw_path)
        if not isinstance(expected_sha256, str) or re.fullmatch(
            r"[0-9a-f]{64}", expected_sha256
        ) is None:
            issues.append(f"{label} evidence {raw_path} has no canonical sha256")
        if kind not in EVIDENCE_KINDS:
            issues.append(f"{label} evidence {raw_path} has unsupported kind {kind!r}")
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or any(
            part in {"", ".", ".."} for part in relative.parts
        ):
            issues.append(f"{label} contains an unsafe evidence path")
            continue
        current = workspace.resolve()
        unsafe = False
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                unsafe = True
                break
        try:
            current.resolve().relative_to(workspace.resolve())
        except (OSError, ValueError):
            unsafe = True
        if unsafe or not current.is_file():
            issues.append(f"{label} evidence file is missing or unsafe: {raw_path}")
            continue
        try:
            payload = current.read_bytes()
        except OSError:
            issues.append(f"{label} evidence file is unreadable: {raw_path}")
            continue
        if len(payload) > MAX_REFERENCED_EVIDENCE_BYTES:
            issues.append(f"{label} evidence file exceeds the size limit: {raw_path}")
            continue
        if not payload.strip():
            issues.append(f"{label} evidence file is empty: {raw_path}")
            continue
        actual_sha256 = hashlib.sha256(payload).hexdigest()
        if expected_sha256 != actual_sha256:
            issues.append(f"{label} evidence sha256 does not match: {raw_path}")
        manifests.append(
            {
                "path": raw_path,
                "sha256": actual_sha256,
                "size": len(payload),
                "kind": kind,
                "resolved": current.resolve(),
            }
        )
    return issues, manifests


def _evidence_set_sha256(manifests: list[dict[str, Any]]) -> tuple[str | None, list[str]]:
    """Bind every distinct referenced evidence byte set in deterministic order."""

    issues: list[str] = []
    by_path: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        serializable = {
            key: manifest[key] for key in ("path", "sha256", "size", "kind")
        }
        previous = by_path.get(serializable["path"])
        if previous is not None and previous != serializable:
            issues.append(
                f"evidence path {serializable['path']} has contradictory bindings"
            )
        by_path[serializable["path"]] = serializable
    if not by_path:
        return None, issues + ["closure evidence set is empty"]
    payload = json.dumps(
        [by_path[path] for path in sorted(by_path)],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), issues


def _black_box_record_issues(
    manifest: dict[str, Any], label: str, expected_metadata: dict[str, Any]
) -> list[str]:
    """Require an inspectable machine-readable result, not a prose PASS claim."""

    if manifest.get("kind") != "black_box_result":
        return [f"{label} must reference kind black_box_result"]
    path = manifest.get("resolved")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (AttributeError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [f"{label} black-box result is not readable JSON"]
    if not isinstance(value, dict):
        return [f"{label} black-box result must contain an object"]
    issues: list[str] = []
    expected = {
        "schemaVersion": "1.0",
        "kind": "black_box_result",
        "status": "passed",
        "representative": True,
        "operatorAssistance": False,
    }
    for field, required in expected.items():
        if value.get(field) != required:
            issues.append(f"{label} black-box result {field} is not {required!r}")
    for field in (
        "entryPoint",
        "scenario",
        "expectedOutcome",
        "actualOutcome",
        "performedBy",
        "startedAt",
        "completedAt",
    ):
        if not isinstance(value.get(field), str) or not value[field].strip():
            issues.append(f"{label} black-box result has no {field}")
        elif value.get(field) != expected_metadata.get(field):
            issues.append(
                f"{label} black-box result {field} does not match the closure audit"
            )
    if str(value.get("performedBy") or "").strip().lower() not in BLACK_BOX_PERFORMERS:
        issues.append(
            f"{label} black-box result names the implementation side or an "
            "unsupported performer"
        )
    return issues


def _authority_record_issues(
    manifests: list[dict[str, Any]], authority: Any, epic_id: Any
) -> list[str]:
    authority_records = [
        item for item in manifests if item.get("kind") == "authority_decision"
    ]
    if len(authority_records) != 1 or len(manifests) != 1:
        return ["closure evidence must bind exactly one authority_decision"]
    path = authority_records[0]["resolved"]
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ["closure authority decision is unreadable"]
    issues: list[str] = []
    decision = (markdown_field(content, "Decision") or "").lower()
    recorded_authority = (markdown_field(content, "Authority") or "").lower()
    if decision not in {"approved", "accepted"}:
        issues.append("closure authority decision is not approved")
    if recorded_authority != str(authority or "").lower():
        issues.append("closure authority decision does not match decisionAuthority")
    if not isinstance(epic_id, str) or epic_id not in content:
        issues.append("closure authority decision does not identify the Epic")
    if re.search(r"\bEpic closure\b", content, re.IGNORECASE) is None:
        issues.append("closure authority decision is not a distinct Epic closure decision")
    if authority == "portfolio_mandate" and not markdown_field(content, "Mandate"):
        issues.append("Portfolio closure authority has no mandate provenance")
    return issues


def _epic_closure_evidence_analysis(
    repo_root: Path, workspace: Path, state: dict[str, Any]
) -> tuple[Path | None, list[str], str | None]:
    """Validate closure truth, returning the complete referenced-byte digest."""

    path, issues = _contained_decision_path(
        repo_root, workspace, state.get("epicClosureEvidence"), "epicClosureEvidence"
    )
    if path is None:
        return None, issues, None
    try:
        if path.stat().st_size > MAX_CLOSURE_EVIDENCE_BYTES:
            return None, ["epicClosureEvidence exceeds the size limit"], None
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, ["epicClosureEvidence is not readable JSON"], None
    if not isinstance(evidence, dict):
        return None, ["epicClosureEvidence must contain an object"], None
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    expected_sha256 = state.get("epicClosureEvidenceSha256")
    if expected_sha256 != actual_sha256:
        issues.append("epicClosureEvidenceSha256 does not bind the current artifact")

    epic_id = state.get("epicId")
    if evidence.get("schemaVersion") != "1.0":
        issues.append("closure evidence schemaVersion is not 1.0")
    if evidence.get("epicId") != epic_id:
        issues.append("closure evidence Epic identity does not match state")
    if evidence.get("recommendation") != "close":
        issues.append("closure evidence recommendation is not close")
    outcome_class = evidence.get("outcomeClass")
    if outcome_class not in OUTCOME_CLASSES:
        issues.append("closure evidence outcomeClass is not product, pilot, or poc")

    epic_path = workspace / "epic.md"
    try:
        epic_markdown = epic_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        epic_markdown = ""
    declared_class = (markdown_field(epic_markdown, "Outcome class") or "").lower()
    if declared_class not in OUTCOME_CLASSES:
        issues.append("epic.md must declare Outcome class: Product, Pilot, or POC")
    elif outcome_class != declared_class:
        issues.append("closure evidence outcomeClass does not match epic.md")

    declared_criteria, declared_criterion_issues = epic_acceptance_criterion_ids(
        epic_markdown
    )
    issues.extend(declared_criterion_issues)
    criteria = evidence.get("acceptanceCriteria")
    evidence_criterion_ids: set[str] = set()
    manifests: list[dict[str, Any]] = []
    if not isinstance(criteria, list) or not criteria:
        issues.append("closure evidence has no acceptance-criterion mapping")
    else:
        seen: set[str] = set()
        for index, criterion in enumerate(criteria, 1):
            prefix = f"acceptance criterion {index}"
            if not isinstance(criterion, dict):
                issues.append(f"{prefix} is not an object")
                continue
            criterion_id = criterion.get("id")
            if not isinstance(criterion_id, str) or not criterion_id.strip():
                issues.append(f"{prefix} has no id")
            else:
                normalized_id = criterion_id.upper()
                if normalized_id in seen:
                    issues.append(f"{prefix} duplicates id {normalized_id}")
                else:
                    seen.add(normalized_id)
                    evidence_criterion_ids.add(normalized_id)
            if criterion.get("status") != "proven":
                issues.append(f"{prefix} is not proven")
            reference_issues, reference_manifests = _evidence_reference_issues(
                workspace, criterion.get("evidence"), prefix
            )
            issues.extend(reference_issues)
            manifests.extend(reference_manifests)
            if reference_manifests and not any(
                item.get("kind") in CRITERION_EVIDENCE_KINDS
                for item in reference_manifests
            ):
                issues.append(f"{prefix} has no proof evidence")
            if (
                outcome_class in {"product", "pilot"}
                and criterion.get("evidenceClass") != "representative"
            ):
                issues.append(f"{prefix} is not supported by representative evidence")
            if outcome_class in {"product", "pilot"} and reference_manifests:
                if not any(
                    item.get("kind") in REPRESENTATIVE_EVIDENCE_KINDS
                    for item in reference_manifests
                ):
                    issues.append(
                        f"{prefix} has no representative proof evidence"
                    )
    if declared_criteria and evidence_criterion_ids != set(declared_criteria):
        missing = sorted(set(declared_criteria) - evidence_criterion_ids)
        unexpected = sorted(evidence_criterion_ids - set(declared_criteria))
        if missing:
            issues.append(
                "closure evidence omits Epic acceptance criteria: " + ", ".join(missing)
            )
        if unexpected:
            issues.append(
                "closure evidence contains unknown acceptance criteria: "
                + ", ".join(unexpected)
            )

    counterevidence = evidence.get("counterevidence")
    if not isinstance(counterevidence, dict) or counterevidence.get("searched") is not True:
        issues.append("counterevidence was not explicitly searched")
    else:
        if counterevidence.get("unresolvedFindings") != []:
            issues.append("counterevidence contains unresolved findings")
        reference_issues, reference_manifests = _evidence_reference_issues(
            workspace, counterevidence.get("evidence"), "counterevidence search"
        )
        issues.extend(reference_issues)
        manifests.extend(reference_manifests)
        if reference_manifests and not any(
            item.get("kind") == "negative_test" for item in reference_manifests
        ):
            issues.append("counterevidence search has no negative_test evidence")
    if evidence.get("remainingGaps") != []:
        issues.append("closure evidence contains remaining gaps")
    if evidence.get("contradictions") != []:
        issues.append("closure evidence contains contradictions")

    black_box = evidence.get("blackBoxValidation")
    if outcome_class in {"product", "pilot"}:
        if not isinstance(black_box, dict):
            issues.append("representative black-box validation is missing")
        else:
            if black_box.get("status") != "passed":
                issues.append("representative black-box validation did not pass")
            if black_box.get("representative") is not True:
                issues.append("black-box validation is synthetic or non-representative")
            if black_box.get("operatorAssistance") is not False:
                issues.append("black-box validation required implementation-team assistance")
            for field in (
                "entryPoint",
                "scenario",
                "expectedOutcome",
                "actualOutcome",
                "performedBy",
                "startedAt",
                "completedAt",
            ):
                if not isinstance(black_box.get(field), str) or not black_box[field].strip():
                    issues.append(f"black-box validation has no {field}")
            reference_issues, reference_manifests = _evidence_reference_issues(
                workspace,
                black_box.get("evidence"),
                "black-box validation",
            )
            issues.extend(reference_issues)
            manifests.extend(reference_manifests)
            black_box_manifests = [
                item
                for item in reference_manifests
                if item.get("kind") == "black_box_result"
            ]
            if not black_box_manifests:
                issues.append("black-box validation has no black_box_result evidence")
            for manifest in black_box_manifests:
                issues.extend(
                    _black_box_record_issues(
                        manifest, "black-box validation", black_box
                    )
                )
    authority = evidence.get("decisionAuthority")
    if authority not in {"user", "portfolio_mandate"}:
        issues.append("closure evidence has no supported decision authority")
    authority_issues, authority_manifests = _evidence_reference_issues(
        workspace, evidence.get("authorityEvidence"), "closure authority"
    )
    issues.extend(authority_issues)
    manifests.extend(authority_manifests)
    issues.extend(_authority_record_issues(authority_manifests, authority, epic_id))

    evidence_set_sha256, evidence_set_issues = _evidence_set_sha256(manifests)
    issues.extend(evidence_set_issues)
    if state.get("epicClosureEvidenceSetSha256") != evidence_set_sha256:
        issues.append(
            "epicClosureEvidenceSetSha256 does not bind all current referenced evidence"
        )
    return (path if not issues else None), issues, evidence_set_sha256


def epic_closure_evidence(
    repo_root: Path, workspace: Path, state: dict[str, Any]
) -> tuple[Path | None, list[str]]:
    """Validate evidence that may truthfully authorize one Epic closure."""

    path, issues, _ = _epic_closure_evidence_analysis(repo_root, workspace, state)
    return path, issues


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
    for closure_field in (
        "epicClosureEvidence",
        "epicClosureEvidenceSha256",
        "epicClosureEvidenceSetSha256",
    ):
        candidate.pop(closure_field, None)
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


def plan_epic_closure(
    repo_root: Path,
    *,
    authority_state_path: str,
    closure_evidence_path: str,
    updated_at: str,
) -> dict[str, Any]:
    """Preview an Epic closure only after a fail-closed truth audit passes."""

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
            "Epic closure preconditions failed: " + "; ".join(mismatches)
        )
    previous_increment_id = source.get("previousIncrementId")
    if (
        not isinstance(previous_increment_id, str)
        or INCREMENT_ID_PATTERN.fullmatch(previous_increment_id) is None
    ):
        raise RuntimeTransitionError(
            "Epic closure requires canonical accepted Increment history."
        )
    _, acceptance_issues = terminal_acceptance(
        root, state_path.parent, source, previous_increment_id
    )
    if acceptance_issues:
        raise RuntimeTransitionError(
            "Accepted history is invalid: " + "; ".join(acceptance_issues)
        )
    if not isinstance(updated_at, str) or not updated_at.strip():
        raise RuntimeTransitionError("updatedAt must be a non-empty timestamp string.")

    candidate = dict(source)
    candidate.pop("uiDecision", None)
    closure_path, closure_path_issues = _contained_decision_path(
        root, state_path.parent, closure_evidence_path, "epicClosureEvidence"
    )
    if closure_path_issues or closure_path is None:
        raise RuntimeTransitionError(
            "Truthful Epic closure evidence is invalid: "
            + "; ".join(closure_path_issues)
        )
    candidate.update(
        {
            "epicStatus": "epic_complete",
            "epicClosureEvidence": closure_evidence_path,
            "epicClosureEvidenceSha256": hashlib.sha256(
                closure_path.read_bytes()
            ).hexdigest(),
            "epicClosureEvidenceSetSha256": "0" * 64,
            "updatedAt": updated_at.strip(),
        }
    )
    _, _, evidence_set_sha256 = _epic_closure_evidence_analysis(
        root, state_path.parent, candidate
    )
    if evidence_set_sha256 is None:
        raise RuntimeTransitionError(
            "Truthful Epic closure evidence is invalid: no referenced evidence set"
        )
    candidate["epicClosureEvidenceSetSha256"] = evidence_set_sha256
    closure_path, closure_issues, verified_evidence_set_sha256 = (
        _epic_closure_evidence_analysis(
            root, state_path.parent, candidate
        )
    )
    if verified_evidence_set_sha256 != evidence_set_sha256:
        closure_issues.append("referenced evidence changed during closure preview")
    if closure_issues:
        raise RuntimeTransitionError(
            "Truthful Epic closure evidence is invalid: " + "; ".join(closure_issues)
        )
    schema_issues = _schema_issues(candidate, _runtime_state_schema(root))
    if schema_issues:
        raise RuntimeTransitionError(
            "Candidate state failed schema validation: " + "; ".join(schema_issues)
        )
    candidate_payload = _json_bytes(candidate)
    return {
        "result": "planned",
        "authorityStatePath": state_path.relative_to(root).as_posix(),
        "epicId": source.get("epicId"),
        "previousIncrementId": previous_increment_id,
        "sourceStateSha256": hashlib.sha256(source_payload).hexdigest(),
        "candidateStateSha256": hashlib.sha256(candidate_payload).hexdigest(),
        "candidate": candidate,
        "epicClosureEvidence": closure_path.relative_to(root).as_posix()
        if closure_path
        else None,
        "epicClosureEvidenceSha256": candidate["epicClosureEvidenceSha256"],
        "epicClosureEvidenceSetSha256": candidate[
            "epicClosureEvidenceSetSha256"
        ],
    }


def apply_epic_closure(
    repo_root: Path,
    *,
    authority_state_path: str,
    closure_evidence_path: str,
    updated_at: str,
    expected_state_sha256: str,
    expected_closure_evidence_sha256: str,
    expected_evidence_set_sha256: str,
) -> dict[str, Any]:
    """Revalidate truth, freshness, and evidence before publishing closure."""

    plan = plan_epic_closure(
        repo_root,
        authority_state_path=authority_state_path,
        closure_evidence_path=closure_evidence_path,
        updated_at=updated_at,
    )
    if plan["sourceStateSha256"] != expected_state_sha256:
        raise RuntimeTransitionError(
            "state.json changed since preview; reload before applying Epic closure."
        )
    if (
        plan["candidate"].get("epicClosureEvidenceSha256")
        != expected_closure_evidence_sha256
    ):
        raise RuntimeTransitionError(
            "Epic closure evidence changed since preview; reload before applying closure."
        )
    if (
        plan["candidate"].get("epicClosureEvidenceSetSha256")
        != expected_evidence_set_sha256
    ):
        raise RuntimeTransitionError(
            "Referenced Epic evidence changed since preview; reload before applying closure."
        )
    state_path = _authority_state_path(repo_root.resolve(), authority_state_path)
    current_payload, _ = _read_runtime_state(state_path)
    if hashlib.sha256(current_payload).hexdigest() != expected_state_sha256:
        raise RuntimeTransitionError(
            "state.json changed immediately before Epic closure; nothing was written."
        )
    _, immediate_issues, immediate_set_sha256 = _epic_closure_evidence_analysis(
        repo_root.resolve(), state_path.parent, plan["candidate"]
    )
    if immediate_issues or immediate_set_sha256 != expected_evidence_set_sha256:
        raise RuntimeTransitionError(
            "Referenced Epic evidence changed immediately before closure; nothing was written."
        )
    candidate_payload = _json_bytes(plan["candidate"])
    _atomic_replace(state_path, candidate_payload)
    written_payload, written = _read_runtime_state(state_path)
    _, closure_issues = epic_closure_evidence(
        repo_root.resolve(), state_path.parent, written
    )
    if (
        hashlib.sha256(written_payload).hexdigest() != plan["candidateStateSha256"]
        or _schema_issues(written, _runtime_state_schema(repo_root.resolve()))
        or closure_issues
    ):
        _atomic_replace(state_path, current_payload)
        raise RuntimeTransitionError("Published Epic closure failed verification.")
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
    closure = subparsers.add_parser(
        "close", help="Preview or apply one truth-audited Epic closure."
    )
    closure.add_argument("--repo", type=Path, default=Path.cwd())
    closure.add_argument("--authority-state-path", required=True)
    closure.add_argument("--closure-evidence-path", required=True)
    closure.add_argument("--updated-at", required=True)
    closure.add_argument("--expected-state-sha256")
    closure.add_argument("--expected-closure-evidence-sha256")
    closure.add_argument("--expected-evidence-set-sha256")
    closure.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.apply:
            if not args.expected_state_sha256:
                raise RuntimeTransitionError(
                    "--apply requires --expected-state-sha256 from preview."
                )
            if args.command == "close":
                if not args.expected_closure_evidence_sha256:
                    raise RuntimeTransitionError(
                        "Epic closure --apply requires "
                        "--expected-closure-evidence-sha256 from preview."
                    )
                if not args.expected_evidence_set_sha256:
                    raise RuntimeTransitionError(
                        "Epic closure --apply requires --expected-evidence-set-sha256 from preview."
                    )
                result = apply_epic_closure(
                    args.repo,
                    authority_state_path=args.authority_state_path,
                    closure_evidence_path=args.closure_evidence_path,
                    updated_at=args.updated_at,
                    expected_state_sha256=args.expected_state_sha256,
                    expected_closure_evidence_sha256=args.expected_closure_evidence_sha256,
                    expected_evidence_set_sha256=args.expected_evidence_set_sha256,
                )
            else:
                result = apply_post_gate_e_continue(
                    args.repo,
                    authority_state_path=args.authority_state_path,
                    increment_id=args.increment_id,
                    updated_at=args.updated_at,
                    expected_state_sha256=args.expected_state_sha256,
                )
        else:
            if args.command == "close":
                result = plan_epic_closure(
                    args.repo,
                    authority_state_path=args.authority_state_path,
                    closure_evidence_path=args.closure_evidence_path,
                    updated_at=args.updated_at,
                )
            else:
                result = plan_post_gate_e_continue(
                    args.repo,
                    authority_state_path=args.authority_state_path,
                    increment_id=args.increment_id,
                    updated_at=args.updated_at,
                )
    except (OSError, RuntimeTransitionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"AIM runtime transition failed: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
