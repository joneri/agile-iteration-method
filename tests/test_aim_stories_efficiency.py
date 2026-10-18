"""Bounded current context and evidence I/O without weaker freshness checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import unittest
import test_aim_stories as fixture
import aim_stories as stories
import test_aim_delivery_quality as quality_fixture


class EfficiencyTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    plan = fixture.StoryDeliveryTests.plan
    authority = fixture.StoryDeliveryTests.authority
    approve = fixture.StoryDeliveryTests.approve
    ready_for_acceptance = fixture.StoryDeliveryTests.ready_for_acceptance
    criterion_evidence = fixture.StoryDeliveryTests.criterion_evidence

    def test_shared_evidence_is_read_once_per_verification(self):
        self.ready_for_acceptance()
        document = self.document
        # Repeat the real same-file references across the frozen criterion set.
        document['deliveries'][0]['criterionEvidence'] *= 6
        reads = []
        original = stories.read_evidence
        def read(repo, path, maximum):
            reads.append(path)
            return original(repo, path, maximum)
        with patch.object(stories, 'read_evidence', side_effect=read):
            stories.verify_evidence(self.repo, document)
        self.assertEqual(reads.count(self.evidence['path']), 1)
        with patch.object(stories, 'read_evidence', side_effect=read):
            stories.verify_evidence(self.repo, document)
        self.assertEqual(reads.count(self.evidence['path']), 2)

    def test_conflicting_hash_for_cached_evidence_is_rejected(self):
        self.ready_for_acceptance()
        self.document['deliveries'][0]['criterionEvidence'][0]['evidence'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(stories.StoryError, 'Evidence changed'):
            stories.verify_evidence(self.repo, self.document)

    def test_file_changed_during_verification_is_rejected(self):
        self.ready_for_acceptance()
        original = stories.read_evidence
        target = self.repo / self.plan_evidence['path']
        def read(repo, path, maximum):
            payload = original(repo, path, maximum)
            if path == self.evidence['path']:
                target.write_text('Replaced plan during this verification')
            return payload
        with patch.object(stories, 'read_evidence', side_effect=read):
            with self.assertRaisesRegex(stories.StoryError, 'changed'):
                stories.verify_evidence(self.repo, self.document)

    def test_compact_status_is_read_only_and_retains_commitment(self):
        self.approve()
        path = self.repo / stories.FILE
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        command = [sys.executable, str(stories.Path(stories.__file__)), '--repo', str(self.repo), 'status', '--compact']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        view = json.loads(result.stdout)
        self.assertEqual(view['view'], 'active')
        self.assertEqual(view['storeSha256'], self.token)
        self.assertEqual({s['id'] for s in view['document']['stories']}, {'US-BUYER', 'US-AGENT'})
        self.assertEqual(view['document']['deliveries'][0]['approval']['scopeSha256'], self.document['deliveries'][0]['scopeSha256'])
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def test_compact_historical_context_is_bounded(self):
        self.approve()
        # View projection only: synthetic historical payload never persisted.
        document = self.document
        historical = {**document['deliveries'][0], 'status': 'accepted', 'reworkHistory': [{'reason': 'x' * 5000}]}
        document['deliveries'].extend([{**historical, 'id': 'DI-OLD-' + str(i)} for i in range(12)])
        full = stories.status_result(document, self.token)
        view = stories.compact_result(full)
        self.assertLess(len(json.dumps(view)), len(json.dumps(full)) * .5)
        self.assertEqual(len(view['document']['deliveries']), 1)
        self.assertEqual(view['totals']['deliveries'], 13)
        self.assertEqual(view['nextStep'], full['nextStep'])

    def test_entire_measure_invocation_reads_each_stable_file_once(self):
        case = quality_fixture.DeliveryQualityTests()
        case.setUp()
        try:
            case.start()
            ref = case.report('one-invocation.json')
            reads = []
            original = stories.read_evidence
            def read(*args):
                reads.append(args[1])
                return original(*args)
            with patch.object(stories, 'read_evidence', side_effect=read):
                result = case.mutate('measure', dict(deliveryId='DI-1', sourcePaths=['app.py'], qualityMeasurements=[ref]))
            self.assertEqual(len(reads), len(set(reads)))
            self.assertEqual(reads.count(ref['path']), 1)
            self.assertEqual(reads.count('app.py'), 1)
            self.assertEqual(result['quality']['deliveries'][0]['nextAction'], 'review')
            receipt = stories.compact_result(result, receipt=True, delivery_id='DI-1')
            self.assertEqual(receipt['nextStep'][0]['operation'], 'review')
            self.assertEqual(receipt['nextStep'][0]['role'], 'reviewer')
            self.assertEqual(Path(receipt['nextStep'][0]['instructions']),
                             fixture.ROOT / 'docs/workflow/role-skill-reviewer.md')
        finally:
            case.doCleanups()

    def test_final_change_after_response_derivation_prevents_commit(self):
        case = quality_fixture.DeliveryQualityTests()
        case.setUp()
        try:
            case.start()
            ref = case.report('race.json')
            before = (case.repo / stories.FILE).read_bytes()
            original = stories.quality_result
            def mutate_after_assessment(*args, **kwargs):
                result = original(*args, **kwargs)
                (case.repo / 'app.py').write_text('changed after verified response')
                return result
            with patch.object(stories, 'quality_result', side_effect=mutate_after_assessment):
                with self.assertRaisesRegex(stories.StoryError, 'changed during verification'):
                    case.mutate('measure', dict(deliveryId='DI-1', sourcePaths=['app.py'], qualityMeasurements=[ref]))
            self.assertEqual(before, (case.repo / stories.FILE).read_bytes())
        finally:
            case.doCleanups()

    def test_source_binding_cannot_cache_a_backlog_hardlink_as_evidence(self):
        case = quality_fixture.DeliveryQualityTests()
        case.setUp()
        try:
            case.start()
            alias = '.aim/ledger-hardlink.json'
            os.link(case.repo / stories.FILE, case.repo / alias)
            ref = case.report('hardlink.json', bindings=case.current_bindings((alias,)))
            before = (case.repo / stories.FILE).read_bytes()
            with self.assertRaisesRegex(stories.StoryError, 'independent.*file identity'):
                case.mutate('measure', dict(deliveryId='DI-1', sourcePaths=[alias],
                                            qualityMeasurements=[ref]))
            self.assertEqual(before, (case.repo / stories.FILE).read_bytes())
        finally:
            case.doCleanups()

    def test_mutation_receipt_reuses_context_and_confirms_same_commit(self):
        self.approve()
        delivery = self.document['deliveries'][0]
        full = stories.status_result(self.document, self.token)
        receipt = stories.compact_result(full, receipt=True, delivery_id=delivery['id'])
        self.assertEqual(receipt['storeSha256'], self.token)
        self.assertEqual(receipt['document']['deliveries'][0]['scopeSha256'], delivery['scopeSha256'])
        self.assertNotIn('qualityPlan', receipt['document']['deliveries'][0])
        self.assertLess(len(json.dumps(receipt)), len(json.dumps(stories.compact_result(full))) / 2)
        # A status request still restores the full current requirements.
        self.assertIn('qualityPlan', stories.compact_result(full)['document']['deliveries'][0])
