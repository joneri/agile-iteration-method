# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/orchestration_runtime.py
"""Durable Native orchestration in the sole product ledger.

Host identities supplied through the CLI are declarations. The native Codex
transport additionally compares its actual bound thread. Evidence is hash-bound,
not a claim that a capability or an owner has been authenticated by this module.
"""
from __future__ import annotations
import copy
import hashlib
import json
from .orchestration import (validate_graph, assess_campaign, _fields, _need, _text,
                            _validate_observation, _id, DECISIONS)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def prepare_plan(graph, story_outcomes):
    """Convert once; preserve the user's graph bytes as a frozen plan member."""
    graph = validate_graph(graph)
    _need(isinstance(story_outcomes, dict) and bool(story_outcomes), 'Supply Story-to-original-Intent mappings.')
    outcomes = {o['id'] for o in graph['outcomes']}
    for sid, ids in story_outcomes.items():
        _id(sid, 'Story ID')
        _need(isinstance(ids, list) and bool(ids) and set(ids) <= outcomes,
              'Story mapping names an unknown original outcome.')
    activities = []
    for node in graph['nodes']:
        ids = [sid for sid, goals in story_outcomes.items() if set(goals) & set(node['outcomeIds'])]
        _need(bool(ids), 'Every node must map to a selected Story.')
        activities.append({key: copy.deepcopy(node[key]) for key in ('id', 'kind', 'role', 'paths', 'dependsOn')})
        activities[-1].update(title=node['id'], storyIds=ids)
    result = dict(version=1, delegationAllowed=graph['policy']['delegationAllowed'],
                  maxWorkers=graph['policy']['maxWorkers'], activities=activities, orchestration=graph)
    if 'parallelBenefit' in graph['policy']:
        result['parallelBenefit'] = graph['policy']['parallelBenefit']
    return result


def native_graph(delivery):
    return delivery.get('executionPlan', {}).get('orchestration')


def validate_native_plan(delivery):
    graph = native_graph(delivery)
    if graph is None:
        return
    validate_graph(graph)
    expected = {item['id']: item['statement'] for item in delivery['intents']}
    _need({o['id']: o['requirement'] for o in graph['outcomes']} == expected,
          'Native outcomes must preserve every selected original Intent ID and statement.')
    story_intents = {s['id']: next(e['intentId'] for e in delivery['epics'] if e['id'] == s['epicId'])
                     for s in delivery['stories']}
    nodes = {node['id']: node for node in graph['nodes']}
    activities = delivery['executionPlan']['activities']
    _need(set(nodes) == {a['id'] for a in activities}, 'Native graph and executable activities differ.')
    for activity in activities:
        node = nodes[activity['id']]
        _need(all(activity[k] == node[k] for k in ('kind', 'role', 'paths', 'dependsOn')),
              'Native node ownership or dependencies differ from executable activities.')
        _need({story_intents[s] for s in activity['storyIds']} == set(node['outcomeIds']),
              'Native node outcome links differ from its actual Story assignments.')
    for key in ('maxWorkers', 'delegationAllowed'):
        _need(delivery['executionPlan'][key] == graph['policy'][key], 'Native worker policy differs from execution plan.')


def campaigns(document):
    return document.get('orchestration', {}).get('campaigns', [])


def waiting_goals(document):
    return [i['id'] for i in document['intents']
            if not any(e['intentId'] == i['id'] for e in document['epics'])
            or any(e['intentId'] == i['id'] and e['status'] == 'open' for e in document['epics'])]


def campaign_for(document, outcome):
    return next((c for c in campaigns(document) if c['outcomeId'] == outcome), None)


def _decision_context(campaign, owner_priority):
    return digest(dict(campaign={k: v for k, v in campaign.items() if k != 'decisions'}, ownerPriority=owner_priority))


def assessment(campaign, check_reference=None, *, owner_priority=None):
    result = assess_campaign(campaign['campaign'])
    latest = next((r for r in reversed(campaign['observations'])
                   if r['observation']['kind'] in {'baseline', 'integrated_progress'}), None)
    result['currentEvidenceFresh'] = None
    if latest is not None and check_reference is not None:
        try:
            for ref in latest['sourceBindings'] + latest['evidence']:
                check_reference(ref)
            result['currentEvidenceFresh'] = True
        except (ValueError, OSError):
            result['currentEvidenceFresh'] = False
    # A real scoped owner decision may open a bounded new checkpoint, while the
    # entire original chronology, highwater and resources remain in assessment.
    used = result['attemptsSinceImprovement']
    start = campaign.get('checkpointStart', 0)
    if start and result['totalAttempts'] >= start:
        remaining_used = max(0, result['totalAttempts'] - start)
        if remaining_used < result['attemptBudget'] and result['budgetExhausted']:
            result['budgetExhausted'] = False
            result['attemptsUsed'] = remaining_used
            result['recommendation'].update(action='change_diagnostic_action',
                targetOutcomeId=campaign['outcomeId'],
                why='A scoped owner decision opened a bounded checkpoint; retained history still requires the changed action.')
    if campaign.get('ownerChoicePending'):
        result['recommendation'].update(action='request_owner_choice', targetOutcomeId=campaign['outcomeId'],
            why='The recorded actual owner choice remains pending; preserve it before resuming this work.')
    result['contextSha256'] = digest(dict(campaign=campaign, ownerPriority=owner_priority or []))
    result['activationAuthenticatesIdentity'] = False
    return result


def validate_native_document(document):
    state = document.get('orchestration')
    if state is not None:
        _fields(state, ('version', 'campaigns'), ('ownerPriority',), label='Native ledger')
        _need(state['version'] == 1 and type(state['version']) is int, 'Native ledger version must be 1.')
        _need(isinstance(state['campaigns'], list) and len(state['campaigns']) <= 256, 'Bounded campaigns required.')
        ids = []
        for c in state['campaigns']:
            _fields(c, ('outcomeId', 'campaign', 'attempts', 'observations', 'decisions'), ('checkpointStart', 'ownerChoicePending', 'nextActionKey'), 'Stored campaign')
            _need(c['outcomeId'] in {i['id'] for i in document['intents']}, 'Unknown original campaign Intent.')
            _need(type(c.get('ownerChoicePending', False)) is bool, 'Invalid owner choice pending state.')
            if 'nextActionKey' in c:
                _text(c['nextActionKey'], 'Pending concrete next action', 128)
            ids.append(c['outcomeId'])
            _need(c['campaign']['outcomeId'] == c['outcomeId'], 'Campaign identity mismatch.')
            assess_campaign(c['campaign'])
            _need(len(c['attempts']) <= 128 and len(c['observations']) <= 512 and len(c['decisions']) <= 128,
                  'Native campaign history is full; retain evidence and ask the owner for disposition.')
            for index, attempt in enumerate(c['attempts'], 1):
                _fields(attempt, ('number', 'deliveryId', 'activityId', 'attempt', 'session', 'actionKey'), label='Campaign attempt')
                _need(attempt['number'] == index, 'Campaign attempts must be sequential.')
                delivery = next((d for d in document['deliveries'] if d['id'] == attempt['deliveryId']), None)
                _need(delivery is not None and native_graph(delivery) is not None, 'Campaign attempt delivery missing.')
                receipt = next((r for r in delivery.get('activityReceipts', [])
                                if r['activityId'] == attempt['activityId'] and r['attempt'] == attempt['attempt']), None)
                _need(receipt is not None and receipt['session'] == attempt['session'], 'Campaign attempt lost actual receipt binding.')
            for record in c['observations']:
                _fields(record, ('observation', 'evidence', 'sourceBindings', 'deliveryId'), ('sourceCheckpoint',), label='Stored observation')
                if record['observation']['kind'] == 'baseline' and record['observation']['usable']:
                    _need('sourceCheckpoint' in record, 'Usable baseline needs recoverable source bytes/version.')
                    import base64
                    checkpoint = record['sourceCheckpoint']
                    _fields(checkpoint, ('kind', 'files'), ('commit',), label='Source checkpoint')
                    _need(checkpoint['kind'] in {'inline', 'git'} and isinstance(checkpoint['files'], list), 'Unknown source checkpoint format.')
                    expected_sources = {r['path']: r['sha256'] for r in record['sourceBindings']}
                    actual_sources = {}
                    total = 0
                    if checkpoint['kind'] == 'git':
                        import re
                        _need(isinstance(checkpoint.get('commit'), str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', checkpoint['commit']), 'Invalid exact Git source commit.')
                    for source in checkpoint['files']:
                        if checkpoint['kind'] == 'inline':
                            _fields(source, ('path', 'sha256', 'contentBase64'), label='Checkpoint source')
                            try:
                                payload = base64.b64decode(source['contentBase64'], validate=True)
                            except (ValueError, TypeError) as exc:
                                raise ValueError('Invalid checkpoint source bytes.') from exc
                            total += len(payload)
                            _need(total <= 262144 and hashlib.sha256(payload).hexdigest() == source['sha256'], 'Checkpoint bytes or hash invalid.')
                        else:
                            _fields(source, ('path', 'sha256'), label='Git checkpoint source')
                        _need(source['path'] not in actual_sources, 'Duplicate checkpoint source.')
                        actual_sources[source['path']] = source['sha256']
                    _need(actual_sources == expected_sources, 'Checkpoint must retain every explicitly bound baseline source.')
                _need(record['observation'] in c['campaign']['observations'], 'Stored observation lost chronology binding.')
            for decision in c['decisions']:
                _fields(decision, ('decision', 'actionKey', 'reason', 'contextSha256', 'evidence', 'at'), ('authority', 'priority', 'targetOutcomeId'), 'Campaign decision')
                _need(decision['decision'] in DECISIONS, 'Unknown orchestration decision.')
        _need(len(ids) == len(set(ids)), 'Duplicate original campaign.')
    for delivery in document['deliveries']:
        validate_native_plan(delivery)
        activation = delivery.get('orchestrationActivation')
        if activation is not None:
            graph = native_graph(delivery)
            _need(graph is not None, 'Native activation requires a frozen graph.')
            _fields(activation, ('scopeSha256', 'coordinatorSession', 'dispatchers', 'evidence', 'at'), label='Activation')
            _need(activation['scopeSha256'] == delivery['scopeSha256'], 'Stale activation scope.')
            history = delivery.get('orchestrationActivationHistory', [])
            _need(len(history) <= 128, 'Activation history is full.')
            first = history[0] if history else activation
            _need(first['coordinatorSession'] == graph['coordinator']['session'], 'Initial coordinator differs from frozen graph.')
            for prior in history:
                _need(prior['scopeSha256'] == delivery['scopeSha256'], 'Historical activation scope mismatch.')
            sessions = []
            for actor in activation['dispatchers']:
                _fields(actor, ('session', 'capability', 'evidence'), label='Activated dispatcher')
                _text(actor['session'], 'Actual dispatcher session', 128)
                _need(actor['capability'] == graph['coordinator']['capability'], 'Dispatcher capability differs from frozen graph.')
                sessions.append(actor['session'])
            _need(sessions and activation['coordinatorSession'] in sessions and len(sessions) == len(set(sessions)),
                  'Coordinator and upstream dispatchers require unique explicit activation.')


def _activation(delivery, session):
    activation = delivery.get('orchestrationActivation')
    _need(activation is not None and activation['scopeSha256'] == delivery['scopeSha256'],
          'Activate the actual coordinator and upstream dispatchers for this frozen Native scope first.')
    _need(session in [a['session'] for a in activation['dispatchers']], 'Actual coordinator/dispatcher session is not activated.')
    return activation


def _fresh_observations(campaign, check_reference):
    # Historical failures remain usable; only a claimed integrated improvement
    # or usable baseline needs current product identity before permitting work.
    for record in campaign['observations']:
        if record['observation']['kind'] in {'baseline', 'integrated_progress', 'falsifier'}:
            for ref in record['evidence']:
                check_reference(ref)


def pending_priority(document, check_reference):
    priorities = [i for i in document.get('orchestration', {}).get('ownerPriority', []) if i in waiting_goals(document)]
    pending = []
    for outcome in priorities:
        candidates = [(d, n) for d in document['deliveries'] if d['status'] not in {'accepted', 'cancelled'} and native_graph(d)
                      for n in native_graph(d)['nodes'] if outcome in n['outcomeIds'] and n['kind'] != 'review']
        if not candidates:
            pending.append(outcome)
            continue
        for delivery, node in candidates:
            receipt = next((r for r in reversed(delivery.get('activityReceipts', [])) if r['activityId'] == node['id']), None)
            complete = receipt is not None and receipt['status'] == 'completed'
            if complete:
                try:
                    for ref in receipt['sourceBindings'] + receipt['evidence']:
                        check_reference(ref)
                except (ValueError, OSError):
                    complete = False
            if not complete:
                pending.append(outcome)
                break
    return pending


def check_activity(document, delivery, request, *, check_reference):
    graph = native_graph(delivery)
    if graph is None:
        return
    _activation(delivery, request.get('coordinatorSession'))
    _text(request.get('actionKey'), 'Concrete diagnostic/delivery actionKey', 128)
    node = next((n for n in graph['nodes'] if n['id'] == request.get('activityId')), None)
    _need(node is not None, 'Unknown Native activity ID.')
    priorities = pending_priority(document, check_reference)
    _need(node['kind'] == 'review' or not priorities or priorities[0] in node['outcomeIds'],
          'Native campaign changed next action: work_owner_priority_first; preserve the actual owner order across campaigns.')
    for outcome in node['outcomeIds']:
        c = campaign_for(document, outcome)
        _need(c is not None, 'Original campaign is not activated.')
        _fresh_observations(c, check_reference)
        if node['kind'] == 'review':
            continue  # Read-only independent proof/recovery remains reachable at a work boundary.
        _need('nextActionKey' not in c or c['nextActionKey'] == request['actionKey'],
              'The actual next action must match the recorded diagnostic/owner decision.')
        last_decision = c['decisions'][-1] if c['decisions'] else None
        _need(last_decision is None or last_decision['decision'] not in {'request_owner_choice', 'independent_work'},
              'Native campaign changed next action: ' + (last_decision['decision'] if last_decision else '') + '; preserve that decision before further work here.')
        result = assessment(c, check_reference, owner_priority=document.get('orchestration', {}).get('ownerPriority', []))
        action = result['recommendation']['action']
        _need(action not in {'request_owner_choice', 'work_owner_priority_first', 'work_independent_ready'},
              'Native campaign changed next action: ' + action + '; use the indicated original goal or scoped owner decision.')
        if action == 'change_diagnostic_action':
            decision = c['decisions'][-1] if c['decisions'] else None
            _need(decision is not None and decision['decision'] in {'change_baseline', 'continue_bounded'}
                  and decision['contextSha256'] == _decision_context(c, document.get('orchestration', {}).get('ownerPriority', [])),
                  'Record a current consequential diagnostic decision before another attempt.')
            _need(decision['actionKey'] == request['actionKey']
                  and (not c['attempts'] or c['attempts'][-1]['actionKey'] != request['actionKey']),
                  'The next actual action must match the changed diagnostic decision.')


def record_start(document, delivery, request, receipt):
    graph = native_graph(delivery)
    if graph is None:
        return
    node = next(n for n in graph['nodes'] if n['id'] == request['activityId'])
    for outcome in node['outcomeIds']:
        c = campaign_for(document, outcome)
        if node['kind'] != 'review':
            c.pop('nextActionKey', None)
        number = len(c['attempts']) + 1
        _need(number <= 128, 'Campaign attempt history is full; preserve it for owner disposition.')
        c['attempts'].append(dict(number=number, deliveryId=delivery['id'], activityId=node['id'],
                                  attempt=receipt['attempt'], session=receipt['session'], actionKey=request['actionKey']))
        c['campaign']['observations'].append(dict(outcomeId=outcome, kind='review' if node['kind'] == 'review' else 'activity', session=receipt['session'],
            attempt=number, activityId=node['id'], graphRevision=delivery['scopeSha256'],
            resourceDelta={'tokens': None, 'elapsedSeconds': None}))


def change_orchestration(document, delivery, request, *, bind_evidence, bind_sources, bind_authority, check_reference, at, read_reference=None, retain_sources=None):
    _need(native_graph(delivery) is not None, 'A frozen Native execution plan is required; historical scopes are not migrated.')
    graph = native_graph(delivery)
    action = request.get('action')
    common = ('deliveryId', 'action', 'coordinatorSession')
    _need(delivery['status'] not in {'accepted', 'cancelled'}, 'Historical Native deliveries are immutable.')
    if action == 'activate':
        _fields(request, common + ('dispatchers', 'evidence'), ('previousCoordinatorSession',), label='Activation request')
        _need(delivery['status'] == 'in_progress', 'Activation requires approved work in progress.')
        previous = delivery.get('orchestrationActivation')
        if previous:
            _need(request.get('previousCoordinatorSession') == previous['coordinatorSession'], 'Resume requires the exact previous coordinator binding.')
            delivery.setdefault('orchestrationActivationHistory', []).append(copy.deepcopy(previous))
        else:
            _need(request['coordinatorSession'] == graph['coordinator']['session'], 'Coordinator differs from frozen scope.')
        dispatchers = copy.deepcopy(request['dispatchers'])
        _need(isinstance(dispatchers, list) and 1 <= len(dispatchers) <= 8, 'Supply actual coordinator and upstream dispatchers.')
        for actor in dispatchers:
            _fields(actor, ('session', 'capability', 'evidence'), label='Dispatcher')
            actor['evidence'] = bind_evidence(actor['evidence'])
        delivery['orchestrationActivation'] = dict(scopeSha256=delivery['scopeSha256'],
            coordinatorSession=request['coordinatorSession'], dispatchers=dispatchers,
            evidence=bind_evidence(request['evidence']), at=at)
        store = document.setdefault('orchestration', dict(version=1, campaigns=[]))
        for outcome in graph['outcomes']:
            if campaign_for(document, outcome['id']) is None:
                store['campaigns'].append(dict(outcomeId=outcome['id'],
                    campaign=dict(version=1, outcomeId=outcome['id'],
                                  attemptBudget=graph['policy']['checkpointAttemptBudget'],
                                  waitingOriginalGoals=waiting_goals(document), observations=[]),
                    attempts=[], observations=[], decisions=[]))
                if 'noProgressLimit' in graph['policy']:
                    store['campaigns'][-1]['campaign']['noProgressLimit'] = graph['policy']['noProgressLimit']
        return
    _activation(delivery, request.get('coordinatorSession'))
    _need(request.get('outcomeId') in {o['id'] for o in graph['outcomes']}, 'Outcome is outside frozen scope.')
    c = campaign_for(document, request['outcomeId'])
    _need(c is not None, 'Original campaign is not activated.')
    if action == 'observe':
        _fields(request, common + ('outcomeId', 'observation', 'evidence', 'sourcePaths'), ('sourceCommit',), label='Observation request')
        observation = copy.deepcopy(request['observation'])
        _validate_observation(observation, c['outcomeId'], c['campaign']['observations'][-1]['attempt'] if c['campaign']['observations'] else 0)
        if observation['kind'] == 'baseline' and not c['attempts']:
            _need(observation['attempt'] == 0, 'Initial baseline must precede the first actual attempt.')
            _need(observation['session'] == request['coordinatorSession'], 'Baseline session differs from coordinator.')
        else:
            _need(bool(c['attempts']) and observation['attempt'] == len(c['attempts']), 'Observation is not from the current campaign attempt.')
            attempt = c['attempts'][-1]
            _need(attempt['deliveryId'] == delivery['id'] and observation['session'] == attempt['session']
                  and observation.get('activityId') == attempt['activityId'], 'Observation worker/activity binding is stale.')
            receipt = next(r for r in delivery['activityReceipts'] if r['activityId'] == attempt['activityId'] and r['attempt'] == attempt['attempt'])
            if observation['kind'] in {'baseline', 'integrated_progress', 'component_pass', 'falsifier'}:
                _need(receipt['status'] == 'completed', 'Positive observation needs a completed, evidenced actual attempt.')
        _need(observation not in c['campaign']['observations'], 'Observation has already been recorded.')
        sources = bind_sources(request['sourcePaths'])
        allowed = next(o['paths'] for o in graph['outcomes'] if o['id'] == c['outcomeId'])
        _need(all(any(r['path'] == p or r['path'].startswith(p + '/') for p in allowed) for r in sources),
              'Observation source exceeds original outcome ownership.')
        if c['attempts'] and observation['kind'] in {'baseline', 'integrated_progress', 'component_pass', 'falsifier'}:
            _need(sources == receipt.get('sourceBindings'), 'Observation sources differ from the completed actual attempt.')
        evidence = bind_evidence(request['evidence'])
        if observation['kind'] in {'baseline', 'integrated_progress', 'falsifier'}:
            _need(read_reference is not None, 'Observation needs a verified raw report reader.')
            expected = dict(orchestrationObservationVersion=1, deliveryId=delivery['id'],
                            scopeSha256=delivery['scopeSha256'], sourceBindingsSha256=digest(sources), observation=observation)
            matching = False
            for ref in evidence:
                try:
                    report = json.loads(read_reference(ref))
                except (ValueError, UnicodeError):
                    continue
                if report == expected:
                    matching = True
            _need(matching, 'Raw observation report must bind the exact observation, current sources and scope.')
        record = dict(observation=observation, evidence=evidence,
                      sourceBindings=sources, deliveryId=delivery['id'])
        if observation['kind'] == 'baseline' and observation['usable']:
            _need(retain_sources is not None, 'Usable baseline needs recoverable source bytes/version.')
            record['sourceCheckpoint'] = retain_sources(sources, request.get('sourceCommit'))
        _need(not any(set((r['path'], r['sha256']) for r in old['evidence']) == set((r['path'], r['sha256']) for r in record['evidence'])
                      and old['observation']['kind'] == observation['kind'] for old in c['observations']),
              'The same proof cannot be replayed as new progress.')
        c['campaign']['observations'].append(observation)
        c['observations'].append(record)
        assess_campaign(c['campaign'])
        return
    _need(action == 'decide', 'Unknown Native orchestration action.')
    _fields(request, common + ('outcomeId', 'contextSha256', 'decision', 'actionKey', 'reason', 'evidence'),
            ('authority', 'priority', 'targetOutcomeId'), 'Decision request')
    result = assessment(c, owner_priority=document.get('orchestration', {}).get('ownerPriority', []))
    _need(request['contextSha256'] == result['contextSha256'], 'Campaign changed; use current assessment context.')
    _need(request['decision'] in graph['coordinator']['permittedDecisions'], 'Decision exceeds frozen coordinator authority.')
    _text(request['reason'], 'Decision reason', 2000)
    _text(request['actionKey'], 'Changed next action', 128)
    _need(not c['attempts'] or request['actionKey'] != c['attempts'][-1]['actionKey'], 'A decision must change the actual next action.')
    decision = {k: copy.deepcopy(request[k]) for k in ('decision', 'actionKey', 'reason')}
    if request['decision'] == 'independent_work':
        _need(request.get('targetOutcomeId') in waiting_goals(document) and request['targetOutcomeId'] != c['outcomeId'],
              'Independent work requires a different waiting original outcome.')
        decision['targetOutcomeId'] = request['targetOutcomeId']
    decision.update(contextSha256=_decision_context(c, document.get('orchestration', {}).get('ownerPriority', [])), evidence=bind_evidence(request['evidence']), at=at)
    if result['budgetExhausted'] or c.get('ownerChoicePending') or request['decision'] == 'reprioritize':
        _need('authority' in request and request['authority'].get('kind') == 'user', 'A scoped actual owner decision is required to change budget or priority.')
        decision['authority'] = bind_authority(request['authority'], request)
        c['ownerChoicePending'] = False
        if result['budgetExhausted']:
            c['checkpointStart'] = result['totalAttempts']
    if 'priority' in request:
        _need(request['decision'] == 'reprioritize' and isinstance(request['priority'], list)
              and set(request['priority']) <= set(c['campaign']['waitingOriginalGoals']), 'Priority must retain original waiting goals.')
        document['orchestration']['ownerPriority'] = copy.deepcopy(request['priority'])
        decision['priority'] = copy.deepcopy(request['priority'])
    if request['decision'] in {'continue_bounded', 'change_baseline'}:
        c['nextActionKey'] = request['actionKey']
    if request['decision'] == 'request_owner_choice':
        c['ownerChoicePending'] = True
    decision['contextSha256'] = _decision_context(c, document.get('orchestration', {}).get('ownerPriority', []))
    c['decisions'].append(decision)


def summary(document, delivery=None):
    relevant = {o['id'] for o in native_graph(delivery)['outcomes']} if delivery and native_graph(delivery) else None
    items = []
    for c in campaigns(document):
        if relevant is not None and c['outcomeId'] not in relevant:
            continue
        item = assessment(c, owner_priority=document.get('orchestration', {}).get('ownerPriority', []))
        current = delivery or next((d for d in document['deliveries']
            if d['status'] not in {'accepted', 'cancelled'} and native_graph(d)
            and c['outcomeId'] in {o['id'] for o in native_graph(d)['outcomes']}), None)
        baseline = next((r for r in reversed(c['observations'])
                         if r['observation']['kind'] == 'baseline' and r['observation']['usable']), None)
        item['latestUsableSourceCheckpoint'] = (dict(kind=baseline['sourceCheckpoint']['kind'],
            sourcePaths=[r['path'] for r in baseline['sourceBindings']],
            commit=baseline['sourceCheckpoint'].get('commit')) if baseline else None)
        if current and current.get('orchestrationActivation'):
            item['ownerDecisionContext'] = dict(orchestrationDecisionVersion=1, operation='orchestration_decision',
                scopeSha256=current['scopeSha256'], outcomeId=c['outcomeId'], contextSha256=item['contextSha256'],
                coordinatorSession=current['orchestrationActivation']['coordinatorSession'], decision=None, actionKey=None)
        items.append(item)
    return dict(version=1, campaigns=items,
                waitingOriginalGoals=waiting_goals(document),
                ownerPriority=copy.deepcopy(document.get('orchestration', {}).get('ownerPriority', [])),
                authorityGranted=False, identityAuthenticated=False,
                boundary='The sole ledger fences supported Native starts and dispatch; external host calls must use its receipts.')
