"""Exercise quality failures through the actual atomic Story state boundary."""
import copy
import json
import unittest
from unittest.mock import patch
import aim_quality.goals as goals
import test_aim_stories as fixture
import aim_stories as stories


class GoalDeliveryTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    authority = fixture.StoryDeliveryTests.authority
    criterion_evidence = fixture.StoryDeliveryTests.criterion_evidence
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def start(self):
        goal = dict(id='KPI-LATENCY', outcome='Complete search while the user waits',
                    workload='all 17576 starts', environment='fixture host', method='full search',
                    unit='s', owner='TDO', action='Profile and correct before readiness',
                    source='Proposed engineering target', threshold=.5, operator='<=',
                    aggregation='median', minSamples=3)
        self.mutate('plan', dict(id='DI-1', title='Useful complete results', goal='Complete the promised workload',
                                storyIds=['US-BUYER', 'US-AGENT'], planEvidence=[self.plan_evidence], qualityGoals=[goal]))
        self.mutate('approve', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))
        self.mutate('review', dict(deliveryId='DI-1', bindings=[self.binding]))
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[self.evidence]))
        return goal

    def measurement(self, samples, **changes):
        item = dict(goalId='KPI-LATENCY', workload='all 17576 starts', environment='fixture host',
                    method='full search', unit='s', samples=samples, productBindingsSha256=stories.digest([self.binding]))
        item.update(changes)
        return self.artifact('measurements.json', json.dumps(dict(qualityMeasurementVersion='1.0', measurements=[item])))

    def acceptance_request(self, ref=None):
        result = dict(deliveryId='DI-1', evidence=[self.evidence], criteria=self.criterion_evidence())
        if ref: result['qualityMeasurements'] = [ref]
        return result

    def test_missing_failed_and_wrong_workload_never_advance(self):
        self.start()
        self.unchanged_failure('acceptance', self.acceptance_request(), 'unmeasured')
        ref = self.measurement([14, 14.8, 15])
        self.mutate('measure', dict(deliveryId='DI-1', qualityMeasurements=[ref]))
        result = stories.quality_result(self.repo, self.document)
        self.assertEqual(result['deliveries'][0]['goals'][0]['state'], 'failed')
        self.unchanged_failure('acceptance', self.acceptance_request(), 'failed')
        # A fix uses rework, preserving the actual failed measurement reference.
        self.mutate('rework', dict(deliveryId='DI-1', reason='Measured latency fails; optimize search'))
        delivery = self.document['deliveries'][0]
        self.assertEqual(delivery['reworkHistory'][0]['qualityMeasurements'], [ref])
        self.assertNotIn('qualityMeasurements', delivery)
        self.mutate('review', dict(deliveryId='DI-1', bindings=[self.binding]))
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[self.evidence]))
        ref = self.artifact('smaller.json', json.dumps(dict(qualityMeasurementVersion='1.0', measurements=[dict(
            goalId='KPI-LATENCY', workload='only one start', environment='fixture host', method='full search',
            unit='s', samples=[.1,.1,.1], productBindingsSha256=stories.digest([self.binding]))])))
        self.unchanged_failure('acceptance', self.acceptance_request(ref), 'mismatch')

    def test_valid_measurements_allow_readiness_but_require_user_acceptance(self):
        self.start()
        ref = self.measurement([.4, .45, .5])
        self.mutate('acceptance', self.acceptance_request(ref))
        self.assertEqual(self.document['deliveries'][0]['status'], 'acceptance')
        self.assertTrue(all(s['status'] != 'done' for s in self.document['stories']))
        self.unchanged_failure('accept', dict(deliveryId='DI-1', authority=self.authority('0'*64)), 'stale')
        (self.repo/'app.py').write_text('changed implementation')
        self.unchanged_failure('accept', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['acceptanceSha256'])), 'Evidence changed')

    def test_frozen_target_cannot_be_lowered(self):
        self.start()
        altered = copy.deepcopy(self.document)
        altered['deliveries'][0]['qualityGoals'][0]['threshold'] = 20
        with self.assertRaisesRegex(stories.StoryError, 'scope fingerprint'):
            stories.validate_document(altered)

    def test_stale_source_digest_rejects_passing_numbers(self):
        self.start()
        ref = self.measurement([.1,.1,.1], productBindingsSha256='0'*64)
        self.unchanged_failure('acceptance', self.acceptance_request(ref), 'stale')

    def test_goal_check_reuses_shared_verification_reads(self):
        self.start()
        ref = self.measurement([.4, .45, .5])
        self.mutate('acceptance', self.acceptance_request(ref))
        reads = []
        original = stories.read_evidence
        def read(*args):
            reads.append(args[1])
            return original(*args)
        with patch.object(stories, 'read_evidence', side_effect=read), patch.object(goals, 'read_evidence', side_effect=read):
            stories.verify_evidence(self.repo, self.document)
        self.assertEqual(reads.count('app.py'), 1)
        self.assertEqual(reads.count(ref['path']), 1)
