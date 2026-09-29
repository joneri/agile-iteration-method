"""Profiles must be consumable by the shipped reader, not just look plausible."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from aim_installer.seed import shared_profile_seed, project_roles_seed
from aim_quality.profiles import check_profiles


class ProfileReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / 'aim.profile.yaml').write_text(shared_profile_seed())
        (self.repo / 'aim.roles.yaml').write_text(project_roles_seed(self.repo))

    def test_seed_is_consumable_without_claiming_truth_or_calibration(self):
        result = check_profiles(self.repo)
        self.assertTrue(result['valid'])
        self.assertFalse(result['semanticTruthVerified'])
        self.assertIn('needs_calibration', (self.repo / 'aim.roles.yaml').read_text())

    def test_json_disguised_as_yaml_is_reported_not_silently_ready(self):
        (self.repo / 'aim.roles.yaml').write_text(json.dumps({'aimProjectRoles': {'status':'ready'}}))
        result = check_profiles(self.repo)
        self.assertFalse(result['valid'])
        self.assertTrue(any(d['path']=='aim.roles.yaml' for d in result['diagnostics']))

    def test_schema_and_unsafe_skill_bindings_are_checked(self):
        path = self.repo / 'aim.roles.yaml'; original = path.read_text()
        path.write_text(original.replace('profileVersion: "0.1"', 'profileVersion: "9.9"'))
        self.assertFalse(check_profiles(self.repo)['valid'])
        path.write_text(original.replace('source: bundled', 'source: project\n          path: ../escape.md'))
        self.assertFalse(check_profiles(self.repo)['valid'])

    def test_missing_and_symlink_profiles_are_diagnostics(self):
        path = self.repo / 'aim.roles.yaml'; path.unlink()
        self.assertFalse(check_profiles(self.repo)['valid'])
        path.symlink_to(ROOT / 'aim.roles.yaml')
        self.assertFalse(check_profiles(self.repo)['valid'])

    def test_public_cli_works_without_source_checkout_or_site_packages(self):
        script = ROOT / 'skills/agile-iteration-method/scripts/aim_engineering.py'
        before = {p.name:p.read_bytes() for p in self.repo.iterdir()}
        result = subprocess.run([sys.executable,'-S',str(script),'--repo',str(self.repo),'profiles'],
                                cwd=self.repo,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertTrue(json.loads(result.stdout)['valid'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.repo.iterdir()})
        (self.repo/'aim.roles.yaml').write_text('{}')
        result = subprocess.run([sys.executable,'-S',str(script),'--repo',str(self.repo),'profiles'],
                                cwd=self.repo,capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stderr+result.stdout)
        self.assertFalse(json.loads(result.stdout)['valid'])
