"""Real installed entry discovers another repo's lesson without known tags."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LearningCliTests(unittest.TestCase):
    def test_real_entry_cross_repo_discovery_and_failed_share(self):
        for package in (ROOT, ROOT / "skills/agile-iteration-method"):
            with self.subTest(package=package), tempfile.TemporaryDirectory() as directory:
                base = Path(directory).resolve()
                repo_a, repo_b = base / "repo-a", base / "repo-b"
                repo_a.mkdir()
                repo_b.mkdir()
                registry = base / "shared/registry.sqlite3"
                proof = b"A was retained after editing current input to B; assertion passed.\n"
                (repo_a / "proof.txt").write_bytes(proof)
                digest = hashlib.sha256(proof).hexdigest()
                lesson = {"title": "Retained results keep input identity",
                          "context": "A worker returns a result before a user edits input",
                          "problem": "Old output is reopened with the new input",
                          "action": "Store immutable input identity with each result",
                          "check": "Compute A, edit B, reopen A and inspect input identity",
                          "terms": ["gammalt resultat", "ändrade indata"],
                          "topics": ["result-lifecycle"], "phases": ["planning", "review"]}

                def invoke(repo, action, *arguments, payload=None, expected=0):
                    result = subprocess.run(
                        [sys.executable, "-S", str(package / "scripts/aim_engineering.py"),
                         "--repo", str(repo), "learning", action, "--registry", str(registry), *arguments],
                        cwd=repo_b, input=payload, capture_output=True, text=True, timeout=10,
                        env={**os.environ, "PYTHONPATH": "", "PYTHONDONTWRITEBYTECODE": "1"})
                    self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
                    return json.loads(result.stdout)

                self.assertFalse(invoke(repo_b, "recall", "--text", "old results")["available"])
                self.assertFalse(registry.parent.exists())
                posted = invoke(repo_a, "share", "--evidence", "proof.txt", "--evidence-sha256", digest,
                                payload=json.dumps(lesson))
                self.assertTrue(posted["changed"])
                recalled = invoke(repo_b, "recall", "--text", "gammalt resultat efter ändrade indata")
                self.assertEqual(recalled["lessons"][0]["id"], posted["record"]["id"])
                self.assertEqual(recalled["lessons"][0]["matchKind"], "text")
                self.assertNotIn(str(repo_a), json.dumps(recalled))
                self.assertEqual(list(repo_b.iterdir()), [])
                retry = invoke(repo_a, "share", "--evidence", "proof.txt", "--evidence-sha256", digest,
                               payload=json.dumps(lesson))
                self.assertFalse(retry["changed"])
                failed = invoke(repo_a, "share", "--evidence", "proof.txt", "--evidence-sha256", "0" * 64,
                                payload=json.dumps(lesson), expected=2)
                self.assertIn("error", failed)
                self.assertEqual(invoke(repo_b, "history", "--lesson-id", posted["record"]["id"])
                                 ["revisions"][0]["revision"], 1)
                self.assertEqual((repo_a / "proof.txt").read_bytes(), proof)


if __name__ == "__main__":
    unittest.main()
