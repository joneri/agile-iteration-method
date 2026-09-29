import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from aim_quality.delegation import check_delegation

class DelegationTests(unittest.TestCase):
    def plan(self):
        return {'version': 1, 'maxWorkers': 2, 'delegationAllowed': True,
                'parallelBenefit': 'Independent API and UI implementation after shared contract',
                'activities': [
                    {'id': 'api', 'kind': 'write', 'paths': ['src/api'], 'dependsOn': []},
                    {'id': 'ui', 'kind': 'write', 'paths': ['src/ui'], 'dependsOn': []},
                    {'id': 'review', 'kind': 'review', 'paths': ['src'], 'dependsOn': ['api', 'ui']}]}
    def test_independent_work_parallel_review_after_integration(self):
        plan = self.plan();before = copy.deepcopy(plan)
        result = check_delegation(plan)
        self.assertEqual(result['waves'], [['api', 'ui'], ['review']])
        self.assertTrue(result['valid']);self.assertFalse(result['reviewIdentityVerified'])
        self.assertEqual(plan, before)
    def test_overlapping_writers_and_reader_are_serialized(self):
        plan = self.plan();plan['activities'][1]['paths'] = ['src/api/client.py']
        self.assertEqual(check_delegation(plan)['waves'], [['api'], ['ui'], ['review']])
        plan['activities'][1]['kind'] = 'read'
        self.assertEqual(check_delegation(plan)['waves'], [['api'], ['ui'], ['review']])
    def test_review_without_dependency_cannot_pass(self):
        plan = self.plan();plan['activities'][2]['dependsOn'] = ['api']
        self.assertFalse(check_delegation(plan)['valid'])
    def test_host_denial_gives_explicit_sequential_fallback(self):
        plan = self.plan();plan['delegationAllowed'] = False
        result = check_delegation(plan)
        self.assertEqual(result['effectiveWorkers'], 1)
        self.assertTrue(result['fallback'])
        self.assertEqual(result['waves'], [['api'], ['ui'], ['review']])
    def test_transitive_dependency_and_prefix_boundaries(self):
        plan = self.plan();plan['activities'][1]['dependsOn'] = ['api'];plan['activities'][2]['dependsOn'] = ['ui']
        self.assertTrue(check_delegation(plan)['valid'])
        plan = self.plan();plan['activities'][1]['paths'] = ['src/api2']
        self.assertEqual(check_delegation(plan)['waves'][0], ['api', 'ui'])
    def test_invalid_graph_scope_and_limits(self):
        for change in [lambda p:p.update(maxWorkers=True),lambda p:p.update(maxWorkers=9),
                       lambda p:p.update(parallelBenefit=''),
                       lambda p:p['activities'][0].update(kind=[]),
                       lambda p:p['activities'][0].update(dependsOn=['review']),
                       lambda p:p['activities'][0].update(dependsOn=['missing'])]:
            p=self.plan();change(p)
            with self.assertRaises(ValueError):check_delegation(p)
        for path in ['../secret','/tmp/x','src/*','src/../x','src//x','src\\x','.aim','.aim/state.json','.aim/portfolio/EPIC-001/state.json','.aim/portfolio/control.json']:
            p=self.plan();p['activities'][0]['paths']=[path]
            with self.subTest(path=path),self.assertRaises(ValueError):check_delegation(p)
    def test_state_free_readonly_analysis_permitted(self):
        p=self.plan();p['activities'][0]['paths']=['.aim/analysis']
        self.assertTrue(check_delegation(p)['valid'])

if __name__ == '__main__':unittest.main()
