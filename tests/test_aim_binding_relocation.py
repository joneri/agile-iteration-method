"""Real helper flows for identical historical inputs; all owner evidence is synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_aim_orchestration_runtime as native
import test_aim_stories as fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from aim_stories import FILE, digest, execute, load, project_story_board, validate_document
from aim_quality.graph import project_graph
from aim_quality.orchestration import construct_default_graph
from aim_quality.orchestration_runtime import (prepare_plan, campaign_for, assessment,
                                               pending_priority, _check_receipt_dependencies)


class BindingRelocationTests(unittest.TestCase):
    setUp = fixture.StoryDeliveryTests.setUp
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    authority = fixture.StoryDeliveryTests.authority
    activate = native.NativeRuntimeTests.activate
    start = native.NativeRuntimeTests.start
    finish = native.NativeRuntimeTests.finish

    def plan(self, budget=5, native_graph=True):
        graph = construct_default_graph("maintenance_repair",
            [dict(id="INT-ACCESS",requirement=self.document["intents"][0]["statement"],paths=["app.py"])],
            dict(session="native-coordinator",capability=dict(id="aim-native-orchestrator",version="4.8.0"),
                 permittedDecisions=["continue_bounded","change_baseline","request_owner_choice","independent_work","reprioritize"]),
            dict(delegationAllowed=False,maxWorkers=1,checkpointAttemptBudget=budget))
        execution = prepare_plan(graph,{"US-BUYER":["INT-ACCESS"]})
        if not native_graph: execution.pop("orchestration")
        self.mutate("plan",dict(id="DI-1",title="Preserve reviewed historical inputs",goal="Complete the new product",
            storyIds=["US-BUYER"],planEvidence=[self.plan_evidence],executionPlan=execution))
        self.mutate("approve",dict(deliveryId="DI-1",authority=self.authority(self.document["deliveries"][0]["scopeSha256"])))
        if native_graph:self.activate()

    def prepared(self,budget=5,native_graph=True):
        self.plan(budget,native_graph)
        if native_graph:
            self.start(activity="diagnose",key="review-original-input")
        else:
            self.mutate("activity",dict(deliveryId="DI-1",activityId="diagnose",status="running",session="reader"))
        self.finish(activity="diagnose")
        self.original = copy.deepcopy(self.document["deliveries"][0]["activityReceipts"][0])
        self.snapshot=self.repo/".aim/baselines/app.py";self.snapshot.parent.mkdir(parents=True)
        self.snapshot.write_bytes((self.repo/"app.py").read_bytes())

    def relocation(self):
        old=self.original["sourceBindings"][0]
        return dict(deliveryId="DI-1",activityId="diagnose",attempt=1,receiptSha256=digest(self.original),
            mappings=[dict(**{"from":copy.deepcopy(old)},to=dict(path=".aim/baselines/app.py",sha256=old["sha256"]))],
            reason="Preserve the exact reviewed input before planned downstream changes.",
            evidence=[self.artifact("binding-proof.md","Synthetic independent check: saved original bytes equal the reviewed fingerprint.")],
            coordinatorSession="native-coordinator")

    def graph(self):return project_graph(self.repo,self.document,self.token)

    def reject(self,command,request,pattern):
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,pattern):self.mutate(command,request)
        self.assertEqual(before,(self.repo/FILE).read_bytes())

    def test_same_running_downstream_attempt_completes_at_exhausted_budget(self):
        self.prepared(budget=2)
        self.start(activity="repair",key="perform-approved-product-change")
        (self.repo/"app.py").write_text("# planned new product bytes\n")
        self.reject("activity",dict(deliveryId="DI-1",activityId="repair",status="completed",session="worker-a",attempt=1,
            sourcePaths=["app.py"],evidence=[self.evidence]),"prerequisites|inputs changed")
        before=copy.deepcopy(self.document);campaign=copy.deepcopy(campaign_for(before,"INT-ACCESS"))
        self.assertTrue(assessment(campaign)["budgetExhausted"])
        result=self.mutate("relocate-bindings",self.relocation())
        expected=copy.deepcopy(before);expected["revision"]=self.document["revision"];expected["updatedAt"]=self.document["updatedAt"]
        expected["deliveries"][0]["bindingRelocations"]=self.document["deliveries"][0]["bindingRelocations"]
        self.assertEqual(expected,self.document)
        self.assertFalse(result["idempotent"])
        read=result["executionGraph"]["activities"][0]
        self.assertEqual(read["status"],"completed")
        self.assertEqual(read["sourceBindings"][0]["path"],".aim/baselines/app.py")
        self.assertEqual(read["originalSourceBindings"],self.original["sourceBindings"])
        self.finish(activity="repair")
        delivery=self.document["deliveries"][0]
        self.assertEqual(delivery["activityReceipts"][0],self.original)
        self.assertEqual(delivery["activityReceipts"][-1]["attempt"],1)
        self.assertEqual(delivery["activityReceipts"][-1]["status"],"completed")
        self.assertEqual(campaign_for(self.document,"INT-ACCESS"),campaign)
        self.assertEqual(assessment(campaign)["attemptsUsed"],2)
        def check(ref):
            if hashlib.sha256((self.repo/ref["path"]).read_bytes()).hexdigest()!=ref["sha256"]:
                raise ValueError("Actual current reference is stale")
        self.assertEqual(pending_priority({**self.document,"orchestration":{**self.document["orchestration"],"ownerPriority":["INT-ACCESS"]}},check),[])
        # Native observation dependency checking resolves the identical input;
        # it still fingerprints the unmodified original dependency receipt.
        _check_receipt_dependencies(delivery,delivery["activityReceipts"][-1],check)
        self.reject("activity",dict(deliveryId="DI-1",activityId="diagnose",status="running",session="another-reader",
            coordinatorSession="native-coordinator",actionKey="extra-work-without-renewal"),"request_owner_choice")

    def test_identical_retry_has_no_revision_timestamp_or_extra_history(self):
        self.prepared();request=self.relocation();self.mutate("relocate-bindings",request)
        before=(self.repo/FILE).read_bytes();result=self.mutate("relocate-bindings",request)
        self.assertTrue(result["idempotent"]);self.assertEqual(before,(self.repo/FILE).read_bytes())
        self.assertEqual(len(self.document["deliveries"][0]["bindingRelocations"]),1)

    def test_wrong_destination_hash_content_receipt_or_coordinator_rejects(self):
        self.prepared();request=self.relocation()
        for mutation in ("sha","content","receipt","session","attempt","original"):
            with self.subTest(mutation=mutation):
                r=copy.deepcopy(request)
                if mutation=="sha":r["mappings"][0]["to"]["sha256"]="0"*64
                if mutation=="content":self.snapshot.write_text("Different bytes")
                if mutation=="receipt":r["receiptSha256"]="0"*64
                if mutation=="session":r["coordinatorSession"]="unactivated"
                if mutation=="attempt":r["attempt"]=2
                if mutation=="original":r["mappings"][0]["from"]["path"]="other.py"
                self.reject("relocate-bindings",r,"fingerprint|Evidence changed|completed read|activated|current binding")
                self.snapshot.write_bytes((self.repo/"app.py").read_bytes())

    def test_unsafe_missing_directory_and_symlink_destinations_reject(self):
        self.prepared();request=self.relocation()
        (self.repo/"linked.py").symlink_to(self.snapshot)
        for path in ("../outside.py",str(self.snapshot),"missing.py",".aim/baselines","linked.py"):
            with self.subTest(path=path):
                r=copy.deepcopy(request);r["mappings"][0]["to"]["path"]=path
                self.reject("relocate-bindings",r,"path|read|regular|symbolic|symlink|directory")

    def test_duplicate_or_unknown_mappings_reject_atomically(self):
        self.prepared();request=self.relocation();request["mappings"]*=2
        self.reject("relocate-bindings",request,"Duplicate")
        r=self.relocation();extra=copy.deepcopy(r["mappings"][0]);extra["from"]["path"]="unknown.py";r["mappings"].append(extra)
        self.reject("relocate-bindings",r,"current binding")

    def test_current_cas_and_fresh_actual_read_proof_are_required(self):
        self.prepared();request=self.relocation();old_token=self.token
        self.mutate("block",dict(deliveryId="DI-1",reason="Unrelated pause retained"))
        before=(self.repo/FILE).read_bytes()
        with self.assertRaisesRegex(ValueError,"Stale product backlog"):execute(self.repo,"relocate-bindings",request,old_token)
        self.assertEqual(before,(self.repo/FILE).read_bytes())
        proof=self.repo/self.original["evidence"][0]["path"];proof.write_text("Changed original actual review")
        self.reject("relocate-bindings",request,"Evidence changed")

    def test_relocation_retains_block_and_does_not_complete_running_target(self):
        self.prepared();self.mutate("block",dict(deliveryId="DI-1",reason="Preserve actual block"))
        self.mutate("relocate-bindings",self.relocation());d=self.document["deliveries"][0]
        self.assertEqual((d["status"],d["blockedFrom"],d["reason"]),("blocked","in_progress","Preserve actual block"))
        self.mutate("unblock",dict(deliveryId="DI-1",reason="Existing blocker resolved"))
        self.start(activity="repair",key="new-product-work")
        r=self.relocation();receipt=self.document["deliveries"][0]["activityReceipts"][-1]
        r.update(activityId="repair",attempt=1,receiptSha256=digest(receipt))
        self.reject("relocate-bindings",r,"never write outputs")

    def test_changed_saved_baseline_becomes_stale_again(self):
        self.prepared();self.mutate("relocate-bindings",self.relocation())
        self.snapshot.write_text("Baseline corrupted later")
        self.assertEqual(self.graph()["activities"][0]["status"],"stale")
        self.reject("activity",dict(deliveryId="DI-1",activityId="repair",status="running",session="worker-a",
            coordinatorSession="native-coordinator",actionKey="must-not-use-corrupt-baseline"),"prerequisites")
        self.assertFalse(project_story_board(self.repo)["valid"])

    def test_chained_move_does_not_require_deleted_obsolete_location(self):
        self.prepared();first=self.relocation();self.mutate("relocate-bindings",first)
        second=self.repo/".aim/baselines/second.py";second.write_bytes(self.snapshot.read_bytes())
        request=copy.deepcopy(first);request["mappings"][0]={"from":first["mappings"][0]["to"],"to":dict(path=".aim/baselines/second.py",sha256=first["mappings"][0]["to"]["sha256"])}
        self.mutate("relocate-bindings",request);self.snapshot.unlink()
        load(self.repo)
        self.assertEqual(self.graph()["activities"][0]["status"],"completed")
        before=(self.repo/FILE).read_bytes()
        original=copy.deepcopy(self.original)
        result=self.mutate("relocate-bindings",first)
        self.assertTrue(result["idempotent"])
        self.assertEqual(before,(self.repo/FILE).read_bytes())
        self.assertEqual(self.document["deliveries"][0]["activityReceipts"][0],original)
        for ref in (first["evidence"][0], original["evidence"][0]):
            proof=self.repo/ref["path"];saved=proof.read_bytes()
            proof.write_text("Changed actual proof")
            self.reject("relocate-bindings",first,"Evidence changed")
            proof.write_bytes(saved)
        second.write_text("Corrupted effective baseline")
        self.reject("relocate-bindings",first,"Evidence changed")
        second.unlink()
        self.reject("relocate-bindings",first,"Cannot safely read")

    def refresh_core(self):
        d=self.document["deliveries"][0];check=d["qualityPlan"]["checks"][0]
        bindings=[dict(path="app.py",sha256=hashlib.sha256((self.repo/"app.py").read_bytes()).hexdigest())]
        report=dict(qualityMeasurementVersion="1.0",measurements=[],qualityCheckVersion="1.0",checks=[dict(checkId=check["id"],
            **{k:check[k] for k in ("workload","environment","method")},observed={"recoverable":1,"explainable":1},productBindingsSha256=digest(bindings))])
        ref=self.artifact("fresh-core.json",json.dumps(report))
        self.mutate("measure",dict(deliveryId="DI-1",qualityMeasurements=[ref],bindings=bindings,response="Record the actual new current fixture source, not the old baseline."))

    def reviewed(self):
        self.prepared();self.start(activity="repair",key="approved-change")
        (self.repo/"app.py").write_text("# changed actual product\n")
        self.mutate("relocate-bindings",self.relocation());self.finish(activity="repair")
        self.start(activity="integrate-review",session="independent-reviewer",key="review-actual-current-product")
        self.finish(activity="integrate-review");self.refresh_core()
        self.mutate("review",dict(deliveryId="DI-1",sourcePaths=["app.py"]))

    def test_later_rework_keeps_history_but_cannot_reuse_old_generation_alias(self):
        self.reviewed();journal=copy.deepcopy(self.document["deliveries"][0]["bindingRelocations"])
        self.mutate("rework",dict(deliveryId="DI-1",reason="Actual later product correction"))
        self.assertEqual(self.document["deliveries"][0]["bindingRelocations"],journal)
        self.assertEqual(self.graph()["activities"][0]["status"],"stale")
        self.reject("relocate-bindings",self.relocation(),"earlier rework generation")
        self.start(activity="diagnose",session="reader-generation-one",key="new-original-input")
        self.finish(activity="diagnose")
        (self.repo/"app.py").write_text("# generation-one current source changed\n")
        self.assertEqual(self.graph()["activities"][0]["status"],"stale")
        self.assertNotIn("bindingRelocationIds",self.graph()["activities"][0])
        load(self.repo,check_evidence=False)

    def test_final_review_and_current_product_gates_are_not_relocated(self):
        self.reviewed()
        self.reject("relocate-bindings",self.relocation(),"approved implementation")
        self.mutate("rework",dict(deliveryId="DI-1",reason="Real rework retains separate current source checks"))
        r=self.relocation();review=next(x for x in self.document["deliveries"][0]["activityReceipts"] if x["activityId"]=="integrate-review")
        r.update(activityId="integrate-review",receiptSha256=digest(review))
        self.reject("relocate-bindings",r,"never write outputs or final review")

    def test_identical_historical_inputs_do_not_hide_a_later_live_product_change(self):
        self.reviewed()
        (self.repo/"app.py").write_text("# live delivered output changed after review\n")
        self.reject("validate",dict(deliveryId="DI-1",evidence=[self.evidence]),"Evidence changed|Recorded quality failure")

    def test_structural_tampering_with_original_receipt_or_journal_rejects(self):
        self.prepared();self.mutate("relocate-bindings",self.relocation())
        for field in ("receipt","scope","generation","mapping"):
            d=copy.deepcopy(self.document);delivery=d["deliveries"][0]
            if field=="receipt":delivery["activityReceipts"][0]["updatedAt"]="Changed history"
            if field=="scope":delivery["bindingRelocations"][0]["scopeSha256"]="0"*64
            if field=="generation":delivery["bindingRelocations"][0]["reworkRevision"]=1
            if field=="mapping":delivery["bindingRelocations"][0]["mappings"][0]["to"]["sha256"]="0"*64
            with self.subTest(field=field),self.assertRaises(ValueError):validate_document(d)

    def test_ordinary_non_native_graph_supports_same_administrative_operation(self):
        self.prepared(native_graph=False);self.mutate("relocate-bindings",self.relocation())
        self.assertEqual(self.graph()["activities"][0]["status"],"completed")
        self.assertNotIn("orchestration",self.document)

    def test_real_cli_and_compact_receipt_expose_audit_and_idempotence(self):
        self.prepared();request=self.relocation();root=Path(__file__).resolve().parents[1]
        args=[sys.executable,str(root/"scripts/aim_stories.py"),"--repo",str(self.repo),"relocate-bindings","--compact","--expected-sha256",self.token]
        p=subprocess.run(args,input=json.dumps(request),text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);r=json.loads(p.stdout)
        self.assertEqual(r["bindingRelocation"]["receiptSha256"],digest(self.original));self.assertFalse(r["idempotent"])
        args[-1]=r["storeSha256"];before=(self.repo/FILE).read_bytes()
        p=subprocess.run(args,input=json.dumps(request),text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)["idempotent"])
        self.assertEqual(before,(self.repo/FILE).read_bytes())

    def test_destination_change_during_verification_rejects_without_partial_journal(self):
        from unittest.mock import patch
        import aim_stories
        self.prepared();request=self.relocation();original=aim_stories._finish_verification
        def changed(repo,cache):
            self.snapshot.write_text("Changed while the operation was verifying")
            original(repo,cache)
        with patch.object(aim_stories,"_finish_verification",side_effect=changed):
            self.reject("relocate-bindings",request,"changed during verification")

    def test_accepted_and_cancelled_history_cannot_receive_new_relocations(self):
        self.reviewed()
        self.mutate("validate",dict(deliveryId="DI-1",evidence=[self.evidence]))
        core=self.document["deliveries"][0]["coreVerification"]["qualityMeasurements"]
        # The reviewed fixture snapshot is current and independently covered.
        self.mutate("measure",dict(deliveryId="DI-1",qualityMeasurements=core))
        self.mutate("acceptance",dict(deliveryId="DI-1",evidence=[self.evidence],
            criteria=[dict(storyId="US-BUYER",criterionId="AC-1",evidence=[self.evidence])]))
        self.mutate("accept",dict(deliveryId="DI-1",authority=self.authority(self.document["deliveries"][0]["acceptanceSha256"],self.acceptance)))
        self.reject("relocate-bindings",self.relocation(),"approved implementation")
        self.setUp();fixture.StoryDeliveryTests.plan(self)
        self.mutate("cancel",dict(deliveryId="DI-1",reason="Unapproved plan cancelled"))
        request=dict(deliveryId="DI-1",activityId="diagnose",attempt=1,receiptSha256="0"*64,
            mappings=[],reason="Must not mutate cancelled history",evidence=[self.evidence],coordinatorSession="native-coordinator")
        self.reject("relocate-bindings",request,"approved implementation")


if __name__ == "__main__":unittest.main()
