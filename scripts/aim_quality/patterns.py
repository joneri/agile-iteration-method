"""Explicit concern lookup of bundled, reviewed engineering advice.

Records are attributed application advice, not instructions or authority to
change AIM roles, gates or mandates. Matching demonstrates relevance of tags,
not semantic applicability or a verified benefit from consulting this registry.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

from .files import read_evidence

MAX_BYTES = 24_000
MAX_PATTERNS = 3
TEXT_FIELDS = ("failure", "counterexample", "control", "notApplicable", "evidence")
RECORD_FIELDS = {"id", "concerns", *TEXT_FIELDS, "status", "checkedDate"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _token(value):
    _require(isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value) is not None,
             "Concerns must be lowercase tags of at most 64 letters, digits or hyphens.")
    return value


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result, "Error-pattern data has duplicate JSON keys.")
        result[key] = value
    return result


def _records():
    payload = read_evidence(Path(__file__).resolve().parent, "error_patterns.json", MAX_BYTES)
    try:
        document = json.loads(payload, object_pairs_hook=_pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError(f"Error-pattern data must be bounded valid JSON: {exc}") from exc
    _require(isinstance(document, dict) and set(document) == {"version", "patterns"}
             and type(document["version"]) is int and document["version"] == 1,
             "Error-pattern data requires version 1 and patterns.")
    records = document["patterns"]
    _require(isinstance(records, list) and len(records) <= MAX_PATTERNS,
             "Error-pattern data permits at most three records.")
    identifiers = set()
    for record in records:
        _require(isinstance(record, dict) and set(record) == RECORD_FIELDS,
                 "Error-pattern record has missing or unsupported fields.")
        identifier = record["id"]
        _require(isinstance(identifier, str)
                 and re.fullmatch(r"PIT-[A-Z0-9]+(?:-[A-Z0-9]+)*", identifier) is not None
                 and len(identifier) <= 64 and identifier not in identifiers,
                 "Error-pattern identifiers must be distinct bounded PIT-* values.")
        identifiers.add(identifier)
        concerns = record["concerns"]
        _require(isinstance(concerns, list) and 1 <= len(concerns) <= 6,
                 "Error-pattern concerns require one to six tags.")
        for concern in concerns:
            _token(concern)
        _require(len(set(concerns)) == len(concerns), "Duplicate error-pattern concern tag.")
        for field in TEXT_FIELDS:
            value = record[field]
            _require(isinstance(value, str) and bool(value.strip()) and len(value) <= 1000
                     and not any(ord(char) < 32 or ord(char) == 127 for char in value),
                     f"Error-pattern {field} requires nonempty text of at most 1000 characters without controls.")
        _require(record["status"] in ("reviewed", "withdrawn"), "Invalid error-pattern status.")
        checked = record["checkedDate"]
        _require(isinstance(checked, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked) is not None,
                 "Error-pattern checkedDate must be an ISO date.")
        try:
            date.fromisoformat(checked)
        except ValueError as exc:
            raise ValueError("Error-pattern checkedDate must be a valid calendar date.") from exc
    return records


def lookup(concerns):
    """Return at most three exact-tag matches; no reads from the consuming repo."""
    _require(isinstance(concerns, list) and 1 <= len(concerns) <= 3,
             "Supply one to three explicit concerns.")
    selected = [_token(concern) for concern in concerns]
    _require(len(set(selected)) == len(selected), "Supply distinct concerns.")
    requested = set(selected)
    records = [record for record in _records()
               if record["status"] == "reviewed" and requested.intersection(record["concerns"])]
    records.sort(key=lambda record: (-len(requested.intersection(record["concerns"])), record["id"]))
    return {"version": 1, "concerns": selected, "patterns": records[:MAX_PATTERNS],
            "advisoryOnly": True, "benefitVerified": False}
