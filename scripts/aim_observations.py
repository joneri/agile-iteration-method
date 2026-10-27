#!/usr/bin/env python3
"""Import attributed exception-delivery observations, without native gate authority.

This is an opt-in read model. Source artifacts and native ledgers are never
changed. Each import appends a bounded snapshot; currentId selects the visible
snapshot. A source change makes that snapshot stale, never silently current.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timezone
from aim_quality.files import read_evidence
from aim_runtime_lock import runtime_lock

FILE = '.aim/delivery-observations.json'
LEDGER = '.aim/product-backlog.json'
LIMIT = 2_000_000
STATES = {'pending', 'running', 'completed', 'failed', 'blocked'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional), 'Observation fields do not match the declared contract.')


def text(value, limit=4000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit
            and not any(ord(c) < 32 and c not in '\n\t\r' for c in value), 'Invalid observation text.')


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', value), 'Invalid observation identity.')


def fingerprint(repo, path):
    return hashlib.sha256(read_evidence(repo, path, LIMIT)).hexdigest()


def reference(repo, ref, verify=True):
    fields(ref, ('path', 'sha256'))
    p = ref['path']
    require(isinstance(p, str) and Path(p).as_posix() == p and '\\' not in p
            and not Path(p).is_absolute() and '..' not in Path(p).parts and p.startswith('.aim/')
            and p not in {FILE, LEDGER}, 'Observation source must be an independent contained .aim artifact.')
    require(isinstance(ref['sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', ref['sha256']), 'Invalid source fingerprint.')
    if verify:
        require(fingerprint(repo, p) == ref['sha256'], 'Observation source changed: ' + p)


def validate_entry(repo, entry, verify=True):
    fields(entry, ('id', 'deliveryId', 'title', 'goal', 'reportedState', 'decisionBoundary',
                   'epic', 'stories', 'activities', 'sources'), ('replacesDeliveryIds', 'deliveryPolicy'))
    from aim_quality.delivery_policy import normalize_policy, DEFAULT_POLICY
    policy = normalize_policy(entry.get('deliveryPolicy', DEFAULT_POLICY))
    if policy['owner']['kind'] == 'agent':
        reference(repo, policy['owner']['mandate'], verify)
    replaces = entry.get('replacesDeliveryIds', [])
    require(isinstance(replaces, list) and len(replaces) <= 64 and len(set(replaces)) == len(replaces), 'Invalid replaced deliveries.')
    for item in replaces: identifier(item)
    for k in ('id', 'deliveryId'): identifier(entry[k])
    for k in ('title', 'goal', 'decisionBoundary'): text(entry[k])
    require(entry['reportedState'] in {'in_progress', 'awaiting_owner', 'rework_required', 'reported_complete'}, 'Invalid reported delivery state.')
    epic = entry['epic']
    fields(epic, ('id', 'title', 'outcome'))
    identifier(epic['id']); text(epic['title']); text(epic['outcome'])
    require(isinstance(entry['stories'], list) and 1 <= len(entry['stories']) <= 64, 'Observation requires bounded Stories.')
    ids = set()
    for s in entry['stories']:
        fields(s, ('id', 'title', 'persona', 'need', 'benefit', 'acceptanceCriteria'), ('boardStatus', 'dependsOn', 'prerequisites', 'corrects'))
        require(s.get('boardStatus', 'backlog') in {'backlog','ready','in_progress','review','done'}, 'Invalid reported Story stage.')
        require(s.get('boardStatus') != 'done' or entry['reportedState'] == 'reported_complete', 'Done requires a reported completed delivery.')
        require(isinstance(s.get('dependsOn', []), list) and all(isinstance(i, str) for i in s.get('dependsOn', [])), 'Invalid Story dependencies.')
        identifier(s['id']); require(s['id'].startswith('US-') and s['id'] not in ids, 'Duplicate or invalid Story identity.')
        ids.add(s['id'])
        for k in ('title', 'persona', 'need', 'benefit'): text(s[k])
        require(isinstance(s['acceptanceCriteria'], list) and 1 <= len(s['acceptanceCriteria']) <= 32, 'Bounded criteria required.')
        acs = set()
        for ac in s['acceptanceCriteria']:
            fields(ac, ('id', 'text')); identifier(ac['id']); text(ac['text'])
            require(ac['id'] not in acs, 'Duplicate criterion identity.'); acs.add(ac['id'])
    from aim_stories import validate_story_dependencies
    validate_story_dependencies(entry['stories'], observation=True)
    acts = entry['activities']
    require(isinstance(acts, list) and 1 <= len(acts) <= 64, 'Bounded activity graph required.')
    nodes = {}
    for a in acts:
        fields(a, ('id', 'title', 'role', 'status', 'dependsOn', 'storyIds', 'reason'))
        identifier(a['id']); require(a['id'] not in nodes, 'Duplicate activity.'); nodes[a['id']] = a
        for k in ('title', 'reason'): text(a[k])
        require(a['role'] in {'po', 'tdo', 'dev', 'reviewer', 'human'}, 'Invalid observed role.')
        require(a['status'] in STATES, 'Invalid observed activity state.')
        for key in ('dependsOn', 'storyIds'):
            require(isinstance(a[key], list) and len(a[key]) <= 64
                    and all(isinstance(i, str) for i in a[key])
                    and len(set(a[key])) == len(a[key]), 'Invalid graph links.')
        require(bool(a['storyIds']) and set(a['storyIds']) <= ids, 'Unknown observed Story link.')
    visited = set()
    def visit(i, active):
        require(i in nodes and i not in active, 'Unknown dependency or cyclic observation graph.')
        if i in visited: return
        for dep in nodes[i]['dependsOn']: visit(dep, active | {i})
        visited.add(i)
    for i in nodes: visit(i, set())
    require(isinstance(entry['sources'], list) and 1 <= len(entry['sources']) <= 32, 'Bounded source references required.')
    require(len({r['path'] for r in entry['sources'] if isinstance(r, dict) and 'path' in r}) == len(entry['sources']), 'Duplicate observation sources.')
    for ref in entry['sources']: reference(repo, ref, verify)


def _stable_scopes(records):
    scopes = {}
    for record in records:
        entry = record['entry']
        from aim_quality.delivery_policy import normalize_policy, DEFAULT_POLICY
        scope = (entry['epic']['id'], sorted(s['id'] for s in entry['stories']),
                 normalize_policy(entry.get('deliveryPolicy', DEFAULT_POLICY)))
        require(scopes.get(entry['deliveryId'], scope) == scope,
                'A refreshed delivery must preserve its Epic, Story identities and frozen owner policy.')
        scopes[entry['deliveryId']] = scope


def load(repo):
    path = Path(repo) / FILE
    if not path.exists() and not path.is_symlink(): return None, None
    raw = read_evidence(repo, FILE, LIMIT)
    data = json.loads(raw)
    fields(data, ('observationVersion', 'revision', 'currentId', 'entries'), ('decisions',))
    require(data['observationVersion'] == 1 and type(data['revision']) is int and data['revision'] > 0, 'Invalid observation version/revision.')
    require(isinstance(data['entries'], list) and 1 <= len(data['entries']) <= 32, 'Bounded observation history required.')
    ids = set(); stories = {}; epics = {}
    for record in data['entries']:
        fields(record, ('entry', 'importedAt', 'ledgerSha256'))
        text(record['importedAt']); require(isinstance(record['ledgerSha256'], str) and re.fullmatch('[a-f0-9]{64}', record['ledgerSha256']), 'Invalid ledger binding.')
        entry = record['entry']; validate_entry(repo, entry, verify=False)
        require(entry['id'] not in ids, 'Duplicate snapshot identity.'); ids.add(entry['id'])
        require(epics.get(entry['epic']['id'], entry['deliveryId']) == entry['deliveryId'], 'Observed Epic collision.'); epics[entry['epic']['id']] = entry['deliveryId']
        for s in entry['stories']:
            require(stories.get(s['id'], entry['deliveryId']) == entry['deliveryId'], 'Observed Story collision.'); stories[s['id']] = entry['deliveryId']
    require(len(stories) <= 256 and data['currentId'] in ids, 'Invalid current observation or excessive Stories.')
    latest = {r['entry']['deliveryId']: r['entry']['id'] for r in data['entries']}
    require(data['currentId'] in latest.values(), 'Current observation must select a latest delivery snapshot.')
    _stable_scopes(data['entries'])
    validate_decisions(repo, data, verify=False)
    return data, hashlib.sha256(raw).hexdigest()


def import_entry(repo, request, expected_sha256=None):
    repo = Path(repo).resolve()
    fields(request, ('ledgerSha256', 'entry'), ('makeCurrent',))
    make_current = request.get('makeCurrent', True)
    require(type(make_current) is bool, 'makeCurrent must be a boolean.')
    path = repo / FILE
    require(not (repo / '.aim').is_symlink(), '.aim must not be a link.')
    with runtime_lock(path):
        data, before = load(repo)
        require(before == expected_sha256, 'Stale observation digest; reload before importing.')
        if not make_current:
            require(data is not None, 'Historical import requires an existing current delivery.')
            current = next(r['entry'] for r in data['entries'] if r['entry']['id'] == data['currentId'])
            require(request['entry']['deliveryId'] != current['deliveryId'],
                    'Use a current import to refresh the current delivery.')
        require(fingerprint(repo, LEDGER) == request['ledgerSha256'], 'Native ledger changed before import.')
        native = json.loads(read_evidence(repo, LEDGER, LIMIT))
        from aim_stories import validate_document
        validate_document(native)
        entry = request['entry']; validate_entry(repo, entry)
        require(set(entry.get('replacesDeliveryIds', [])) <= {d['id'] for d in native.get('deliveries', [])}, 'Unknown replaced native delivery.')
        require(entry['deliveryId'] not in {d['id'] for d in native.get('deliveries', [])}, 'Observation cannot replace a native delivery.')
        require(entry['epic']['id'] not in {e['id'] for e in native.get('epics', [])}, 'Observation cannot replace a native Epic.')
        require(not {s['id'] for s in entry['stories']} & {s['id'] for s in native.get('stories', [])}, 'Observation cannot replace native Stories.')
        data = data or dict(observationVersion=1, revision=0, currentId=entry['id'], entries=[])
        data['entries'].append(dict(entry=entry, importedAt=datetime.now(timezone.utc).isoformat(), ledgerSha256=request['ledgerSha256']))
        data.update(revision=data['revision'] + 1)
        if make_current:
            data['currentId'] = entry['id']
        _stable_scopes(data['entries'])
        from aim_story_links import validate_links
        validate_links(entry['stories'], native, data)
        raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
        require(len(raw) <= LIMIT and len(data['entries']) <= 32, 'Observation history limit reached.')
        # Validate the aggregate before writing, without touching the original ledger.
        require(len({r['entry']['id'] for r in data['entries']}) == len(data['entries']), 'Snapshot identity already imported.')
        story_owners = {}; epic_owners = {}
        for rec in data['entries']:
            item = rec['entry']
            for sid in [s['id'] for s in item['stories']]:
                require(story_owners.get(sid, item['deliveryId']) == item['deliveryId'], 'Observed Story collision.')
                story_owners[sid] = item['deliveryId']
            eid = item['epic']['id']
            require(epic_owners.get(eid, item['deliveryId']) == item['deliveryId'], 'Observed Epic collision.')
            epic_owners[eid] = item['deliveryId']
        require(len(story_owners) <= 256, 'Too many observed Stories.')
        validate_entry(repo, entry)  # Detect changed producer evidence before commit.
        require(fingerprint(repo, LEDGER) == request['ledgerSha256'], 'Native ledger changed during import.')
        _write_store(path, raw)
    return dict(storeSha256=hashlib.sha256(raw).hexdigest(), currentId=data['currentId'], nativeLedgerChanged=False)


def _write_store(path, raw):
    fd, tmp = tempfile.mkstemp(prefix='.observation-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def selected_scope(entry, story_ids):
    """Requirement selection and declared owner; never transient activity/card state."""
    from aim_quality.delivery_policy import normalize_policy, DEFAULT_POLICY
    require(isinstance(story_ids, list) and 0 < len(story_ids) <= 64
            and all(isinstance(i, str) for i in story_ids)
            and len(set(story_ids)) == len(story_ids), 'Select distinct named Stories.')
    stories = {s['id']: s for s in entry['stories']}
    require(set(story_ids) <= set(stories), 'Decision refers to unknown Stories.')
    scope = []
    for sid in sorted(story_ids):
        story = {k: copy.deepcopy(v) for k,v in stories[sid].items() if k not in {'boardStatus', 'prerequisites'}}
        if 'prerequisites' in stories[sid]:
            story['prerequisites'] = [{k:v for k,v in item.items() if k != 'resolved'} for item in stories[sid]['prerequisites']]
        scope.append(story)
    return digest(dict(deliveryId=entry['deliveryId'], epic=entry['epic'], goal=entry['goal'],
                       stories=scope, deliveryPolicy=normalize_policy(entry.get('deliveryPolicy', DEFAULT_POLICY))))


def decision_scope(entry, story_ids, correction_context=None):
    requirements = selected_scope(entry, story_ids)
    return digest(dict(requirementsScopeSha256=requirements, correctionContextSha256=correction_context)) if correction_context else requirements


def decision_context(repo, request):
    fields(request, ('deliveryId', 'storyIds'))
    data, sha = load(repo)
    require(data is not None, 'Register the delivery requirements before its owner decision.')
    entry = next((r['entry'] for r in reversed(data['entries']) if r['entry']['deliveryId'] == request['deliveryId']), None)
    require(entry is not None, 'Unknown observation delivery.')
    context = _correction_context(repo, entry['deliveryId'], request['storyIds'])
    return dict(storeSha256=sha, deliveryId=entry['deliveryId'], storyIds=request['storyIds'],
                scopeSha256=decision_scope(entry, request['storyIds'], context.get('correctionContextSha256')), **context)


def _correction_context(repo, delivery_id, story_ids):
    from aim_story_links import incoming_context, digest
    incoming = incoming_context(repo, delivery_id, story_ids)
    return dict(corrections=incoming, correctionContextSha256=digest(incoming)) if incoming else {}


def _decision_authority(repo, request, entry, verify=True):
    from aim_quality.delivery_policy import validate_authority_binding, normalize_policy, DEFAULT_POLICY
    authority = request['authority']
    require(isinstance(authority, dict), 'Supply actual owner authority.')
    policy = normalize_policy(entry.get('deliveryPolicy', DEFAULT_POLICY))
    validate_authority_binding(authority, policy, 'accept')
    require(authority['scopeSha256'] == request['scopeSha256'], 'Authority has a different requirement scope.')
    reference(repo, {k:authority[k] for k in ('path','sha256')}, verify)
    if policy['owner']['kind'] == 'agent': reference(repo, policy['owner']['mandate'], verify)
    if authority['kind'] == 'agent' and verify:
        def pairs(items):
            result = {}
            for key,value in items:
                require(key not in result, 'Ambiguous owner decision JSON.'); result[key] = value
            return result
        evidence = json.loads(read_evidence(repo, authority['path'], 16384), object_pairs_hook=pairs)
        fields(evidence, ('ownerDecisionVersion','deliveryId','operation','scopeSha256','id','session','decision','reason'))
        require(type(evidence['ownerDecisionVersion']) is int and evidence['ownerDecisionVersion'] == 1,
                'Unsupported owner decision version.')
        require(evidence['operation'] == 'accept' and evidence['deliveryId'] == request['deliveryId']
                and evidence['decision'] == request['decision']
                and all(evidence[k] == authority[k] for k in ('scopeSha256','id','session')),
                'Owner evidence does not match this delivery, disposition, identity and scope.')
        text(evidence['reason'])


def validate_decision(repo, request, entry, verify=True):
    fields(request, ('id','deliveryId','storyIds','scopeSha256','decision','authority','reason','evidence'), ('correctionContextSha256',))
    identifier(request['id']); identifier(request['deliveryId']); text(request['reason'])
    require(request['deliveryId'] == entry['deliveryId'], 'Decision delivery mismatch.')
    require(request['decision'] in {'approved','changes_requested'}, 'Owner decision must approve or request changes.')
    require(request['scopeSha256'] == decision_scope(entry, request['storyIds'], request.get('correctionContextSha256')), 'Decision refers to changed requirements or owner policy.')
    _decision_authority(repo, request, entry, verify)
    if 'correctionContextSha256' in request:
        require(isinstance(request['correctionContextSha256'], str) and re.fullmatch('[a-f0-9]{64}', request['correctionContextSha256']), 'Invalid correction decision context.')
    refs = request['evidence']
    require(isinstance(refs, list) and 1 <= len(refs) <= 32, 'Supply bounded current assessment evidence.')
    require(len({r['path'] for r in refs}) == len(refs), 'Duplicate decision evidence.')
    for ref in refs: reference(repo, ref, verify)


def validate_decisions(repo, data, verify=False):
    records = data.get('decisions', [])
    require(isinstance(records, list) and len(records) <= 256, 'Decision journal limit reached.')
    snapshots = {r['entry']['id']:r['entry'] for r in data['entries']}
    ids = set()
    for record in records:
        fields(record, ('request','snapshotId','recordedAt','requestSha256'))
        request = record['request']; text(record['recordedAt'])
        require(record['snapshotId'] in snapshots, 'Decision snapshot missing.')
        validate_decision(repo, request, snapshots[record['snapshotId']], verify)
        require(request['id'] not in ids and record['requestSha256'] == digest(request), 'Duplicate or changed decision identity.')
        ids.add(request['id'])


def record_decision(repo, request, expected_sha256=None):
    """One atomic owner decision. Board state is derived, never separately edited."""
    repo = Path(repo).resolve(); path = repo / FILE
    require(not (repo / '.aim').is_symlink(), '.aim must not be a link.')
    with runtime_lock(path):
        data, before = load(repo)
        require(data is not None, 'Register delivery requirements first.')
        fields(request, ('id','deliveryId','storyIds','scopeSha256','decision','authority','reason','evidence'), ('correctionContextSha256',))
        previous = next((r for r in data.get('decisions', []) if r['request']['id'] == request['id']), None)
        if previous:
            require(previous['requestSha256'] == digest(request), 'Decision identity already has a different payload.')
            return dict(storeSha256=before, decisionId=request['id'], alreadyRecorded=True,
                        currentId=data['currentId'], nativeLedgerChanged=False)
        require(before == expected_sha256, 'Stale decision context; reload before recording.')
        require(len(data.get('decisions', [])) < 256, 'Decision journal limit reached.')
        record = next((r for r in reversed(data['entries']) if r['entry']['deliveryId'] == request['deliveryId']), None)
        require(record is not None, 'Unknown observation delivery.')
        entry = record['entry']
        validate_entry(repo, entry)
        require(native_binding_current(repo, record), 'Native ledger changed since requirement publication.')
        validate_decision(repo, request, entry)
        context = _correction_context(repo, entry['deliveryId'], request['storyIds'])
        require(request.get('correctionContextSha256') == context.get('correctionContextSha256'),
                'Correction context changed or was not reviewed; reload the original decision context.')
        if context and request['decision'] == 'approved':
            from aim_stories import project_story_board
            selected = [s for s in project_story_board(repo)['stories'] if s['id'] in request['storyIds']]
            require(all((s.get('waitingForOwner') or s['status'] == 'done') and not s.get('sourceStale')
                        and all(c['ready'] for c in s.get('corrections', [])) for s in selected), 'Resubmit and verify the complete original scope before final acceptance.')
        data.setdefault('decisions', []).append(dict(request=copy.deepcopy(request), snapshotId=entry['id'],
            requestSha256=digest(request), recordedAt=datetime.now(timezone.utc).isoformat()))
        data['revision'] += 1
        raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
        require(len(raw) <= LIMIT, 'Observation store size limit reached.')
        validate_decisions(repo, data)
        validate_decision(repo, request, entry)  # Fresh proof immediately before the single commit.
        validate_entry(repo, entry)
        require(native_binding_current(repo, record), 'Native ledger changed during decision recording.')
        require(context == _correction_context(repo, entry['deliveryId'], request['storyIds']), 'Correction context changed during decision recording.')
        _write_store(path, raw)
    return dict(storeSha256=hashlib.sha256(raw).hexdigest(), decisionId=request['id'], alreadyRecorded=False,
                currentId=data['currentId'], nativeLedgerChanged=False)


def _apply_decisions(repo, data, entry, stories):
    snapshots = {s['id']: (s['sourceNote'], s.get('sourceStale', False), list(s['evidence']), s['column']) for s in stories}
    history = {s['id']: [] for s in stories}
    for record in data.get('decisions', []):
        request = record['request']
        if request['deliveryId'] != entry['deliveryId']: continue
        # Old decisions never promote changed requirements, even if a producer copies old Done.
        matches = request['scopeSha256'] == decision_scope(entry, request['storyIds'], request.get('correctionContextSha256'))
        for story in stories:
            if story['id'] not in request['storyIds']: continue
            snapshot_note, snapshot_stale, snapshot_evidence, snapshot_stage = snapshots[story['id']]
            earlier = ' Earlier owner decisions: ' + '; '.join(history[story['id']]) if history[story['id']] else ''
            history[story['id']].append(request['id'] + ': ' + request['decision'] + ' at ' + record['recordedAt'])
            if not matches:
                story.pop('decisionId', None)
                stage = 'review' if snapshot_stage == 'done' else snapshot_stage
                story.update(status=stage, column=stage,
                             waitingForOwner=stage == 'review' and
                             (snapshot_stage == 'done' or entry['reportedState'] == 'awaiting_owner'),
                             sourceStale=snapshot_stale or snapshot_stage == 'done')
                story['sourceNote'] = 'Previous owner decision belongs to changed requirements; new assessment needed. ' + earlier + ' Historical progress snapshot: ' + snapshot_note
                continue
            issues = []
            try: validate_decision(repo, request, entry)
            except (ValueError,OSError,KeyError,TypeError) as exc: issues.append(str(exc))
            approved = request['decision'] == 'approved'
            resubmitted = (not approved and entry['id'] != record['snapshotId']
                           and entry['reportedState'] == 'awaiting_owner' and snapshot_stage == 'review')
            stage = 'done' if approved else 'review' if resubmitted else 'in_progress'
            story.update(status=stage, column=stage,
                waitingForOwner=resubmitted, decisionId=request['id'], sourceStale=snapshot_stale or bool(issues))
            story['prerequisites'] = [{**item, 'resolved': approved} if item.get('kind') == 'owner_assessment' else item for item in story.get('prerequisites', [])]
            story['sourceNote'] = ('Corrected work awaits a new owner assessment. Last recorded owner decision (' if resubmitted else 'Current owner decision (') + request['id'] + ', ' + record['recordedAt'] + '): ' + request['decision'] + '. ' + request['reason'] + earlier + ' Historical progress snapshot: ' + snapshot_note
            if issues: story['sourceNote'] += ' Recorded decision evidence needs verification: ' + ' '.join(issues)
            story['evidence'] = snapshot_evidence + [{**r, 'label':'Owner decision evidence'} for r in [
                {k:request['authority'][k] for k in ('path','sha256')}, *request['evidence']]]



def native_binding_current(repo, record, native=None):
    if fingerprint(repo, LEDGER) == record['ledgerSha256']:
        return True
    # Explicit native correction targets bind immutable requirements separately
    # from native phase transitions. Every Story must carry that narrower binding.
    if native is None:
        from aim_stories import load as load_native
        native, _ = load_native(repo, check_evidence=False)
    entry = record['entry']
    native_ids = {d['id'] for d in native.get('deliveries', [])}
    if not all(any(link['deliveryId'] in native_ids for link in story.get('corrects', [])) for story in entry['stories']):
        return False
    from aim_story_links import validate_links
    try:
        validate_links(entry['stories'], native, None)
    except ValueError:
        return False
    return True


def project(repo, native):
    result = dict(entries=[], currentId=None, issues=[])
    try:
        data, sha = load(repo)
        if data is None: return result
        result.update(currentId=data['currentId'], storeSha256=sha)
        native_ids = {s['id'] for s in native['stories']}
        native_epics = {e['id'] for e in native['epics']}
        native_deliveries = {d['id'] for d in native['deliveries']}
        latest = {record['entry']['deliveryId']: record for record in data['entries']}
        for record in latest.values():
            e = record['entry']
            require(not {s['id'] for s in e['stories']} & native_ids and e['epic']['id'] not in native_epics
                    and e['deliveryId'] not in native_deliveries, 'Observation collides with native records.')
            issues = []
            try:
                validate_entry(repo, e)
                require(native_binding_current(repo, record, native), 'Native ledger changed since observation import.')
            except (ValueError, OSError) as exc: issues.append(str(exc))
            stale = bool(issues)
            native_advanced = not stale and fingerprint(repo, LEDGER) != record['ledgerSha256']
            label = 'Observed exception work · ' + ('source changed; refresh required' if stale else e['reportedState'].replace('_', ' '))
            stories = [{**s, 'epicId': e['epic']['id'], 'priority': 1000 + n, 'status': s.get('boardStatus', 'review' if e['reportedState'] in {'awaiting_owner', 'reported_complete'} else 'in_progress'), 'column': s.get('boardStatus', 'review' if e['reportedState'] in {'awaiting_owner', 'reported_complete'} else 'in_progress'),
                        'observationId': e['id'], 'readOnly': True, 'deliveryIds': [e['deliveryId']], 'evidence': [],
                        'attention': label + '. ' + e['decisionBoundary']} for n,s in enumerate(e['stories'])]
            graph = dict(available=True, configured=True, source='observation', nativeEvidenceValid=False,
                deliveryId=e['deliveryId'], title=e['title'], goal=e['goal'], stories=stories,
                summary=label + '. ' + e['decisionBoundary'], recommendedIds=[], retryIds=[], readyIds=[],
                blockers=[{'reason': i} for i in issues] + [dict(activityId=a['id'], reason=a['reason'])
                    for a in e['activities'] if a['status'] in {'blocked', 'failed'}], activities=[{**a, 'status': 'stale' if stale else a['status'],
                    'kind': 'observation', 'evidence': e['sources']} for a in e['activities']],
                edges=[{'from': dep, 'to': a['id']} for a in e['activities'] for dep in a['dependsOn']])
            for story in stories:
                story['sourceNote'] = label + '. ' + e['decisionBoundary']
                story['sourceStale'] = stale
                if native_advanced:
                    story['sourceNote'] += ' Native delivery progressed; linked original requirement bindings remain current.'
                story['waitingForOwner'] = e['reportedState'] == 'awaiting_owner' and story['column'] == 'review'
                story['evidence'] = [{**ref, 'label': 'Source'} for ref in e['sources']]
                story['attention'] = ''
            _apply_decisions(repo, data, e, stories)
            for story in stories:
                story['ownerDecisionState'] = ('awaiting_owner' if story['waitingForOwner'] else
                                               'approved' if story['column'] == 'done' and story.get('decisionId') else
                                               'changes_requested' if story.get('decisionId') and story['column'] == 'in_progress' else None)
            result['entries'].append(dict(id=e['id'], title=e['title'], reportedState=e['reportedState'],
                decisionBoundary=e['decisionBoundary'], stale=stale, importedAt=record['importedAt'],
                deliveryPolicy=e.get('deliveryPolicy', dict(mode='ship', owner=dict(kind='human'))), replacesDeliveryIds=e.get('replacesDeliveryIds', []), epic={**e['epic'], 'observationId': e['id']}, stories=stories, graph=graph))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result.update(entries=[], currentId=None, issues=[str(exc)])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['import', 'status', 'decision-context', 'decision']); p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--input', type=Path); p.add_argument('--expected-sha256')
    args=p.parse_args()
    try:
        if args.command == 'import':
            require(args.input is not None, 'Import requires a normalized request file.')
            result=import_entry(args.repo, json.loads(args.input.read_text()), args.expected_sha256)
        elif args.command in {'decision-context', 'decision'}:
            require(args.input is not None, 'Decision operation requires an input file.')
            raw=args.input.read_bytes()
            require(len(raw) <= LIMIT, 'Decision request exceeds the size limit.')
            request=json.loads(raw)
            result=decision_context(args.repo,request) if args.command == 'decision-context' else record_decision(args.repo,request,args.expected_sha256)
        else:
            data,sha=load(args.repo); result=dict(storeSha256=sha,document=data)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'error':str(exc),'committed':False})); return 1
    return 0

if __name__ == '__main__': raise SystemExit(main())
