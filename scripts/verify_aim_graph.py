#!/usr/bin/env python3
"""Drive the actual AIM Graph UI on a disposable native delivery; retain raw proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import aim_stories
import aim_observations
import aim_ui_control as control
from verify_aim_ui import (PlaywrightCli, VerificationError, finish_workspace,
                           isolated_state, preserve_server_log, read_json,
                           require, seed, utc_now, verify_doctor)


def reference(repo, path, contents=None):
    file = repo / path
    if contents is not None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(contents)
    return {"path": path, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}


def seed_graph(repo):
    imported = seed(repo)
    criteria = ["US-VERIFY-ONE/AC-1"]
    check = dict(id="QC-GRAPH", criteria=criteria, kind="journey", stage="both",
                 workload="synthetic Graph browser route", environment="disposable local repo",
                 method="native receipts then actual UI controls", expected={"graph": 1}, goalIds=[])
    quality = dict(checks=[check], numericGoals="not_applicable", reviewPolicy={"mode": "independent"},
        rationale="Synthetic activity lifecycle fixture; source performance is checked separately.",
        primaryResult={"checkId": "QC-GRAPH", "notApplicableReason": "Fixture data preparation is not a delivered computation workload."},
        caseCoverage={"failureCases": {"checkIds": ["QC-GRAPH"]},
                      "nonDefaultModes": {"notApplicableReason": "No selectable domain modes."},
                      "resultValidity": {"checkIds": ["QC-GRAPH"]},
                      "workloadFamilies": {"notApplicableReason": "No performance check in this UI fixture."}},
        sharedRequirements=[dict(source="INT-VERIFY", requirement="Read-only UI preserves native authority", checkIds=["QC-GRAPH"])])
    def activity(identifier, title, paths, deps, kind="write"):
        role = "reviewer" if kind == "review" else "dev"
        return dict(id=identifier, title=title, kind=kind, role=role, storyIds=["US-VERIFY-ONE"],
                    paths=paths, dependsOn=deps, skills=[f"aim-{role}-engineering"])
    plan = dict(version=1, delegationAllowed=True, maxWorkers=2,
                parallelBenefit="Independent view and storage work after a shared contract",
                activities=[activity("contract", "Define the idea contract", ["contract.py"], []),
                    activity("capture", "Build idea capture", ["view.py"], ["contract"]),
                    activity("storage", "Keep ideas after refresh", ["storage.py"], ["contract"]),
                    activity("review", "Review capture and recovery", ["contract.py", "view.py", "storage.py"],
                             ["capture", "storage"], "review")])
    evidence = reference(repo, ".aim/graph-plan.md", "Synthetic Graph browser fixture; no real product acceptance.\n")
    result = aim_stories.execute(repo, "plan", dict(id="DI-GRAPH-FIXTURE", title="Idea wall verification fixture",
        goal="Capture an idea and keep it after refreshing", storyIds=["US-VERIFY-ONE"],
        planEvidence=[evidence], qualityPlan=quality, executionPlan=plan), imported["storeSha256"])
    delivery = result["document"]["deliveries"][0]
    authority = reference(repo, ".aim/fixture-authority.md", "Synthetic authority used only to verify native graph behavior.\n")
    return aim_stories.execute(repo, "approve", dict(deliveryId=delivery["id"], authority={
        "kind": "user", **authority, "scopeSha256": delivery["scopeSha256"]}), result["storeSha256"])



# The public graph is Story-first. Keep seed_graph for package/native contract tests.
from verify_aim_story_board import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--playwright-cli")
    args=parser.parse_args()
    require(shutil.which("npx") is not None,"npx must already be installed")
    executable=shutil.which(args.playwright_cli or "playwright-cli")
    if executable is None and args.playwright_cli is None:
        wrapper=Path.home()/".codex/skills/playwright/scripts/playwright_cli.sh"
        if wrapper.is_file() and os.access(wrapper,os.X_OK): executable=str(wrapper)
    require(executable is not None,"Installed Playwright CLI is unavailable")
    output=(args.output or Path("output/playwright")/("aim-graph-"+uuid.uuid4().hex[:10])).resolve()
    result=run(output,executable)
    print(f"AIM Graph verification {result['status']}: {output/'result.json'}")
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
