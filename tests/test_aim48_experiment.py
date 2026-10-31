"""Isolation and provenance checks for unpublished paired method experiments."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_aim48_experiment as build


class ExperimentPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = self.root / "spec"
        self.game = self.root / "game"
        self.upstream = self.root / "upstream"
        self.out = self.root / "pair"
        self.write(self.root, "VERSION", "4.7.7\n")
        self.write(self.spec, "protocol.json", json.dumps({"baseAimVersion": "4.7.7", "candidateVersions": {"native": "4.8.0-native.1", "sp": "4.8.0-sp.1"}, "brief": {"requirement": "Three usable levels"}}))
        for item in ("native/SKILL.md", "sp/SKILL.md", "common-governance.md", "native-contract.json", "package-manifest-experiment.py"):
            self.write(self.spec, item, "fixture")
        for item in ("scripts/aim_orchestrate.py", "scripts/aim_quality/orchestration.py"):
            self.write(self.root, item, "# fixture\n")
        package = self.root / "skills/agile-iteration-method"
        self.write(package, "manifest.json", '{"productVersion":"4.7.7"}')
        self.write(package, "SKILL.md", "shared AIM entry")
        self.write(package, "references/shared.md", "same quality obligations")
        (package / "scripts/aim_quality").mkdir(parents=True)
        for item in build.PRODUCT_FILES:
            self.write(self.game, item, "{}")
        self.write(self.game, "native-probe/core.swift", "let original = 1\n")
        self.write(self.game, "native-probe/build.sh", "python3 native-probe/Verification/package-manifest.py\n")
        self.write(self.game, "native-probe/build/cache", "not a source")
        self.write(self.game, "aim/assets/b2/sprite.png", "fixture asset")
        for item in ("LICENSE", "skills/writing-plans/SKILL.md", "skills/subagent-driven-development/SKILL.md", "skills/executing-plans/SKILL.md"):
            self.write(self.upstream, item, "upstream fixture")
        self.write(self.upstream, ".gitignore", "ignored-secret.env\n")
        self.git(self.upstream, "init", "-q")
        self.git(self.upstream, "config", "user.name", "Fixture")
        self.git(self.upstream, "config", "user.email", "fixture@localhost")
        self.git(self.upstream, "add", ".")
        self.git(self.upstream, "commit", "-qm", "fixture")
        self.write(self.upstream, "ignored-secret.env", "must never enter an experiment")
        self.addCleanup(patch.stopall)
        patch.object(build, "ROOT", self.root).start()
        patch.object(build, "SPEC", self.spec).start()

    def write(self, root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def git(self, root, *args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)

    def test_identical_product_and_shared_method_without_mutating_original(self):
        original = build.inventory(self.game)
        result = build.prepare(self.game, self.upstream, self.out)
        self.assertEqual(result["status"], "prepared_not_started")
        self.assertEqual(build.inventory(self.out / "native"), build.inventory(self.out / "sp"))
        for relative, expected in original.items():
            self.assertEqual(build.digest(self.out / "native" / relative), expected)
        self.assertEqual(build.inventory(self.game), original)
        for arm in ("native", "sp"):
            self.assertEqual((self.out / arm / "method/references/shared.md").read_text(), "same quality obligations")
            tracked = self.git(self.out / arm, "ls-files").decode()
            self.assertIn(build.PRODUCT_FILES[0], tracked)
            self.assertNotIn("build/cache", tracked)
        self.assertFalse((self.out / "sp/method/scripts/aim_orchestrate.py").exists())

    def test_only_committed_upstream_bytes_are_packaged(self):
        build.prepare(self.game, self.upstream, self.out)
        vendor = self.out / "sp/method/vendor/superpowers"
        self.assertTrue((vendor / "LICENSE").is_file())
        self.assertFalse((vendor / "ignored-secret.env").exists())
        self.assertFalse((vendor / ".git").exists())

    def test_existing_output_and_stale_package_are_rejected_before_writes(self):
        self.out.mkdir()
        self.write(self.out, "keep", "prior evidence")
        with self.assertRaisesRegex(ValueError, "never overwrite"):
            build.prepare(self.game, self.upstream, self.out)
        self.assertEqual((self.out / "keep").read_text(), "prior evidence")
        other = self.root / "other"
        self.write(self.root, "VERSION", "4.8.0\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            build.prepare(self.game, self.upstream, other)
        self.assertFalse(other.exists())

    def test_symlinked_fixture_ancestor_is_rejected(self):
        analysis = self.game / ".aim/analysis"
        moved = self.root / "external-analysis"
        analysis.rename(moved)
        analysis.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            build.inventory(self.game)

    def test_shared_package_drift_is_not_silently_accepted(self):
        original_copy = build.copy_tree
        calls = []
        def drift(source, destination):
            original_copy(source, destination)
            calls.append(destination)
            if len(calls) == 1:
                (source / "references/shared.md").write_text("changed between arms")
        with patch.object(build, "copy_tree", side_effect=drift):
            with self.assertRaisesRegex(ValueError, "Shared AIM source differs|Method source changed"):
                build.prepare(self.game, self.upstream, self.out)


if __name__ == "__main__":
    unittest.main()
