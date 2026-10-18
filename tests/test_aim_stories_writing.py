"""Reuse explicit evidence without inferring coverage or changing authority."""
import copy
import hashlib
import json
import unittest
import test_aim_stories as fixture
import aim_stories as stories


class WritingTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    plan = fixture.StoryDeliveryTests.plan
    approve = fixture.StoryDeliveryTests.approve
    authority = fixture.StoryDeliveryTests.authority
    criterion_evidence = fixture.StoryDeliveryTests.criterion_evidence
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def validation(self):
        self.approve()
        self.mutate('review', {'deliveryId':'DI-1','sourcePaths':['app.py']})
        self.assertEqual(self.document['deliveries'][0]['productBindings'],[self.binding])
        self.mutate('validate', {'deliveryId':'DI-1','evidence':[self.evidence]})

    def coverage(self, data=None):
        return self.artifact('coverage.json', json.dumps(data or {'criterionCoverage':{
            'US-BUYER':{'AC-1':'Independent order recovery check passed.'},
            'US-AGENT':{'AC-1':'Independent support timeline check passed.'}}}))

    def acceptance_input(self, ref):
        return {'deliveryId':'DI-1','evidence':[ref],'criteriaFrom':ref}

    def test_reuse_matches_explicit_criterion_refs_without_new_artifacts(self):
        self.validation(); ref=self.coverage()
        before=set(p.relative_to(self.repo) for p in self.repo.rglob('*'))
        self.mutate('acceptance',self.acceptance_input(ref))
        self.assertEqual(self.document['deliveries'][0]['criterionEvidence'],[
            {'storyId':story,'criterionId':'AC-1','evidence':[ref]} for story in ['US-BUYER','US-AGENT']])
        self.assertEqual(before,set(p.relative_to(self.repo) for p in self.repo.rglob('*')))
        self.assertEqual(self.document['deliveries'][0]['status'],'acceptance')

    def test_missing_extra_or_blank_coverage_rejected_without_write(self):
        self.validation()
        for coverage in [
            {'US-BUYER':{'AC-1':'passed'}},
            {'US-BUYER':{'AC-1':'passed','AC-2':'extra'},'US-AGENT':{'AC-1':'passed'}},
            {'US-BUYER':{'AC-1':''},'US-AGENT':{'AC-1':'passed'}},
            {'US-BUYER':{'AC-1':True},'US-AGENT':{'AC-1':'passed'}},
        ]:
            ref=self.coverage({'criterionCoverage':coverage})
            self.unchanged_failure('acceptance',self.acceptance_input(ref),'coverage|Criterion')

    def test_changed_report_and_ambiguous_input_rejected(self):
        self.validation();ref=self.coverage()
        (self.repo/ref['path']).write_text('{}')
        self.unchanged_failure('acceptance',self.acceptance_input(ref),'Evidence changed')
        ref=self.coverage()
        self.unchanged_failure('acceptance',{**self.acceptance_input(ref),'criteria':self.criterion_evidence()},'exactly one')

    def test_source_paths_reject_ambiguous_input_and_unsafe_paths(self):
        self.approve()
        self.unchanged_failure('review',{'deliveryId':'DI-1','sourcePaths':['app.py'],'bindings':[self.binding]},'exactly one')
        for paths in [['app.py','app.py'],['../escape'],['.aim/product-backlog.json']]:
            self.unchanged_failure('review',{'deliveryId':'DI-1','sourcePaths':paths},'Duplicate|relative|independent')

    def test_epic_closure_reuses_explicit_epic_coverage_and_needs_own_authority(self):
        self.validation(); ref=self.coverage()
        self.mutate('acceptance',self.acceptance_input(ref))
        scope=self.document['deliveries'][0]['acceptanceSha256']
        self.mutate('accept',{'deliveryId':'DI-1','authority':self.authority(scope,self.acceptance)})
        epic_ref=self.artifact('epic-coverage.json',json.dumps({'epicCoverage':{'EPIC-SUPPORT':{'AC-1':'Representative support outcome verified.'}}}))
        compact={'epicId':'EPIC-SUPPORT','criteriaFrom':epic_ref}
        explicit={'epicId':'EPIC-SUPPORT','criteria':[{'criterionId':'AC-1','evidence':[epic_ref]}]}
        preview=stories.closure_preview(self.repo,compact)
        self.assertEqual(preview,stories.closure_preview(self.repo,explicit))
        self.unchanged_failure('close-epic',{**compact,'authority':self.authority(scope)},'stale or different')
        self.mutate('close-epic',{**compact,'authority':self.authority(preview['scopeSha256'])})
        self.assertEqual(next(x for x in self.document['epics'] if x['id']=='EPIC-SUPPORT')['status'],'closed')
        with self.assertRaises(stories.StoryError):
            stories.closure_preview(self.repo,{'epicId':'EPIC-BUY','criteriaFrom':epic_ref})
