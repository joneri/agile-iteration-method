# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/delegation.py
"""Check bounded agent ownership and schedule a proposed dependency graph.

This helper validates a coordinator's plan; it neither launches agents nor
predicts speedup. Paths are lexical ownership scopes, not filesystem authority.
Input v1: maxWorkers (1..8), delegationAllowed (bool), parallelBenefit (text
when >1 worker), activities (1..32 objects: id, kind read/write/review,
paths (nonempty literal scopes), dependsOn (ids)). Only write activities own
write scopes. A final review depends transitively on every relevant writer.
The caller decides materiality and actual host permissions. Higher-priority
host/user constraints always apply, even when a supplied plan says allowed.
"""
from __future__ import annotations

from pathlib import PurePosixPath


def _scope(value):
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError('ownership scopes must be nonempty bounded paths')
    p = PurePosixPath(value)
    if (p.is_absolute() or '..' in p.parts or str(p) != value or value == '.'
            or '\\' in value or ':' in value or any(c in value for c in '*?[]\x00')):
        raise ValueError('ownership scopes must be literal contained canonical paths')
    return value


def _overlap(a, b):
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


def check_delegation(document: dict) -> dict:
    if not isinstance(document, dict) or type(document.get('version')) is not int or document['version'] != 1:
        raise ValueError('delegation plan version must be 1')
    workers = document.get('maxWorkers')
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError('maxWorkers must be an integer from 1 to 8')
    allowed = document.get('delegationAllowed')
    if type(allowed) is not bool:
        raise ValueError('delegationAllowed must reflect actual host/user policy')
    if workers > 1 and (not isinstance(document.get('parallelBenefit'), str)
                        or not document['parallelBenefit'].strip()):
        raise ValueError('parallel work requires a concrete expected benefit')
    activities = document.get('activities')
    if not isinstance(activities, list) or not 1 <= len(activities) <= 32:
        raise ValueError('activities must contain 1 to 32 items')
    tasks = {}
    for item in activities:
        if not isinstance(item, dict):
            raise ValueError('each activity must be an object')
        identifier = item.get('id')
        if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 128 or identifier in tasks:
            raise ValueError('activity ids must be unique nonempty bounded strings')
        if not isinstance(item.get('kind'), str) or item['kind'] not in {'read', 'write', 'review'}:
            raise ValueError('activity kind must be read, write or review')
        paths = item.get('paths')
        if not isinstance(paths, list) or not 1 <= len(paths) <= 128:
            raise ValueError('each activity needs 1 to 128 ownership scopes')
        paths = [_scope(p) for p in paths]
        if len(set(paths)) != len(paths):
            raise ValueError('duplicate ownership scope')
        deps = item.get('dependsOn')
        if not isinstance(deps, list) or len(deps) > 32 or any(not isinstance(x, str) for x in deps) or len(set(deps)) != len(deps):
            raise ValueError('dependsOn must contain unique activity ids')
        if item['kind'] == 'write' and any((p == '.aim' or p.startswith('.aim/')) and not (p == '.aim/analysis' or p.startswith('.aim/analysis/')) for p in paths):
            raise ValueError('only the coordinator owns AIM runtime outside scoped analysis output')
        tasks[identifier] = dict(item, paths=paths, dependsOn=deps)
    for identifier, item in tasks.items():
        if identifier in item['dependsOn'] or any(x not in tasks for x in item['dependsOn']):
            raise ValueError('self or unknown dependency')
    visiting, closure = set(), {}
    def ancestors(identifier):
        if identifier in visiting:
            raise ValueError('dependency cycle')
        if identifier not in closure:
            visiting.add(identifier)
            closure[identifier] = set()
            for dep in tasks[identifier]['dependsOn']:
                closure[identifier].add(dep)
                closure[identifier].update(ancestors(dep))
            visiting.remove(identifier)
        return closure[identifier]
    for identifier in tasks:
        ancestors(identifier)
    diagnostics = []
    for identifier, item in tasks.items():
        if item['kind'] != 'review':
            continue
        for writer, candidate in tasks.items():
            if candidate['kind'] == 'write' and any(_overlap(a, b) for a in item['paths'] for b in candidate['paths']) and writer not in closure[identifier]:
                diagnostics.append({'activity': identifier, 'writer': writer,
                                    'error': 'final review must depend on every writer in its scope'})
    # Writes conflict with reads as well as other writes; reviewers must see a stable snapshot.
    def conflict(first, second):
        a, b = tasks[first], tasks[second]
        return ('write' in {a['kind'], b['kind']} and any(_overlap(x, y) for x in a['paths'] for y in b['paths']))
    capacity = workers if allowed else 1
    remaining = list(tasks)
    completed = set()
    waves, serialized = [], []
    while remaining:
        ready = [x for x in remaining if set(tasks[x]['dependsOn']) <= completed]
        selected = []
        for candidate in ready:
            conflicts = [x for x in selected if conflict(candidate, x)]
            if conflicts:
                serialized.append({'activity': candidate, 'conflictsWith': conflicts})
            elif len(selected) < capacity:
                selected.append(candidate)
        if not selected:
            raise ValueError('unschedulable dependency graph')
        waves.append(selected)
        completed.update(selected)
        remaining = [x for x in remaining if x not in completed]
    return {'version': 1, 'valid': not diagnostics, 'diagnostics': diagnostics,
            'waves': waves, 'serializedOwnershipConflicts': serialized,
            'effectiveWorkers': capacity,
            'fallback': None if allowed else 'No delegation permitted; coordinator executes sequentially. Review independence unavailable unless another permitted session exists.',
            'reviewIdentityVerified': False, 'speedupVerified': False,
            'scope': 'Declared dependencies and lexical ownership only; no agents launched or filesystem permissions granted.'}
