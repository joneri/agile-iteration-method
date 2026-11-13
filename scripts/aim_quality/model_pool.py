"""Approval-bound child model choices; declarations are not host authentication.

Budget allowances cover recorded child work starts and conservative cost
reservations, not provider billing. Historical receipts retain their start-time
estimates; later observed overruns prevent new work without rewriting history.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math

def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _fields(value, required, optional=()):
    _need(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional),
          'Model-pool data has missing or unsupported fields.')


def _text(value, label, maximum=2000):
    _need(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
          label + ' must be bounded nonempty text.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _amount(value):
    _need(type(value) in (int, float) and (type(value) is int or math.isfinite(value)) and value >= 0,
          'Model cost must be a finite nonnegative number; unknown is not zero.')
    return Fraction(str(value))


def _display(value):
    # Every input is a finite JSON decimal, hence denominators contain only 2/5.
    # Render with integers: approximate Decimal division must not feed a guard.
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2; twos += 1
    while denominator % 5 == 0:
        denominator //= 5; fives += 1
    _need(denominator == 1, 'Model cost is not a finite decimal.')
    places = max(twos, fives)
    scaled = value.numerator * (2 ** (places - twos)) * (5 ** (places - fives))
    if not places:
        return str(scaled)
    sign = '-' if scaled < 0 else ''
    digits = str(abs(scaled)).rjust(places + 1, '0')
    return sign + digits[:-places] + '.' + digits[-places:]


def _cost(value, limit=None):
    _fields(value, ('unit', 'amount'))
    _text(value['unit'], 'Explicit cost unit', 64)
    result = _amount(value['amount'])
    if limit:
        _need(value['unit'] == limit['unit'], 'Model cost unit differs from the approved allowance.')
    return result


def validate_pool(pool):
    _fields(pool, ('version', 'choices', 'budget'))
    _need(type(pool['version']) is int and pool['version'] == 1, 'Unsupported model-pool version.')
    choices = pool['choices']
    _need(isinstance(choices, list) and 1 <= len(choices) <= 32, 'Supply 1–32 approved model/effort pairs.')
    ids, pairs = set(), set()
    for choice in choices:
        _fields(choice, ('id', 'model', 'reasoningEffort'))
        for field in ('id', 'model', 'reasoningEffort'):
            _text(choice[field], 'Approved choice ' + field, 128)
        pair = (choice['model'], choice['reasoningEffort'])
        _need(choice['id'] not in ids and pair not in pairs, 'Approved choice IDs and model/effort pairs must be unique.')
        ids.add(choice['id']); pairs.add(pair)
    budget = pool['budget']
    _fields(budget, ('maxStarts',), ('costLimit',))
    _need(type(budget['maxStarts']) is int and 0 <= budget['maxStarts'] <= 256,
          'Model-pool maxStarts must be an integer from 0 to 256.')
    if 'costLimit' in budget:
        _cost(budget['costLimit'])
    return pool


def _children(records):
    return [record for record in records if 'modelSelection' in record]


def usage(pool, records, *, actual=True):
    children = _children(records)
    limit = pool['budget'].get('costLimit')
    estimated, accounted, unknown = Fraction(0), Fraction(0), 0
    for record in children:
        estimate = record['modelSelection'].get('estimatedCost')
        reports = record.get('modelObservationHistory', []) + ([record['modelObservation']] if 'modelObservation' in record else [])
        observed = [r['actualCost'] for r in reports if r['actualCost'] is not None]
        unknown += not observed
        if limit:
            cost = _cost(estimate, limit)
            estimated += cost
            accounted += max([cost, *(_cost(c, limit) for c in observed)]) if actual else cost
    return dict(usedStarts=len(children), remainingStarts=max(0, pool['budget']['maxStarts'] - len(children)),
                reservedEstimate=_display(estimated) if limit else None,
                accountedCost=_display(accounted) if limit else None,
                remainingCost=_display(max(Fraction(0), _cost(limit) - accounted)) if limit else None,
                costUnit=limit['unit'] if limit else None, unknownActualCosts=unknown,
                actualCostKnown=unknown == 0, billingLimitVerified=False)


def _check_allowance(pool, records, estimate, *, actual):
    current = usage(pool, records, actual=actual)
    _need(current['remainingStarts'] > 0, 'Approved model-pool start allowance is exhausted; retries do not renew it.')
    limit = pool['budget'].get('costLimit')
    if estimate is not None:
        _cost(estimate, limit)
    if limit:
        _need(estimate is not None, 'An explicit cost estimate is required; unknown cost is not free.')
        _need(Fraction(current['accountedCost']) + _cost(estimate, limit) <= _cost(limit),
              'Approved model-pool cost allowance is exhausted or overrun.')


def _selection(pool, selection, records, *, actual, stored=False):
    _fields(selection, ('choiceId', 'task', 'risk', 'budgetReason'),
            ('estimatedCost', 'poolSha256', 'requested', 'spawnRequest') if stored else ('estimatedCost',))
    for key in ('choiceId', 'task', 'risk', 'budgetReason'):
        _text(selection[key], 'Model selection ' + key)
    choice = next((c for c in pool['choices'] if c['id'] == selection['choiceId']), None)
    _need(choice is not None, 'Model selection is outside the approved pool.')
    _check_allowance(pool, records, selection.get('estimatedCost'), actual=actual)
    result = {key: copy.deepcopy(selection[key]) for key in ('choiceId', 'task', 'risk', 'budgetReason', 'estimatedCost') if key in selection}
    result.update(poolSha256=digest(pool),
                  requested={key: choice[key] for key in ('model', 'reasoningEffort')},
                  spawnRequest=dict(model=choice['model'], reasoning_effort=choice['reasoningEffort'], fork_turns='none'))
    if stored:
        _need(selection == result, 'Recorded model selection differs from the approved pair or launch parameters.')
    return result


def prepare_selection(delivery, request):
    pool = delivery['executionPlan'].get('modelPool')
    if pool is None:
        _need('modelSelection' not in request and 'modelObservation' not in request,
              'Model selection requires an explicitly approved model pool.')
        return None
    coordinator = request.get('coordinatorSession')
    _text(coordinator, 'Actual coordinating session', 128)
    if request['session'] == coordinator:
        _need('modelSelection' not in request, 'Model pools select children, not the coordinator or its model.')
        return None
    _need(delivery['executionPlan']['delegationAllowed'], 'A model pool does not authorize forbidden subagent delegation.')
    _need('modelSelection' in request, 'Choose an approved model/effort pair for this child activity.')
    return _selection(pool, request['modelSelection'], delivery.get('activityReceipts', []), actual=True)


def unknown_observation():
    return dict(source='unknown', dispatchAccepted=None, model=None, reasoningEffort=None,
                actualCost=None, evidence=[])


def _validate_observed(value, pool):
    _fields(value, ('source', 'dispatchAccepted', 'model', 'reasoningEffort', 'actualCost', 'evidence'))
    _need(value['source'] in ('host', 'worker', 'unknown'), 'Unknown model-observation source.')
    _need(value['dispatchAccepted'] is None or type(value['dispatchAccepted']) is bool,
          'Host dispatch acceptance must be true, false or unknown.')
    for field in ('model', 'reasoningEffort'):
        if value[field] is not None:
            _text(value[field], 'Reported ' + field, 128)
    if value['actualCost'] is not None:
        _cost(value['actualCost'], pool['budget'].get('costLimit'))
    _need(isinstance(value['evidence'], list) and len(value['evidence']) <= 1,
          'Model observation requires at most one typed evidence artifact.')
    if value['source'] == 'unknown':
        _need(value['model'] is None and value['reasoningEffort'] is None and value['actualCost'] is None,
              'Unknown model observation cannot assert actual settings or cost.')
    if value != unknown_observation():
        _need(bool(value['evidence']), 'Reported model settings, cost or acceptance require attempt-bound evidence.')


def read_observation(delivery, receipt, reference, read_reference):
    payload = read_reference(reference)
    _need(len(payload.encode() if isinstance(payload, str) else payload) <= 16384,
          'Model-observation evidence exceeds 16 KiB.')
    try:
        def unique_object(items):
            value = {}
            for key, item in items:
                _need(key not in value, 'Duplicate field in model-observation evidence.')
                value[key] = item
            return value
        report = json.loads(payload, object_pairs_hook=unique_object)
    except (ValueError, TypeError) as exc:
        raise ValueError('Model observation requires typed attempt-bound JSON evidence.') from exc
    keys = ('modelObservationVersion', 'deliveryId', 'scopeSha256', 'activityId', 'session', 'attempt',
            'source', 'dispatchAccepted', 'model', 'reasoningEffort', 'actualCost')
    _fields(report, keys)
    expected = dict(modelObservationVersion=1, deliveryId=delivery['id'], scopeSha256=delivery['scopeSha256'],
                    activityId=receipt['activityId'], session=receipt['session'], attempt=receipt['attempt'])
    _need(type(report['modelObservationVersion']) is int and type(report['attempt']) is int
          and all(report[k] == v for k, v in expected.items()),
          'Model-observation evidence refers to another scope, child or attempt.')
    result = {k: copy.deepcopy(report[k]) for k in ('source', 'dispatchAccepted', 'model', 'reasoningEffort', 'actualCost')}
    result['evidence'] = [copy.deepcopy(reference)]
    _validate_observed(result, delivery['executionPlan']['modelPool'])
    return result


def observation_mismatch(selection, observation):
    return (observation['dispatchAccepted'] is False
            or any(observation[k] is not None and observation[k] != selection['requested'][k]
                   for k in ('model', 'reasoningEffort')))


def record_observation(receipt, observation):
    previous = receipt.get('modelObservation')
    if previous is not None and previous != observation:
        history = receipt.setdefault('modelObservationHistory', [])
        _need(len(history) < 64, 'Model-observation history is full; preserve evidence and escalate before further updates.')
        history.append(copy.deepcopy(previous))
    receipt['modelObservation'] = copy.deepcopy(observation)


def observation_update(request):
    return request.get('status') == 'running' and 'modelObservation' in request


def validate_receipts(delivery, *, read_reference=None):
    pool = delivery.get('executionPlan', {}).get('modelPool')
    records = delivery.get('activityReceipts', [])
    if pool is None:
        _need(not any(any(k in r for k in ('modelSelection','modelObservation','modelObservationHistory')) for r in records),
              'Unapproved model-pool receipts are not allowed.')
        return
    validate_pool(pool)
    coordinators = {delivery['executionPlan']['orchestration']['coordinator']['session']}
    coordinators.update(a['coordinatorSession'] for a in delivery.get('orchestrationActivationHistory', []))
    if 'orchestrationActivation' in delivery:
        coordinators.add(delivery['orchestrationActivation']['coordinatorSession'])
    previous = []
    for receipt in records:
        _need(receipt.get('coordinatorSession') in coordinators, 'Model-pool receipt has no retained coordinator binding.')
        child = receipt['session'] != receipt['coordinatorSession']
        if child:
            _need('modelSelection' in receipt, 'Pooled child receipt has no approved selection.')
            _selection(pool, receipt['modelSelection'], previous, actual=False, stored=True)
            observation = receipt.get('modelObservation')
            history = receipt.get('modelObservationHistory', [])
            _need(isinstance(history, list) and len(history) <= 64, 'Model-observation history must be bounded.')
            for observation in history + ([observation] if observation is not None else []):
                _validate_observed(observation, pool)
                if read_reference and observation['evidence']:
                    _need(read_observation(delivery, receipt, observation['evidence'][0], read_reference) == observation,
                          'Reported model observation differs from its bound evidence.')
            _need(receipt['status'] == 'running' or 'modelObservation' in receipt,
                  'Terminated child attempts must preserve reported or unknown configuration.')
            if receipt['status'] == 'completed':
                _need(not any(observation_mismatch(receipt['modelSelection'], o)
                              for o in history + [receipt['modelObservation']]),
                      'Known child model mismatch cannot be successful completion.')
        else:
            _need(not any(k in receipt for k in ('modelSelection','modelObservation','modelObservationHistory')),
                  'Coordinator work cannot claim a selected child model.')
        previous.append(receipt)


def projection(delivery, receipt=None):
    pool = delivery.get('executionPlan', {}).get('modelPool')
    if pool is None:
        return None
    result = dict(poolSha256=digest(pool), choices=copy.deepcopy(pool['choices']),
                  budget=copy.deepcopy(pool['budget']), usage=usage(pool, delivery.get('activityReceipts', [])),
                  authority='approved-delivery-plan', hostIdentityAuthenticated=False)
    if receipt and 'modelSelection' in receipt:
        result['selection'] = copy.deepcopy(receipt['modelSelection'])
        result['observation'] = copy.deepcopy(receipt.get('modelObservation', unknown_observation()))
    return result
