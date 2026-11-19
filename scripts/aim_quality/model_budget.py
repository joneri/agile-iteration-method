"""Scoped, append-only model-start allowances. Original pools remain frozen."""
from __future__ import annotations

import copy
import json

from .delivery_policy import validate_authority_binding
from .model_pool import _fields, _need, digest, effective_budget, usage


def _starts(records):
    keys = ('activityId', 'session', 'attempt', 'scopeSha256', 'coordinatorSession', 'modelSelection')
    return [{key: r[key] for key in keys if key in r} for r in records]


def _grant(document, reference):
    from .orchestration_runtime import campaign_for
    _fields(reference, ('outcomeId', 'decisionSha256'))
    campaign = campaign_for(document, reference['outcomeId'])
    _need(campaign is not None, 'Resource grant campaign is missing.')
    decision = next((d for d in campaign['decisions'] if digest(d) == reference['decisionSha256']), None)
    _need(decision is not None and 'additionalAttempts' in decision, 'Resource grant is missing or has no finite allowance.')
    return campaign, decision


def context(document, delivery, request):
    from .orchestration_runtime import _activation, _decision_context, _delegated_grants
    _fields(request, ('deliveryId', 'coordinatorSession', 'additionalStarts', 'reason'), ('resourceGrant', 'ownerKind'))
    _need(delivery['status'] not in {'planned', 'accepted', 'cancelled'}, 'Model budget requires an approved active delivery.')
    activation = _activation(delivery, request['coordinatorSession'])
    _need(request['coordinatorSession'] == activation['coordinatorSession'], 'Only the current coordinator may request a model budget decision.')
    pool = delivery.get('executionPlan', {}).get('modelPool')
    _need(pool is not None, 'No approved model pool exists.')
    records = delivery.get('activityReceipts', [])
    current = usage({**pool, 'budget': effective_budget(delivery, records)}, records)
    _need(current['remainingStarts'] == 0, 'Use the remaining model allowance before requesting an extension.')
    count = request['additionalStarts']
    _need(type(count) is int and 1 <= count <= 128, 'Additional model starts must be an integer from 1 to 128.')
    history = delivery.get('modelPoolExtensions', [])
    _need(len(history) < 128 and pool['budget']['maxStarts'] + sum(r['context']['additionalStarts'] for r in history) + count <= 256,
          'Model-start allowance exceeds its retained storage boundary.')
    _need(isinstance(request['reason'], str) and 0 < len(request['reason'].strip()) <= 2000, 'A bounded model budget reason is required.')
    owner = delivery.get('deliveryPolicy', {}).get('owner', {'kind': 'human'})
    kind = request.get('ownerKind', owner['kind'])
    _need(isinstance(kind, str) and kind in {'agent', 'user', 'human'}, 'Unknown model budget owner kind.')
    delegated = kind == 'agent'
    expected_owner = {k: owner[k] for k in ('kind', 'id', 'session')} if delegated and owner['kind'] == 'agent' else {'kind': 'user'}
    if delegated:
        _need(owner['kind'] == 'agent' and 'orchestrate' in owner['decisions'], 'Model budget resources were not delegated.')
        _need(owner['session'] in {a['session'] for a in activation['dispatchers']}, 'Activate the actual upstream model budget owner.')
    linked = request.get('resourceGrant')
    if linked:
        campaign, grant = _grant(document, linked)
        _need(grant.get('deliveryId') == delivery['id'], 'Resource grant must belong to this delivery.')
        actual_owner = {k: grant['authority'][k] for k in expected_owner}
        _need(actual_owner == expected_owner, 'Resource grant belongs to a different owner.')
        if delegated:
            _need(grant.get('delegation') == owner['mandate'], 'Resource grant belongs to a different mandate.')
        renewals = [d for d in campaign['decisions'] if 'additionalAttempts' in d]
        _need(renewals[-1] == grant, 'Only the current resource grant can fund a pool extension.')
        anchor = grant.get('grantReceiptCount')
        if anchor is None:
            graph = delivery['executionPlan']['orchestration']
            _need(all(linked['outcomeId'] in node['outcomeIds'] for node in graph['nodes'])
                  and grant['contextSha256'] == _decision_context(campaign, document.get('orchestration', {}).get('ownerPriority', [])),
                  'Historical resource grant consumption cannot be established; retain it and obtain a separately authorized allowance.')
            spent = 0
        else:
            _need(type(anchor) is int and 0 <= anchor <= len(records), 'Resource grant start boundary is invalid.')
            spent = len(records) - anchor
        _need(count <= grant['additionalAttempts'] - spent, 'Model extension exceeds the remaining linked resource grant.')
        for other in document['deliveries']:
            _need(not any(r['context'].get('resourceGrant') == linked for r in other.get('modelPoolExtensions', [])), 'Resource grant already funds a model budget extension.')
    elif delegated:
        _need(count <= owner['maxAdditionalAttempts'] - _delegated_grants(document, owner), 'Model extension exceeds the remaining delegated resource allowance.')
    result = dict(deliveryId=delivery['id'], scopeSha256=delivery['scopeSha256'], poolSha256=digest(pool),
                  coordinatorSession=request['coordinatorSession'], activationSha256=digest(activation),
                  budgetRevision=len(history), previousExtensionsSha256=digest(history),
                  receiptCount=len(records), startsSha256=digest(_starts(records)), usage=current,
                  additionalStarts=count, reason=request['reason'], owner=expected_owner,
                  delegation=copy.deepcopy(owner['mandate']) if delegated else None,
                  delegatedGrants=_delegated_grants(document, owner) if delegated else None)
    if linked:
        result['resourceGrant'] = copy.deepcopy(linked)
    return result


def decision_payload(value):
    return dict(modelPoolBudgetDecisionVersion=1, operation='extend_model_pool', context=value, decision='approved')


def validate_extensions(document, read_reference=None):
    used_grants = set()
    for delivery in document['deliveries']:
        history = delivery.get('modelPoolExtensions', [])
        _need(isinstance(history, list) and len(history) <= 128, 'Model budget history is invalid.')
        pool = delivery.get('executionPlan', {}).get('modelPool')
        records = delivery.get('activityReceipts', [])
        previous = []
        total = pool['budget']['maxStarts'] if pool else 0
        for record in history:
            _fields(record, ('context', 'authority', 'at'))
            value, authority = record['context'], record['authority']
            _fields(value, ('deliveryId', 'scopeSha256', 'poolSha256', 'coordinatorSession',
                            'activationSha256', 'budgetRevision', 'previousExtensionsSha256',
                            'receiptCount', 'startsSha256', 'usage', 'additionalStarts', 'reason',
                            'owner', 'delegation', 'delegatedGrants'), ('resourceGrant',))
            _need(pool is not None and value['deliveryId'] == delivery['id'] and value['scopeSha256'] == delivery['scopeSha256']
                  and value['poolSha256'] == digest(pool), 'Model extension lost its original frozen pool/scope.')
            _need(value['budgetRevision'] == len(previous) and value['previousExtensionsSha256'] == digest(previous), 'Model budget history was reordered or replaced.')
            anchor = value['receiptCount']
            _need(type(anchor) is int and 0 <= anchor <= len(records)
                  and value['startsSha256'] == digest(_starts(records[:anchor])), 'Model budget start history changed.')
            prior_delivery = {**delivery, 'modelPoolExtensions': previous}
            prior_usage = usage({**pool, 'budget': effective_budget(prior_delivery, records[:anchor])}, records[:anchor])
            _need(prior_usage['remainingStarts'] == 0, 'Overlapping model budget allowances are not supported; spend the prior allowance first.')
            count = value['additionalStarts']
            _need(type(count) is int and 1 <= count <= 128, 'Invalid recorded model allowance.')
            total += count
            _need(total <= 256, 'Retained model allowance exceeds its storage boundary.')
            validate_authority_binding(authority, delivery.get('deliveryPolicy'), 'orchestrate')
            _need(authority['scopeSha256'] == digest(value), 'Model budget answer is stale or bound to a different context.')
            expected_owner = {k: authority[k] for k in value['owner']}
            _need(expected_owner == value['owner'], 'Model budget answer has the wrong owner.')
            if authority['kind'] == 'agent':
                from .orchestration_runtime import _delegated_grants
                owner = delivery['deliveryPolicy']['owner']
                _need(_delegated_grants(document, owner) <= owner['maxAdditionalAttempts'], 'Recorded model grants exceed the cumulative delegated allowance.')
                _need(value['delegation'] == delivery['deliveryPolicy']['owner']['mandate'], 'Model budget mandate changed.')
            if value.get('resourceGrant'):
                key = digest(value['resourceGrant'])
                _need(key not in used_grants, 'Resource grant was reused for multiple pool extensions.')
                used_grants.add(key)
                _, grant = _grant(document, value['resourceGrant'])
                _need(grant.get('deliveryId') == delivery['id'] and count <= grant['additionalAttempts'], 'Model budget lost its linked resource grant.')
            if read_reference:
                raw = read_reference({k: authority[k] for k in ('path', 'sha256')})
                def unique(items):
                    result = {}
                    for key, item in items:
                        _need(key not in result, 'Duplicate model budget decision keys.')
                        result[key] = item
                    return result
                _need(json.loads(raw, object_pairs_hook=unique) == decision_payload(value), 'Model budget answer must approve this exact context.')
            previous.append(record)


def apply(document, delivery, request, *, bind_evidence, read_reference, at):
    _fields(request, ('deliveryId', 'coordinatorSession', 'additionalStarts', 'reason', 'authority'), ('resourceGrant', 'ownerKind'))
    raw = {k: v for k, v in request.items() if k != 'authority'}
    value = context(document, delivery, raw)
    authority = copy.deepcopy(request['authority'])
    validate_authority_binding(authority, delivery.get('deliveryPolicy'), 'orchestrate')
    _need(authority['scopeSha256'] == digest(value), 'Model budget answer has a stale context.')
    bind_evidence([{k: authority[k] for k in ('path', 'sha256')}])
    if value['delegation']:
        bind_evidence([value['delegation']])
    delivery.setdefault('modelPoolExtensions', []).append(dict(context=value, authority=authority, at=at))
    validate_extensions(document, read_reference)
