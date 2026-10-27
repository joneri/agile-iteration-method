"""Literal dependency/ownership witnesses for the native delivery activity entry."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import test_aim_stories as fixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_stories import StoryError, compact_result, execute, load, project_story_board, _source_bindings
from aim_quality.graph import project_graph


def activity(identifier, paths, deps=(), kind="write"):
    return dict(id=identifier, title="Task " + identifier, kind=kind,
                role="reviewer" if kind == "review" else "dev",
                skills=["aim-reviewer-engineering" if kind == "review" else "aim-dev-engineering"],
                storyIds=["US-BUYER"], paths=paths, dependsOn=list(deps))


def diamond():
    return dict(version=1, delegationAllowed=True, maxWorkers=2,
                parallelBenefit="UI and storage are disjoint after the shared contract.",
                activities=[activity("A", ["contract.py"]),
                            activity("B", ["ui.py"], ["A"]),
                            activity("C", ["storage.py"], ["A"]),
                            activity("D", ["contract.py", "ui.py", "storage.py"], ["B", "C"], "review")])


class GraphTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    authority = fixture.StoryDeliveryTests.authority
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def plan_graph(self, plan=None, approve=True):
        for name in ("contract.py", "ui.py", "storage.py"):
            (self.repo / name).write_text(name + " v1\n")
        self.mutate("plan", dict(id="DI-1", title="A dependency graph", goal="Prove bounded useful work",
                                storyIds=["US-BUYER"], planEvidence=[self.plan_evidence], executionPlan=plan or diamond()))
        if approve:
            self.mutate("approve", dict(deliveryId="DI-1", authority=self.authority(self.document["deliveries"][0]["scopeSha256"])))

    def graph(self):
        return project_story_board(self.repo)["executionGraph"]

    def start(self, identifier, session=None):
        result = self.mutate("activity", dict(deliveryId="DI-1", activityId=identifier,
                                             status="running", session=session or "session-" + identifier))
        return next(a for a in result["executionGraph"]["activities"] if a["id"] == identifier)["attempt"]

    def finish(self, identifier, source, attempt=1, session=None):
        proof = self.artifact(f"activity-{identifier}-{attempt}.txt", f"Observed result for {identifier} attempt {attempt}\n")
        return self.mutate("activity", dict(deliveryId="DI-1", activityId=identifier,
                    status="completed", session=session or "session-" + identifier, attempt=attempt,
                    sourcePaths=source if isinstance(source, list) else [source], evidence=[proof]))

    def test_diamond_literal_oracle_and_failure(self):
        self.plan_graph()
        self.assertEqual(self.graph()["readyIds"], ["A"])
        self.assertEqual(self.graph()["recommendedIds"], ["A"])
        self.start("A")
        result = self.finish("A", "contract.py")
        self.assertEqual(result["executionGraph"]["readyIds"], ["B", "C"])
        self.assertEqual(result["executionGraph"]["recommendedIds"], ["B", "C"])
        self.assertEqual(compact_result(result, receipt=True)["executionGraph"]["readyIds"], ["B", "C"])
        self.start("B")
        self.mutate("activity", dict(deliveryId="DI-1", activityId="B", status="failed",
                                    session="session-B", attempt=1, reason="UI counterexample failed."))
        self.assertEqual(next(a["status"] for a in self.graph()["activities"] if a["id"] == "D"), "blocked")
        self.assertEqual(self.graph()["readyIds"], ["C"])
        self.assertEqual(self.graph()["retryIds"], ["B"])
        self.assertEqual(self.graph()["recommendedIds"], ["B", "C"])
        self.assertEqual(self.document["deliveries"][0]["status"], "in_progress")

    def test_repeated_diagnosis_reassesses_before_retry_without_blocking_independent_work(self):
        self.plan_graph()
        self.start('A'); self.finish('A', 'contract.py')
        self.start('B')
        self.mutate('activity', dict(deliveryId='DI-1', activityId='B', status='failed',
                    session='session-B', attempt=1, reason='First real diagnostic failure.'))
        # A bounded first correction can continue without a new question/form.
        self.assertEqual(self.start('B', 'second-session'), 2)
        self.mutate('activity', dict(deliveryId='DI-1', activityId='B', status='failed',
                    session='second-session', attempt=2, reason='Second failure; investigation expanded.'))
        graph = self.graph()
        self.assertEqual(graph['recommendedIds'], ['C'])
        task = next(a for a in graph['activities'] if a['id'] == 'B')
        self.assertTrue(task['reassessmentRequired'])
        self.assertEqual(task['diagnosticFailures'], 2)
        self.unchanged_failure('activity', dict(deliveryId='DI-1', activityId='B',
                              status='running', session='third-session'), 'reassessment')
        decision = dict(contextSha256=task['retryContextSha256'], decision='continue_bounded',
                        userOutcome='Restore the approved buyer recovery journey; stress remains a technical constraint, not the user outcome.',
                        resources='Two failed attempts across two sessions; elapsed cost unavailable, not zero. Original resource mandate remains binding.',
                        alternatives='Complete independent storage work now; then one isolated UI correction, or block for an actual owner scope choice.',
                        boundary='One next attempt within the existing mandate and frozen quality; stop on failure and reassess before expanding.')
        self.start('C'); self.finish('C', 'storage.py')
        request = dict(deliveryId='DI-1', activityId='B', status='running', session='third-session', reassessment=decision)
        owner_choice = copy.deepcopy(request); owner_choice['reassessment']['decision'] = 'owner_decision'
        self.unchanged_failure('activity', owner_choice, 'owner decision|independent work')
        self.mutate('activity', request)
        self.assertEqual(self.document['deliveries'][0]['activityReceipts'][-1]['reassessment'], decision)
        self.mutate('activity', dict(deliveryId='DI-1', activityId='B', status='failed',
                    session='third-session', attempt=3, reason='Third failure retained unchanged.'))
        self.unchanged_failure('activity', request, 'context')
        self.assertEqual(len([r for r in self.document['deliveries'][0]['activityReceipts']
                              if r['activityId']=='B' and r['status']=='failed']), 3)
        self.assertEqual(self.document['deliveries'][0]['status'], 'in_progress')

    def test_prerequisite_rework_invalidates_retry_assessment_without_rewriting_history(self):
        self.plan_graph(); self.start('A'); self.finish('A', 'contract.py')
        for attempt in (1, 2):
            self.start('B')
            self.mutate('activity', dict(deliveryId='DI-1', activityId='B', status='failed',
                        session='session-B', attempt=attempt, reason='Recorded diagnostic failure.'))
        task = next(a for a in self.graph()['activities'] if a['id']=='B')
        assessment = dict(contextSha256=task['retryContextSha256'], decision='continue_bounded',
                          userOutcome='Keep the approved recovery outcome and quality.', resources='Two failed attempts; elapsed cost unknown.',
                          alternatives='Independent storage work or an actual owner decision.', boundary='One bounded retry with contract A attempt1 unchanged.')
        (self.repo/'contract.py').write_text('contract v2')
        self.start('A', 'revised-contract'); self.finish('A', 'contract.py', 2, 'revised-contract')
        q=dict(deliveryId='DI-1', activityId='B', status='running', session='new-B', reassessment=assessment)
        self.unchanged_failure('activity', q, 'context')
        task = next(a for a in self.graph()['activities'] if a['id']=='B')
        assessment.update(contextSha256=task['retryContextSha256'], boundary='One bounded retry using the current A attempt2; stop on failure.')
        self.mutate('activity', q); self.finish('B', 'ui.py', 3, 'new-B')
        # Later prerequisite progress does not invalidate the recorded historical
        # assessment: it is checked against the actual prefix at its own start.
        (self.repo/'contract.py').write_text('contract v3')
        self.start('A', 'later-contract'); self.finish('A', 'contract.py', 3, 'later-contract')
        self.assertEqual(self.start('B', 'after-success'), 4)
        self.assertFalse(next(a for a in self.graph()['activities'] if a['id']=='B')['reassessmentRequired'])

    def test_running_descendant_fenced_by_dependency_receipt_and_binding(self):
        self.plan_graph()
        self.start("A"); self.finish("A", "contract.py")
        self.start("B")
        (self.repo / "contract.py").write_text("contract v2\n")
        before = (self.repo / ".aim/product-backlog.json").read_bytes()
        with self.assertRaisesRegex(StoryError, "inputs changed"):
            self.finish("B", "ui.py")
        self.assertEqual(before, (self.repo / ".aim/product-backlog.json").read_bytes())
        self.assertEqual([a["status"] for a in self.graph()["activities"]], ["stale"] * 4)
        self.assertEqual(self.graph()["readyIds"], [])
        self.assertEqual(self.graph()["recommendedIds"], ["A"])
        self.assertEqual(self.start("A", "retry-A"), 2)
        self.finish("A", "contract.py", 2, "retry-A")
        with self.assertRaisesRegex(StoryError, "inputs changed"):
            self.finish("B", "ui.py")
        self.assertEqual(next(a["status"] for a in self.graph()["activities"] if a["id"] == "B"), "stale")
        self.assertEqual(self.start("B", "retry-B"), 2)
        with self.assertRaisesRegex(StoryError, "session or attempt"):
            self.finish("B", "ui.py", 1)
        self.finish("B", "ui.py", 2, "retry-B")
        self.assertEqual(len(self.document["deliveries"][0]["activityReceipts"]), 4)

    def test_changed_or_symlinked_proof_fails_closed(self):
        self.plan_graph()
        self.start("A"); self.finish("A", "contract.py")
        proof = self.repo / ".aim/evidence/activity-A-1.txt"
        proof.unlink(); proof.symlink_to(self.repo / "contract.py")
        self.assertEqual(self.graph()["readyIds"], [])
        self.assertEqual(self.graph()["activities"][0]["status"], "stale")
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="B", status="running", session="B"), "prerequisites")

    def test_unapproved_blocked_fences_capacity_and_ownership(self):
        plan = diamond()
        plan["activities"].append(activity("E", ["contract.py"]))
        # D must cover every overlapping writer in the same scope.
        plan["activities"][3]["dependsOn"].append("E")
        self.plan_graph(plan, approve=False)
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="A", status="running", session="A"), "approved")
        self.mutate("approve", dict(deliveryId="DI-1", authority=self.authority(self.document["deliveries"][0]["scopeSha256"])))
        self.start("A")
        self.assertEqual(self.graph()["recommendedIds"], [])
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="E", status="running", session="E"), "overlaps")
        self.finish("A", "contract.py")
        self.start("B"); self.start("C")
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="E", status="running", session="E"), "capacity")
        self.mutate("block", dict(deliveryId="DI-1", reason="Need owner decision."))
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="B", status="failed", session="session-B", attempt=1, reason="Stopped"), "approved")

    def test_review_requires_current_all_activity_proof(self):
        self.plan_graph()
        self.unchanged_failure("review", dict(deliveryId="DI-1", sourcePaths=["contract.py"]), "unresolved or stale")
        self.start("A"); self.finish("A", "contract.py")
        self.start("B"); self.finish("B", "ui.py")
        self.start("C"); self.finish("C", "storage.py")
        self.assertEqual(self.graph()["readyIds"], ["D"])
        self.start("D"); self.finish("D", "contract.py")
        self.assertEqual(self.document["deliveries"][0]["status"], "in_progress")
        self.mutate("review", dict(deliveryId="DI-1", sourcePaths=["app.py", "contract.py", "ui.py", "storage.py"]))
        self.assertEqual(self.document["deliveries"][0]["status"], "review")
        # Activity completion never creates reviewer identity or Gate E proof.
        self.assertNotIn("reviewEvidence", self.document["deliveries"][0])
        self.assertNotIn("acceptance", self.document["deliveries"][0])
        (self.repo / "contract.py").write_text("contract v2\n")
        board = project_story_board(self.repo)
        self.assertFalse(board["valid"])
        self.assertEqual(board["executionGraph"]["activities"][0]["status"], "stale")

    def test_serial_no_delegation_and_cli_graph_are_read_only(self):
        plan = dict(version=1, delegationAllowed=False, maxWorkers=1,
                    activities=[activity("A", ["contract.py"]), activity("B", ["ui.py"], ["A"])])
        self.plan_graph(plan)
        self.start("A"); self.finish("A", "contract.py")
        self.assertEqual(self.graph()["recommendedIds"], ["B"])
        before = (self.repo / ".aim/product-backlog.json").read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/aim_stories.py"), "--repo", str(self.repo), "graph"],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["readyIds"], ["B"])
        self.assertEqual(before, (self.repo / ".aim/product-backlog.json").read_bytes())

    def test_assignment_contains_frozen_requirement_and_no_identity_claim(self):
        self.plan_graph()
        node = self.graph()["activities"][0]
        self.assertEqual(node["assignment"]["stories"][0]["acceptanceCriteria"][0]["id"], "AC-1")
        self.assertEqual(node["assignment"]["checks"][0]["id"], "QC-JOURNEY")
        self.assertFalse(node["assignment"]["skillAvailabilityVerified"])
        self.assertFalse(self.graph()["reviewIdentityVerified"])

    def test_dependency_change_during_completion_never_commits(self):
        self.plan_graph()
        self.start("A"); self.finish("A", "contract.py")
        self.start("B")
        def racing_binding(*args, **kwargs):
            result = _source_bindings(*args, **kwargs)
            (self.repo / "contract.py").write_text("contract changed during B completion\n")
            return result
        before = (self.repo / ".aim/product-backlog.json").read_bytes()
        with patch("aim_stories._source_bindings", side_effect=racing_binding):
            with self.assertRaisesRegex(StoryError, "changed during verification"):
                self.finish("B", "ui.py")
        self.assertEqual(before, (self.repo / ".aim/product-backlog.json").read_bytes())

    def test_actual_skill_disappearance_prevents_start(self):
        instructions = self.repo / "custom-skill.md"
        instructions.write_text("Inspect assigned product behavior.\n")
        (self.repo / "aim.roles.yaml").write_text("""aimProjectRoles:
  roles:
    dev:
      skills:
        - id: real-project-skill
          source: project
          status: available
          path: custom-skill.md
""")
        plan = diamond()
        plan["activities"][0]["skills"] = ["real-project-skill"]
        self.plan_graph(plan)
        instructions.unlink()
        self.unchanged_failure("activity", dict(deliveryId="DI-1", activityId="A", status="running", session="A"), "unavailable")

    def test_accepted_activity_history_remains_distinct_from_current_freshness(self):
        self.plan_graph()
        for identifier, source in (("A", "contract.py"), ("B", "ui.py"), ("C", "storage.py"), ("D", "contract.py")):
            self.start(identifier); self.finish(identifier, source)
        self.mutate("review", dict(deliveryId="DI-1", sourcePaths=["app.py"]))
        self.mutate("validate", dict(deliveryId="DI-1", evidence=[self.evidence]))
        self.mutate("acceptance", dict(deliveryId="DI-1", evidence=[self.evidence], criteria=[
            dict(storyId="US-BUYER", criterionId="AC-1", evidence=[self.evidence])]))
        self.mutate("accept", dict(deliveryId="DI-1", authority=self.authority(self.document["deliveries"][0]["acceptanceSha256"], self.acceptance)))
        before = (self.repo / ".aim/product-backlog.json").read_bytes()
        (self.repo / "contract.py").write_text("Later accepted product revision\n")
        board = project_story_board(self.repo)
        self.assertTrue(board["valid"])
        self.assertTrue(board["executionGraph"]["historical"])
        self.assertEqual(board["executionGraph"]["activities"][0]["status"], "stale")
        self.assertEqual(board["executionGraph"]["recommendedIds"], [])
        self.assertEqual(before, (self.repo / ".aim/product-backlog.json").read_bytes())

    def test_bounded_32_node_64_file_complete_projection(self):
        plan = dict(version=1, delegationAllowed=True, maxWorkers=8,
                    parallelBenefit="Independent source ownership in the fixed 32-node fixture.",
                    activities=[activity("N" + str(i), [f"source-{i}-0.txt", f"source-{i}-1.txt"]) for i in range(32)])
        for i in range(32):
            for j in range(2):
                (self.repo / f"source-{i}-{j}.txt").write_text(f"Source {i}:{j}\n")
        self.plan_graph(plan)
        for i in range(32):
            self.start("N" + str(i)); self.finish("N" + str(i), [f"source-{i}-0.txt", f"source-{i}-1.txt"])
        samples = []
        for _ in range(3):
            started = time.perf_counter_ns()
            graph = project_story_board(self.repo)["executionGraph"]
            samples.append((time.perf_counter_ns() - started) / 1_000_000)
            self.assertEqual(len(graph["activities"]), 32)
            self.assertEqual(graph["summary"]["completed"], 32)
            self.assertEqual(graph["readyIds"], [])
        self.assertLessEqual(max(samples), 100)
        print(json.dumps(dict(workload="32 completed activities / 64 bound local source files / 32 proof files", samplesMs=samples,
                              nodeCount=32, invalidReady=0, maximumMs=max(samples))))

    def test_plan_strictness_scope_binding_and_unconfigured_fallback(self):
        for mutation in (lambda p: p["activities"][0].update(storyIds=["US-LATER"]),
                         lambda p: p["activities"][0].update(skills=["invented-skill"]),
                         lambda p: p["activities"][0].update(surprise=True),
                         lambda p: p["activities"][0].update(paths=["../escape"]),
                         lambda p: p["activities"][0].update(dependsOn=["D"])):
            plan = diamond(); mutation(plan)
            with self.assertRaises((StoryError, ValueError)):
                self.plan_graph(plan)
        self.mutate("plan", dict(id="DI-1", title="Lifecycle", goal="Useful outcome", storyIds=["US-BUYER"], planEvidence=[self.plan_evidence]))
        graph = self.graph()
        self.assertFalse(graph["configured"])
        self.assertEqual(graph["readyIds"], [])
        self.assertEqual(len(graph["activities"]), 6)


if __name__ == "__main__":
    unittest.main()
