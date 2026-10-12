#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_stories.py
"""PO-owned requirements and independent, cross-Epic delivery execution.

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
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from aim_quality.files import read_evidence
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
            "accept", "rework", "cancel", "block", "unblock", "close-epic")


class StoryError(ValueError):
    """A requirements or delivery operation could not be applied safely."""


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
    return {key: delivery[key] for key in ("id", "title", "goal", "stories", "epics", "intents", "planEvidence")}


def _acceptance_scope(delivery):
    return {key: delivery[key] for key in
            ("scopeSha256", "approval", "productBindings", "reviewEvidence", "validationEvidence", "criterionEvidence")}


def _by_id(document, collection, identifier):
    matches = [item for item in document[collection] if item["id"] == identifier]
    require(len(matches) == 1, f"Unknown {collection} identity: {identifier}.")
    return matches[0]


def _ref(repo, reference, *, product=False):
    fields(reference, ("path", "sha256"))
    path = text(reference["path"], "Evidence path", 1000)
    require(Path(path).as_posix() == path, "Evidence paths must use canonical relative spelling.")
    require((product or path.startswith(".aim/")) and path != FILE and "\\" not in path,
            "Evidence must be an independent artifact inside .aim.")
    require(isinstance(reference["sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]) is not None,
            "Evidence requires a SHA-256 fingerprint.")
    try:
        ledger = Path(repo) / FILE
        require(not ledger.exists() or not ledger.samefile(Path(repo) / path),
                "Evidence must be independent of the product backlog file identity.")
        payload = read_evidence(repo, path, MAX_BYTES)
    except (OSError, ValueError) as exc:
        raise StoryError(f"Cannot safely read evidence {path}: {exc}") from exc
    require(hashlib.sha256(payload).hexdigest() == reference["sha256"],
            f"Evidence changed: {path}.")
    return copy.deepcopy(reference)


def _refs(repo, values, *, product=False):
    require(isinstance(values, list) and 1 <= len(values) <= 64, "Supply 1–64 evidence references.")
    result = [_ref(repo, value, product=product) for value in values]
    unique([item["path"] for item in result], "evidence paths")
    return result


def _authority(repo, value, scope):
    fields(value, ("kind", "path", "sha256", "scopeSha256"))
    require(value["kind"] == "user", "This decision requires supplied user authority; Auto is not final acceptance.")
    require(value["scopeSha256"] == scope, "Authority refers to a stale or different scope.")
    _ref(repo, {key: value[key] for key in ("path", "sha256")})
    return copy.deepcopy(value)


def _criterion_evidence(repo, values, expected, *, stories):
    require(isinstance(values, list) and len(values) == len(expected),
            "Evidence must cover every selected acceptance criterion exactly once.")
    result = []
    actual = []
    for value in values:
        fields(value, ("storyId", "criterionId", "evidence") if stories else ("criterionId", "evidence"))
        key = (value["storyId"], value["criterionId"]) if stories else value["criterionId"]
        actual.append(key)
        result.append({**value, "evidence": _refs(repo, value["evidence"])})
    unique(actual, "criterion evidence")
    require(set(actual) == set(expected), "Criterion evidence does not match the approved requirements.")
    return result


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
            require(delivery.get("acceptanceSha256") == digest(_acceptance_scope(delivery)), "Acceptance scope mismatch.")
        if effective == "accepted":
            require(delivery.get("acceptance", {}).get("scopeSha256") == delivery["acceptanceSha256"],
                    "Delivery has no matching user acceptance.")
    for story in stories.values():
        if story["status"] not in {"draft", "ready"}:
            require(story["id"] in ownership, "Story lifecycle has no delivery evidence.")
    for epic in epics.values():
        if epic["status"] == "closed":
            members = [item for item in stories.values() if item["epicId"] == epic["id"]]
            require(bool(members) and all(item["id"] in accepted for item in members), "Closed Epic has unfinished Stories.")
            require("closure" in epic, "Epic closure requires explicit evidence and authority.")
            expected = {item["id"] for item in epic["acceptanceCriteria"]}
            actual = [item["criterionId"] for item in epic["closure"]["criteria"]]
            require(len(actual) == len(expected) and set(actual) == expected, "Incomplete Epic closure evidence.")
            require(epic["closure"]["authority"]["scopeSha256"] == digest(_closure_scope(document, epic, epic["closure"]["criteria"])),
                    "Epic closure scope mismatch.")


def verify_evidence(repo, document):
    for delivery in document["deliveries"]:
        if delivery["status"] == "cancelled":
            continue
        _refs(repo, delivery["planEvidence"])
        # Accepted bindings record the inspected historical product snapshot.
        # Later deliveries may legitimately change those same product files.
        if delivery["status"] != "accepted" and "productBindings" in delivery:
            _refs(repo, delivery["productBindings"], product=True)
        for key in ("approval", "acceptance"):
            if key in delivery:
                _ref(repo, {field: delivery[key][field] for field in ("path", "sha256")})
        for key in ("reviewEvidence", "validationEvidence"):
            if key in delivery:
                _refs(repo, delivery[key])
        for item in delivery.get("criterionEvidence", []):
            _refs(repo, item["evidence"])
    for epic in document["epics"]:
        if "closure" in epic:
            record = epic["closure"]
            _ref(repo, {field: record["authority"][field] for field in ("path", "sha256")})
            for item in record["criteria"]:
                _refs(repo, item["evidence"])


def load(repo, *, check_evidence=True):
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
        verify_evidence(repo, document)
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
    fields(request, ("epicId", "criteria"))
    document, store_hash = load(repo)
    epic = _by_id(document, "epics", request["epicId"])
    evidence = _criterion_evidence(repo, request["criteria"], [ac["id"] for ac in epic["acceptanceCriteria"]], stories=False)
    return {"storeSha256": store_hash, "scopeSha256": digest(_closure_scope(document, epic, evidence))}


def _change(repo, document, command, request):
    if command in {"import", "refine"}:
        _import(document, request)
        return
    if command == "plan":
        fields(request, ("id", "title", "goal", "storyIds", "planEvidence"))
        identity(request["id"], "DI")
        require(not any(item["id"] == request["id"] for item in document["deliveries"]), "Delivery identity is already allocated.")
        require(isinstance(request["storyIds"], list) and 1 <= len(request["storyIds"]) <= MAX_ITEMS, "Select 1–256 Stories.")
        unique(request["storyIds"], "selected Stories")
        selected = [_by_id(document, "stories", item) for item in request["storyIds"]]
        require(all(item["status"] == "ready" for item in selected), "Only refined ready Stories can be selected.")
        selected_epics = [_by_id(document, "epics", identifier) for identifier in dict.fromkeys(item["epicId"] for item in selected)]
        selected_intents = [_by_id(document, "intents", identifier) for identifier in dict.fromkeys(item["intentId"] for item in selected_epics)]
        require(all(item["status"] == "open" for item in selected_epics), "Selected Epics must be open.")
        delivery = {"id": request["id"], "title": text(request["title"], "Delivery title", 240),
                    "goal": text(request["goal"], "Delivery goal"), "status": "planned", "createdAt": now(),
                    "planEvidence": _refs(repo, request["planEvidence"]),
                    "stories": [_story_snapshot(item) for item in selected],
                    "intents": [_intent_snapshot(item) for item in selected_intents],
                    "epics": [_epic_snapshot(item) for item in selected_epics]}
        delivery["scopeSha256"] = digest(_scope(delivery))
        document["deliveries"].append(delivery)
        return
    if command == "close-epic":
        fields(request, ("epicId", "criteria", "authority"))
        epic = _by_id(document, "epics", request["epicId"])
        require(epic["status"] == "open", "Epic is already closed.")
        evidence = _criterion_evidence(repo, request["criteria"], [ac["id"] for ac in epic["acceptanceCriteria"]], stories=False)
        authority = _authority(repo, request["authority"], digest(_closure_scope(document, epic, evidence)))
        epic.update(status="closed", closure={"criteria": evidence, "authority": authority, "closedAt": now()})
        return
    required = {"approve": ("authority",), "review": ("bindings",), "validate": ("evidence",),
                "acceptance": ("evidence", "criteria"), "accept": ("authority",),
                "rework": ("reason",), "cancel": ("reason",), "block": ("reason",), "unblock": ("reason",)}
    require(command in required, "Unknown Story command.")
    fields(request, ("deliveryId", *required[command]))
    delivery = _by_id(document, "deliveries", request["deliveryId"])
    status = delivery["status"]
    if command == "approve":
        require(status == "planned", "Gate A/B approval requires a planned delivery.")
        delivery["approval"] = _authority(repo, request["authority"], delivery["scopeSha256"])
        delivery["status"] = "in_progress"
    elif command == "review":
        require(status == "in_progress", "Review requires implementation in progress.")
        delivery["productBindings"] = _refs(repo, request["bindings"], product=True)
        delivery["status"] = "review"
    elif command == "validate":
        require(status == "review", "Validation requires Reviewer completion.")
        delivery["reviewEvidence"] = _refs(repo, request["evidence"])
        delivery["status"] = "validation"
    elif command == "acceptance":
        require(status == "validation", "PO acceptance requires TDO validation.")
        delivery["validationEvidence"] = _refs(repo, request["evidence"])
        expected = [(story["id"], ac["id"]) for story in delivery["stories"] for ac in story["acceptanceCriteria"]]
        delivery["criterionEvidence"] = _criterion_evidence(repo, request["criteria"], expected, stories=True)
        delivery["acceptanceSha256"] = digest(_acceptance_scope(delivery))
        delivery["status"] = "acceptance"
    elif command == "accept":
        require(status == "acceptance", "Gate E acceptance requires reviewed, validated delivery evidence.")
        delivery["acceptance"] = _authority(repo, request["authority"], delivery["acceptanceSha256"])
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
        for key in ("productBindings", "reviewEvidence", "validationEvidence", "criterionEvidence", "acceptanceSha256"):
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
        if command == "accept":
            verify_evidence(repo, document)
        # A rejected delivery must be recoverable even if its discarded review
        # artifact changed. Rework removes those bindings, then validates all
        # remaining authority and evidence before committing.
        candidate = copy.deepcopy(document)
        _change(repo, candidate, command, request)
        candidate["revision"] += 1
        candidate["updatedAt"] = now()
        validate_document(candidate)
        verify_evidence(repo, candidate)
        payload = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode()
        require(len(payload) <= MAX_BYTES, "Product backlog exceeds the bounded store size.")
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
    return status_result(candidate, hashlib.sha256(payload).hexdigest())


def status_result(document, store_hash):
    next_steps = []
    operations = {"planned": "approve", "in_progress": "review", "review": "validate",
                  "validation": "acceptance", "acceptance": "accept", "blocked": "unblock"}
    for delivery in document["deliveries"]:
        if delivery["status"] in operations:
            next_steps.append({"deliveryId": delivery["id"], "operation": operations[delivery["status"]]})
    if not next_steps:
        next_steps.append({"operation": "plan" if any(item["status"] == "ready" for item in document["stories"]) else "refine"})
    return {"storeSha256": store_hash, "document": document, "nextStep": next_steps}


def project_story_board(repo):
    result = {"version": 1, "configured": (Path(repo) / FILE).exists(), "valid": True,
              "columns": [{"id": key, "label": label} for key, label in COLUMNS],
              "intents": [], "epics": [], "stories": [], "deliveries": [], "issues": []}
    try:
        document, store_hash = load(repo)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(valid=False, issues=[str(exc)])
        return result
    result.update(intents=document["intents"], epics=document["epics"], deliveries=document["deliveries"], storeSha256=store_hash)
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
    parser.add_argument("command", choices=(*COMMANDS, "status", "closure-preview"))
    parser.add_argument("--input", default="-", help="JSON file, or - for stdin")
    parser.add_argument("--expected-sha256", help="Digest returned by the last successful read or write")
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            document, store_hash = load(args.repo)
            result = status_result(document, store_hash)
        else:
            raw = sys.stdin.buffer.read(MAX_BYTES + 1) if args.input == "-" else Path(args.input).read_bytes()
            require(len(raw) <= MAX_BYTES, "Request exceeds input size limit.")
            request = json.loads(raw)
            result = closure_preview(args.repo, request) if args.command == "closure-preview" else execute(
                args.repo, args.command, request, args.expected_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "committed": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
