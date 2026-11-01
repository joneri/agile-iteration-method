"""Bounded Native correction cycles; all owner evidence here is synthetic."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_aim_orchestration_runtime as native
from aim_stories import load, project_graph, validate_document, verify_evidence
from aim_quality.orchestration_runtime import campaign_for, assessment

TRACE = {}


class NativeReworkTests(unittest.TestCase):
    setUp = native.NativeRuntimeTests.setUp
    artifact = native.NativeRuntimeTests.artifact
    mutate = native.NativeRuntimeTests.mutate
    authority = native.NativeRuntimeTests.authority
    native_plan = native.NativeRuntimeTests.native_plan
    activate = native.NativeRuntimeTests.activate
    start = native.NativeRuntimeTests.start
    finish = native.NativeRuntimeTests.finish

    def candidate(self, budget=3):
        self.native_plan(budget=budget)
        self.start(); self.finish()
        self.start(activity='integrate-review', session='reviewer-original')
        self.finish(activity='integrate-review')
        self.to_acceptance()

    def to_acceptance(self):
        self.mutate('review', dict(deliveryId='DI-1', sourcePaths=['app.py']))
        core = self.document['deliveries'][0]['coreVerification']['qualityMeasurements']
        self.mutate('measure', dict(deliveryId='DI-1', qualityMeasurements=core))
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[self.evidence]))
        self.mutate('acceptance', dict(deliveryId='DI-1', evidence=[self.evidence], criteria=[dict(
            storyId='US-BUYER', criterionId='AC-1', evidence=[self.evidence])]))

    def reject(self, command, request, pattern):
        before = (self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError, pattern) as raised:
            self.mutate(command, request)
        self.assertEqual(before, (self.repo/'.aim/product-backlog.json').read_bytes())
        return str(raised.exception)

    def legacy_reworked(self):
        self.candidate()
        self.mutate('rework', dict(deliveryId='DI-1', reason='Synthetic negative owner feedback.'))
        # Explicit historical fixture construction, never a supported repair:
        # installed4.8.2 had this exact shape after rework, without the new marker.
        document = copy.deepcopy(self.document)
        document['deliveries'][0].pop('activityReworkRevision')
        validate_document(document)
        (self.repo/'.aim/product-backlog.json').write_text(json.dumps(document)+'\n')
        self.document, self.token = load(self.repo)

    def test_rework_restarts_before_source_edits_and_reaches_real_gate_sequence(self):
        self.candidate()
        original = copy.deepcopy(self.document['deliveries'][0])
        campaign = copy.deepcopy(campaign_for(self.document, 'INT-ACCESS'))
        source = (self.repo/'app.py').read_bytes()
        self.mutate('rework', dict(deliveryId='DI-1', reason='Synthetic owner rejected delivered behavior.'))
        delivery = self.document['deliveries'][0]
        self.assertEqual(delivery['activityReceipts'], original['activityReceipts'])
        for key in ('id','scopeSha256','approval','deliveryPolicy','stories','epics','intents'):
            self.assertEqual(delivery[key], original[key])
        self.assertEqual(campaign_for(self.document,'INT-ACCESS'), campaign)
        self.assertEqual(delivery['reworkHistory'][0]['criterionEvidence'], original['criterionEvidence'])
        self.reject('accept', dict(deliveryId='DI-1', authority=self.authority(delivery['scopeSha256'])),
                    'requires reviewed, validated')
        self.start(key='correct-original-obligation', session='author-correction')
        self.assertEqual(source, (self.repo/'app.py').read_bytes())
        receipt = self.document['deliveries'][0]['activityReceipts'][-1]
        self.assertEqual((receipt['status'],receipt['attempt'],receipt['reworkRevision']), ('running',2,1))
        TRACE.update(restartStatus=receipt['status'], oldReceiptsPreserved=(
            self.document['deliveries'][0]['activityReceipts'][:len(original['activityReceipts'])]
            == original['activityReceipts']))
        error = self.reject('activity', dict(deliveryId='DI-1',activityId='integrate-review',status='running',
            session='reviewer-correction',coordinatorSession='native-coordinator',actionKey='review-correction'),
            'prerequisites')
        TRACE['newReviewRequired'] = 'prerequisites' in error
        self.reject('activity',dict(deliveryId='DI-1',activityId='implement',status='failed',
            session='worker-a',attempt=1,reason='Late old-worker outcome'), 'stale')
        self.finish()
        self.start(activity='integrate-review',session='reviewer-correction',key='review-correction')
        self.finish(activity='integrate-review')
        self.to_acceptance()
        self.assertEqual(self.document['stories'][0]['status'], 'acceptance')
        self.assertNotIn('acceptance', self.document['deliveries'][0])
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['totalAttempts'], 2)
        delivery=self.document['deliveries'][0]
        self.mutate('accept',dict(deliveryId='DI-1',authority=self.authority(delivery['acceptanceSha256'],self.acceptance)))
        self.assertEqual(self.document['stories'][0]['status'],'done')
        self.assertEqual(self.document['deliveries'][0]['status'],'accepted')
        verify_evidence(self.repo,self.document)

    def test_marker_free_history_is_unchanged_until_explicit_blocked_recovery(self):
        self.legacy_reworked()
        before=(self.repo/'.aim/product-backlog.json').read_bytes()
        graph=project_graph(self.repo,self.document,self.token)
        self.assertEqual([a['status'] for a in graph['activities']], ['completed','completed'])
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())
        original=copy.deepcopy(self.document['deliveries'][0]);campaign=copy.deepcopy(campaign_for(self.document,'INT-ACCESS'))
        self.mutate('block',dict(deliveryId='DI-1',reason='Legacy continuation is blocked.'))
        self.mutate('rework',dict(deliveryId='DI-1',reason='Explicitly recover the unchanged original correction.'))
        delivery=self.document['deliveries'][0]
        self.assertEqual(delivery['activityReworkRevision'],2)
        self.assertEqual(delivery['reworkHistory'][-1]['from'],'in_progress')
        self.assertEqual(delivery['reworkHistory'][-1]['blockedReason'],'Legacy continuation is blocked.')
        self.assertEqual(delivery['activityReceipts'],original['activityReceipts'])
        self.assertEqual(delivery['reworkHistory'][0],original['reworkHistory'][0])
        self.assertEqual(campaign_for(self.document,'INT-ACCESS'),campaign)
        self.reject('rework',dict(deliveryId='DI-1',reason='Do not silently reset this new round.'),'requires an unaccepted')
        self.start(key='recover-original-correction',session='recovery-author')
        self.assertEqual(self.document['deliveries'][0]['activityReceipts'][-1]['reworkRevision'],2)

    def test_rework_does_not_renew_exhausted_campaign_resources(self):
        self.candidate(budget=1)
        campaign=copy.deepcopy(campaign_for(self.document,'INT-ACCESS'))
        self.mutate('rework',dict(deliveryId='DI-1',reason='Correction requested, no resource extension.'))
        self.assertEqual(campaign_for(self.document,'INT-ACCESS'),campaign)
        error=self.reject('activity',dict(deliveryId='DI-1',activityId='implement',status='running',
            session='new-author',coordinatorSession='native-coordinator',actionKey='correction-without-renewal'),
            'request_owner_choice')
        self.assertTrue(assessment(campaign_for(self.document,'INT-ACCESS'))['budgetExhausted'])
        TRACE['exhaustedStart']='rejected' if 'request_owner_choice' in error else error

    def test_recovery_rejects_initial_work_and_raw_running_workers_even_if_stale(self):
        self.native_plan()
        self.reject('rework',dict(deliveryId='DI-1',reason='No prior rejected completion.'),'requires an unaccepted')
        # A separate bounded fixture exercises an actual raw running receipt.
        self.setUp(); self.legacy_reworked()
        record=self.document['deliveries'][0]['activityReceipts'][-1]
        record['status']='running';record.pop('sourceBindings');record.pop('evidence')
        (self.repo/'app.py').write_text('changed dependency source\n')
        (self.repo/'.aim/product-backlog.json').write_text(json.dumps(self.document)+'\n')
        self.document,self.token=load(self.repo)
        graph=project_graph(self.repo,self.document,self.token)
        self.assertEqual(graph['activities'][-1]['status'],'stale')
        self.reject('rework',dict(deliveryId='DI-1',reason='Must not cancel a real worker.'),'actual running activity')


if __name__ == '__main__':
    unittest.main()
