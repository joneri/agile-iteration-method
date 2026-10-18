# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/delivery.py
"""Frozen verification obligations, using the existing consolidated evidence.

Structure and source-bound observations are checked here. Whether a check covers
the user's intent or was honestly executed remains an independent review duty.
"""
from __future__ import annotations

import json
import math
import re

from .goals import (_digest, _fields, _pairs, _read_reference, _reference, _report_context,
                    _require, _sha, _text)

CONTEXT = ("workload", "environment", "method")
CASE_CATEGORIES = ("failureCases", "nonDefaultModes", "resultValidity", "workloadFamilies")


def stages(check):
    return {"core", "delivery"} if check["stage"] == "both" else {check["stage"]}


def _projection_fields(observation, expected):
    _require(isinstance(observation, dict) and bool(observation)
             and set(observation) == set(expected),
             "Raw observation must cover exactly every expected field.")
    for recipe in observation.values():
        fields = {"pointer", "transform"} if isinstance(recipe, dict) and "transform" in recipe else {"pointer"}
        _fields(recipe, fields, "Raw observation field")
        pointer = recipe["pointer"]
        _require(isinstance(pointer, str) and len(pointer) <= 512
                 and (pointer == "" or pointer.startswith("/"))
                 and len(pointer.split("/")) <= 17
                 and re.search(r"~(?![01])", pointer) is None,
                 "Raw observation requires a bounded JSON pointer.")
        if "transform" in recipe:
            _require(recipe["transform"] == "length", "Only array length transformation is supported.")


def _raw_float(text):
    value = float(text)
    _require(math.isfinite(value), "Raw observation requires finite JSON.")
    return value


def _project(raw, observation):
    result = {}
    for name, recipe in observation.items():
        value = raw
        for token in recipe["pointer"].split("/")[1:]:
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(value, dict):
                _require(token in value, "Raw observation pointer is missing a field.")
                value = value[token]
            else:
                _require(isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token)
                         and int(token) < len(value), "Raw observation pointer has an invalid array index.")
                value = value[int(token)]
        if "transform" in recipe:
            _require(isinstance(value, list), "Raw observation length requires an array.")
            value = len(value)
        result[name] = value
    return result


def validate_plan(plan, goals, stories, *, require_current_contract=False):
    fields = {"checks", "numericGoals", "rationale", "sharedRequirements"}
    if isinstance(plan, dict) and "primaryResult" in plan:
        fields.add("primaryResult")
    if isinstance(plan, dict) and "caseCoverage" in plan:
        fields.add("caseCoverage")
    if isinstance(plan, dict) and "reviewPolicy" in plan:
        fields.add("reviewPolicy")
    _fields(plan, fields, "Quality plan")
    current = require_current_contract or "caseCoverage" in plan
    _require(not current or "primaryResult" in plan,
             "New plans require primaryResult: assess complete-result latency separately from responsiveness.")
    _require(not current or "caseCoverage" in plan,
             "New plans require caseCoverage linked to checks or explicit non-applicability.")
    _require(not require_current_contract or "reviewPolicy" in plan,
             "New plans require reviewPolicy: independent material review or a justified nonmaterial exception.")
    if "reviewPolicy" in plan:
        policy = plan["reviewPolicy"]
        _require(isinstance(policy, dict), "Review policy must be an object.")
        _require(policy.get("mode") in ("independent", "self"),
                 "Review policy must require independent review or justify self-review of nonmaterial work.")
        _fields(policy, {"mode", "reason"} if policy["mode"] == "self" else {"mode"}, "Review policy")
        if policy["mode"] == "self":
            _text(policy["reason"], "Nonmaterial self-review reason")
    _text(plan["rationale"], "Quality applicability rationale")
    _require(plan["numericGoals"] in ("required", "not_applicable"),
             "Decide numeric goal applicability explicitly.")
    _require(bool(goals) == (plan["numericGoals"] == "required"),
             "Applicable numeric goals must be declared; otherwise justify non-applicability.")
    checks = plan["checks"]
    _require(isinstance(checks, list) and 1 <= len(checks) <= 32,
             "Quality plan requires 1–32 checks, reusing checks across criteria.")
    wanted = {f"{s['id']}/{ac['id']}" for s in stories for ac in s["acceptanceCriteria"]}
    known_goals = {g["id"] for g in goals}
    covered, linked_goals, ids = set(), set(), set()
    for check in checks:
        optional = {"observation"} if isinstance(check, dict) and "observation" in check else set()
        _fields(check, {"id", "criteria", "kind", "stage", *CONTEXT, "expected", "goalIds", *optional},
                "Quality check")
        identifier = check["id"]
        _require(isinstance(identifier, str) and len(identifier) <= 100
                 and re.fullmatch(r"QC-[A-Z0-9]+(?:-[A-Z0-9]+)*", identifier),
                 "Quality check requires a bounded QC-* identifier.")
        _require(identifier not in ids, "Duplicate quality check ID.")
        ids.add(identifier)
        _require(check["kind"] in ("behavior", "performance", "journey"), "Unknown quality check kind.")
        _require(check["stage"] in ("core", "delivery", "both"), "Unknown quality check stage.")
        for key in CONTEXT:
            _text(check[key], f"Quality check {key}")
        refs = check["criteria"]
        _require(isinstance(refs, list) and 0 <= len(refs) <= len(wanted)
                 and all(isinstance(r, str) and r in wanted for r in refs)
                 and len(set(refs)) == len(refs), "Quality check must reference selected Story/criterion IDs.")
        covered.update(refs)
        goal_ids = check["goalIds"]
        _require(isinstance(goal_ids, list) and len(goal_ids) <= 32
                 and all(isinstance(g, str) and g in known_goals for g in goal_ids)
                 and len(set(goal_ids)) == len(goal_ids), "Quality check refers to unknown/duplicate numeric goals.")
        linked_goals.update(goal_ids)
        expected = check["expected"]
        _require(isinstance(expected, dict) and len(expected) <= 32,
                 "Expected observations must be a bounded object.")
        _require(bool(expected) or bool(goal_ids), "Supply expected observations or raw numeric goals.")
        _require(not set(expected) & {"passed", "verified", "success"},
                 "Use concrete expected observations, not a caller's pass flag.")
        _require(len(json.dumps(expected, allow_nan=False)) <= 4000, "Expected observations exceed the bound.")
        if "observation" in check:
            _projection_fields(check["observation"], expected)
        if check["kind"] == "performance":
            _require(bool(goal_ids) and "core" in stages(check),
                     "Performance checks require numeric goals measured on the early core.")
            if current:
                _require(bool(expected),
                         "Performance checks require concrete result observations on the timed workload.")
                _require(all(all(check[key] == goal[key] for key in CONTEXT)
                             for goal in goals if goal["id"] in goal_ids),
                         "Performance check and every linked goal must describe the same workload, environment and method.")
    _require(covered == wanted, "Quality plan must cover every selected criterion.")
    shared = plan["sharedRequirements"]
    _require(isinstance(shared, list) and 1 <= len(shared) <= 16,
             "Assess relevant intent/Epic/shared quality requirements explicitly.")
    for requirement in shared:
        _fields(requirement, {"source", "requirement", "checkIds"}, "Shared quality requirement")
        _text(requirement["source"], "Shared requirement source")
        _text(requirement["requirement"], "Shared quality requirement")
        linked = requirement["checkIds"]
        _require(isinstance(linked, list) and 1 <= len(linked) <= len(ids)
                 and all(isinstance(c, str) and c in ids for c in linked)
                 and len(set(linked)) == len(linked), "Shared requirement needs concrete quality checks.")
    _require(linked_goals == known_goals, "Every numeric goal must belong to a quality check.")
    _require(any("core" in stages(c) for c in checks), "Quality plan requires an early core check.")
    _require(any(c["kind"] == "journey" and "delivery" in stages(c) for c in checks),
             "Quality plan requires a real-entry delivery journey check.")
    if "primaryResult" in plan:
        primary = plan["primaryResult"]
        _require(isinstance(primary, dict), "Primary result must identify its core check.")
        numeric = "latencyGoalId" in primary
        _fields(primary, {"checkId", "latencyGoalId" if numeric else "notApplicableReason"},
                "Primary result")
        _require(isinstance(primary["checkId"], str) and primary["checkId"] in ids,
                 "Primary result needs a known quality check.")
        check = next(c for c in checks if c["id"] == primary["checkId"])
        _require("core" in stages(check) and bool(check["criteria"]),
                 "Primary result requires an early core check tied to selected criteria.")
        if numeric:
            identifier = primary["latencyGoalId"]
            _require(isinstance(identifier, str) and identifier in check["goalIds"]
                     and check["kind"] == "performance",
                     "Primary result latency needs a linked core performance goal.")
            goal = next(g for g in goals if g["id"] == identifier)
            _require(goal["unit"] in ("s", "ms") and goal["operator"] == "<="
                     and goal["aggregation"] in ("median", "max"),
                     "Primary result latency requires seconds/milliseconds, an upper bound and median/max samples.")
            _require(all(check[key] == goal[key] for key in CONTEXT),
                     "Primary result check and latency goal must describe the same workload, environment and method.")
        else:
            _text(primary["notApplicableReason"], "Primary result latency non-applicability reason")
    if "caseCoverage" in plan:
        coverage = plan["caseCoverage"]
        _fields(coverage, set(CASE_CATEGORIES), "Case coverage")
        by_id = {c["id"]: c for c in checks}
        linked_cases = {}
        for category in CASE_CATEGORIES:
            entry = coverage[category]
            applicable = isinstance(entry, dict) and "checkIds" in entry
            _fields(entry, {"checkIds" if applicable else "notApplicableReason"},
                    f"Case coverage {category}")
            linked = entry["checkIds"] if applicable else []
            if applicable:
                _require(isinstance(linked, list) and 1 <= len(linked) <= len(ids)
                         and all(isinstance(c, str) and c in ids for c in linked)
                         and len(set(linked)) == len(linked),
                         f"Case coverage {category} needs known, unique check IDs.")
                _require(all(by_id[c]["expected"] for c in linked),
                         f"Case coverage {category} needs concrete expected observations.")
            else:
                _text(entry["notApplicableReason"], f"Case coverage {category} non-applicability reason")
            linked_cases[category] = set(linked)
        performance = {c["id"] for c in checks if c["kind"] == "performance"}
        _require(linked_cases["workloadFamilies"] == performance,
                 "Workload families must cover every performance check and only performance checks.")
        _require(performance <= linked_cases["resultValidity"],
                 "Every timed workload family also requires result validity on that same check.")


def assess_checks(repo, plan, refs, bindings, *, read_reference=None,
                  raw_read_reference=None, scope_sha256=None):
    """Compare actual observations with the frozen plan, never execute method text."""
    reader = read_reference or _read_reference
    known = {c["id"]: c for c in plan["checks"]}
    records = {}
    raw_cache = {}
    for ref in refs:
        _reference(ref, measurement=True)
        payload, fresh = reader(repo, ref)
        _require(fresh, f"Quality evidence changed: {ref['path']}.")
        try:
            report = json.loads(payload, object_pairs_hook=_pairs)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise ValueError(f"Invalid quality check report: {exc}") from exc
        _require(isinstance(report, dict), "Quality check report must be an object.")
        # Numeric-only reports may share this reference collection.
        if "qualityCheckVersion" not in report:
            continue
        _require(report["qualityCheckVersion"] == "1.0", "Unsupported quality check version.")
        context = _report_context(report, scope_sha256)
        items = report.get("checks")
        _require(isinstance(items, list) and 1 <= len(items) <= 32, "Quality report requires 1–32 checks.")
        for item in items:
            identifier = item.get("checkId") if isinstance(item, dict) else None
            _require(isinstance(identifier, str) and identifier in known,
                     "Observation refers to an unknown quality check.")
            check = known[identifier]
            if "observation" in check:
                required = {"checkId", "raw"} if context is not None else {
                    "checkId", "raw", *CONTEXT, "productBindingsSha256"}
                _fields(item, required, "Raw check observation; observed overrides are forbidden")
                raw_ref = item["raw"]
                _reference(raw_ref, measurement=True)
                _require(raw_ref["path"] != ref["path"],
                         "Raw observation must be independent of its report.")
                key = (raw_ref["path"], raw_ref["sha256"])
                if key not in raw_cache:
                    payload, fresh = (raw_read_reference or reader)(repo, raw_ref)
                    _require(fresh, "Raw observation evidence changed.")
                    _require(not (repo / raw_ref["path"]).samefile(repo / ref["path"]),
                             "Raw observation must be independent of its report.")
                    try:
                        raw_cache[key] = json.loads(payload, object_pairs_hook=_pairs, parse_float=_raw_float,
                            parse_constant=lambda value: _require(False, "Raw observation requires finite JSON."))
                    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
                        raise ValueError(f"Invalid raw observation JSON: {exc}") from exc
                item = {k: v for k, v in item.items() if k != "raw"}
                item["observed"] = _project(raw_cache[key], check["observation"])
            if context is not None:
                _fields(item, {"checkId", "observed"}, "Compact check observation")
                identifier = item["checkId"]
                _require(isinstance(identifier, str) and identifier in known,
                         "Observation refers to an unknown quality check.")
                item = {**item, **{k: known[identifier][k] for k in CONTEXT},
                        "productBindingsSha256": context["productBindingsSha256"]}
            _fields(item, {"checkId", *CONTEXT, "observed", "productBindingsSha256"}, "Check observation")
            identifier = item["checkId"]
            _require(isinstance(identifier, str) and identifier in known, "Observation refers to an unknown quality check.")
            _require(identifier not in records, "Duplicate quality check observation.")
            for key in CONTEXT:
                _text(item[key], f"Observation {key}")
            _sha(item["productBindingsSha256"], "Observation source binding")
            _require(isinstance(item["observed"], dict), "Observed results must be an object.")
            records[identifier] = item
    fresh = bool(bindings)
    for ref in bindings:
        _reference(ref, measurement=False)
        _, current = reader(repo, ref)
        fresh = fresh and current
    fingerprint = _digest(bindings)
    result = []
    for check in plan["checks"]:
        item = records.get(check["id"])
        state, detail = "unmeasured", "No concrete observation supplied."
        if item is None and not check["expected"] and check["goalIds"]:
            # No duplicate observation for a purely numeric check. Its goals
            # still independently require raw samples and current bindings.
            state, detail = "passed", "Determined by linked raw numeric goals."
        if item is not None:
            if not fresh or item["productBindingsSha256"] != fingerprint:
                state, detail = "stale", "Observation does not bind current product sources."
            elif any(item[k] != check[k] for k in CONTEXT):
                state, detail = "mismatch", "Observation workload, environment or method differs from the plan."
            else:
                missing = [k for k in check["expected"] if k not in item["observed"]]
                different = [k for k, v in check["expected"].items()
                             if k in item["observed"] and _digest(item["observed"][k]) != _digest(v)]
                if missing or different:
                    state = "failed"
                    detail = "Actual observations differ from frozen expectations."
                    if missing:
                        detail += " Missing observations: " + ", ".join(missing) + "."
                    if different:
                        detail += " Mismatched observations: " + ", ".join(different) + "."
                else:
                    state, detail = "passed", "Current observations match frozen expectations; numeric goals checked separately."
        result.append({"checkId": check["id"], "state": state, "detail": detail})
    return result
