"""One persisted owner decision, no copied Story status or subsequent import."""
import copy
import json
from unittest.mock import patch
import unittest
import test_aim_observations as fixtures
import aim_observations as obs
from aim_stories import project_story_board


class AutomaticDecisionTests(unittest.TestCase):
    # Reuse the disposable project setup, not the inherited test methods.
    def setUp(self):
        fixtures.ObservationTests.setUp(self)
        self.entry['reportedState']='awaiting_owner'
        self.entry['stories'][0]['boardStatus']='review'
        self.entry['stories'][0]['prerequisites']=[dict(id='OWNER',text='Owner assesses the actual result',resolved=False,kind='owner_assessment')]
        other=copy.deepcopy(self.entry['stories'][0]);other.update(id='US-OBS-SECOND',title='Predictable jump')
        self.entry['stories'].append(other)
        for activity in self.entry['activities']:activity['storyIds'].append(other['id'])
        self.first=obs.import_entry(self.repo,self.request)

    def request_for(self, ids=None, decision='approved', ident='decision-1'):
        ids=ids or ['US-OBS']
        context=obs.decision_context(self.repo,dict(deliveryId=self.entry['deliveryId'],storyIds=ids))
        authority=self.fixture.artifact(ident+'.md','Synthetic actual owner decision: '+decision)
        return dict(id=ident,deliveryId=self.entry['deliveryId'],storyIds=ids,scopeSha256=context['scopeSha256'],
            decision=decision,authority=dict(kind='user',**authority,scopeSha256=context['scopeSha256']),
            reason='Actual named owner assessment in this synthetic fixture.',evidence=[self.source]),context['storeSha256']

    def board(self):return {s['id']:s for s in project_story_board(self.repo)['stories']}

    def test_focus_change_keeps_pending_and_rejected_obligations_in_ordinary_work(self):
        request, sha = self.request_for(decision='changes_requested')
        receipt = obs.record_decision(self.repo, request, sha)
        prior, _ = obs.load(self.repo)
        original_entries = copy.deepcopy(prior['entries'])
        original_decisions = copy.deepcopy(prior['decisions'])
        q = copy.deepcopy(self.request)
        q['entry'].update(id='new-delivery', deliveryId='NEXT-DELIVERY')
        q['entry']['epic']['id'] = 'EPIC-NEXT'
        for i, story in enumerate(q['entry']['stories']):
            story['id'] = 'US-NEXT-' + str(i)
        for activity in q['entry']['activities']:
            activity['storyIds'] = [s['id'] for s in q['entry']['stories']]
        obs.import_entry(self.repo, q, receipt['storeSha256'])
        cards = self.board()
        for sid in ['US-OBS', 'US-OBS-SECOND']:
            self.assertFalse(cards[sid].get('historical', False), sid)
            self.assertTrue(cards[sid]['previousDelivery'])
            self.assertEqual(cards[sid]['deliveryIds'], ['LOOP-EXCEPTION'])
        self.assertEqual(cards['US-OBS']['ownerDecisionState'], 'changes_requested')
        self.assertEqual(cards['US-OBS']['column'], 'in_progress')
        self.assertFalse(cards['US-OBS']['waitingForOwner'])
        self.assertEqual(cards['US-OBS-SECOND']['ownerDecisionState'], 'awaiting_owner')
        self.assertTrue(cards['US-OBS-SECOND']['waitingForOwner'])
        after, _ = obs.load(self.repo)
        self.assertEqual(after['entries'][:-1], original_entries)
        self.assertEqual(after['decisions'], original_decisions)
        self.assertEqual((self.repo / obs.LEDGER).read_bytes(), self.original)
        # Genuine scoped owner acceptance remains possible after focus changes;
        # it changes only the named Story and leaves the new delivery current.
        accepted, sha = self.request_for(ids=['US-OBS-SECOND'], ident='later-owner')
        obs.record_decision(self.repo, accepted, sha)
        cards = self.board()
        self.assertEqual(cards['US-OBS-SECOND']['column'], 'done')
        self.assertEqual(cards['US-OBS']['column'], 'in_progress')
        self.assertEqual(obs.load(self.repo)[0]['currentId'], 'new-delivery')

    def test_human_decision_drives_only_named_card_without_import_or_status_edit(self):
        request,sha=self.request_for();before,_=obs.load(self.repo)
        receipt=obs.record_decision(self.repo,request,sha);after,_=obs.load(self.repo)
        self.assertEqual(after['entries'],before['entries'])
        self.assertEqual(after['currentId'],before['currentId'])
        cards=self.board();self.assertEqual(cards['US-OBS']['column'],'done')
        self.assertTrue(cards['US-OBS']['prerequisites'][0]['resolved'])
        self.assertFalse(cards['US-OBS']['waitingForOwner'])
        self.assertEqual(cards['US-OBS-SECOND']['column'],'review')
        self.assertTrue(cards['US-OBS-SECOND']['waitingForOwner'])
        self.assertEqual((self.repo/obs.LEDGER).read_bytes(),self.original)
        # Same decision after an uncertain outcome works with its original stale CAS.
        retried=obs.record_decision(self.repo,request,sha)
        self.assertTrue(retried['alreadyRecorded']);self.assertEqual(retried['storeSha256'],receipt['storeSha256'])
        self.assertEqual(len(obs.load(self.repo)[0]['decisions']),1)
        request['reason']='different'
        with self.assertRaisesRegex(ValueError,'different payload'):obs.record_decision(self.repo,request,sha)

    def test_changes_requested_moves_only_affected_story_and_preserves_prior_acceptance(self):
        request,sha=self.request_for();obs.record_decision(self.repo,request,sha)
        q,sha=self.request_for(decision='changes_requested',ident='decision-2');obs.record_decision(self.repo,q,sha)
        self.assertEqual(self.board()['US-OBS']['column'],'in_progress')
        self.assertEqual(self.board()['US-OBS-SECOND']['column'],'review')
        self.assertEqual(len(obs.load(self.repo)[0]['decisions']),2)

    def test_corrected_work_can_return_to_owner_review_after_changes_requested(self):
        request,sha=self.request_for(decision='changes_requested');receipt=obs.record_decision(self.repo,request,sha)
        self.assertEqual(self.board()['US-OBS']['column'],'in_progress')
        q=copy.deepcopy(self.request);q['entry']['id']='corrected-review'
        q['entry']['reportedState']='awaiting_owner'
        for a in q['entry']['activities']:
            if a['role']!='human':a['status']='completed'
        obs.import_entry(self.repo,q,receipt['storeSha256'])
        card=self.board()['US-OBS'];self.assertEqual(card['column'],'review')
        self.assertTrue(card['waitingForOwner'])
        self.assertFalse(card['prerequisites'][0]['resolved'])
        self.assertFalse(card['sourceStale'])
        accepted,sha=self.request_for(ident='new-assessment');obs.record_decision(self.repo,accepted,sha)
        self.assertEqual(self.board()['US-OBS']['column'],'done')

    def test_requirement_change_does_not_reuse_acceptance_or_copied_done(self):
        request,sha=self.request_for();receipt=obs.record_decision(self.repo,request,sha)
        q=copy.deepcopy(self.request);q['entry']['id']='snapshot-refresh'
        q['entry']['stories'][0]['boardStatus']='done';q['entry']['reportedState']='reported_complete'
        q['entry']['stories'][0]['acceptanceCriteria'][0]['text']='Different demanded outcome'
        obs.import_entry(self.repo,q,receipt['storeSha256'])
        card=self.board()['US-OBS'];self.assertEqual(card['column'],'review');self.assertTrue(card['sourceStale'])
        self.assertIn('changed requirements',card['sourceNote'])

    def test_changed_requirements_keep_actual_progress_instead_of_old_decision_stage(self):
        request, sha = self.request_for(decision='changes_requested')
        receipt = obs.record_decision(self.repo, request, sha)
        for stage in ('backlog', 'ready', 'in_progress', 'review'):
            with self.subTest(stage=stage):
                q = copy.deepcopy(self.request)
                q['entry']['id'] = 'changed-' + stage
                q['entry']['reportedState'] = 'awaiting_owner' if stage == 'review' else 'in_progress'
                q['entry']['stories'][0]['boardStatus'] = stage
                q['entry']['stories'][0]['acceptanceCriteria'][0]['text'] = 'Different demanded outcome'
                receipt = obs.import_entry(self.repo, q, receipt['storeSha256'])
                card = self.board()['US-OBS']
                self.assertEqual(card['column'], stage)
                self.assertEqual(card['waitingForOwner'], stage == 'review')
                self.assertFalse(card['sourceStale'])
                self.assertNotIn('decisionId', card)

    def test_progress_refresh_cannot_undo_a_matching_owner_decision(self):
        request,sha=self.request_for();receipt=obs.record_decision(self.repo,request,sha)
        q=copy.deepcopy(self.request);q['entry']['id']='snapshot-refresh'
        q['entry']['activities'][0]['reason']='New routine progress note'
        obs.import_entry(self.repo,q,receipt['storeSha256'])
        self.assertEqual(self.board()['US-OBS']['column'],'done')

    def test_stale_context_unknown_selection_and_wrong_scope_reject_without_writes(self):
        request,sha=self.request_for();before=(self.repo/obs.FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,'Stale decision'):obs.record_decision(self.repo,request,'0'*64)
        for ids in [['US-MISSING'],['US-OBS','US-OBS']]:
            with self.assertRaises(ValueError):obs.decision_context(self.repo,dict(deliveryId=self.entry['deliveryId'],storyIds=ids))
        request['scopeSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'changed requirements'):obs.record_decision(self.repo,request,sha)
        self.assertEqual(before,(self.repo/obs.FILE).read_bytes())

    def test_source_changes_remain_readable_with_explicit_warning(self):
        request,sha=self.request_for();obs.record_decision(self.repo,request,sha)
        (self.repo/request['authority']['path']).write_text('edited authority')
        card=self.board()['US-OBS'];self.assertEqual(card['column'],'done');self.assertTrue(card['sourceStale'])
        self.assertIn('needs verification',card['sourceNote'])

    def test_cannot_accept_stale_published_source_or_native_ledger(self):
        request,sha=self.request_for();before=(self.repo/obs.FILE).read_bytes()
        (self.repo/self.source['path']).write_text('changed requirements source')
        with self.assertRaisesRegex(ValueError,'source changed'):obs.record_decision(self.repo,request,sha)
        self.assertEqual(before,(self.repo/obs.FILE).read_bytes())
        (self.repo/self.source['path']).write_text('Original exception plan and actual pending human decision.')
        (self.repo/obs.LEDGER).write_bytes(self.original+b' ')
        with self.assertRaisesRegex(ValueError,'Native ledger changed'):obs.record_decision(self.repo,request,sha)
        self.assertEqual(before,(self.repo/obs.FILE).read_bytes())

    def test_changed_progress_proof_after_acceptance_never_loses_warning(self):
        request,sha=self.request_for()
        # Decision assessment itself is separate from the original progress source.
        request['evidence']=[self.fixture.artifact('independent-review.md','Synthetic reviewed proof')]
        obs.record_decision(self.repo,request,sha)
        (self.repo/self.source['path']).write_text('later changed progress artifact')
        card=self.board()['US-OBS'];self.assertEqual(card['column'],'done')
        self.assertTrue(card['sourceStale'])

    def test_historical_decision_never_changes_current_delivery(self):
        q=copy.deepcopy(self.request);q['entry'].update(id='new-current',deliveryId='LOOP-OTHER')
        q['entry']['epic']['id']='EPIC-OTHER'
        for s in q['entry']['stories']:s['id']=s['id'].replace('OBS','OTHER')
        for a in q['entry']['activities']:a['storyIds']=[i.replace('OBS','OTHER') for i in a['storyIds']]
        obs.import_entry(self.repo,q,self.first['storeSha256'])
        request,sha=self.request_for();obs.record_decision(self.repo,request,sha)
        self.assertEqual(obs.load(self.repo)[0]['currentId'],'new-current')
        self.assertEqual(self.board()['US-OBS']['column'],'done')

    def test_atomic_failure_leaves_no_half_decision(self):
        request,sha=self.request_for();before=(self.repo/obs.FILE).read_bytes()
        with patch('aim_observations.os.replace',side_effect=OSError('commit failure')):
            with self.assertRaises(OSError):obs.record_decision(self.repo,request,sha)
        self.assertEqual(before,(self.repo/obs.FILE).read_bytes());self.assertEqual(self.board()['US-OBS']['column'],'review')

    def test_commit_succeeds_but_response_fails_then_identical_retry_acknowledges_once(self):
        request,sha=self.request_for();write=obs._write_store
        def uncertain(path,raw):
            write(path,raw)
            raise OSError('response delivery failed after commit')
        with patch('aim_observations._write_store',side_effect=uncertain):
            with self.assertRaises(OSError):obs.record_decision(self.repo,request,sha)
        self.assertEqual(self.board()['US-OBS']['column'],'done')
        retry=obs.record_decision(self.repo,request,sha)
        self.assertTrue(retry['alreadyRecorded'])
        self.assertEqual(len(obs.load(self.repo)[0]['decisions']),1)

    def test_change_to_other_story_does_not_invalidate_named_owner_assessment(self):
        request,sha=self.request_for(ids=['US-OBS-SECOND']);receipt=obs.record_decision(self.repo,request,sha)
        q=copy.deepcopy(self.request);q['entry']['id']='changed-other-story'
        q['entry']['stories'][0]['acceptanceCriteria'][0]['text']='Different first Story requirement'
        obs.import_entry(self.repo,q,receipt['storeSha256'])
        self.assertEqual(self.board()['US-OBS-SECOND']['column'],'done')
        self.assertFalse(self.board()['US-OBS-SECOND']['sourceStale'])

    def test_no_retroactive_delegation(self):
        q=copy.deepcopy(self.request);q['entry']['id']='policy-change'
        mandate=self.fixture.artifact('mandate.md','Synthetic actual scoped delegation')
        q['entry']['deliveryPolicy']=dict(mode='loop',owner=dict(kind='agent',id='owner',session='owner-session',mandate=mandate,decisions=['accept']))
        with self.assertRaisesRegex(ValueError,'frozen owner policy'):obs.import_entry(self.repo,q,self.first['storeSha256'])

    def test_delegated_owner_identity_disposition_and_mandate_are_bound(self):
        # New delivery with a delegated policy frozen at first registration.
        q=copy.deepcopy(self.request);q['entry'].update(id='agent-first',deliveryId='LOOP-AGENT')
        q['entry']['epic']['id']='EPIC-AGENT'
        for s in q['entry']['stories']:s['id']=s['id'].replace('OBS','DELEGATED')
        for a in q['entry']['activities']:a['storyIds']=[i.replace('OBS','DELEGATED') for i in a['storyIds']]
        mandate=self.fixture.artifact('mandate.md','Synthetic actual scoped human delegation')
        q['entry']['deliveryPolicy']=dict(mode='loop',owner=dict(kind='agent',id='actual-owner',session='actual-session',mandate=mandate,decisions=['accept']))
        obs.import_entry(self.repo,q,self.first['storeSha256'])
        ctx=obs.decision_context(self.repo,dict(deliveryId='LOOP-AGENT',storyIds=['US-DELEGATED']))
        evidence=dict(ownerDecisionVersion=1,deliveryId='LOOP-AGENT',operation='accept',scopeSha256=ctx['scopeSha256'],id='actual-owner',session='actual-session',decision='approved',reason='Independent integrated owner assessment')
        ref=self.fixture.artifact('actual-owner.json',json.dumps(evidence))
        request=dict(id='delegated-1',deliveryId='LOOP-AGENT',storyIds=['US-DELEGATED'],scopeSha256=ctx['scopeSha256'],decision='approved',authority=dict(kind='agent',**ref,id='actual-owner',session='actual-session',scopeSha256=ctx['scopeSha256']),reason='Actual delegated assessment',evidence=[self.source])
        wrong=copy.deepcopy(request);wrong['authority']['session']='implementer'
        with self.assertRaisesRegex(ValueError,'identity'):obs.record_decision(self.repo,wrong,ctx['storeSha256'])
        wrong=copy.deepcopy(request);wrong['decision']='changes_requested'
        with self.assertRaisesRegex(ValueError,'disposition'):obs.record_decision(self.repo,wrong,ctx['storeSha256'])
        obs.record_decision(self.repo,request,ctx['storeSha256'])
        self.assertEqual(self.board()['US-DELEGATED']['column'],'done')
        self.assertEqual(self.board()['US-DELEGATED-SECOND']['column'],'review')
