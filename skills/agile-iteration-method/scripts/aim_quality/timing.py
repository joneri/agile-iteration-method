# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/timing.py
"""Summarize one sequential run's attributed intervals without inventing time."""

from __future__ import annotations

from datetime import datetime
import re


ACTIVITIES = {
    # Mixed startup is not automatically verified repository improvement.
    "setup": "setup",
    "calibration": "repositoryImprovement",
    "configuration": "repositoryImprovement",
    "reflection": "repositoryImprovement",
    "knowledge-maintenance": "repositoryImprovement",
    "implementation": "implementation",
    "verification": "verification",
    "coordination": "coordination",
    "waiting": "waiting",
}
TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})"
)


def _instant(value: object) -> datetime:
    if not isinstance(value, str) or TIMESTAMP.fullmatch(value) is None:
        raise ValueError("interval timestamps require a date, time and explicit zone")
    # Python 3.9 accepts only three or six fractional digits in fromisoformat.
    normalized = value.replace("Z", "+00:00")
    if "." in normalized:
        prefix, suffix = normalized.split(".", 1)
        normalized = prefix + "." + suffix[:-6].ljust(6, "0") + suffix[-6:]
    zone = normalized[-6:]
    if zone == "-00:00" or int(zone[1:3]) > 23 or int(zone[4:]) > 59:
        raise ValueError("interval timestamp has an unknown or invalid timezone")
    return datetime.fromisoformat(normalized)


def summarize_timing(document: dict) -> dict:
    """Reject overlapping intervals rather than double-counting one session.

    These are attributed measurements, not verified proof of activity. Parallel
    sessions need separate reports; adding their durations is not wall time.
    """
    if (not isinstance(document, dict) or type(document.get("version")) is not int
            or document["version"] != 1):
        raise ValueError("timing version must be integer 1")
    intervals = document.get("intervals")
    if not isinstance(intervals, list) or not 1 <= len(intervals) <= 4096:
        raise ValueError("timing requires 1 to 4096 intervals")
    seen, parsed = set(), []
    for item in intervals:
        if not isinstance(item, dict):
            raise ValueError("each interval must be an object")
        identifier, activity = item.get("id"), item.get("activity")
        if (not isinstance(identifier, str) or not identifier.strip()
                or len(identifier) > 128 or identifier in seen):
            raise ValueError("interval ids must be nonempty, bounded and unique")
        seen.add(identifier)
        if not isinstance(activity, str) or activity not in ACTIVITIES:
            raise ValueError("interval activity is unsupported")
        start, end = _instant(item.get("start")), _instant(item.get("end"))
        if end < start:
            raise ValueError("interval ends before it starts")
        parsed.append((start, end, activity, identifier))
    parsed.sort()
    by_activity = {name: 0.0 for name in ACTIVITIES}
    previous_end = None
    for start, end, activity, identifier in parsed:
        if previous_end is not None and start < previous_end:
            raise ValueError(f"interval {identifier} overlaps another interval")
        previous_end = end
        by_activity[activity] += (end - start).total_seconds()
    categories = {name: 0.0 for name in set(ACTIVITIES.values())}
    for activity, duration in by_activity.items():
        categories[ACTIVITIES[activity]] += duration
    recorded = sum(by_activity.values())
    elapsed = (parsed[-1][1] - parsed[0][0]).total_seconds()
    return {
        "version": 1,
        "intervals": len(parsed),
        "secondsByActivity": {key: round(value, 6) for key, value in by_activity.items()},
        "secondsByCategory": {key: round(categories[key], 6) for key in sorted(categories)},
        "recordedSeconds": round(recorded, 6),
        "elapsedSeconds": round(elapsed, 6),
        "unattributedSeconds": round(max(0.0, elapsed - recorded), 6),
        "activityIndependentlyVerified": False,
        "scope": "one sequential session; includes recorded waiting; gaps remain unattributed",
    }
