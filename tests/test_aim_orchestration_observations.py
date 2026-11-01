"""Actual ledger regressions for PR #14's two observation review findings."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_aim_orchestration_runtime as fixtures
from aim_quality.orchestration import construct_default_graph
from aim_quality.orchestration_runtime import prepare_plan, campaign_for, assessment, summary
from aim_stories import digest

ROOT = Path(__file__).resolve().parents[1]


class ObservationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.NativeRuntimeTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.repo = self.case.repo
        (self.repo / 'other.py').write_text('other outcome or activity\n')
        (self.repo / 'helper.py').write_text('shared helper\n')

    def plan(self, *, multiple_outcomes=False, dependency=False):
        c = self.case
        outcomes = [dict(id='INT-ACCESS', requirement=c.document['intents'][0]['statement'],
                         paths=['app.py', 'helper.py'] if multiple_outcomes else ['app.py', 'other.py'])]
        mapping = {'US-BUYER': ['INT-ACCESS']}
        if multiple_outcomes:
            request = copy.deepcopy(c.request)
            request['intents'].append(dict(id='INT-SUPPORT', statement='Explain support state.'))
            request['epics'][1]['intentId'] = 'INT-SUPPORT'
            c.mutate('import', request)
            outcomes.append(dict(id='INT-SUPPORT', requirement='Explain support state.', paths=['other.py']))
            mapping['US-AGENT'] = ['INT-SUPPORT']
        graph = construct_default_graph('cohesive_delivery', outcomes,
            dict(session='native-coordinator', capability=dict(id='aim-native-orchestrator', version='4.8.0'),
                 permittedDecisions=['continue_bounded', 'request_owner_choice']),
            dict(delegationAllowed=True, maxWorkers=2, checkpointAttemptBudget=8,
                 noProgressLimit=2, parallelBenefit='Disjoint activities can finish independently.'))
        if not multiple_outcomes:
            left, review = graph['nodes']
            left.update(id='left', paths=['app.py'])
            right = copy.deepcopy(left)
            right.update(id='right', paths=['other.py'])
            review['dependsOn'] = ['left', 'right']
            graph['nodes'] = [left, right, review]
            graph['origin'] = dict(kind='custom', reference='two-disjoint-writers-one-original-outcome')
            if dependency:
                (self.repo / 'contract.py').write_text('shared original input\n')
                graph['outcomes'][0]['paths'].append('contract.py')
                first = copy.deepcopy(left)
                first.update(id='contract', paths=['contract.py'])
                left['dependsOn'] = right['dependsOn'] = ['contract']
                graph['nodes'].insert(0, first)
        c.mutate('plan', dict(id='DI-1', title='Original outcome observations', goal='Record actual integrated proof',
            storyIds=list(mapping), planEvidence=[c.plan_evidence], executionPlan=prepare_plan(graph, mapping)))
        c.mutate('approve', dict(deliveryId='DI-1', authority=c.authority(c.document['deliveries'][0]['scopeSha256'])))
        c.activate()

    def start(self, activity):
        self.case.start(activity=activity, session='worker-' + activity, key='work-' + activity)

    def finish(self, activity, paths):
        c = self.case
        receipt = next(r for r in reversed(c.document['deliveries'][0]['activityReceipts']) if r['activityId'] == activity)
        proof = c.artifact('complete-' + activity + '-' + str(c.document['revision']) + '.txt', 'Synthetic completed source witness.')
        c.mutate('activity', dict(deliveryId='DI-1', activityId=activity, status='completed', session=receipt['session'],
            attempt=receipt['attempt'], sourcePaths=paths, evidence=[proof]))

    def request(self, kind, number, activity, paths, outcome='INT-ACCESS', **extra):
        c = self.case
        observation = dict(outcomeId=outcome, kind=kind, attempt=number,
                           session='worker-' + activity if activity else 'native-coordinator', **extra)
        if activity:
            observation['activityId'] = activity
        sources = [dict(path=p, sha256=hashlib.sha256((self.repo / p).read_bytes()).hexdigest()) for p in paths]
        report = dict(orchestrationObservationVersion=1, deliveryId='DI-1', scopeSha256=c.document['deliveries'][0]['scopeSha256'],
                      sourceBindingsSha256=digest(sources), observation=observation)
        proof = c.artifact('report-' + str(c.document['revision']) + '.json', json.dumps(report))
        return dict(deliveryId='DI-1', action='observe', coordinatorSession='native-coordinator', outcomeId=outcome,
                    observation=observation, evidence=[proof], sourcePaths=paths)

    def observe(self, kind, number, activity, paths, outcome='INT-ACCESS', **extra):
        return self.case.mutate('orchestrate', self.request(kind, number, activity, paths, outcome, **extra))

    def baseline(self, *, paths=None, outcome='INT-ACCESS'):
        self.observe('baseline', 0, None, paths or ['app.py', 'other.py'], outcome,
                     baselineId='base-' + outcome, comparisonKey='original-journey', metric='passing-cases',
                     direction='higher', value=0, usable=True)

    def progress(self, number, activity, paths, value, outcome='INT-ACCESS'):
        self.observe('integrated_progress', number, activity, paths, outcome, baselineId='base-' + outcome,
                     comparisonKey='original-journey', metric='passing-cases', direction='higher', value=value)

    def state(self, outcome='INT-ACCESS'):
        return assessment(campaign_for(self.case.document, outcome))

    def rejects(self, request, pattern):
        before = (self.repo / '.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError, pattern):
            self.case.mutate('orchestrate', request)
        self.assertEqual((self.repo / '.aim/product-backlog.json').read_bytes(), before)

    def test_cohesive_receipt_allows_exact_outcome_sources_progress_and_checkpoint(self):
        self.plan(multiple_outcomes=True)
        self.baseline(paths=['app.py', 'helper.py'])
        self.baseline(paths=['other.py'], outcome='INT-SUPPORT')
        self.start('implement')
        self.finish('implement', ['app.py', 'helper.py', 'other.py'])
        self.rejects(self.request('component_pass', 1, 'implement', ['app.py']), 'sources differ')
        self.rejects(self.request('component_pass', 1, 'implement', ['app.py', 'helper.py', 'other.py']), 'ownership')
        # Reference order is incidental; raw proof still binds the exact supplied order.
        self.progress(1, 'implement', ['helper.py', 'app.py'], 1)
        self.progress(1, 'implement', ['other.py'], 1, outcome='INT-SUPPORT')
        self.assertEqual(self.state()['noProgressStreak'], 0)
        self.assertEqual(self.state('INT-SUPPORT')['noProgressStreak'], 0)
        self.observe('baseline', 1, 'implement', ['app.py', 'helper.py'], baselineId='usable-after-work',
                     comparisonKey='original-journey', metric='passing-cases', direction='higher', value=1, usable=True)
        record = campaign_for(self.case.document, 'INT-ACCESS')['observations'][-1]
        self.assertEqual({r['path'] for r in record['sourceCheckpoint']['files']}, {'app.py', 'helper.py'})

    def test_concurrent_earlier_worker_reports_progress_while_later_worker_runs(self):
        self.plan(); self.baseline(); self.start('left'); self.start('right')
        self.finish('left', ['app.py'])
        self.progress(1, 'left', ['app.py'], 1)
        self.assertEqual(self.state()['noProgressStreak'], 1)
        self.finish('right', ['other.py'])
        self.progress(2, 'right', ['other.py'], 2)
        self.assertEqual(self.state()['noProgressStreak'], 0)

    def test_reverse_completion_preserves_identity_arrival_journal_and_best_result(self):
        self.plan(); self.baseline(); self.start('left'); self.start('right')
        self.finish('right', ['other.py']); self.progress(2, 'right', ['other.py'], 2)
        before = copy.deepcopy(campaign_for(self.case.document, 'INT-ACCESS')['campaign']['observations'])
        self.finish('left', ['app.py']); self.progress(1, 'left', ['app.py'], 1)
        history = campaign_for(self.case.document, 'INT-ACCESS')['campaign']['observations']
        self.assertEqual(history[:-1], before)
        self.assertEqual(history[-1]['attempt'], 1)
        self.assertEqual(history[-1]['session'], 'worker-left')
        self.assertEqual(self.state()['bestValue']['value'], 2)
        self.assertEqual(self.state()['noProgressStreak'], 0)

    def test_late_higher_measurement_retains_newer_regression_and_newer_source_view(self):
        self.plan(); self.baseline(); self.start('left'); self.start('right')
        self.finish('right', ['other.py']); self.progress(2, 'right', ['other.py'], 5)
        self.finish('left', ['app.py']); self.progress(1, 'left', ['app.py'], 10)
        self.assertEqual(self.state()['bestValue']['value'], 10)
        self.assertEqual(self.state()['noProgressStreak'], 1)
        checked = []
        assessment(campaign_for(self.case.document, 'INT-ACCESS'), check_reference=lambda ref: checked.append(ref['path']))
        self.assertIn('other.py', checked); self.assertNotIn('app.py', checked)

    def test_shared_prerequisite_dag_checks_each_receipt_once_and_still_checks_every_edge(self):
        from aim_quality.orchestration_runtime import _check_receipt_dependencies
        receipts = []
        for number in range(32):
            receipts.append(dict(activityId='node-' + str(number), attempt=1, status='completed',
                sourceBindings=[dict(path='source-' + str(number), sha256='a' * 64)], evidence=[],
                dependencies=[dict(activityId=r['activityId'], attempt=1, receiptSha256=digest(r)) for r in receipts]))
        checks = []
        _check_receipt_dependencies(dict(activityReceipts=receipts), receipts[-1], lambda ref: checks.append(ref['path']))
        self.assertEqual(len(checks), 31)
        self.assertEqual(len(set(checks)), 31)
        receipts[-1]['dependencies'][-1]['receiptSha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'dependency'):
            _check_receipt_dependencies(dict(activityReceipts=receipts), receipts[-1], lambda ref: None)

    def test_late_success_cannot_clear_newer_crash_or_newer_no_progress(self):
        self.plan(); self.baseline(); self.start('left'); self.start('right')
        self.case.fail(activity='right')
        self.observe('crash', 2, 'right', ['other.py'])
        self.finish('left', ['app.py']); self.progress(1, 'left', ['app.py'], 1)
        self.assertEqual(self.state()['activeBlockingFailure']['attempt'], 2)
        self.assertEqual(self.state()['attemptsSinceImprovement'], 1)
        self.assertEqual(self.state()['recommendation']['action'], 'debug_blocking_failure')

    def test_late_falsifier_does_not_renew_information_gain_consumed_by_newer_start(self):
        self.plan(); self.start('left'); self.start('right'); self.finish('left', ['app.py'])
        self.observe('falsifier', 1, 'left', ['app.py'], informationGain=True)
        self.assertEqual(self.state()['recommendation']['action'], 'change_diagnostic_action')
        self.assertEqual(self.state()['noProgressStreak'], 2)

    def test_wrong_worker_activity_future_attempt_and_graph_revision_leave_ledger_unchanged(self):
        self.plan(); self.start('left'); self.start('right'); self.finish('left', ['app.py'])
        for changes, pattern in [({'session': 'worker-right'}, 'binding'), ({'activityId': 'right'}, 'binding'),
                                 ({'attempt': 3}, 'recorded'), ({'graphRevision': 'old-scope'}, 'revision')]:
            request = self.request('component_pass', 1, 'left', ['app.py'])
            request['observation'].update(changes)
            self.rejects(request, pattern)

    def test_superseded_same_activity_receipt_cannot_report_old_attempt(self):
        self.plan(); self.start('left'); self.case.fail(activity='left'); self.start('left')
        self.rejects(self.request('crash', 1, 'left', ['app.py']), 'superseded')

    def test_changed_sources_or_receipt_proof_cannot_be_rebound_to_new_report(self):
        self.plan(); self.start('left'); self.finish('left', ['app.py'])
        (self.repo / 'app.py').write_text('different source\n')
        self.rejects(self.request('component_pass', 1, 'left', ['app.py']), 'sources differ')
        original = 'def recover(): return True\n'
        (self.repo / 'app.py').write_text(original)
        receipt = self.case.document['deliveries'][0]['activityReceipts'][-1]
        (self.repo / receipt['evidence'][0]['path']).write_text('Changed completed proof')
        self.rejects(self.request('component_pass', 1, 'left', ['app.py']), 'changed|match|digest')

    def test_changed_prerequisite_source_rejects_dependent_positive_observation(self):
        self.plan(dependency=True); self.start('contract'); self.finish('contract', ['contract.py'])
        self.start('left'); self.finish('left', ['app.py'])
        (self.repo / 'contract.py').write_text('changed prerequisite')
        self.rejects(self.request('component_pass', 2, 'left', ['app.py']), 'changed|match|digest')

    def test_late_old_baseline_does_not_replace_newer_checkpoint_or_freshness_selection(self):
        self.plan(); self.start('left'); self.start('right')
        for number, activity, paths in [(2, 'right', ['other.py']), (1, 'left', ['app.py'])]:
            self.finish(activity, paths)
            self.observe('baseline', number, activity, paths, baselineId='baseline-' + str(number),
                         comparisonKey='original-journey', metric='passing-cases', direction='higher', value=number, usable=True)
        campaign = campaign_for(self.case.document, 'INT-ACCESS')
        self.assertEqual(self.state()['latestUsableBaseline']['baselineId'], 'baseline-2')
        calls = []
        assessment(campaign, check_reference=lambda ref: calls.append(ref['path']))
        self.assertIn('other.py', calls); self.assertNotIn('app.py', calls)
        self.assertEqual(summary(self.case.document)['campaigns'][0]['latestUsableSourceCheckpoint']['sourcePaths'], ['other.py'])
        exported = subprocess.run([sys.executable, str(ROOT / 'scripts/aim_orchestrate.py'), 'checkpoint',
            '--repo', str(self.repo), '--outcome', 'INT-ACCESS'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(exported.stdout)['sourceCheckpoint']['files'][0]['path'], 'other.py')


if __name__ == '__main__':
    unittest.main()
