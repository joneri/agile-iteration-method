"""Goal-derived checks through the actual atomic Story boundary (no benchmark)."""
import copy
import hashlib
import json
import unittest

import test_aim_stories as fixture
import aim_stories as stories


class DeliveryQualityTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    authority = fixture.StoryDeliveryTests.authority
    criterion_evidence = fixture.StoryDeliveryTests.criterion_evidence
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def mutate(self, command, request):
        result = stories.execute(self.repo, command, request, self.token)
        self.token, self.document = result['storeSha256'], result['document']
        return result

    def plan_request(self):
        goal = dict(id='KPI-LATENCY', outcome='Useful complete result', workload='complete fixture workload',
                    environment='fixture host', method='native core command', unit='s', owner='Dev',
                    action='Profile and correct or block for an owner decision', source='Engineering target',
                    threshold=.5, operator='<=', aggregation='median', minSamples=3)
        refs = ['US-BUYER/AC-1', 'US-AGENT/AC-1']
        check = dict(id='QC-CORE', criteria=refs, kind='behavior', stage='core',
                     workload='complete fixture workload', environment='fixture host',
                     method='native core command', expected={'result':'correct'}, goalIds=[])
        numeric = dict(check, id='QC-TIME', kind='performance', goalIds=['KPI-LATENCY'])
        journey = dict(check, id='QC-ENTRY', kind='journey', stage='delivery',
                       workload='documented installed entry', method='run documented entry',
                       expected={'exitCode':0, 'workerStatus':200})
        plan = dict(checks=[check,numeric,journey], numericGoals='required',
                    reviewPolicy=dict(mode='independent'),
                    primaryResult=dict(checkId='QC-TIME', latencyGoalId='KPI-LATENCY'),
                    caseCoverage=dict(failureCases=dict(checkIds=['QC-CORE']),
                        nonDefaultModes=dict(notApplicableReason='This fixture exposes one operation with no selectable modes.'),
                        resultValidity=dict(checkIds=['QC-CORE','QC-TIME']),
                        workloadFamilies=dict(checkIds=['QC-TIME'])),
                    rationale='Shared quality requires usable complete results; latency is decisive.',
                    sharedRequirements=[dict(source='INT-ACCESS and EPIC-BUY',
                        requirement='Results remain correct and reachable through the delivered entry point',
                        checkIds=['QC-CORE','QC-TIME','QC-ENTRY'])])
        return dict(id='DI-1', title='Useful delivery', goal='The actual user outcome',
                    storyIds=['US-BUYER','US-AGENT'], planEvidence=[self.plan_evidence],
                    qualityGoals=[goal], qualityPlan=plan)

    def start(self):
        self.mutate('plan', self.plan_request())
        self.mutate('approve', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))

    def current_bindings(self, paths=('app.py',)):
        return [dict(path=p, sha256=hashlib.sha256((self.repo/p).read_bytes()).hexdigest()) for p in paths]

    def report(self, name, *, core=True, bindings=None, samples=(.1,.2,.3), observed=None, **context):
        bindings = bindings or self.current_bindings()
        plan = self.document['deliveries'][0]['qualityPlan']
        selected = [c for c in plan['checks'] if c['id'] in (('QC-CORE','QC-TIME') if core else ('QC-ENTRY',))]
        observations = [dict(checkId=c['id'], **{k:c[k] for k in ('workload','environment','method')},
                             observed=observed if observed is not None else c['expected'],
                             productBindingsSha256=stories.digest(bindings)) for c in selected]
        observations[0].update(context)
        numeric = [dict(goalId='KPI-LATENCY', workload='complete fixture workload', environment='fixture host',
                        method='native core command', unit='s', samples=list(samples),
                        productBindingsSha256=stories.digest(bindings))] if core else []
        return self.artifact(name, json.dumps(dict(qualityMeasurementVersion='1.0',measurements=numeric,
                                                  qualityCheckVersion='1.0',checks=observations)))

    def measure_core(self, name='core.json', response=None, **changes):
        ref = self.report(name, **changes)
        request = dict(deliveryId='DI-1', qualityMeasurements=[ref], sourcePaths=['app.py'])
        if response: request['response'] = response
        return self.mutate('measure', request)

    def review_and_validate(self, paths=('app.py',)):
        self.mutate('review', dict(deliveryId='DI-1', sourcePaths=list(paths)))
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[fixture.review_evidence(self)]))

    def acceptance_request(self, ref=None):
        r = dict(deliveryId='DI-1', evidence=[self.evidence], criteria=self.criterion_evidence())
        if ref: r['qualityMeasurements']=[ref]
        return r

    def compact_payload(self, *, core=True):
        return dict(qualityMeasurementVersion='1.0', qualityCheckVersion='1.0',
                    context=dict(scopeSha256=self.document['deliveries'][0]['scopeSha256'],
                                 productBindingsSha256=stories.digest(self.current_bindings())),
                    measurements=[dict(goalId='KPI-LATENCY', unit='s', samples=[.1,.2,.3])] if core else [],
                    checks=[dict(checkId='QC-CORE', observed={'result':'correct'}),
                            dict(checkId='QC-TIME', observed={'result':'correct'})] if core else
                           [dict(checkId='QC-ENTRY', observed={'exitCode':0,'workerStatus':200})])

    def test_compact_evidence_reaches_readiness_without_repeating_plan_labels(self):
        self.start()
        ref = self.artifact('compact-core.json', json.dumps(self.compact_payload()))
        result = self.mutate('measure', dict(deliveryId='DI-1', sourcePaths=['app.py'], qualityMeasurements=[ref]))
        self.assertEqual(result['nextStep'][0]['operation'], 'review')
        self.mutate('review', dict(deliveryId='DI-1', sourcePaths=['app.py']))
        payload = self.compact_payload(core=False)
        payload['criterionCoverage'] = {
            'US-BUYER': {'AC-1':'The buyer result was observed through the documented entry.'},
            'US-AGENT': {'AC-1':'The agent result was observed through the documented entry.'}}
        ref = self.artifact('compact-entry.json', json.dumps(payload))
        self.mutate('measure', dict(deliveryId='DI-1', qualityMeasurements=[ref]))
        self.mutate('validate', dict(deliveryId='DI-1', evidence=[fixture.review_evidence(self), ref]))
        self.mutate('acceptance', dict(deliveryId='DI-1', evidence=[ref], criteriaFrom=ref))
        self.assertEqual(self.document['deliveries'][0]['status'], 'acceptance')
        loaded, token = stories.load(self.repo)
        self.assertEqual(token, self.token)
        self.assertNotIn('acceptance', loaded['deliveries'][0])

    def test_quality_pass_cannot_supply_missing_explicit_criterion_coverage(self):
        self.start(); self.measure_core()
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py']))
        payload = self.compact_payload(core=False)
        payload['criterionCoverage'] = {'US-BUYER':{'AC-1':'Buyer result observed.'}}
        ref = self.artifact('missing-criterion.json',json.dumps(payload))
        self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[ref]))
        self.mutate('validate',dict(deliveryId='DI-1',evidence=[fixture.review_evidence(self), ref]))
        self.unchanged_failure('acceptance',dict(deliveryId='DI-1',evidence=[ref],criteriaFrom=ref),
                               'selected Stor')

    def test_compact_evidence_cannot_resolve_another_scope_or_override_context(self):
        self.start()
        variants = []
        wrong_scope = self.compact_payload(); wrong_scope['context']['scopeSha256'] = '0'*64
        variants.append(wrong_scope)
        missing_binding = self.compact_payload(); missing_binding['context'].pop('productBindingsSha256')
        variants.append(missing_binding)
        override = self.compact_payload(); override['checks'][0]['workload'] = 'convenient different work'
        variants.append(override)
        override_goal = self.compact_payload(); override_goal['measurements'][0]['method'] = 'different method'
        variants.append(override_goal)
        pass_flag = self.compact_payload(); pass_flag['verified'] = True
        variants.append(pass_flag)
        for index, payload in enumerate(variants):
            with self.subTest(index=index):
                ref = self.artifact(f'invalid-compact-{index}.json', json.dumps(payload))
                before = (self.repo/stories.FILE).read_bytes()
                with self.assertRaises(ValueError):
                    self.mutate('measure', dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref]))
                self.assertEqual((self.repo/stories.FILE).read_bytes(), before)

    def test_compact_evidence_preserves_failed_missing_unit_and_stale_results(self):
        self.start()
        payload = self.compact_payload()
        payload['measurements'][0].update(samples=[14,15,16], unit='ms')
        payload['checks'][0]['observed'] = {'result':'wrong'}
        payload['checks'].pop()
        ref = self.artifact('compact-failed.json', json.dumps(payload))
        result = self.mutate('measure', dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref]))
        q = result['quality']['deliveries'][0]
        self.assertEqual(q['goals'][0]['state'], 'mismatch')
        self.assertEqual({c['checkId']:c['state'] for c in q['checks']},
                         {'QC-CORE':'failed','QC-TIME':'unmeasured'})
        self.unchanged_failure('review',dict(deliveryId='DI-1',sourcePaths=['app.py']),'verification not met')
        payload = self.compact_payload(); payload['measurements'][0]['samples'] = [14,15,16]
        ref = self.artifact('compact-slow.json', json.dumps(payload))
        result = self.mutate('measure',dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref],
                             response='Corrected the recorded unit; the actual measurement still misses the target.'))
        self.assertEqual(result['quality']['deliveries'][0]['goals'][0]['state'],'failed')
        payload = self.compact_payload()
        (self.repo/'app.py').write_text('changed after the observed run\n')
        ref = self.artifact('compact-stale.json',json.dumps(payload))
        result = self.mutate('measure',dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref],
                             response='The source changed; retain this stale observation instead of passing it.'))
        q = result['quality']['deliveries'][0]
        self.assertTrue(all(c['state']=='stale' for c in q['goals']+q['checks']))
        self.assertEqual(len(self.document['deliveries'][0]['coreVerificationHistory']),2)

    def test_missing_observation_key_is_named_in_the_existing_receipt(self):
        self.start()
        result = self.measure_core(observed={'answer':'correct'})
        checks = result['quality']['deliveries'][0]['checks']
        self.assertTrue(all(c['state']=='failed' for c in checks))
        self.assertTrue(all('Missing observations: result.' in c['detail'] for c in checks))
        self.assertEqual(result['nextStep'][0]['operation'],'correct_or_decide')

    def test_both_criterion_inputs_reject_another_explicit_scope_or_source(self):
        from unittest.mock import patch
        self.start(); self.measure_core(); self.review_and_validate()
        current = self.compact_payload(core=False)
        current['criterionCoverage'] = {
            'US-BUYER': {'AC-1':'Buyer result observed.'},
            'US-AGENT': {'AC-1':'Agent result observed.'}}
        current_ref = self.artifact('current-context.json',json.dumps(current))
        self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[current_ref]))
        for field in ('scopeSha256','productBindingsSha256'):
            other = copy.deepcopy(current); other['context'][field] = 'a'*64
            ref = self.artifact('other-'+field+'.json',json.dumps(other))
            for compact in (True,False):
                with self.subTest(field=field,compact=compact):
                    request = dict(deliveryId='DI-1',evidence=[ref])
                    if compact: request['criteriaFrom'] = ref
                    else:
                        request['criteria'] = [dict(storyId=s,criterionId='AC-1',evidence=[ref])
                                               for s in ('US-BUYER','US-AGENT')]
                    self.unchanged_failure('acceptance',request,'another approved scope|reviewed product sources')
        request = dict(deliveryId='DI-1',evidence=[current_ref],criteria=[
            dict(storyId=s,criterionId='AC-1',evidence=[current_ref])for s in ('US-BUYER','US-AGENT')])
        with patch.object(stories,'read_evidence',wraps=stories.read_evidence) as reader:
            self.mutate('acceptance',request)
        self.assertEqual(sum(call.args[1]==current_ref['path']for call in reader.call_args_list),1)

    def test_delivery_quality_context_cannot_claim_broader_epic_coverage(self):
        self.start(); self.measure_core(); self.review_and_validate()
        entry = self.report('entry.json',core=False)
        self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[entry]))
        self.mutate('acceptance',self.acceptance_request())
        self.mutate('accept',dict(deliveryId='DI-1',authority=self.authority(
            self.document['deliveries'][0]['acceptanceSha256'])))
        epic = self.document['epics'][0]
        report = self.compact_payload(core=False)
        report['epicCoverage'] = {epic['id']:{c['id']:'Observed Epic outcome.'for c in epic['acceptanceCriteria']}}
        ref = self.artifact('delivery-is-not-epic.json',json.dumps(report))
        for compact in (True,False):
            with self.subTest(compact=compact):
                request = dict(epicId=epic['id'])
                if compact: request['criteriaFrom'] = ref
                else: request['criteria'] = [dict(criterionId=c['id'],evidence=[ref])for c in epic['acceptanceCriteria']]
                before = (self.repo/stories.FILE).read_bytes()
                with self.assertRaisesRegex(stories.StoryError,'broader Epic'):
                    stories.closure_preview(self.repo,request)
                self.assertEqual((self.repo/stories.FILE).read_bytes(),before)

    def test_new_plans_cannot_omit_obligations_or_applicable_goals(self):
        request = self.plan_request()
        omitted = copy.deepcopy(request); omitted['qualityPlan'].pop('reviewPolicy')
        self.unchanged_failure('plan', omitted, 'New plans require reviewPolicy')
        omitted = copy.deepcopy(request); omitted['qualityPlan']['reviewPolicy'] = dict(mode='self')
        self.unchanged_failure('plan', omitted, 'Review policy requires exactly')
        omitted = copy.deepcopy(request); omitted.pop('qualityPlan')
        self.unchanged_failure('plan', omitted, 'qualityPlan')
        omitted = copy.deepcopy(request); omitted.pop('qualityGoals')
        self.unchanged_failure('plan', omitted, 'Applicable numeric')
        omitted = copy.deepcopy(request)
        for c in omitted['qualityPlan']['checks']: c['criteria']=['US-BUYER/AC-1']
        self.unchanged_failure('plan', omitted, 'every selected criterion')
        omitted = copy.deepcopy(request); omitted['qualityPlan']['sharedRequirements']=[]
        self.unchanged_failure('plan', omitted, 'shared quality requirements')
        omitted = copy.deepcopy(request); omitted['qualityPlan']['checks'][2]['kind']='behavior'
        self.unchanged_failure('plan', omitted, 'real-entry delivery journey')
        omitted = copy.deepcopy(request); omitted['qualityPlan']['checks'][0]['expected']={'passed':True}
        self.unchanged_failure('plan', omitted, 'pass flag')

    def test_native_validation_rejects_opaque_conflicting_incomplete_and_failed_review_atomically(self):
        self.start(); self.measure_core()
        (self.repo/'entry.py').write_text('documented entry\n')
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py','entry.py']))
        valid = json.loads((self.repo/fixture.review_evidence(self)['path']).read_text())
        variants = [self.evidence]
        changes = [dict(scopeSha256='0'*64), dict(sources=valid['sources'][:1]),
                   dict(sources=[dict(valid['sources'][0],sha256='0'*64),valid['sources'][1]]),
                   dict(reviewer=dict(id='fixture-author',session='separate-session')),
                   dict(reviewer=dict(id='separate-id',session='fixture-implementation')),
                   dict(reviewMode='self'), dict(reviewMode='unavailable',reviewer=None),
                   dict(findings=[dict(id='F1',severity='material',status='open',description='A required counterexample fails.')])]
        variants += [self.artifact(f'rejected-review-{i}.json',json.dumps(dict(valid,**change)))
                     for i,change in enumerate(changes)]
        duplicate = json.dumps(valid)[:-1]+',"scopeSha256":"0"}'
        variants.append(self.artifact('duplicate-review.json',duplicate))
        for ref in variants:
            with self.subTest(path=ref['path']):
                self.unchanged_failure('validate',dict(deliveryId='DI-1',evidence=[ref]),
                                       'structured review|Review requirements')
        self.mutate('validate',dict(deliveryId='DI-1',evidence=[fixture.review_evidence(self)]))
        self.assertEqual(self.document['deliveries'][0]['status'],'validation')

    def test_native_review_reuses_safe_source_and_report_reads_in_one_invocation(self):
        from unittest.mock import patch
        self.start(); self.measure_core()
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py']))
        ref = fixture.review_evidence(self)
        with patch.object(stories,'read_evidence',wraps=stories.read_evidence) as reader, \
             patch('aim_quality.review.fingerprint',side_effect=AssertionError('Must reuse the containing reader')):
            self.mutate('validate',dict(deliveryId='DI-1',evidence=[ref]))
        for path in ('app.py',ref['path']):
            self.assertEqual(sum(call.args[1]==path for call in reader.call_args_list),1)

    def test_readonly_load_checks_review_structure_even_when_a_file_hash_was_updated(self):
        self.start(); self.measure_core(); self.review_and_validate()
        ref = fixture.review_evidence(self,reviewer=dict(id='fixture-author',session='conflicting-review'))
        altered = copy.deepcopy(self.document)
        altered['deliveries'][0]['reviewEvidence'] = [ref]
        path = self.repo/stories.FILE
        payload = (json.dumps(altered,indent=2)+'\n').encode(); path.write_bytes(payload)
        with self.assertRaisesRegex(stories.StoryError,'Independent reviewer must differ'):
            stories.load(self.repo)
        self.assertEqual(path.read_bytes(),payload)

    def test_self_review_uses_only_the_frozen_nonmaterial_policy_and_never_waives_findings(self):
        request = self.plan_request()
        request['qualityPlan']['reviewPolicy'] = dict(mode='self',reason='Synthetic nonmaterial label-only fixture.')
        self.mutate('plan',request)
        self.mutate('approve',dict(deliveryId='DI-1',authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))
        self.measure_core()
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py']))
        ref = fixture.review_evidence(self,reviewMode='self',reviewer=dict(id='fixture-author',session='fixture-implementation'),
            findings=[dict(id='F1',severity='material',status='open',description='A real defect is still open.')])
        self.unchanged_failure('validate',dict(deliveryId='DI-1',evidence=[ref]),'Unresolved material finding')
        ref = fixture.review_evidence(self,reviewMode='self',reviewer=dict(id='fixture-author',session='fixture-implementation'))
        self.mutate('validate',dict(deliveryId='DI-1',evidence=[ref]))
        self.assertEqual(self.document['deliveries'][0]['status'],'validation')

    def test_historical_case_plan_without_review_policy_stays_readable_and_unmodified(self):
        self.mutate('plan',self.plan_request())
        old = copy.deepcopy(self.document); delivery = old['deliveries'][0]
        delivery['qualityPlan'].pop('reviewPolicy')
        delivery['scopeSha256'] = stories.digest(stories._scope(delivery))
        payload = (json.dumps(old,indent=2)+'\n').encode()
        path = self.repo/stories.FILE; path.write_bytes(payload)
        restored,token = stories.load(self.repo)
        self.assertEqual(restored,old); self.assertEqual(path.read_bytes(),payload)
        self.assertEqual(token,hashlib.sha256(payload).hexdigest())
        self.assertEqual(stories.quality_result(self.repo,restored)['deliveries'][0]['planCoverage'],
                         'legacy_review_structure_not_assessed')

    def test_accepted_review_remains_historical_when_a_later_delivery_changes_product(self):
        self.start(); self.measure_core(); self.review_and_validate()
        self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[self.report('entry.json',core=False)]))
        self.mutate('acceptance',self.acceptance_request())
        self.mutate('accept',dict(deliveryId='DI-1',authority=self.authority(self.document['deliveries'][0]['acceptanceSha256'])))
        before = (self.repo/stories.FILE).read_bytes()
        (self.repo/'app.py').write_text('later authorized implementation\n')
        restored,token = stories.load(self.repo)
        self.assertEqual(token,self.token); self.assertEqual(restored['deliveries'][0]['status'],'accepted')
        self.assertEqual((self.repo/stories.FILE).read_bytes(),before)

    def test_primary_result_cannot_be_omitted_or_replaced_with_delivery_only_responsiveness(self):
        request = self.plan_request()
        omitted = copy.deepcopy(request); omitted['qualityPlan'].pop('primaryResult')
        self.unchanged_failure('plan', omitted, 'New plans require primaryResult')
        omitted = copy.deepcopy(request)
        omitted['qualityPlan']['primaryResult']['checkId'] = 'QC-ENTRY'
        self.unchanged_failure('plan', omitted, 'early core check')
        omitted = copy.deepcopy(request)
        omitted['qualityGoals'][0]['aggregation'] = 'min'
        self.unchanged_failure('plan', omitted, 'median/max')
        omitted = copy.deepcopy(request)
        omitted['qualityGoals'][0]['workload'] = 'cancel control only'
        self.unchanged_failure('plan', omitted, 'same workload')

    def test_primary_result_allows_reasoned_nonapplicability_without_an_extra_metric(self):
        request = self.plan_request()
        request.pop('qualityGoals')
        plan = request['qualityPlan']; plan['numericGoals'] = 'not_applicable'
        plan['checks'] = [c for c in plan['checks'] if c['id'] != 'QC-TIME']
        plan['sharedRequirements'][0]['checkIds'].remove('QC-TIME')
        plan['caseCoverage']['workloadFamilies'] = dict(notApplicableReason='No computation or I/O is changed.')
        plan['caseCoverage']['resultValidity']['checkIds'].remove('QC-TIME')
        plan['primaryResult'] = dict(checkId='QC-CORE', notApplicableReason='')
        self.unchanged_failure('plan', request, 'non-applicability reason')
        plan['primaryResult']['notApplicableReason'] = 'A static copy correction has no new calculation, I/O or latency-sensitive operation.'
        self.mutate('plan', request)
        self.assertEqual(self.document['deliveries'][0]['qualityPlan'], plan)

    def test_existing_primaryless_plan_is_readable_without_scope_or_byte_migration(self):
        self.mutate('plan', self.plan_request())
        old = copy.deepcopy(self.document)
        delivery = old['deliveries'][0]
        delivery['qualityPlan'].pop('primaryResult'); delivery['qualityPlan'].pop('caseCoverage')
        delivery['scopeSha256'] = stories.digest(stories._scope(delivery))
        payload = (json.dumps(old, indent=2)+'\n').encode()
        path = self.repo / stories.FILE; path.write_bytes(payload)
        restored, fingerprint = stories.load(self.repo)
        self.assertEqual(restored, old)
        self.assertEqual(fingerprint, hashlib.sha256(payload).hexdigest())
        self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(stories.quality_result(self.repo, restored)['deliveries'][0]['planCoverage'],
                         'legacy_primary_result_not_assessed')

    def test_fast_numeric_samples_cannot_hide_wrong_results_on_the_timed_workload(self):
        self.start()
        ref = self.report('fast-but-wrong.json')
        report = json.loads((self.repo / ref['path']).read_text())
        next(c for c in report['checks'] if c['checkId'] == 'QC-TIME')['observed'] = {'result':'wrong'}
        ref = self.artifact('fast-but-wrong.json', json.dumps(report))
        result = self.mutate('measure', dict(deliveryId='DI-1', sourcePaths=['app.py'], qualityMeasurements=[ref]))
        quality = result['quality']['deliveries'][0]
        self.assertEqual(quality['goals'][0]['state'], 'passed')
        self.assertEqual(next(c for c in quality['checks'] if c['checkId'] == 'QC-CORE')['state'], 'passed')
        self.assertEqual(quality['nextAction'], 'correct_or_decide')
        self.assertEqual(result['nextStep'][0]['operation'], 'correct_or_decide')
        self.unchanged_failure('review', dict(deliveryId='DI-1', sourcePaths=['app.py']), 'QC-TIME failed')

    def test_declared_nondefault_case_requires_its_own_current_observation(self):
        request = self.plan_request()
        risk = dict(request['qualityPlan']['checks'][0], id='QC-RESUME',
                    workload='resume with nondefault input state', expected={'result':'resumed correctly'})
        request['qualityPlan']['checks'].append(risk)
        request['qualityPlan']['caseCoverage']['nonDefaultModes'] = dict(checkIds=['QC-RESUME'])
        self.mutate('plan', request)
        self.mutate('approve', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))
        result = self.measure_core()
        self.assertEqual(result['quality']['deliveries'][0]['nextAction'], 'correct_or_decide')
        self.unchanged_failure('review', dict(deliveryId='DI-1', sourcePaths=['app.py']), 'QC-RESUME unmeasured')

    def test_case_coverage_cannot_disconnect_timed_work_from_result_validity(self):
        request = self.plan_request()
        omitted = copy.deepcopy(request); omitted['qualityPlan'].pop('caseCoverage')
        self.unchanged_failure('plan', omitted, 'New plans require caseCoverage')
        omitted = copy.deepcopy(request)
        omitted['qualityPlan']['caseCoverage']['resultValidity']['checkIds'].remove('QC-TIME')
        self.unchanged_failure('plan', omitted, 'same check')
        omitted = copy.deepcopy(request); omitted['qualityPlan']['checks'][1]['expected'] = {}
        self.unchanged_failure('plan', omitted, 'concrete result observations')
        omitted = copy.deepcopy(request)
        omitted['qualityPlan']['caseCoverage']['workloadFamilies'] = dict(notApplicableReason='Only a smaller workload was measured.')
        self.unchanged_failure('plan', omitted, 'every performance check')
        omitted = copy.deepcopy(request)
        extra_goal = dict(omitted['qualityGoals'][0], id='KPI-OTHER', workload='different cheaper workload')
        omitted['qualityGoals'].append(extra_goal)
        omitted['qualityPlan']['checks'][1]['goalIds'].append('KPI-OTHER')
        self.unchanged_failure('plan', omitted, 'every linked goal')

    def test_existing_numeric_only_plan_stays_readable_without_becoming_current_coverage(self):
        self.mutate('plan', self.plan_request())
        old = copy.deepcopy(self.document)
        delivery = old['deliveries'][0]; delivery['qualityPlan'].pop('caseCoverage')
        delivery['qualityPlan']['checks'][1]['expected'] = {}
        delivery['scopeSha256'] = stories.digest(stories._scope(delivery))
        payload = (json.dumps(old, indent=2)+'\n').encode()
        path = self.repo / stories.FILE; path.write_bytes(payload)
        loaded, fingerprint = stories.load(self.repo)
        self.assertEqual(path.read_bytes(), payload)
        self.assertEqual(fingerprint, hashlib.sha256(payload).hexdigest())
        self.assertEqual(stories.quality_result(self.repo, loaded)['deliveries'][0]['planCoverage'],
                         'legacy_case_coverage_not_assessed')

    def test_early_miss_changes_next_action_and_retains_failed_evidence(self):
        self.start()
        self.unchanged_failure('review', dict(deliveryId='DI-1', sourcePaths=['app.py']), 'Early core.*unmeasured')
        result = self.measure_core(samples=(14,14.8,15))
        self.assertEqual(result['quality']['deliveries'][0]['nextAction'], 'correct_or_decide')
        self.assertEqual(self.document['deliveries'][0]['status'], 'in_progress')
        old = copy.deepcopy(self.document['deliveries'][0]['coreVerification'])
        self.unchanged_failure('review', dict(deliveryId='DI-1', sourcePaths=['app.py']), 'KPI-LATENCY failed')
        self.mutate('block',dict(deliveryId='DI-1',reason='Measured miss; owner decision required for a larger resource scope'))
        self.assertEqual(self.document['deliveries'][0]['coreVerification'], old)
        self.mutate('unblock',dict(deliveryId='DI-1',reason='Correction remains inside authorized scope'))
        ref=self.report('fixed.json')
        self.unchanged_failure('measure',dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref]),'response')
        (self.repo/'app.py').write_text('def recover(): return "corrected"\n')
        self.measure_core('corrected.json', response='Removed repeated core work; same workload and correctness oracle')
        self.assertEqual(self.document['deliveries'][0]['coreVerificationHistory'], [old])
        self.review_and_validate()

    def test_documented_entry_failure_blocks_readiness_without_erasing_core(self):
        self.start(); self.measure_core(); self.review_and_validate()
        failed=self.report('broken-entry.json',core=False,observed={'exitCode':1,'workerStatus':404})
        self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[failed]))
        self.unchanged_failure('acceptance',self.acceptance_request(),'QC-ENTRY failed')
        self.mutate('rework',dict(deliveryId='DI-1',reason='Correct documented bundle entry'))
        self.assertEqual(self.document['deliveries'][0]['reworkHistory'][-1]['qualityMeasurements'],[failed])
        self.review_and_validate()  # Reuse unchanged core, no second core measurement.
        passed=self.report('working-entry.json',core=False)
        self.mutate('acceptance',self.acceptance_request(passed))
        self.assertEqual(self.document['deliveries'][0]['status'],'acceptance')
        self.assertTrue(all(s['status']!='done' for s in self.document['stories']))

    def test_current_core_reuse_with_new_integration_and_changed_source_rejection(self):
        self.start(); self.measure_core()
        (self.repo/'entry.py').write_text('from app import recover\nprint(recover())\n')
        bindings=self.current_bindings(('app.py','entry.py'))
        self.review_and_validate(('app.py','entry.py'))
        self.unchanged_failure('acceptance',self.acceptance_request(),'QC-ENTRY unmeasured')
        wrong=self.report('wrong-entry-context.json',core=False,bindings=bindings,workload='development server only')
        self.unchanged_failure('acceptance',self.acceptance_request(wrong),'mismatch')
        ref=self.report('entry.json',core=False,bindings=bindings)
        self.mutate('acceptance',self.acceptance_request(ref))
        self.assertNotIn('coreVerificationHistory',self.document['deliveries'][0])
        (self.repo/'entry.py').write_text('raise RuntimeError("changed bundle")\n')
        self.unchanged_failure('accept',dict(deliveryId='DI-1',authority=self.authority(self.document['deliveries'][0]['acceptanceSha256'])),'Evidence changed')

    def test_stale_core_cannot_be_used_to_enter_review(self):
        self.start(); self.measure_core()
        (self.repo/'app.py').write_text('changed core\n')
        self.unchanged_failure('review',dict(deliveryId='DI-1',sourcePaths=['app.py']),'stale')

    def test_premature_delivery_observations_cannot_cover_added_integration(self):
        for stage in ('delivery','both'):
            with self.subTest(stage=stage):
                if stage=='both': self.setUp()
                request=self.plan_request();request['qualityPlan']['checks'][2]['stage']=stage
                self.mutate('plan',request)
                self.mutate('approve',dict(deliveryId='DI-1',authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))
                ref=self.report('premature-entry.json')
                payload=json.loads((self.repo/ref['path']).read_text())
                check=request['qualityPlan']['checks'][2]
                payload['checks'].append(dict(checkId=check['id'],**{k:check[k] for k in ('workload','environment','method')},
                    observed=check['expected'], productBindingsSha256=stories.digest(self.current_bindings())))
                ref=self.artifact('premature-entry.json',json.dumps(payload))
                self.mutate('measure',dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[ref]))
                (self.repo/'entry.py').write_text('raise RuntimeError("broken documented entry")\n')
                self.review_and_validate(('app.py','entry.py'))
                self.unchanged_failure('acceptance',self.acceptance_request(),'QC-ENTRY unmeasured')

    def test_archived_failed_observations_cannot_be_deleted(self):
        self.start();self.measure_core();self.review_and_validate()
        pending=stories.status_result(self.document,self.token,quality=stories.quality_result(self.repo,self.document))
        self.assertEqual(pending['nextStep'][0]['operation'],'measure')
        self.assertEqual(pending['nextStep'][0]['role'],'tdo')
        failed=self.report('failed-entry.json',core=False,observed={'exitCode':1,'workerStatus':404})
        result=self.mutate('measure',dict(deliveryId='DI-1',qualityMeasurements=[failed]))
        self.assertEqual(result['document']['deliveries'][0]['status'], 'validation')
        self.assertEqual(result['nextStep'][0]['operation'], 'rework_or_decide')
        self.assertEqual(result['nextStep'][0]['role'], 'tdo')
        self.mutate('rework',dict(deliveryId='DI-1',reason='Correct entry and retain failed result'))
        (self.repo/failed['path']).unlink()
        with self.assertRaisesRegex(stories.StoryError,'Cannot safely read evidence'):
            stories.load(self.repo)
        self.unchanged_failure('review',dict(deliveryId='DI-1',sourcePaths=['app.py']),'Cannot safely read evidence')

    def test_historical_scope_remains_readable_without_migration(self):
        self.mutate('plan',self.plan_request())
        doc=copy.deepcopy(self.document)
        delivery=doc['deliveries'][0];delivery.pop('qualityPlan');delivery.pop('qualityGoals')
        delivery['scopeSha256']=stories.digest(stories._scope(delivery))
        path=self.repo/stories.FILE;path.write_text(json.dumps(doc))
        original=path.read_bytes()
        loaded,_=stories.load(self.repo)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(stories.quality_result(self.repo,loaded)['deliveries'][0]['planCoverage'],'legacy_not_assessed')


class RawObservationTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    authority = fixture.StoryDeliveryTests.authority
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure
    mutate = DeliveryQualityTests.mutate
    plan_request = DeliveryQualityTests.plan_request
    current_bindings = DeliveryQualityTests.current_bindings
    compact_payload = DeliveryQualityTests.compact_payload

    def start_raw(self):
        request = self.plan_request()
        check = request['qualityPlan']['checks'][0]
        check['expected'] = {'value':7, 'visible':2}
        check['observation'] = {'value':{'pointer':'/output/value'},
                                'visible':{'pointer':'/rows', 'transform':'length'}}
        self.mutate('plan', request)
        self.mutate('approve', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))

    def raw_request(self, name, payload, *, override=False, response=None):
        raw = self.artifact(name+'-raw.json', payload if isinstance(payload,str) else json.dumps(payload))
        report = self.compact_payload()
        report['checks'][0] = dict(checkId='QC-CORE', raw=raw)
        if override:
            report['checks'][0]['observed'] = {'value':7, 'visible':2}
        proof = self.artifact(name+'-report.json', json.dumps(report))
        request = dict(deliveryId='DI-1', sourcePaths=['app.py'], qualityMeasurements=[proof])
        if response:
            request['response'] = response
        return request, raw

    def test_raw_failure_cannot_be_hidden_then_same_frozen_projection_passes(self):
        self.start_raw()
        before, _ = self.raw_request('before', {'output':{'value':6},'rows':[1,2]})
        result = self.mutate('measure', before)
        self.assertEqual(result['quality']['deliveries'][0]['checks'][0]['state'],'failed')
        self.unchanged_failure('review',dict(deliveryId='DI-1',sourcePaths=['app.py']),'verification not met')
        after, _ = self.raw_request('after', {'output':{'value':7},'rows':[1,2]}, response='Correct the observed wrong result; preserve prior bytes.')
        self.mutate('measure', after)
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py']))
        self.assertEqual(self.document['deliveries'][0]['status'],'review')
        self.assertEqual(len(self.document['deliveries'][0]['coreVerificationHistory']),1)

    def test_override_bad_pointer_duplicate_json_and_changed_raw_are_rejected(self):
        self.start_raw()
        bad = [('override', {'output':{'value':6},'rows':[1,2]}, True),
               ('missing', {'output':{},'rows':[1,2]}, False),
               ('type', {'output':{'value':7},'rows':'ab'}, False),
               ('duplicate','{"output":{"value":7,"value":6},"rows":[1,2]}',False)]
        for name,payload,override in bad:
            with self.subTest(name=name):
                request,_=self.raw_request(name,payload,override=override)
                self.unchanged_failure('measure',request,'observation' if name!='duplicate' else 'duplicate')
        request,raw=self.raw_request('changed',{'output':{'value':7},'rows':[1,2]})
        (self.repo/raw['path']).write_text('{}')
        self.unchanged_failure('measure',request,'Evidence changed')

    def test_projection_is_frozen_complete_and_shared_raw_is_read_once_and_sealed(self):
        request=self.plan_request()
        request['qualityPlan']['checks'][0]['observation']={}
        self.unchanged_failure('plan',request,'exactly every expected')
        self.start_raw()
        request,raw=self.raw_request('shared',{'output':{'value':7},'rows':[1,2]})
        from unittest.mock import patch
        original=stories.read_evidence
        reads=[]
        def read(*args):
            reads.append(args[1]);return original(*args)
        with patch.object(stories,'read_evidence',side_effect=read):
            self.mutate('measure',request)
        self.assertEqual(reads.count(raw['path']),1)
        token=self.token;before=(self.repo/stories.FILE).read_bytes()
        finish=stories._finish_verification
        def tamper(repo,cache):
            if raw['path'] in cache:
                (repo/raw['path']).write_text('{}')
            finish(repo,cache)
        with patch.object(stories,'_finish_verification',side_effect=tamper):
            with self.assertRaisesRegex(stories.StoryError,'changed during verification'):
                stories.execute(self.repo,'review',dict(deliveryId='DI-1',sourcePaths=['app.py']),token)
        self.assertEqual((self.repo/stories.FILE).read_bytes(),before)

    def test_failed_raw_history_is_immutable_without_retaining_history_payloads(self):
        self.start_raw()
        before,oldraw=self.raw_request('history-before',{'output':{'value':6},'rows':[1,2]})
        self.mutate('measure',before)
        after,newraw=self.raw_request('history-after',{'output':{'value':7},'rows':[1,2]},response='Correct actual value')
        self.mutate('measure',after)
        cache=stories._verification_cache(self.document)
        stories.verify_evidence(self.repo,self.document,cache=cache)
        self.assertIn(newraw['path'],cache.payloads)
        self.assertNotIn(oldraw['path'],cache.payloads)
        self.assertNotIn(before['qualityMeasurements'][0]['path'],cache.payloads)
        self.assertNotIn(self.plan_evidence['path'],cache.payloads)
        original=(self.repo/oldraw['path']).read_bytes()
        for remove in (False,True):
            with self.subTest(deleted=remove):
                p=self.repo/oldraw['path']
                p.unlink() if remove else p.write_text('{}')
                self.unchanged_failure('review',dict(deliveryId='DI-1',sourcePaths=['app.py']),'[Ee]vidence')
                p.write_bytes(original)
        # A pending report may reuse a historical raw file: one read, actual failure.
        from unittest.mock import patch
        payload=self.compact_payload();payload['checks'][0]=dict(checkId='QC-CORE',raw=oldraw)
        report=self.artifact('history-reuse.json',json.dumps(payload))
        real=stories.read_evidence;reads=[]
        def read(*args):
            reads.append(args[1]);return real(*args)
        with patch.object(stories,'read_evidence',side_effect=read):
            result=self.mutate('measure',dict(deliveryId='DI-1',sourcePaths=['app.py'],qualityMeasurements=[report],response='Retained-data negative control'))
        self.assertEqual(reads.count(oldraw['path']),1)
        self.assertEqual(result['quality']['deliveries'][0]['checks'][0]['state'],'failed')

    def test_active_raw_retention_has_a_total_budget_without_large_fixtures(self):
        self.start_raw()
        request,_=self.raw_request('budget',{'output':{'value':7},'rows':[1,2]})
        from unittest.mock import patch
        with patch.object(stories,'RAW_OBSERVATION_CACHE_BYTES',1):
            self.unchanged_failure('measure',request,'bounded memory budget')
