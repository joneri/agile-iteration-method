"""Exercise the shipped Story helper without importing checkout modules."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/agile-iteration-method"


class ShippedStoryJourneyTests(unittest.TestCase):
    def test_packaged_cli_import_selection_and_real_board_share_story_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            def invoke(command, request=None, token=None):
                args = [sys.executable, str(PACKAGE / "scripts/aim_stories.py"),
                        "--repo", str(repo), command]
                if token:
                    args.extend(["--expected-sha256", token])
                env = dict(os.environ)
                env.pop("PYTHONPATH", None)
                result = subprocess.run(args, input=json.dumps(request or {}),
                                        text=True, capture_output=True, cwd=repo,
                                        env=env, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            criterion = [{"id": "AC-1", "text": "The persona completes the stated task."}]
            request = {
                "intents": [{"id": "INT-SERVICE", "statement": "Recover interrupted purchases."}],
                "epics": [
                    {"id": "EPIC-BUY", "intentId": "INT-SERVICE", "title": "Recovery",
                     "outcome": "Buyers recover", "acceptanceCriteria": criterion},
                    {"id": "EPIC-SUPPORT", "intentId": "INT-SERVICE", "title": "Support",
                     "outcome": "Agents help", "acceptanceCriteria": criterion}],
                "stories": [
                    {"id": identity, "epicId": epic, "title": title, "persona": persona,
                     "need": title, "benefit": "Complete the purchase safely",
                     "acceptanceCriteria": criterion, "priority": priority, "status": "ready"}
                    for identity, epic, title, persona, priority in (
                        ("US-RETRY", "EPIC-BUY", "Retry payment", "Buyer", 1),
                        ("US-FIND", "EPIC-SUPPORT", "Find failed order", "Support agent", 2),
                        ("US-REPORT", "EPIC-SUPPORT", "Report failures", "Operator", 3))]}
            imported = invoke("import", request)
            plan = repo / ".aim/plan.md"
            plan.write_text("Implement buyer retry and support lookup in service.py; verify both paths.")
            planned = invoke("plan", {
                "id": "DI-001", "title": "Recover a purchase", "goal": "Buyer and agent recover together",
                "storyIds": ["US-FIND", "US-RETRY"],
                "planEvidence": [{"path": ".aim/plan.md", "sha256": hashlib.sha256(plan.read_bytes()).hexdigest()}]},
                imported["storeSha256"])
            self.assertEqual([s["id"] for s in planned["document"]["deliveries"][0]["stories"]],
                             ["US-FIND", "US-RETRY"])
            self.assertEqual(planned["nextStep"][0]["operation"], "approve")
            snapshot = (repo / ".aim/product-backlog.json").read_bytes()
            code = "import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from aim_ui import build_board; print(json.dumps(build_board(Path(sys.argv[2]))))"
            result = subprocess.run([sys.executable, "-c", code, str(PACKAGE / "scripts"), str(repo)],
                                    text=True, capture_output=True, cwd=repo, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            board = json.loads(result.stdout)["storyBoard"]
            self.assertTrue(board["valid"])
            self.assertEqual([s["id"] for s in board["stories"]], ["US-RETRY", "US-FIND", "US-REPORT"])
            self.assertEqual(board["stories"][2]["deliveryIds"], [])
            self.assertEqual(len(board["epics"]), 2)
            self.assertEqual((repo / ".aim/product-backlog.json").read_bytes(), snapshot)
            self.assertFalse((repo / ".aim/state.json").exists())
            self.assertFalse((repo / ".aim/portfolio-backlog.json").exists())
            self.assertTrue((PACKAGE / "references/schemas/aim-product-backlog.schema.json").is_file())
            self.assertTrue((PACKAGE / "references/user-stories.md").is_file())


if __name__ == "__main__":
    unittest.main()
