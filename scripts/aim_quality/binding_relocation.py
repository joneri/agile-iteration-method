"""Append-only locations for identical historical inputs, never product outputs."""
from __future__ import annotations

import copy
import hashlib
import json
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional),
            "Binding relocation has missing or unsupported fields.")


REQUEST_FIELDS = ("deliveryId", "activityId", "attempt", "receiptSha256", "mappings",
                  "reason", "evidence", "coordinatorSession")
RECORD_FIELDS = tuple(k for k in REQUEST_FIELDS if k != "deliveryId") + (
    "version", "scopeSha256", "reworkRevision", "requestSha256", "at")


def target(delivery, activity_id, attempt):
    require(type(attempt) is int and attempt >= 1, "Invalid relocation attempt.")
    task = next((a for a in delivery.get("executionPlan", {}).get("activities", [])
                 if a["id"] == activity_id), None)
    receipt = next((r for r in delivery.get("activityReceipts", [])
                    if r["activityId"] == activity_id and r["attempt"] == attempt), None)
    require(task is not None and task["kind"] == "read",
            "Relocate only historical inputs of read activities, never write outputs or final review.")
    require(receipt is not None and receipt["status"] == "completed",
            "Binding relocation requires an original completed read receipt.")
    return receipt


def apply_mappings(bindings, mappings):
    require(isinstance(mappings, list) and 1 <= len(mappings) <= 64,
            "Supply 1–64 binding mappings.")
    sources, destinations = [], []
    for item in mappings:
        fields(item, ("from", "to"))
        for ref in (item["from"], item["to"]):
            fields(ref, ("path", "sha256"))
            require(isinstance(ref["path"], str) and bool(ref["path"].strip()), "Invalid relocation path.")
            require(isinstance(ref["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]),
                    "Invalid relocation source fingerprint.")
        require(item["from"] in bindings, "Relocation source is not a current binding of this exact receipt.")
        require(item["from"]["path"] != item["to"]["path"], "Relocation requires a different baseline path.")
        require(item["from"]["sha256"] == item["to"]["sha256"],
                "Relocation must preserve the exact original content fingerprint.")
        sources.append(item["from"]["path"])
        destinations.append(item["to"]["path"])
    require(len(set(sources)) == len(sources) and len(set(destinations)) == len(destinations),
            "Duplicate binding relocation source or destination.")
    replacements = {item["from"]["path"]: item["to"] for item in mappings}
    result = [copy.deepcopy(replacements.get(ref["path"], ref)) for ref in bindings]
    require(len({ref["path"] for ref in result}) == len(result), "Relocation collides with an existing binding.")
    return result


def effective_bindings(delivery, receipt):
    bindings = copy.deepcopy(receipt.get("sourceBindings", []))
    if not delivery.get("bindingRelocations"):
        return bindings
    fingerprint = digest(receipt)
    for record in delivery.get("bindingRelocations", []):
        if (record["activityId"], record["attempt"], record["receiptSha256"]) == (
                receipt["activityId"], receipt["attempt"], fingerprint):
            bindings = apply_mappings(bindings, record["mappings"])
    return bindings


def validate_records(delivery):
    """History survives new attempts/rework; eligibility is checked only on write."""
    states, ids = {}, set()
    for record in delivery.get("bindingRelocations", []):
        fields(record, RECORD_FIELDS)
        require(type(record["version"]) is int and record["version"] == 1, "Invalid relocation version.")
        receipt = target(delivery, record["activityId"], record["attempt"])
        require(record["receiptSha256"] == digest(receipt), "Original relocated receipt changed.")
        require(record["scopeSha256"] == delivery["scopeSha256"]
                and type(record["reworkRevision"]) is int
                and record["reworkRevision"] == receipt.get("reworkRevision", 0),
                "Relocation has a different scope or activity generation.")
        request = {k: record[k] for k in REQUEST_FIELDS if k != "deliveryId"}
        request["deliveryId"] = delivery["id"]
        require(record["requestSha256"] == digest(request), "Relocation request fingerprint changed.")
        require(record["requestSha256"] not in ids, "Duplicate relocation journal entry.")
        if delivery.get("executionPlan", {}).get("orchestration"):
            activations = delivery.get("orchestrationActivationHistory", []) + (
                [delivery["orchestrationActivation"]] if "orchestrationActivation" in delivery else [])
            require(record["coordinatorSession"] in {actor["session"] for a in activations for actor in a["dispatchers"]},
                    "Relocation coordinator has no retained Native activation.")
        ids.add(record["requestSha256"])
        key = (record["activityId"], record["attempt"])
        states[key] = apply_mappings(states.get(key, receipt["sourceBindings"]), record["mappings"])


def relocate(document, request, *, check_reference, bind_evidence, at):
    fields(request, REQUEST_FIELDS)
    require(type(request["attempt"]) is int and request["attempt"] >= 1, "Invalid relocation attempt.")
    require(isinstance(request["reason"], str) and 0 < len(request["reason"].strip()) <= 2000,
            "Supply a bounded relocation reason.")
    require(isinstance(request["coordinatorSession"], str) and 0 < len(request["coordinatorSession"].strip()) <= 128,
            "Supply the actual relocation coordinator session.")
    delivery = next((d for d in document["deliveries"] if d["id"] == request["deliveryId"]), None)
    require(delivery is not None, "Unknown relocation delivery.")
    phase = delivery.get("blockedFrom") if delivery["status"] == "blocked" else delivery["status"]
    require(delivery["status"] not in {"accepted", "cancelled"}
            and phase == "in_progress" and "approval" in delivery,
            "Relocate bindings only during approved implementation or its preserved block.")
    from .orchestration_runtime import native_graph, _activation
    if native_graph(delivery) is not None:
        _activation(delivery, request["coordinatorSession"])
    receipt = target(delivery, request["activityId"], request["attempt"])
    latest = next(r for r in reversed(delivery["activityReceipts"]) if r["activityId"] == request["activityId"])
    require(receipt == latest and receipt.get("reworkRevision", 0) == delivery.get("activityReworkRevision", 0),
            "Cannot relocate a superseded attempt or an earlier rework generation.")
    require(request["receiptSha256"] == digest(receipt), "Stale or different original receipt fingerprint.")
    existing = next((r for r in delivery.get("bindingRelocations", [])
                     if r["requestSha256"] == digest(request)), None)
    bindings = effective_bindings(delivery, receipt)
    if existing is None:
        apply_mappings(bindings, request["mappings"])
    # The old live path may have changed or vanished. Verify the preserved
    # original bytes at the new location and the unchanged actual review proof.
    # A retry acknowledges retained history; subsequent moves may have retired
    # its destinations. Verify the receipt's current locations instead.
    references = bindings if existing is not None else [m["to"] for m in request["mappings"]]
    for ref in references:
        check_reference(ref)
    bind_evidence(receipt["evidence"])
    evidence = bind_evidence(request["evidence"])
    if existing is not None:
        return copy.deepcopy(existing), False
    require(len(delivery.get("bindingRelocations", [])) < 128, "Binding relocation history is full.")
    record = {k: copy.deepcopy(request[k]) for k in REQUEST_FIELDS if k != "deliveryId"}
    record.update(version=1, scopeSha256=delivery["scopeSha256"],
                  reworkRevision=receipt.get("reworkRevision", 0), requestSha256=digest(request), at=at,
                  evidence=evidence)
    delivery.setdefault("bindingRelocations", []).append(record)
    return copy.deepcopy(record), True


def verify_records(delivery, check_reference, bind_evidence):
    # Old journal locations are history. Only the effective locations of the
    # latest current-generation receipts are active proof consumers.
    latest = {r["activityId"]: r for r in delivery.get("activityReceipts", [])}
    for record in delivery.get("bindingRelocations", []):
        bind_evidence(record["evidence"])
    if delivery["status"] == "accepted":
        return
    for receipt in latest.values():
        if receipt.get("reworkRevision", 0) != delivery.get("activityReworkRevision", 0):
            continue
        records = [r for r in delivery.get("bindingRelocations", [])
                   if r["activityId"] == receipt["activityId"] and r["attempt"] == receipt["attempt"]]
        if records:
            bindings = effective_bindings(delivery, receipt)
            # Verify only relocated consumers here; other stale inputs still
            # block graph completion normally and are never silently waived.
            moved = {m["to"]["path"] for r in records for m in r["mappings"]}
            for ref in bindings:
                if ref["path"] in moved:
                    check_reference(ref)
