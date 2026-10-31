"""Real ledger and host-boundary regression oracles for Native orchestration."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import test_aim_stories as fixture
from aim_stories import execute, load, StoryError
from aim_quality.orchestration import construct_default_graph, assess_campaign
from aim_quality.orchestration_runtime import prepare_plan, assessment, campaign_for
from aim_codex_bridge import capture_action_target, CodexBridgeError, validate_native_envelope

class NativeRuntimeTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    authority = fixture.StoryDeliveryTests.authority
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def native_plan(self, budget=3, activate=True, delivery='DI-1', session='native-coordinator'):
        graph = construct_default_graph('cohesive_delivery',
            [dict(id='INT-ACCESS', requirement=self.document['intents'][0]['statement'], paths=['app.py'])],
            dict(session=session, capability=dict(id='aim-native-orchestrator', version='4.8.0'),
                 permittedDecisions=['continue_bounded', 'change_baseline', 'request_owner_choice', 'independent_work', 'reprioritize']),
            dict(delegationAllowed=False, maxWorkers=1, checkpointAttemptBudget=budget))
        graph['origin'] = dict(kind='custom', reference='owner-dag-r1')
        plan = prepare_plan(graph, {'US-BUYER': ['INT-ACCESS']})
        self.mutate('plan', dict(id=delivery,title='Native original outcome', goal='Restore original journey',
            storyIds=['US-BUYER'], planEvidence=[self.plan_evidence], executionPlan=plan))
        d = self.document['deliveries'][-1]
        self.mutate('approve', dict(deliveryId=delivery, authority=self.authority(d['scopeSha256'])))
        if activate:
            self.activate(delivery, session)
        return graph

    def activate(self, delivery='DI-1', session='native-coordinator', **extra):
        proof = self.artifact('activation-'+str(self.document['revision'])+'.md', 'Actual session capability loaded; declaration, not authentication.')
        return self.mutate('orchestrate', dict(deliveryId=delivery, action='activate', coordinatorSession=session,
            dispatchers=[dict(session=session, capability=dict(id='aim-native-orchestrator',version='4.8.0'),evidence=[proof])],
            evidence=[proof], **extra))

    def start(self, key='restore-journey', session='worker-a', coordinator='native-coordinator', delivery='DI-1', activity='implement'):
        return self.mutate('activity', dict(deliveryId=delivery,activityId=activity,status='running',session=session,
            coordinatorSession=coordinator,actionKey=key))

    def fail(self, delivery='DI-1', activity='implement'):
        r = self.document['deliveries'][-1]['activityReceipts'][-1]
        return self.mutate('activity',dict(deliveryId=delivery,activityId=activity,status='failed',session=r['session'],
            attempt=r['attempt'],reason='Original integrated user journey still fails.'))

    def finish(self, delivery='DI-1', activity='implement'):
        r = self.document['deliveries'][-1]['activityReceipts'][-1]
        proof = self.artifact('complete-'+str(self.document['revision'])+'.txt','Component check passed; integrated journey unproven.')
        return self.mutate('activity',dict(deliveryId=delivery,activityId=activity,status='completed',session=r['session'],
            attempt=r['attempt'],sourcePaths=['app.py'],evidence=[proof]))

    def observe(self, kind, attempt, session, **extra):
        observation = dict(outcomeId='INT-ACCESS',kind=kind,session=session,attempt=attempt,**extra)
        from aim_quality.orchestration_runtime import digest
        sources = [dict(path='app.py',sha256=hashlib.sha256((self.repo/'app.py').read_bytes()).hexdigest())]
        report = dict(orchestrationObservationVersion=1,deliveryId='DI-1',scopeSha256=self.document['deliveries'][0]['scopeSha256'],
                      sourceBindingsSha256=digest(sources),observation=observation)
        proof = self.artifact('observation-'+str(self.document['revision'])+'.json',json.dumps(report))
        return self.mutate('orchestrate',dict(deliveryId='DI-1',action='observe',coordinatorSession='native-coordinator',
            outcomeId='INT-ACCESS',observation=observation,evidence=[proof],sourcePaths=['app.py']))

    def test_actual_activation_and_custom_graph_fidelity(self):
        graph = self.native_plan(activate=False)
        with self.assertRaisesRegex(ValueError,'Activate'):
            self.start()
        self.activate()
        self.assertEqual(self.document['deliveries'][0]['executionPlan']['orchestration'],graph)
        self.start()
        c = campaign_for(self.document,'INT-ACCESS')
        self.assertEqual(c['attempts'][0]['session'],'worker-a')
        self.assertEqual(c['campaign']['observations'][0]['attempt'],1)
        self.assertIn('tokens',assessment(c)['resources']['unknownUnits'])

    def test_failure_budget_cannot_reset_at_node_session_or_delivery_boundary(self):
        self.native_plan(budget=2)
        self.start(); self.fail()
        self.start(session='replacement-worker'); self.fail()
        with self.assertRaisesRegex(ValueError,'request_owner_choice'):
            self.start(session='third-worker')
        # A replacement delivery's activation may not recreate the campaign.
        from aim_quality.orchestration_runtime import change_orchestration, check_activity
        original = copy.deepcopy(campaign_for(self.document, 'INT-ACCESS'))
        replacement = copy.deepcopy(self.document['deliveries'][0])
        replacement['id'] = 'DI-2'
        replacement.pop('orchestrationActivation')
        replacement['executionPlan']['orchestration']['policy']['checkpointAttemptBudget'] = 8
        change_orchestration(self.document, replacement,
            dict(deliveryId='DI-2', action='activate', coordinatorSession='native-coordinator',
                dispatchers=[dict(session='native-coordinator', capability=dict(id='aim-native-orchestrator',version='4.8.0'),evidence=[self.evidence])], evidence=[self.evidence]),
            bind_evidence=lambda x:x, bind_sources=lambda x:x, bind_authority=lambda x,y:x,
            check_reference=lambda x:None,at='fixture')
        self.assertEqual(campaign_for(self.document,'INT-ACCESS'),original)
        with self.assertRaisesRegex(ValueError,'request_owner_choice'):
            check_activity(self.document,replacement,dict(activityId='implement',coordinatorSession='native-coordinator',actionKey='new-node'),check_reference=lambda x:None)

    def test_activation_resume_retains_campaign_and_original_binding(self):
        self.native_plan(); self.start(); self.fail()
        with self.assertRaisesRegex(ValueError,'previous'):
            self.activate(session='new-coordinator')
        self.activate(session='new-coordinator',previousCoordinatorSession='native-coordinator')
        self.start(coordinator='new-coordinator',session='new-worker')
        d = self.document['deliveries'][0]
        self.assertEqual(d['orchestrationActivationHistory'][0]['coordinatorSession'],'native-coordinator')
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['totalAttempts'],2)

    def test_observations_bind_completed_actual_worker_attempt(self):
        self.native_plan()
        self.observe('baseline',0,'native-coordinator',baselineId='known-working',comparisonKey='original-journey',metric='success',direction='higher',value=0,usable=True)
        self.start()
        with self.assertRaisesRegex(ValueError,'completed'):
            self.observe('integrated_progress',1,'worker-a',activityId='implement',baselineId='known-working',comparisonKey='original-journey',metric='success',direction='higher',value=1)
        self.finish()
        with self.assertRaisesRegex(ValueError,'binding'):
            self.observe('integrated_progress',1,'another-worker',activityId='implement',baselineId='known-working',comparisonKey='original-journey',metric='success',direction='higher',value=1)
        self.observe('integrated_progress',1,'worker-a',activityId='implement',baselineId='known-working',comparisonKey='original-journey',metric='success',direction='higher',value=1)
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['noProgressStreak'],0)
        with self.assertRaisesRegex(ValueError,'already'):
            self.observe('integrated_progress',1,'worker-a',activityId='implement',baselineId='known-working',comparisonKey='original-journey',metric='success',direction='higher',value=1)
        with self.assertRaisesRegex(ValueError,'binding'):
            self.observe('baseline',1,'native-coordinator',baselineId='lower-new-baseline',comparisonKey='original-journey',metric='success',direction='higher',value=-1,usable=True)

    def test_first_working_core_can_establish_baseline_and_later_progress_without_resetting_history(self):
        self.native_plan(budget=4)
        self.start();self.finish()
        self.observe('baseline',1,'worker-a',activityId='implement',baselineId='first-working-core',
            comparisonKey='original-journey',metric='success',direction='higher',value=1,usable=True)
        c=campaign_for(self.document,'INT-ACCESS')
        self.assertEqual(assessment(c)['noProgressStreak'],1)
        self.assertEqual(assessment(c)['totalAttempts'],1)
        self.assertEqual(c['observations'][-1]['sourceCheckpoint']['kind'],'inline')
        # Replacing the source makes the prior activity stale and requires an actual new attempt.
        (self.repo/'app.py').write_text('def recover(): return True  # next integrated candidate\n')
        self.start(session='worker-b',key='expand-proven-working-core');self.finish()
        self.observe('integrated_progress',2,'worker-b',activityId='implement',baselineId='first-working-core',
            comparisonKey='original-journey',metric='success',direction='higher',value=2)
        self.observe('baseline',2,'worker-b',activityId='implement',baselineId='latest-usable-core',
            comparisonKey='original-journey',metric='success',direction='higher',value=2,usable=True)
        c=campaign_for(self.document,'INT-ACCESS')
        self.assertEqual(assessment(c)['totalAttempts'],2)
        self.assertEqual(assessment(c)['noProgressStreak'],0)
        self.assertEqual(assessment(c)['latestUsableBaseline']['baselineId'],'latest-usable-core')
        # A lower replacement baseline and result do not erase the proven highwater.
        (self.repo/'app.py').write_text('def recover(): return False  # regressed candidate\n')
        self.start(session='worker-c',key='test-regressed-candidate');self.finish()
        self.observe('baseline',3,'worker-c',activityId='implement',baselineId='regressed-usable-core',
            comparisonKey='original-journey',metric='success',direction='higher',value=0,usable=True)
        self.observe('integrated_progress',3,'worker-c',activityId='implement',baselineId='regressed-usable-core',
            comparisonKey='original-journey',metric='success',direction='higher',value=1)
        c=campaign_for(self.document,'INT-ACCESS')
        self.assertEqual(assessment(c)['bestValue']['value'],2)
        self.assertEqual(assessment(c)['noProgressStreak'],1)
        self.assertEqual(assessment(c)['totalAttempts'],3)


    def test_durable_owner_budget_choice_changes_real_next_action(self):
        self.native_plan(budget=1); self.start(); self.fail()
        c = campaign_for(self.document,'INT-ACCESS')
        context = assessment(c)['contextSha256']
        request = dict(deliveryId='DI-1',action='decide',coordinatorSession='native-coordinator',outcomeId='INT-ACCESS',
            contextSha256=context,decision='continue_bounded',actionKey='isolate-known-usable-baseline',reason='One actual owner-authorized alternative diagnostic.',evidence=[self.evidence])
        with self.assertRaisesRegex(ValueError,'owner'):
            self.mutate('orchestrate',request)
        scope = self.document['deliveries'][0]['scopeSha256']
        request['authority'] = self.authority(scope)
        with self.assertRaisesRegex(ValueError,'scoped JSON'):
            self.mutate('orchestrate',request)
        payload = dict(orchestrationDecisionVersion=1,operation='orchestration_decision',scopeSha256=scope,
            **{k:request[k] for k in ('outcomeId','contextSha256','decision','actionKey','coordinatorSession')})
        proof = self.artifact('actual-owner-choice.json',json.dumps(payload))
        request['authority'] = self.authority(scope,proof)
        self.mutate('orchestrate',request)
        with self.assertRaisesRegex(ValueError,'actual next action|changed diagnostic'):
            self.start(key='restore-journey')
        self.start(key='isolate-known-usable-baseline')
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['totalAttempts'],2)
        self.fail()
        with self.assertRaisesRegex(ValueError,'request_owner_choice'):
            self.start(key='another-key')

    def test_pending_actual_owner_choice_requires_fresh_scoped_answer_below_budget(self):
        self.native_plan(budget=4)
        c=campaign_for(self.document,'INT-ACCESS')
        question=dict(deliveryId='DI-1',action='decide',coordinatorSession='native-coordinator',outcomeId='INT-ACCESS',
            contextSha256=assessment(c)['contextSha256'],decision='request_owner_choice',actionKey='ask-owner-specific-tradeoff',
            reason='A real outcome tradeoff needs the actual owner.',evidence=[self.evidence])
        self.mutate('orchestrate',question)
        c=campaign_for(self.document,'INT-ACCESS')
        self.assertFalse(assessment(c)['budgetExhausted'])
        answer=dict(question,contextSha256=assessment(c)['contextSha256'],decision='continue_bounded',actionKey='owner-selected-diagnostic')
        before=(self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'owner decision'):
            self.mutate('orchestrate',answer)
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),before)
        scope=self.document['deliveries'][0]['scopeSha256']
        payload=dict(orchestrationDecisionVersion=1,operation='orchestration_decision',scopeSha256=scope,
            **{k:answer[k] for k in ('outcomeId','contextSha256','decision','actionKey','coordinatorSession')})
        proof=self.artifact('actual-answer-below-budget.json',json.dumps(payload))
        answer['authority']=self.authority(scope,proof)
        self.mutate('orchestrate',answer)
        with self.assertRaisesRegex(ValueError,'actual next action'):
            self.start(key='coordinator-invented-alternative')
        self.start(key='owner-selected-diagnostic')

    def test_global_priority_change_invalidates_old_campaign_answer_context(self):
        from aim_quality.orchestration_runtime import change_orchestration
        self.native_plan()
        document=copy.deepcopy(self.document)
        d=document['deliveries'][0]
        document['intents'].append(dict(id='INT-SECOND',statement='Second original goal'))
        document['epics'].append(dict(id='EPIC-SECOND',intentId='INT-SECOND',status='open'))
        d['executionPlan']['orchestration']['outcomes'].append(dict(id='INT-SECOND',requirement='Second original goal',paths=['app.py']))
        c=campaign_for(document,'INT-ACCESS')
        c['campaign']['waitingOriginalGoals'].append('INT-SECOND')
        second=copy.deepcopy(c);second['outcomeId']='INT-SECOND';second['campaign']['outcomeId']='INT-SECOND'
        document['orchestration']['campaigns'].append(second)
        old_context=assessment(c,owner_priority=[])['contextSha256']
        document['orchestration']['ownerPriority']=['INT-SECOND','INT-ACCESS']
        request=dict(deliveryId='DI-1',action='decide',coordinatorSession='native-coordinator',outcomeId='INT-ACCESS',
            contextSha256=old_context,decision='reprioritize',actionKey='restore-stale-owner-order',reason='A stale recorded choice.',
            evidence=[self.evidence],authority=self.authority(d['scopeSha256']),priority=['INT-ACCESS','INT-SECOND'])
        before=copy.deepcopy(document)
        with self.assertRaisesRegex(ValueError,'Campaign changed'):
            change_orchestration(document,d,request,bind_evidence=lambda x:x,bind_sources=lambda x:x,
                bind_authority=lambda x,y:x,check_reference=lambda x:None,at='fixture')
        self.assertEqual(document,before)

    def test_owner_answer_cannot_retarget_independent_work(self):
        from aim_stories import _orchestration_authority
        self.native_plan()
        d=self.document['deliveries'][0]
        request=dict(outcomeId='INT-ACCESS',contextSha256=assessment(campaign_for(self.document,'INT-ACCESS'))['contextSha256'],
            decision='independent_work',actionKey='work-second-goal',coordinatorSession='native-coordinator',targetOutcomeId='INT-SECOND')
        payload=dict(orchestrationDecisionVersion=1,operation='orchestration_decision',scopeSha256=d['scopeSha256'],**request)
        proof=self.artifact('owner-independent-target.json',json.dumps(payload))
        authority=self.authority(d['scopeSha256'],proof)
        _orchestration_authority(self.repo,authority,request,d)
        request['targetOutcomeId']='INT-THIRD'
        with self.assertRaisesRegex(ValueError,'exact campaign'):
            _orchestration_authority(self.repo,authority,request,d)


    def test_heartbeat_cannot_substitute_for_launch_or_improvement(self):
        self.native_plan(budget=1); self.start(); self.fail()
        self.observe('heartbeat',1,'worker-a',activityId='implement')
        with self.assertRaisesRegex(ValueError,'request_owner_choice'):
            self.start()
        self.assertEqual(assessment(campaign_for(self.document,'INT-ACCESS'))['totalAttempts'],1)

    def test_current_store_cas_and_actual_native_dispatch_preflight(self):
        self.native_plan()
        d = self.document['deliveries'][0]
        envelope = dict(actionVersion='native-1',action='native_activity',authorityStatePath='.aim/product-backlog.json',
            expectedStoreSha256=self.token,deliveryId='DI-1',activityId='implement',scopeSha256=d['scopeSha256'],
            coordinatorSession='native-coordinator',session='native-coordinator',actionKey='restore-original-journey')
        self.assertTrue(capture_action_target(self.repo,envelope)['native'])
        self.start(); self.fail()
        with self.assertRaisesRegex(CodexBridgeError,'changed'):
            capture_action_target(self.repo,envelope)
        envelope['expectedStoreSha256']=self.token
        envelope['authorityStatePath']='.aim/other/product-backlog.json'
        with self.assertRaisesRegex(CodexBridgeError,'exact'):
            capture_action_target(self.repo,envelope)

    def test_cli_status_recovers_durable_campaign_without_mutation(self):
        self.native_plan(); self.start(); self.fail()
        before = (self.repo/'.aim/product-backlog.json').read_bytes()
        command=[sys.executable,str(ROOT/'scripts/aim_orchestrate.py'),'status','--repo',str(self.repo)]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        state=json.loads(result.stdout)
        self.assertEqual(state['campaigns'][0]['totalAttempts'],1)
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),before)

    def test_native_projection_exposes_contract_and_blocks_unactivated_or_exhausted_work(self):
        from aim_stories import project_story_board
        self.native_plan(budget=1,activate=False)
        graph=project_story_board(self.repo)['executionGraph']
        self.assertEqual(graph['recommendedIds'],[])
        self.assertIn('Activate',graph['activities'][0]['nativeBlocker'])
        self.assertEqual(graph['activities'][0]['assignment']['nativeContract']['origin']['kind'],'custom')
        self.activate();self.start();self.fail()
        graph=project_story_board(self.repo)['executionGraph']
        self.assertNotIn('implement',graph['recommendedIds'])
        self.assertIn('request_owner_choice',graph['activities'][0]['nativeBlocker'])

    def test_read_only_review_and_inline_checkpoint_remain_available_at_budget_boundary(self):
        import base64
        self.native_plan(budget=1)
        original=(self.repo/'app.py').read_bytes()
        self.observe('baseline',0,'native-coordinator',baselineId='retained-source',comparisonKey='original-journey',metric='success',direction='higher',value=0,usable=True)
        self.start();self.finish()
        self.start(activity='integrate-review',session='separate-reviewer',key='independent-reference-review')
        self.finish(activity='integrate-review')
        c=campaign_for(self.document,'INT-ACCESS')
        self.assertEqual(assessment(c)['totalAttempts'],1)
        (self.repo/'app.py').write_text('A later broken source version')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/aim_orchestrate.py'),'checkpoint','--repo',str(self.repo),'--outcome','INT-ACCESS'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        checkpoint=json.loads(result.stdout)['sourceCheckpoint']
        self.assertEqual(base64.b64decode(checkpoint['files'][0]['contentBase64']),original)

    def test_git_checkpoint_verifies_exact_source_and_supports_large_selected_module(self):
        from aim_stories import _orchestration_checkpoint
        source=self.repo/'app.py'
        source.write_text('x' * 300000)
        for args in [('init',),('add','app.py'),('-c','user.email=fixture@example.test','-c','user.name=Fixture','commit','-m','Known usable source')]:
            subprocess.run(['git','-C',str(self.repo),*args],capture_output=True,check=True)
        commit=subprocess.run(['git','-C',str(self.repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        refs=[dict(path='app.py',sha256=hashlib.sha256(source.read_bytes()).hexdigest())]
        self.assertEqual(_orchestration_checkpoint(self.repo,refs,commit)['kind'],'git')
        with self.assertRaisesRegex(ValueError,'256 KiB'):
            _orchestration_checkpoint(self.repo,refs)
        refs[0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'differ'):
            _orchestration_checkpoint(self.repo,refs,commit)

    def test_git_checkpoint_oversize_and_timeout_reject_without_ledger_change(self):
        from types import SimpleNamespace
        self.native_plan()
        observation=dict(outcomeId='INT-ACCESS',kind='baseline',session='native-coordinator',attempt=0,
            baselineId='existing-source',comparisonKey='original-journey',metric='success',direction='higher',value=0,usable=True)
        from aim_quality.orchestration_runtime import digest
        bindings=[dict(path='app.py',sha256=hashlib.sha256((self.repo/'app.py').read_bytes()).hexdigest())]
        report=dict(orchestrationObservationVersion=1,deliveryId='DI-1',scopeSha256=self.document['deliveries'][0]['scopeSha256'],
                    sourceBindingsSha256=digest(bindings),observation=observation)
        proof=self.artifact('git-baseline-observation.json',json.dumps(report))
        commit='a'*40
        request=dict(deliveryId='DI-1',action='observe',coordinatorSession='native-coordinator',outcomeId='INT-ACCESS',
            observation=observation,evidence=[proof],sourcePaths=['app.py'],sourceCommit=commit)
        before=(self.repo/'.aim/product-backlog.json').read_bytes()
        calls=[]
        def oversized(command,**kwargs):
            calls.append(command)
            if 'rev-parse' in command:
                return SimpleNamespace(returncode=0,stdout=(commit+'\n').encode())
            if '-s' in command:
                return SimpleNamespace(returncode=0,stdout=b'1000001\n')
            self.fail('Oversized Git blob must never be read.')
        with patch('subprocess.run',side_effect=oversized):
            with self.assertRaisesRegex(StoryError,'size limit'):
                self.mutate('orchestrate',request)
        self.assertFalse(any('blob' in call for call in calls))
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),before)
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired(['git'],10)):
            with self.assertRaisesRegex(StoryError,'timed out'):
                self.mutate('orchestrate',request)
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),before)


    def test_owner_priority_applies_across_campaigns_and_does_not_deadlock_cohesive_work(self):
        from aim_quality.orchestration_runtime import change_orchestration, check_activity
        self.native_plan()
        document=copy.deepcopy(self.document)
        d=document['deliveries'][0]
        second=copy.deepcopy(document['orchestration']['campaigns'][0])
        second['outcomeId']='INT-SECOND'
        second['campaign']['outcomeId']='INT-SECOND'
        second['campaign']['waitingOriginalGoals']=['INT-ACCESS','INT-SECOND']
        document['orchestration']['campaigns'].append(second)
        document['intents'].append(dict(id='INT-SECOND',statement='A second original outcome'))
        document['epics'].append(dict(id='EPIC-SECOND',intentId='INT-SECOND',status='open'))
        d['executionPlan']['orchestration']['outcomes'].append(dict(id='INT-SECOND',requirement='A second original outcome',paths=['app.py']))
        node=d['executionPlan']['orchestration']['nodes'][0]
        node['outcomeIds'].append('INT-SECOND')
        document['orchestration']['ownerPriority']=['INT-ACCESS','INT-SECOND']
        request=dict(activityId='implement',coordinatorSession='native-coordinator',actionKey='cohesive-original-outcomes')
        # A cohesive node covering both goals respects the first-priority goal.
        check_activity(document,d,request,check_reference=lambda r:None)
        # A branch serving only the later goal must wait for earlier actual work.
        node['outcomeIds']=['INT-SECOND']
        first=copy.deepcopy(node);first.update(id='first-branch',outcomeIds=['INT-ACCESS'])
        d['executionPlan']['orchestration']['nodes'].append(first)
        with self.assertRaisesRegex(ValueError,'work_owner_priority_first'):
            check_activity(document,d,request,check_reference=lambda r:None)
        d['activityReceipts']=[dict(activityId='first-branch',status='completed',sourceBindings=[],evidence=[])]
        check_activity(document,d,request,check_reference=lambda r:None)


    def envelope(self, **changes):
        d = self.document['deliveries'][0]
        result = dict(actionVersion='native-1',action='native_activity',authorityStatePath='.aim/product-backlog.json',
            expectedStoreSha256=self.token,deliveryId='DI-1',activityId='implement',scopeSha256=d['scopeSha256'],
            coordinatorSession='native-coordinator',session='native-coordinator',actionKey='restore-original-journey')
        result.update(changes)
        return result

    def test_real_async_dispatch_binds_start_and_observes_evidenced_result(self):
        from aim_codex_bridge import DispatchManager
        from test_aim_codex_bridge import FakeClient, wait_for
        self.native_plan()
        calls=[]
        case=self
        class WorkerClient(FakeClient):
            def request(self,method,params):
                result=super().request(method,params)
                if method=='turn/start':
                    document,token=load(case.repo)
                    r=document['deliveries'][0]['activityReceipts'][-1]
                    case.assertEqual(r['session'],'native-coordinator')
                    proof=case.artifact('host-result.txt','Actual bounded worker output, not a turn completion inference.')
                    execute(case.repo,'activity',dict(deliveryId='DI-1',activityId='implement',status='completed',
                        session='native-coordinator',attempt=r['attempt'],sourcePaths=['app.py'],evidence=[proof]),token)
                return result
        manager=DispatchManager(self.repo,'native-coordinator',ledger_path=self.repo/'transport.json',client_factory=lambda:WorkerClient(calls))
        queued=manager.dispatch(self.envelope(),'exact native assignment')
        complete=wait_for(manager,queued['id'],{'completed'})
        self.assertTrue(complete['result']['verified'])
        self.assertEqual(sum(m=='turn/start' for m,_ in calls),1)
        document,_=load(self.repo)
        self.assertEqual(len(campaign_for(document,'INT-ACCESS')['attempts']),1)
        manager.dispatch(self.envelope(),'duplicate')
        self.assertEqual(sum(m=='turn/start' for m,_ in calls),1)

    def test_real_async_dispatch_rechecks_queued_store_before_turn_start(self):
        from aim_codex_bridge import DispatchManager
        from test_aim_codex_bridge import FakeClient, wait_for
        self.native_plan()
        calls=[]
        case=self
        class ChangingClient(FakeClient):
            def request(self,method,params):
                result=super().request(method,params)
                if method=='thread/resume':
                    case.activate(session='new-coordinator',previousCoordinatorSession='native-coordinator')
                return result
        manager=DispatchManager(self.repo,'native-coordinator',ledger_path=self.repo/'transport.json',client_factory=lambda:ChangingClient(calls))
        queued=manager.dispatch(self.envelope(),'exact assignment')
        wait_for(manager,queued['id'],{'rejected'})
        self.assertFalse(any(m=='turn/start' for m,_ in calls))
        self.assertEqual(campaign_for(self.document,'INT-ACCESS')['attempts'],[])

    def test_budget_and_wrong_actual_host_prevent_real_turn_start(self):
        from aim_codex_bridge import DispatchManager
        from test_aim_codex_bridge import FakeClient, wait_for
        self.native_plan(budget=1)
        calls=[]
        manager=DispatchManager(self.repo,'wrong-actual-thread',ledger_path=self.repo/'transport.json',client_factory=lambda:FakeClient(calls))
        queued=manager.dispatch(self.envelope(),'exact assignment')
        wait_for(manager,queued['id'],{'rejected'})
        self.assertFalse(any(m=='turn/start' for m,_ in calls))
        self.start();self.fail()
        with self.assertRaisesRegex(CodexBridgeError,'request_owner_choice'):
            manager.dispatch(self.envelope(),'forbidden same work')
        self.assertFalse(any(m=='turn/start' for m,_ in calls))


class CampaignContinuityTests(unittest.TestCase):
    def test_baseline_identity_and_regression_cannot_launder_highwater(self):
        def baseline(identifier,value,attempt):
            return dict(outcomeId='ORIGINAL',kind='baseline',session='c',attempt=attempt,baselineId=identifier,
                comparisonKey='same-journey',metric='success',direction='higher',value=value,usable=True)
        def progress(identifier,value,attempt):
            return dict(outcomeId='ORIGINAL',kind='integrated_progress',session='w',attempt=attempt,baselineId=identifier,
                comparisonKey='same-journey',metric='success',direction='higher',value=value)
        for new_baseline,new_value in [(1,2),(15,14)]:
            c=dict(version=1,outcomeId='ORIGINAL',attemptBudget=8,waitingOriginalGoals=['ORIGINAL'],
                observations=[baseline('b1',10,0),progress('b1',12,1),
                    dict(outcomeId='ORIGINAL',kind='activity',session='new',attempt=2),
                    baseline('b2',new_baseline,2),progress('b2',new_value,3)])
            self.assertEqual(assess_campaign(c)['noProgressStreak'],2)
        self.assertEqual(assess_campaign(c)['resources']['coverage'],'partial_or_unavailable')

if __name__=='__main__': unittest.main()
