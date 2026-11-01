"""Owner direction changes are terminal decisions, never fabricated acceptance.

All owner instructions in these temporary repositories are synthetic fixtures.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_aim_stories as fixture
import test_aim_orchestration_runtime as native

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from aim_stories import (FILE, compact_result, digest, disposition_context, execute,
                         load, project_story_board, validate_document)
from aim_quality.orchestration_runtime import campaign_for


class OwnerDispositionTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    plan = fixture.StoryDeliveryTests.plan
    authority = fixture.StoryDeliveryTests.authority
    approve = fixture.StoryDeliveryTests.approve
    ready_for_acceptance = fixture.StoryDeliveryTests.ready_for_acceptance
    criterion_evidence = fixture.StoryDeliveryTests.criterion_evidence
    accept = fixture.StoryDeliveryTests.accept
    unchanged_failure = fixture.StoryDeliveryTests.unchanged_failure

    def disposition_request(self, operation="cancel", **changes):
        return dict(deliveryId="DI-1", operation=operation,
                    reason="Synthetic owner no longer wants the optional feature.", **changes)

    def decision(self, request):
        before = (self.repo / FILE).read_bytes()
        context = disposition_context(self.repo, request)
        self.assertEqual(before, (self.repo / FILE).read_bytes())
        evidence = self.artifact("disposition-"+str(self.document["revision"])+".json",
                                 json.dumps(context["decisionEvidence"]))
        return {k:v for k,v in request.items() if k != "operation"} | dict(
            authority=self.authority(context["scopeSha256"], evidence))

    def assert_history(self, original, delivery):
        restored = copy.deepcopy(delivery)
        record = restored.pop("disposition")
        restored["status"] = record["context"]["fromStatus"]
        self.assertEqual(original, restored)
        self.assertEqual(record["context"]["deliverySha256"], digest(original))
        self.assertEqual(delivery["status"], "cancelled")
        self.assertNotIn("acceptance", delivery)

    def replacement(self):
        story = {**copy.deepcopy(self.request["stories"][0]), "id":"US-NEXT",
                 "acceptanceCriteria":[dict(id="AC-NEXT",text="Complete the new outcome without the optional feature.")]}
        self.mutate("import", dict(stories=[story]))
        quality = copy.deepcopy(self.document["deliveries"][0]["qualityPlan"])
        quality["checks"][0]["criteria"] = ["US-NEXT/AC-NEXT"]
        return dict(id="DI-2", title="Owner's current direction", goal="Deliver current intent",
                    storyIds=["US-NEXT"], planEvidence=[self.plan_evidence], qualityPlan=quality)

    def test_cancel_each_approved_phase_preserves_full_snapshot_and_releases_slot(self):
        for phase in ("in_progress", "review", "validation", "acceptance", "blocked"):
            with self.subTest(phase=phase):
                self.setUp()
                self.ready_for_acceptance() if phase in {"acceptance","blocked"} else self.approve()
                if phase in {"review","validation"}:
                    self.mutate("review", dict(deliveryId="DI-1",bindings=[self.binding]))
                if phase == "validation":
                    self.mutate("validate", dict(deliveryId="DI-1",evidence=[self.evidence]))
                if phase == "blocked":
                    self.mutate("block", dict(deliveryId="DI-1",reason="Old failure, retained verbatim."))
                original = copy.deepcopy(self.document["deliveries"][0])
                request = self.decision(self.disposition_request())
                result = self.mutate("cancel", request)
                self.assert_history(original,self.document["deliveries"][0])
                self.assertTrue(all(s["status"] == "draft" for s in self.document["stories"]))
                self.assertEqual(result["nextStep"], [{"operation":"refine"}])
                receipt=compact_result(result,receipt=True,delivery_id="DI-1")
                self.assertEqual(receipt["document"]["deliveries"][0]["disposition"],self.document["deliveries"][0]["disposition"])
                board = project_story_board(self.repo)
                self.assertTrue(board["valid"],board["issues"])
                self.assertFalse(board["executionGraph"]["available"])
                from aim_quality.graph import project_graph
                history=project_graph(self.repo,self.document,self.token,"DI-1")
                self.assertTrue(history["historical"])
                self.assertFalse(any(a["status"]=="running" for a in history["activities"]))
                self.assertTrue(all(not s["waitingForOwner"] and not s["deliveryIds"] for s in board["stories"]))
                # Replanning can change current requirements, while the old
                # snapshot retains exactly the original optional feature.
                story=copy.deepcopy(self.request["stories"][0])
                story["acceptanceCriteria"]=[dict(id="AC-CURRENT",text="Current owner requirement.")]
                self.mutate("refine",dict(stories=[story]))
                self.mutate("plan",dict(id="DI-2",title="New plan",goal="Current goal",
                    storyIds=[story["id"]],planEvidence=[self.plan_evidence]))
                self.assertEqual(self.document["deliveries"][1]["status"],"planned")
                self.assert_history(original,self.document["deliveries"][0])

    def test_cancel_requires_present_exact_human_decision_and_current_cas(self):
        self.approve()
        self.unchanged_failure("cancel",dict(deliveryId="DI-1",reason="Changed mind"),"Missing fields")
        req=self.decision(self.disposition_request())
        for changed in ({"reason":"Different owner reason"},
                        {"authority":self.authority(self.document["deliveries"][0]["scopeSha256"])},
                        {"authority":{**req["authority"],"kind":"auto"}}):
            with self.subTest(changed=changed):
                self.unchanged_failure("cancel",req|changed,"scope|user authority|acceptance")
        old_token=self.token
        self.mutate("block",dict(deliveryId="DI-1",reason="New current obstacle"))
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,"Stale product backlog"):
            execute(self.repo,"cancel",req,old_token)
        self.assertEqual(before,(self.repo/FILE).read_bytes())
        self.unchanged_failure("cancel",req,"stale or different scope")

    def test_old_approval_cannot_be_relabelled_as_a_cancellation(self):
        self.approve()
        req=self.decision(self.disposition_request())
        req["authority"]={**req["authority"],**self.approval}
        self.unchanged_failure("cancel",req,"JSON|Expecting value")

    def test_decision_changed_or_duplicate_keys_are_rejected_atomically(self):
        self.approve()
        req=self.decision(self.disposition_request())
        p=self.repo/req["authority"]["path"]
        text=p.read_text();p.write_text(text+" ")
        self.unchanged_failure("cancel",req,"Evidence changed")
        import hashlib
        p.write_text(text[:-1]+',"operation":"cancel"}')
        req["authority"]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.unchanged_failure("cancel",req,"Duplicate disposition")

    def test_stale_product_and_failed_measurements_do_not_prevent_abandoning_work(self):
        self.ready_for_acceptance()
        original=copy.deepcopy(self.document["deliveries"][0])
        (self.repo/"app.py").write_text("# New product direction; previous bindings are obsolete.\n")
        self.mutate("cancel",self.decision(self.disposition_request()))
        self.assert_history(original,self.document["deliveries"][0])
        load(self.repo)

    def test_changed_or_missing_obsolete_quality_and_review_artifacts_do_not_block_disposition(self):
        for artifact_kind in ("quality", "review"):
            for missing in (False, True):
                with self.subTest(artifact=artifact_kind,missing=missing):
                    self.setUp();self.ready_for_acceptance()
                    original=copy.deepcopy(self.document["deliveries"][0])
                    ref=(original["coreVerification"]["qualityMeasurements"][0]
                         if artifact_kind=="quality" else original["reviewEvidence"][0])
                    path=self.repo/ref["path"]
                    path.unlink() if missing else path.write_text("Obsolete report from an abandoned direction.\n")
                    self.mutate("cancel",self.decision(self.disposition_request()))
                    self.assert_history(original,self.document["deliveries"][0])
                    load(self.repo)

    def test_replace_commits_one_revision_with_new_unapproved_scope(self):
        self.approve()
        replacement=self.replacement()
        original=copy.deepcopy(self.document["deliveries"][0])
        req=self.decision(self.disposition_request("replace",replacement=replacement))
        before=self.document["revision"]
        self.mutate("replace",req)
        self.assertEqual(self.document["revision"],before+1)
        old,new=self.document["deliveries"]
        self.assert_history(original,old)
        self.assertEqual(old["disposition"]["context"]["replacement"],dict(id="DI-2",scopeSha256=new["scopeSha256"]))
        self.assertEqual(new["status"],"planned")
        self.assertNotIn("approval",new)
        self.assertEqual([s["id"] for s in new["stories"]],["US-NEXT"])
        board=project_story_board(self.repo)
        self.assertTrue(board["valid"],board["issues"])
        self.assertEqual(board["executionGraph"]["deliveryId"],"DI-2")
        self.assertEqual(self.document["stories"][0]["status"],"draft")
        self.assertEqual(self.document["stories"][-1]["status"],"ready")
        self.mutate("approve",dict(deliveryId="DI-2",authority=self.authority(new["scopeSha256"])))
        self.assertEqual(self.document["deliveries"][-1]["status"],"in_progress")

    def test_invalid_or_changed_replacement_cannot_cancel_the_original(self):
        self.approve()
        replacement=self.replacement()
        req=self.decision(self.disposition_request("replace",replacement=replacement))
        bad=copy.deepcopy(req);bad["replacement"]["goal"]="A different replacement"
        self.unchanged_failure("replace",bad,"stale or different scope")
        for delta in ({"id":"DI-1"},{"storyIds":["US-MISSING"]},{"qualityPlan":{}},
                      {"storyIds":["US-BUYER"]}):
            with self.subTest(delta=delta):
                self.unchanged_failure("replace",req|dict(replacement=replacement|delta),
                                       "already allocated|Unknown|plan|ready Stories")
        self.unchanged_failure("cancel",req,"Only replace")

    def test_replacement_revalidates_correction_provenance_and_retains_original_target(self):
        from aim_story_links import requirements_scope, catalog
        from unittest.mock import patch
        self.approve()
        replacement=self.replacement()
        original=self.document["deliveries"][0]
        story=copy.deepcopy(self.request["stories"][0])
        story.update(id="US-NEXT",acceptanceCriteria=[dict(id="AC-NEXT",text="Complete the new outcome without the optional feature.")],
                     corrects=[dict(deliveryId="DI-1",storyId="US-BUYER",criterionIds=["AC-1"],
                                    scopeSha256=requirements_scope(original,original["stories"][0]))])
        self.mutate("refine",dict(stories=[story]))
        req=self.decision(self.disposition_request("replace",replacement=replacement))
        # Independently inject a provenance rejection at the shared gate; the
        # original cancellation must not commit if replacement validation fails.
        with patch("aim_story_links.validate_links",side_effect=ValueError("Correction provenance changed")) as validate:
            before=(self.repo/FILE).read_bytes()
            with self.assertRaisesRegex(ValueError,"Correction provenance changed"):
                self.mutate("replace",req)
            self.assertEqual(before,(self.repo/FILE).read_bytes())
            self.assertEqual(validate.call_args[0][0][0]["id"],"US-NEXT")
        self.mutate("replace",req)
        records=catalog(self.document,{})
        self.assertIn(("DI-1","US-BUYER"),records)
        self.assertTrue(project_story_board(self.repo)["valid"])

    def test_gate_delegation_is_not_cancellation_authority(self):
        self.approve()
        req=self.decision(self.disposition_request())
        delegated={**req["authority"],"kind":"agent","id":"owner","session":"actual-owner-session"}
        self.unchanged_failure("cancel",{**req,"authority":delegated},"Historical deliveries have no delegated")

    def test_accepted_and_already_disposed_deliveries_are_immutable(self):
        self.accept()
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,"approved, unaccepted"):
            disposition_context(self.repo,self.disposition_request())
        self.assertEqual(before,(self.repo/FILE).read_bytes())
        self.setUp();self.approve();req=self.decision(self.disposition_request())
        self.mutate("cancel",req)
        self.unchanged_failure("cancel",req,"approved, unaccepted")
        for command,payload in (("unblock",dict(reason="Resume")),("rework",dict(reason="Resume")),
                                ("accept",dict(authority=req["authority"]))):
            self.unchanged_failure(command,dict(deliveryId="DI-1",**payload),"blocked|Rework requires|Gate E")

    def test_tampered_history_and_missing_replacement_links_fail_structural_validation(self):
        self.approve();replacement=self.replacement()
        self.mutate("replace",self.decision(self.disposition_request("replace",replacement=replacement)))
        for changed in ("approval","reason","receipt","replacement","record"):
            with self.subTest(changed=changed):
                d=copy.deepcopy(self.document);old=d["deliveries"][0]
                if changed=="approval": old["approval"]["path"]=".aim/fake.md"
                if changed=="reason": old["reason"]="Erased failure"
                if changed=="receipt": old["coreVerification"]={**old["coreVerification"],"at":"changed"}
                if changed=="replacement": d["deliveries"].pop()
                if changed=="record": old.pop("disposition")
                with self.assertRaises(ValueError):validate_document(d)

    def test_real_cli_preview_cancel_receipt_and_fresh_status(self):
        self.approve();request=self.disposition_request()
        root=Path(__file__).resolve().parents[1]
        def cli(command,payload=None,**extra):
            args=[sys.executable,str(root/"scripts/aim_stories.py"),"--repo",str(self.repo),command,"--compact"]
            if payload is not None:args += ["--expected-sha256",self.token]
            p=subprocess.run(args,input=json.dumps(payload) if payload else None,text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr)
            return json.loads(p.stdout)
        preview=cli("disposition-context",request)
        evidence=self.artifact("cli-owner.json",json.dumps(preview["decisionEvidence"]))
        req={k:v for k,v in request.items() if k!="operation"}|dict(authority=self.authority(preview["scopeSha256"],evidence))
        receipt=cli("cancel",req)
        self.assertEqual(receipt["document"]["deliveries"][0]["status"],"cancelled")
        status=cli("status")
        self.assertEqual(status["document"]["deliveries"],[])
        self.assertEqual(status["nextStep"],[dict(operation="refine")])


class NativeOwnerDispositionTests(unittest.TestCase):
    setUp = OwnerDispositionTests.setUp
    artifact = OwnerDispositionTests.artifact
    mutate = OwnerDispositionTests.mutate
    authority = OwnerDispositionTests.authority
    disposition_request = OwnerDispositionTests.disposition_request
    decision = OwnerDispositionTests.decision
    replacement = OwnerDispositionTests.replacement
    assert_history = OwnerDispositionTests.assert_history
    native_plan = native.NativeRuntimeTests.native_plan
    activate = native.NativeRuntimeTests.activate
    start = native.NativeRuntimeTests.start
    finish = native.NativeRuntimeTests.finish

    def test_native_running_worker_blocks_disposition_even_after_source_drift(self):
        self.native_plan();self.start()
        (self.repo/"app.py").write_text("# worker edited the source\n")
        self.mutate("block",dict(deliveryId="DI-1",reason="Paused while worker exists"))
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,"running activities"):
            disposition_context(self.repo,self.disposition_request())
        self.assertEqual(before,(self.repo/FILE).read_bytes())

    def test_native_attempts_campaign_and_failure_history_survive_replacement(self):
        self.native_plan(budget=1);self.start();self.finish()
        self.mutate("block",dict(deliveryId="DI-1",reason="Owner changed direction after failed play assessment"))
        replacement=self.replacement()
        campaign=copy.deepcopy(campaign_for(self.document,"INT-ACCESS"))
        original=copy.deepcopy(self.document["deliveries"][0])
        self.mutate("replace",self.decision(self.disposition_request("replace",replacement=replacement)))
        self.assertEqual(campaign_for(self.document,"INT-ACCESS"),campaign)
        self.assert_history(original,self.document["deliveries"][0])
        self.assertEqual(len(self.document["deliveries"][0]["activityReceipts"]),1)
        self.assertEqual(self.document["deliveries"][-1]["status"],"planned")

    def store_fixture(self, document):
        """Synthetic historical input, never a supported runtime mutation."""
        validate_document(document)
        (self.repo/FILE).write_text(json.dumps(document)+"\n")
        self.document,self.token=load(self.repo,check_evidence=False)

    def test_older_raw_running_worker_is_not_erased_by_a_newer_terminal_receipt(self):
        self.native_plan();self.start()
        document=copy.deepcopy(self.document)
        receipts=document["deliveries"][0]["activityReceipts"]
        receipts.append({**copy.deepcopy(receipts[0]),"attempt":2,"status":"failed","reason":"Newer attempt failed"})
        self.store_fixture(document)
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,"running activities"):
            disposition_context(self.repo,self.disposition_request())
        self.assertEqual(before,(self.repo/FILE).read_bytes())

    def test_retired_owner_priority_does_not_block_next_real_native_dispatch(self):
        from aim_quality.orchestration import construct_default_graph
        from aim_quality.orchestration_runtime import prepare_plan, pending_priority
        self.native_plan(budget=1);self.start();self.finish()
        document=copy.deepcopy(self.document)
        document["orchestration"]["ownerPriority"]=["INT-ACCESS"]
        self.store_fixture(document)
        campaign=copy.deepcopy(campaign_for(self.document,"INT-ACCESS"))
        self.assertEqual(pending_priority(self.document,lambda ref:None),[])
        self.mutate("cancel",self.decision(self.disposition_request()))
        record=self.document["deliveries"][0]["disposition"]["context"]
        self.assertEqual(record["ownerPriorityBefore"],["INT-ACCESS"])
        self.assertEqual(record["ownerPriorityAfter"],[])
        self.assertEqual(pending_priority(self.document,lambda ref:None),[])
        self.assertEqual(campaign_for(self.document,"INT-ACCESS"),campaign)
        ac=[dict(id="AC-NEW",text="The newly requested outcome works.")]
        self.mutate("import",dict(intents=[dict(id="INT-NEW",statement="A new owner outcome")],
            epics=[dict(id="EPIC-NEW",intentId="INT-NEW",title="Current direction",outcome="New useful result",acceptanceCriteria=ac)],
            stories=[dict(id="US-NEW",epicId="EPIC-NEW",title="New story",persona="Owner",need="Current request",benefit="Useful new result",priority=1,status="ready",acceptanceCriteria=ac)]))
        graph=construct_default_graph("cohesive_delivery",
            [dict(id="INT-NEW",requirement="A new owner outcome",paths=["app.py"])],
            dict(session="native-coordinator",capability=dict(id="aim-native-orchestrator",version="4.8.0"),
                 permittedDecisions=["continue_bounded","change_baseline","request_owner_choice","independent_work","reprioritize"]),
            dict(delegationAllowed=False,maxWorkers=1,checkpointAttemptBudget=1))
        quality=copy.deepcopy(self.document["deliveries"][0]["qualityPlan"])
        quality["checks"][0]["criteria"]=["US-NEW/AC-NEW"]
        quality["sharedRequirements"][0]["source"]="INT-NEW"
        self.mutate("plan",dict(id="DI-2",title="Next actual delivery",goal="A new owner outcome",storyIds=["US-NEW"],
            planEvidence=[self.plan_evidence],qualityPlan=quality,executionPlan=prepare_plan(graph,{"US-NEW":["INT-NEW"]})))
        self.mutate("approve",dict(deliveryId="DI-2",authority=self.authority(self.document["deliveries"][-1]["scopeSha256"])))
        self.activate(delivery="DI-2")
        self.start(delivery="DI-2",key="implement-new-outcome")
        self.assertEqual(self.document["deliveries"][-1]["activityReceipts"][-1]["status"],"running")
        self.assertEqual(campaign_for(self.document,"INT-ACCESS"),campaign)


if __name__ == "__main__":
    unittest.main()
