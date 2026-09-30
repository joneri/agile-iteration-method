#!/usr/bin/env python3
"""Shared, bounded proposals and single-commit approval registration for AIM."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

import aim_runtime_contract as runtime
from aim_quality.files import read_evidence
from aim_runtime_lock import runtime_lock

VERSION = "1.0"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
DECISIONS = {"approve_epic", "approve_increment", "accept_increment", "close_epic", "continue_epic", "split_scope"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _fail(message: str):
    raise runtime.RuntimeTransitionError(message)


def _base(state):
    return {key: value for key, value in state.items() if key != "decisionProposal"}


def _read(root, relative):
    if not isinstance(relative, str) or "\\" in relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        _fail("Expected a contained relative file path.")
    return read_evidence(root, relative)


def _json(root, relative):
    value = json.loads(_read(root, relative))
    if not isinstance(value, dict):
        _fail("Expected a JSON object.")
    return value


def _state(repo, authority):
    path = runtime._authority_state_path(repo, authority)
    _, state = runtime._read_runtime_state(path)
    issues = runtime._schema_issues(state, runtime._runtime_state_schema(repo))
    phases = {"gate_a_pending": ("PO", None), "gate_b_pending": ("TDO", "Gate A"),
              "increment_in_progress": ("Dev", "Gate B"), "review_in_progress": ("Reviewer", "Gate C"),
              "tdo_validation_in_progress": ("TDO", "Gate D"), "po_approval_pending": ("PO", "Gate D"),
              "done_increment_accepted": ("PO", "Gate E"), "epic_complete": ("PO", "Gate E")}
    expected = phases.get(state.get("epicStatus"))
    if expected and expected != (state.get("currentRole"), state.get("lastGatePassed")):
        issues.append("role/checkpoint contradicts the current phase")
    if state.get("epicStatus") in {"gate_a_pending", "done_increment_accepted", "epic_complete"}:
        if state.get("activeIncrementId") is not None:
            issues.append("this phase cannot have an active Increment")
    elif expected and not runtime.INCREMENT_ID_PATTERN.fullmatch(str(state.get("activeIncrementId", ""))):
        issues.append("this phase requires a canonical active Increment")
    if issues:
        _fail("Invalid runtime state: " + "; ".join(issues))
    return path, state


def _commit_state(path, state):
    payload = runtime._json_bytes(state)
    if len(payload) > runtime.MAX_RUNTIME_STATE_BYTES:
        _fail("Decision state exceeds the bounded runtime size limit.")
    runtime._atomic_replace(path, payload)
    _sync_directory(path.parent)


def _remaining_portfolio(repo, state):
    path = repo / ".aim/portfolio-run.json"
    if path.exists() or path.is_symlink():
        from aim_portfolio_run import load_run, remaining_epic_candidates
        run = load_run(repo)
        if run["status"] in {"running", "paused"} and isinstance(run.get("activeCandidateId"), str) and run["activeCandidateId"] == state.get("portfolioCandidateId"):
            if remaining_epic_candidates(run, run["activeCandidateId"]):
                _fail("The Portfolio mandate still requires another Increment in this Epic.")


def closure_readiness(repo: Path, authority: str, evidence_path: str):
    """Read-only technical readiness, with no fabricated decision authority."""
    path, state = _state(repo, authority)
    evidence = _json(path.parent, evidence_path)
    issues, evidence_hash = runtime.closure_content_issues(path.parent, state["epicId"], evidence, require_authority=False)
    _remaining_portfolio(repo, state)
    return {"ready": not issues, "issues": issues, "evidenceSetSha256": evidence_hash, "evidence": evidence}


def _offered(state, kind, recommendation):
    status = state["epicStatus"]
    if kind == "start" and status == "gate_a_pending" and state["lastGatePassed"] is None:
        return ["approve_epic", "approve_increment"]
    if kind == "plan" and status == "gate_b_pending" and state["lastGatePassed"] == "Gate A":
        return ["approve_increment"]
    if kind == "delivery" and status == "po_approval_pending" and state["lastGatePassed"] == "Gate D":
        base = ["accept_increment"]
    elif kind == "disposition" and status == "done_increment_accepted" and state["lastGatePassed"] == "Gate E":
        base = []
    else:
        _fail("Proposal kind does not match the current decision checkpoint.")
    action = {"close": "close_epic", "continue": "continue_epic", "split": "split_scope"}.get(recommendation)
    if not action:
        _fail("Delivery requires exactly one close, continue or split recommendation.")
    return base + [action]


def prepare(repo: Path, authority: str, spec: dict):
    """Build a reviewable proposal without writing runtime or decision files."""
    repo = repo.resolve()
    path, state = _state(repo, authority)
    for key in ("proposalId", "incrementId", "kind", "summary", "scope", "remainingWork", "risk"):
        if not isinstance(spec.get(key), str) or not spec[key].strip() or len(spec[key]) > 4000:
            _fail(f"Proposal requires bounded {key}.")
    if not ID.fullmatch(spec["proposalId"]):
        _fail("Invalid proposalId.")
    increment = spec["incrementId"]
    if not runtime.INCREMENT_ID_PATTERN.fullmatch(increment):
        _fail("Invalid Increment identity.")
    offered = _offered(state, spec["kind"], spec.get("recommendation"))
    expected = state.get("plannedIncrementId") if spec["kind"] == "start" else state.get("previousIncrementId") if spec["kind"] == "disposition" else state.get("activeIncrementId")
    if expected is not None and expected != increment:
        _fail("Proposal targets a different Increment.")
    plan, issues = runtime.terminal_increment_artifact(path.parent, state["epicId"], increment)
    if issues:
        _fail("; ".join(issues))
    if spec["kind"] == "disposition":
        _, issues = runtime.terminal_acceptance(repo, path.parent, state, increment)
        if issues:
            _fail("; ".join(issues))
    bindings = []
    for relative in [str((path.parent / "epic.md").relative_to(repo)), str(plan.relative_to(repo))] + spec.get("bindingPaths", []):
        payload = _read(repo, relative)
        bindings.append({"path": relative, "sha256": hashlib.sha256(payload).hexdigest()})
    epic_text = _read(repo, str((path.parent / "epic.md").relative_to(repo))).decode("utf-8")
    if (runtime.markdown_field(epic_text, "Outcome class") or "").lower() not in runtime.OUTCOME_CLASSES:
        _fail("Epic must declare Product, Pilot or POC before direction approval.")
    _, criterion_issues = runtime.epic_acceptance_criterion_ids(epic_text)
    if criterion_issues:
        _fail("; ".join(criterion_issues))
    proof = spec.get("evidence", [])
    if spec["kind"] in {"delivery", "disposition"}:
        issues, _ = runtime._evidence_reference_issues(path.parent, proof, "delivery")
        if issues:
            _fail("; ".join(issues))
        if not any(item["kind"] in runtime.CRITERION_EVIDENCE_KINDS for item in proof):
            _fail("Delivery needs verification evidence, not an authority record.")
        if not spec.get("bindingPaths"):
            _fail("Delivery must bind the relevant product code/configuration and input snapshots.")
    if "close_epic" in offered:
        ready = closure_readiness(repo, authority, spec.get("closureEvidence", ""))
        if not ready["ready"]:
            _fail("Epic is not ready: " + "; ".join(ready["issues"]))
    proposal = {
        "proposalVersion": VERSION, "authorityStatePath": authority,
        "epicId": state["epicId"], "sourceStateSha256": digest(_base(state)),
        "decisions": offered, "bindings": bindings,
        **{key: spec[key] for key in ("proposalId", "incrementId", "kind", "summary", "scope", "remainingWork", "risk")},
        "recommendation": spec.get("recommendation"), "evidence": proof,
    }
    if "close_epic" in offered:
        proposal["closureEvidence"] = spec["closureEvidence"]
        proposal["closureEvidenceSha256"] = hashlib.sha256(_read(path.parent, spec["closureEvidence"])).hexdigest()
    return proposal


def validate_proposal(repo: Path, authority: str, state: dict, proposal: dict):
    if not isinstance(proposal, dict) or proposal.get("proposalVersion") != VERSION:
        _fail("Unsupported decision proposal.")
    if proposal.get("authorityStatePath") != authority or proposal.get("epicId") != state["epicId"]:
        _fail("Proposal authority does not match.")
    if proposal.get("sourceStateSha256") != digest(_base(state)):
        _fail("Proposal state changed; re-evaluate the affected decision.")
    spec = {**proposal, "bindingPaths": [item["path"] for item in proposal.get("bindings", [])][2:]}
    fresh = prepare(repo, authority, spec)
    if digest(fresh) != digest(proposal):
        _fail("Proposal inputs or evidence changed; reverify before renewing the proposal.")


def publish(repo: Path, authority: str, proposal: dict):
    path, _ = _state(repo, authority)
    with runtime_lock(path):
        _, state = _state(repo, authority)
        validate_proposal(repo, authority, state, proposal)
        state["decisionProposal"] = proposal
        _commit_state(path, state)
    return {"result": "published", "proposalSha256": digest(proposal), "proposal": proposal}


def _sync_directory(path):
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _immutable(path: Path, payload: bytes):
    """Stage immutable receipts. State is the sole commit marker; retry is safe."""
    if path.parent.is_symlink() or not path.parent.is_dir():
        _fail("Unsafe or missing decisions directory.")
    if path.exists() or path.is_symlink():
        if path.is_symlink() or _read(path.parent, path.name) != payload:
            _fail("Existing operation artifacts differ; nothing may be overwritten.")
        return
    fd, name = tempfile.mkstemp(prefix=".decision-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        _sync_directory(path.parent)
    finally:
        os.unlink(name)


def apply(repo: Path, authority: str, response: dict):
    """Register the host-attributed actual user response, once, under one lock.

    The host owns authenticating user input; this tool never infers consent from
    repository text. Auto mandates retain their existing authorization path.
    """
    repo = repo.resolve()
    path, _ = _state(repo, authority)
    for key in ("operationId", "proposalSha256", "source", "text", "updatedAt"):
        if not isinstance(response.get(key), str) or not response[key].strip() or len(response[key]) > 8000:
            _fail(f"Actual response requires {key}.")
    if not ID.fullmatch(response["operationId"]):
        _fail("Invalid operationId.")
    selected = response.get("decisions")
    if not isinstance(selected, list) or not selected or any(not isinstance(x, str) for x in selected) or len(set(selected)) != len(selected) or not set(selected) <= DECISIONS:
        _fail("Response must explicitly select offered decisions.")
    request_hash = digest(response)
    name = "decision-" + response["operationId"]
    receipt_path = path.parent / "decisions" / (name + ".json")
    receipt_relative = receipt_path.relative_to(repo).as_posix()
    with runtime_lock(path):
        source_bytes, state = runtime._read_runtime_state(path)
        for reference in state.get("decisionReceipts", []):
            if reference["path"] == receipt_relative:
                payload = _read(repo, receipt_relative)
                if hashlib.sha256(payload).hexdigest() != reference["sha256"] or json.loads(payload)["requestSha256"] != request_hash:
                    _fail("Operation identity was reused with different content.")
                return {"result": "already_applied", "next": next_step(repo, authority)}
        proposal = state.get("decisionProposal")
        validate_proposal(repo, authority, state, proposal)
        if digest(proposal) != response["proposalSha256"] or not set(selected) <= set(proposal["decisions"]):
            _fail("Response does not match the current proposal and offered decisions.")
        if proposal["kind"] == "start" and "approve_increment" in selected and "approve_epic" not in selected:
            _fail("First implementation also requires the presented Epic direction.")
        if proposal["kind"] == "delivery" and "accept_increment" not in selected:
            _fail("Disposition requires Increment acceptance first.")
        candidate = _base(state)
        candidate.pop("uiDecision", None)
        candidate.pop("decisionChange", None)
        candidate.pop("epicDisposition", None)
        candidate.pop("nextWork", None)
        candidate["updatedAt"] = response["updatedAt"]
        increment = proposal["incrementId"]
        record = (f"# {proposal['epicId']} / {increment}\n\nDecision: Accepted\n"
                  f"Authority: user\nAccepted at: {response['updatedAt']}\n"
                  f"Proposal: {proposal['proposalId']}\nSource: {response['source']}\n"
                  f"Decisions: {', '.join(selected)}\n\n")
        if "close_epic" in selected:
            record += "Epic closure: Approved\n\n"
        record += "User response (quoted data):\n" + "\n".join("> " + line for line in response["text"].splitlines()) + "\n"
        record_path = receipt_path.with_suffix(".md")
        _immutable(record_path, record.encode())
        if "approve_epic" in selected:
            candidate.pop("plannedIncrementId", None)
            candidate.update(epicStatus="gate_b_pending", activeIncrementId=increment, currentRole="TDO", lastGatePassed="Gate A")
        if "approve_increment" in selected:
            candidate.update(epicStatus="increment_in_progress", activeIncrementId=increment, currentRole="Dev", lastGatePassed="Gate B")
        if "accept_increment" in selected:
            candidate.update(epicStatus="done_increment_accepted", activeIncrementId=None,
                             previousIncrementId=increment, previousIncrementStatus="accepted",
                             gateEAcceptance=record_path.relative_to(repo).as_posix(), currentRole="PO", lastGatePassed="Gate E")
        for decision, disposition in (("continue_epic", "continue"), ("split_scope", "split")):
            if decision in selected:
                candidate["epicDisposition"] = disposition
                candidate["nextWork"] = proposal["remainingWork"]
        if "close_epic" in selected:
            _remaining_portfolio(repo, state)
            evidence = closure_readiness(repo, authority, proposal["closureEvidence"])["evidence"]
            evidence["decisionAuthority"] = "user"
            evidence["authorityEvidence"] = [{"path": record_path.relative_to(path.parent).as_posix(), "kind": "authority_decision", "sha256": hashlib.sha256(record.encode()).hexdigest()}]
            issues, proof_hash = runtime.closure_content_issues(path.parent, state["epicId"], evidence, require_authority=True)
            if issues:
                _fail("; ".join(issues))
            closure_path = receipt_path.with_name(name + "-closure.json")
            closure_bytes = runtime._json_bytes(evidence)
            _immutable(closure_path, closure_bytes)
            candidate.update(epicStatus="epic_complete", epicDisposition="close",
                             epicClosureEvidence=closure_path.relative_to(repo).as_posix(),
                             epicClosureEvidenceSha256=hashlib.sha256(closure_bytes).hexdigest(),
                             epicClosureEvidenceSetSha256=proof_hash)
        issues = runtime._schema_issues(candidate, runtime._runtime_state_schema(repo))
        if candidate["epicStatus"] in runtime.TERMINAL_RUNTIME_STATUSES:
            _, acceptance_issues = runtime.terminal_acceptance(repo, path.parent, candidate, increment)
            issues += acceptance_issues
        if candidate["epicStatus"] == "epic_complete":
            _, closure_issues = runtime.epic_closure_evidence(repo, path.parent, candidate)
            issues += closure_issues
        if issues:
            _fail("; ".join(issues))
        receipt = {"decisionVersion": VERSION, "requestSha256": request_hash, "response": response,
                   "proposal": proposal, "candidateStateSha256": digest(candidate),
                   "decisionEvidence": {"path": record_path.relative_to(repo).as_posix(), "sha256": hashlib.sha256(record.encode()).hexdigest()}}
        receipt_bytes = runtime._json_bytes(receipt)
        _immutable(receipt_path, receipt_bytes)
        candidate["decisionReceipts"] = [*state.get("decisionReceipts", []), {"path": receipt_relative, "sha256": hashlib.sha256(receipt_bytes).hexdigest()}]
        final_issues = runtime._schema_issues(candidate, runtime._runtime_state_schema(repo))
        if final_issues:
            _fail("; ".join(final_issues))
        validate_proposal(repo, authority, state, proposal)
        if path.read_bytes() != source_bytes:
            _fail("Runtime changed before commit; no decision was registered.")
        _commit_state(path, candidate)
    return {"result": "applied", "decisions": selected, "next": next_step(repo, authority)}


def renew_response(repo: Path, authority: str, renewal: dict):
    """Preserve actual consent through administrative freshness changes only."""
    _, state = _state(repo, authority)
    current = state.get("decisionProposal")
    validate_proposal(repo, authority, state, current)
    previous = renewal.get("proposal")
    response = renewal.get("response")
    reason = renewal.get("reason")
    if not isinstance(previous, dict) or not isinstance(response, dict) or not isinstance(reason, str) or not reason.strip():
        _fail("Renewal requires the original proposal, actual response and administrative reason.")
    if response.get("proposalSha256") != digest(previous):
        _fail("Original response is not bound to the original proposal.")
    without_state = lambda value: {key: item for key, item in value.items() if key != "sourceStateSha256"}
    if digest(without_state(previous)) != digest(without_state(current)):
        _fail("Delivery or decision changed; administrative renewal cannot reuse this approval.")
    return {**response, "operationId": "renew-" + digest([response, current])[:40], "proposalSha256": digest(current),
            "renewal": {"originalProposalSha256": digest(previous), "originalResponseSha256": digest(response), "reason": reason}}


def request_change(repo: Path, authority: str, expected_proposal_sha256: str, reason: str):
    """Invalidate a pending proposal under the same lock used for approval."""
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 2000:
        _fail("A bounded change request is required.")
    path, _ = _state(repo, authority)
    with runtime_lock(path):
        _, state = _state(repo, authority)
        proposal = state.get("decisionProposal")
        if not proposal or digest(proposal) != expected_proposal_sha256:
            _fail("Change request targets a stale proposal; inspect the current delivery.")
        state.pop("decisionProposal")
        state["decisionChange"] = {"proposalId": proposal["proposalId"], "reason": reason}
        state["uiDecision"] = {"visibility": "preparing", "gate": "Gate E" if proposal["kind"] == "delivery" else "Gate B", "targetId": proposal["incrementId"]}
        _commit_state(path, state)
    return {"result": "change_requested", "next": next_step(repo, authority)}


def committed_acceptance(repo: Path, workspace: Path, state: dict, increment: str):
    """Read accepted history only from receipts referenced by committed state."""
    found = []
    for reference in state.get("decisionReceipts", []):
        receipt_path, issues = runtime._contained_decision_path(repo, workspace, reference["path"], "decision receipt")
        if issues:
            _fail("; ".join(issues))
        payload = _read(repo, reference["path"])
        if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
            _fail("Committed decision receipt changed.")
        receipt = json.loads(payload)
        proposal, response = receipt["proposal"], receipt["response"]
        if proposal["epicId"] != state["epicId"]:
            _fail("Committed receipt belongs to a different Epic.")
        if proposal["incrementId"] != increment or "accept_increment" not in response["decisions"]:
            continue
        evidence = receipt["decisionEvidence"]
        path, issues = runtime._contained_decision_path(repo, workspace, evidence["path"], "decision evidence")
        if issues or hashlib.sha256(_read(repo, evidence["path"])).hexdigest() != evidence["sha256"]:
            _fail("Committed acceptance evidence changed or is unsafe.")
        if not runtime.decision_accepts_increment(path, increment):
            _fail("Committed receipt does not prove Increment acceptance.")
        found.append(path)
    if len(set(found)) > 1:
        _fail("Duplicate committed Increment acceptances.")
    return found[0] if found else None


def next_step(repo: Path, authority: str):
    """Read-only next operation. Wording and UI derive from this same resolver."""
    try:
        path, state = _state(repo, authority)
        status = state["epicStatus"]
        if status in {"blocked", "epic_paused"}:
            _fail(f"Saved status is {status}. Resolve the pause/blocker and verify authority before resuming.")
        if status == "epic_complete":
            _, closure_issues = runtime.epic_closure_evidence(repo, path.parent, state)
            if closure_issues:
                _fail("Saved completion is unverified: " + "; ".join(closure_issues))
        if state.get("decisionProposal") is not None:
            validate_proposal(repo, authority, state, state["decisionProposal"])
            if state["mode"] == "Auto" and "close_epic" not in state["decisionProposal"]["decisions"]:
                return {"operation": "revalidate_auto_authority", "summary": "Revalidate the existing Auto mandate and carry out the offered work only when covered.", "nextDecision": "A mandate boundary or final acceptance.", "canExecute": True}
            return {"operation": "present_decision", "summary": state["decisionProposal"]["summary"], "nextDecision": "Approve the offered decisions or request a change.", "canExecute": False}
        if state.get("decisionChange"):
            return {"operation": "revise_proposal", "summary": state["decisionChange"]["reason"], "nextDecision": "Review the revised proposal before implementation or acceptance.", "canExecute": True}
        if state["mode"] == "Auto" and status in {"gate_a_pending", "gate_b_pending", "po_approval_pending"}:
            return {"operation": "revalidate_auto_authority", "summary": "Revalidate the existing Auto mandate, then continue only the work it covers.", "nextDecision": "A mandate boundary or final user acceptance; a mode label alone grants no new authority.", "canExecute": True}
        operations = {
            "gate_a_pending": ("plan_increment", "Prepare the direction and first Increment together.", "Approve the direction and first Increment.", True),
            "gate_b_pending": ("present_decision", "Review the proposed Increment.", "Approve the plan before implementation.", False),
            "po_approval_pending": ("present_decision", "Review the delivery and recommended Epic disposition.", "Accept the delivery and the explicitly offered disposition.", False),
            "increment_in_progress": ("implement", "Resume the approved implementation, review and verification.", "Delivery acceptance, or an earlier material scope/risk decision.", True),
            "review_in_progress": ("review", "Complete review and correct findings within the approved scope.", "Delivery acceptance, or a material scope/risk decision.", True),
            "tdo_validation_in_progress": ("verify", "Complete verification and prepare the Epic recommendation.", "Delivery acceptance.", True),
            "epic_complete": ("complete", "The Epic is complete.", "A new work request.", False),
        }
        if status == "done_increment_accepted":
            _, issues = runtime.terminal_acceptance(repo, path.parent, state, state.get("previousIncrementId", ""))
            if issues:
                _fail("; ".join(issues))
            if state.get("epicDisposition") == "continue":
                return {"operation": "plan_increment", "summary": state.get("nextWork", "Plan the remaining Epic outcome."), "nextDecision": "Approve the next plan before implementation." if state["mode"] == "Strict" else "Revalidate Auto authority before implementation; final acceptance remains required.", "canExecute": True}
            if state.get("epicDisposition") == "split":
                return {"operation": "split_scope", "summary": "Carry out the approved scope split: " + state.get("nextWork", "Separate the agreed new scope while preserving all original Epic requirements."), "nextDecision": "After the split, assess the original Epic for continuation or closure. Separate implementation requires its own plan and authority.", "canExecute": True}
            return {"operation": "present_decision", "summary": "Assess the remaining Epic scope and present a disposition.", "nextDecision": "Decide the Epic disposition.", "canExecute": False}
        if status not in operations:
            _fail("Resolve the saved pause/blocker and verify authority before resuming.")
        operation, summary, decision, execute = operations[status]
        if operation in {"implement", "review", "verify"}:
            plan, issues = runtime.terminal_increment_artifact(path.parent, state["epicId"], state["activeIncrementId"])
            if issues:
                _fail("; ".join(issues))
            heading = _read(path.parent, plan.relative_to(path.parent).as_posix()).decode("utf-8").splitlines()[0].lstrip("# ")
            summary = f"{heading}: {summary}"
        return {"operation": operation, "summary": summary, "nextDecision": decision, "canExecute": execute}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {"operation": "blocked", "summary": str(exc), "nextDecision": "Resolve this inconsistency before continuing.", "canExecute": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "publish", "apply", "change", "status", "readiness", "renew"])
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--authority-state-path", required=True)
    parser.add_argument("--input", type=Path, help="JSON spec, prepared proposal, actual response, or change request.")
    parser.add_argument("--evidence", help="Workspace-relative closure audit for read-only readiness.")
    args = parser.parse_args()
    try:
        if args.command == "status":
            result = next_step(args.repo, args.authority_state_path)
        elif args.command == "readiness":
            result = closure_readiness(args.repo, args.authority_state_path, args.evidence)
        else:
            value = json.loads(args.input.read_text()) if args.input else {}
            if args.command == "change":
                result = request_change(args.repo, args.authority_state_path, value.get("proposalSha256"), value.get("reason"))
            else:
                result = {"prepare": prepare, "publish": publish, "apply": apply, "renew": renew_response}[args.command](args.repo, args.authority_state_path, value)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"AIM decision failed: {exc}\n")


if __name__ == "__main__":
    main()
