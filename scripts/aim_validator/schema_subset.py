"""Deterministic JSON Schema subset used by AIM's dependency-free validator.

The public schemas remain ordinary Draft 2020-12 JSON Schema documents. This
module implements only the structural keywords AIM publishes; product policy
belongs in the validator that calls it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


SUPPORTED_SCHEMA_KEYWORDS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "const",
    "description",
    "enum",
    "items",
    "minItems",
    "minLength",
    "pattern",
    "properties",
    "required",
    "title",
    "type",
}


@dataclass(frozen=True)
class SchemaIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def validate(instance: Any, schema: dict[str, Any]) -> list[SchemaIssue]:
    """Validate ``instance`` against AIM's supported JSON Schema subset."""

    issues: list[SchemaIssue] = []
    _validate_node(instance, schema, schema, "$", issues)
    return issues


def unsupported_keywords(schema: dict[str, Any]) -> list[SchemaIssue]:
    """Return schema keywords AIM's internal subset cannot enforce."""

    issues: list[SchemaIssue] = []
    _inspect_schema_node(schema, "$", issues)
    return issues


def _inspect_schema_node(
    schema: dict[str, Any], path: str, issues: list[SchemaIssue]
) -> None:
    for keyword, value in schema.items():
        if keyword not in SUPPORTED_SCHEMA_KEYWORDS:
            issues.append(SchemaIssue(f"{path}.{keyword}", "unsupported schema keyword"))
            continue
        if keyword in {"properties", "$defs"} and isinstance(value, dict):
            for name, child in value.items():
                if isinstance(child, dict):
                    _inspect_schema_node(child, f"{path}.{keyword}.{name}", issues)
        elif keyword in {"items", "additionalProperties"} and isinstance(value, dict):
            _inspect_schema_node(value, f"{path}.{keyword}", issues)


def _resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"only local JSON Schema references are supported: {reference}")
    node: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"JSON Schema reference does not resolve to an object: {reference}")
    return node


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    raise ValueError(f"unsupported JSON Schema type: {expected}")


def _validate_node(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    issues: list[SchemaIssue],
) -> None:
    if "$ref" in schema:
        referenced = _resolve_ref(root_schema, schema["$ref"])
        _validate_node(instance, referenced, root_schema, path, issues)
        return

    if "const" in schema and instance != schema["const"]:
        issues.append(SchemaIssue(path, f"must equal {schema['const']!r}"))

    if "enum" in schema and instance not in schema["enum"]:
        values = ", ".join(repr(value) for value in schema["enum"])
        issues.append(SchemaIssue(path, f"must be one of: {values}"))

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(instance, expected_type):
        issues.append(SchemaIssue(path, f"must be a {expected_type}"))
        return

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                issues.append(SchemaIssue(path, f"missing required property {key!r}"))

        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                _validate_node(value, properties[key], root_schema, child_path, issues)
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                issues.append(SchemaIssue(child_path, "additional property is not allowed"))
            elif isinstance(additional, dict):
                _validate_node(value, additional, root_schema, child_path, issues)

    if isinstance(instance, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(instance) < minimum:
            issues.append(SchemaIssue(path, f"must contain at least {minimum} items"))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                _validate_node(
                    value, item_schema, root_schema, f"{path}[{index}]", issues
                )

    if isinstance(instance, str):
        minimum = schema.get("minLength")
        if minimum is not None and len(instance) < minimum:
            issues.append(
                SchemaIssue(path, f"must contain at least {minimum} characters")
            )
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            issues.append(SchemaIssue(path, f"must match pattern {pattern!r}"))
