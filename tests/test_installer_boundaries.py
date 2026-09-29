"""Install isolation, collision preservation and recovery through real plans."""
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import json
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from aim_installer import apply, planner
from aim_installer.manifest import load_manifest

SOURCE = Path(__file__).resolve().parents[1]


class InstallerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / 'repo'; self.repo.mkdir()
        self.home = self.base / 'home'; self.home.mkdir()
        self.outside = self.base / 'outside'; self.outside.mkdir()
        self.manifest = load_manifest(SOURCE)

    def plan(self):
        return planner.compute_plan(source_root=SOURCE, target_root=self.repo,
            home_root=self.home, mode='standard', footprint='adapters',
            footprint_explicit=True, adapters=['codex'], manifest=self.manifest,
            validator_result={})

    def apply(self, plan):
        return apply.apply_plan(plan=plan, source_root=SOURCE, target_root=self.repo,
                                manifest=self.manifest, force=True)

    def test_preview_rejects_ancestor_and_leaf_links_in_both_scopes(self):
        for root, relative in [(self.repo, '.codex'), (self.repo, 'aim.roles.yaml'),
                               (self.home, '.agents')]:
            with self.subTest(relative=relative):
                link = root / relative
                link.symlink_to(self.outside, target_is_directory=True)
                with self.assertRaises(planner.PlanError): self.plan()
                self.assertEqual(list(self.outside.iterdir()), [])
                link.unlink()

    def test_missing_selected_home_can_be_created_without_fixed_backup_names(self):
        self.home.rmdir()
        self.apply(self.plan())
        self.assertTrue((self.home / '.agents/skills/agile-iteration-method/SKILL.md').is_file())
        self.assertEqual(list(self.home.rglob('.aim-install-*')), [])

    def test_adapter_install_contains_working_profile_checker(self):
        self.apply(self.plan())
        result = subprocess.run([sys.executable, '-S', str(self.repo / 'scripts/aim_engineering.py'),
                                 '--repo', str(self.repo), 'profiles'], cwd=self.home,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)['valid'])
        result = subprocess.run([sys.executable, '-S', str(self.repo / 'scripts/aim_engineering.py'),
                                 '--repo', str(self.repo), 'localities'], cwd=self.home,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(json.loads(result.stdout)['semanticTruthVerified'])

    def test_selected_root_replaced_by_link_is_refused(self):
        plan = self.plan()
        self.repo.rename(self.base / 'retained-root')
        self.repo.symlink_to(self.outside, target_is_directory=True)
        with self.assertRaises(apply.ApplyRefused): self.apply(plan)
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_apply_rechecks_path_changed_after_preview(self):
        plan = self.plan()
        (self.repo / '.codex').symlink_to(self.outside, target_is_directory=True)
        with self.assertRaises(apply.ApplyRefused): self.apply(plan)
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_user_backup_and_hardlinked_file_are_preserved(self):
        sentinel = self.repo / 'aim.roles.yaml.aim-backup'
        sentinel.write_bytes(b'USER BACKUP')
        outside_file = self.outside / 'roles'; outside_file.write_bytes(b'ORIGINAL')
        os.link(outside_file, self.repo / 'aim.roles.yaml')
        self.apply(self.plan())
        self.assertEqual(sentinel.read_bytes(), b'USER BACKUP')
        self.assertEqual(outside_file.read_bytes(), b'ORIGINAL')
        self.assertEqual(list(self.repo.rglob('.aim-install-*')), [])

    def test_mid_apply_failure_restores_files_without_touching_user_backup(self):
        (self.repo / 'aim.roles.yaml').write_bytes(b'OLD')
        (self.repo / 'aim.roles.yaml.aim-backup').write_bytes(b'BACKUP')
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        original = apply._write_file
        count = 0
        def fail_later(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 8: raise OSError('injected disk failure')
            return original(*args, **kwargs)
        with mock.patch.object(apply, '_write_file', side_effect=fail_later):
            with self.assertRaises(apply.ApplyFailed): self.apply(self.plan())
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(list(self.home.rglob('.aim-install-*')), [])

    def test_home_destination_outside_reviewed_home_is_refused(self):
        plan = self.plan()
        action = next(a for a in plan['actions'] if a['scope'] == 'home')
        action['destination'] = str(self.outside / 'payload')
        with self.assertRaises(apply.ApplyRefused): self.apply(plan)
        self.assertEqual(list(self.repo.iterdir()), [])
        self.assertEqual(list(self.outside.iterdir()), [])

    @unittest.skipUnless(os.open in os.supports_dir_fd, 'requires directory descriptors')
    def test_parent_replacement_cannot_redirect_a_pinned_write(self):
        parent = self.repo / 'nested'; parent.mkdir()
        original = apply._parent_handle
        journal = apply._Journal()
        def swapped(root, dest, journal):
            fd = original(root, dest, journal)
            parent.rename(self.repo / 'retained')
            parent.symlink_to(self.outside, target_is_directory=True)
            return fd
        with mock.patch.object(apply, '_parent_handle', side_effect=swapped):
            apply._write_file(parent / 'file', b'payload', journal, self.repo)
        journal.rollback()
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertEqual(list((self.repo / 'retained').iterdir()), [])

    def test_dangling_links_and_special_files_are_rejected(self):
        link = self.repo / 'aim.roles.yaml'; link.symlink_to(self.outside / 'missing')
        with self.assertRaises(planner.PlanError): self.plan()
        link.unlink()
        if hasattr(os, 'mkfifo'):
            os.mkfifo(link)
            with self.assertRaises(planner.PlanError): self.plan()
