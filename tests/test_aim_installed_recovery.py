"""Exercise startup/recovery from the real installed payload, away from source."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from aim_installer import apply, planner, seed
from aim_installer.manifest import load_manifest


class InstalledRecoveryTests(unittest.TestCase):
    def test_installed_start_and_catalog_recovery_preserve_checkpoint(self):
        for footprint in ('external', 'local', 'profile', 'adapters', 'full'):
            with self.subTest(footprint=footprint):
                self.exercise_installed_recovery(footprint)

    def exercise_installed_recovery(self, footprint):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo, home = base / 'product', base / 'home'
            repo.mkdir()
            home.mkdir()
            manifest = load_manifest(ROOT)
            plan = planner.compute_plan(
                source_root=ROOT, target_root=repo, mode='standard',
                footprint=footprint, footprint_explicit=True,
                adapters=['codex'], manifest=manifest,
                validator_result={'resultClass': 'healthy', 'exitCode': 0},
                home_root=home,
            )
            apply.apply_plan(plan=plan, source_root=ROOT, target_root=repo,
                             manifest=manifest, force=False)

            package = repo if footprint in ('adapters', 'full') else home / '.aim/installs/agile-iteration-method'

            def invoke(script, *arguments):
                result = subprocess.run(
                    [sys.executable, '-S', str(package / 'scripts' / script),
                     '--repo', str(repo), *arguments], cwd=base,
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                return json.loads(result.stdout)

            arguments = [
                '--epic-id', 'EPIC-INSTALL', '--increment-id', 'DI-001',
                '--title', 'Installed startup', '--mode', 'Auto',
                '--updated-at', '2026-09-29T10:00:00Z',
            ]
            preview = invoke('aim_start.py', *arguments)
            self.assertFalse((repo / '.aim/ui-portfolio.json').exists())
            invoke('aim_start.py', *arguments, '--apply',
                   '--expected-start-sha256', preview['startSha256'])
            state = repo / '.aim/portfolio/EPIC-INSTALL/state.json'
            original_state = state.read_bytes()
            catalog = repo / '.aim/ui-portfolio.json'
            original_catalog = json.loads(catalog.read_text())
            catalog.unlink()
            result = invoke('aim_recovery.py')
            self.assertEqual(result['result'], 'recovered')
            self.assertEqual(json.loads(catalog.read_text()), original_catalog)
            self.assertEqual(state.read_bytes(), original_state)
            self.assertEqual(invoke('aim_recovery.py')['result'], 'unchanged')
            (repo / 'aim.profile.yaml').write_text(seed.shared_profile_seed())
            (repo / 'aim.roles.yaml').write_text(seed.project_roles_seed(repo))
            self.assertTrue(invoke('aim_engineering.py', 'profiles')['valid'])



if __name__ == '__main__':
    unittest.main()
