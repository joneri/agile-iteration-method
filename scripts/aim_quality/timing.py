"""Summarize one sequential run's attributed intervals without inventing time."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
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

TRACE_LIMIT = 64 * 1024 * 1024
TRACE_ACTIVITIES = ("administration", "implementation", "verification", "review", "mixed")


def summarize_trace(payload: bytes, first_call: str, last_call: str, *,
                    activity="mixed", max_calls=None, max_input_bytes=None) -> dict:
    """Summarize an explicit window of existing Codex JSONL, without executing it.

    Call envelopes are observable; nested shell/file operations and model work
    are not. Activity is supplied attribution, never inferred from command text.
    """
    if len(payload) > TRACE_LIMIT:
        raise ValueError("trace exceeds 64 MiB; select a smaller existing trace")
    if not first_call or not last_call or activity not in TRACE_ACTIVITIES:
        raise ValueError("trace needs explicit call boundaries and supported activity")
    for limit in (max_calls, max_input_bytes):
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("trace budgets must be nonnegative integers")
    calls, outputs, intervals, output_hashes = {}, set(), [], set()
    input_bytes = output_bytes = repeated_bytes = 0
    started = finished = False
    start = end = previous = None
    user_message = False

    def size_and_hash(value):
        raw = (value if isinstance(value, str) else json.dumps(
            value, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
        return len(raw), hashlib.sha256(raw).hexdigest()

    for line in payload.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("trace events must be objects")
        item = event.get("payload", {})
        if not isinstance(item, dict):
            raise ValueError("trace payloads must be objects")
        kind, identifier = item.get("type"), item.get("call_id")
        response = event.get("type") == "response_item"
        is_call = response and kind in ("function_call", "custom_tool_call")
        is_output = response and kind in ("function_call_output", "custom_tool_call_output")
        if not started:
            if not is_call or identifier != first_call:
                continue
            started = True
            start = _instant(event.get("timestamp"))
        timestamp = _instant(event.get("timestamp"))
        if previous is not None and timestamp < previous:
            raise ValueError("selected trace timestamps go backwards")
        previous = timestamp
        if item.get("role") == "user" or kind == "user_message":
            user_message = True
        if is_call:
            if not isinstance(identifier, str) or not identifier or identifier in calls:
                raise ValueError("selected call IDs must be nonempty and unique")
            field = "input" if kind == "custom_tool_call" else "arguments"
            if field not in item:
                raise ValueError("selected call is missing input")
            calls[identifier] = timestamp
            input_bytes += size_and_hash(item[field])[0]
        elif is_output:
            if (not isinstance(identifier, str) or not identifier or identifier not in calls
                    or identifier in outputs or "output" not in item):
                raise ValueError("selected output has no unique matching call")
            outputs.add(identifier)
            length, fingerprint = size_and_hash(item["output"])
            output_bytes += length
            if fingerprint in output_hashes:
                repeated_bytes += length
            output_hashes.add(fingerprint)
            intervals.append((calls[identifier], timestamp))
            if identifier == last_call:
                end, finished = timestamp, True
                break
    if not finished or set(calls) != outputs:
        raise ValueError("trace window is missing boundaries or contains unfinished calls")
    # Union avoids double counting overlapping tool waits in one session.
    union = []
    for left, right in sorted(intervals):
        if union and left <= union[-1][1]:
            union[-1] = (union[-1][0], max(union[-1][1], right))
        else:
            union.append((left, right))
    observed_wait = sum((right - left).total_seconds() for left, right in union)
    elapsed = (end - start).total_seconds()
    exceeded = []
    for name, value, limit in (("toolCalls", len(calls), max_calls),
                               ("inputBytes", input_bytes, max_input_bytes)):
        if limit is not None and value > limit:
            exceeded.append({"metric": name, "observed": value, "limit": limit})
    return {
        "version": 1, "sourceSha256": hashlib.sha256(payload).hexdigest(), "sourceBytes": len(payload),
        "firstCall": first_call, "lastCall": last_call,
        "activity": activity, "activityIndependentlyVerified": False,
        "toolCalls": len(calls), "inputBytes": input_bytes, "outputBytes": output_bytes,
        "exactRepeatedOutputBytes": repeated_bytes,
        "elapsedSeconds": round(elapsed, 6),
        "toolRoundTripUnionSeconds": round(observed_wait, 6),
        "outsideToolCallsSeconds": round(max(0, elapsed - observed_wait), 6),
        "containsUserMessage": user_message,
        "modelSeconds": None, "filesystemSeconds": None, "userWaitingSeconds": None,
        "fileReads": None, "fileWrites": None, "toolRounds": None,
        "tokens": None, "agentTotalSeconds": None,
        "budgetState": "exceeded" if exceeded else (
            "within" if max_calls is not None or max_input_bytes is not None else "not-set"),
        "exceeded": exceeded, "needsReview": bool(exceeded),
        "nextAction": ("Inspect repeated reads/writes; reuse valid evidence and compact confirmed "
                       "results within mandate. Preserve required checks; report any resource gap."
                       if exceeded else "Retain this observation; no additional measurement run required."),
        "scope": "One selected session window; includes all interleaved tool envelopes, not nested operations or other agents. Activity and boundaries need review.",
        "byteEncoding": "UTF-8 strings; structured payloads serialized as compact JSON. Repeated output is not necessarily waste.",
    }


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
