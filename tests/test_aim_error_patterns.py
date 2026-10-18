"""Bounded concern advice stays local, data-only and package-relative."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_quality import patterns


class ErrorPatternTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((ROOT / "scripts/aim_quality/error_patterns.json").read_text())

    def supplied(self, document):
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "patterns.py"
            (module.parent / "error_patterns.json").write_text(json.dumps(document))
            with patch.object(patterns, "__file__", str(module)):
                return patterns.lookup(["async-results", "constraint-search", "method-evaluation"])

    def test_relevance_empty_result_and_query_bounds(self):
        self.assertEqual([p["id"] for p in patterns.lookup(["async-results"])["patterns"]],
                         ["PIT-RESULT-IDENTITY"])
        self.assertEqual(patterns.lookup(["unrelated-concern"])["patterns"], [])
        result = patterns.lookup(["result-handoff", "constraint-search", "method-evaluation"])
        self.assertEqual(len(result["patterns"]), 3)
        self.assertTrue(result["advisoryOnly"])
        self.assertFalse(result["benefitVerified"])
        for concerns in ([], ["a"] * 4, ["async-results"] * 2, "constraint-search", [None],
                         ["../project"], ["$(touch bad)"], ["line\nbreak"], ["a" * 65]):
            with self.subTest(concerns=concerns):
                with self.assertRaises(ValueError):
                    patterns.lookup(concerns)

    def test_withdrawn_patterns_are_never_returned(self):
        self.document["patterns"][0]["status"] = "withdrawn"
        result = self.supplied(self.document)
        self.assertEqual(len(result["patterns"]), 2)
        self.assertNotIn("PIT-RESULT-IDENTITY", [p["id"] for p in result["patterns"]])

    def test_malformed_metadata_and_unsafe_data_are_rejected(self):
        variants = [dict(version=True, patterns=[]), dict(version=1, patterns=self.document["patterns"] * 2)]
        for key, value in (("id", "../bad"), ("status", "approved"), ("checkedDate", "2026-02-30"),
                           ("concerns", ["../bad"]), ("evidence", "x" * 1001), ("control", "line\nbreak")):
            document = copy.deepcopy(self.document)
            document["patterns"][0][key] = value
            variants.append(document)
        duplicate = copy.deepcopy(self.document)
        duplicate["patterns"][1]["id"] = duplicate["patterns"][0]["id"]
        variants.append(duplicate)
        for document in variants:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    self.supplied(document)
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "patterns.py"
            data = module.parent / "error_patterns.json"
            with patch.object(patterns, "__file__", str(module)):
                for payload in (b"not JSON", b'{"version":1,"version":1,"patterns":[]}',
                                b" " * (patterns.MAX_BYTES + 1), b"[" * 1500 + b"]" * 1500):
                    data.write_bytes(payload)
                    with self.assertRaises(ValueError):
                        patterns.lookup(["async-results"])
                data.unlink()
                target = module.parent / "target.json"
                target.write_text(json.dumps(self.document))
                data.symlink_to(target)
                with self.assertRaises((OSError, ValueError)):
                    patterns.lookup(["async-results"])

    def test_local_lookup_never_executes_advice_or_touches_project(self):
        self.document["patterns"][0]["control"] = "$(touch forbidden-marker); arbitrary command text is data."
        with patch("os.system", side_effect=AssertionError("commands are forbidden")), \
             patch("subprocess.Popen", side_effect=AssertionError("commands are forbidden")):
            record = next(item for item in self.supplied(self.document)["patterns"]
                          if item["id"] == "PIT-RESULT-IDENTITY")
            self.assertIn("$(touch", record["control"])
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project-data.txt").write_text("Must remain unread and unchanged")
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in project.iterdir()}
            result = subprocess.run([sys.executable, str(ROOT / "scripts/aim_engineering.py"),
                                     "--repo", str(project / "nonexistent"), "pitfalls", "--concern", "async-results"],
                                    cwd=project, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["patterns"]), 1)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in project.iterdir()})

    def test_adjacent_data_works_in_relocated_package(self):
        for source in (ROOT, ROOT / 'skills/agile-iteration-method'):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "scripts/aim_quality"
                package.mkdir(parents=True)
                for name in ("__init__.py", "files.py", "patterns.py", "error_patterns.json"):
                    shutil.copyfile(source / "scripts/aim_quality" / name, package / name)
                program = "import json; from aim_quality.patterns import lookup; print(json.dumps(lookup(['method-evaluation'])))"
                result = subprocess.run([sys.executable, "-S", "-c", program], cwd=directory,
                                        env={**os.environ, "PYTHONPATH": str(package.parent), "PYTHONDONTWRITEBYTECODE": "1"},
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["patterns"][0]["id"], "PIT-METHOD-ACTIVATION")
                self.assertIn("repository-only", report["patterns"][0]["control"])
                self.assertFalse(report["benefitVerified"])
                self.assertEqual(set(p.name for p in package.iterdir()),
                                 {"__init__.py", "files.py", "patterns.py", "error_patterns.json"})
                if source != ROOT:
                    result = subprocess.run([sys.executable, '-S', str(source/'scripts/aim_engineering.py'),
                        '--repo', str(Path(directory)/'absent-project'), 'pitfalls', '--concern', 'constraint-search'],
                        cwd=directory, env={**os.environ, 'PYTHONPATH':'', 'PYTHONDONTWRITEBYTECODE':'1'},
                        capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)['patterns'][0]['id'], 'PIT-SEARCH-WORKLOAD')


if __name__ == "__main__":
    unittest.main()
