"""Repo-profile schema loading and AIM-owned product-rule validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aim_installer.yaml_lite import YamlLiteError, loads
from aim_validator.schema_subset import validate as validate_schema


REPO_PROFILE_SCHEMA_PATH = "schemas/aim-repo-profile.schema.json"
PERSONAL_HINTS_SCHEMA_PATH = "schemas/aim-personal-hints.schema.json"
SUPPORTED_PROFILE_VERSION = "0.2"
SUPPORTED_HINTS_VERSION = "0.1"

PERSONAL_HINTS_FORBIDDEN_AUTHORITY_KEYS = {
    "approvalNotes",
    "deployment",
    "deploymentRules",
    "migration",
    "migrationRules",
    "owners",
    "ownership",
    "policy",
    "risk",
    "riskZones",
    "security",
    "securityRules",
    "validation",
    "validationPolicy",
}

AIM_RUNTIME_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])\.aim(?:/[A-Za-z0-9._/-]*)?(?![A-Za-z0-9_./-])"
)

REPO_PROFILE_ALLOWED_RUNTIME_PATHS = {
    "$.aimRepoProfile.storage.workingStateLocation",
}


@dataclass(frozen=True)
class ContractIssue:
    kind: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def load_schema(repo_root: Path, relative_path: str) -> dict[str, Any]:
    path = repo_root / relative_path
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return data


def parse_yaml_document(source: str) -> Any:
    return loads(source)


def validate_repo_profile(
    data: Any, schema: dict[str, Any]
) -> list[ContractIssue]:
    issues = [
        ContractIssue("structure", issue.path, issue.message)
        for issue in validate_schema(data, schema)
    ]
    profile = data.get("aimRepoProfile") if isinstance(data, dict) else None
    if not isinstance(profile, dict):
        return issues

    version = profile.get("profileVersion")
    if version != SUPPORTED_PROFILE_VERSION:
        issues.append(
            ContractIssue(
                "product",
                "$.aimRepoProfile.profileVersion",
                f"unsupported profile version {version!r}; supported version is {SUPPORTED_PROFILE_VERSION!r}",
            )
        )

    storage = profile.get("storage")
    if isinstance(storage, dict):
        for key in ("profileLocation", "personalHintsLocation"):
            value = storage.get(key)
            if isinstance(value, str) and _is_aim_runtime_path(value):
                issues.append(
                    ContractIssue(
                        "product",
                        f"$.aimRepoProfile.storage.{key}",
                        "stable repo-awareness must not be stored under .aim/",
                    )
                )
    issues.extend(_durable_runtime_reference_issues(profile, "$.aimRepoProfile"))
    return issues


def validate_personal_hints(
    data: Any, schema: dict[str, Any]
) -> list[ContractIssue]:
    issues = [
        ContractIssue("structure", issue.path, issue.message)
        for issue in validate_schema(data, schema)
    ]
    hints = data.get("aimPersonalHints") if isinstance(data, dict) else None
    if not isinstance(hints, dict):
        return issues

    version = hints.get("hintsVersion")
    if version != SUPPORTED_HINTS_VERSION:
        issues.append(
            ContractIssue(
                "product",
                "$.aimPersonalHints.hintsVersion",
                f"unsupported Personal hints version {version!r}; supported version is {SUPPORTED_HINTS_VERSION!r}",
            )
        )

    for path, key in _walk_keys(hints, "$.aimPersonalHints"):
        if key in PERSONAL_HINTS_FORBIDDEN_AUTHORITY_KEYS:
            issues.append(
                ContractIssue(
                    "product",
                    f"{path}.{key}",
                    "Personal hints must not claim shared policy authority",
                )
            )
    issues.extend(_durable_runtime_reference_issues(hints, "$.aimPersonalHints"))
    return issues


def parse_and_validate_repo_profile(
    source: str, schema: dict[str, Any]
) -> tuple[Any | None, list[ContractIssue]]:
    try:
        data = parse_yaml_document(source)
    except (YamlLiteError, IndexError) as exc:
        return None, [ContractIssue("structure", "$", f"invalid AIM YAML: {exc}")]
    return data, validate_repo_profile(data, schema)


def parse_and_validate_personal_hints(
    source: str, schema: dict[str, Any]
) -> tuple[Any | None, list[ContractIssue]]:
    try:
        data = parse_yaml_document(source)
    except (YamlLiteError, IndexError) as exc:
        return None, [ContractIssue("structure", "$", f"invalid AIM YAML: {exc}")]
    return data, validate_personal_hints(data, schema)


def _is_aim_runtime_path(value: str) -> bool:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized == ".aim" or normalized.startswith(".aim/")


def _durable_runtime_reference_issues(value: Any, path: str) -> list[ContractIssue]:
    issues = []
    for scalar_path, scalar_value in _walk_scalar_strings(value, path):
        if scalar_path in REPO_PROFILE_ALLOWED_RUNTIME_PATHS:
            continue
        matches = sorted(set(AIM_RUNTIME_PATH_RE.findall(scalar_value)))
        if not matches:
            continue
        issues.append(
            ContractIssue(
                "product",
                scalar_path,
                "durable repo-awareness must not reference .aim/ runtime artifacts; "
                "normalize reusable knowledge into aim.profile.yaml, Personal hints, "
                "or a static docs path",
            )
        )
    return issues


def _walk_scalar_strings(value: Any, path: str):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_scalar_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_scalar_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _walk_keys(value: Any, path: str):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path, str(key)
            yield from _walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{index}]")
