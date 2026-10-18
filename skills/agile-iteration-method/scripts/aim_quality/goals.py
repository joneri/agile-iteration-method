# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/goals.py
"""Bounded numeric quality goals; evidence is data and never executable code.

These checks establish numeric results and unchanged source/context bindings,
not that the declared workload or measurement faithfully represents the product.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path

from .files import MAX_BYTES, read_evidence

MAX_GOALS = 32
MAX_SAMPLES = 1000
CONTEXT_FIELDS = ("workload", "environment", "method", "unit")
TEXT_FIELDS = ("outcome", *CONTEXT_FIELDS, "owner", "action", "source")
GOAL_FIELDS = {"id", *TEXT_FIELDS, "threshold", "operator", "aggregation", "minSamples"}
MEASUREMENT_FIELDS = {"goalId", *CONTEXT_FIELDS,
                      "samples", "productBindingsSha256"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, expected, label):
    _require(isinstance(value, dict) and set(value) == expected,
             f"{label} requires exactly these fields: {', '.join(sorted(expected))}.")


def _text(value, label, maximum=2000):
    _require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
             f"{label} must be nonempty text of at most {maximum} characters.")


def _number(value, label):
    _require(type(value) in (int, float), f"{label} must be a finite number, not a boolean.")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    _require(finite, f"{label} must be a finite number within the supported range.")


def _sha(value, label):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"{label} requires a SHA-256 fingerprint.")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_goals(goals):
    """Validate a list of zero to 32 frozen numeric goals, raising ValueError."""
    _require(isinstance(goals, list) and len(goals) <= MAX_GOALS,
             f"Quality goals must be a list of at most {MAX_GOALS} items.")
    identifiers = set()
    for goal in goals:
        _fields(goal, GOAL_FIELDS, "Quality goal")
        identifier = goal["id"]
        _require(isinstance(identifier, str) and len(identifier) <= 100
                 and re.fullmatch(r"KPI-[A-Z0-9]+(?:-[A-Z0-9]+)*", identifier) is not None,
                 "Quality goal requires a bounded KPI-* identifier.")
        _require(identifier not in identifiers, "Duplicate quality goal ID.")
        identifiers.add(identifier)
        for name in TEXT_FIELDS:
            _text(goal[name], f"Quality goal {name}")
        _number(goal["threshold"], "Quality goal threshold")
        _require(goal["operator"] in ("<=", ">="), "Quality goal operator must be <= or >=.")
        _require(goal["aggregation"] in ("median", "min", "max"),
                 "Quality goal aggregation must be median, min or max.")
        _require(type(goal["minSamples"]) is int and 3 <= goal["minSamples"] <= MAX_SAMPLES,
                 f"Quality goal minSamples must be an integer from 3 to {MAX_SAMPLES}.")


def _reference(reference, *, measurement):
    _fields(reference, {"path", "sha256"}, "Evidence reference")
    relative = reference["path"]
    _text(relative, "Evidence path", 1000)
    path = Path(relative)
    _require(not path.is_absolute() and ".." not in path.parts and "\\" not in relative
             and path.as_posix() == relative and "\x00" not in relative,
             "Evidence path must use canonical contained relative spelling.")
    _require(relative != ".aim/product-backlog.json", "Evidence must be independent of the product backlog.")
    if measurement:
        _require(relative.startswith(".aim/"), "Quality measurements must be inside .aim.")
    _sha(reference["sha256"], "Evidence reference")


def _read_reference(repo, reference):
    relative = reference["path"]
    try:
        ledger = repo / ".aim/product-backlog.json"
        _require(not ledger.exists() or not ledger.samefile(repo / relative),
                 "Evidence must be independent of the product backlog file identity.")
        payload = read_evidence(repo, relative, MAX_BYTES)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot safely read quality evidence {relative}: {exc}") from exc
    return payload, hashlib.sha256(payload).hexdigest() == reference["sha256"]


def _pairs(pairs):
    result = {}
    for name, value in pairs:
        _require(name not in result, "Quality measurement has duplicate JSON keys.")
        result[name] = value
    return result


def _report_context(report, scope_sha256):
    """Resolve an explicit reference to the caller's validated frozen scope.

    This avoids copying plan labels into every record. It does not establish
    that the declared experiment ran; raw values and independent review remain
    necessary. Never resolve a report against an unbound or different scope.
    """
    if "context" not in report:
        return None
    context = report["context"]
    _fields(context, {"scopeSha256", "productBindingsSha256"}, "Quality report context")
    _sha(context["scopeSha256"], "Quality report scope")
    _sha(context["productBindingsSha256"], "Quality report product binding")
    _require(scope_sha256 is not None and context["scopeSha256"] == scope_sha256,
             "Quality report context must match the validated approved scope.")
    return context


def _measurements(payload, *, goals=None, scope_sha256=None):
    try:
        result = json.loads(payload, object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError(f"Quality measurement must be bounded valid JSON: {exc}") from exc
    expected = {"qualityMeasurementVersion", "measurements"}
    # Reuse one final evidence artifact at the existing criterion/Epic gates.
    # Those consumers validate their own explicit coverage; it is never inferred
    # from a numeric pass or used to manufacture a missing observation here.
    expected |= {key for key in ("context", "criterionCoverage", "epicCoverage") if key in result}
    if "qualityCheckVersion" in result:
        expected |= {"qualityCheckVersion", "checks"}
        _require(result["qualityCheckVersion"] == "1.0" and isinstance(result.get("checks"), list)
                 and 1 <= len(result["checks"]) <= MAX_GOALS, "Invalid consolidated quality checks.")
    _fields(result, expected, "Quality measurement envelope")
    _require(result["qualityMeasurementVersion"] == "1.0", "Unsupported quality measurement version.")
    context = _report_context(result, scope_sha256)
    records = result["measurements"]
    minimum = 0 if "qualityCheckVersion" in result else 1
    _require(isinstance(records, list) and minimum <= len(records) <= MAX_GOALS,
             f"Measurement envelope must contain {minimum}–{MAX_GOALS} records.")
    expanded = []
    for measurement in records:
        if context is not None:
            _fields(measurement, {"goalId", "unit", "samples"}, "Compact quality measurement")
            identifier = measurement["goalId"]
            _require(isinstance(identifier, str) and goals is not None and identifier in goals,
                     "Quality measurement refers to an unknown goal.")
            measurement = {**measurement,
                           **{k: goals[identifier][k] for k in ("workload", "environment", "method")},
                           "productBindingsSha256": context["productBindingsSha256"]}
        _fields(measurement, MEASUREMENT_FIELDS, "Quality measurement")
        _text(measurement["goalId"], "Measurement goalId", 100)
        for name in CONTEXT_FIELDS:
            _text(measurement[name], f"Measurement {name}")
        _sha(measurement["productBindingsSha256"], "Measurement product binding")
        samples = measurement["samples"]
        _require(isinstance(samples, list) and 1 <= len(samples) <= MAX_SAMPLES,
                 f"Measurement samples must contain 1–{MAX_SAMPLES} raw numbers.")
        for sample in samples:
            _number(sample, "Measurement sample")
        expanded.append(measurement)
    return expanded


def _aggregate(samples, aggregation):
    ordered = sorted(samples)
    if aggregation == "min":
        return ordered[0]
    if aggregation == "max":
        return ordered[-1]
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    # Preserve the exact midpoint for comparison: rounding can cross a threshold.
    return (Fraction(ordered[middle - 1]) + Fraction(ordered[middle])) / 2


def assess(repo, goals, measurement_refs, product_bindings, *, read_reference=None,
           scope_sha256=None):
    """Return per-goal state/detail records; malformed or unsafe data raises.

    States: passed, failed, unmeasured, stale, mismatch. Missing references are
    unmeasured; unreadable referenced artifacts are errors. Bindings use the same
    canonical JSON digest as aim_stories.digest, preserving the array order.
    Product files and measurement files are each read at most once in this call.
    Optional read_reference(repo, reference) -> (payload, fresh) is a trusted
    internal integration hook for an invocation-scoped verified reader, never an
    externally supplied proof. It must preserve safe reads and hash validation;
    payload may be None for product sources, but measurement payloads are bytes.
    The default reader independently checks the actual files.
    scope_sha256, when supplied, must come from the validated approved delivery;
    it permits compact reports to reference its frozen context by ID.
    """
    validate_goals(goals)
    repo = Path(repo)
    reader = _read_reference if read_reference is None else read_reference
    _require(isinstance(measurement_refs, list) and len(measurement_refs) <= MAX_GOALS,
             f"Quality measurements must be a list of at most {MAX_GOALS} references.")
    _require(isinstance(product_bindings, list) and len(product_bindings) <= 256,
             "Product bindings must be a list of at most 256 references.")
    known = {goal["id"]: goal for goal in goals}
    measurements = {}
    paths = set()
    for reference in measurement_refs:
        _reference(reference, measurement=True)
        _require(reference["path"] not in paths, "Duplicate quality measurement path.")
        paths.add(reference["path"])
        payload, fresh = reader(repo, reference)
        # Never interpret changed bytes as authentic evidence for another goal.
        _require(fresh, f"Quality measurement evidence changed: {reference['path']}.")
        for measurement in _measurements(payload, goals=known, scope_sha256=scope_sha256):
            identifier = measurement["goalId"]
            _require(identifier in known, "Quality measurement refers to an unknown goal.")
            _require(identifier not in measurements, "Duplicate measurement for quality goal.")
            measurements[identifier] = measurement
    if not goals:
        return []
    binding_paths = set()
    bindings_fresh = bool(product_bindings)
    for reference in product_bindings:
        _reference(reference, measurement=False)
        _require(reference["path"] not in binding_paths, "Duplicate product binding path.")
        _require(reference["path"] not in paths, "A measurement cannot bind itself as product source.")
        binding_paths.add(reference["path"])
        _, fresh = reader(repo, reference)
        bindings_fresh = bindings_fresh and fresh
    binding_digest = _digest(product_bindings)
    results = []
    for goal in goals:
        record = {"goalId": goal["id"], "state": "unmeasured", "detail": "No measurement supplied."}
        measurement = measurements.get(goal["id"])
        if measurement is not None:
            if not bindings_fresh or measurement["productBindingsSha256"] != binding_digest:
                record.update(state="stale", detail="Measurement does not bind the current product sources.")
            elif any(measurement[name] != goal[name] for name in CONTEXT_FIELDS):
                record.update(state="mismatch", detail="Measurement workload, environment, method or unit differs from the goal.")
            elif len(measurement["samples"]) < goal["minSamples"]:
                record.update(detail=f"At least {goal['minSamples']} raw samples are required.")
            else:
                value = _aggregate(measurement["samples"], goal["aggregation"])
                passed = value <= goal["threshold"] if goal["operator"] == "<=" else value >= goal["threshold"]
                # JSON has no rational type; only presentation is rounded, never
                # the comparison. The detail retains the exact midpoint.
                displayed = float(value) if isinstance(value, Fraction) else value
                record.update(state="passed" if passed else "failed", value=displayed,
                              sampleCount=len(measurement["samples"]), unit=goal["unit"],
                              detail=f"{goal['aggregation']} {value} {goal['unit']} {goal['operator']} {goal['threshold']}: {'passed' if passed else 'failed'}.")
        results.append(record)
    return results
