# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/orchestration.py
"""Pure, bounded AIM 4.8 orchestration planning and campaign assessment.

Version 1 documents are declarative only: they validate a coordinator binding
and proposed work, but never launch agents, grant authority, mutate a ledger,
or infer acceptance. Campaign history is supplied by the caller and keyed by
the stable outcome ID, so graph/activity renames and session changes do not
reset observed progress.
"""
from __future__ import annotations

import copy
import math
import re

from .delegation import _scope, check_delegation

VERSION = 1
PATTERNS = {
    "cohesive_delivery",
    "maintenance_repair",
    "independent_branches",
    "bounded_investigation",
}
ROLES = {"po", "tdo", "dev", "reviewer"}
DECISIONS = {
    "continue_bounded", "independent_work", "change_baseline",
    "request_owner_choice", "reprioritize",
}
OBSERVATION_KINDS = {
    "baseline", "integrated_progress", "component_pass", "activity",
    "heartbeat", "falsifier", "crash", "freeze", "review",
}
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
MAX_CAMPAIGN_OBSERVATIONS = 512


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _text(value, label, limit=2000):
    _need(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
          f"{label} must be bounded nonempty text.")


def _id(value, label):
    _need(isinstance(value, str) and ID_RE.fullmatch(value) is not None,
          f"{label} must be a bounded stable identifier.")


def _text_list(value, label, *, minimum=1, maximum=32):
    _need(isinstance(value, list) and minimum <= len(value) <= maximum,
          f"{label} must contain {minimum} to {maximum} items.")
    for item in value:
        _text(item, label + " item")
    return value


def _id_list(value, label, *, minimum=1, maximum=256):
    _need(isinstance(value, list) and minimum <= len(value) <= maximum,
          f"{label} must contain {minimum} to {maximum} IDs.")
    for item in value:
        _id(item, label + " item")
    _need(len(value) == len(set(value)), f"{label} must be unique.")
    return value


def _fields(value, required, optional=(), label="Document"):
    _need(isinstance(value, dict), f"{label} must be an object.")
    _need(set(required) <= set(value) <= set(required) | set(optional),
          f"{label} has missing or unsupported fields.")


def _outcomes(value):
    _need(isinstance(value, list) and 1 <= len(value) <= 32,
          "Outcomes must contain 1 to 32 items.")
    seen = set()
    normalized = []
    for outcome in value:
        _fields(outcome, ("id", "requirement", "paths"), label="Outcome")
        _id(outcome["id"], "Outcome ID")
        _need(outcome["id"] not in seen, "Outcome IDs must be unique.")
        seen.add(outcome["id"])
        _text(outcome["requirement"], "Outcome requirement")
        paths = outcome["paths"]
        _need(isinstance(paths, list) and 1 <= len(paths) <= 128,
              "Each outcome needs 1 to 128 literal paths.")
        for path in paths:
            _scope(path)
        _need(len(paths) == len(set(paths)), "Outcome paths must be unique.")
        normalized.append(copy.deepcopy(outcome))
    return normalized


def _coordinator(value):
    _fields(value, ("session", "capability", "permittedDecisions"), label="Coordinator binding")
    _text(value["session"], "Coordinator session", 256)
    capability = value["capability"]
    _fields(capability, ("id", "version"), label="Coordinator capability")
    _id(capability["id"], "Capability ID")
    _text(capability["version"], "Capability version", 64)
    decisions = value["permittedDecisions"]
    _need(isinstance(decisions, list) and len(decisions) <= len(DECISIONS),
          "Permitted decisions must be a bounded list.")
    _need(all(isinstance(item, str) and item in DECISIONS for item in decisions)
          and len(decisions) == len(set(decisions)),
          "Permitted decisions contain an unsupported or duplicate decision.")


def _policy(value):
    _fields(value, ("delegationAllowed", "maxWorkers", "checkpointAttemptBudget"),
            ("parallelBenefit", "noProgressLimit"), "Policy")
    _need(type(value["delegationAllowed"]) is bool, "delegationAllowed must be boolean.")
    _need(type(value["maxWorkers"]) is int and 1 <= value["maxWorkers"] <= 8,
          "maxWorkers must be an integer from 1 to 8.")
    _need(type(value["checkpointAttemptBudget"]) is int
          and 1 <= value["checkpointAttemptBudget"] <= 8,
          "checkpointAttemptBudget must be an integer from 1 to 8.")
    if "noProgressLimit" in value:
        _need(type(value["noProgressLimit"]) is int and 1 <= value["noProgressLimit"] <= value["checkpointAttemptBudget"],
              "noProgressLimit must be a positive integer within the checkpoint budget.")
    if "parallelBenefit" in value:
        _text(value.get("parallelBenefit"), "Parallel benefit")
    elif value["maxWorkers"] > 1:
        _need(False, "Parallel benefit is required when maxWorkers exceeds one.")


def _node(identifier, kind, role, paths, depends, outcome_ids, inputs, outputs, proofs):
    return {
        "id": identifier,
        "kind": kind,
        "role": role,
        "paths": list(paths),
        "dependsOn": list(depends),
        "outcomeIds": list(outcome_ids),
        "inputs": list(inputs),
        "outputs": list(outputs),
        "proofExpectations": list(proofs),
    }


def construct_default_graph(pattern, outcomes, coordinator, policy):
    """Construct one declarative default graph from explicit outcome scope."""
    _need(isinstance(pattern, str) and pattern in PATTERNS, "Unknown default graph pattern.")
    outcomes = _outcomes(outcomes)
    _coordinator(coordinator)
    _policy(policy)
    ids = [item["id"] for item in outcomes]
    all_paths = list(dict.fromkeys(path for item in outcomes for path in item["paths"]))
    _need(len(all_paths) <= 128, "A default graph may own at most 128 distinct literal paths.")
    nodes = []
    if pattern == "independent_branches":
        _need(len(outcomes) <= 31, "Independent branches allow at most 31 outcomes plus integration review.")
        for index, outcome in enumerate(outcomes, start=1):
            nodes.append(_node(
                "branch-" + str(index), "write", "dev", outcome["paths"], [],
                [outcome["id"]], ["Frozen requirement for outcome " + outcome["id"]],
                ["Candidate change for outcome " + outcome["id"]],
                ["Outcome-specific component evidence; does not establish integration."],
            ))
        deps = [node["id"] for node in nodes]
        nodes.append(_node(
            "integrate-review", "review", "reviewer", all_paths, deps, ids,
            ["All branch outputs and frozen original requirements"],
            ["Integrated outcome assessment"],
            ["Run the original end-to-end expectations across selected outcomes."],
        ))
    elif pattern == "maintenance_repair":
        nodes.extend([
            _node("diagnose", "read", "dev", all_paths, [], ids,
                  ["Original requirements", "Current behavior in explicit outcome paths"],
                  ["Reproducible failure evidence"],
                  ["Record a concrete reproducer or falsifier before repair."]),
            _node("repair", "write", "dev", all_paths, ["diagnose"], ids,
                  ["Reproducible failure evidence", "Frozen requirements"],
                  ["Targeted repair candidate"],
                  ["Run the targeted regression check for each changed outcome."]),
            _node("integrate-review", "review", "reviewer", all_paths, ["repair"], ids,
                  ["Repair candidate and original requirements"],
                  ["Integrated outcome assessment"],
                  ["Recheck the original integrated behavior and regressions."]),
        ])
    elif pattern == "bounded_investigation":
        nodes.extend([
            _node("investigate", "read", "dev", all_paths, [], ids,
                  ["Original requirements", "Latest usable baseline"],
                  ["Bounded hypothesis and discriminating test"],
                  ["A falsifiable result that changes the next diagnostic choice."]),
            _node("bounded-change", "write", "dev", all_paths, ["investigate"], ids,
                  ["Bounded hypothesis", "Explicit outcome paths"],
                  ["One bounded change"],
                  ["Run a comparable integrated check against the named baseline."]),
            _node("integrate-review", "review", "reviewer", all_paths, ["bounded-change"], ids,
                  ["Bounded change and original requirements"],
                  ["Integrated outcome assessment"],
                  ["Recheck original outcomes; activity and component passes do not count as integration."]),
        ])
    else:
        nodes.extend([
            _node("implement", "write", "dev", all_paths, [], ids,
                  ["All frozen outcome requirements"],
                  ["Cohesive implementation candidate"],
                  ["Outcome-specific component evidence, followed by integrated verification."]),
            _node("integrate-review", "review", "reviewer", all_paths, ["implement"], ids,
                  ["Implementation candidate and original requirements"],
                  ["Integrated outcome assessment"],
                  ["Run the original end-to-end expectations across selected outcomes."]),
        ])
    graph = {
        "version": VERSION,
        "origin": {"kind": "default", "template": pattern},
        "coordinator": copy.deepcopy(coordinator),
        "policy": copy.deepcopy(policy),
        "outcomes": outcomes,
        "nodes": nodes,
        "execution": {"launchesAgents": False, "grantsAuthority": False},
    }
    return validate_graph(graph)


def validate_graph(graph):
    """Validate a v1 graph and return a deep copy without rewriting its origin."""
    _fields(graph, ("version", "origin", "coordinator", "policy", "outcomes", "nodes", "execution"),
            label="Orchestration graph")
    _need(type(graph["version"]) is int and graph["version"] == VERSION,
          "Orchestration graph version must be 1.")
    origin = graph["origin"]
    _need(isinstance(origin, dict) and isinstance(origin.get("kind"), str)
          and origin["kind"] in {"default", "custom"},
          "Graph origin must identify a default or custom graph.")
    if origin["kind"] == "default":
        _fields(origin, ("kind", "template"), label="Default graph origin")
        _need(isinstance(origin["template"], str) and origin["template"] in PATTERNS,
              "Graph origin names an unknown default template.")
    else:
        _fields(origin, ("kind", "reference"), label="Custom graph origin")
        _text(origin["reference"], "Custom graph reference", 256)
    _coordinator(graph["coordinator"])
    _policy(graph["policy"])
    outcomes = _outcomes(graph["outcomes"])
    by_id = {item["id"]: item for item in outcomes}
    execution = graph["execution"]
    _fields(execution, ("launchesAgents", "grantsAuthority"), label="Execution boundary")
    _need(execution["launchesAgents"] is False and execution["grantsAuthority"] is False,
          "The orchestration kernel cannot launch agents or grant authority.")
    _need(isinstance(graph["nodes"], list) and 1 <= len(graph["nodes"]) <= 32,
          "Graph nodes must contain 1 to 32 activities.")
    covered = set()
    dag_nodes = []
    for node in graph["nodes"]:
        _fields(node, ("id", "kind", "role", "paths", "dependsOn", "outcomeIds",
                       "inputs", "outputs", "proofExpectations"), label="Graph node")
        _id(node["id"], "Node ID")
        _need(isinstance(node["kind"], str) and node["kind"] in {"read", "write", "review"},
              "Node kind must be read, write or review.")
        _need(isinstance(node["role"], str) and node["role"] in ROLES,
              "Node role must be po, tdo, dev or reviewer.")
        paths = node["paths"]
        _need(isinstance(paths, list) and 1 <= len(paths) <= 128, "Each node needs literal ownership paths.")
        for path in paths:
            _scope(path)
        _need(len(paths) == len(set(paths)), "Node paths must be unique.")
        outcome_ids = _id_list(node["outcomeIds"], "Node outcomeIds", maximum=32)
        _need(set(outcome_ids) <= set(by_id), "Node refers to an unknown outcome.")
        covered.update(outcome_ids)
        allowed_paths = [path for outcome_id in outcome_ids for path in by_id[outcome_id]["paths"]]
        _need(all(any(path == scope or path.startswith(scope + "/") for scope in allowed_paths)
                  for path in paths), "Node ownership path exceeds its linked outcome paths.")
        _id_list(node["dependsOn"], "Node dependencies", minimum=0, maximum=32)
        _text_list(node["inputs"], "Node inputs")
        _text_list(node["outputs"], "Node outputs")
        _text_list(node["proofExpectations"], "Proof expectations")
        dag_nodes.append({"id": node["id"], "kind": node["kind"], "paths": paths,
                          "dependsOn": node["dependsOn"]})
    _need(covered == set(by_id), "Every explicit outcome must be linked to at least one graph node.")
    delegation = {"version": 1, "delegationAllowed": graph["policy"]["delegationAllowed"],
                  "maxWorkers": graph["policy"]["maxWorkers"], "activities": dag_nodes}
    if "parallelBenefit" in graph["policy"]:
        delegation["parallelBenefit"] = graph["policy"]["parallelBenefit"]
    check = check_delegation(delegation)
    _need(check["valid"], "Final review nodes must depend on every overlapping writer.")
    return copy.deepcopy(graph)


def _campaign_fields(campaign):
    _fields(campaign, ("version", "outcomeId", "attemptBudget", "waitingOriginalGoals", "observations"),
            ("ownerPriority", "independentReady", "noProgressLimit"), "Campaign")
    _need(type(campaign["version"]) is int and campaign["version"] == VERSION,
          "Campaign version must be 1.")
    _id(campaign["outcomeId"], "Campaign outcomeId")
    _need(type(campaign["attemptBudget"]) is int and 1 <= campaign["attemptBudget"] <= 8,
          "Campaign attemptBudget must be an integer from 1 to 8.")
    if "noProgressLimit" in campaign:
        _need(type(campaign["noProgressLimit"]) is int
              and 1 <= campaign["noProgressLimit"] <= MAX_CAMPAIGN_OBSERVATIONS,
              "Campaign noProgressLimit must be a bounded positive integer.")
    _id_list(campaign["waitingOriginalGoals"], "waitingOriginalGoals", minimum=0)
    for field in ("ownerPriority", "independentReady"):
        if field in campaign:
            _id_list(campaign[field], field, minimum=0)
    observations = campaign["observations"]
    _need(isinstance(observations, list) and len(observations) <= MAX_CAMPAIGN_OBSERVATIONS,
          "Campaign observations must be a bounded chronological list.")


def _number(value, label):
    _need(type(value) in (int, float) and abs(value) <= 1e300 and math.isfinite(value),
          f"{label} must be a finite bounded number.")


def _validate_observation(item, outcome_id, previous_attempt):
    base = {"outcomeId", "kind", "session", "attempt"}
    metadata = {"activityId", "graphRevision"}
    optional = {"resourceDelta", "baselineId", "comparisonKey", "metric", "direction",
                "value", "usable", "informationGain"} | metadata
    _fields(item, base, optional, "Observation")
    _need(item["outcomeId"] == outcome_id, "Observation outcomeId does not match stable campaign identity.")
    _need(isinstance(item["kind"], str) and item["kind"] in OBSERVATION_KINDS,
          "Unsupported observation kind.")
    _text(item["session"], "Observation session", 256)
    if "activityId" in item:
        _id(item["activityId"], "Observation activityId")
    if "graphRevision" in item:
        _text(item["graphRevision"], "Observation graphRevision", 128)
    attempt = item["attempt"]
    _need(type(attempt) is int and 0 <= attempt <= 128 and attempt >= previous_attempt,
          "Observation attempts must be chronological nonnegative integers.")
    if item["kind"] in {"integrated_progress", "component_pass", "activity", "falsifier", "crash", "freeze"}:
        _need(attempt > 0, "Work observations require a positive attempt number.")
    if item["kind"] == "baseline":
        _fields(item, base | {"baselineId", "comparisonKey", "metric", "direction", "value", "usable"},
                {"resourceDelta"} | metadata, "Baseline observation")
        _need(type(item["usable"]) is bool, "Baseline usable must be boolean.")
    elif item["kind"] == "integrated_progress":
        _fields(item, base | {"baselineId", "comparisonKey", "metric", "direction", "value"},
                {"resourceDelta"} | metadata, "Integrated progress observation")
        _need(attempt > 0, "Integrated progress requires a work attempt.")
    elif item["kind"] == "falsifier":
        _fields(item, base | {"informationGain"}, {"resourceDelta"} | metadata, "Falsifier observation")
        _need(type(item["informationGain"]) is bool, "Falsifier informationGain must be boolean.")
    elif item["kind"] != "baseline":
        _fields(item, base, {"resourceDelta"} | metadata, "Activity observation")
    if item["kind"] in {"baseline", "integrated_progress"}:
        _id(item["baselineId"], "Baseline ID")
        _text(item["comparisonKey"], "Comparison key", 256)
        _id(item["metric"], "Metric ID")
        _need(isinstance(item["direction"], str) and item["direction"] in {"higher", "lower"},
              "Metric direction must be higher or lower.")
        _number(item["value"], "Metric value")
    delta = item.get("resourceDelta", {})
    _need(isinstance(delta, dict) and len(delta) <= 16, "resourceDelta must be a bounded object.")
    for unit, amount in delta.items():
        _id(unit, "Resource unit")
        if amount is not None:
            _number(amount, "Resource delta")
            _need(amount >= 0, "Resource deltas cannot be negative.")
    return attempt


def _better(value, baseline_value, direction):
    return value > baseline_value if direction == "higher" else value < baseline_value


def assess_campaign(campaign):
    """Return a concrete continuation recommendation without changing authority.

    Observation list order is the chronology. Only a numerically better
    integrated measurement against the latest usable, same-identity best value
    can reset the no-progress streak and active checkpoint budget. Work is
    counted by distinct attempt number; heartbeat observations are metadata.
    """
    _campaign_fields(campaign)
    outcome_id = campaign["outcomeId"]
    baselines = {}
    latest_baseline = None
    best_values = {}
    last_best_key = None
    no_progress = 0
    attempts_since_improvement = 0
    total_attempts = 0
    work_attempts = set()
    review_attempts = set()
    last_observed_attempt = 0
    active_blocking_failure = None
    blocking_failure_history = []
    information_gain_pending = False
    information_gain_attempt = None
    totals = {}
    unknown_units = set()
    resource_coverage = True
    for item in campaign["observations"]:
        previous_attempt = last_observed_attempt
        attempt = _validate_observation(item, outcome_id, previous_attempt)
        last_observed_attempt = attempt
        if not item.get("resourceDelta"):
            resource_coverage = False
        for unit, amount in item.get("resourceDelta", {}).items():
            if amount is None:
                unknown_units.add(unit)
            else:
                totals[unit] = totals.get(unit, 0) + amount
        kind = item["kind"]
        if kind == "review":
            review_attempts.add(attempt)
        if kind in {"integrated_progress", "component_pass", "activity", "falsifier", "crash", "freeze"}:
            if attempt not in work_attempts and attempt not in review_attempts:
                if information_gain_pending and attempt != information_gain_attempt:
                    information_gain_pending = False
                work_attempts.add(attempt)
                total_attempts += 1
                attempts_since_improvement += 1
                no_progress += 1
        if kind == "baseline":
            baseline_id = item["baselineId"]
            _need(baseline_id not in baselines, "A baseline ID cannot be reused across graph revisions.")
            baseline = {key: copy.deepcopy(item[key]) for key in
                        ("baselineId", "comparisonKey", "metric", "direction", "value", "usable")}
            baselines[baseline_id] = baseline
            if baseline["usable"]:
                latest_baseline = baseline
                key = (baseline["comparisonKey"], baseline["metric"], baseline["direction"])
                _need(not best_values or key in best_values,
                      "Measurement meaning cannot change within one campaign; retain original comparison contract.")
                best_values.setdefault(key, baseline["value"])
                last_best_key = key
            continue
        if kind == "integrated_progress":
            key = (item["comparisonKey"], item["metric"], item["direction"])
            baseline = baselines.get(item["baselineId"])
            valid_comparison = bool(
                latest_baseline is not None
                and latest_baseline["baselineId"] == item["baselineId"]
                and baseline is not None and baseline["usable"]
                and baseline["comparisonKey"] == item["comparisonKey"]
                and baseline["metric"] == item["metric"]
                and baseline["direction"] == item["direction"]
            )
            best_value = best_values.get(key, baseline["value"] if baseline else None)
            improved = (valid_comparison and best_value is not None
                        and _better(item["value"], best_value, item["direction"])
                        and _better(item["value"], baseline["value"], item["direction"]))
            if improved:
                best_values[key] = item["value"]
                last_best_key = key
                no_progress = 0
                attempts_since_improvement = 0
                information_gain_pending = False
                information_gain_attempt = None
                active_blocking_failure = None
            elif valid_comparison:
                _need(not best_values or key in best_values,
                      "Measurement meaning cannot change within one campaign; retain original comparison contract.")
                best_values.setdefault(key, baseline["value"])
                last_best_key = key
        if kind == "falsifier" and item["informationGain"]:
            information_gain_pending = True
            information_gain_attempt = attempt
        if kind in {"crash", "freeze"}:
            active_blocking_failure = {"kind": kind, "attempt": attempt, "session": item["session"]}
            if "activityId" in item:
                active_blocking_failure["activityId"] = item["activityId"]
            if "graphRevision" in item:
                active_blocking_failure["graphRevision"] = item["graphRevision"]
            blocking_failure_history.append(copy.deepcopy(active_blocking_failure))

    budget = campaign["attemptBudget"]
    no_progress_limit = campaign.get("noProgressLimit", budget)
    exhausted = attempts_since_improvement >= budget
    priorities = campaign.get("ownerPriority", [])
    waiting = campaign["waitingOriginalGoals"]
    independent = campaign.get("independentReady", [])
    _need(set(priorities) <= set(waiting), "ownerPriority must preserve IDs in waitingOriginalGoals.")
    _need(set(independent) <= set(waiting), "independentReady must name waiting original goals.")
    target = outcome_id
    action = "continue_original_outcome"
    reason = "Continue the frozen original outcome; no acceptance is inferred from activity evidence."
    next_step = "Run the next bounded check that can produce comparable integrated evidence."
    if priorities and priorities[0] != outcome_id:
        target = priorities[0]
        action = "work_owner_priority_first"
        reason = "The frozen owner priority list puts another waiting outcome first; preserve that order."
        next_step = "Continue the explicitly first waiting outcome before this one."
    elif exhausted:
        if independent:
            target = independent[0]
            action = "work_independent_ready"
            reason = ("The checkpoint attempt budget is exhausted for this outcome. Continue independent "
                      "ready work without retrying this same diagnostic action.")
            next_step = "Work the first explicitly independent ready original goal."
        else:
            action = "request_owner_choice"
            reason = ("The checkpoint attempt budget is exhausted. A changed action is required; choose a "
                      "new baseline, independent work, or an owner-directed reprioritization.")
            next_step = "Ask the owner to choose a changed action before another attempt on this outcome."
    elif active_blocking_failure:
        failure_kind = active_blocking_failure["kind"]
        action = "debug_blocking_failure"
        reason = (f"A recorded {failure_kind} is a real blocking failure, not cosmetic activity; "
                  "one bounded diagnostic step remains available.")
        next_step = "Reproduce the blocking failure and change one controlled factor within the budget."
    elif no_progress >= no_progress_limit:
        if information_gain_pending:
            action = "continue_bounded_debugging"
            reason = ("A bounded falsifier produced explicit information gain on the current attempt; "
                      "continue one controlled diagnostic step without resetting the no-progress streak.")
            next_step = "Use that falsifier to choose one discriminating follow-up within the remaining budget."
        elif independent:
            target = independent[0]
            action = "work_independent_ready"
            reason = "Repeated local activity has not improved integrated behavior; make progress on independent ready work."
            next_step = "Work the first explicitly independent ready original goal."
        else:
            action = "change_diagnostic_action"
            reason = "Repeated activity, component passes, or heartbeats have not improved integrated behavior."
            next_step = "Change the baseline or diagnostic method before repeating the same work."
    elif information_gain_pending:
        action = "continue_bounded_debugging"
        reason = "A bounded falsifier produced explicit information gain; one justified diagnostic step remains."
        next_step = "Use the falsifier to select one discriminating follow-up within the existing budget."
    resources = {"knownTotals": totals, "unknownUnits": sorted(unknown_units),
                 "coverage": "partial_or_unavailable" if not resource_coverage or unknown_units else "reported_only",
                 "cumulativeAcrossSessions": True}
    best_values_list = [
        {"comparisonKey": key[0], "metric": key[1],
         "direction": key[2], "value": value}
        for key, value in best_values.items()
    ]
    best_value = next((item for item in best_values_list
                       if last_best_key is not None
                       and (item["comparisonKey"], item["metric"], item["direction"])
                       == last_best_key), None)
    return {
        "version": VERSION,
        "outcomeId": outcome_id,
        "recommendation": {"action": action, "targetOutcomeId": target,
                           "nextStep": next_step, "why": reason},
        "attemptsUsed": attempts_since_improvement,
        "attemptsSinceImprovement": attempts_since_improvement,
        "totalAttempts": total_attempts,
        "attemptBudget": budget,
        "budgetExhausted": exhausted,
        "noProgressStreak": no_progress,
        "noProgressLimit": no_progress_limit,
        "latestUsableBaseline": copy.deepcopy(latest_baseline),
        "bestValue": copy.deepcopy(best_value),
        "bestValues": best_values_list,
        "activeBlockingFailure": copy.deepcopy(active_blocking_failure),
        "blockingFailureHistory": blocking_failure_history,
        "resources": resources,
        "waitingOriginalGoals": list(waiting),
        "acceptanceInferred": False,
        "authorityGranted": False,
    }
