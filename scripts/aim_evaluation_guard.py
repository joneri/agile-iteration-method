#!/usr/bin/env python3
"""Read-only admission checks for native AIM evaluation runs, not product scoring.

The coordinator retains the activation result in its existing run record before
releasing implementation. A submission cannot manufacture that earlier record.
Package/PRD hashes, actual agent provenance and semantic coverage remain separate
assessor obligations; a valid runtime record is not proof of product quality.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import aim_stories as stories


class AdmissionError(ValueError):
    def __init__(self, message, validity="invalid"):
        super().__init__(message)
        self.validity = validity


def require(condition, message, validity="invalid"):
    if not condition:
        raise AdmissionError(message, validity)


def check(repo, delivery_id, scope_sha256, protocol_sha256, checkpoint,
          *, activation=None, outcome="completed"):
    """Return a compact receipt; never create/repair a ledger or run a product."""
    require(checkpoint in {"activation", "submission"}, "Unknown checkpoint.")
    require(outcome in {"completed", "failed", "interrupted"}, "Unknown outcome.")
    for value in (scope_sha256, protocol_sha256):
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
                "Expected frozen scope and protocol SHA-256 digests.")
    repo = Path(repo).resolve()
    document, store_sha256 = stories.load(repo)
    require(store_sha256 is not None, "AIM ledger is missing; do not release implementation.")
    matches = [d for d in document["deliveries"] if d["id"] == delivery_id]
    require(len(matches) == 1, "Expected exactly one selected native delivery.")
    delivery = matches[0]
    require(delivery["scopeSha256"] == scope_sha256, "Delivery differs from the frozen approved scope.")
    require("approval" in delivery, "Gate A/B approval is missing.")
    plan = delivery.get("qualityPlan")
    require(isinstance(plan, dict), "The evaluation delivery has no quality plan.")
    stories.validate_quality_plan(plan, delivery.get("qualityGoals", []), delivery["stories"],
                                  require_current_contract=True)
    require(plan["reviewPolicy"]["mode"] == "independent",
            "This material evaluation requires independent review.")
    identity = dict(repo=str(repo), deliveryId=delivery_id, scopeSha256=scope_sha256,
                    protocolSha256=protocol_sha256)
    result = dict(**identity, checkpoint=checkpoint, aimMethodValidity="valid",
                  revision=document["revision"], storeSha256=store_sha256,
                  nativePhase=delivery["status"], checkedAt=datetime.now(timezone.utc).isoformat())
    if checkpoint == "activation":
        require(delivery["status"] == "in_progress",
                "Activation admission must occur after approval and before implementation/review.")
        require("productBindings" not in delivery and "coreVerification" not in delivery,
                "Activation was not checked before measured/reviewed implementation; do not backfill it.")
        return result
    require(isinstance(activation, dict),
            "No coordinator activation receipt; method validity is unknown. Do not backfill it.", "unknown")
    require(all(activation.get(k) == v for k, v in identity.items())
            and activation.get("checkpoint") == "activation"
            and activation.get("aimMethodValidity") == "valid"
            and activation.get("nativePhase") == "in_progress",
            "Activation receipt belongs to another run, scope or phase.")
    revision = activation.get("revision")
    require(type(revision) is int and 0 <= revision <= document["revision"],
            "Activation receipt has an invalid revision.")
    receipt_sha = activation.get("storeSha256")
    require(isinstance(receipt_sha, str) and re.fullmatch(r"[0-9a-f]{64}", receipt_sha),
            "Activation receipt has an invalid store digest.")
    try:
        checked = datetime.fromisoformat(activation["checkedAt"].replace("Z", "+00:00"))
        created = datetime.fromisoformat(delivery["createdAt"].replace("Z", "+00:00"))
        require(checked.utcoffset() is not None and created <= checked <= datetime.now(timezone.utc),
                "Activation receipt has an invalid timestamp.")
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise AdmissionError("Activation receipt has an invalid timestamp.") from exc
    require(revision != document["revision"] or activation.get("storeSha256") == store_sha256,
            "Ledger bytes changed without a native revision.")
    allowed = {"validation", "acceptance"} if outcome == "completed" else {
        "in_progress", "review", "validation", "acceptance", "blocked"}
    require(delivery["status"] in allowed,
            "Declared outcome contradicts the native phase; keep it as a failed/interrupted attempt.")
    quality = next(x for x in stories.quality_result(repo, document)["deliveries"]
                   if x["deliveryId"] == delivery_id)
    result.update(outcome=outcome, quality=quality)
    # Failed/missing KPIs are findings, not a reason to discard a real AIM run.
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--delivery", required=True)
    parser.add_argument("--scope-sha256", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--checkpoint", choices=("activation", "submission"), required=True)
    parser.add_argument("--activation-record", type=Path,
                        help="Coordinator-owned existing run record containing aimActivation; never product-authored")
    parser.add_argument("--outcome", choices=("completed", "failed", "interrupted"), default="completed")
    args = parser.parse_args()
    try:
        activation = None
        if args.activation_record:
            try:
                activation = json.loads(args.activation_record.read_text())["aimActivation"]
            except (FileNotFoundError, KeyError) as exc:
                raise AdmissionError("No coordinator activation receipt; do not backfill it.", "unknown") from exc
        result = check(args.repo, args.delivery, args.scope_sha256, args.protocol_sha256,
                       args.checkpoint, activation=activation, outcome=args.outcome)
    except (ValueError, OSError, KeyError, stories.StoryError) as exc:
        print(json.dumps(dict(aimMethodValidity=getattr(exc, "validity", "invalid"),
                              error=str(exc))))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
