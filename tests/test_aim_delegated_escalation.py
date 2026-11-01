"""One isolated Native handoff: routing, attributed response and finite resources."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_aim_orchestration_runtime as native
from aim_quality.orchestration_runtime import campaign_for, assessment, summary
from aim_stories import StoryError, verify_evidence


class DelegatedEscalationTests(unittest.TestCase):
    setUp = native.NativeRuntimeTests.setUp
    artifact = native.NativeRuntimeTests.artifact
    authority = native.NativeRuntimeTests.authority
    native_plan = native.NativeRuntimeTests.native_plan
    start = native.NativeRuntimeTests.start
    fail = native.NativeRuntimeTests.fail
    finish = native.NativeRuntimeTests.finish
    observe = native.NativeRuntimeTests.observe

    def mutate(self, operation, request):
        if operation == 'plan' and hasattr(self, 'owner'):
            request = {**request, 'deliveryPolicy': dict(mode='ship', owner=self.owner)}
        return native.NativeRuntimeTests.mutate(self, operation, request)

    def activate(self, delivery='DI-1', session='native-coordinator', **extra):
        proof = self.artifact('activation-'+str(self.document['revision'])+'.txt',
                              'Synthetic fixture: coordinator and upstream owner received this contract.')
        dispatchers = [dict(session=session, capability=dict(id='aim-native-orchestrator', version='4.8.0'), evidence=[proof])]
        if hasattr(self, 'owner'):
            dispatchers.append({**dispatchers[0], 'session': self.owner['session']})
        return self.mutate('orchestrate', dict(deliveryId=delivery, action='activate', coordinatorSession=session,
                           dispatchers=dispatchers, evidence=[proof], **extra))

    def exhaust(self, budget=1, cap=2, delegated=True):
        mandate = self.artifact('human-delegation.txt',
            'SYNTHETIC TEST AUTHORITY: named owner may grant at most the stated additional attempts; no acceptance.')
        self.owner = dict(kind='agent', id='owner-root', session='owner-session', mandate=mandate,
                          decisions=['orchestrate'] if delegated else ['accept'])
        if delegated:
            self.owner['maxAdditionalAttempts'] = cap
        self.native_plan(budget=budget)
        for n in range(budget):
            self.start(session='worker-'+str(n)); self.fail()
        return summary(self.document)['pendingDecisions'][0]

    def answer(self, count=1, kind='agent', **changes):
        route = summary(self.document)['pendingDecisions'][0]
        context = copy.deepcopy(route['context'])
        context.update(decision='continue_bounded', actionKey='bounded-corrected-layout', additionalAttempts=count)
        context.pop('id', None); context.pop('session', None)
        authority = dict(kind=kind, scopeSha256=context['scopeSha256'])
        if kind == 'agent':
            context.update(id=self.owner['id'], session=self.owner['session'])
            authority.update(id=self.owner['id'], session=self.owner['session'])
        context.update(changes)
        proof = self.artifact('actual-fixture-answer-'+str(self.document['revision'])+'.json', json.dumps(context))
        authority.update(proof)
        request = {k:context[k] for k in ('outcomeId','contextSha256','decision','actionKey','additionalAttempts')}
        request.update(deliveryId='DI-1', action='decide', coordinatorSession='native-coordinator',
                       reason='Synthetic owner actually chooses this finite follow-up.', evidence=[proof], authority=authority)
        return request

    def reject(self, request, pattern):
        before = (self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex((ValueError, StoryError), pattern):
            self.mutate('orchestrate', request)
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(), before)

    def test_routed_owner_answer_resumes_only_its_finite_grant_even_after_progress(self):
        route = self.exhaust(budget=3, cap=1)
        self.assertEqual(route['recipient'], dict(kind='agent', id='owner-root', session='owner-session'))
        self.assertEqual(route['responseDestination'], 'native-coordinator')
        self.assertFalse(route['requiresHumanDecision'])
        self.assertFalse(route['delivered'])  # Projection never claims an actual host message.
        self.assertEqual(route['requestId'], summary(self.document)['pendingDecisions'][0]['requestId'])
        answer = self.answer()
        self.mutate('orchestrate', answer)
        c = campaign_for(self.document, 'INT-ACCESS')
        self.assertEqual(len(c['attempts']), 3)
        self.assertEqual(c['decisions'][-1]['authority']['kind'], 'agent')
        self.assertNotIn('acceptance', self.document['deliveries'][0])
        self.start(key=answer['actionKey'], session='worker-four'); self.finish()
        self.observe('baseline', 4, 'worker-four', activityId='implement', baselineId='real-core',
                     comparisonKey='journey', metric='success', direction='higher', value=0, usable=True)
        self.observe('integrated_progress', 4, 'worker-four', activityId='implement', baselineId='real-core',
                     comparisonKey='journey', metric='success', direction='higher', value=1)
        c = campaign_for(self.document, 'INT-ACCESS')
        self.assertEqual(assessment(c)['noProgressStreak'], 0)
        self.assertEqual(assessment(c)['totalAttempts'], 4)
        self.assertTrue(assessment(c)['budgetExhausted'])
        with self.assertRaisesRegex(ValueError, 'request_owner_choice'):
            self.start(key=answer['actionKey'], session='fifth-worker')
        self.assertTrue(summary(self.document)['pendingDecisions'][0]['requiresHumanDecision'])

    def test_overgrant_and_replayed_answer_reject_without_renewing_history(self):
        self.exhaust(cap=1)
        self.reject(self.answer(count=2), 'allowance')
        answer = self.answer(count=1)
        self.mutate('orchestrate', answer)
        self.reject(answer, 'Campaign changed')
        self.start(key=answer['actionKey']); self.fail()
        self.reject(self.answer(count=1, actionKey='a-different-bounded-followup'), 'allowance')
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['totalAttempts'], 2)

    def test_wrong_identity_stale_context_and_changed_mandate_reject(self):
        self.exhaust()
        bad = self.answer(); bad['authority']['session'] = 'unrelated-session'
        self.reject(bad, 'identity')
        bad = self.answer(contextSha256='0'*64)
        self.reject(bad, 'Campaign changed')
        good = self.answer()
        (self.repo/self.owner['mandate']['path']).write_text('Changed mandate; no longer the frozen authority.')
        self.reject(good, 'Evidence changed')

    def test_acceptance_delegation_does_not_grant_resources_and_human_can_answer(self):
        route = self.exhaust(delegated=False)
        self.assertEqual(route['recipient']['session'], 'owner-session')
        self.assertTrue(route['requiresHumanDecision'])
        self.reject(self.answer(), 'not delegated')
        self.mutate('orchestrate', self.answer(kind='user', count=2))
        self.assertFalse(assessment(campaign_for(self.document,'INT-ACCESS'))['budgetExhausted'])

    def test_missing_upstream_activation_cannot_authorize_agent_renewal(self):
        self.exhaust()
        proof = self.artifact('resume.txt', 'Synthetic coordinator resumed without owner activation.')
        self.mutate('orchestrate', dict(deliveryId='DI-1', action='activate', coordinatorSession='native-coordinator',
            previousCoordinatorSession='native-coordinator', evidence=[proof], dispatchers=[dict(
                session='native-coordinator', capability=dict(id='aim-native-orchestrator',version='4.8.0'), evidence=[proof])]))
        self.reject(self.answer(), 'upstream')

    def test_completed_native_delivery_reaches_review_with_full_campaign_context(self):
        self.native_plan()
        self.start(); self.finish()
        self.start(activity='integrate-review', session='independent-reviewer')
        self.finish(activity='integrate-review')
        self.mutate('review', dict(deliveryId='DI-1', sourcePaths=['app.py']))
        self.assertEqual(self.document['deliveries'][0]['status'], 'review')
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[self.evidence]))
        verify_evidence(self.repo, self.document)
        self.assertEqual(self.document['deliveries'][0]['status'], 'validation')


if __name__ == '__main__':
    unittest.main()
