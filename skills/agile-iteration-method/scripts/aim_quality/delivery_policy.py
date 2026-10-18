# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/delivery_policy.py
"""Delivery cadence and explicitly delegated product-owner decisions.

These checks bind declared authority to a frozen plan. The host must establish
the real human mandate and agent identity; a file or role name cannot do that.
"""
from __future__ import annotations

import copy
import json
import re


DEFAULT_POLICY = {"mode": "ship", "owner": {"kind": "human"}}
OWNER_DECISIONS = {"approve", "accept"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, required, optional=()):
    _require(isinstance(value, dict), "Delivery policy must contain objects.")
    _require(set(required) <= set(value) <= set(required) | set(optional),
             "Delivery policy has missing or unsupported fields.")


def _identity(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 240


def normalize_policy(value):
    """Normalize only a NEW plan; never infer policy for historical deliveries."""
    _fields(value, ("mode",), ("owner",))
    _require(isinstance(value["mode"], str) and value["mode"] in {"ship", "loop"}, "Delivery mode must be ship or loop.")
    owner = value.get("owner", {"kind": "human"})
    _require(isinstance(owner, dict), "Delivery owner must be an object.")
    if owner.get("kind") == "human":
        _fields(owner, ("kind",))
    else:
        _fields(owner, ("kind", "id", "session", "mandate", "decisions"))
        _require(owner["kind"] == "agent", "Delivery owner must be human or agent.")
        _require(_identity(owner["id"]) and _identity(owner["session"]),
                 "Agent owner requires its actual non-empty id and session.")
        mandate = owner["mandate"]
        _fields(mandate, ("path", "sha256"))
        _require(isinstance(mandate["path"], str) and mandate["path"].startswith(".aim/"),
                 "Agent owner requires contained human mandate evidence.")
        _require(isinstance(mandate["sha256"], str)
                 and re.fullmatch(r"[0-9a-f]{64}", mandate["sha256"]) is not None,
                 "Agent owner mandate requires a SHA-256 fingerprint.")
        decisions = owner["decisions"]
        _require(isinstance(decisions, list) and 1 <= len(decisions) <= 2
                 and all(isinstance(item, str) and item in OWNER_DECISIONS for item in decisions)
                 and len(set(decisions)) == len(decisions),
                 "Delegate only explicit approve and/or accept decisions.")
    return {"mode": value["mode"], "owner": copy.deepcopy(owner)}


def validate_authority_binding(authority, policy, operation):
    """Check a real decision's declared provenance, not evidence eligibility."""
    common = {"kind", "path", "sha256", "scopeSha256"}
    if authority.get("kind") == "user":
        _require(set(authority) == common, "User authority has unsupported fields.")
        return
    _require(authority.get("kind") == "agent",
             "This decision requires supplied user authority or an explicitly delegated agent owner; Auto is not final acceptance.")
    _require(set(authority) == common | {"id", "session"},
             "Agent decision requires its actual id and session.")
    _require(policy is not None, "Historical deliveries have no delegated agent owner.")
    owner = normalize_policy(policy)["owner"]
    _require(owner["kind"] == "agent", "No agent owner was delegated for this delivery.")
    _require(operation in owner["decisions"], "This owner decision was not delegated.")
    _require((authority["id"], authority["session"]) == (owner["id"], owner["session"]),
             "Decision identity does not match the delegated agent owner.")
    _require(authority["path"] != owner["mandate"]["path"]
             and authority["sha256"] != owner["mandate"]["sha256"],
             "The human mandate is not the agent owner's actual gate decision.")


def parse_owner_decision(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate JSON keys in owner decision evidence.")
            result[key] = value
        return result
    try:
        decision = json.loads(payload, object_pairs_hook=pairs)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("Owner decision evidence must be valid unambiguous JSON.") from exc
    _fields(decision, ("ownerDecisionVersion", "deliveryId", "operation", "scopeSha256",
                       "id", "session", "decision", "reason"))
    _require(type(decision["ownerDecisionVersion"]) is int and decision["ownerDecisionVersion"] == 1,
             "Unsupported owner decision evidence version.")
    _require(decision["decision"] == "approved" and isinstance(decision["reason"], str)
             and bool(decision["reason"].strip()) and len(decision["reason"]) <= 4000,
             "Owner decision must explicitly approve the scope with an assessment.")
    return decision


def validate_owner_decision(decision, authority, delivery_id, operation):
    expected = {"deliveryId": delivery_id, "operation": operation,
                **{key: authority[key] for key in ("id", "session", "scopeSha256")}}
    _require(all(decision.get(key) == value for key, value in expected.items()),
             "Owner decision evidence does not match this operation, delivery, identity or scope.")
