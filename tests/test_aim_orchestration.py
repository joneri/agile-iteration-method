"""Literal contracts for the experimental AIM 4.8 orchestration kernel."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aim_quality.orchestration import (  # noqa: E402
    assess_campaign,
    construct_default_graph,
    validate_graph,
)


def coordinator():
    return {
        "session": "actual-coordinator-session",
        "capability": {"id": "aim-native-orchestrator", "version": "4.8.0"},
        "permittedDecisions": [
            "continue_bounded", "independent_work", "change_baseline",
            "request_owner_choice", "reprioritize",
        ],
    }


def policy(**changes):
    result = {
        "delegationAllowed": True,
        "maxWorkers": 2,
        "checkpointAttemptBudget": 4,
        "parallelBenefit": "Disjoint outcome paths can progress while integration remains fenced.",
    }
    result.update(changes)
    return result


def outcomes():
    return [
        {"id": "AIM3D-MAJOR", "requirement": "Preserve the major user goal.", "paths": ["src/major"]},
        {"id": "AIM3D-RELEASE", "requirement": "Ship the approved release behavior.", "paths": ["src/release"]},
        {"id": "AIM3D-CONTACT", "requirement": "Keep the contact journey usable.", "paths": ["src/contact"]},
    ]


def event(outcome_id, kind, attempt, session, **extra):
    return {"outcomeId": outcome_id, "kind": kind, "attempt": attempt,
            "session": session, **extra}


def campaign(outcome_id="GOAL-A", *, budget=4, observations=(), waiting=None,
             priority=None, independent=None, no_progress_limit=None):
    result = {
        "version": 1,
        "outcomeId": outcome_id,
        "attemptBudget": budget,
        "waitingOriginalGoals": list(waiting if waiting is not None else [outcome_id]),
        "observations": list(observations),
    }
    if priority is not None:
        result["ownerPriority"] = list(priority)
    if independent is not None:
        result["independentReady"] = list(independent)
    if no_progress_limit is not None:
        result["noProgressLimit"] = no_progress_limit
    return result


class OrchestrationGraphTests(unittest.TestCase):
    def test_default_templates_link_every_outcome_and_keep_execution_declarative(self):
        for template in ("cohesive_delivery", "maintenance_repair",
                         "independent_branches", "bounded_investigation"):
            with self.subTest(template=template):
                graph = construct_default_graph(template, outcomes(), coordinator(), policy())
                self.assertEqual(graph["version"], 1)
                self.assertEqual(graph["origin"], {"kind": "default", "template": template})
                linked = {identifier for node in graph["nodes"] for identifier in node["outcomeIds"]}
                self.assertEqual(linked, {item["id"] for item in outcomes()})
                self.assertTrue(all(node["inputs"] and node["outputs"] and node["proofExpectations"]
                                    for node in graph["nodes"]))
                self.assertFalse(graph["execution"]["launchesAgents"])
                self.assertFalse(graph["execution"]["grantsAuthority"])

    def test_custom_origin_survives_validation_and_node_rename(self):
        graph = construct_default_graph("cohesive_delivery", outcomes(), coordinator(), policy())
        graph["origin"] = {"kind": "custom", "reference": "user-graph-release-contact-r2"}
        graph["nodes"][0]["id"] = "implementation-after-renamed-release"
        graph["nodes"][1]["dependsOn"] = ["implementation-after-renamed-release"]
        checked = validate_graph(graph)
        self.assertEqual(checked["origin"], graph["origin"])
        self.assertEqual(checked["nodes"][0]["id"], "implementation-after-renamed-release")

    def test_rejects_unknown_missing_unsafe_and_cyclic_graph_scope(self):
        graph = construct_default_graph("cohesive_delivery", outcomes(), coordinator(), policy())
        invalid = copy.deepcopy(graph)
        invalid["nodes"][0]["outcomeIds"] = ["MISSING"]
        with self.assertRaisesRegex(ValueError, "unknown outcome"):
            validate_graph(invalid)
        invalid = copy.deepcopy(graph)
        invalid["outcomes"].append({"id": "UNLINKED", "requirement": "Explicit but missing.",
                                    "paths": ["src/unlinked"]})
        with self.assertRaisesRegex(ValueError, "Every explicit outcome"):
            validate_graph(invalid)
        invalid = copy.deepcopy(graph)
        invalid["outcomes"][0]["paths"] = ["../outside"]
        with self.assertRaises(ValueError):
            validate_graph(invalid)
        invalid = copy.deepcopy(graph)
        invalid["nodes"][0]["dependsOn"] = [invalid["nodes"][1]["id"]]
        with self.assertRaisesRegex(ValueError, "cycle"):
            validate_graph(invalid)
        invalid = copy.deepcopy(graph)
        invalid["execution"]["grantsAuthority"] = True
        with self.assertRaisesRegex(ValueError, "cannot launch agents"):
            validate_graph(invalid)


class CampaignAssessmentTests(unittest.TestCase):
    def test_aim3d_five_outcomes_preserve_major_first_across_renamed_variants(self):
        goals = ["AIM3D-MAJOR", "AIM3D-RELEASE", "AIM3D-CONTACT", "AIM3D-API", "AIM3D-OPS"]
        results = {}
        for index, goal in enumerate(goals):
            history = [
                event(goal, "activity", 1, f"release-r{index + 1}",
                      activityId=f"release-check-{index}", graphRevision="graph-r1",
                      resourceDelta={"tokens": 4}),
                event(goal, "component_pass", 2, f"contact-r{index + 2}",
                      activityId=f"contact-check-{index}", graphRevision="graph-r2",
                      resourceDelta={"tokens": None if goal == "AIM3D-RELEASE" else 2}),
            ]
            if goal == "AIM3D-RELEASE":
                history.append(event(goal, "heartbeat", 2, "renamed-contact-r8",
                                     activityId="new-contact-observer", graphRevision="graph-r3",
                                     resourceDelta={"tokens": 3}))
            results[goal] = assess_campaign(campaign(
                goal, budget=5, observations=history, waiting=goals, priority=goals,
                no_progress_limit=2,
            ))
        self.assertEqual([results[goal]["waitingOriginalGoals"] for goal in goals], [goals] * 5)
        self.assertTrue(all(not results[goal]["acceptanceInferred"] for goal in goals))
        self.assertTrue(all(results[goal]["noProgressStreak"] >= 2 for goal in goals))
        self.assertEqual(results["AIM3D-MAJOR"]["recommendation"]["action"], "change_diagnostic_action")
        for goal in goals[1:]:
            self.assertEqual(results[goal]["recommendation"]["action"], "work_owner_priority_first")
            self.assertEqual(results[goal]["recommendation"]["targetOutcomeId"], "AIM3D-MAJOR")
        self.assertIn("tokens", results["AIM3D-RELEASE"]["resources"]["unknownUnits"])

    def test_old_orchestrator_check_and_schedule_completion_is_not_product_progress(self):
        goals = ["BUYER-RECOVERY", "BUYER-EXPORT"]
        history = [
            event("BUYER-RECOVERY", "component_pass", 1, "old-coordinator", resourceDelta={"minutes": 12}),
            event("BUYER-RECOVERY", "activity", 2, "new-coordinator"),
            event("BUYER-RECOVERY", "heartbeat", 2, "new-session"),
        ]
        result = assess_campaign(campaign(
            "BUYER-RECOVERY", budget=3, observations=history,
            waiting=goals, no_progress_limit=2,
        ))
        self.assertEqual(result["noProgressStreak"], 2)
        self.assertEqual(result["recommendation"]["action"], "change_diagnostic_action")
        self.assertEqual(result["waitingOriginalGoals"], goals)
        self.assertFalse(result["acceptanceInferred"])

    def test_meaningful_falsifier_justifies_one_bounded_hard_debug_step(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="fixture-v1",
                  metric="latency", direction="lower", value=10, usable=True),
            event("GOAL-A", "activity", 1, "s1"),
            event("GOAL-A", "falsifier", 2, "s2", informationGain=True),
        ]
        result = assess_campaign(campaign(observations=history, budget=3))
        self.assertEqual(result["recommendation"]["action"], "continue_bounded_debugging")
        self.assertEqual(result["attemptsUsed"], 2)
        self.assertEqual(result["noProgressStreak"], 2)
        self.assertEqual(result["noProgressLimit"], 3)  # Defaults to the attempt budget.

    def test_falsifier_gain_is_consumed_by_one_followup_attempt(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="fixture-v1",
                  metric="latency", direction="lower", value=10, usable=True),
            event("GOAL-A", "falsifier", 1, "s1", informationGain=True),
            event("GOAL-A", "activity", 2, "s2"),
            event("GOAL-A", "activity", 3, "s3"),
        ]
        result = assess_campaign(campaign(
            observations=history, budget=5, no_progress_limit=2,
        ))
        self.assertEqual(result["noProgressStreak"], 3)
        self.assertEqual(result["recommendation"]["action"], "change_diagnostic_action")

    def test_crash_or_freeze_is_a_blocking_failure_not_a_cosmetic_pass(self):
        history = [
            event("GOAL-A", "activity", 1, "diagnosis-r1"),
            event("GOAL-A", "freeze", 2, "diagnosis-r2"),
        ]
        result = assess_campaign(campaign(observations=history, budget=3))
        self.assertEqual(result["recommendation"]["action"], "debug_blocking_failure")
        self.assertIn("real blocking failure", result["recommendation"]["why"])
        self.assertEqual(result["noProgressStreak"], 2)

    def test_only_comparable_integrated_improvement_resets_no_progress(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="journey-v1",
                  metric="success_rate", direction="higher", value=0.70, usable=True),
            event("GOAL-A", "component_pass", 1, "s1"),
            event("GOAL-A", "integrated_progress", 2, "s2", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.72),
        ]
        result = assess_campaign(campaign(observations=history, budget=4))
        self.assertEqual(result["noProgressStreak"], 0)
        self.assertEqual(result["latestUsableBaseline"]["baselineId"], "base-1")
        self.assertFalse(result["acceptanceInferred"])

    def test_best_integrated_value_does_not_regress_on_a_lower_measurement(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="journey-v1",
                  metric="success_rate", direction="higher", value=0.70, usable=True),
            event("GOAL-A", "integrated_progress", 1, "s1", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.72),
            event("GOAL-A", "integrated_progress", 2, "s2", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.50),
            event("GOAL-A", "integrated_progress", 3, "s3", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.60),
        ]
        result = assess_campaign(campaign(observations=history, budget=5, no_progress_limit=2))
        self.assertEqual(result["bestValue"]["value"], 0.72)
        self.assertEqual(result["noProgressStreak"], 2)
        self.assertNotEqual(result["recommendation"]["action"], "continue_original_outcome")

    def test_improved_integrated_evidence_clears_active_crash_but_keeps_history(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="journey-v1",
                  metric="success_rate", direction="higher", value=0.70, usable=True),
            event("GOAL-A", "freeze", 1, "s1"),
            event("GOAL-A", "integrated_progress", 2, "s2", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.71),
        ]
        result = assess_campaign(campaign(observations=history, budget=3, no_progress_limit=2))
        self.assertIsNone(result["activeBlockingFailure"])
        self.assertEqual([item["kind"] for item in result["blockingFailureHistory"]], ["freeze"])
        self.assertEqual(result["noProgressStreak"], 0)

    def test_attempt_budget_restarts_after_progress_and_reports_cumulative_attempts(self):
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="journey-v1",
                  metric="success_rate", direction="higher", value=0.70, usable=True),
            event("GOAL-A", "activity", 1, "s1"),
            event("GOAL-A", "activity", 2, "s2"),
            event("GOAL-A", "activity", 3, "s3"),
            event("GOAL-A", "integrated_progress", 4, "s4", baselineId="base-1",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.72),
            event("GOAL-A", "activity", 5, "s5"),
        ]
        result = assess_campaign(campaign(observations=history, budget=4, no_progress_limit=3))
        self.assertEqual(result["totalAttempts"], 5)
        self.assertEqual(result["attemptsSinceImprovement"], 1)
        self.assertFalse(result["budgetExhausted"])

    def test_heartbeat_does_not_consume_attempt_or_count_as_no_progress(self):
        history = [
            event("GOAL-A", "activity", 1, "s1", activityId="implementation"),
            event("GOAL-A", "component_pass", 1, "s1", activityId="implementation"),
            event("GOAL-A", "heartbeat", 2, "s2", activityId="renamed-monitor"),
            event("GOAL-A", "heartbeat", 2, "s3", activityId="new-monitor"),
        ]
        result = assess_campaign(campaign(observations=history, budget=2, no_progress_limit=2))
        self.assertEqual(result["totalAttempts"], 1)
        self.assertEqual(result["attemptsSinceImprovement"], 1)
        self.assertEqual(result["noProgressStreak"], 1)
        self.assertFalse(result["budgetExhausted"])

    def test_budget_exhaustion_changes_action_but_keeps_independent_work_ready(self):
        history = [
            event("GOAL-A", "activity", 1, "session-a", resourceDelta={"tokens": 5, "minutes": 2}),
            event("GOAL-A", "heartbeat", 2, "session-b", resourceDelta={"tokens": None, "minutes": 3}),
            event("GOAL-A", "component_pass", 2, "session-c", resourceDelta={"tokens": 2}),
        ]
        result = assess_campaign(campaign(
            observations=history, budget=2, waiting=["GOAL-A", "GOAL-B"], independent=["GOAL-B"],
        ))
        self.assertEqual(result["recommendation"]["action"], "work_independent_ready")
        self.assertEqual(result["recommendation"]["targetOutcomeId"], "GOAL-B")
        self.assertEqual(result["resources"]["knownTotals"], {"tokens": 7, "minutes": 5})
        self.assertEqual(result["resources"]["unknownUnits"], ["tokens"])
        self.assertTrue(result["resources"]["cumulativeAcrossSessions"])

    def test_budget_exhaustion_without_ready_work_requires_owner_choice(self):
        result = assess_campaign(campaign(
            observations=[event("GOAL-A", "activity", 1, "s1"),
                          event("GOAL-A", "activity", 2, "s2")],
            budget=2, no_progress_limit=2,
        ))
        self.assertEqual(result["recommendation"]["action"], "request_owner_choice")
        self.assertIn("changed action is required", result["recommendation"]["why"])

    def test_session_and_graph_activity_changes_do_not_reset_streak_or_identity(self):
        history = [
            event("GOAL-A", "activity", 1, "release-session", activityId="release-check",
                  graphRevision="graph-r1"),
            event("GOAL-A", "component_pass", 2, "contact-session", activityId="contact-check",
                  graphRevision="graph-r2"),
        ]
        result = assess_campaign(campaign("GOAL-A", budget=4, observations=history))
        self.assertEqual(result["outcomeId"], "GOAL-A")
        self.assertEqual(result["noProgressStreak"], 2)

    def test_rejects_cross_outcome_history_and_uncomparable_integrated_claims(self):
        with self.assertRaisesRegex(ValueError, "stable campaign identity"):
            assess_campaign(campaign(observations=[event("OTHER", "activity", 1, "s1")]))
        history = [
            event("GOAL-A", "baseline", 0, "s0", baselineId="base-1", comparisonKey="journey-v1",
                  metric="success_rate", direction="higher", value=0.70, usable=True),
            event("GOAL-A", "integrated_progress", 1, "s1", baselineId="base-old",
                  comparisonKey="journey-v1", metric="success_rate", direction="higher", value=0.90),
        ]
        result = assess_campaign(campaign(observations=history, budget=3))
        self.assertEqual(result["noProgressStreak"], 1)


if __name__ == "__main__":
    unittest.main()
