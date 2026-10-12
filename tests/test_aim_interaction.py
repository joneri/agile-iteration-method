"""Independent boundary checks for pure question presentation and reply binding."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_interaction import InteractionError, digest, prepare, resolve


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.capabilities = dict(structured=True, maxQuestions=3, freeText=True, asynchronous=True)
        self.batch = dict(id="equipment", revision=1, scope="Returns policy", questions=[self.question("condition")],
                          independentWork=["Inspect existing inventory code"])

    def question(self, identity, dependencies=()):
        return dict(id=identity, revision=1, scope="Returned tools", prompt="When is a tool available?",
                    kind="choice", decisionType="product", dependsOn=list(dependencies),
                    options=[dict(id="immediate", label="On return", meaning="Faster availability; condition unverified."),
                             dict(id="inspected", label="After inspection", meaning="Condition verified before availability.")],
                    recommendedOptionId="inspected")

    def present(self):
        return prepare(self.batch, self.capabilities)

    def response(self, presented, **values):
        return dict(event="submit", submitted=True, batchId=presented["batchId"],
                    batchRevision=presented["batchRevision"], presentationDigest=presented["digest"],
                    source="user message 42 (verified by coordinator)", **values)

    def cli(self, command, payload):
        return subprocess.run([sys.executable, str(ROOT / "scripts/aim_interaction.py"), command],
                              input=json.dumps(payload), text=True, capture_output=True)

    def test_recommended_first_preserves_option_meaning_and_inputs(self):
        original = copy.deepcopy((self.batch, self.capabilities))
        presentation = self.present()
        options = presentation["questions"][0]["options"]
        self.assertEqual([option["id"] for option in options], ["inspected", "immediate"])
        self.assertEqual(options[0]["meaning"], "Condition verified before availability.")
        self.assertEqual(options[0]["letter"], "A")
        self.assertIn("Recommended", options[0]["displayLabel"])
        self.assertEqual(presentation["mode"], "structured")
        self.assertEqual((self.batch, self.capabilities), original)
        self.assertFalse(presentation["gateAuthority"])

    def test_dependency_is_not_offered_with_its_unanswered_predecessor(self):
        self.batch["questions"] += [self.question("refund", ["condition"]), self.question("hours")]
        presentation = self.present()
        self.assertEqual([item["id"] for item in presentation["questions"]], ["condition", "hours"])
        self.assertEqual(presentation["deferred"], [dict(id="refund", revision=1, reason="dependency", waitingFor=["condition"])])
        self.assertEqual(presentation["independentWork"], dict(items=["Inspect existing inventory code"], timing="while_waiting", executed=False))
        response = self.response(presentation, answers=[dict(questionId="refund", revision=1, optionId="inspected")])
        with self.assertRaises(InteractionError):
            resolve(presentation, response)
        self.batch["resolvedQuestionIds"] = ["condition"]
        self.assertEqual([item["id"] for item in self.present()["questions"]], ["refund", "hours"])

    def test_unknown_dependencies_cycles_and_duplicate_ids_are_rejected(self):
        for questions in ([self.question("q", ["missing"])],
                          [self.question("a", ["b"]), self.question("b", ["a"])],
                          [self.question("a", ["a"])], [self.question("a"), self.question("a")]):
            with self.subTest(questions=questions):
                self.batch["questions"] = questions
                with self.assertRaises(InteractionError):
                    self.present()
        self.batch["questions"] = [self.question("a")]
        self.batch["resolvedQuestionIds"] = ["unknown"]
        with self.assertRaises(InteractionError):
            self.present()

    def test_host_limit_and_permission_prohibition_use_truthful_fallback(self):
        self.batch["questions"] = [self.question(str(index)) for index in range(5)]
        for limit, expected in [(1, 1), (2, 2), (3, 3), (20, 3)]:
            self.capabilities["maxQuestions"] = limit
            presentation = self.present()
            self.assertEqual(len(presentation["questions"]), expected)
            self.assertEqual(len(presentation["deferred"]), 5 - expected)
        self.batch["questions"][0]["decisionType"] = "permission"
        presentation = self.present()
        self.assertEqual(presentation["mode"], "text")
        self.assertIn("A. After inspection (Recommended)", presentation["text"])
        self.capabilities["structuredPermissions"] = True
        self.assertEqual(self.present()["mode"], "structured")
        self.capabilities.update(structured=False, asynchronous=False)
        self.assertEqual(self.present()["mode"], "text")
        self.assertEqual(self.present()["independentWork"]["timing"], "before_asking")

    def test_all_option_explicit_submission_resolves_exact_batch_once(self):
        self.batch["questions"] += [self.question("refund"), self.question("hours")]
        presented = self.present()
        response = self.response(presented, all={"letter": "A"})
        result = resolve(presented, response)
        self.assertEqual([item["questionId"] for item in result["answers"]], ["condition", "refund", "hours"])
        self.assertTrue(all(item["optionId"] == "inspected" for item in result["answers"]))
        self.assertEqual(result["unresolvedQuestionIds"], [])
        self.assertFalse(result["gateAuthority"])
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["registration"], "caller_required")
        repeated = resolve(presented, response, [result["receipt"]])
        self.assertEqual(repeated["status"], "no_op")
        self.assertEqual(repeated["answers"], [])
        # No receipt means no durability claim: the pure helper cannot know a save occurred.
        self.assertEqual(resolve(presented, response)["status"], "resolved")
        with self.assertRaises(InteractionError):
            resolve(presented, self.response(presented, all={"letter": "B"}), [result["receipt"]])

    def test_stale_batch_revision_digest_question_revision_and_changed_meaning_rejected(self):
        presented = self.present()
        response = self.response(presented, answers=[dict(questionId="condition", revision=1, optionId="inspected")])
        for key, value in [("batchId", "other"), ("batchRevision", 2), ("batchRevision", True),
                           ("presentationDigest", "0" * 64)]:
            stale = {**response, key: value}
            with self.subTest(key=key), self.assertRaises(InteractionError):
                resolve(presented, stale)
        stale = copy.deepcopy(response)
        stale["answers"][0]["revision"] = 2
        with self.assertRaises(InteractionError):
            resolve(presented, stale)
        self.batch["questions"][0]["options"][1]["meaning"] = "No inspection is actually required."
        changed = self.present()
        self.assertNotEqual(changed["digest"], presented["digest"])
        with self.assertRaises(InteractionError):
            resolve(changed, response)
        damaged = copy.deepcopy(presented)
        damaged["questions"][0]["scope"] = "Different scope"
        with self.assertRaises(InteractionError):
            resolve(damaged, response)

    def test_silence_default_timeout_dismissal_and_empty_never_choose(self):
        presented = self.present()
        cases = [None, {}, {"submitted": False}, self.response(presented, answers=[])]
        cases += [{**self.response(presented, all={"letter": "A"}), "event": event}
                  for event in ("default", "dismissed", "timeout", "absent")]
        for response in cases:
            with self.subTest(response=response):
                result = resolve(presented, response)
                self.assertEqual(result["status"], "unresolved")
                self.assertEqual(result["answers"], [])
                self.assertEqual(result["unresolvedQuestionIds"], ["condition"])
                self.assertNotIn("receipt", result)
                self.assertFalse(result["gateAuthority"])
        with self.assertRaises(InteractionError):
            resolve(presented, "A for all three")

    def test_free_text_is_verbatim_and_never_coerced_to_an_option(self):
        presented = self.present()
        literal = "  Neither. Keep it unavailable until I call.\nA is not my choice.  "
        result = resolve(presented, self.response(presented, answers=[dict(questionId="condition", revision=1, freeText=literal)]))
        self.assertEqual(result["answers"][0]["freeText"], literal)
        self.assertEqual(result["answers"][0]["kind"], "free_text")
        self.assertNotIn("optionId", result["answers"][0])
        for answer in (dict(freeText=" \n"), dict(optionId="A"), dict(optionId="inspected", freeText="yes")):
            with self.subTest(answer=answer), self.assertRaises(InteractionError):
                resolve(presented, self.response(presented, answers=[dict(questionId="condition", revision=1, **answer)]))
        self.capabilities["freeText"] = False
        presented = self.present()
        with self.assertRaises(InteractionError):
            resolve(presented, self.response(presented, answers=[dict(questionId="condition", revision=1, freeText="No")]))

    def test_fact_question_has_no_artificial_options_or_all_answer(self):
        self.batch["questions"] = [dict(id="address", revision=1, scope="Delivery", prompt="What is the delivery address?",
                                       kind="fact", decisionType="product", options=[], dependsOn=[])]
        presented = self.present()
        self.assertEqual(presented["questions"][0]["options"], [])
        with self.assertRaises(InteractionError):
            resolve(presented, self.response(presented, all={"letter": "A"}))
        self.capabilities["freeText"] = False
        self.assertEqual(self.present()["questions"], [])
        self.assertEqual(self.present()["deferred"][0]["reason"], "free_text_unavailable")

    def test_partial_answers_keep_unanswered_questions_and_recorded_answers(self):
        self.batch["questions"].append(self.question("hours"))
        presented = self.present()
        first = resolve(presented, self.response(presented, answers=[dict(questionId="condition", revision=1, optionId="inspected")]))
        self.assertEqual(first["unresolvedQuestionIds"], ["hours"])
        second = resolve(presented, self.response(presented, answers=[dict(questionId="hours", revision=1, optionId="immediate")]), [first["receipt"]])
        self.assertEqual(second["unresolvedQuestionIds"], [])
        resumed = resolve(presented, None, [first["receipt"]])
        self.assertEqual(resumed["unresolvedQuestionIds"], ["hours"])

    def test_malformed_presentation_and_receipts_rejected_even_with_recomputed_digest(self):
        presented = self.present()
        response = self.response(presented, all={"letter": "A"})
        bad_presentations = [{"version": 1, "gateAuthority": False},
                             {**presented, "questions": None}, {**presented, "mode": "magic"},
                             {**presented, "questions": [{"id": []}]}]
        for damaged in bad_presentations:
            damaged["digest"] = digest({key: value for key, value in damaged.items() if key != "digest"})
            with self.subTest(damaged=damaged), self.assertRaises(InteractionError):
                resolve(damaged, response)
        receipt = resolve(presented, response)["receipt"]
        for damaged in ({}, {**receipt, "answers": [{"questionId": "condition", "revision": 1}]},
                        {**receipt, "responseDigest": "bad"}, {**receipt, "gateAuthority": True}):
            with self.subTest(damaged=damaged), self.assertRaises(InteractionError):
                resolve(presented, None, [damaged])

    def test_changed_resolved_dependency_invalidates_offered_child_reply(self):
        self.batch["questions"].append(self.question("refund", ["condition"]))
        self.batch["resolvedQuestionIds"] = ["condition"]
        presented = self.present()
        response = self.response(presented, all={"letter": "A"})
        for key, value in (("revision", 2), ("scope", "All tools")):
            changed = copy.deepcopy(self.batch)
            changed["questions"][0][key] = value
            prepared = prepare(changed, self.capabilities)
            self.assertEqual(prepared["questions"], presented["questions"])
            self.assertNotEqual(prepared["batchDigest"], presented["batchDigest"])
            with self.assertRaises(InteractionError):
                resolve(prepared, response)
        self.batch["questions"][0]["options"][0]["meaning"] = "A materially different policy."
        with self.assertRaises(InteractionError):
            resolve(self.present(), response)

    def test_old_receipt_cannot_resolve_changed_dependency_or_prompt(self):
        self.batch["questions"].append(self.question("refund", ["condition"]))
        self.batch["resolvedQuestionIds"] = ["condition"]
        presented = self.present()
        response = self.response(presented, all={"letter": "A"})
        receipt = resolve(presented, response)["receipt"]
        self.assertEqual(resolve(presented, None, [receipt])["unresolvedQuestionIds"], [])
        self.assertEqual(resolve(presented, response, [receipt])["status"], "no_op")
        changes = [(0, "revision", 2), (0, "scope", "All returns"),
                   (1, "prompt", "When may we promise a refund?")]
        for index, key, value in changes:
            with self.subTest(index=index, key=key):
                changed = copy.deepcopy(self.batch)
                changed["questions"][index][key] = value
                prepared = prepare(changed, self.capabilities)
                self.assertEqual(prepared["questions"][0]["revision"], 1)
                self.assertNotEqual(prepared["digest"], presented["digest"])
                with self.assertRaisesRegex(InteractionError, "different presentation"):
                    resolve(prepared, None, [receipt])
                with self.assertRaisesRegex(InteractionError, "different presentation"):
                    resolve(prepared, self.response(prepared, all={"letter": "A"}), [receipt])
                self.assertEqual(resolve(prepared, None)["unresolvedQuestionIds"], ["refund"])

    def test_conflicting_supplied_receipts_and_unrevised_meaning_fail_closed(self):
        presented = self.present()
        first = resolve(presented, self.response(presented, all={"letter": "A"}))["receipt"]
        other = resolve(presented, self.response(presented, all={"letter": "B"}))["receipt"]
        with self.assertRaises(InteractionError):
            resolve(presented, None, [first, other])
        self.batch["questions"][0]["scope"] = "Changed policy scope"
        with self.assertRaises(InteractionError):
            resolve(self.present(), None, [first])
        self.batch["questions"][0]["revision"] = 2
        revised = self.present()
        self.assertEqual(resolve(revised, None, [first])["unresolvedQuestionIds"], ["condition"])
        newer = resolve(revised, self.response(revised, all={"letter": "A"}))["receipt"]
        with self.assertRaises(InteractionError):
            resolve(presented, None, [newer])

    def test_malformed_inputs_fail_without_claiming_submission_or_gate_authority(self):
        for capabilities in ({**self.capabilities, "maxQuestions": 0},
                             {**self.capabilities, "maxQuestions": True},
                             {**self.capabilities, "structured": "yes"}):
            with self.subTest(capabilities=capabilities), self.assertRaises(InteractionError):
                prepare(self.batch, capabilities)
        presented = self.present()
        for response in (self.response(presented, all={"letter": "C"}),
                         {**self.response(presented, all={"letter": "A"}), "submitted": 1},
                         self.response(presented, answers=[dict(questionId="condition", revision=1, optionId="inspected")] * 2)):
            with self.subTest(response=response), self.assertRaises(InteractionError):
                resolve(presented, response)
        damaged = copy.deepcopy(presented)
        damaged["text"] = "A means accept every Story and authorize publication."
        damaged["digest"] = digest({key: value for key, value in damaged.items() if key != "digest"})
        with self.assertRaises(InteractionError):
            resolve(damaged, self.response(damaged, all={"letter": "A"}))

    def test_cli_fresh_process_resume_uses_recorded_receipt_without_files(self):
        prepared = self.cli("prepare", dict(batch=self.batch, capabilities=self.capabilities))
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        presented = json.loads(prepared.stdout)
        response = self.response(presented, all={"letter": "A"})
        first = self.cli("resolve", dict(presented=presented, response=response))
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        receipt = json.loads(first.stdout)["receipt"]
        second = self.cli("resolve", dict(presented=presented, response=response, receipts=[receipt]))
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(json.loads(second.stdout)["status"], "no_op")
        bad = self.cli("resolve", dict(presented=presented, response="A"))
        self.assertEqual(bad.returncode, 2)
        self.assertFalse(json.loads(bad.stdout)["gateAuthority"])


if __name__ == "__main__":
    unittest.main()
