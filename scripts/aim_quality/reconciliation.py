"""Present-authorized acceptance of existing Native work; never past gate repair.

All identity fields are host declarations, not authentication. Only the canonical
Story helper commits this journal and the corresponding original Story statuses.
"""
from __future__ import annotations
import copy
import json


def _api():
    import aim_stories
    return aim_stories


def _json(repo, ref, cache):
    s = _api()
    s._ref(repo, ref, cache=cache)
    def pairs(items):
        result = {}
        for key, value in items:
            s.require(key not in result, 'Duplicate reconciliation evidence JSON key.')
            result[key] = value
        return result
    return json.loads(s.read_evidence(repo, ref['path']), object_pairs_hook=pairs)


CONTEXT_FIELDS = ('id', 'storyIds', 'originalPlan', 'reviewEvidence', 'packageEvidence',
                  'acceptanceEvidence', 'authorizationEvidence', 'sourcePaths',
                  'acceptanceMapping', 'deviation', 'limitations', 'implementers')


def _selection(document, ids):
    s = _api()
    s.require(isinstance(ids, list) and 1 <= len(ids) <= 256, 'Select 1–256 original Native Stories.')
    s.unique(ids, 'reconciliation Stories')
    stories = [s._by_id(document, 'stories', sid) for sid in ids]
    # Never steal an existing delivery, including an unapproved or cancelled plan.
    allocated = {x['id'] for d in document['deliveries'] for x in d['stories']}
    s.require(not allocated.intersection(ids), 'Reconciliation requires Stories without any original delivery.')
    s.require(all(x['status'] == 'ready' for x in stories), 'Reconciliation requires ready undelivered Stories.')
    s.require(not any(x.get('corrects') for x in stories), 'Use the existing correction workflow for linked corrective Stories.')
    for story in stories:
        s.require(all(s._by_id(document, 'stories', dep)['status'] == 'done' or dep in ids
                      for dep in story.get('dependsOn', [])), 'Unresolved Story dependencies prevent reconciliation.')
        s.require(all(p['resolved'] or p.get('kind') == 'owner_assessment' or not p.get('blocking', True)
                      for p in story.get('prerequisites', [])), 'Unresolved blocking prerequisites prevent reconciliation.')
    epics = [s._by_id(document, 'epics', eid) for eid in dict.fromkeys(x['epicId'] for x in stories)]
    intents = [s._by_id(document, 'intents', iid) for iid in dict.fromkeys(x['intentId'] for x in epics)]
    return dict(stories=copy.deepcopy(stories), epics=copy.deepcopy(epics), intents=copy.deepcopy(intents))


def build_context(repo, document, request, cache):
    s = _api()
    s.fields(request, CONTEXT_FIELDS)
    s.identity(request['id'], 'REC')
    scope = _selection(document, request['storyIds'])
    s.text(request['deviation'], 'Missing original activation and execution deviation', 4000)
    s.require(isinstance(request['limitations'], list) and 1 <= len(request['limitations']) <= 32,
              'Retain explicit evidence limitations.')
    for limitation in request['limitations']:
        s.text(limitation, 'Reconciliation limitation', 4000)
    for key in ('originalPlan', 'acceptanceEvidence', 'authorizationEvidence'):
        s._ref(repo, request[key], product=(key == 'originalPlan'), cache=cache)
    for key in ('reviewEvidence', 'packageEvidence'):
        s._refs(repo, request[key], cache=cache)
    refs = [request['originalPlan'], request['acceptanceEvidence'], request['authorizationEvidence'],
            *request['reviewEvidence'], *request['packageEvidence']]
    s.require(len({r['path'] for r in refs}) == len(refs), 'Original plan, review, package, acceptance and present authorization need separate evidence.')
    auth = _json(repo, request['authorizationEvidence'], cache)
    s.require(auth.get('kind') == 'actual_user_authorization_for_present_reconciliation'
              and auth.get('storyIds') == request['storyIds'],
              'Present human authorization must explicitly name exactly these original Stories.')
    s.text(auth.get('originalMessage'), 'Actual present human instruction', 8000)
    s.require(auth.get('priorActualProductApproval') == request['acceptanceEvidence']['path'],
              'Present authorization must identify the actual prior product approval.')
    approval = _json(repo, request['acceptanceEvidence'], cache)
    s.require(approval.get('kind') in {'actual_human_product_feedback', 'actual_human_playtest_feedback'} and approval.get('decision') == 'approved',
              'Prior actual human product approval is required.')
    s.text(approval.get('originalMessage'), 'Actual product approval', 8000)
    mapping = request['acceptanceMapping']
    s.require(isinstance(mapping, dict) and set(mapping) == set(request['storyIds'])
              and all(isinstance(v, str) and v for v in mapping.values())
              and len(set(mapping.values())) == len(mapping)
              and isinstance(approval.get('scope'), list)
              and len(approval['scope']) == len(mapping)
              and set(mapping.values()) == set(approval['scope']),
              'Map every original Story to the exact actual approved product scope.')
    sources = s._source_bindings(repo, request['sourcePaths'], cache=cache)
    # Validate declared implementer identities using the same independent review
    # contract later; preserve them inside the digest now.
    s.require(isinstance(request['implementers'], list) and 1 <= len(request['implementers']) <= 32,
              'Identify the actual implementers.')
    for actor in request['implementers']:
        s.fields(actor, ('id', 'session'))
        for key in ('id', 'session'):
            s.text(actor[key], 'Actual implementer '+key, 128)
    context = dict(reconciliationVersion=1, **copy.deepcopy(request), **scope,
                   sourceBindings=sources, originalActivation='missing', operation='reconcile')
    return dict(context=context, scopeSha256=s.digest(context))


def validate_records(document):
    """Pure journal validation and association, without fresh product reads."""
    s = _api()
    records = document.get('reconciliations', [])
    s.require(isinstance(records, list) and len(records) <= 256, 'Invalid reconciliation journal.')
    s.unique([r.get('id') for r in records], 'reconciliation IDs')
    owned = {}
    for record in records:
        s.fields(record, ('id', 'status', 'recordedAt', 'scopeSha256', 'context', 'request', 'requestSha256'))
        s.require(record['status'] == 'accepted', 'Unsupported reconciliation disposition.')
        s.text(record['recordedAt'], 'Present reconciliation timestamp', 64)
        context = record['context']; request = record['request']
        s.fields(context, ('reconciliationVersion', *CONTEXT_FIELDS, 'stories', 'epics', 'intents',
                           'sourceBindings', 'originalActivation', 'operation'))
        s.require(context['reconciliationVersion'] == 1 and context['originalActivation'] == 'missing'
                  and context['operation'] == 'reconcile', 'Reconciliation cannot assert past activation.')
        s.require(record['scopeSha256'] == s.digest(context), 'Reconciliation scope fingerprint is invalid.')
        s.require(record['requestSha256'] == s.digest(request), 'Reconciliation request fingerprint is invalid.')
        s.fields(request, ('context', 'scopeSha256', 'decisionEvidence', 'reviewRecord'))
        s.require(request['context'] == {k:context[k] for k in CONTEXT_FIELDS}
                  and request['scopeSha256'] == record['scopeSha256']
                  and record['id'] == context['id'], 'Reconciliation identity or scope mismatch.')
        s.identity(record['id'], 'REC')
        ids = context['storyIds']; s.unique(ids, 'reconciled Stories')
        s.require(ids == [x['id'] for x in context['stories']], 'Reconciliation Story snapshots do not match.')
        s.require({x['epicId'] for x in context['stories']} == {x['id'] for x in context['epics']}
                  and {x['intentId'] for x in context['epics']} == {x['id'] for x in context['intents']},
                  'Reconciliation original requirement snapshots do not match.')
        for before in context['stories']:
            current = s._by_id(document, 'stories', before['id'])
            s.require(before['status'] == 'ready' and current == {**before, 'status':'done'},
                      'Reconciled original requirements/history changed.')
            s.require(before['id'] not in owned, 'A Story has overlapping reconciliations.')
            owned[before['id']] = record
    return owned


def verify_record(repo, record, cache, *, current=False):
    s = _api(); c = record['context']; req = record['request']
    for key in ('originalPlan', 'acceptanceEvidence', 'authorizationEvidence'):
        s._ref(repo, c[key], product=(key == 'originalPlan'), cache=cache)
    for key in ('reviewEvidence', 'packageEvidence'):
        s._refs(repo, c[key], cache=cache)
    decision = _json(repo, req['decisionEvidence'], cache)
    s.fields(decision, ('reconciliationDecisionVersion', 'operation', 'id', 'scopeSha256',
                        'storyIds', 'kind', 'decision', 'authorizationEvidence', 'acceptanceEvidence', 'reason'))
    s.require(decision['reconciliationDecisionVersion'] == 1 and decision['kind'] == 'user'
              and decision['decision'] == 'accepted' and decision['operation'] == 'reconcile'
              and decision['id'] == record['id'] and decision['scopeSha256'] == record['scopeSha256']
              and decision['storyIds'] == c['storyIds']
              and decision['authorizationEvidence'] == c['authorizationEvidence']
              and decision['acceptanceEvidence'] == c['acceptanceEvidence'],
              'Actual present human reconciliation decision does not match exact identity, scope and evidence.')
    s.text(decision['reason'], 'Actual owner reconciliation assessment', 4000)
    review = _json(repo, req['reviewRecord'], cache)
    s.require(review.get('scopeSha256') == record['scopeSha256']
              and review.get('sources') == c['sourceBindings'] and review.get('implementers') == c['implementers']
              and review.get('reconciliationId') == record['id']
              and review.get('reviewEvidence') == c['reviewEvidence']
              and review.get('packageEvidence') == c['packageEvidence'],
              'Independent review must bind the exact reconciliation, sources and historical evidence.')
    expected = {x['id']: {a['id'] for a in x['acceptanceCriteria']} for x in c['stories']}
    coverage = review.get('criterionAssessment')
    s.require(isinstance(coverage, dict) and set(coverage) == set(expected), 'Review must cover exactly the original Stories.')
    for sid, criteria in expected.items():
        s.require(isinstance(coverage[sid], dict) and set(coverage[sid]) == criteria,
                  'Review must cover every original criterion.')
        for value in coverage[sid].values(): s.text(value, 'Original criterion assessment', 4000)
    from aim_quality.review import check_review
    # check_review may inspect current sources. For accepted historical journals,
    # validate its identities/findings against a reader of the retained bindings.
    by_path = {r['path']:r for r in c['sourceBindings']}
    def historical(root, ref):
        s.require(ref == by_path[ref['path']], 'Historical review source mismatch.')
        return None, True
    def fresh(root, ref):
        s._ref(repo, ref, product=True, cache=cache)
        return None, True
    assessed = check_review(repo, review, list(by_path), require_independent=True,
                            read_reference=fresh if current else historical)
    s.require(assessed['eligible'] and assessed['independentReviewDeclared'],
              'Reconciliation requires eligible independent review: ' + '; '.join(assessed['diagnostics']))


def apply(repo, document, request, cache):
    s = _api()
    s.fields(request, ('context', 'scopeSha256', 'decisionEvidence', 'reviewRecord'))
    original = request['context']; identifier = original.get('id')
    previous = next((r for r in document.get('reconciliations', []) if r['id'] == identifier), None)
    if previous:
        s.require(previous['request'] == request, 'Reconciliation ID already records a different operation.')
        verify_record(repo, previous, cache)
        return previous, False
    built = build_context(repo, document, original, cache)
    s.require(built['scopeSha256'] == request['scopeSha256'], 'Stale reconciliation scope; rebuild context from current requirements and proof.')
    record = dict(id=identifier, status='accepted', recordedAt=s.now(), context=built['context'],
                  scopeSha256=built['scopeSha256'], request=copy.deepcopy(request), requestSha256=s.digest(request))
    verify_record(repo, record, cache, current=True)
    document.setdefault('reconciliations', []).append(record)
    for sid in original['storyIds']:
        s._by_id(document, 'stories', sid)['status'] = 'done'
    return record, True
