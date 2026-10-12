#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_interaction.py
"""Pure presentation and reply binding; no decision engine, persistence or gates.

The coordinator supplies validated current questions, resolved dependency IDs and
host capabilities. It must keep one active presentation per unresolved revision,
reconcile prior evidence before presenting again, verify the response's source,
and atomically register a returned receipt in existing evidence before dependent
work. Supplied receipts are evidence inputs, not authenticated records. A digest
binds bytes; it does not authenticate a human, establish currentness independently
of the caller, grant authority, or prove that registration has happened.

CLI: `aim_interaction.py prepare|resolve`, one JSON object on stdin. Prepare takes
{batch, capabilities}; resolve takes {presented, response, receipts}. CLI and Python
API never write files. A fresh process can reconcile a caller-recorded receipt.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys


class InteractionError(ValueError):
    """Invalid, stale, ambiguous or conflicting interaction data."""


def require(condition, message):
    if not condition:
        raise InteractionError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), "Expected an object.")
    require(set(required) <= value.keys(), "Missing fields: " + ", ".join(sorted(set(required) - value.keys())))
    require(value.keys() <= set(required) | set(optional), "Unexpected fields.")


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be non-empty text.")
    return value


def revision(value):
    require(type(value) is int and value > 0, "Revision must be a positive integer.")
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def strings(value, label):
    require(isinstance(value, list), f"{label} must be a list.")
    for item in value:
        text(item, label)
    require(len(set(value)) == len(value), f"Duplicate {label}.")
    return value


def prepare(batch, capabilities):
    """Return recommended-first controls; dependencies and host limits defer work.

    Caller-owned choices and option meanings are preserved. `structuredPermissions`
    is opt-in: permission questions otherwise use text, even on structured hosts.
    `independentWork` is an instruction to the caller, never executed by this helper.
    """
    fields(batch, ("id", "revision", "scope", "questions"), ("resolvedQuestionIds", "independentWork"))
    fields(capabilities, ("structured", "maxQuestions", "freeText", "asynchronous"),
           ("structuredPermissions",))
    for key in ("structured", "freeText", "asynchronous", "structuredPermissions"):
        require(type(capabilities.get(key, False)) is bool, f"{key} must be boolean.")
    maximum = capabilities["maxQuestions"]
    require(type(maximum) is int and maximum > 0, "maxQuestions must be a positive integer.")
    maximum = min(maximum, 3)
    text(batch["id"], "Batch ID")
    revision(batch["revision"])
    text(batch["scope"], "Batch scope")
    require(isinstance(batch["questions"], list), "Questions must be a list.")
    questions = {}
    for question in batch["questions"]:
        fields(question, ("id", "revision", "scope", "prompt", "kind", "decisionType", "dependsOn", "options"),
               ("recommendedOptionId",))
        for key in ("id", "scope", "prompt"):
            text(question[key], key)
        revision(question["revision"])
        require(question["id"] not in questions, "Duplicate question ID.")
        require(question["kind"] in ("choice", "fact"), "Unknown question kind.")
        require(question["decisionType"] in ("product", "permission"), "Unknown decision type.")
        strings(question["dependsOn"], "dependencies")
        require(isinstance(question["options"], list), "Options must be a list.")
        ids = []
        for option in question["options"]:
            fields(option, ("id", "label", "meaning"))
            for key in ("id", "label", "meaning"):
                text(option[key], key)
            ids.append(option["id"])
        require(len(set(ids)) == len(ids), "Duplicate option ID.")
        if question["kind"] == "choice":
            require(2 <= len(ids) <= 3, "Choice questions need two or three options.")
            require(question.get("recommendedOptionId") in ids, "Recommendation must name an option.")
        else:
            require(not ids and "recommendedOptionId" not in question, "Fact questions must not invent options.")
        questions[question["id"]] = copy.deepcopy(question)
    resolved = strings(batch.get("resolvedQuestionIds", []), "resolved question IDs")
    require(set(resolved) <= questions.keys(), "Unknown resolved question ID.")
    for question in questions.values():
        require(set(question["dependsOn"]) <= questions.keys(), "Unknown dependency.")
    visiting, visited = set(), set()

    def visit(question_id):
        require(question_id not in visiting, "Cyclic question dependencies.")
        if question_id in visited:
            return
        visiting.add(question_id)
        for dependency in questions[question_id]["dependsOn"]:
            visit(dependency)
        visiting.remove(question_id)
        visited.add(question_id)

    for question_id in questions:
        visit(question_id)
    offered, deferred = [], []
    for question in questions.values():
        if question["id"] in resolved:
            continue
        pending = [item for item in question["dependsOn"] if item not in resolved]
        reason = ("dependency" if pending else "free_text_unavailable"
                  if question["kind"] == "fact" and not capabilities["freeText"] else
                  "batch_limit" if len(offered) >= maximum else None)
        if reason:
            deferred.append({"id": question["id"], "revision": question["revision"],
                             "reason": reason, "waitingFor": pending})
            continue
        options = sorted(question["options"], key=lambda item: item["id"] != question.get("recommendedOptionId"))
        question["options"] = [{**item, "letter": chr(65 + index), "recommended": index == 0,
                                "displayLabel": item["label"] + (" (Recommended)" if index == 0 else "")}
                               for index, item in enumerate(options)]
        question["freeText"] = capabilities["freeText"]
        offered.append(question)
    structured = capabilities["structured"] and all(
        question["decisionType"] != "permission" or capabilities.get("structuredPermissions", False)
        for question in offered)
    work = strings(batch.get("independentWork", []), "independent work")
    result = {"version": 1, "batchId": batch["id"], "batchRevision": batch["revision"],
              "batchDigest": digest(batch), "scope": batch["scope"], "mode": "structured" if structured else "text",
              "questions": offered, "deferred": deferred, "resolvedQuestionIds": list(resolved),
              "independentWork": {"items": list(work), "timing": "while_waiting" if capabilities["asynchronous"] else "before_asking",
                                  "executed": False}, "gateAuthority": False}
    result["text"] = presentation_text(result)
    result["digest"] = digest(result)
    return result


def presentation_text(presented):
    lines = [f"Batch {presented['batchId']} · revision {presented['batchRevision']}", presented["scope"]]
    for question in presented["questions"]:
        lines.append(f"{question['id']} · revision {question['revision']} · {question['scope']}: {question['prompt']}")
        lines.extend(f"{item['letter']}. {item['displayLabel']} — {item['meaning']}" for item in question["options"])
        if question["freeText"]:
            lines.append("An explicit free-text answer is also supported.")
    return "\n".join(lines)


def fingerprint(value):
    require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
            "Invalid SHA-256 fingerprint.")


def validate_presentation(presented):
    fields(presented, ("version", "batchId", "batchRevision", "batchDigest", "scope", "mode", "questions",
                       "deferred", "resolvedQuestionIds", "independentWork", "gateAuthority", "text", "digest"))
    require(type(presented["version"]) is int and presented["version"] == 1 and presented["gateAuthority"] is False,
            "Unsupported presentation.")
    for key in ("batchId", "scope", "text"):
        text(presented[key], key)
    revision(presented["batchRevision"])
    fingerprint(presented["batchDigest"])
    fingerprint(presented["digest"])
    require(presented["mode"] in ("text", "structured"), "Unknown presentation mode.")
    require(isinstance(presented["questions"], list) and len(presented["questions"]) <= 3, "Invalid presented questions.")
    ids = []
    for question in presented["questions"]:
        fields(question, ("id", "revision", "scope", "prompt", "kind", "decisionType", "dependsOn", "options", "freeText"),
               ("recommendedOptionId",))
        for key in ("id", "scope", "prompt"):
            text(question[key], key)
        revision(question["revision"])
        ids.append(question["id"])
        strings(question["dependsOn"], "dependencies")
        require(question["kind"] in ("choice", "fact") and question["decisionType"] in ("product", "permission")
                and type(question["freeText"]) is bool, "Invalid question controls.")
        require(isinstance(question["options"], list), "Invalid presented options.")
        option_ids = []
        for index, option in enumerate(question["options"]):
            fields(option, ("id", "label", "meaning", "letter", "recommended", "displayLabel"))
            for key in ("id", "label", "meaning"):
                text(option[key], key)
            require(option["letter"] == chr(65 + index) and option["recommended"] is (index == 0)
                    and option["displayLabel"] == option["label"] + (" (Recommended)" if index == 0 else ""),
                    "Invalid option presentation.")
            option_ids.append(option["id"])
        require(len(set(option_ids)) == len(option_ids), "Duplicate option ID.")
        if question["kind"] == "choice":
            require(2 <= len(option_ids) <= 3 and question.get("recommendedOptionId") == option_ids[0], "Invalid recommendation.")
        else:
            require(not option_ids and "recommendedOptionId" not in question and question["freeText"], "Invalid fact controls.")
    strings(ids, "presented question IDs")
    resolved = strings(presented["resolvedQuestionIds"], "resolved question IDs")
    require(not set(ids) & set(resolved), "Resolved question was presented again.")
    for question in presented["questions"]:
        require(set(question["dependsOn"]) <= set(resolved), "Unresolved dependency was presented.")
    require(isinstance(presented["deferred"], list), "Invalid deferred questions.")
    deferred_ids = []
    for question in presented["deferred"]:
        fields(question, ("id", "revision", "reason", "waitingFor"))
        text(question["id"], "Deferred ID")
        revision(question["revision"])
        require(question["reason"] in ("dependency", "free_text_unavailable", "batch_limit"), "Unknown defer reason.")
        strings(question["waitingFor"], "pending dependencies")
        require(bool(question["waitingFor"]) == (question["reason"] == "dependency"), "Invalid defer reason.")
        deferred_ids.append(question["id"])
    strings(ids + deferred_ids + resolved, "presentation question IDs")
    for question in presented["deferred"]:
        require(set(question["waitingFor"]) <= set(ids + deferred_ids), "Unknown pending dependency.")
    work = presented["independentWork"]
    fields(work, ("items", "timing", "executed"))
    strings(work["items"], "independent work")
    require(work["timing"] in ("while_waiting", "before_asking") and work["executed"] is False, "Invalid work instruction.")
    require(presented["text"] == presentation_text(presented), "Displayed text and question meanings disagree.")
    body = {key: value for key, value in presented.items() if key != "digest"}
    require(presented["digest"] == digest(body), "Presentation digest mismatch.")


def validate_receipts(receipts):
    require(isinstance(receipts, (list, tuple)), "Receipts must be a list.")
    for receipt in receipts:
        fields(receipt, ("version", "batchId", "batchRevision", "presentationDigest", "responseDigest", "answers", "source", "gateAuthority"))
        require(type(receipt["version"]) is int and receipt["version"] == 1 and receipt["gateAuthority"] is False, "Invalid supplied receipt.")
        text(receipt["batchId"], "Receipt batch ID")
        text(receipt["source"], "Receipt source")
        revision(receipt["batchRevision"])
        fingerprint(receipt["presentationDigest"])
        fingerprint(receipt["responseDigest"])
        require(isinstance(receipt["answers"], list) and bool(receipt["answers"]), "Invalid receipt answers.")
        ids = []
        for answer in receipt["answers"]:
            require(isinstance(answer, dict) and answer.get("kind") in ("option", "free_text"), "Invalid receipt answer kind.")
            keys = ("optionId", "label", "meaning") if answer["kind"] == "option" else ("freeText",)
            fields(answer, ("questionId", "revision", "scope", "kind") + keys)
            for key in ("questionId", "scope") + keys:
                text(answer[key], key)
            revision(answer["revision"])
            ids.append(answer["questionId"])
        strings(ids, "receipt question IDs")


def resolve(presented, response, receipts=()):
    """Bind an explicit submission or return unresolved/no_op without side effects.

    Use the sole active presentation, not one selected by the incoming response.
    Receipts must be reconciled by the coordinator against original evidence.
    A receipt can resolve a presented question only in its exact original batch
    presentation. Reusing an answer across changed presentations requires caller
    revalidation outside this helper, including changed prompts and dependencies.
    Changing a recorded answer requires a revised question; this helper does not
    implement supersession. No result is Gate B/E or authenticated human consent.
    """
    validate_presentation(presented)
    validate_receipts(receipts)
    questions = {item["id"]: item for item in presented["questions"]}
    prior_by_question = {}
    for receipt in receipts:
        for answer in receipt["answers"]:
            question = questions.get(answer["questionId"])
            if question is None:
                continue
            require(answer["revision"] <= question["revision"], "Presentation predates a supplied question receipt.")
            if answer["revision"] != question["revision"]:
                continue
            require(receipt["presentationDigest"] == presented["digest"]
                    and receipt["batchId"] == presented["batchId"]
                    and receipt["batchRevision"] == presented["batchRevision"],
                    "Receipt belongs to a different presentation; coordinator revalidation is required.")
            require(answer["scope"] == question["scope"], "Recorded scope changed without revision.")
            if answer["kind"] == "option":
                option = next((item for item in question["options"] if item["id"] == answer["optionId"]), None)
                require(option is not None and all(option[key] == answer[key] for key in ("label", "meaning")),
                        "Recorded option meaning changed without revision.")
            key = answer["questionId"]
            require(key not in prior_by_question or prior_by_question[key] == receipt, "Conflicting supplied receipts.")
            prior_by_question[key] = receipt
    previously_answered = set(prior_by_question)
    pending = [item for item in questions if item not in previously_answered]
    base = {"gateAuthority": False, "authenticated": False, "presentationDigest": presented["digest"]}
    if response is None:
        return {**base, "status": "unresolved", "answers": [], "unresolvedQuestionIds": pending}
    require(isinstance(response, dict), "Response must be a structured envelope; ambiguous text is not parsed.")
    require("submitted" not in response or type(response["submitted"]) is bool, "submitted must be boolean.")
    if response.get("event") in ("default", "dismissed", "timeout", "absent") or response.get("submitted") is not True:
        return {**base, "status": "unresolved", "answers": [], "unresolvedQuestionIds": pending}
    fields(response, ("event", "submitted", "batchId", "batchRevision", "presentationDigest", "source"),
           ("answers", "all"))
    require(response["event"] == "submit", "Explicit submission required.")
    require(response["batchId"] == presented["batchId"] and
            type(response["batchRevision"]) is int and response["batchRevision"] == presented["batchRevision"] and
            response["presentationDigest"] == presented["digest"], "Stale or mismatched batch, revision or digest.")
    text(response["source"], "Response source (caller verified)")
    require(("answers" in response) != ("all" in response), "Supply answers or one explicit all-option selection.")
    if "all" in response:
        fields(response["all"], ("letter",))
        letter = response["all"]["letter"]
        require(letter in ("A", "B", "C") and bool(questions), "Unknown or empty all-option selection.")
        answers = []
        for question in questions.values():
            option = next((item for item in question["options"] if item["letter"] == letter), None)
            require(option is not None, "All-option selection does not apply to every presented question.")
            answers.append({"questionId": question["id"], "revision": question["revision"], "optionId": option["id"]})
    else:
        answers = response["answers"]
        require(isinstance(answers, list), "Answers must be a list.")
    bound, seen = [], set()
    for answer in answers:
        fields(answer, ("questionId", "revision"), ("optionId", "freeText"))
        require(isinstance(answer["questionId"], str) and answer["questionId"] in questions, "Unknown or deferred question.")
        question = questions[answer["questionId"]]
        require(answer["questionId"] not in seen, "Duplicate question answer.")
        seen.add(answer["questionId"])
        require(type(answer["revision"]) is int and answer["revision"] == question["revision"], "Stale question revision.")
        require(("optionId" in answer) != ("freeText" in answer), "Answer must select an option or explicit free text.")
        value = {"questionId": question["id"], "revision": question["revision"], "scope": question["scope"]}
        if "optionId" in answer:
            option = next((item for item in question["options"] if item["id"] == answer["optionId"]), None)
            require(option is not None, "Unknown option ID.")
            value.update(kind="option", optionId=option["id"], label=option["label"], meaning=option["meaning"])
        else:
            require(question["freeText"], "Free text is unavailable for this presentation.")
            value.update(kind="free_text", freeText=text(answer["freeText"], "Free-text answer"))
        bound.append(value)
    if not bound:
        return {**base, "status": "unresolved", "answers": [], "unresolvedQuestionIds": pending}
    candidate = {"version": 1, "batchId": presented["batchId"], "batchRevision": presented["batchRevision"],
                 "presentationDigest": presented["digest"], "responseDigest": digest(response),
                 "answers": bound, "source": response["source"], "gateAuthority": False}
    replay = False
    for receipt in receipts:
        if receipt == candidate:
            replay = True
        for prior in receipt["answers"]:
            if prior["questionId"] in seen and prior.get("revision") == questions[prior["questionId"]]["revision"]:
                require(receipt == candidate, "Conflicting replay; revise and explicitly supersede the recorded question.")
    return {**base, "status": "no_op" if replay else "resolved", "answers": [] if replay else bound,
            "unresolvedQuestionIds": [item for item in questions if item not in seen | previously_answered],
            "receipt": copy.deepcopy(candidate), "registration": "caller_required" if not replay else "caller_supplied_receipt"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "resolve"))
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        if args.command == "prepare":
            fields(payload, ("batch", "capabilities"))
            result = prepare(**payload)
        else:
            fields(payload, ("presented", "response"), ("receipts",))
            result = resolve(**payload)
    except (InteractionError, ValueError, TypeError, KeyError, RecursionError) as exc:
        json.dump({"error": str(exc), "gateAuthority": False}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
