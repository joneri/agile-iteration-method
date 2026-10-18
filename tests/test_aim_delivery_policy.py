"""Native policy/owner boundaries; fixtures declare no real human acceptance."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest

import test_aim_stories as fixtures
from aim_stories import FILE, StoryError, _scope, compact_result, digest, execute, load, validate_document


class DeliveryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.StoryDeliveryTests(methodName="runTest")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.mandate = self.case.artifact("human-owner-mandate.md", "Synthetic human delegation of product decisions to owner-session.")
        self.owner = dict(kind="agent", id="owner", session="owner-session", mandate=self.mandate,
                          decisions=["approve", "accept"])

    def plan(self, policy=None, execution_plan=None):
        request = dict(id="DI-1", title="Recover and explain", goal="Both fixture personas can recover",
                       storyIds=["US-BUYER", "US-AGENT"], planEvidence=[self.case.plan_evidence])
        if policy is not None:
            request["deliveryPolicy"] = policy
        if execution_plan is not None:
            request["executionPlan"] = execution_plan
        return self.case.mutate("plan", request)

    @property
    def delivery(self):
        return self.case.document["deliveries"][0]

    def decision(self, scope, operation="approve"):
        record = dict(ownerDecisionVersion=1, deliveryId="DI-1", operation=operation,
                      scopeSha256=scope, id="owner", session="owner-session", decision="approved",
                      reason="Synthetic actual owner assessment of the frozen scope and current evidence.")
        evidence = self.case.artifact("owner-decision-"+str(self.case.document["revision"])+".json", json.dumps(record))
        return dict(kind="agent", id="owner", session="owner-session", **evidence,
                    scopeSha256=scope)

    def reject(self, command, request, pattern):
        before = (self.case.repo / FILE).read_bytes()
        with self.assertRaisesRegex((StoryError, ValueError), pattern):
            execute(self.case.repo, command, request, self.case.token)
        self.assertEqual(before, (self.case.repo / FILE).read_bytes())

    def test_default_ship_persists_and_is_visible_in_receipt(self):
        result = self.plan()
        self.assertEqual(self.delivery["deliveryPolicy"], {"mode":"ship", "owner":{"kind":"human"}})
        receipt = compact_result(result, receipt=True, delivery_id="DI-1")
        self.assertEqual(receipt["document"]["deliveries"][0]["deliveryPolicy"]["mode"], "ship")
        saved, _ = load(self.case.repo)
        self.assertEqual(saved["deliveries"][0]["deliveryPolicy"], self.delivery["deliveryPolicy"])

    def test_explicit_loop_keeps_human_owner_by_default(self):
        self.plan({"mode":"loop"})
        self.assertEqual(self.delivery["deliveryPolicy"], {"mode":"loop", "owner":{"kind":"human"}})

    def test_invalid_mode_and_implicit_agent_rejected_without_writes(self):
        for policy in ({"mode":"auto"}, {"mode":[]}, {"mode":"loop", "owner":{"kind":"agent"}},
                       {"mode":"ship", "owner":{"kind":"human", "decisions":["accept"]}}):
            with self.subTest(policy=policy):
                before = (self.case.repo / FILE).read_bytes()
                with self.assertRaises((StoryError, ValueError)):
                    self.plan(policy)
                self.assertEqual(before, (self.case.repo / FILE).read_bytes())

    def test_frozen_policy_cannot_be_changed(self):
        self.plan({"mode":"loop"})
        changed = copy.deepcopy(self.case.document)
        changed["deliveries"][0]["deliveryPolicy"]["mode"] = "ship"
        with self.assertRaisesRegex(StoryError, "scope fingerprint"):
            validate_document(changed)

    def test_legacy_absent_policy_loads_without_reinterpretation(self):
        self.plan()
        legacy = copy.deepcopy(self.case.document)
        del legacy["deliveries"][0]["deliveryPolicy"]
        legacy["deliveries"][0]["scopeSha256"] = digest(_scope(legacy["deliveries"][0]))
        path = self.case.repo / FILE
        path.write_text(json.dumps(legacy))
        before = path.read_bytes()
        document, _ = load(self.case.repo)
        self.assertNotIn("deliveryPolicy", document["deliveries"][0])
        self.assertEqual(path.read_bytes(), before)

    def test_agent_cannot_approve_default_human_delivery(self):
        self.plan()
        self.reject("approve", dict(deliveryId="DI-1", authority=self.decision(self.delivery["scopeSha256"])), "No agent owner")

    def test_named_agent_can_approve_and_accept_complete_verified_delivery(self):
        self.plan({"mode":"loop", "owner":self.owner})
        self.case.mutate("approve", dict(deliveryId="DI-1", authority=self.decision(self.delivery["scopeSha256"])))
        self.case.mutate("review", dict(deliveryId="DI-1", bindings=[self.case.binding]))
        self.case.mutate("validate", dict(deliveryId="DI-1", evidence=[self.case.evidence]))
        self.case.mutate("acceptance", dict(deliveryId="DI-1", evidence=[self.case.evidence], criteria=self.case.criterion_evidence()))
        self.case.mutate("accept", dict(deliveryId="DI-1", authority=self.decision(self.delivery["acceptanceSha256"], "accept")))
        saved, _ = load(self.case.repo)
        self.assertEqual(saved["deliveries"][0]["status"], "accepted")
        self.assertEqual(saved["deliveries"][0]["acceptance"]["kind"], "agent")
        self.assertTrue(all(s["status"] == "done" for s in saved["stories"] if s["id"] != "US-LATER"))

    def test_delegated_loop_preserves_graph_completion_gate(self):
        graph = dict(version=1, delegationAllowed=False, maxWorkers=1, activities=[dict(
            id="BUILD", title="Build both fixture journeys", kind="write", role="dev",
            storyIds=["US-BUYER", "US-AGENT"], paths=["app.py"], dependsOn=[])])
        self.plan({"mode":"loop", "owner":self.owner}, execution_plan=graph)
        self.case.mutate("approve", dict(deliveryId="DI-1", authority=self.decision(self.delivery["scopeSha256"])))
        self.reject("review", dict(deliveryId="DI-1", sourcePaths=["app.py"]), "unresolved or stale")
        self.case.mutate("activity", dict(deliveryId="DI-1", activityId="BUILD", status="running", session="fixture-dev"))
        self.case.mutate("activity", dict(deliveryId="DI-1", activityId="BUILD", status="completed",
            session="fixture-dev", attempt=1, sourcePaths=["app.py"], evidence=[self.case.evidence]))
        self.assertNotIn("acceptance", self.delivery)
        self.case.mutate("review", dict(deliveryId="DI-1", bindings=[self.case.binding]))
        self.case.mutate("validate", dict(deliveryId="DI-1", evidence=[self.case.evidence]))
        self.case.mutate("acceptance", dict(deliveryId="DI-1", evidence=[self.case.evidence], criteria=self.case.criterion_evidence()))
        self.case.mutate("accept", dict(deliveryId="DI-1", authority=self.decision(self.delivery["acceptanceSha256"], "accept")))
        saved, _ = load(self.case.repo)
        self.assertEqual(saved["deliveries"][0]["status"], "accepted")
        self.assertEqual(saved["deliveries"][0]["deliveryPolicy"]["mode"], "loop")
        self.assertEqual(saved["deliveries"][0]["activityReceipts"][0]["status"], "completed")

    def test_owner_identity_and_operation_must_match_delegation(self):
        owner = {**self.owner, "decisions":["accept"]}
        self.plan({"mode":"loop", "owner":owner})
        self.reject("approve", dict(deliveryId="DI-1", authority=self.decision(self.delivery["scopeSha256"])), "not delegated")

    def test_verified_product_does_not_grant_undelegated_acceptance(self):
        owner = {**self.owner, "decisions":["approve"]}
        self.plan({"mode":"loop", "owner":owner})
        self.case.mutate("approve", dict(deliveryId="DI-1", authority=self.decision(self.delivery["scopeSha256"])))
        self.case.mutate("review", dict(deliveryId="DI-1", bindings=[self.case.binding]))
        self.case.mutate("validate", dict(deliveryId="DI-1", evidence=[self.case.evidence]))
        self.case.mutate("acceptance", dict(deliveryId="DI-1", evidence=[self.case.evidence], criteria=self.case.criterion_evidence()))
        self.reject("accept", dict(deliveryId="DI-1", authority=self.decision(self.delivery["acceptanceSha256"], "accept")), "not delegated")

    def test_wrong_session_or_scope_cannot_approve(self):
        self.plan({"mode":"loop", "owner":self.owner})
        decision = self.decision(self.delivery["scopeSha256"])
        self.reject("approve", dict(deliveryId="DI-1", authority={**decision,"session":"another-session"}), "identity")
        self.reject("approve", dict(deliveryId="DI-1", authority={**decision,"scopeSha256":"0"*64}), "stale or different")

    def test_mandate_cannot_replace_actual_owner_decision(self):
        self.plan({"mode":"loop", "owner":self.owner})
        decision = {**self.decision(self.delivery["scopeSha256"]), **self.mandate}
        self.reject("approve", dict(deliveryId="DI-1", authority=decision), "actual gate decision")

    def test_copied_mandate_is_not_an_agent_decision(self):
        self.plan({"mode":"loop", "owner":self.owner})
        copied = self.case.artifact("copied-mandate.md", (self.case.repo/self.mandate["path"]).read_text())
        decision = {**self.decision(self.delivery["scopeSha256"]), **copied}
        self.reject("approve", dict(deliveryId="DI-1", authority=decision), "actual gate decision")

    def test_decision_evidence_cannot_be_retargeted(self):
        self.plan({"mode":"loop", "owner":self.owner})
        for changes in ({"operation":"accept"}, {"deliveryId":"DI-OTHER"},
                        {"scopeSha256":"0"*64}, {"session":"other"}):
            decision = self.decision(self.delivery["scopeSha256"])
            path = self.case.repo / decision["path"]
            record = {**json.loads(path.read_text()), **changes}
            artifact = self.case.artifact(path.name, json.dumps(record))
            self.reject("approve", dict(deliveryId="DI-1", authority={**decision, **artifact}), "does not match")

    def test_changed_mandate_invalidates_gate_before_write(self):
        self.plan({"mode":"loop", "owner":self.owner})
        decision = self.decision(self.delivery["scopeSha256"])
        (self.case.repo / self.mandate["path"]).write_text("changed delegation")
        self.reject("approve", dict(deliveryId="DI-1", authority=decision), "Evidence changed")

    def test_native_cli_preserves_explicit_policy(self):
        self.plan({"mode":"loop", "owner":self.owner})
        for base in (fixtures.ROOT, fixtures.ROOT/"skills/agile-iteration-method"):
            with self.subTest(package=base):
                result = subprocess.run([sys.executable, str(base/"scripts/aim_stories.py"), "--repo", str(self.case.repo),
                                         "--compact", "status"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
                document = json.loads(result.stdout)["document"]
                self.assertEqual(document["deliveries"][0]["deliveryPolicy"]["owner"]["session"], "owner-session")


if __name__ == "__main__":
    unittest.main()
