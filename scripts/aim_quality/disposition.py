"""Present owner disposition of approved work, without acceptance or history loss."""
from __future__ import annotations

import copy
import hashlib
import json


APPROVED_PHASES = {"in_progress", "review", "validation", "acceptance", "blocked"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional),
            "Disposition has missing or unsupported fields.")


def eligible(delivery):
    require(delivery["status"] in APPROVED_PHASES and "approval" in delivery,
            "Owner disposition requires an approved, unaccepted delivery.")
    require(not any(r["status"] == "running" for r in delivery.get("activityReceipts", [])),
            "Reconcile actual running activities before owner disposition, even if their proof is stale.")


def prepare(document, request, make_plan):
    """Build a read-only context and the same prospective atomic replacement."""
    fields(request, ("deliveryId", "operation", "reason"), ("replacement",))
    require(request["operation"] in {"cancel", "replace"}, "Disposition operation must be cancel or replace.")
    reason = request["reason"]
    require(isinstance(reason, str) and bool(reason.strip()) and len(reason) <= 2000,
            "Disposition reason must be non-empty text of at most 2000 characters.")
    require(("replacement" in request) == (request["operation"] == "replace"),
            "Only replace requires a replacement plan.")
    candidate = copy.deepcopy(document)
    delivery = next((d for d in candidate["deliveries"] if d["id"] == request["deliveryId"]), None)
    require(delivery is not None, "Unknown disposition delivery.")
    eligible(delivery)
    context = dict(version=1, deliveryId=delivery["id"], operation=request["operation"],
                   reason=reason, fromStatus=delivery["status"], deliverySha256=digest(delivery))
    if "ownerPriority" in candidate.get("orchestration", {}):
        before = candidate["orchestration"]["ownerPriority"]
        retired = {i["id"] for i in delivery["intents"]}
        after = [i for i in before if i not in retired]
        context["ownerPriorityBefore"] = copy.deepcopy(before)
        context["ownerPriorityAfter"] = after
        candidate["orchestration"]["ownerPriority"] = copy.deepcopy(after)
    delivery["status"] = "cancelled"
    ids = {s["id"] for s in delivery["stories"]}
    for story in candidate["stories"]:
        if story["id"] in ids:
            story["status"] = "draft"
    if request["operation"] == "replace":
        # The normal planner enforces fresh identities, ready requirements and
        # the complete quality contract. It does not approve or activate work.
        make_plan(candidate, request["replacement"])
        replacement = candidate["deliveries"][-1]
        context["replacement"] = {k: replacement[k] for k in ("id", "scopeSha256")}
    return context, candidate


def validate_record(document, delivery):
    record = delivery.get("disposition")
    if record is None:
        require(not (delivery["status"] == "cancelled" and "approval" in delivery),
                "Cancelled approved work requires an owner disposition record.")
        return
    fields(record, ("context", "scopeSha256", "authority", "at"))
    context = record["context"]
    fields(context, ("version", "deliveryId", "operation", "reason", "fromStatus", "deliverySha256"),
           ("replacement", "ownerPriorityBefore", "ownerPriorityAfter"))
    require(type(context["version"]) is int and context["version"] == 1,
            "Unsupported disposition context version.")
    require(context["operation"] in {"cancel", "replace"}
            and ("replacement" in context) == (context["operation"] == "replace"),
            "Invalid disposition operation or replacement.")
    require(delivery["status"] == "cancelled" and context["deliveryId"] == delivery["id"]
            and context["fromStatus"] in APPROVED_PHASES,
            "Disposition must retain its original approved delivery and phase.")
    original = copy.deepcopy(delivery)
    original.pop("disposition")
    original["status"] = context["fromStatus"]
    eligible(original)
    require(original["approval"]["scopeSha256"] == original["scopeSha256"],
            "Historical approval scope mismatch.")
    require(context["deliverySha256"] == digest(original), "Disposed delivery history changed.")
    require(record["scopeSha256"] == digest(context), "Disposition context fingerprint is invalid.")
    require(("ownerPriorityBefore" in context) == ("ownerPriorityAfter" in context),
            "Disposition priority history is incomplete.")
    if "ownerPriorityBefore" in context:
        before = context["ownerPriorityBefore"]
        retired = {i["id"] for i in original["intents"]}
        require(isinstance(before, list) and all(isinstance(i, str) for i in before)
                and len(before) == len(set(before))
                and context["ownerPriorityAfter"] == [i for i in before if i not in retired],
                "Disposition must retain unrelated priorities and record retired priorities.")
    authority = record["authority"]
    fields(authority, ("kind", "path", "sha256", "scopeSha256"))
    require(authority["kind"] == "user" and authority["scopeSha256"] == record["scopeSha256"],
            "Disposition requires exact present human authority; existing gate delegation is insufficient.")
    if "replacement" in context:
        fields(context["replacement"], ("id", "scopeSha256"))
        replacement = next((d for d in document["deliveries"] if d["id"] == context["replacement"]["id"]), None)
        require(replacement is not None and replacement["id"] != delivery["id"]
                and replacement["scopeSha256"] == context["replacement"]["scopeSha256"],
                "Disposition replacement is missing or its frozen scope changed.")


def decision(record):
    """Exact typed evidence prevents repurposing an old plan/acceptance decision."""
    context = record["context"]
    return dict(dispositionDecisionVersion=1, deliveryId=context["deliveryId"],
                operation=context["operation"], scopeSha256=record["scopeSha256"],
                reason=context["reason"])


def verify_decision(record, payload):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "Duplicate disposition decision JSON key.")
            value[key] = item
        return value
    actual = json.loads(payload, object_pairs_hook=pairs)
    require(isinstance(actual, dict) and type(actual.get("dispositionDecisionVersion")) is int
            and actual == decision(record),
            "Owner disposition evidence must bind this exact operation, delivery, reason and context.")
