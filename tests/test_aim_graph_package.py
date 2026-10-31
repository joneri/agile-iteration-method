"""Run native Graph from real isolated public and adaptive installations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_aim_graph import seed_graph


class GraphPackageTests(unittest.TestCase):
    def test_real_distributions_run_graph_without_source_checkout_imports(self):
        with tempfile.TemporaryDirectory(prefix="aim-graph-install-") as folder:
            base = Path(folder)
            for footprint in ("public", "external", "adapters"):
                with self.subTest(footprint=footprint):
                    repo = base / footprint / "product"
                    repo.mkdir(parents=True)
                    seed_graph(repo)
                    if footprint == "public":
                        package = ROOT / "skills/agile-iteration-method"
                    else:
                        isolated_home = base / footprint / "home"
                        installed = subprocess.run([sys.executable, str(ROOT / "scripts/aim_install.py"),
                            "--target", str(repo), "--home", str(isolated_home), "--source", str(ROOT),
                            "--adapter", "codex", "--footprint", footprint, "--non-interactive", "--apply", "--format", "json"],
                            capture_output=True, text=True, cwd=base)
                        self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout[-2000:])
                        package = repo if footprint == "adapters" else isolated_home / ".aim/installs/agile-iteration-method"
                    self.assertTrue((package / "aim-ui/graph-views.js").is_file())
                    before = (repo / ".aim/product-backlog.json").read_bytes()
                    process = subprocess.run([sys.executable, "-S", str(package / "scripts/aim_stories.py"),
                        "--repo", str(repo), "graph"], cwd=base, capture_output=True, text=True)
                    self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
                    graph = json.loads(process.stdout)
                    self.assertEqual(graph["recommendedIds"], ["contract"])
                    self.assertEqual(graph["scopeSha256"], graph["activities"][0]["assignment"]["scopeSha256"])
                    self.assertEqual((repo / ".aim/product-backlog.json").read_bytes(), before)

                    # Run the shipped helper outside the source checkout with
                    # site packages disabled: its complete dependency closure
                    # and user-graph preservation must survive installation.
                    helper = package / "scripts/aim_orchestrate.py"
                    def run_helper(operation, payload=None):
                        command = [sys.executable, "-S", str(helper), operation]
                        if operation == "status":
                            command += ["--repo", str(repo)]
                        result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                                                cwd=base, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                        return json.loads(result.stdout)
                    native = run_helper("default", {
                        "pattern": "cohesive_delivery",
                        "outcomes": [{"id": "INT-VERIFY", "requirement": "Preserve the original journey.",
                                      "paths": ["contract.py"]}],
                        "coordinator": {"session": "actual-coordinator",
                                        "capability": {"id": "aim-native-orchestration", "version": "4.8.0"},
                                        "permittedDecisions": ["continue_bounded", "request_owner_choice"]},
                        "policy": {"delegationAllowed": True, "maxWorkers": 1, "checkpointAttemptBudget": 3}})
                    native["origin"] = {"kind": "custom", "reference": "owner-graph-r2"}
                    validated = run_helper("validate", native)
                    self.assertEqual(validated, native)
                    execution = run_helper("plan", {"graph": validated,
                                                    "storyOutcomes": {"US-VERIFY-ONE": ["INT-VERIFY"]}})
                    self.assertEqual(execution["orchestration"], native)
                    self.assertEqual(execution["activities"][-1]["dependsOn"], ["implement"])
                    native_status = run_helper("status")
                    self.assertEqual(native_status["campaigns"], [])
                    self.assertFalse(native_status["authorityGranted"])
                    self.assertEqual((repo / ".aim/product-backlog.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
