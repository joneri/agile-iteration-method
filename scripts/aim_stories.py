#!/usr/bin/env python3
"""PO-owned Epics, TDO-owned Stories and coherent cross-Epic delivery execution.

The caller supplies real decisions and evidence. This helper validates their
scope and persistence; it cannot authenticate the human behind an authority
record. It never changes a legacy Epic workspace or invents acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from aim_quality.files import read_evidence
from aim_quality.goals import validate_goals, assess as assess_goals, _sha
from aim_quality.delivery import validate_plan, assess_checks, stages
from aim_quality.delivery_policy import (DEFAULT_POLICY, normalize_policy, parse_owner_decision,
                                         validate_authority_binding, validate_owner_decision)
from aim_quality.review import check_review
from aim_quality.graph import (change_activity, project_graph, validate_activity_receipts,
                               validate_execution_plan)
from aim_quality.skills import BUNDLE_ROOT
from aim_runtime_lock import runtime_lock
from aim_validator.schema_subset import validate as schema_validate

FILE = ".aim/product-backlog.json"
MAX_BYTES = 1_000_000
MAX_ITEMS = 256
COLUMNS = (("backlog", "Backlog"), ("ready", "Ready"),
           ("in_progress", "In progress"), ("review", "Review"),
           ("validation", "Validation"), ("acceptance", "Acceptance"),
           ("done", "Done"))
PHASES = {"planned", "in_progress", "review", "validation", "acceptance", "accepted", "cancelled", "blocked"}
COMMANDS = ("import", "refine", "plan", "approve", "review", "validate", "acceptance",
            "accept", "measure", "rework", "cancel", "block", "unblock", "close-epic", "activity")


class StoryError(ValueError):
    """A requirements or delivery operation could not be applied safely."""


def validate_quality_plan(*args, **kwargs):
    try:
        validate_plan(*args, **kwargs)
    except ValueError as exc:
        raise StoryError(str(exc)) from exc


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require(condition, message):
    if not condition:
        raise StoryError(message)


def text(value, label, maximum=2000):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
            f"{label} must be non-empty text of at most {maximum} characters.")
    return value


def fields(value, required, optional=()):
    require(isinstance(value, dict), "Expected an object.")
    require(set(required) <= set(value), "Missing fields: " + ", ".join(sorted(set(required) - set(value))))
    require(set(value) <= set(required) | set(optional),
            "Unsupported fields: " + ", ".join(sorted(set(value) - set(required) - set(optional))))


def identity(value, prefix):
    require(isinstance(value, str) and len(value) <= 100
            and re.fullmatch(prefix + r"-[A-Z0-9]+(?:-[A-Z0-9]+)*", value) is not None,
            f"Expected a bounded {prefix}-* identifier.")
    return value


def unique(items, label):
    require(len(items) == len(set(items)), f"Duplicate {label}.")


def criteria(value):
    require(isinstance(value, list) and 1 <= len(value) <= 64,
            "Acceptance criteria must contain 1–64 items.")
    for item in value:
        fields(item, ("id", "text"))
        identity(item["id"], "AC")
        text(item["text"], "Criterion")
    unique([item["id"] for item in value], "criterion IDs")


def _schema():
    root = Path(__file__).resolve().parents[1]
    for relative in ("schemas/aim-product-backlog.schema.json", "references/schemas/aim-product-backlog.schema.json"):
        path = root / relative
        if path.is_file():
            return json.loads(path.read_text())
    raise StoryError("Trusted product backlog schema is unavailable.")


def _empty():
    return {"productBacklogVersion": "1.0", "revision": 0, "updatedAt": "initial",
            "intents": [], "epics": [], "stories": [], "deliveries": []}


def _story_snapshot(story):
    return {key: copy.deepcopy(story[key]) for key in
            ("id", "epicId", "title", "persona", "need", "benefit", "acceptanceCriteria", "revision")}


def _epic_snapshot(epic):
    return {key: copy.deepcopy(epic[key]) for key in
            ("id", "intentId", "title", "outcome", "outcomeClass", "nonGoals", "acceptanceCriteria", "revision")}


def _intent_snapshot(intent):
    return {key: copy.deepcopy(intent[key]) for key in ("id", "statement", "revision")}


def _scope(delivery):
    result = {key: delivery[key] for key in ("id", "title", "goal", "stories", "epics", "intents", "planEvidence")}
    for key in ("qualityGoals", "qualityPlan", "executionPlan", "deliveryPolicy"):
        if key in delivery:
            result[key] = delivery[key]
    return result


def _acceptance_scope(delivery):
    result = {key: delivery[key] for key in
              ("scopeSha256", "approval", "productBindings", "reviewEvidence", "validationEvidence", "criterionEvidence")}
    if "qualityMeasurements" in delivery:
        result["qualityMeasurements"] = delivery["qualityMeasurements"]
    for key in ("coreVerification", "coreVerificationHistory"):
        if key in delivery:
            result[key] = delivery[key]
    return result


def _by_id(document, collection, identifier):
    matches = [item for item in document[collection] if item["id"] == identifier]
    require(len(matches) == 1, f"Unknown {collection} identity: {identifier}.")
    return matches[0]


RAW_OBSERVATION_CACHE_BYTES = 4 * MAX_BYTES


class _EvidenceCache(dict):
    """Invocation-local hashes; retain only active quality/review payloads."""
    def __init__(self, retained_paths, context_paths=(), measurement_paths=()):
        super().__init__()
        self.retained_paths = set(retained_paths)
        self.payloads = {}
        self.context_paths = set(context_paths)
        self.quality_contexts = {}
        self.measurement_paths = set(measurement_paths)
        self.measurement_references = dict(measurement_paths) if isinstance(measurement_paths, dict) else {}
        self.raw_references = {}
        self.raw_paths = set()
        self.owner_decisions = {}


def _coverage_paths(request):
    """Paths whose explicit quality context a criterion consumer must honor."""
    paths = set()
    if not isinstance(request, dict):
        return paths
    ref = request.get("criteriaFrom")
    if isinstance(ref, dict) and isinstance(ref.get("path"), str):
        paths.add(ref["path"])
    criteria = request.get("criteria", [])
    for criterion in criteria if isinstance(criteria, list) else []:
        refs = criterion.get("evidence", []) if isinstance(criterion, dict) else []
        for ref in refs if isinstance(refs, list) else []:
            if isinstance(ref, dict) and isinstance(ref.get("path"), str):
                paths.add(ref["path"])
    return paths


def _remember_quality_context(cache, path, payload):
    if cache is None or path not in cache.context_paths:
        return
    duplicate = False
    def pairs(items):
        nonlocal duplicate
        result = {}
        for key, value in items:
            duplicate = duplicate or key in result
            result[key] = value
        return result
    try:
        report = json.loads(payload, object_pairs_hook=pairs)
    except (ValueError, UnicodeError, RecursionError):
        return  # Opaque pre-existing logs and other evidence remain supported.
    if not isinstance(report, dict) or "context" not in report or not (
            "qualityMeasurementVersion" in report or "qualityCheckVersion" in report):
        return
    try:
        require(not duplicate, "Duplicate JSON keys in scoped quality evidence.")
        context = report["context"]
        fields(context, ("scopeSha256", "productBindingsSha256"))
        _sha(context["scopeSha256"], "Quality evidence scope")
        _sha(context["productBindingsSha256"], "Quality evidence source binding")
        cache.quality_contexts[path] = dict(context)
    except ValueError as exc:
        cache.quality_contexts[path] = {"error": str(exc)}


def _require_coverage_context(cache, reference, scope_sha256, binding_sha256):
    context = cache.quality_contexts.get(reference["path"])
    if context is None:
        return
    require("error" not in context, "Invalid scoped quality evidence: " + context.get("error", ""))
    require(scope_sha256 is not None and binding_sha256 is not None,
            "Delivery-scoped quality evidence cannot establish broader Epic coverage.")
    require(context["scopeSha256"] == scope_sha256,
            "Criterion quality evidence refers to another approved scope.")
    require(context["productBindingsSha256"] == binding_sha256,
            "Criterion quality evidence does not bind the reviewed product sources.")


def _verification_cache(document, request=None, *, command=None):
    retained = {ref["path"] for delivery in document.get("deliveries", [])
                if delivery["status"] not in {"accepted", "cancelled"}
                for record in (delivery, delivery.get("coreVerification", {}))
                for ref in record.get("qualityMeasurements", [])}
    for delivery in document.get("deliveries", []):
        if (delivery["status"] not in {"accepted", "cancelled"}
                and "reviewPolicy" in delivery.get("qualityPlan", {})):
            refs = delivery.get("reviewEvidence", [])
            if refs:
                retained.add(refs[0]["path"])
            if command == "validate" and isinstance(request, dict) and request.get("deliveryId") == delivery["id"]:
                refs = request.get("evidence", [])
                if isinstance(refs, list) and refs and isinstance(refs[0], dict) and isinstance(refs[0].get("path"), str):
                    retained.add(refs[0]["path"])
    if isinstance(request, dict):
        values = request.get("qualityMeasurements", [])
        if isinstance(values, list):
            retained.update(ref["path"] for ref in values if isinstance(ref, dict)
                            and isinstance(ref.get("path"), str))
        ref = request.get("criteriaFrom")
        if isinstance(ref, dict) and isinstance(ref.get("path"), str):
            retained.add(ref["path"])
    measurements = {ref["path"]: ref for delivery in document.get("deliveries", [])
                    for record in (delivery, delivery.get("coreVerification", {}),
                                   *delivery.get("coreVerificationHistory", []), *delivery.get("reworkHistory", []))
                    for ref in record.get("qualityMeasurements", [])}
    if isinstance(request, dict):
        measurements.update({ref["path"]: ref for ref in request.get("qualityMeasurements", [])
                             if isinstance(ref, dict) and isinstance(ref.get("path"), str)})
    return _EvidenceCache(retained, _coverage_paths(request), measurements)


def _finish_verification(repo, cache):
    for path, (before, _) in cache.items():
        try:
            require(before == _evidence_stamp(repo, path), f"Evidence changed during verification: {path}.")
        except OSError as exc:
            raise StoryError(f"Evidence changed during verification: {path}: {exc}") from exc


def _evidence_stamp(repo, relative):
    """Check every component, retaining identity and regular-file change stamps.

    This is invocation-local freshness detection, never a persistent trust cache.
    The content read still uses the descriptor-based contained-file reader.
    """
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts and bool(path.parts),
            "Evidence path must be relative and contained.")
    current = Path(repo).resolve()
    stamps = []
    for i, component in enumerate(path.parts):
        current = current / component
        metadata = current.lstat()
        require(not stat.S_ISLNK(metadata.st_mode)
                and not getattr(metadata, "st_file_attributes", 0) & 1024,
                "Evidence traverses a link or reparse point.")
        final = i == len(path.parts) - 1
        require(stat.S_ISREG(metadata.st_mode) if final else stat.S_ISDIR(metadata.st_mode),
                "Evidence requires regular files and directory ancestors.")
        stamp = (metadata.st_dev, metadata.st_ino, metadata.st_mode)
        if final:
            stamp += (metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)
        stamps.append(stamp)
    return tuple(stamps)


def _ref(repo, reference, *, product=False, cache=None):
    fields(reference, ("path", "sha256"))
    path = text(reference["path"], "Evidence path", 1000)
    require(Path(path).as_posix() == path, "Evidence paths must use canonical relative spelling.")
    require((product or path.startswith(".aim/")) and path != FILE and "\\" not in path,
            "Evidence must be an independent artifact inside .aim.")
    require(isinstance(reference["sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]) is not None,
            "Evidence requires a SHA-256 fingerprint.")
    # All cached paths are checked again at the end of this verification.
    # Repeating path traversal for each criterion defeats the bounded read set.
    if cache is not None and path in cache:
        require(cache[path][1] == reference["sha256"], f"Evidence changed: {path}.")
        return copy.deepcopy(reference)
    try:
        ledger = Path(repo) / FILE
        require(not ledger.exists() or not ledger.samefile(Path(repo) / path),
                "Evidence must be independent of the product backlog file identity.")
        before = _evidence_stamp(repo, path)
        payload = read_evidence(repo, path, MAX_BYTES)
        require(before == _evidence_stamp(repo, path), f"Evidence changed while reading: {path}.")
        actual_hash = hashlib.sha256(payload).hexdigest()
        if cache is not None:
            _remember_quality_context(cache, path, payload)
            cache[path] = (before, actual_hash)
            if path in cache.measurement_paths:
                try:
                    report = json.loads(payload)
                except (ValueError, UnicodeError):
                    report = None  # Historical non-check evidence stays opaque.
                refs = []
                if isinstance(report, dict) and report.get("qualityCheckVersion") == "1.0":
                    items = report.get("checks", [])
                    require(isinstance(items, list) and len(items) <= 32, "Invalid raw observation check list.")
                    refs = [item["raw"] for item in items if isinstance(item, dict) and "raw" in item]
                    for raw in refs:
                        fields(raw, ("path", "sha256"))
                        text(raw["path"], "Raw observation evidence path", 1000)
                    if path in cache.retained_paths:
                        for raw in refs:
                            cache.retained_paths.add(raw["path"])
                            cache.raw_paths.add(raw["path"])
                cache.raw_references[path] = refs
            if path in cache.retained_paths:
                require(sum(len(v) for p, v in cache.payloads.items() if p in cache.raw_paths)
                        + (len(payload) if path in cache.raw_paths else 0) <= RAW_OBSERVATION_CACHE_BYTES,
                        "Raw observation cache exceeds its bounded memory budget.")
                cache.payloads[path] = payload
    except (OSError, ValueError) as exc:
        raise StoryError(f"Cannot safely read evidence {path}: {exc}") from exc
    require(actual_hash == reference["sha256"],
            f"Evidence changed: {path}.")
    return copy.deepcopy(reference)


def _refs(repo, values, *, product=False, cache=None):
    maximum = 256 if product else 64
    require(isinstance(values, list) and 1 <= len(values) <= maximum,
            f"Supply 1–{maximum} {'product source' if product else 'evidence'} references.")
    result = [_ref(repo, value, product=product, cache=cache) for value in values]
    unique([item["path"] for item in result], "evidence paths")
    return result


def _owner_authority(value, delivery, operation):
    try:
        validate_authority_binding(value, delivery.get("deliveryPolicy") if delivery else None, operation)
    except ValueError as exc:
        prefix = "Delivery has no matching user acceptance or delegated owner decision: " if operation == "accept" else ""
        raise StoryError(prefix + str(exc)) from exc


def _authority(repo, value, scope, *, cache=None, delivery=None, operation=None):
    fields(value, ("kind", "path", "sha256", "scopeSha256"), ("id", "session"))
    _owner_authority(value, delivery, operation)
    require(value["scopeSha256"] == scope, "Authority refers to a stale or different scope.")
    _ref(repo, {key: value[key] for key in ("path", "sha256")}, cache=cache)
    if value["kind"] == "agent":
        _owner_decision_evidence(repo, value, delivery, operation, cache=cache)
    return copy.deepcopy(value)


def _owner_decision_evidence(repo, value, delivery, operation, *, cache=None):
    decisions = cache.owner_decisions if cache is not None else {}
    key = (value["path"], value["sha256"])
    try:
        if key not in decisions:
            payload = read_evidence(repo, value["path"], 16384)
            require(hashlib.sha256(payload).hexdigest() == value["sha256"],
                    "Owner decision evidence changed while reading.")
            decisions[key] = parse_owner_decision(payload)
        validate_owner_decision(decisions[key], value, delivery["id"], operation)
    except ValueError as exc:
        raise StoryError(str(exc)) from exc


def _criterion_evidence(repo, values, expected, *, stories, cache=None,
                        scope_sha256=None, binding_sha256=None):
    require(isinstance(values, list) and len(values) == len(expected),
            "Evidence must cover every selected acceptance criterion exactly once.")
    if cache is None:
        cache = _EvidenceCache([], _coverage_paths({"criteria": values}))
    result = []
    actual = []
    for value in values:
        fields(value, ("storyId", "criterionId", "evidence") if stories else ("criterionId", "evidence"))
        key = (value["storyId"], value["criterionId"]) if stories else value["criterionId"]
        actual.append(key)
        refs = _refs(repo, value["evidence"], cache=cache)
        for ref in refs:
            _require_coverage_context(cache, ref, scope_sha256, binding_sha256)
        result.append({**value, "evidence": refs})
    unique(actual, "criterion evidence")
    require(set(actual) == set(expected), "Criterion evidence does not match the approved requirements.")
    return result


def _one_input(request, first, second):
    require((first in request) != (second in request),
            f"Supply exactly one of {first} or {second}.")


def _source_bindings(repo, paths, *, cache=None):
    """Freeze explicitly selected current sources at entry to review."""
    require(isinstance(paths, list) and 1 <= len(paths) <= 256, "Supply 1–256 source paths.")
    for path in paths:
        text(path, "Source path", 1000)
    unique(paths, "source paths")
    bindings = []
    for path in paths:
        try:
            before = _evidence_stamp(repo, path)
            # Cache entries must satisfy the same independence check as _ref.
            # Otherwise a backlog hard link could seed an apparently valid ref.
            ledger = Path(repo) / FILE
            require(not ledger.exists() or not ledger.samefile(Path(repo) / path),
                    "Evidence must be independent of the product backlog file identity.")
            if cache is not None and path in cache:
                require(before == cache[path][0], f"Source changed while binding: {path}.")
                fingerprint = cache[path][1]
            else:
                payload = read_evidence(repo, path, MAX_BYTES)
                fingerprint = hashlib.sha256(payload).hexdigest()
                if cache is not None:
                    _remember_quality_context(cache, path, payload)
                    cache[path] = (before, fingerprint)
                    if path in cache.retained_paths:
                        cache.payloads[path] = payload
            require(before == _evidence_stamp(repo, path), f"Source changed while reading: {path}.")
        except (OSError, ValueError) as exc:
            raise StoryError(f"Cannot safely bind source {path}: {exc}") from exc
        bindings.append({"path": path, "sha256": fingerprint})
    return _refs(repo, bindings, product=True, cache=cache)


def _coverage_evidence(repo, request, expected, *, stories, epic_id=None, cache=None,
                       scope_sha256=None, binding_sha256=None):
    """Expand an explicit coverage declaration; never infer proof from test counts.

    Only request syntax changes. Persist the same criterion/reference records as
    the full input form, with the report's supplied hash (never a refreshed hash).
    """
    _one_input(request, "criteria", "criteriaFrom")
    if cache is None:
        paths = _coverage_paths(request)
        cache = _EvidenceCache(paths if "criteriaFrom" in request else [], paths)
    if "criteria" in request:
        return _criterion_evidence(repo, request["criteria"], expected, stories=stories, cache=cache,
                                   scope_sha256=scope_sha256, binding_sha256=binding_sha256)
    reference = request["criteriaFrom"]
    require(isinstance(reference, dict), "Criterion coverage requires an evidence reference.")
    text(reference.get("path"), "Criterion coverage path", 1000)
    ref = _ref(repo, reference, cache=cache)
    _require_coverage_context(cache, ref, scope_sha256, binding_sha256)
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate key in criterion coverage JSON.")
            result[key] = value
        return result
    try:
        report = json.loads(cache.payloads[ref["path"]], object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise StoryError(f"Invalid criterion coverage JSON: {exc}") from exc
    require(isinstance(report, dict), "Criterion coverage report must be an object.")
    if stories:
        coverage = report.get("criterionCoverage")
        selected = {story_id for story_id, _ in expected}
        require(isinstance(coverage, dict) and set(coverage) == selected,
                "Criterion coverage must match the selected Stories exactly.")
        for story_id in selected:
            actual = coverage[story_id]
            wanted = {criterion_id for sid, criterion_id in expected if sid == story_id}
            require(isinstance(actual, dict) and set(actual) == wanted,
                    "Criterion coverage must match every selected criterion exactly.")
        records = []
        for story_id, criterion_id in expected:
            text(coverage[story_id][criterion_id], "Criterion coverage assessment", 4000)
            records.append({"storyId": story_id, "criterionId": criterion_id, "evidence": [copy.deepcopy(ref)]})
        return records
    epics = report.get("epicCoverage")
    require(isinstance(epics, dict) and epic_id in epics,
            "Epic coverage must explicitly identify the requested Epic.")
    coverage = epics[epic_id]
    require(isinstance(coverage, dict) and set(coverage) == set(expected),
            "Epic coverage must match every Epic criterion exactly.")
    for criterion_id in expected:
        text(coverage[criterion_id], "Criterion coverage assessment", 4000)
    return [{"criterionId": criterion_id, "evidence": [copy.deepcopy(ref)]} for criterion_id in expected]


def validate_document(document):
    """Validate structure and relationships; no repository reads or writes."""
    issues = schema_validate(document, _schema())
    require(not issues, "Invalid product backlog: " + "; ".join(str(item) for item in issues[:8]))
    require(document["revision"] >= 0, "Store revision must not be negative.")
    for collection, prefix in (("intents", "INT"), ("epics", "EPIC"), ("stories", "US"), ("deliveries", "DI")):
        unique([item["id"] for item in document[collection]], collection + " IDs")
        for item in document[collection]:
            identity(item["id"], prefix)
            if collection != "deliveries":
                require(item["revision"] >= 1, "Requirement revisions must be positive.")
    intents = {item["id"]: item for item in document["intents"]}
    epics = {item["id"]: item for item in document["epics"]}
    stories = {item["id"]: item for item in document["stories"]}
    for epic in epics.values():
        require(epic["intentId"] in intents, "Epic references an unknown Intent.")
        criteria(epic["acceptanceCriteria"])
        criteria(epic["originalAcceptanceCriteria"])
    for story in stories.values():
        require(story["priority"] >= 1, "Story priority must be positive.")
        require(story["epicId"] in epics, "Story references an unknown Epic.")
        criteria(story["acceptanceCriteria"])
        criteria(story["originalAcceptanceCriteria"])
    ownership = {}
    accepted = {}
    require(sum(item["status"] not in {"accepted", "cancelled"} for item in document["deliveries"]) <= 1,
            "Only one nonterminal delivery may run at a time.")
    for delivery in document["deliveries"]:
        if "executionPlan" in delivery:
            try:
                validate_execution_plan(delivery["executionPlan"], delivery["stories"])
                validate_activity_receipts(delivery)
            except ValueError as exc:
                raise StoryError(str(exc)) from exc
        if "deliveryPolicy" in delivery:
            try:
                require(normalize_policy(delivery["deliveryPolicy"]) == delivery["deliveryPolicy"],
                        "Stored delivery policy must be normalized.")
            except ValueError as exc:
                raise StoryError(str(exc)) from exc
        validate_goals(delivery.get("qualityGoals", []))
        if "qualityPlan" in delivery:
            validate_quality_plan(delivery["qualityPlan"], delivery.get("qualityGoals", []), delivery["stories"])
        require(delivery["scopeSha256"] == digest(_scope(delivery)), "Delivery scope fingerprint is invalid.")
        unique([item["id"] for item in delivery["stories"]], "selected Stories")
        unique([item["id"] for item in delivery["epics"]], "selected Epics")
        unique([item["id"] for item in delivery["intents"]], "selected Intents")
        require({item["epicId"] for item in delivery["stories"]} == {item["id"] for item in delivery["epics"]},
                "Delivery Epic snapshots do not match its Stories.")
        require({item["intentId"] for item in delivery["epics"]} == {item["id"] for item in delivery["intents"]},
                "Delivery Intent snapshots do not match its Epics.")
        if delivery["status"] == "cancelled":
            continue
        effective = delivery.get("blockedFrom") if delivery["status"] == "blocked" else delivery["status"]
        require(effective in PHASES - {"blocked", "cancelled"}, "Invalid blocked phase.")
        for snapshot in delivery["stories"]:
            require(snapshot["id"] in stories, "Delivery references an unknown Story.")
            story = stories[snapshot["id"]]
            require(snapshot == _story_snapshot(story), "Selected Story changed after planning.")
            require(story["id"] not in ownership, "A Story belongs to overlapping deliveries.")
            ownership[story["id"]] = delivery["id"]
            expected_status = "done" if effective == "accepted" else "ready" if effective == "planned" else effective
            require(story["status"] == expected_status, "Story phase contradicts its delivery.")
            if effective == "accepted":
                accepted[story["id"]] = delivery
        for snapshot in delivery["epics"]:
            require(snapshot["id"] in epics, "Delivery references an unknown Epic.")
            if effective != "accepted":
                require(snapshot == _epic_snapshot(epics[snapshot["id"]]), "Selected Epic changed after planning.")
        for snapshot in delivery["intents"]:
            require(snapshot["id"] in intents, "Delivery references an unknown Intent.")
            if effective != "accepted":
                require(snapshot == _intent_snapshot(intents[snapshot["id"]]), "Selected Intent changed after planning.")
        if effective != "planned":
            require("approval" in delivery, "Delivery has no Gate A/B authority.")
            _owner_authority(delivery["approval"], delivery, "approve")
            require(delivery["approval"]["scopeSha256"] == delivery["scopeSha256"], "Approval scope mismatch.")
        if effective in {"validation", "acceptance", "accepted"}:
            require(bool(delivery.get("reviewEvidence")), "Delivery requires passed review evidence.")
        if effective in {"review", "validation", "acceptance", "accepted"}:
            require(bool(delivery.get("productBindings")), "Delivery requires product source bindings.")
        if effective in {"acceptance", "accepted"}:
            require(bool(delivery.get("validationEvidence")) and bool(delivery.get("criterionEvidence")),
                    "Delivery requires validation and criterion evidence.")
            expected = {(story["id"], ac["id"]) for story in delivery["stories"] for ac in story["acceptanceCriteria"]}
            actual = [(item["storyId"], item["criterionId"]) for item in delivery["criterionEvidence"]]
            require(len(actual) == len(expected) and set(actual) == expected, "Incomplete delivery criterion evidence.")
            require(not delivery.get("qualityGoals") or bool(delivery.get("qualityMeasurements"))
                    or bool(delivery.get("coreVerification")),
                    "Delivery requires measured quality goals.")
            require(delivery.get("acceptanceSha256") == digest(_acceptance_scope(delivery)), "Acceptance scope mismatch.")
        if effective == "accepted":
            _owner_authority(delivery.get("acceptance", {}), delivery, "accept")
            require(delivery.get("acceptance", {}).get("scopeSha256") == delivery["acceptanceSha256"],
                    "Delivery has no matching user acceptance.")
    for story in stories.values():
        if story["status"] not in {"draft", "ready"}:
            require(story["id"] in ownership, "Story lifecycle has no delivery evidence.")
    for epic in epics.values():
        if epic["status"] == "closed":
            require(epic.get("closure", {}).get("authority", {}).get("kind") == "user",
                    "Epic closure requires supplied user authority.")
            members = [item for item in stories.values() if item["epicId"] == epic["id"]]
            require(bool(members) and all(item["id"] in accepted for item in members), "Closed Epic has unfinished Stories.")
            require("closure" in epic, "Epic closure requires explicit evidence and authority.")
            expected = {item["id"] for item in epic["acceptanceCriteria"]}
            actual = [item["criterionId"] for item in epic["closure"]["criteria"]]
            require(len(actual) == len(expected) and set(actual) == expected, "Incomplete Epic closure evidence.")
            require(epic["closure"]["authority"]["scopeSha256"] == digest(_closure_scope(document, epic, epic["closure"]["criteria"])),
                    "Epic closure scope mismatch.")


def _quality_refs(repo, values, *, cache):
    refs = _refs(repo, values, cache=cache)
    # Preserve the direct raw bytes of failed, reworked and accepted observations.
    # Do not reassess historical product sources or recursively follow raw data.
    for ref in refs:
        for raw in cache.raw_references.get(ref["path"], []):
            _ref(repo, raw, cache=cache)
    return refs


def verify_evidence(repo, document, *, cache=None):
    # Retain only active quality/review JSON. Historical references and product
    # files retain hashes/stamps, not their content bytes.
    if cache is None:
        cache = _verification_cache(document)
    else:
        discovered = _verification_cache(document)
        cache.retained_paths.update(discovered.retained_paths)
        cache.measurement_paths.update(discovered.measurement_paths)
        cache.measurement_references.update(discovered.measurement_references)
    # Discover all active consumers before history can read the same raw file.
    # This retains only active raw payloads, with hashes/stamps for all history.
    for path in sorted(cache.measurement_paths & cache.retained_paths):
        if path in cache.measurement_references:
            _ref(repo, cache.measurement_references[path], cache=cache)
    for delivery in document["deliveries"]:
        if delivery["status"] == "cancelled":
            continue
        _refs(repo, delivery["planEvidence"], cache=cache)
        owner = delivery.get("deliveryPolicy", {}).get("owner", {})
        if owner.get("kind") == "agent":
            _ref(repo, owner["mandate"], cache=cache)
        # Accepted bindings record the inspected historical product snapshot.
        # Later deliveries may legitimately change those same product files.
        if delivery["status"] != "accepted" and "productBindings" in delivery:
            _refs(repo, delivery["productBindings"], product=True, cache=cache)
        for key in ("approval", "acceptance"):
            if key in delivery:
                _ref(repo, {field: delivery[key][field] for field in ("path", "sha256")}, cache=cache)
                if delivery[key]["kind"] == "agent":
                    _owner_decision_evidence(repo, delivery[key], delivery,
                                             "approve" if key == "approval" else "accept", cache=cache)
        for key in ("reviewEvidence", "validationEvidence"):
            if key in delivery:
                _refs(repo, delivery[key], cache=cache)
        if delivery.get("qualityMeasurements"):
            _quality_refs(repo, delivery["qualityMeasurements"], cache=cache)
        if "coreVerification" in delivery:
            _quality_refs(repo, delivery["coreVerification"]["qualityMeasurements"], cache=cache)
        for previous in delivery.get("coreVerificationHistory", []):
            _quality_refs(repo, previous["qualityMeasurements"], cache=cache)
        for previous in delivery.get("reworkHistory", []):
            if previous.get("qualityMeasurements"):
                _quality_refs(repo, previous["qualityMeasurements"], cache=cache)
        for item in delivery.get("criterionEvidence", []):
            _refs(repo, item["evidence"], cache=cache)
        effective = delivery.get("blockedFrom", delivery["status"])
        if effective in {"validation", "acceptance"}:
            _require_review(repo, delivery, cache=cache)
        if effective == "acceptance" and (delivery.get("qualityGoals") or delivery.get("qualityPlan")):
            _require_quality(repo, delivery, cache=cache)
    for epic in document["epics"]:
        if "closure" in epic:
            record = epic["closure"]
            _ref(repo, {field: record["authority"][field] for field in ("path", "sha256")}, cache=cache)
            for item in record["criteria"]:
                _refs(repo, item["evidence"], cache=cache)

    _finish_verification(repo, cache)


def _require_activity_completion(repo, delivery, *, cache=None):
    if "executionPlan" not in delivery:
        return
    graph = project_graph(repo, {"deliveries": [delivery]}, None,
                          check_reference=lambda ref: _ref(repo, ref, product=True, cache=cache))
    require(all(a["status"] == "completed" for a in graph["activities"]),
            "Delivery has unresolved or stale execution activities; finish or rework before review.")


def _require_review(repo, delivery, *, cache):
    """Consume the existing review record at the native validation boundary."""
    _require_activity_completion(repo, delivery, cache=cache)
    policy = delivery.get("qualityPlan", {}).get("reviewPolicy")
    if policy is None:
        return  # Preserve historical approved scope; do not assert current coverage.
    reference = delivery["reviewEvidence"][0]
    _ref(repo, reference, cache=cache)
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, "Review evidence has duplicate JSON keys.")
            result[name] = value
        return result
    def reviewed_reference(root, ref):
        try:
            _ref(root, ref, product=True, cache=cache)
        except (OSError, ValueError):
            return None, False
        return None, True
    try:
        record = json.loads(cache.payloads[reference["path"]], object_pairs_hook=pairs)
        require(isinstance(record, dict) and record.get("scopeSha256") == delivery["scopeSha256"],
                "Review evidence must bind the approved scopeSha256.")
        assessment = check_review(repo, record, [r["path"] for r in delivery["productBindings"]],
                                  require_independent=policy["mode"] == "independent",
                                  allowed_exceptions=("trivial",) if policy["mode"] == "self" else (),
                                  read_reference=reviewed_reference)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise StoryError(f"Invalid structured review evidence: {exc}") from exc
    require(assessment["eligible"], "Review requirements not met: " + "; ".join(assessment["diagnostics"]))



def review_record(repo, request, expected_sha256=None):
    """Format supplied reviewer observations against a confirmed review snapshot.

    Read-only: bindings are copied, never refreshed. Identity and semantic review
    remain the reviewer's declarations; this helper neither performs nor accepts
    the review. Open material findings can be recorded, but still block validate.
    """
    fields(request, ("deliveryId", "reviewer", "reviewMode", "findings"),
           ("implementer", "implementers", "exception", "notes", "observations"))
    _one_input(request, "implementer", "implementers")
    _sha(expected_sha256, "Confirmed review receipt")
    identity(request["deliveryId"], "DI")
    if "notes" in request:
        text(request["notes"], "Review notes", 4096)
    if "observations" in request:
        observations = request["observations"]
        require(isinstance(observations, list) and len(observations) <= 32,
                "Review observations must contain at most 32 entries.")
        for observation in observations:
            text(observation, "Review observation", 4096)
    repo = Path(repo).resolve()
    before = _evidence_stamp(repo, FILE)
    document, current_hash = load(repo, check_evidence=False)
    require(current_hash == expected_sha256, "Stale review receipt; use the confirmed current review digest.")
    delivery = _by_id(document, "deliveries", request["deliveryId"])
    require(delivery["status"] == "review", "Review record requires a delivery in review.")
    record = {"version": 1, "scopeSha256": delivery["scopeSha256"],
              "sources": copy.deepcopy(delivery["productBindings"]),
              "implementers": copy.deepcopy([request["implementer"]] if "implementer" in request
                                            else request["implementers"]),
              **{key: copy.deepcopy(request[key]) for key in ("reviewer", "reviewMode", "findings")}}
    for key in ("exception", "notes", "observations"):
        if key in request:
            record[key] = copy.deepcopy(request[key])
    require(len((json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()) <= MAX_BYTES,
            "Review record exceeds the bounded evidence size.")
    cache = _EvidenceCache(())
    def reviewed_reference(root, reference):
        _ref(root, reference, product=True, cache=cache)
        return None, True
    policy = delivery.get("qualityPlan", {}).get("reviewPolicy", {"mode": "independent"})
    try:
        assessment = check_review(repo, record, [ref["path"] for ref in delivery["productBindings"]],
                                  require_independent=policy["mode"] == "independent",
                                  allowed_exceptions=("trivial",) if policy["mode"] == "self" else (),
                                  read_reference=reviewed_reference)
    except ValueError as exc:
        raise StoryError(f"Invalid structured review input: {exc}") from exc
    # A report must preserve negative findings. Only that explicit diagnostic
    # may remain here; the native validate consumer still requires eligibility.
    recorded_findings = {f"Unresolved material finding: {identifier}"
                         for identifier in assessment["unresolvedMaterialFindings"]}
    failures = [message for message in assessment["diagnostics"] if message not in recorded_findings]
    require(not failures, "Review record requirements not met: " + "; ".join(failures))
    _finish_verification(repo, cache)
    require(before == _evidence_stamp(repo, FILE), "Review receipt changed during record creation.")
    return record

def _require_quality(repo, delivery, *, cache=None):
    results = _quality_assessment(repo, delivery, cache=cache)
    failures = [item for item in results if item["state"] != "passed"]
    require(not failures, "Quality requirements not met: " + "; ".join(
        f"{item.get('goalId', item.get('checkId'))} {item['state']}: {item['detail']}" for item in failures))
    return results


def _quality_assessment(repo, delivery, *, cache=None, core_only=False):
    measurement_paths = {ref["path"] for record in (delivery, delivery.get("coreVerification", {}))
                         for ref in record.get("qualityMeasurements", [])}
    if cache is None:
        cache = _EvidenceCache(measurement_paths, measurement_paths=measurement_paths)
    def verified_read(root, reference):
        try:
            _ref(root, reference, product=True, cache=cache)
        except StoryError:
            # Changed product sources are a stale result. Changed observation
            # bytes must never be interpreted as authentic measurement data.
            if reference["path"] in measurement_paths:
                raise
            if reference["path"] not in cache:
                raise
            return None, False
        return cache.payloads.get(reference["path"]), True
    options = {"read_reference": verified_read, "scope_sha256": delivery["scopeSha256"]}
    def read_raw(root, reference):
        cache.retained_paths.add(reference["path"])
        cache.raw_paths.add(reference["path"])
        _ref(root, reference, cache=cache)
        return cache.payloads[reference["path"]], True
    plan = delivery.get("qualityPlan")
    goals = delivery.get("qualityGoals", [])
    def assess(record):
        refs, bindings = record.get("qualityMeasurements", []), record.get("productBindings", [])
        numeric = assess_goals(repo, goals, refs, bindings, **options)
        try:
            checks = assess_checks(repo, plan, refs, bindings, raw_read_reference=read_raw, **options) if plan else []
        except ValueError as exc:
            raise StoryError(str(exc)) from exc
        return numeric + checks
    if not plan:
        return assess(delivery)
    early = assess(delivery.get("coreVerification", {}))
    core_checks = {c["id"] for c in plan["checks"] if "core" in stages(c)}
    core_goals = {g for c in plan["checks"] if c["id"] in core_checks for g in c["goalIds"]}
    if core_only:
        return [r for r in early if r.get("checkId") in core_checks or r.get("goalId") in core_goals]
    current = assess(delivery)
    early_by_id = {r.get("goalId", r.get("checkId")): r for r in early}
    # Reuse current early observations only when their bound sources are included
    # in the final reviewed snapshot. New integration still needs its journey.
    bound = {r["path"]: r["sha256"] for r in delivery.get("productBindings", [])}
    early_bound = {r["path"]: r["sha256"]
                   for r in delivery.get("coreVerification", {}).get("productBindings", [])}
    reusable = bool(early_bound) and all(bound.get(p) == h for p, h in early_bound.items())
    checks_by_id = {c["id"]: c for c in plan["checks"]}
    for result in current:
        identifier = result.get("goalId", result.get("checkId"))
        eligible = identifier in core_goals or identifier in core_checks
        check = checks_by_id.get(identifier)
        if check and "delivery" in stages(check):
            eligible = eligible and bound == early_bound
        if result["state"] == "unmeasured" and reusable and eligible and identifier in early_by_id:
            result.update(early_by_id[identifier])
    # A later passing measurement cannot erase an unresolved failed early core.
    unresolved = [r for r in early if (r.get("checkId") in core_checks or r.get("goalId") in core_goals)
                  and r["state"] != "passed"]
    return current + [{**r, "detail": "Early core: " + r["detail"]} for r in unresolved]


def _require_core(repo, delivery, *, cache=None):
    if "qualityPlan" not in delivery:
        return
    results = _quality_assessment(repo, delivery, core_only=True, cache=cache)
    failures = [r for r in results if r["state"] != "passed"]
    require(not failures, "Early core verification not met; measure, correct or block for a decision: " +
            "; ".join(f"{r.get('goalId', r.get('checkId'))} {r['state']}" for r in failures))


def quality_result(repo, document, *, cache=None):
    if cache is None:
        cache = _verification_cache(document)
    records = []
    for delivery in document["deliveries"]:
        if delivery["status"] in {"accepted", "cancelled"}:
            continue
        early = delivery.get("blockedFrom", delivery["status"]) == "in_progress"
        results = _quality_assessment(repo, delivery, core_only=early, cache=cache)
        plan = delivery.get("qualityPlan", {})
        coverage = ("current_contract" if {"caseCoverage", "reviewPolicy"} <= plan.keys()
                    else "legacy_review_structure_not_assessed" if "caseCoverage" in plan
                    else "legacy_case_coverage_not_assessed" if "primaryResult" in delivery.get("qualityPlan", {})
                    else "legacy_primary_result_not_assessed" if "qualityPlan" in delivery
                    else "legacy_not_assessed")
        records.append({"deliveryId": delivery["id"],
                        "planCoverage": coverage,
                        "goals": [r for r in results if "goalId" in r],
                        "checks": [r for r in results if "checkId" in r],
                        "nextAction": "correct_or_decide" if any(r["state"] != "passed" for r in results)
                                      else "review" if early else "continue_validation"})
    _finish_verification(repo, cache)
    return {"deliveries": records}


def load(repo, *, check_evidence=True, cache=None):
    repo = Path(repo).resolve()
    require(not (repo / ".aim").is_symlink(), ".aim must not be a symbolic link.")
    path = repo / FILE
    require(not path.is_symlink(), "Product backlog must not be a symbolic link.")
    if not path.exists():
        return _empty(), None
    try:
        payload = read_evidence(repo, FILE, MAX_BYTES)
        document = json.loads(payload)
    except (OSError, ValueError, UnicodeError) as exc:
        raise StoryError(f"Cannot read product backlog: {exc}") from exc
    validate_document(document)
    if check_evidence:
        verify_evidence(repo, document, cache=cache)
    return document, hashlib.sha256(payload).hexdigest()


def _import(document, request):
    fields(request, (), ("intents", "epics", "stories"))
    require(bool(request), "Import must contain requirements.")
    definitions = {
        "intents": (("id", "statement"), ()),
        "epics": (("id", "intentId", "title", "outcome", "acceptanceCriteria"), ("outcomeClass", "nonGoals")),
        "stories": (("id", "epicId", "title", "persona", "need", "benefit", "acceptanceCriteria", "priority", "status"), ()),
    }
    for collection in definitions:
        incoming = request.get(collection, [])
        require(isinstance(incoming, list) and len(incoming) <= MAX_ITEMS, "Import exceeds collection limit.")
        seen = []
        for raw in incoming:
            fields(raw, *definitions[collection])
            seen.append(raw["id"])
            current = next((item for item in document[collection] if item["id"] == raw["id"]), None)
            if collection == "epics":
                raw = {**raw,
                       "outcomeClass": raw.get("outcomeClass", current["outcomeClass"] if current else "Product"),
                       "nonGoals": raw.get("nonGoals", copy.deepcopy(current["nonGoals"]) if current else [])}
            if current and all(current.get(key) == value for key, value in raw.items()):
                continue
            if collection == "stories":
                require(raw["status"] in {"draft", "ready"}, "Import cannot set runtime or accepted Story status.")
                require(not current or current["status"] in {"draft", "ready"}, "Active or accepted Stories cannot be rewritten.")
            if collection == "intents":
                require(not any(delivery["status"] not in {"cancelled", "accepted"} and any(epic["intentId"] == raw["id"] for epic in delivery["epics"])
                                for delivery in document["deliveries"]), "An Intent with selected delivery scope is frozen.")
            if collection in {"stories", "epics"}:
                snapshot_key = collection
                require(not any(delivery["status"] not in {"cancelled", "accepted"} and any(item["id"] == raw["id"] for item in delivery[snapshot_key])
                                for delivery in document["deliveries"]), "Selected requirements are frozen; cancel the unapproved plan before refinement.")
                require(not current or current.get("status") != "closed", "Closed Epics cannot be rewritten.")
            item = copy.deepcopy(raw)
            item["revision"] = current["revision"] + 1 if current else 1
            if collection in {"epics", "stories"}:
                item["originalAcceptanceCriteria"] = copy.deepcopy(current["originalAcceptanceCriteria"] if current else raw["acceptanceCriteria"])
            if collection == "epics":
                item["status"] = "open"
            if current:
                document[collection][document[collection].index(current)] = item
            else:
                document[collection].append(item)
        unique(seen, "import identities")


def _closure_scope(document, epic, evidence):
    stories = [story for story in document["stories"] if story["epicId"] == epic["id"]]
    delivered = []
    for story in stories:
        matches = [delivery for delivery in document["deliveries"] if delivery["status"] == "accepted"
                   and any(item["id"] == story["id"] for item in delivery["stories"])]
        require(story["status"] == "done" and len(matches) == 1, "Every Epic Story must be accepted before closure.")
        delivered.append({"story": _story_snapshot(story), "acceptanceSha256": matches[0]["acceptanceSha256"],
                          "authority": matches[0]["acceptance"]})
    require(bool(stories), "An Epic without accepted Stories cannot close.")
    return {"epic": _epic_snapshot(epic), "delivered": delivered, "criteria": evidence}


def closure_preview(repo, request):
    fields(request, ("epicId",), ("criteria", "criteriaFrom"))
    cache = _verification_cache({}, request)
    document, store_hash = load(repo, cache=cache)
    epic = _by_id(document, "epics", request["epicId"])
    evidence = _coverage_evidence(repo, request, [ac["id"] for ac in epic["acceptanceCriteria"]], stories=False, epic_id=epic["id"], cache=cache)
    _finish_verification(repo, cache)
    return {"storeSha256": store_hash, "scopeSha256": digest(_closure_scope(document, epic, evidence))}


def _change(repo, document, command, request, *, cache=None):
    if command in {"import", "refine"}:
        _import(document, request)
        return
    if command == "plan":
        fields(request, ("id", "title", "goal", "storyIds", "planEvidence", "qualityPlan"), ("qualityGoals", "executionPlan", "deliveryPolicy"))
        try:
            policy = normalize_policy(request.get("deliveryPolicy", DEFAULT_POLICY))
        except ValueError as exc:
            raise StoryError(str(exc)) from exc
        if policy["owner"]["kind"] == "agent":
            _ref(repo, policy["owner"]["mandate"], cache=cache)
        validate_goals(request.get("qualityGoals", []))
        identity(request["id"], "DI")
        require(not any(item["id"] == request["id"] for item in document["deliveries"]), "Delivery identity is already allocated.")
        require(isinstance(request["storyIds"], list) and 1 <= len(request["storyIds"]) <= MAX_ITEMS, "Select 1–256 Stories.")
        unique(request["storyIds"], "selected Stories")
        selected = [_by_id(document, "stories", item) for item in request["storyIds"]]
        require(all(item["status"] == "ready" for item in selected), "Only refined ready Stories can be selected.")
        validate_quality_plan(request["qualityPlan"], request.get("qualityGoals", []), selected,
                              require_current_contract=True)
        selected_epics = [_by_id(document, "epics", identifier) for identifier in dict.fromkeys(item["epicId"] for item in selected)]
        selected_intents = [_by_id(document, "intents", identifier) for identifier in dict.fromkeys(item["intentId"] for item in selected_epics)]
        require(all(item["status"] == "open" for item in selected_epics), "Selected Epics must be open.")
        delivery = {"id": request["id"], "title": text(request["title"], "Delivery title", 240),
                    "goal": text(request["goal"], "Delivery goal"), "status": "planned", "createdAt": now(),
                    "planEvidence": _refs(repo, request["planEvidence"], cache=cache),
                    "stories": [_story_snapshot(item) for item in selected],
                    "intents": [_intent_snapshot(item) for item in selected_intents],
                    "epics": [_epic_snapshot(item) for item in selected_epics]}
        delivery["qualityPlan"] = copy.deepcopy(request["qualityPlan"])
        delivery["deliveryPolicy"] = policy
        if "qualityGoals" in request:
            delivery["qualityGoals"] = copy.deepcopy(request["qualityGoals"])
        if "executionPlan" in request:
            try:
                validate_execution_plan(request["executionPlan"], delivery["stories"], repo)
            except ValueError as exc:
                raise StoryError(str(exc)) from exc
            delivery["executionPlan"] = copy.deepcopy(request["executionPlan"])
        delivery["scopeSha256"] = digest(_scope(delivery))
        document["deliveries"].append(delivery)
        return
    if command == "close-epic":
        fields(request, ("epicId", "authority"), ("criteria", "criteriaFrom"))
        epic = _by_id(document, "epics", request["epicId"])
        require(epic["status"] == "open", "Epic is already closed.")
        evidence = _coverage_evidence(repo, request, [ac["id"] for ac in epic["acceptanceCriteria"]], stories=False, epic_id=epic["id"], cache=cache)
        authority = _authority(repo, request["authority"], digest(_closure_scope(document, epic, evidence)), cache=cache)
        epic.update(status="closed", closure={"criteria": evidence, "authority": authority, "closedAt": now()})
        return
    if command == "activity":
        require(isinstance(request, dict) and "deliveryId" in request, "Activity request requires a delivery ID.")
        delivery = _by_id(document, "deliveries", request["deliveryId"])
        try:
            change_activity(repo, delivery, request,
                            bind_sources=lambda paths: _source_bindings(repo, paths, cache=cache),
                            bind_evidence=lambda refs: _refs(repo, refs, cache=cache), at=now(),
                            check_reference=lambda ref: _ref(repo, ref, product=True, cache=cache))
        except ValueError as exc:
            raise StoryError(str(exc)) from exc
        return
    required = {"approve": ("authority",), "review": (), "validate": ("evidence",),
                "acceptance": ("evidence",), "accept": ("authority",), "measure": ("qualityMeasurements",),
                "rework": ("reason",), "cancel": ("reason",), "block": ("reason",), "unblock": ("reason",)}
    require(command in required, "Unknown Story command.")
    optional = {"review": ("bindings", "sourcePaths"),
                "measure": ("bindings", "sourcePaths", "response"),
                "acceptance": ("qualityMeasurements", "criteria", "criteriaFrom")}
    fields(request, ("deliveryId", *required[command]), optional.get(command, ()))
    delivery = _by_id(document, "deliveries", request["deliveryId"])
    status = delivery["status"]
    if command == "approve":
        require(status == "planned", "Gate A/B approval requires a planned delivery.")
        delivery["approval"] = _authority(repo, request["authority"], delivery["scopeSha256"], cache=cache,
                                          delivery=delivery, operation="approve")
        delivery["status"] = "in_progress"
    elif command == "review":
        require(status == "in_progress", "Review requires implementation in progress.")
        _require_activity_completion(repo, delivery, cache=cache)
        _require_core(repo, delivery, cache=cache)
        _one_input(request, "bindings", "sourcePaths")
        delivery["productBindings"] = (_source_bindings(repo, request["sourcePaths"], cache=cache) if "sourcePaths" in request
                                       else _refs(repo, request["bindings"], product=True, cache=cache))
        delivery["status"] = "review"
    elif command == "validate":
        require(status == "review", "Validation requires Reviewer completion.")
        if "qualityPlan" in delivery:
            failures = [r for r in _quality_assessment(repo, delivery, cache=cache)
                        if r["state"] in {"failed", "stale", "mismatch"}]
            require(not failures, "Recorded quality failure requires rework or a blocked decision before validation.")
        delivery["reviewEvidence"] = _refs(repo, request["evidence"], cache=cache)
        delivery["status"] = "validation"
    elif command == "measure":
        require(status in {"in_progress", "review", "validation"}, "Record measurements during core implementation or review/validation.")
        refs = _refs(repo, request["qualityMeasurements"], cache=cache)
        if status == "in_progress":
            require("qualityPlan" in delivery, "Early measurement requires a planned quality contract.")
            _one_input(request, "bindings", "sourcePaths")
            bindings = (_source_bindings(repo, request["sourcePaths"], cache=cache) if "sourcePaths" in request
                        else _refs(repo, request["bindings"], product=True, cache=cache))
            previous = delivery.get("coreVerification")
            if previous:
                text(request.get("response"), "Correction or owner-decision response")
                delivery.setdefault("coreVerificationHistory", []).append(previous)
            record = {"productBindings": bindings, "qualityMeasurements": refs, "at": now()}
            if "response" in request:
                record["response"] = text(request["response"], "Correction or owner-decision response")
            delivery["coreVerification"] = record
            _quality_assessment(repo, delivery, core_only=True, cache=cache)  # Keep failures as observations.
        else:
            require(not any(k in request for k in ("bindings", "sourcePaths", "response")),
                    "Review measurements use the reviewed snapshot; rework before corrections.")
            require("qualityMeasurements" not in delivery or delivery["qualityMeasurements"] == refs,
                    "Rework before replacing recorded measurements; retain earlier results in history.")
            delivery["qualityMeasurements"] = refs
            _quality_assessment(repo, delivery, cache=cache)
    elif command == "acceptance":
        require(status == "validation", "PO acceptance requires TDO validation.")
        delivery["validationEvidence"] = _refs(repo, request["evidence"], cache=cache)
        expected = [(story["id"], ac["id"]) for story in delivery["stories"] for ac in story["acceptanceCriteria"]]
        delivery["criterionEvidence"] = _coverage_evidence(
            repo, request, expected, stories=True, cache=cache,
            scope_sha256=delivery["scopeSha256"], binding_sha256=digest(delivery["productBindings"]))
        if "qualityMeasurements" in request:
            refs = _refs(repo, request["qualityMeasurements"], cache=cache)
            require("qualityMeasurements" not in delivery or delivery["qualityMeasurements"] == refs,
                    "Rework before replacing recorded measurements; retain earlier results in history.")
            delivery["qualityMeasurements"] = refs
        _require_quality(repo, delivery, cache=cache)
        delivery["acceptanceSha256"] = digest(_acceptance_scope(delivery))
        delivery["status"] = "acceptance"
    elif command == "accept":
        require(status == "acceptance", "Gate E acceptance requires reviewed, validated delivery evidence.")
        delivery["acceptance"] = _authority(repo, request["authority"], delivery["acceptanceSha256"], cache=cache,
                                           delivery=delivery, operation="accept")
        delivery.update(status="accepted", acceptedAt=now())
    elif command == "cancel":
        require(status == "planned", "Only an unapproved plan can be cancelled.")
        delivery.update(status="cancelled", reason=text(request["reason"], "Cancellation reason"))
    elif command == "rework":
        prior_phase = delivery.get("blockedFrom") if status == "blocked" else status
        require(prior_phase in {"review", "validation", "acceptance"}, "Rework requires an unaccepted review/validation/acceptance phase.")
        record = {"reason": text(request["reason"], "Rework reason"), "from": prior_phase, "at": now()}
        if status == "blocked":
            record["blockedReason"] = delivery.pop("reason")
            delivery.pop("blockedFrom")
        for key in ("productBindings", "reviewEvidence", "validationEvidence", "criterionEvidence", "qualityMeasurements", "acceptanceSha256"):
            if key in delivery:
                record[key] = delivery.pop(key)
        delivery.setdefault("reworkHistory", []).append(record)
        delivery["status"] = "in_progress"
    elif command == "block":
        require(status in {"in_progress", "review", "validation", "acceptance"}, "Only active delivery work can be blocked.")
        delivery.update(status="blocked", blockedFrom=status, reason=text(request["reason"], "Block reason"))
    elif command == "unblock":
        require(status == "blocked", "Delivery is not blocked.")
        delivery["status"] = delivery.pop("blockedFrom")
        delivery["reason"] = text(request["reason"], "Resolution reason")
    effective = delivery.get("blockedFrom", delivery["status"])
    if effective not in {"planned", "cancelled"}:
        for snapshot in delivery["stories"]:
            _by_id(document, "stories", snapshot["id"])["status"] = "done" if effective == "accepted" else effective


def execute(repo, command, request, expected_sha256=None):
    """Apply one CAS mutation under a process lock, atomically replacing one file."""
    repo = Path(repo).resolve()
    require(repo.is_dir(), "Repository directory does not exist.")
    aim = repo / ".aim"
    require(not aim.is_symlink(), ".aim must not be a symbolic link.")
    aim.mkdir(exist_ok=True)
    path = repo / FILE
    with runtime_lock(path):
        document, current_hash = load(repo, check_evidence=False)
        require(current_hash == expected_sha256, "Stale product backlog digest; reload before changing requirements.")
        cache = _verification_cache(document, request, command=command)
        if command == "accept":
            verify_evidence(repo, document, cache=cache)
        # A rejected delivery must be recoverable even if its discarded review
        # artifact changed. Rework removes those bindings, then validates all
        # remaining authority and evidence before committing.
        candidate = copy.deepcopy(document)
        _change(repo, candidate, command, request, cache=cache)
        candidate["revision"] += 1
        candidate["updatedAt"] = now()
        validate_document(candidate)
        verify_evidence(repo, candidate, cache=cache)
        # Derive the response before commit. A later evidence read failure must
        # never make a confirmed write look like a rejected operation.
        quality = quality_result(repo, candidate, cache=cache) if command == "measure" else None
        payload = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode()
        require(len(payload) <= MAX_BYTES, "Product backlog exceeds the bounded store size.")
        result = status_result(candidate, hashlib.sha256(payload).hexdigest(), quality=quality)
        if command == "activity":
            result["executionGraph"] = project_graph(repo, candidate, result["storeSha256"], request["deliveryId"],
                                                     check_reference=lambda ref: _ref(repo, ref, product=True, cache=cache))
        _finish_verification(repo, cache)
        descriptor, temporary = tempfile.mkstemp(prefix=".product-backlog-", dir=aim)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    # Return the confirmed committed snapshot. A failed follow-up read must not
    # turn a successful write into an ambiguous retry of the same operation.
    return result


def status_result(document, store_hash, *, quality=None):
    next_steps = []
    operations = {"planned": "approve", "in_progress": "review", "review": "validate",
                  "validation": "acceptance", "acceptance": "accept", "blocked": "unblock"}
    assessed = {d["deliveryId"]: d for d in quality["deliveries"]} if quality else {}
    roles = {"approve": "tdo", "measure": "dev", "quality": "dev", "correct_or_decide": "dev",
             "review": "reviewer", "validate": "tdo", "acceptance": "tdo", "accept": "po", "unblock": "tdo",
             "rework_or_decide": "tdo"}
    for delivery in document["deliveries"]:
        if delivery["status"] in operations:
            operation = operations[delivery["status"]]
            assessment = assessed.get(delivery["id"])
            if delivery["status"] == "in_progress" and "qualityPlan" in delivery:
                operation = assessment["nextAction"] if assessment else "quality" if "coreVerification" in delivery else "measure"
            elif delivery["status"] in {"review", "validation"} and assessment and assessment["nextAction"] == "correct_or_decide":
                failed = any(r["state"] in {"failed", "stale", "mismatch"}
                             for r in assessment["goals"] + assessment["checks"])
                # First observations can still be supplied on this snapshot.
                # Replacing a recorded report requires supported rework.
                operation = "rework_or_decide" if failed or "qualityMeasurements" in delivery else "measure"
            role = roles[operation]
            if operation == "measure" and delivery["status"] != "in_progress":
                role = "tdo"
            relative = f"references/role-skill-{role}.md"
            if not (BUNDLE_ROOT / relative).is_file():
                relative = f"docs/workflow/role-skill-{role}.md"
            next_steps.append({"deliveryId": delivery["id"], "operation": operation, "role": role,
                               "instructions": str(BUNDLE_ROOT / relative)})
    if not next_steps:
        next_steps.append({"operation": "plan" if any(item["status"] == "ready" for item in document["stories"]) else "refine"})
    return {"storeSha256": store_hash, "document": document, "nextStep": next_steps,
            **({"quality": quality} if quality is not None else {})}


def compact_result(result, *, receipt=False, delivery_id=None):
    """Derive an active view from a confirmed snapshot, without another read.

    This view is not a replacement ledger and never supplies mutation authority.
    When no delivery is active, show at most twenty next ready/draft Stories.
    """
    if "document" not in result:
        return result
    document = result["document"]
    if receipt:
        # The caller already has its request and the prior confirmed context.
        # Return new state/identities, not another copy of requirements or plans.
        selected = [d for d in document["deliveries"] if d["id"] == delivery_id] if delivery_id else [
            d for d in document["deliveries"] if d["status"] not in {"accepted", "cancelled"}]
        deliveries = []
        for delivery in selected:
            entry = {k: delivery[k] for k in ("id", "status", "scopeSha256", "acceptanceSha256", "deliveryPolicy") if k in delivery}
            if "productBindings" in delivery:
                entry["productBindingsSha256"] = digest(delivery["productBindings"])
            if "coreVerification" in delivery:
                entry["coreBindingsSha256"] = digest(delivery["coreVerification"]["productBindings"])
            deliveries.append(entry)
        confirmed = {k: document[k] for k in ("productBacklogVersion", "revision", "updatedAt")}
        confirmed["deliveries"] = deliveries
        return {"view": "receipt", "storeSha256": result["storeSha256"], "document": confirmed,
                "nextStep": result["nextStep"], **({"quality": result["quality"]} if "quality" in result else {}),
                **({"executionGraph": result["executionGraph"]} if "executionGraph" in result else {})}
    active = [d for d in document["deliveries"] if d["status"] not in {"accepted", "cancelled"}]
    selected = {s["id"] for d in active for s in d["stories"]}
    visible = ([s for s in document["stories"] if s["id"] in selected] if active else
               sorted((s for s in document["stories"] if s["status"] in {"draft", "ready"}),
                      key=lambda s: (s["priority"], s["id"]))[:20])
    epic_ids = {s["epicId"] for s in visible}
    epics = [e for e in document["epics"] if e["id"] in epic_ids]
    intent_ids = {e["intentId"] for e in epics}
    compact = {key: document[key] for key in ("productBacklogVersion", "revision", "updatedAt")}
    compact.update(intents=[i for i in document["intents"] if i["id"] in intent_ids],
                   epics=epics, stories=visible,
                   deliveries=[{**{k: v for k, v in d.items()
                                    if k not in {"stories", "epics", "intents", "reworkHistory", "criterionEvidence"}},
                                "storyIds": [s["id"] for s in d["stories"]]} for d in active])
    return {**({"quality": result["quality"]} if "quality" in result else {}),
            "view": "active", "storeSha256": result["storeSha256"], "document": compact,
            "totals": {key: len(document[key]) for key in ("intents", "epics", "stories", "deliveries")},
            "nextStep": result["nextStep"]}


def project_story_board(repo):
    result = {"version": 1, "configured": (Path(repo) / FILE).exists(), "valid": True,
              "columns": [{"id": key, "label": label} for key, label in COLUMNS],
              "intents": [], "epics": [], "stories": [], "deliveries": [], "issues": []}
    try:
        cache = _EvidenceCache([])
        document, store_hash = load(repo, cache=cache)
        graph = project_graph(repo, document, store_hash,
                              check_reference=lambda ref: _ref(repo, ref, product=True, cache=cache))
        _finish_verification(repo, cache)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(valid=False, issues=[str(exc)])
        # A stale native review binding blocks gates but should still expose the
        # dependency that needs correction. Structural corruption stays closed.
        try:
            document, store_hash = load(repo, check_evidence=False)
            result["executionGraph"] = project_graph(repo, document, store_hash)
            result["executionGraph"].update(readyIds=[], retryIds=[], recommendedIds=[], nativeEvidenceValid=False)
            for activity in result["executionGraph"]["activities"]:
                if activity["status"] == "ready":
                    activity.update(status="blocked", reason="Native delivery evidence could not be verified.")
            result["executionGraph"]["summary"] = {
                state: sum(a["status"] == state for a in result["executionGraph"]["activities"])
                for state in result["executionGraph"]["summary"]}
            result["executionGraph"]["blockers"].append({"status": "blocked", "reason": str(exc)})
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return result
    result.update(intents=document["intents"], epics=document["epics"], deliveries=document["deliveries"], storeSha256=store_hash)
    result["executionGraph"] = graph
    for story in sorted(document["stories"], key=lambda item: (item["priority"], item["id"])):
        related = [delivery for delivery in document["deliveries"] if delivery["status"] != "cancelled"
                   and any(item["id"] == story["id"] for item in delivery["stories"])]
        evidence = []
        for delivery in related:
            for record in delivery.get("criterionEvidence", []):
                if record["storyId"] == story["id"]:
                    evidence.extend({"label": record["criterionId"], "path": ref["path"],
                                     "url": "/api/evidence?path=" + quote(ref["path"], safe="")}
                                    for ref in record["evidence"])
        result["stories"].append({**story, "column": "backlog" if story["status"] == "draft" else story["status"],
                                  "deliveryIds": [item["id"] for item in related], "evidence": evidence,
                                  "attention": next((item["reason"] for item in related if item["status"] == "blocked"), None)})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("command", choices=(*COMMANDS, "status", "quality", "graph", "closure-preview", "review-record"))
    parser.add_argument("--input", default="-", help="JSON file, or - for stdin")
    parser.add_argument("--expected-sha256", help="Digest returned by the last successful read or write")
    parser.add_argument("--compact", action="store_true", help="Current context for status; confirmed receipt for mutations; full history stays in the ledger")
    args = parser.parse_args(argv)
    try:
        if args.command == "quality":
            document, _ = load(args.repo, check_evidence=False)
            result = quality_result(args.repo, document)
        elif args.command == "status":
            document, store_hash = load(args.repo)
            result = status_result(document, store_hash)
        elif args.command == "graph":
            board = project_story_board(args.repo)
            require("executionGraph" in board, "; ".join(board["issues"]) or "Execution graph unavailable.")
            result = board["executionGraph"]
        else:
            raw = sys.stdin.buffer.read(MAX_BYTES + 1) if args.input == "-" else Path(args.input).read_bytes()
            require(len(raw) <= MAX_BYTES, "Request exceeds input size limit.")
            def pairs(items):
                result = {}
                for key, value in items:
                    require(key not in result, "Review input has duplicate JSON keys.")
                    result[key] = value
                return result
            request = json.loads(raw, object_pairs_hook=pairs) if args.command == "review-record" else json.loads(raw)
            if args.command == "review-record":
                result = review_record(args.repo, request, args.expected_sha256)
            elif args.command == "closure-preview":
                result = closure_preview(args.repo, request)
            else:
                result = execute(args.repo, args.command, request, args.expected_sha256)
        if args.compact:
            result = compact_result(result, receipt=args.command in COMMANDS,
                                    delivery_id=request.get("deliveryId", request.get("id")) if args.command in COMMANDS else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        print(json.dumps({"error": str(exc), "committed": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
