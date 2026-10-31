#!/usr/bin/env python3
"""Validate and total independent observations against the frozen pilot rubric.

Does not play games or assign subjective points. A structurally valid assessment
does not prove its evidence true; independent inspection remains essential.
"""
import argparse
import json
import math
from pathlib import Path


def summarize(protocol, assessment):
    expected_levels = {level["id"] for level in protocol["brief"]["levels"]}
    levels = assessment["levels"]
    if len(levels) != len(expected_levels) or {level["id"] for level in levels} != expected_levels:
        raise ValueError("Assess each original level exactly once.")
    if assessment.get("methodIdentityKnownBeforeScoring") not in (True, False):
        raise ValueError("Report the actual blinding limitation.")
    totals, complete = {}, True
    anchors = protocol["scoring"]["anchors"]
    for level in levels:
        if type(level["requiredCapabilitiesDemonstrated"]) is not bool:
            raise ValueError("Capability demonstration must be an explicit judgment.")
        if level["observedPlayable"] not in (True, False, None):
            raise ValueError("Playable observation is true, false or unavailable.")
        if set(level["categories"]) != set(anchors):
            raise ValueError("All frozen rubric categories are required.")
        score = 0
        for category, specifications in anchors.items():
            rows = level["categories"][category]
            if len(rows) != len(specifications):
                raise ValueError("Every frozen scoring anchor requires its own assessment.")
            for row, specification in zip(rows, specifications):
                value = row["points"]
                maximum = specification["maximum"]
                if type(value) not in (int, float) or not math.isfinite(value) or value not in (0, maximum / 2, maximum):
                    raise ValueError("Use the frozen zero/half/full anchor, not invented precision.")
                if not isinstance(row.get("basis"), str) or not row["basis"].strip():
                    raise ValueError("Each score needs its concrete observation or unavailable limitation.")
                if value > 0 and not row.get("evidence"):
                    raise ValueError("Positive points require inspected evidence references.")
                score += value
        if level["observedPlayable"] is not True and level["categories"]["playability_and_cooperation"][0]["points"] != 0:
            raise ValueError("No native normal-input playable observation: no live-playability points.")
        totals[level["id"]] = score
        complete &= level["observedPlayable"] is True and level["requiredCapabilitiesDemonstrated"]
    return {"perLevel": totals, "total": sum(totals.values()),
            "maximum": protocol["scoring"]["totalMaximum"],
            "allThreePlayableWithRequiredCapabilities": complete,
            "methodIdentityKnownBeforeScoring": assessment["methodIdentityKnownBeforeScoring"],
            "inference": "Single paired pilot only; numeric totals are independent judgments, not general method superiority or user acceptance."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.protocol.read_text()), json.loads(args.assessment.read_text())), indent=2))
