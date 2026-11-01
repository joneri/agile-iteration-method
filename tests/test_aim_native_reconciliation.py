"""Synthetic owner/host declarations exercise real atomic journal operations."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import test_aim_stories as fixture
from aim_stories import (execute, load, digest, reconciliation_context, project_story_board,
                         validate_document, StoryError, compact_result)


class ReconciliationTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate

    def context_request(self, ids=None):
        ids = ids or ['US-BUYER']
        approval = self.artifact('actual-approval.json', json.dumps(dict(kind='actual_human_playtest_feedback',
            decision='approved', scope=['original-product-'+sid for sid in ids], originalMessage='Synthetic explicit product approval.')))
        auth = self.artifact('present-authorization.json', json.dumps(dict(
            kind='actual_user_authorization_for_present_reconciliation', storyIds=ids,
            priorActualProductApproval=approval['path'], originalMessage='Synthetic present reconciliation instruction, not old exception.')))
        return dict(id='REC-ORIGINAL', storyIds=ids, originalPlan=self.plan_evidence,
                    reviewEvidence=[self.evidence], packageEvidence=[self.artifact('package.md','Synthetic reviewed package.')],
                    acceptanceEvidence=approval, authorizationEvidence=auth, sourcePaths=['app.py'],
                    acceptanceMapping={sid:'original-product-'+sid for sid in ids},
                    deviation='Actual original activation was missing; work happened outside Native gates.',
                    limitations=['Manual test executable identity was not independently observed.'],
                    implementers=[dict(id='actual-author',session='actual-author-session')])

    def prepared(self, context=None):
        context = self.context_request() if context is None else context
        built = reconciliation_context(self.repo, context)
        scope = built['scopeSha256']; c = built['context']
        decision = dict(reconciliationDecisionVersion=1, operation='reconcile', id=context['id'],
                        scopeSha256=scope, storyIds=context['storyIds'], kind='user', decision='accepted',
                        authorizationEvidence=context['authorizationEvidence'], acceptanceEvidence=context['acceptanceEvidence'],
                        reason='Actual bounded instruction transcribed in this synthetic fixture.')
        review = dict(version=1, scopeSha256=scope, sources=c['sourceBindings'],
                      implementers=context['implementers'], reviewer=dict(id='separate-reviewer',session='separate-session'),
                      reviewMode='independent', findings=[], reconciliationId=context['id'],
                      reviewEvidence=context['reviewEvidence'], packageEvidence=context['packageEvidence'],
                      criterionAssessment={s['id']:{a['id']:'Bounded independent criterion assessment with actual limitations.'
                          for a in s['acceptanceCriteria']} for s in c['stories']})
        decision_ref=self.artifact('reconciliation-decision.json',json.dumps(decision))
        review_ref=self.artifact('independent-reconciliation-review.json',json.dumps(review))
        return dict(context=context, scopeSha256=scope, decisionEvidence=decision_ref, reviewRecord=review_ref)

    def reject(self, request, pattern):
        before=(self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError,pattern): execute(self.repo,'reconcile',request,self.token)
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())

    def change_proof(self, req, key, mutate):
        ref=req[key]; p=self.repo/ref['path']; d=json.loads(p.read_text()); mutate(d)
        p.write_text(json.dumps(d)); req[key]=dict(path=ref['path'],sha256=hashlib.sha256(p.read_bytes()).hexdigest())

    def test_original_ids_done_same_journal_receipt_and_preserved_requirements(self):
        before=copy.deepcopy(self.document); req=self.prepared()
        result=execute(self.repo,'reconcile',req,self.token); d=result['document']
        self.assertEqual(d['deliveries'],before['deliveries'])
        self.assertEqual(d['intents'],before['intents']); self.assertEqual(d['epics'],before['epics'])
        for old,new in zip(before['stories'],d['stories']):
            self.assertEqual(new,{**old,'status':'done'} if old['id']=='US-BUYER' else old)
        record=result['reconciliation']; self.assertEqual(record['context']['originalActivation'],'missing')
        self.assertEqual(record['context']['stories'][0],before['stories'][0])
        self.assertFalse(result['idempotent']); self.assertNotIn('approval',record)
        board=project_story_board(self.repo); card=next(s for s in board['stories'] if s['id']=='US-BUYER')
        self.assertEqual(card['column'],'done'); self.assertEqual(card['reconciliationIds'],['REC-ORIGINAL'])
        self.assertEqual(card['deliveryIds'],[]); self.assertEqual(len(card['evidence']),2)
        self.assertEqual(compact_result(result,receipt=True)['reconciliation'],record)

    def test_idempotent_identical_request_no_write_and_stale_cas_rejects(self):
        req=self.prepared(); r=execute(self.repo,'reconcile',req,self.token)
        before=(self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'Stale'): execute(self.repo,'reconcile',req,self.token)
        again=execute(self.repo,'reconcile',req,r['storeSha256'])
        self.assertTrue(again['idempotent']); self.assertEqual(again['reconciliation'],r['reconciliation'])
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())
        req['scopeSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'different operation'): execute(self.repo,'reconcile',req,r['storeSha256'])
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())

    def test_accepted_sources_remain_historical_after_later_changes(self):
        req=self.prepared(); execute(self.repo,'reconcile',req,self.token)
        (self.repo/'app.py').write_text('legitimate later work\n')
        d,_=load(self.repo); self.assertEqual(d['stories'][0]['status'],'done')
        self.assertTrue(project_story_board(self.repo)['valid'])

    def test_reject_changed_original_scope_without_mutation(self):
        req=self.prepared(); self.mutate('refine',dict(stories=[{**self.request_story(),'need':'Changed original need'}]))
        self.reject(req,'Stale reconciliation scope')

    def request_story(self): return copy.deepcopy(self.request_data_story())
    def request_data_story(self):
        d=self.document['stories'][0]
        return {k:copy.deepcopy(v) for k,v in d.items() if k not in {'revision','originalAcceptanceCriteria'}}

    def test_reject_stale_or_changed_evidence_and_sources(self):
        req=self.prepared(); (self.repo/'app.py').write_text('changed source')
        self.reject(req,'Stale reconciliation scope')
        (self.repo/'app.py').write_text('def recover(): return True\n')
        (self.repo/req['context']['packageEvidence'][0]['path']).write_text('changed package')
        self.reject(req,'changed|digest|fingerprint|SHA')

    def test_reject_missing_or_wrong_present_authority_and_unrelated_story(self):
        req=self.prepared(); req['context']['storyIds']=['US-AGENT']
        self.reject(req,'authorization')
        req=self.prepared(); self.change_proof(req,'decisionEvidence',lambda d:d.update(kind='agent'))
        self.reject(req,'human reconciliation decision')
        req=self.prepared(); self.change_proof(req,'decisionEvidence',lambda d:d.update(scopeSha256='0'*64))
        self.reject(req,'human reconciliation decision')

    def test_reject_wrong_owner_scope_mapping_and_missing_original_deviation(self):
        req=self.prepared(); req['context']['acceptanceMapping']={'US-BUYER':'different-room'}
        self.reject(req,'approved product scope')
        req=self.prepared(); req['context']['deviation']=''
        self.reject(req,'deviation')

    def test_reject_nonindependent_incomplete_and_material_review(self):
        for edit,pattern in [
            (lambda d:d.update(reviewer=dict(id='actual-author',session='different')),'independent review'),
            (lambda d:d.update(reviewMode='self'),'independent review'),
            (lambda d:d.update(criterionAssessment={}), 'exactly the original Stories'),
            (lambda d:d.update(findings=[dict(id='F-1',description='Current material failure',severity='material',status='open')]),'independent review')]:
            req=self.prepared(); self.change_proof(req,'reviewRecord',edit); self.reject(req,pattern)

    def test_reject_existing_delivery_even_unapproved(self):
        req=self.prepared(); self.mutate('plan',dict(id='DI-1',title='Existing',goal='Existing work',storyIds=['US-BUYER'],planEvidence=[self.plan_evidence]))
        self.reject(req,'without any original delivery')

    def test_later_epic_closure_remains_separate_real_decision(self):
        from aim_stories import closure_preview
        # This Epic has US-BUYER and US-LATER; refine the latter before selecting.
        story=self.document['stories'][2]
        self.mutate('refine',dict(stories=[{k:("ready" if k=="status" else v) for k,v in story.items()
                                          if k not in {'revision','originalAcceptanceCriteria'}}]))
        req=self.prepared(self.context_request(['US-BUYER','US-LATER']))
        result=execute(self.repo,'reconcile',req,self.token)
        self.assertEqual(result['document']['epics'][0]['status'],'open')
        scope=closure_preview(self.repo,dict(epicId='EPIC-BUY',criteria=[dict(criterionId='AC-1',evidence=[self.evidence])]))
        authority=dict(kind='user',**self.acceptance,scopeSha256=scope['scopeSha256'])
        closed=execute(self.repo,'close-epic',dict(epicId='EPIC-BUY',criteria=[dict(criterionId='AC-1',evidence=[self.evidence])],
                                                authority=authority),result['storeSha256'])
        self.assertEqual(closed['document']['epics'][0]['status'],'closed')

    def test_multiple_story_scope_atomic(self):
        req=self.prepared(self.context_request(['US-BUYER','US-AGENT']))
        result=execute(self.repo,'reconcile',req,self.token)
        self.assertEqual([s['status'] for s in result['document']['stories']],['done','done','draft'])
        self.assertEqual(len(result['document']['reconciliations']),1)

    def test_context_read_only_and_invalid_journal_cannot_claim_delivery_gates(self):
        before=(self.repo/'.aim/product-backlog.json').read_bytes();req=self.prepared()
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())
        result=execute(self.repo,'reconcile',req,self.token)
        forged=copy.deepcopy(result['document']);forged['reconciliations'][0]['context']['originalActivation']='completed'
        with self.assertRaisesRegex(ValueError,'past activation'):validate_document(forged)

if __name__=='__main__': unittest.main()
