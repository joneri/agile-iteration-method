"""Issue #25: real ledger mutations, synthetic human mandates, no host-auth claims."""
from __future__ import annotations

import copy
import json
import unittest

import test_aim_orchestration_runtime as runtime_fixture
from aim_stories import FILE
from aim_quality.orchestration_runtime import campaign_for, digest


class OrchestrationOwnershipTests(unittest.TestCase):
    setUp = runtime_fixture.NativeRuntimeTests.setUp
    artifact = runtime_fixture.NativeRuntimeTests.artifact
    mutate = runtime_fixture.NativeRuntimeTests.mutate
    authority = runtime_fixture.NativeRuntimeTests.authority
    unchanged_failure = runtime_fixture.NativeRuntimeTests.unchanged_failure
    native_plan = runtime_fixture.NativeRuntimeTests.native_plan
    activate = runtime_fixture.NativeRuntimeTests.activate
    start = runtime_fixture.NativeRuntimeTests.start
    fail = runtime_fixture.NativeRuntimeTests.fail

    def owned(self):
        self.native_plan(activate=False)
        self.activate(ownership=dict(receivingSession='native-coordinator', kind='receiving'))

    def handoff(self, target='child-coordinator', **changes):
        previous = self.document['deliveries'][0].get('orchestrationActivation')
        source = previous['coordinatorSession'] if previous else 'receiving-root'
        receiver = previous.get('ownership', {}).get('receivingSession', source) if previous else source
        record = dict(orchestrationHandoffVersion=1, deliveryId='DI-1',
                      scopeSha256=self.document['deliveries'][0]['scopeSha256'],
                      receivingSession=receiver, fromSession=source, toSession=target,
                      previousActivationSha256=digest(previous) if previous else None,
                      residualRole='relay', originalMessage='Synthetic user: explicitly transfer this delivery to the named separate coordinator.')
        record.update(changes)
        mandate = self.artifact('handoff-'+str(self.document['revision'])+'.json', json.dumps(record))
        ownership = dict(receivingSession=receiver, kind='handoff', mandate=mandate)
        return ownership

    def test_normal_receiver_delegates_worker_without_separate_coordinator(self):
        self.owned()
        self.start(session='bounded-dev-worker')
        activation = self.document['deliveries'][0]['orchestrationActivation']
        self.assertEqual(activation['coordinatorSession'], 'native-coordinator')
        self.assertEqual(activation['ownership']['kind'], 'receiving')

    def test_initial_subordinate_mismatch_rejects_without_mandate_atomically(self):
        self.native_plan(activate=False)
        for ownership in (dict(receivingSession='receiving-root', kind='receiving'),
                          dict(receivingSession='receiving-root', kind='handoff'),
                          dict(receivingSession='receiving-root', kind='recovery')):
            before = (self.repo / FILE).read_bytes()
            with self.assertRaisesRegex(ValueError, 'default coordinator|mandate|previous coordinator'):
                self.activate(ownership=ownership)
            self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_malformed_ownership_rejects_atomically(self):
        self.native_plan(activate=False)
        cases = [None, [], {}, dict(receivingSession='native-coordinator', kind=[]),
                 dict(receivingSession='', kind='receiving'),
                 dict(receivingSession='native-coordinator', kind='parent-role')]
        for ownership in cases:
            with self.subTest(ownership=ownership):
                before = (self.repo / FILE).read_bytes()
                with self.assertRaises(ValueError):
                    self.activate(ownership=ownership)
                self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_malformed_and_oversized_handoff_evidence_rejects_atomically(self):
        self.owned()
        for raw in ('not JSON', '{}', 'x'*16385):
            mandate = self.artifact('invalid-handoff.json', raw)
            before = (self.repo / FILE).read_bytes()
            with self.assertRaises(ValueError):
                self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator',
                    ownership=dict(receivingSession='native-coordinator', kind='handoff', mandate=mandate))
            self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_initial_explicit_handoff_binds_frozen_target_and_receiver(self):
        self.native_plan(activate=False)
        ownership = self.handoff(target='native-coordinator')
        self.activate(ownership=ownership)
        activation = self.document['deliveries'][0]['orchestrationActivation']
        self.assertEqual(activation['ownership'], ownership)
        self.assertEqual(activation['coordinatorSession'], 'native-coordinator')
        self.start()

    def test_handoff_preserves_campaign_but_activated_parent_cannot_steer(self):
        self.owned(); self.start(); self.fail()
        campaign = copy.deepcopy(campaign_for(self.document, 'INT-ACCESS'))
        ownership = self.handoff()
        proof = self.artifact('parent-still-activated.md', 'Parent relays actual user instructions and status only.')
        self.mutate('orchestrate', dict(deliveryId='DI-1', action='activate',
            coordinatorSession='child-coordinator', previousCoordinatorSession='native-coordinator',
            dispatchers=[dict(session=s, capability=dict(id='aim-native-orchestrator', version='4.8.0'), evidence=[proof])
                         for s in ('native-coordinator', 'child-coordinator')],
            evidence=[proof], ownership=ownership))
        self.assertEqual(campaign_for(self.document, 'INT-ACCESS'), campaign)
        before = (self.repo / FILE).read_bytes()
        with self.assertRaisesRegex(ValueError, 'relays'):
            self.start(coordinator='native-coordinator', session='replacement-worker')
        self.assertEqual((self.repo / FILE).read_bytes(), before)
        for action in ('observe', 'decide'):
            with self.assertRaisesRegex(ValueError, 'relays'):
                self.mutate('orchestrate', dict(deliveryId='DI-1', action=action,
                    coordinatorSession='native-coordinator', outcomeId='INT-ACCESS'))
            self.assertEqual((self.repo / FILE).read_bytes(), before)
        self.start(coordinator='child-coordinator', session='real-child-worker')

    def test_handoff_rejects_retargeted_or_unscoped_human_evidence(self):
        self.owned()
        cases = [dict(deliveryId='DI-OTHER'), dict(scopeSha256='0'*64),
                 dict(receivingSession='other-root'), dict(fromSession='someone-else'),
                 dict(toSession='other-child'), dict(residualRole='coordinator'),
                 dict(previousActivationSha256='0'*64),
                 dict(originalMessage=''), dict(retainedDecisions='all'),
                 dict(orchestrationHandoffVersion=True)]
        for changes in cases:
            with self.subTest(changes=changes):
                ownership = self.handoff(**changes)
                before = (self.repo / FILE).read_bytes()
                with self.assertRaises(ValueError):
                    self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=ownership)
                self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_changed_mandate_bytes_reject_on_next_transaction(self):
        self.owned()
        ownership = self.handoff()
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=ownership)
        (self.repo / ownership['mandate']['path']).write_text('Changed authority after binding.')
        before = (self.repo / FILE).read_bytes()
        with self.assertRaises(ValueError):
            self.start(coordinator='child-coordinator')
        self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_scoped_owner_decisions_remain_frozen_at_handoff(self):
        self.owned()
        policy = copy.deepcopy(self.document['deliveries'][0]['deliveryPolicy'])
        ownership = self.handoff(retainedDecisions=['Only resource decisions explicitly delegated by the human.'])
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=ownership)
        self.assertEqual(self.document['deliveries'][0]['deliveryPolicy'], policy)

    def test_recovery_retains_receiver_history_and_campaign_without_new_handoff(self):
        self.owned(); self.start(); self.fail()
        campaign = copy.deepcopy(campaign_for(self.document, 'INT-ACCESS'))
        self.activate(session='resumed-real-session', previousCoordinatorSession='native-coordinator',
                      ownership=dict(receivingSession='native-coordinator', kind='recovery'))
        delivery = self.document['deliveries'][0]
        self.assertEqual(delivery['orchestrationActivationHistory'][0]['coordinatorSession'], 'native-coordinator')
        self.assertEqual(delivery['executionPlan']['orchestration']['coordinator']['session'], 'native-coordinator')
        self.assertEqual(campaign_for(self.document, 'INT-ACCESS'), campaign)
        self.start(coordinator='resumed-real-session')

    def test_recovery_after_handoff_preserves_original_receiver(self):
        self.owned()
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=self.handoff())
        self.activate(session='child-resumed', previousCoordinatorSession='child-coordinator',
                      ownership=dict(receivingSession='native-coordinator', kind='recovery'))
        self.assertEqual(len(self.document['deliveries'][0]['orchestrationActivationHistory']), 2)
        self.start(coordinator='child-resumed')

    def test_bound_ownership_cannot_downgrade_or_rename_receiver(self):
        self.owned()
        for extra in ({}, dict(ownership=dict(receivingSession='renamed-root', kind='recovery'))):
            before = (self.repo / FILE).read_bytes()
            with self.assertRaisesRegex(ValueError, 'omitted|Receiving session cannot change'):
                self.activate(session='new-session', previousCoordinatorSession='native-coordinator', **extra)
            self.assertEqual((self.repo / FILE).read_bytes(), before)

    def test_returning_control_requires_scoped_reassignment(self):
        self.owned()
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=self.handoff())
        with self.assertRaisesRegex(ValueError, 'Returning coordination'):
            self.activate(previousCoordinatorSession='child-coordinator',
                          ownership=dict(receivingSession='native-coordinator', kind='receiving'))
        ownership = self.handoff(target='native-coordinator')
        self.activate(previousCoordinatorSession='child-coordinator', ownership=ownership)
        self.start()

    def test_old_handoff_cannot_replay_after_round_trip_reassignment(self):
        self.owned()
        original = self.handoff()
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=original)
        self.activate(previousCoordinatorSession='child-coordinator', ownership=self.handoff(target='native-coordinator'))
        before = (self.repo / FILE).read_bytes()
        with self.assertRaisesRegex(ValueError, 'does not match'):
            self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=original)
        self.assertEqual((self.repo / FILE).read_bytes(), before)
        self.activate(session='child-coordinator', previousCoordinatorSession='native-coordinator', ownership=self.handoff())
        self.start(coordinator='child-coordinator')

    def test_historical_activation_recovers_without_migration_or_new_mandate(self):
        self.native_plan()
        self.activate(session='historical-resume', previousCoordinatorSession='native-coordinator')
        self.assertNotIn('ownership', self.document['deliveries'][0]['orchestrationActivation'])
        self.start(coordinator='historical-resume')


if __name__ == '__main__':
    unittest.main()
