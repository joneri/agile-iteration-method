"""Exercise new consumers through the standalone shipped CLI, without site packages."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from aim_installer.seed import shared_profile_seed

class ExecutionPackageTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.base=Path(temp.name);self.repo=self.base/'product';self.repo.mkdir()
        self.package=self.base/'package';shutil.copytree(ROOT/'skills/agile-iteration-method',self.package)
        (self.repo/'src').mkdir();(self.repo/'src/app.py').write_text('value = 8\n')
    def run_cli(self,*args):
        p=subprocess.run([sys.executable,'-S',str(self.package/'scripts/aim_engineering.py'),'--repo',str(self.repo),*args],cwd=self.base,capture_output=True,text=True)
        self.assertNotIn('Traceback',p.stderr);return p.returncode,json.loads(p.stdout)
    def write(self,name,data):
        (self.repo/name).write_text(json.dumps(data));return name
    def test_review_tracks_complete_current_changed_set(self):
        source={'path':'src/app.py','sha256':hashlib.sha256((self.repo/'src/app.py').read_bytes()).hexdigest()}
        record={'version':1,'sources':[source],'implementers':[{'id':'dev','session':'s1'}],'reviewer':{'id':'review','session':'s2'},'reviewMode':'independent','findings':[]}
        self.write('review.json',record)
        code,result=self.run_cli('review','review.json','--changed','src/app.py')
        self.assertEqual(code,0);self.assertTrue(result['eligible']);self.assertFalse(result['provenance']['identityAuthenticated'])
        code,result=self.run_cli('review','review.json','--changed','src/app.py','--changed','src/uncovered.py')
        self.assertEqual(code,1);self.assertFalse(result['coverageComplete'])
        (self.repo/'src/app.py').write_text('value = 0\n')
        code,result=self.run_cli('review','review.json','--changed','src/app.py')
        self.assertEqual(code,1);self.assertFalse(result['fresh'])
    def test_delegation_uses_packaged_module_and_handles_malformed_input(self):
        plan={'version':1,'delegationAllowed':True,'maxWorkers':2,'parallelBenefit':'Separate source questions','activities':[{'id':'a','kind':'read','paths':['src/app.py'],'dependsOn':[]},{'id':'b','kind':'read','paths':['src/app.py'],'dependsOn':[]}]}
        self.write('plan.json',plan)
        code,result=self.run_cli('delegation','plan.json');self.assertEqual(code,0);self.assertEqual(result['waves'],[['a','b']])
        plan['activities'][0]['kind']=[];self.write('plan.json',plan)
        code,result=self.run_cli('delegation','plan.json');self.assertEqual(code,2);self.assertIn('error',result)
    def test_knowledge_and_product_profile_contract_packaged(self):
        profile=shared_profile_seed().replace('localities: []','''localities:
      - id: app
        paths:
          - src/app.py''').replace('validation: []','''validation:
      - id: invariant
        summary: App value
        appliesTo:
          - app
        expectedUse: Check value before change
        recheckWhen:
          - Behavior changes''')
        path=self.repo/'aim.profile.yaml';path.write_text(profile)
        code,result=self.run_cli('knowledge','--locality','app')
        self.assertEqual(code,0);self.assertEqual(result['rules'][0]['freshness'],'unverified')
        self.assertFalse(result['semanticTruthVerified'])
        path.write_text(profile.replace('profileLocation: aim.profile.yaml','profileLocation: .aim/profile.yaml'))
        code,result=self.run_cli('profiles','--only','repo')
        self.assertEqual(code,1);self.assertFalse(result['valid'])

if __name__=='__main__':unittest.main()
