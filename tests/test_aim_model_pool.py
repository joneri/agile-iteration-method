"""Original user examples through real Native ledgers and the launch consumer.

Mandates/host telemetry in temporary repositories are explicitly synthetic.
Literal launch expectations below are independent of the model-pool resolver.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_aim_orchestration_runtime as runtime_fixture
from aim_stories import FILE, dispatch_check, execute, model_budget_context
from aim_quality.orchestration import construct_default_graph
from aim_quality.orchestration_runtime import prepare_plan
from aim_quality.model_pool import projection, validate_pool
from aim_codex_bridge import capture_action_target, CodexBridgeError


ROOT = Path(__file__).resolve().parents[1]

CHOICES = [dict(id='luna', model='gpt-6-luna', reasoningEffort='xhigh'),
           dict(id='sol', model='gpt-6.1-sol', reasoningEffort='medium'),
           dict(id='astra', model='gpt-6-astra', reasoningEffort='medium')]


class ModelPoolTests(unittest.TestCase):
    setUp = runtime_fixture.NativeRuntimeTests.setUp
    artifact = runtime_fixture.NativeRuntimeTests.artifact
    mutate = runtime_fixture.NativeRuntimeTests.mutate
    authority = runtime_fixture.NativeRuntimeTests.authority
    activate = runtime_fixture.NativeRuntimeTests.activate

    def plan_pool(self, max_starts=6, cost_limit=None, pool=True, owner=None, campaign_budget=8):
        graph = construct_default_graph('cohesive_delivery',
            [dict(id='INT-ACCESS', requirement=self.document['intents'][0]['statement'], paths=['app.py'])],
            dict(session='native-coordinator', capability=dict(id='aim-native-orchestrator', version='4.8.0'),
                 permittedDecisions=['continue_bounded', 'request_owner_choice']),
            dict(delegationAllowed=True, maxWorkers=3, checkpointAttemptBudget=campaign_budget,
                 parallelBenefit='Independent read-only worker fixtures with disjoint results.'))
        original, review = graph['nodes']
        graph['origin'] = dict(kind='custom', reference='approved-three-child-fixture')
        graph['nodes'] = [{**copy.deepcopy(original), 'id':'read-'+str(i), 'kind':'read'} for i in range(1, 4)]
        review['dependsOn'] = ['read-1', 'read-2', 'read-3']
        graph['nodes'].append(review)
        plan = prepare_plan(graph, {'US-BUYER':['INT-ACCESS']})
        if pool:
            budget = dict(maxStarts=max_starts)
            if cost_limit is not None:
                budget['costLimit'] = dict(unit='credits', amount=cost_limit)
            plan['modelPool'] = dict(version=1, choices=copy.deepcopy(CHOICES), budget=budget)
        self.mutate('plan', dict(id='DI-1', title='Approved child routing', goal='Use the right approved settings',
            storyIds=['US-BUYER'], planEvidence=[self.plan_evidence], executionPlan=plan,
            **({'deliveryPolicy':dict(mode='ship',owner=owner)} if owner else {})))
        self.mutate('approve', dict(deliveryId='DI-1', authority=self.authority(self.document['deliveries'][0]['scopeSha256'])))
        self.activate()

    def delegated_pool(self, campaign_budget=8, cost_limit=None):
        mandate = self.artifact('resource-mandate.md', 'Synthetic human mandate: owner-root / owner-session may authorize at most two additional starts, including explicitly shared campaign/pool grants. No monetary increase.')
        owner = dict(kind='agent', id='owner-root', session='owner-session', mandate=mandate,
                     decisions=['orchestrate'], maxAdditionalAttempts=2)
        self.plan_pool(max_starts=1, owner=owner, campaign_budget=campaign_budget, cost_limit=cost_limit)
        proof = self.artifact('upstream.md', 'Synthetic actual owner activation.')
        self.mutate('orchestrate',dict(deliveryId='DI-1', action='activate', coordinatorSession='native-coordinator',
            previousCoordinatorSession='native-coordinator', evidence=[proof], dispatchers=[
                dict(session=session, capability=dict(id='aim-native-orchestrator',version='4.8.0'),evidence=[proof])
                for session in ['native-coordinator','owner-session']]))
        return owner

    def budget_answer(self, count=2, grant=None):
        request = dict(deliveryId='DI-1',coordinatorSession='native-coordinator',additionalStarts=count,
                       reason='Synthetic actual scoped resource owner authorizes this bounded continuation.')
        if grant:
            request['resourceGrant'] = grant
        preview = model_budget_context(self.repo, request)
        proof = self.artifact('pool-answer-'+str(self.document['revision'])+'.json', json.dumps(preview['decisionEvidence']))
        authority = dict(kind='user', **proof, scopeSha256=preview['scopeSha256'])
        owner = self.document['deliveries'][0].get('deliveryPolicy',{}).get('owner',{})
        if owner.get('kind') == 'agent':
            authority.update(kind='agent',id=owner['id'],session=owner['session'])
        return {**request,'authority':authority}

    def campaign_grant(self):
        from aim_quality.orchestration_runtime import summary,digest,campaign_for
        context = summary(self.document)['pendingDecisions'][0]['context']
        context.update(id='owner-root',session='owner-session',additionalAttempts=2,
                       decision='continue_bounded',actionKey='bounded-pool-correction')
        proof = self.artifact('campaign-answer.json',json.dumps(context))
        request = {key:context[key] for key in ['outcomeId','contextSha256','decision','actionKey','additionalAttempts']}
        request.update(deliveryId='DI-1',action='decide',coordinatorSession='native-coordinator',
                       reason='Synthetic actual owner grants two starts shared with the pool.',evidence=[proof],
                       authority=dict(kind='agent',id='owner-root',session='owner-session',scopeSha256=context['scopeSha256'],**proof))
        self.mutate('orchestrate',request)
        grant = campaign_for(self.document,'INT-ACCESS')['decisions'][-1]
        return dict(outcomeId='INT-ACCESS',decisionSha256=digest(grant))

    def next_diagnostic(self, index):
        from aim_quality.orchestration_runtime import assessment,campaign_for
        current=assessment(campaign_for(self.document,'INT-ACCESS'),owner_priority=[])
        action='explicit-next-'+str(index)
        self.mutate('orchestrate',dict(deliveryId='DI-1',action='decide',coordinatorSession='native-coordinator',
            outcomeId='INT-ACCESS',contextSha256=current['contextSha256'],decision='continue_bounded',
            actionKey=action,reason='Synthetic consequential transition to the next independent input.',evidence=[self.evidence]))
        request=self.start_request(index=index);request['actionKey']=action
        self.mutate('activity',request)

    def test_pool_extension_preserves_frozen_history_and_rejects_stale_owner_and_cap(self):
        from aim_quality.orchestration_runtime import _delegated_grants
        owner = self.delegated_pool()
        self.start(); self.end()
        before = copy.deepcopy(self.document['deliveries'][0])
        answer = self.budget_answer()
        preview_request={k:v for k,v in answer.items() if k!='authority'}
        cli=subprocess.run([sys.executable,str(ROOT/'scripts/aim_stories.py'),'--repo',str(self.repo),
                            'model-budget-context','--input','-'],input=json.dumps(preview_request),
                           text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(cli.stdout)['scopeSha256'],answer['authority']['scopeSha256'])
        bad = copy.deepcopy(answer); bad['authority']['session']='wrong-owner'
        self.assert_rejected_without_write_command('model-budget',bad,'identity')
        with self.assertRaisesRegex(ValueError,'delegated resource allowance'):
            self.budget_answer(count=3)
        stale=copy.deepcopy(answer);stale['authority']['scopeSha256']='0'*64
        self.assert_rejected_without_write_command('model-budget',stale,'stale context')
        self.mutate('model-budget',answer)
        delivery = self.document['deliveries'][0]
        self.assertEqual(delivery['executionPlan'],before['executionPlan'])
        self.assertEqual(delivery['scopeSha256'],before['scopeSha256'])
        self.assertEqual(delivery['activityReceipts'],before['activityReceipts'])
        self.assertEqual(_delegated_grants(self.document,owner),2)
        self.assert_rejected_without_write_command('model-budget',answer,'remaining model allowance')
        self.start(index=2); self.end(index=2)
        self.next_diagnostic(index=3); self.end(index=3)
        request=self.start_request(); request['activityId']='integrate-review'
        self.assert_rejected_without_write(request,'allowance is exhausted')
        with self.assertRaisesRegex(ValueError,'delegated resource allowance'):
            self.budget_answer(count=1)

    def assert_rejected_without_write_command(self, command, request, pattern):
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,pattern):
            self.mutate(command,request)
        self.assertEqual((self.repo/FILE).read_bytes(),before)

    def test_shared_campaign_pool_grant_counts_once_and_third_start_rejects(self):
        from aim_quality.orchestration_runtime import _delegated_grants
        owner=self.delegated_pool(campaign_budget=1)
        self.start(); self.end()
        grant=self.campaign_grant()
        self.mutate('model-budget',self.budget_answer(grant=grant))
        self.assertEqual(_delegated_grants(self.document,owner),2)
        request=self.start_request(index=2);request['actionKey']='bounded-pool-correction'
        self.mutate('activity',request);self.end(index=2)
        self.next_diagnostic(index=3);self.end(index=3)
        request=self.start_request();request['activityId']='integrate-review'
        self.assert_rejected_without_write(request,'allowance is exhausted')
        with self.assertRaisesRegex(ValueError,'remaining linked resource grant|already funds'):
            self.budget_answer(count=1,grant=grant)

    def test_shared_grant_retains_pre_amendment_coordinator_consumption(self):
        self.delegated_pool(campaign_budget=1)
        self.start();self.end()
        grant=self.campaign_grant()
        request=self.start_request(index=2,session='native-coordinator')
        request.pop('modelSelection');request['actionKey']='bounded-pool-correction'
        self.mutate('activity',request);self.end(index=2)
        with self.assertRaisesRegex(ValueError,'remaining linked resource grant'):
            self.budget_answer(count=2,grant=grant)
        self.mutate('model-budget',self.budget_answer(count=1,grant=grant))
        self.next_diagnostic(index=3);self.end(index=3)
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['remainingStarts'],0)

    def test_start_extension_cannot_raise_cost_limit_or_erase_unknown_spend(self):
        self.plan_pool(max_starts=1,cost_limit=1)
        self.start(estimate=1);self.end()
        with self.assertRaisesRegex(ValueError,'not delegated'):
            model_budget_context(self.repo,dict(deliveryId='DI-1',coordinatorSession='native-coordinator',
                additionalStarts=1,reason='Synthetic denied undelegated resource decision.',ownerKind='agent'))
        self.mutate('model-budget',self.budget_answer(count=1))
        self.assert_rejected_without_write(self.start_request(index=2,estimate=.01),'cost allowance')
        state=projection(self.document['deliveries'][0])
        self.assertEqual(state['budget']['costLimit'],dict(unit='credits',amount=1))
        self.assertEqual(state['usage']['unknownActualCosts'],1)

    def start_request(self, index=1, choice='luna', estimate=None, session=None):
        selected = dict(choiceId=choice, task='Inspect the assigned recovery input',
                        risk='Read-only fixture with literal expected result',
                        budgetReason='Within the approved cumulative child allowance')
        if estimate is not None:
            selected['estimatedCost'] = dict(unit='credits', amount=estimate)
        return dict(deliveryId='DI-1', activityId='read-'+str(index), status='running',
                    session=session or 'child-'+choice, coordinatorSession='native-coordinator',
                    actionKey='child-'+str(index)+'-'+str(self.document['revision']), modelSelection=selected)

    def start(self, **kwargs):
        return self.mutate('activity', self.start_request(**kwargs))

    def end(self, index=1, status='completed', observation=None):
        receipt = next(r for r in reversed(self.document['deliveries'][0]['activityReceipts']) if r['activityId']=='read-'+str(index))
        request = dict(deliveryId='DI-1',activityId=receipt['activityId'],status=status,
                       session=receipt['session'],attempt=receipt['attempt'])
        if status=='completed':
            request.update(sourcePaths=['app.py'], evidence=[self.evidence])
        else:
            request['reason']='Synthetic failed child; preserve reservation and configuration.'
        if observation is not None:
            report = dict(modelObservationVersion=1, deliveryId='DI-1',
                scopeSha256=self.document['deliveries'][0]['scopeSha256'], activityId=receipt['activityId'],
                session=receipt['session'],attempt=receipt['attempt'],source='host',dispatchAccepted=True,
                model=receipt['modelSelection']['requested']['model'],
                reasoningEffort=receipt['modelSelection']['requested']['reasoningEffort'],actualCost=None)
            report.update(observation)
            request['modelObservation']=self.artifact('model-observation-'+str(self.document['revision'])+'.json',json.dumps(report))
        return self.mutate('activity',request)

    def observe_running(self, index=1, **observation):
        receipt=next(r for r in reversed(self.document['deliveries'][0]['activityReceipts']) if r['activityId']=='read-'+str(index))
        report=dict(modelObservationVersion=1,deliveryId='DI-1',scopeSha256=self.document['deliveries'][0]['scopeSha256'],
                    activityId=receipt['activityId'],session=receipt['session'],attempt=receipt['attempt'],
                    source='host',dispatchAccepted=True,model=receipt['modelSelection']['requested']['model'],
                    reasoningEffort=receipt['modelSelection']['requested']['reasoningEffort'],actualCost=None)
        report.update(observation)
        ref=self.artifact('running-model-'+str(self.document['revision'])+'.json',json.dumps(report))
        return self.mutate('activity',dict(deliveryId='DI-1',activityId=receipt['activityId'],status='running',
            session=receipt['session'],attempt=receipt['attempt'],coordinatorSession='native-coordinator',
            actionKey='observe-current-child',modelObservation=ref))

    def assert_rejected_without_write(self, request, pattern):
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,pattern):
            self.mutate('activity',request)
        self.assertEqual((self.repo/FILE).read_bytes(),before)

    def test_three_literal_pairs_reach_native_spawn_consumer_with_explicit_context(self):
        self.plan_pool(max_starts=3)
        calls=[]
        expected=[dict(model='gpt-6-luna',reasoning_effort='xhigh',fork_turns='none'),
                  dict(model='gpt-6.1-sol',reasoning_effort='medium',fork_turns='none'),
                  dict(model='gpt-6-astra',reasoning_effort='medium',fork_turns='none')]
        for index,choice in enumerate(('luna','sol','astra'),start=1):
            request=self.start_request(index=index,choice=choice)
            before=(self.repo/FILE).read_bytes()
            # Real CLI consumer: a missing model/effort would inherit defaults.
            p=subprocess.run([sys.executable,str(runtime_fixture.ROOT/'scripts/aim_stories.py'),'--repo',str(self.repo),
                'dispatch-check','--expected-sha256',self.token],input=json.dumps(request),capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            preview=json.loads(p.stdout)
            spawn=preview['prospectiveAttempt']['modelSelection']['spawnRequest']
            self.assertEqual(spawn,expected[index-1])
            self.assertEqual((self.repo/FILE).read_bytes(),before)
            self.mutate('activity',request)
            def native_spawn(*,model='INHERITED',reasoning_effort='INHERITED',fork_turns='all'):
                calls.append(dict(model=model,reasoning_effort=reasoning_effort,fork_turns=fork_turns))
                return dict(session='child-'+choice,model=model,reasoningEffort=reasoning_effort)
            result=native_spawn(**spawn)
            self.assertEqual(result['session'],request['session'])
        self.assertEqual(calls,expected)
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['usedStarts'],3)

    def test_invalid_choice_and_missing_rationale_reject_before_start(self):
        self.plan_pool()
        cases=[]
        invalid=self.start_request(choice='outside-pool');cases.append(invalid)
        for field in ('task','risk','budgetReason'):
            request=self.start_request();request['modelSelection'][field]='';cases.append(request)
        request=self.start_request();request['modelSelection']['requested']={'model':'unapproved','reasoningEffort':'max'};cases.append(request)
        for request in cases:
            self.assert_rejected_without_write(request,'outside|nonempty|unsupported')

    def test_model_and_reasoning_are_approved_pairs_not_cartesian_lists(self):
        self.plan_pool()
        request=self.start_request();request['modelSelection']['reasoningEffort']='medium'
        self.assert_rejected_without_write(request,'unsupported')
        self.start()
        self.assertEqual(self.document['deliveries'][0]['activityReceipts'][-1]['modelSelection']['requested'],
                         {'model':'gpt-6-luna','reasoningEffort':'xhigh'})

    def test_start_allowance_survives_failed_retry_and_session_change(self):
        self.plan_pool(max_starts=1)
        self.start();self.end(status='failed')
        self.assert_rejected_without_write(self.start_request(session='replacement-child'),'allowance is exhausted')

    def test_cost_cap_requires_explicit_known_estimate_and_counts_concurrent_reservations(self):
        self.plan_pool(cost_limit=1)
        self.assert_rejected_without_write(self.start_request(),'explicit cost estimate')
        self.start(estimate=.6)
        self.assert_rejected_without_write(self.start_request(index=2,choice='sol',estimate=.5),'cost allowance')
        self.start(index=2,choice='sol',estimate=.4)

    def test_decimal_boundary_is_not_binary_float_budget_error(self):
        self.plan_pool(cost_limit=.3)
        self.start(estimate=.1);self.start(index=2,choice='sol',estimate=.2)
        usage=projection(self.document['deliveries'][0])['usage']
        self.assertEqual(usage['reservedEstimate'],'0.3')
        self.assertEqual(usage['unknownActualCosts'],2)
        self.assertFalse(usage['actualCostKnown'])

    def test_large_finite_budget_does_not_round_away_an_extra_reservation(self):
        self.plan_pool(cost_limit=10**30)
        self.start(estimate=10**30)
        self.assert_rejected_without_write(self.start_request(index=2,choice='sol',estimate=1),'cost allowance')

    def test_exact_tiny_decimal_boundary_is_not_rounded_when_rendered(self):
        from aim_quality.model_pool import _amount, _display
        total=sum((_amount(x) for x in [8.673617379884e-19,3.5472059622406e-33,9.5953369140625e-47]))
        self.assertEqual(_display(total),'0.000000000000000000867361737988403547205962240695953369140625')

    def test_running_known_overrun_blocks_new_start_without_new_attempt_or_campaign_entry(self):
        self.plan_pool(cost_limit=1);self.start(estimate=.4)
        before=copy.deepcopy(self.document['deliveries'][0]['activityReceipts'][0]['modelSelection'])
        attempts=len(self.document['orchestration']['campaigns'][0]['attempts'])
        self.observe_running(actualCost={'unit':'credits','amount':1.2})
        receipt=self.document['deliveries'][0]['activityReceipts'][0]
        self.assertEqual(receipt['status'],'running')
        self.assertEqual(receipt['attempt'],1)
        self.assertEqual(receipt['modelSelection'],before)
        self.assertEqual(len(self.document['orchestration']['campaigns'][0]['attempts']),attempts)
        self.assert_rejected_without_write(self.start_request(index=2,choice='sol',estimate=.4),'cost allowance')

    def test_running_unknown_or_lower_report_cannot_erase_known_spend(self):
        self.plan_pool(cost_limit=1);self.start(estimate=.4)
        self.observe_running(actualCost={'unit':'credits','amount':1.2})
        self.observe_running(source='unknown',model=None,reasoningEffort=None,actualCost=None)
        self.observe_running(actualCost={'unit':'credits','amount':.1})
        usage=projection(self.document['deliveries'][0])['usage']
        self.assertEqual(usage['accountedCost'],'1.2')
        self.assertEqual(usage['unknownActualCosts'],0)
        self.assert_rejected_without_write(self.start_request(index=2,choice='sol',estimate=0),'cost allowance')
        self.end()
        self.assertEqual(len(self.document['deliveries'][0]['activityReceipts'][0]['modelObservationHistory']),2)

    def test_running_mismatch_cannot_be_hidden_by_later_matching_report(self):
        self.plan_pool();self.start()
        self.observe_running(model='wrong-child-model')
        self.observe_running()
        with self.assertRaisesRegex(ValueError,'Known child model mismatch'):
            self.end()
        self.end(status='failed')

    def test_observation_update_requires_current_coordinator_and_running_attempt(self):
        self.plan_pool();self.start();self.observe_running()
        r=self.document['deliveries'][0]['activityReceipts'][0]
        request=dict(deliveryId='DI-1',activityId='read-1',status='running',session=r['session'],attempt=1,
                     coordinatorSession='old-coordinator',modelObservation=r['modelObservation']['evidence'][0])
        self.assert_rejected_without_write(request,'current activated coordinator')
        request['coordinatorSession']='native-coordinator';request['attempt']=2
        self.assert_rejected_without_write(request,'stale session, attempt')
        self.end()
        request['attempt']=1
        self.assert_rejected_without_write(request,'only a running selected child')

    def test_reported_actual_overrun_blocks_later_work_without_invalidating_other_valid_starts(self):
        self.plan_pool(cost_limit=1)
        self.start(estimate=.4);self.start(index=2,choice='sol',estimate=.4)
        self.end(observation={'actualCost':{'unit':'credits','amount':.8}})
        self.assert_rejected_without_write(self.start_request(index=3,choice='astra',estimate=0),'cost allowance')
        self.end(index=2)
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['accountedCost'],'1.2')

    def test_lower_actual_cost_does_not_refund_the_original_reservation(self):
        self.plan_pool(cost_limit=1)
        self.start(estimate=.8);self.end(observation={'actualCost':{'unit':'credits','amount':.1}})
        self.assert_rejected_without_write(self.start_request(index=2,choice='sol',estimate=.3),'cost allowance')

    def test_unknown_or_worker_report_is_never_host_confirmation(self):
        self.plan_pool();self.start();self.end()
        receipt=self.document['deliveries'][0]['activityReceipts'][-1]
        self.assertEqual(receipt['modelObservation']['source'],'unknown')
        self.assertIsNone(receipt['modelObservation']['model'])
        self.start(index=2,choice='sol');self.end(index=2,observation={'source':'worker'})
        self.assertEqual(projection(self.document['deliveries'][0],self.document['deliveries'][0]['activityReceipts'][-1])['observation']['source'],'worker')

    def test_wrong_observation_scope_session_attempt_and_unrelated_hash_reject(self):
        self.plan_pool();self.start()
        for change in ({'session':'another-child'},{'scopeSha256':'0'*64},{'attempt':99}):
            before=(self.repo/FILE).read_bytes()
            with self.assertRaisesRegex(ValueError,'another scope, child or attempt'):
                self.end(observation=change)
            self.assertEqual((self.repo/FILE).read_bytes(),before)
        receipt=self.document['deliveries'][0]['activityReceipts'][-1]
        self.assert_rejected_without_write(dict(deliveryId='DI-1',activityId='read-1',status='failed',session=receipt['session'],attempt=1,reason='host failed',modelObservation=self.evidence),'JSON evidence')

    def test_mismatch_is_not_success_but_failed_attempt_retains_report_and_budget(self):
        self.plan_pool();self.start()
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,'Known child model mismatch'):
            self.end(observation={'model':'different-model'})
        self.assertEqual((self.repo/FILE).read_bytes(),before)
        self.end(status='failed',observation={'model':'different-model'})
        self.assertEqual(self.document['deliveries'][0]['activityReceipts'][-1]['modelObservation']['model'],'different-model')
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['usedStarts'],1)

    def test_root_work_keeps_its_model_and_does_not_claim_child_selection(self):
        self.plan_pool()
        request=self.start_request(session='native-coordinator')
        self.assert_rejected_without_write(request,'select children')
        request.pop('modelSelection');self.mutate('activity',request)
        receipt=self.document['deliveries'][0]['activityReceipts'][-1]
        self.assertNotIn('modelSelection',receipt)
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['usedStarts'],0)

    def test_bound_parent_bridge_rejects_pool_without_queue_or_ledger_mutation(self):
        self.plan_pool()
        d=self.document['deliveries'][0]
        envelope=dict(actionVersion='native-1',action='native_activity',authorityStatePath='.aim/product-backlog.json',
            expectedStoreSha256=self.token,deliveryId='DI-1',activityId='read-1',scopeSha256=d['scopeSha256'],
            coordinatorSession='native-coordinator',session='native-coordinator',actionKey='parent-must-not-switch')
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(CodexBridgeError,'bound-coordinator bridge'):
            capture_action_target(self.repo,envelope)
        self.assertEqual((self.repo/FILE).read_bytes(),before)

    def test_historical_inherited_plans_retain_behavior_and_reject_unapproved_model_fields(self):
        self.plan_pool(pool=False)
        self.assert_rejected_without_write(self.start_request(),'explicitly approved model pool')
        request=self.start_request();request.pop('modelSelection');self.mutate('activity',request)
        self.assertNotIn('modelSelection',self.document['deliveries'][0]['activityReceipts'][-1])

    def test_rework_preserves_child_start_reservations(self):
        self.plan_pool(max_starts=4)
        for index,choice in enumerate(('luna','sol','astra'),1):
            self.start(index=index,choice=choice);self.end(index=index)
        request=self.start_request(choice='sol',session='independent-review-child')
        request['activityId']='integrate-review';self.mutate('activity',request)
        self.mutate('activity',dict(deliveryId='DI-1',activityId='integrate-review',status='completed',
            session='independent-review-child',attempt=1,sourcePaths=['app.py'],evidence=[self.evidence]))
        # A material review can require correction; no new allowance is granted.
        self.mutate('review',dict(deliveryId='DI-1',sourcePaths=['app.py']))
        self.mutate('rework',dict(deliveryId='DI-1',reason='Independent review requires correction'))
        self.assertEqual(projection(self.document['deliveries'][0])['usage']['usedStarts'],4)
        self.assert_rejected_without_write(self.start_request(session='rework-child'),'allowance is exhausted')

    def test_profile_candidate_needs_approval_and_valid_resource_values(self):
        from aim_quality.skills import role_skill_issues
        candidate=dict(version=1,choices=copy.deepcopy(CHOICES),budget=dict(maxStarts=3))
        profile=dict(aimProjectRoles=dict(orchestration=dict(modelPolicy='approved-pool',modelPool=candidate)))
        self.assertEqual(role_skill_issues(self.repo,profile),[])
        self.plan_pool(pool=False)
        # An otherwise valid local candidate does not change the approved plan.
        (self.repo/'aim.roles.yaml').write_text(json.dumps(profile))
        self.assert_rejected_without_write(self.start_request(),'explicitly approved model pool')
        for invalid in (-1,True,float('inf'),float('nan')):
            pool=copy.deepcopy(candidate);pool['budget']['costLimit']=dict(unit='credits',amount=invalid)
            with self.assertRaisesRegex(ValueError,'finite nonnegative'):
                validate_pool(pool)

    def test_retained_selection_and_observation_bytes_cannot_be_relabelled(self):
        self.plan_pool();self.start();self.observe_running()
        from aim_stories import validate_document
        corrupted=copy.deepcopy(self.document)
        corrupted['deliveries'][0]['activityReceipts'][0]['modelSelection']['poolSha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Recorded model selection'):
            validate_document(corrupted)
        receipt=self.document['deliveries'][0]['activityReceipts'][0]
        artifact=self.repo/receipt['modelObservation']['evidence'][0]['path']
        artifact.write_text(artifact.read_text().replace('gpt-6-luna','other-model'))
        with self.assertRaisesRegex(ValueError,'Evidence changed'):
            self.end()

    def test_distributed_schemas_enforce_nullable_observations_and_budget_bounds(self):
        from aim_validator.schema_subset import validate, unsupported_keywords
        schema=json.loads((runtime_fixture.ROOT/'schemas/aim-product-backlog.schema.json').read_text())
        self.assertEqual(unsupported_keywords(schema),[])
        observation={'$ref':'#/$defs/modelObservation', '$defs':schema['$defs']}
        base=dict(source='unknown',dispatchAccepted=None,model=None,reasoningEffort=None,actualCost=None,evidence=[])
        self.assertEqual(validate(base,observation),[])
        for field,value in [('model',42),('reasoningEffort',True),('actualCost','free'),('dispatchAccepted','yes')]:
            with self.subTest(field=field):
                self.assertTrue(validate({**base,field:value},observation))
        pool_schema={'$ref':'#/$defs/modelPool','$defs':schema['$defs']}
        pool=dict(version=1,choices=copy.deepcopy(CHOICES),budget=dict(maxStarts=256))
        self.assertEqual(validate(pool,pool_schema),[])
        for invalid in (-1,257,True):
            pool['budget']['maxStarts']=invalid
            self.assertTrue(validate(pool,pool_schema))
        # Unsupported keywords inside an alternative must not evade inspection.
        self.assertTrue(unsupported_keywords({'anyOf':[{'unevaluatedProperties':False}]}))


if __name__=='__main__':
    unittest.main()
