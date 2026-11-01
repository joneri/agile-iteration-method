"""Read-only preflight and actual start must agree, with no reserved authority."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import test_aim_orchestration_runtime as native
from aim_stories import dispatch_check, execute

class DispatchPreflightTests(unittest.TestCase):
    setUp=native.NativeRuntimeTests.setUp
    artifact=native.NativeRuntimeTests.artifact
    mutate=native.NativeRuntimeTests.mutate
    authority=native.NativeRuntimeTests.authority
    native_plan=native.NativeRuntimeTests.native_plan
    activate=native.NativeRuntimeTests.activate
    start=native.NativeRuntimeTests.start
    fail=native.NativeRuntimeTests.fail

    def start_request(self,**changes):
        return dict(deliveryId='DI-1',activityId='implement',status='running',session='worker-a',
                    coordinatorSession='native-coordinator',actionKey='restore-journey',**changes)
    def check(self,request=None): return dispatch_check(self.repo,request or self.start_request(),self.token)
    def test_actual_start_matches_read_only_check_then_old_check_is_stale(self):
        self.native_plan(); before=(self.repo/'.aim/product-backlog.json').read_bytes()
        r=self.check(); self.assertTrue(r['eligible']);self.assertFalse(r['committed'])
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())
        old=self.token; result=execute(self.repo,'activity',self.start_request(),old)
        actual=result['document']['deliveries'][0]['activityReceipts'][-1]
        self.assertEqual({k:v for k,v in r['prospectiveAttempt'].items() if k not in {'at','updatedAt'}},
                         {k:v for k,v in actual.items() if k not in {'at','updatedAt'}})
        with self.assertRaisesRegex(ValueError,'Stale'):dispatch_check(self.repo,self.start_request(),old)
    def test_missing_delivery_and_activation_reject_without_write(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):self.check()
        self.native_plan(activate=False);before=(self.repo/'.aim/product-backlog.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'Activate'):self.check()
        self.assertEqual(before,(self.repo/'.aim/product-backlog.json').read_bytes())
    def test_wrong_coordinator_and_missing_approval_reject(self):
        self.native_plan();req=self.start_request();req['coordinatorSession']='wrong'
        with self.assertRaisesRegex(ValueError,'coordinator|Activate|activated'):self.check(req)
    def test_resource_boundary_and_duplicate_attempt_reject(self):
        self.native_plan(budget=1);self.start()
        with self.assertRaises(ValueError):self.check()
        self.fail()
        with self.assertRaisesRegex(ValueError,'request_owner_choice'):self.check()
    def test_dependency_rejects_premature_review(self):
        self.native_plan();req=self.start_request();req['activityId']='integrate-review'
        with self.assertRaisesRegex(ValueError,'prerequisites'):self.check(req)

if __name__=='__main__':unittest.main()
