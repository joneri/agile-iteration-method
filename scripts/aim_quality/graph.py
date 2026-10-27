"""Bounded delivery activities derived from the native ledger and local proof.

Receipts are observations, not authenticated agent identities or gate decisions.
Dependency snapshots fence an attempt even after a prerequisite is rerun.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from .delegation import check_delegation, _overlap, _scope
from .files import read_evidence
from .skills import BASE_SKILLS, role_skill_issues

MAX_ATTEMPTS = 8
ROLES = set(BASE_SKILLS)
STATES = ("pending", "ready", "running", "completed", "failed", "stale", "blocked")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(item, required, optional=()):
    _require(isinstance(item, dict), "Activity data must be an object.")
    _require(set(required) <= set(item) <= set(required) | set(optional),
             "Activity data has missing or unsupported fields.")


def _text(value, label, maximum=240):
    _require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
             f"{label} must be bounded nonempty text.")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def validate_execution_plan(plan, stories, repo=None):
    """Require the same bounded ownership DAG plus explicit product assignments."""
    _fields(plan, ("version", "delegationAllowed", "maxWorkers", "activities"), ("parallelBenefit",))
    if "parallelBenefit" in plan:
        _text(plan["parallelBenefit"], "Parallel benefit", 2000)
    assessed = check_delegation(plan)
    _require(assessed["valid"], "Execution plan has incomplete review dependencies.")
    selected = {s["id"] for s in stories}
    for item in plan["activities"]:
        _fields(item, ("id", "title", "kind", "role", "storyIds", "paths", "dependsOn"), ("skills",))
        _text(item["title"], "Activity title")
        _require(item["role"] in ROLES, "Activity role must be po, tdo, dev or reviewer.")
        ids = item["storyIds"]
        _require(isinstance(ids, list) and 1 <= len(ids) <= 256
                 and all(isinstance(x, str) for x in ids) and len(ids) == len(set(ids))
                 and set(ids) <= selected, "Activity Story links must name selected Stories exactly once.")
        skills = item.get("skills", [])
        _require(isinstance(skills, list) and len(skills) <= 16
                 and all(isinstance(x, str) and len(x) <= 128
                         and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", x) for x in skills)
                 and len(skills) == len(set(skills)), "Activity skills must contain bounded actual skill IDs.")
    if repo is not None and any(a.get("skills") for a in plan["activities"]):
        available = {role: {identifier} for role, identifier in BASE_SKILLS.items()}
        profile = Path(repo) / "aim.roles.yaml"
        if profile.exists() or profile.is_symlink():
            from aim_installer.yaml_lite import loads
            data = loads(read_evidence(Path(repo), "aim.roles.yaml").decode("utf-8"))
            roles = data.get("aimProjectRoles", {}).get("roles", {})
            issues = role_skill_issues(Path(repo), data)
            for role in ROLES:
                for binding in roles.get(role, {}).get("skills", []):
                    if (binding.get("status") in {"available", "verified"}
                            and not any(issue.startswith(role + ":") and str(binding.get("id")) in issue for issue in issues)):
                        available[role].add(binding.get("id"))
        for item in plan["activities"]:
            _require(set(item.get("skills", [])) <= available[item["role"]],
                     "Activity names an unavailable or unbound skill ID for its role.")
    return assessed


def _retry_context(delivery, activity_id, records=None):
    """A completed correction ends the failure streak; session changes do not."""
    history = delivery.get('activityReceipts', []) if records is None else records
    attempts = [r for r in history if r['activityId'] == activity_id]
    task = next(a for a in delivery['executionPlan']['activities'] if a['id'] == activity_id)
    latest = {r['activityId']: r for r in history}
    prerequisites = {ident: latest.get(ident) for ident in task['dependsOn']}
    failures = 0
    for record in attempts:
        if record['status'] == 'completed':
            failures = 0
        elif record['status'] == 'failed':
            failures += 1
    return dict(required=failures >= 2, failures=failures,
                contextSha256=_digest(dict(scopeSha256=delivery['scopeSha256'],
                                          activityId=activity_id, attempts=attempts,
                                          prerequisites=prerequisites,
                                          failedWork=[r for r in history if r['status'] == 'failed'])))


def _validate_reassessment(value, context):
    _fields(value, ('contextSha256', 'decision', 'userOutcome', 'resources', 'alternatives', 'boundary'))
    _require(value['contextSha256'] == context['contextSha256'],
             'Diagnostic reassessment context changed; use current attempts and cumulative consequences.')
    _require(value['decision'] in {'continue_bounded', 'owner_decision', 'independent_work'},
             'Invalid diagnostic reassessment decision.')
    for key in ('userOutcome', 'resources', 'alternatives', 'boundary'):
        _text(value[key], 'Reassessment ' + key, 2000)


def validate_activity_receipts(delivery):
    records = delivery.get("activityReceipts", [])
    _require("executionPlan" in delivery or not records, "Activity receipts require an execution plan.")
    if not records:
        return
    tasks = {a["id"]: a for a in delivery["executionPlan"]["activities"]}
    counters = {}
    latest = {}
    for index, record in enumerate(records):
        identifier = record["activityId"]
        if 'reassessment' in record:
            _require(index > 0, 'Reassessment requires prior activity history.')
            _validate_reassessment(record['reassessment'], _retry_context(delivery, identifier, records[:index]))
            _require(record['reassessment']['decision'] == 'continue_bounded',
                     'Only a bounded continuation can have an activity attempt.')
        _require(identifier in tasks, "Receipt refers to an unknown activity.")
        counters[identifier] = counters.get(identifier, 0) + 1
        _require(record["attempt"] == counters[identifier] <= MAX_ATTEMPTS,
                 "Activity attempts must be sequential and bounded.")
        _require(record["scopeSha256"] == delivery["scopeSha256"], "Activity receipt scope mismatch.")
        deps = record["dependencies"]
        _require(len(deps) == len(tasks[identifier]["dependsOn"])
                 and {d["activityId"] for d in deps} == set(tasks[identifier]["dependsOn"]),
                 "Activity receipt dependencies do not match the approved plan.")
        for dep in deps:
            prior = latest.get(dep["activityId"])
            _require(prior is not None and prior["status"] == "completed"
                     and prior["attempt"] == dep["attempt"] and _digest(prior) == dep["receiptSha256"],
                     "Activity dependency snapshot was not a completed receipt at start.")
        if record["status"] == "completed":
            _require(bool(record.get("sourceBindings")) and bool(record.get("evidence")),
                     "Completed activities require source and evidence bindings.")
            _source_scope(tasks[identifier], [ref["path"] for ref in record["sourceBindings"]])
        elif record["status"] == "failed":
            _text(record.get("reason"), "Activity failure reason", 2000)
        latest[identifier] = record


def _source_scope(task, paths):
    _require(isinstance(paths, list) and 1 <= len(paths) <= 128
             and all(isinstance(p, str) for p in paths) and len(paths) == len(set(paths)),
             "Supply 1–128 unique activity source paths.")
    for path in paths:
        _scope(path)
        _require(any(path == scope or path.startswith(scope + "/") for scope in task["paths"]),
                 "Activity source binding is outside its approved ownership paths.")


def _conflict(first, second):
    return "write" in {first["kind"], second["kind"]} and any(
        _overlap(a, b) for a in first["paths"] for b in second["paths"])


def _fresh(repo, refs, cache, check_reference=None):
    for ref in refs:
        path = ref["path"]
        if check_reference is not None:
            try:
                check_reference(ref)
            except (OSError, ValueError):
                return False
            continue
        if path not in cache:
            try:
                cache[path] = hashlib.sha256(read_evidence(Path(repo), path)).hexdigest()
            except (OSError, ValueError):
                cache[path] = None
        if cache[path] != ref["sha256"]:
            return False
    return True


def project_graph(repo, document, store_hash, delivery_id=None, *, check_reference=None):
    """Project all nodes without writes, command execution, launches or acceptance."""
    active = [d for d in document["deliveries"] if d["status"] not in {"accepted", "cancelled"}]
    delivery = (next((d for d in document["deliveries"] if d["id"] == delivery_id), None)
                if delivery_id else active[0] if active else
                next((d for d in reversed(document["deliveries"]) if d["status"] == "accepted"), None))
    result = dict(version=1, available=delivery is not None, configured=False,
                  deliveryId=None, title="Delivery graph", goal="", scopeSha256=None,
                  storeSha256=store_hash, phase=None, activities=[], edges=[], readyIds=[],
                  retryIds=[], recommendedIds=[], runningIds=[], blockers=[], summary={}, stories=[])
    if delivery is None:
        result["blockers"] = ["No delivery is selected."]
        return result
    result.update(deliveryId=delivery["id"], title=delivery["title"], goal=delivery["goal"],
                  scopeSha256=delivery["scopeSha256"], phase=delivery["status"],
                  stories=copy.deepcopy(delivery["stories"]))
    if "executionPlan" not in delivery:
        return _lifecycle(result, delivery)
    plan = delivery["executionPlan"]
    result["configured"] = True
    result["historical"] = delivery["status"] == "accepted"
    result["identityVerified"] = False
    result["reviewIdentityVerified"] = False
    result["speedupVerified"] = False
    tasks = {a["id"]: a for a in plan["activities"]}
    receipts = {r["activityId"]: r for r in delivery.get("activityReceipts", [])}
    nodes, cache = {}, {}
    approved = delivery["status"] == "in_progress" and delivery.get("approval", {}).get("scopeSha256") == delivery["scopeSha256"]
    def node(identifier):
        if identifier in nodes:
            return nodes[identifier]
        task, receipt = tasks[identifier], receipts.get(identifier)
        dependencies = [node(dep) for dep in task["dependsOn"]]
        status, reason = "pending", "Waiting for prerequisite activities."
        obsolete = any(dep["status"] == "stale" for dep in dependencies)
        if receipt:
            snapshot = {d["activityId"]: d for d in receipt["dependencies"]}
            changed = any(dep not in receipts or snapshot[dep]["attempt"] != receipts[dep]["attempt"]
                          or snapshot[dep]["receiptSha256"] != _digest(receipts[dep])
                          for dep in task["dependsOn"])
            obsolete = obsolete or changed or any(dep["status"] != "completed" for dep in dependencies)
            if receipt["status"] == "completed" and not _fresh(
                    repo, receipt["sourceBindings"] + receipt["evidence"], cache, check_reference):
                obsolete = True
            status, reason = receipt["status"], receipt.get("reason", "Recorded activity receipt.")
        if obsolete:
            status, reason = "stale", "Source, proof or prerequisite receipt changed; a new attempt is required."
        elif not receipt:
            if any(dep["status"] in {"failed", "blocked"} for dep in dependencies):
                status, reason = "blocked", "A prerequisite failed or is blocked."
            elif all(dep["status"] == "completed" for dep in dependencies):
                status, reason = "ready", "Prerequisites have current completion evidence."
        if status in {"ready", "pending"} and not approved:
            status, reason = "blocked", "Activity starts require an approved delivery in progress."
        selected_stories = [s for s in delivery["stories"] if s["id"] in task["storyIds"]]
        checks = [check for check in delivery.get("qualityPlan", {}).get("checks", [])
                  if not check.get("criteria") or any(
                      criterion.split("/", 1)[0] in task["storyIds"] for criterion in check["criteria"])]
        assignment = dict(deliveryId=delivery["id"], scopeSha256=delivery["scopeSha256"],
                          activityId=identifier, title=task["title"], goal=delivery["goal"],
                          role=task["role"], skills=task.get("skills", []),
                          skillsToResolve=task.get("skills", []), skillAvailabilityVerified=False,
                          storyIds=task["storyIds"], paths=task["paths"], dependsOn=task["dependsOn"],
                          stories=copy.deepcopy(selected_stories), checks=copy.deepcopy(checks),
                          boundary="Work only in these approved paths; record actual session, attempt and proof. Activity completion does not advance native gates.")
        retry = _retry_context(delivery, identifier)
        reassessment_required = status in {'failed', 'stale'} and retry['required']
        if reassessment_required:
            reason += ' Repeated diagnosis requires benefit/cumulative-resource reassessment before another attempt.'
            assignment['diagnosticReassessment'] = dict(contextSha256=retry['contextSha256'],
                instruction='Relate this technical goal to the approved user outcome; assess cumulative spent/unknown resources across sessions, uncertainty, alternatives and one bounded next action. Preserve quality and actual authority. Use an existing owner/block decision if a tradeoff needs it; independent ready work can continue.')
        value = {**copy.deepcopy(task), "skills": task.get("skills", []), "status": status,
                 "reassessmentRequired": reassessment_required,
                 "retryContextSha256": retry['contextSha256'], "diagnosticFailures": retry['failures'],
                 "reason": reason, "evidence": copy.deepcopy(receipt.get("evidence", [])) if receipt else [],
                 "session": receipt["session"] if receipt else None,
                 "attempt": receipt["attempt"] if receipt else None,
                 "sourceBindings": copy.deepcopy(receipt.get("sourceBindings", [])) if receipt else [],
                 "layer": max((dep["layer"] + 1 for dep in dependencies), default=0),
                 "assignment": assignment}
        nodes[identifier] = value
        return value
    result["activities"] = [node(identifier) for identifier in tasks]
    result["edges"] = [{"from": dep, "to": a["id"]} for a in plan["activities"] for dep in a["dependsOn"]]
    result["readyIds"] = [a["id"] for a in result["activities"] if a["status"] == "ready"]
    result["retryIds"] = [a["id"] for a in result["activities"]
                          if approved and a["status"] in {"failed", "stale"}
                          and not a['reassessmentRequired']
                          and receipts.get(a["id"], {}).get("attempt", 0) < MAX_ATTEMPTS
                          and all(nodes[dep]["status"] == "completed" for dep in a["dependsOn"])]
    # A stale running receipt may still own files. It continues to consume a
    # slot until explicitly restarted or failed; projected staleness is no lease.
    running = [identifier for identifier, r in receipts.items() if r["status"] == "running"]
    result["runningIds"] = running
    capacity = plan["maxWorkers"] if plan["delegationAllowed"] else 1
    chosen = []
    for identifier in result["retryIds"] + result["readyIds"]:
        occupied = set(running + chosen) - {identifier}
        if len(occupied) < capacity and not any(_conflict(tasks[identifier], tasks[other]) for other in occupied):
            chosen.append(identifier)
    result["recommendedIds"] = chosen
    result["blockers"] = [{"activityId": a["id"], "status": a["status"], "reason": a["reason"]}
                          for a in result["activities"] if a["status"] in {"failed", "blocked", "stale"}]
    result["summary"] = {state: sum(a["status"] == state for a in result["activities"]) for state in STATES}
    return result


def _lifecycle(result, delivery):
    """Honest fallback: lifecycle evidence, never fabricated implementation work."""
    phases = ("planned", "in_progress", "review", "validation", "acceptance", "accepted")
    labels = ("Approve scope", "Implement Stories", "Review delivery", "Validate Stories", "User acceptance", "Accepted delivery")
    phase = delivery.get("blockedFrom", delivery["status"])
    current = phases.index(phase) if phase in phases else -1
    for i, (identifier, title) in enumerate(zip(phases, labels)):
        status = "completed" if i < current else "blocked" if delivery["status"] == "blocked" and i == current else "running" if i == current else "pending"
        if phase == "accepted":
            status = "completed"
        result["activities"].append(dict(id="lifecycle-" + identifier, title=title, kind="lifecycle",
            role=None, skills=[], storyIds=[s["id"] for s in delivery["stories"]], paths=[],
            dependsOn=[] if i == 0 else ["lifecycle-" + phases[i-1]], status=status,
            reason="Native delivery lifecycle; no execution activities were configured.",
            evidence=[], session=None, attempt=None, layer=i, assignment=None))
    result["edges"] = [{"from": "lifecycle-" + phases[i-1], "to": "lifecycle-" + phases[i]} for i in range(1, len(phases))]
    result["summary"] = {state: sum(a["status"] == state for a in result["activities"]) for state in STATES}
    return result


def change_activity(repo, delivery, request, *, bind_sources, bind_evidence, at, check_reference=None):
    _fields(request, ("deliveryId", "activityId", "status", "session"),
            ("attempt", "sourcePaths", "evidence", "reason", "reassessment"))
    _require(delivery["status"] == "in_progress" and delivery.get("approval", {}).get("scopeSha256") == delivery["scopeSha256"],
             "Activity changes require an approved delivery in progress.")
    _require("executionPlan" in delivery, "Delivery has no approved execution plan.")
    _text(request["session"], "Actual session", 128)
    _require(request["status"] in {"running", "completed", "failed"}, "Activity status must be running, completed or failed.")
    task = next((a for a in delivery["executionPlan"]["activities"] if a["id"] == request["activityId"]), None)
    _require(task is not None, "Unknown activity ID.")
    graph = project_graph(repo, {"deliveries": [delivery]}, None, check_reference=check_reference)
    state = next(a for a in graph["activities"] if a["id"] == task["id"])
    records = delivery.setdefault("activityReceipts", [])
    latest = {r["activityId"]: r for r in records}
    previous = latest.get(task["id"])
    if request["status"] == "running":
        validate_execution_plan(delivery["executionPlan"], delivery["stories"], repo)
        _require(not any(k in request for k in ("attempt", "sourcePaths", "evidence", "reason")), "Starting an activity creates its attempt; do not supply outcome fields.")
        _require(previous is None or state["status"] in {"failed", "stale"}, "Activity already has a current attempt.")
        _require(all(next(a for a in graph["activities"] if a["id"] == dep)["status"] == "completed" for dep in task["dependsOn"]),
                 "Activity prerequisites are not currently completed.")
        running = [identifier for identifier, record in latest.items()
                   if record["status"] == "running" and identifier != task["id"]]
        plan = delivery["executionPlan"]
        _require(len(running) < (plan["maxWorkers"] if plan["delegationAllowed"] else 1), "Activity worker capacity is exhausted.")
        tasks = {a["id"]: a for a in plan["activities"]}
        _require(not any(_conflict(task, tasks[other]) for other in running), "Activity ownership overlaps running work.")
        retry = _retry_context(delivery, task['id'])
        if retry['required'] or 'reassessment' in request:
            _require(previous is not None and 'reassessment' in request,
                     'Repeated diagnostic failure requires a current benefit/resource reassessment before retry.')
            _validate_reassessment(request['reassessment'], retry)
            _require(request['reassessment']['decision'] == 'continue_bounded',
                     'Use an actual owner decision or independent work; this assessment does not authorize another retry.')
        attempt = previous["attempt"] + 1 if previous else 1
        _require(attempt <= MAX_ATTEMPTS, "Activity attempt history is full; retain evidence and plan a new delivery.")
        records.append(dict(activityId=task["id"], session=request["session"], attempt=attempt,
                            status="running", at=at, updatedAt=at, scopeSha256=delivery["scopeSha256"],
                            dependencies=[dict(activityId=dep, attempt=latest[dep]["attempt"],
                                               receiptSha256=_digest(latest[dep])) for dep in task["dependsOn"]]))
        if 'reassessment' in request:
            records[-1]['reassessment'] = copy.deepcopy(request['reassessment'])
        return
    _require('reassessment' not in request, 'Reassessment belongs to the new attempt, not its outcome.')
    _require(previous is not None and previous["status"] == "running", "Activity has no running attempt.")
    _require(type(request.get("attempt")) is int and request["attempt"] == previous["attempt"]
             and request["session"] == previous["session"], "Activity session or attempt is stale.")
    if request["status"] == "completed":
        _require("reason" not in request, "Completed activity does not take a failure reason.")
        _require(state["status"] == "running", "Activity inputs changed since start; restart the stale attempt.")
        _source_scope(task, request.get("sourcePaths"))
        previous["sourceBindings"] = bind_sources(request["sourcePaths"])
        previous["evidence"] = bind_evidence(request.get("evidence"))
    else:
        _require("sourcePaths" not in request and "evidence" not in request, "Failed activity takes a reason, not completion bindings.")
        _text(request.get("reason"), "Activity failure reason", 2000)
        previous["reason"] = request["reason"]
    previous.update(status=request["status"], updatedAt=at)
