"""Original requirements stay open through correction and a real scoped decision."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_aim_observation_decisions as fixtures
import aim_observations as obs
from aim_stories import project_story_board, execute, load
from aim_story_links import link_context, requirements_scope


class StoryLinkTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.AutomaticDecisionTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.repo = self.case.repo
        request, sha = self.case.request_for(decision='changes_requested')
        obs.record_decision(self.repo, request, sha)
        self.original = (self.repo / obs.LEDGER).read_bytes()
        self.correction = copy.deepcopy(self.case.request)
        entry = self.correction['entry']
        entry.update(id='correction-registered', deliveryId='CORRECTION-1', reportedState='in_progress')
        entry['epic']['id'] = 'EPIC-CORRECTION'
        entry['sources'] = [self.case.fixture.artifact('correction.md', 'Actual corrected proof in this synthetic fixture.')]
        entry['stories'] = [copy.deepcopy(entry['stories'][0])]
        entry['stories'][0].update(id='US-CORRECTION', boardStatus='in_progress', corrects=[self.link()])
        for activity in entry['activities']:
            activity['storyIds'] = ['US-CORRECTION']

    def link(self, delivery='LOOP-EXCEPTION', story='US-OBS'):
        return link_context(self.repo, dict(deliveryId=delivery, storyId=story, criterionIds=['AC-1']))

    def publish(self, request=None):
        return obs.import_entry(self.repo, request or self.correction, obs.load(self.repo)[1])

    def ready_correction(self):
        self.correction['entry']['reportedState'] = 'awaiting_owner'
        self.correction['entry']['stories'][0]['boardStatus'] = 'review'
        self.publish()

    def resubmit_original(self):
        request = copy.deepcopy(self.case.request)
        request['entry']['id'] = 'original-corrected'
        request['entry']['sources'].extend(self.correction['entry']['sources'])
        request['entry']['activities'][0]['reason'] = 'Original full requirement scope revalidated with linked correction proof.'
        self.publish(request)

    def decision(self, ids=None):
        request, sha = self.case.request_for(ids=ids, ident='original-final')
        context = obs.decision_context(self.repo, dict(deliveryId=request['deliveryId'], storyIds=request['storyIds']))
        request.update({k: context[k] for k in ['correctionContextSha256'] if k in context})
        return request, sha

    def test_nonblocking_provenance_and_original_context_resubmission(self):
        self.ready_correction()
        cards = self.case.board()
        self.assertNotIn('dependsOn', cards['US-CORRECTION'])
        self.assertTrue(cards['US-OBS']['correctionReady'])
        self.assertEqual(cards['US-OBS']['ownerDecisionState'], 'changes_requested')
        self.assertFalse(cards['US-OBS']['waitingForOwner'])
        self.assertEqual(cards['US-OBS']['corrections'][0]['storyId'], 'US-CORRECTION')
        context = cards['US-OBS']['ownerHandoff']
        self.assertEqual(context['storyIds'], ['US-OBS', 'US-OBS-SECOND'])
        self.assertFalse(context['ready'])
        request, sha = self.decision()
        before = (self.repo / obs.FILE).read_bytes()
        with self.assertRaisesRegex(ValueError, 'Resubmit'):
            obs.record_decision(self.repo, request, sha)
        self.assertEqual(before, (self.repo / obs.FILE).read_bytes())
        self.resubmit_original()
        cards = self.case.board()
        self.assertTrue(cards['US-OBS']['ownerHandoff']['ready'])
        self.assertIn('changes_requested', cards['US-OBS']['sourceNote'])
        request, sha = self.decision()
        receipt = obs.record_decision(self.repo, request, sha)
        self.assertFalse(receipt['nativeLedgerChanged'])
        cards = self.case.board()
        self.assertEqual(cards['US-OBS']['column'], 'done')
        self.assertEqual(cards['US-OBS-SECOND']['column'], 'review')
        self.assertEqual(cards['US-CORRECTION']['column'], 'review')
        self.assertEqual(self.original, (self.repo / obs.LEDGER).read_bytes())
        self.assertEqual(len(obs.load(self.repo)[0]['decisions']), 2)
        self.assertTrue(obs.record_decision(self.repo, request, sha)['alreadyRecorded'])

    def test_correction_acceptance_never_accepts_original(self):
        self.ready_correction()
        context = obs.decision_context(self.repo, dict(deliveryId='CORRECTION-1', storyIds=['US-CORRECTION']))
        request, _ = self.case.request_for(ident='correction-only')
        request.update(deliveryId='CORRECTION-1', storyIds=['US-CORRECTION'], scopeSha256=context['scopeSha256'])
        request['authority']['scopeSha256'] = context['scopeSha256']
        obs.record_decision(self.repo, request, context['storeSha256'])
        self.assertEqual(self.case.board()['US-CORRECTION']['column'], 'done')
        self.assertEqual(self.case.board()['US-OBS']['ownerDecisionState'], 'changes_requested')
        self.assertFalse(self.case.board()['US-OBS']['historical'])

    def test_unknown_stale_self_and_bad_criterion_links_reject_without_writes(self):
        before = (self.repo / obs.FILE).read_bytes()
        for key, value, pattern in [('storyId', 'US-MISSING', 'Unknown'),
                                    ('scopeSha256', '0'*64, 'changed'),
                                    ('criterionIds', ['AC-MISSING'], 'criteria')]:
            request = copy.deepcopy(self.correction)
            request['entry']['stories'][0]['corrects'][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, pattern):
                self.publish(request)
            self.assertEqual(before, (self.repo / obs.FILE).read_bytes())

    def test_stale_original_or_correction_proof_cannot_establish_readiness(self):
        self.ready_correction()
        self.resubmit_original()
        request, sha = self.decision()
        path = self.repo / self.correction['entry']['sources'][0]['path']
        path.write_text('Proof changed after question')
        cards = self.case.board()
        self.assertFalse(cards['US-OBS']['ownerHandoff']['ready'])
        before = (self.repo / obs.FILE).read_bytes()
        with self.assertRaisesRegex(ValueError, 'changed'):
            obs.record_decision(self.repo, request, sha)
        self.assertEqual(before, (self.repo / obs.FILE).read_bytes())
        self.assertEqual(cards['US-OBS']['column'], 'review')

    def test_changed_correction_context_requires_new_original_question_context(self):
        self.ready_correction()
        self.resubmit_original()
        request, _ = self.decision()
        self.correction['entry']['id'] = 'correction-new-proof'
        self.correction['entry']['sources'] = [self.case.fixture.artifact('new-proof.md', 'New correction evidence')]
        self.publish()
        before = (self.repo / obs.FILE).read_bytes()
        with self.assertRaisesRegex(ValueError, 'context changed'):
            obs.record_decision(self.repo, request, obs.load(self.repo)[1])
        self.assertEqual(before, (self.repo / obs.FILE).read_bytes())

    def test_native_correction_links_freeze_in_scope_and_keep_readiness_independent(self):
        fixture = self.case.fixture
        native_link = self.link()
        story = copy.deepcopy(fixture.request['stories'][2])
        story.update(status='ready', corrects=[native_link])
        fixture.mutate('refine', dict(stories=[story]))
        fixture.mutate('plan', dict(id='DI-CORRECTION', title='Correct original observed work',
            goal='Fix original AC1', storyIds=['US-LATER'], planEvidence=[fixture.plan_evidence]))
        document, _ = load(self.repo)
        self.assertEqual(document['deliveries'][0]['stories'][0]['corrects'], [native_link])
        # New native plans do not silently accept the original observed obligation.
        self.assertNotEqual(project_story_board(self.repo)['stories'][-1]['column'], 'done')

    def test_native_original_target_and_readonly_cli_context(self):
        self.case.fixture.approve()
        self.correction['ledgerSha256'] = obs.fingerprint(self.repo, obs.LEDGER)
        self.correction['entry']['stories'][0]['corrects'] = [self.link('DI-1', 'US-BUYER')]
        self.publish()
        cards = self.case.board()
        self.assertEqual(cards['US-BUYER']['corrections'][0]['storyId'], 'US-CORRECTION')
        before = (self.repo / obs.FILE).read_bytes()
        script = Path(__file__).resolve().parents[1] / 'scripts/aim_story_links.py'
        command = [sys.executable, str(script), 'owner-context', '--repo', str(self.repo), '--delivery-id', 'DI-1']
        process = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        context = json.loads(process.stdout)
        self.assertEqual(context['storyIds'], ['US-BUYER', 'US-AGENT'])
        self.assertFalse(context['ready'])
        self.assertEqual(before, (self.repo / obs.FILE).read_bytes())

    def test_native_original_incoming_proof_is_frozen_and_phase_changes_do_not_deadlock(self):
        f = self.case.fixture
        f.ready_for_acceptance()
        old_acceptance = f.document['deliveries'][0]['acceptanceSha256']
        self.correction['ledgerSha256'] = obs.fingerprint(self.repo, obs.LEDGER)
        self.correction['entry']['stories'][0]['corrects'] = [self.link('DI-1', 'US-BUYER')]
        self.ready_correction()
        before = (self.repo / obs.LEDGER).read_bytes()
        with self.assertRaisesRegex(ValueError, 'correction context changed'):
            execute(self.repo, 'accept', dict(deliveryId='DI-1', authority=f.authority(old_acceptance, f.acceptance)), f.token)
        self.assertEqual(before, (self.repo / obs.LEDGER).read_bytes())
        # Supported original rework revalidates the full original scope. Native
        # phase changes do not invalidate the correction's exact requirement link.
        f.mutate('rework', dict(deliveryId='DI-1', reason='Revalidate original scope with linked correction proof'))
        f.mutate('review', dict(deliveryId='DI-1', bindings=[f.binding]))
        f.mutate('validate', dict(deliveryId='DI-1', evidence=[f.evidence]))
        f.mutate('acceptance', dict(deliveryId='DI-1', evidence=[f.evidence], criteria=f.criterion_evidence()))
        delivery = f.document['deliveries'][0]
        self.assertIn('correctionContextSha256', delivery)
        self.assertNotEqual(old_acceptance, delivery['acceptanceSha256'])
        cards = self.case.board()
        self.assertTrue(cards['US-BUYER']['ownerHandoff']['ready'])
        self.assertFalse(cards['US-CORRECTION']['sourceStale'])
        f.mutate('accept', dict(deliveryId='DI-1', authority=f.authority(delivery['acceptanceSha256'], f.acceptance)))
        cards = self.case.board()
        self.assertEqual(cards['US-BUYER']['column'], 'done')
        self.assertEqual(cards['US-CORRECTION']['column'], 'review')

    def test_incoming_partial_correction_does_not_cover_other_original_criteria(self):
        request = copy.deepcopy(self.case.request)
        request['entry']['id'] = 'original-second-criterion'
        request['entry']['reportedState'] = 'rework_required'
        for story in request['entry']['stories']:
            story['boardStatus'] = 'in_progress'
        request['entry']['stories'][0]['acceptanceCriteria'].append(dict(id='AC-2', text='The original second behavior must also work.'))
        self.publish(request)
        self.correction['entry']['stories'][0]['corrects'] = [self.link()]
        self.ready_correction()
        context = self.case.board()['US-OBS']['ownerHandoff']
        self.assertEqual(context['corrections'][0]['criterionIds'], ['AC-1'])
        self.assertFalse(context['ready'])
        self.assertEqual(len(self.case.board()['US-OBS']['acceptanceCriteria']), 2)

    def test_stale_native_correction_never_makes_original_ready(self):
        f = self.case.fixture
        story = copy.deepcopy(f.request['stories'][0])
        story['corrects'] = [self.link()]
        f.mutate('refine', dict(stories=[story]))
        f.ready_for_acceptance()
        # Publish original full resubmission against the current native ledger.
        self.case.request['ledgerSha256'] = obs.fingerprint(self.repo, obs.LEDGER)
        request = copy.deepcopy(self.case.request)
        request['entry']['id'] = 'original-with-native-proof'
        self.publish(request)
        cards = self.case.board()
        self.assertTrue(cards['US-OBS']['ownerHandoff']['ready'])
        (self.repo / 'app.py').write_text('Changed after native review')
        cards = self.case.board()
        self.assertFalse(cards['US-OBS']['ownerHandoff']['ready'])
        self.assertFalse(cards['US-OBS']['corrections'][0]['ready'])
        with self.assertRaisesRegex(ValueError, 'Evidence changed'):
            obs.decision_context(self.repo, dict(deliveryId='LOOP-EXCEPTION', storyIds=['US-OBS']))

    def test_correction_context_is_inside_owner_scope_not_only_request_envelope(self):
        self.ready_correction()
        self.resubmit_original()
        first = obs.decision_context(self.repo, dict(deliveryId='LOOP-EXCEPTION', storyIds=['US-OBS']))
        self.correction['entry']['id'] = 'correction-after-question'
        self.correction['entry']['sources'] = [self.case.fixture.artifact('later-proof.md', 'New independently reviewed proof')]
        self.publish()
        second = obs.decision_context(self.repo, dict(deliveryId='LOOP-EXCEPTION', storyIds=['US-OBS']))
        self.assertNotEqual(first['correctionContextSha256'], second['correctionContextSha256'])
        self.assertNotEqual(first['scopeSha256'], second['scopeSha256'])
        original = self.case.request['entry']
        self.assertNotEqual(second['scopeSha256'], obs.selected_scope(original, ['US-OBS']))

    def test_accepted_native_link_history_does_not_block_unrelated_new_plan(self):
        f = self.case.fixture
        story = copy.deepcopy(f.request['stories'][0])
        story['corrects'] = [self.link()]
        f.mutate('refine', dict(stories=[story]))
        f.accept()
        request = copy.deepcopy(self.case.request)
        request['ledgerSha256'] = obs.fingerprint(self.repo, obs.LEDGER)
        request['entry']['id'] = 'original-later-requirements'
        request['entry']['stories'][0]['acceptanceCriteria'][0]['text'] = 'Later legitimate requirements.'
        self.publish(request)
        later = copy.deepcopy(f.request['stories'][2])
        later['status'] = 'ready'
        f.mutate('refine', dict(stories=[later]))
        f.mutate('plan', dict(id='DI-LATER', title='Unrelated new work', goal='Preserve accepted history',
                             storyIds=['US-LATER'], planEvidence=[f.plan_evidence]))
        self.assertEqual(f.document['deliveries'][0]['status'], 'accepted')
        self.assertEqual(f.document['deliveries'][-1]['status'], 'planned')
