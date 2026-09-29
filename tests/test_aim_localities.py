"""Exercise the public consumer against stale and shared repository knowledge."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from aim_installer.seed import shared_profile_seed, project_roles_seed
from aim_quality.localities import check_localities
from aim_quality.profiles import check_profiles

class LocalityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)
        (self.repo/'src/shared').mkdir(parents=True)
        (self.repo/'tests').mkdir()
        (self.repo/'tests/a.py').write_text('pass')
        self.profile('''      - id: api
        paths: ["src"]
        tests: ["tests/a.py"]
        dependsOn: ["shared"]
      - id: shared
        paths: ["src/shared"]
        dependsOn: ["api"]''')
    def profile(self, entries):
        import re
        entries=re.sub(r'(        \w+:) \[(.+?)\]', lambda m: m[1]+'\n'+''.join('          - '+v.strip()+'\n' for v in m[2].split(',')).rstrip(), entries)
        (self.repo/'aim.profile.yaml').write_text(shared_profile_seed().replace('    localities: []','    localities:\n'+entries))
    def test_standalone_calibration_checks_only_requested_profile(self):
        self.assertTrue(check_profiles(self.repo,'repo')['valid'])
        self.assertFalse(check_profiles(self.repo)['valid'])
        (self.repo/'aim.roles.yaml').write_text(project_roles_seed(self.repo))
        self.assertTrue(check_profiles(self.repo)['valid'])
        (self.repo/'aim.roles.yaml').write_text('{}')
        self.assertFalse(check_profiles(self.repo,'roles')['valid'])
    def test_overlap_and_cycle_are_bounded_and_not_false_conflicts(self):
        report=check_localities(self.repo,['api'])
        self.assertTrue(report['valid'],report)
        self.assertEqual([x['id'] for x in report['localities']],['api','shared'])
        self.assertEqual(len(report['overlaps']),1)
        self.assertFalse(report['semanticTruthVerified'])
    def test_moved_source_and_deleted_test_require_refresh_then_recover(self):
        (self.repo/'src/shared').rename(self.repo/'src/moved')
        (self.repo/'tests/a.py').unlink()
        report=check_localities(self.repo,['shared'])
        self.assertFalse(report['valid'])
        self.assertEqual(len(report['diagnostics']),2)
        p=self.repo/'aim.profile.yaml';p.write_text(p.read_text().replace('src/shared','src/moved').replace('tests:\n          - "tests/a.py"','tests: []'))
        self.assertTrue(check_localities(self.repo)['valid'])
    def test_unknown_dependencies_duplicates_and_labels_are_not_ready(self):
        self.profile('''      - id: api
        dependsOn: ["missing"]
      - id: api
        dependsOn: ["missing"]''')
        report=check_localities(self.repo)
        self.assertFalse(report['valid']);self.assertEqual(len(report['diagnostics']),3)
    def test_targeted_selection_does_not_force_unrelated_path_checks(self):
        self.profile('''      - id: live
        paths: ["src"]
      - id: stale
        paths: ["absent"]''')
        self.assertTrue(check_localities(self.repo,['live'])['valid'])
        self.assertFalse(check_localities(self.repo)['valid'])
        self.assertFalse(check_localities(self.repo,['unknown'])['valid'])
    def test_unsafe_paths_and_shapes_are_diagnostics(self):
        (self.repo/'alias').symlink_to(self.repo/'src',target_is_directory=True)
        for value in ['../outside','/tmp','alias/shared','src/**']:
            with self.subTest(value=value):
                self.profile('      - id: a\n        paths: ['+json.dumps(value)+']')
                self.assertFalse(check_localities(self.repo)['valid'])
        self.profile('      - id: a\n        paths: "src"')
        self.assertFalse(check_localities(self.repo)['valid'])
    def test_packaged_cli_no_site_packages_and_read_only(self):
        script=ROOT/'skills/agile-iteration-method/scripts/aim_engineering.py'
        before=(self.repo/'aim.profile.yaml').read_bytes()
        for args in [('profiles','--only','repo'),('localities','--locality','api')]:
            result=subprocess.run([sys.executable,'-S',str(script),'--repo',str(self.repo),*args],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)['valid'])
        self.assertEqual(before,(self.repo/'aim.profile.yaml').read_bytes())
