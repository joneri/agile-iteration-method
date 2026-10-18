"""Small synthetic admission checks; no AI run, browser or benchmark."""
import copy
from contextlib import redirect_stdout
import io
import json
import unittest
from unittest.mock import patch

import test_aim_delivery_quality as fixture
import aim_evaluation_guard as guard
import aim_stories as stories


class EvaluationGuardTests(unittest.TestCase):
    setUp = fixture.DeliveryQualityTests.setUp
    artifact = fixture.DeliveryQualityTests.artifact
    mutate = fixture.DeliveryQualityTests.mutate
    authority = fixture.DeliveryQualityTests.authority
    plan_request = fixture.DeliveryQualityTests.plan_request
    start = fixture.DeliveryQualityTests.start
    report = fixture.DeliveryQualityTests.report
    current_bindings = fixture.DeliveryQualityTests.current_bindings
    measure_core = fixture.DeliveryQualityTests.measure_core
    review_and_validate = fixture.DeliveryQualityTests.review_and_validate

    def admission(self, checkpoint="activation", **kwargs):
        scope = self.document['deliveries'][0]['scopeSha256']
        before = (self.repo/stories.FILE).read_bytes()
        try:
            return guard.check(self.repo, 'DI-1', scope, 'a'*64, checkpoint, **kwargs)
        finally:
            self.assertEqual((self.repo/stories.FILE).read_bytes(), before)

    def test_missing_ledger_and_unapproved_delivery_stop(self):
        empty = self.repo/'empty'; empty.mkdir()
        with self.assertRaisesRegex(guard.AdmissionError, 'ledger is missing'):
            guard.check(empty, 'DI-1', 'b'*64, 'a'*64, 'activation')
        self.assertFalse((empty/'.aim').exists())
        self.mutate('plan', self.plan_request())
        with self.assertRaisesRegex(guard.AdmissionError, 'approval is missing'):
            self.admission()

    def test_submission_requires_prior_coordinator_receipt_and_current_sources(self):
        self.start(); activation = self.admission()
        self.measure_core(); self.review_and_validate()
        with self.assertRaises(guard.AdmissionError) as caught:
            self.admission('submission')
        self.assertEqual(caught.exception.validity, 'unknown')
        result = self.admission('submission', activation=activation)
        self.assertEqual(result['aimMethodValidity'], 'valid')
        self.assertTrue(any(c['state']=='unmeasured' for c in result['quality']['checks']))
        changed = copy.deepcopy(activation); changed['protocolSha256'] = 'c'*64
        with self.assertRaisesRegex(guard.AdmissionError, 'another run'):
            self.admission('submission', activation=changed)
        for key, value in [('revision', -1), ('storeSha256', None), ('checkedAt', 'not-a-date')]:
            changed = copy.deepcopy(activation); changed[key] = value
            with self.assertRaisesRegex(guard.AdmissionError, 'invalid'):
                self.admission('submission', activation=changed)
        record = self.repo/'coordinator.json'
        for missing in ('file', 'field'):
            if missing == 'field':
                record.write_text('{}')
            argv = ['guard', '--repo', str(self.repo), '--delivery', 'DI-1',
                    '--scope-sha256', activation['scopeSha256'], '--protocol-sha256', 'a'*64,
                    '--checkpoint', 'submission', '--activation-record', str(record)]
            output = io.StringIO()
            with patch('sys.argv', argv), redirect_stdout(output):
                self.assertEqual(guard.main(), 2)
            self.assertEqual(json.loads(output.getvalue())['aimMethodValidity'], 'unknown')
        (self.repo/'app.py').write_text('changed source')
        with self.assertRaisesRegex(stories.StoryError, 'Evidence changed'):
            self.admission('submission', activation=activation)

    def test_failed_kpi_remains_a_valid_failed_attempt(self):
        self.start(); activation = self.admission()
        self.measure_core(samples=(14,14,14))
        result = self.admission('submission', activation=activation, outcome='failed')
        self.assertEqual(result['aimMethodValidity'], 'valid')
        self.assertEqual(result['quality']['nextAction'], 'correct_or_decide')
        self.assertTrue(any(g['state']=='failed' for g in result['quality']['goals']))
        with self.assertRaisesRegex(guard.AdmissionError, 'outcome contradicts'):
            self.admission('submission', activation=activation)
        with self.assertRaisesRegex(guard.AdmissionError, 'do not backfill'):
            self.admission()

    def test_legacy_or_self_review_plan_does_not_establish_current_method(self):
        self.start()
        for change in ('legacy', 'self'):
            d = copy.deepcopy(self.document)
            plan = d['deliveries'][0]['qualityPlan']
            if change == 'legacy':
                plan.pop('reviewPolicy')
            else:
                plan['reviewPolicy'] = dict(mode='self', reason='An author assertion is insufficient here.')
            d['deliveries'][0]['scopeSha256'] = stories.digest(stories._scope(d['deliveries'][0]))
            d['deliveries'][0]['approval']['scopeSha256'] = d['deliveries'][0]['scopeSha256']
            (self.repo/stories.FILE).write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError, 'reviewPolicy|independent review'):
                guard.check(self.repo, 'DI-1', d['deliveries'][0]['scopeSha256'], 'a'*64, 'activation')
