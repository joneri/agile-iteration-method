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


OPEN = """
await page.locator('[data-view="graph"]').click();
await page.locator('#graph-node-contract').waitFor();
if (!await page.locator('#graph-node-contract').getAttribute('data-status').then(s => s === 'ready')) throw new Error('Contract not ready');
await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], {origin:new URL(expected.url).origin});
await page.locator('#graph-copy-assignment').click();
await page.waitForFunction(() => document.querySelector('#graph-copy-feedback')?.textContent.startsWith('Copied.'));
const clipboard = await page.evaluate(() => navigator.clipboard.readText());
if (!clipboard.includes('untrusted repository data') || !clipboard.includes(expected.sha)
    || !clipboard.includes('aim-dev-engineering') || !clipboard.includes('contract.py')) throw new Error('Assignment missing boundaries');
await page.locator('#graph-node-capture').focus();
await page.evaluate(() => window.scrollTo(0,0));
await page.screenshot({path:expected.screenshot,fullPage:true});
return {phase:'open',graphVisible:1,assignmentBounded:1,clipboard,dom:await page.content()};
"""

PROGRESS = """
await page.waitForFunction(() => document.querySelector('#graph-node-capture')?.dataset.status === 'ready',null,{timeout:15000});
if (await page.locator('#graph-node-contract').getAttribute('data-status') !== 'completed') throw new Error('Missing completed receipt');
if (await page.evaluate(() => document.activeElement.id) !== 'graph-node-capture') throw new Error('Polling lost keyboard focus');
await page.locator('#graph-node-capture').press('Enter');
await page.locator('#graph-inspector').filter({hasText:'Build idea capture'}).waitFor();
if (!await page.locator('#graph-copy-assignment').isEnabled()) throw new Error('Ready assignment unavailable');
const graphSize = () => {
  const canvas = document.getElementById('graph-canvas');
  const svg = document.getElementById('graph-edges');
  return {layoutHeight:canvas.clientHeight,scrollHeight:canvas.scrollHeight,svgHeight:Number(svg.getAttribute('height'))};
};
const beforeResize = await page.evaluate(graphSize);
for (let i=0;i<4;i++) {
  await page.setViewportSize({width:1440-i*10,height:1000});
  await page.waitForTimeout(60);
}
const afterResize = await page.evaluate(graphSize);
if (afterResize.scrollHeight > afterResize.layoutHeight+1 || afterResize.svgHeight !== afterResize.layoutHeight) throw new Error('Graph redraw grows its own overflow');
await page.evaluate(() => window.scrollTo(0,0));
await page.screenshot({path:expected.screenshot,fullPage:true});
await page.setViewportSize({width:1200,height:1000});
const region = page.locator('#graph-scroll');
await region.focus();
await region.press('ArrowRight');
await region.press('ArrowRight');
await page.waitForTimeout(150);
const regionScroll = await region.evaluate(el => el.scrollLeft);
if (regionScroll < 1) throw new Error('Graph scroll-region witness did not scroll');
return {phase:'progress',pollingUpdated:1,beforeResize,afterResize,regionScroll,dom:await page.content()};
"""

STALE = """
await page.waitForFunction(() => document.querySelector('#graph-node-contract')?.dataset.status === 'stale',null,{timeout:15000});
if (await page.evaluate(() => document.activeElement.id) !== 'graph-scroll') throw new Error('Polling lost scroll-region focus');
const regionScroll = await page.locator('#graph-scroll').evaluate(el => el.scrollLeft);
if (regionScroll < 1) throw new Error('Polling reset graph reading position');
const capture = await page.locator('#graph-node-capture').getAttribute('data-status');
if (capture === 'ready' || await page.locator('#graph-copy-assignment').count()) throw new Error('Stale dependency still offers assignment');
await page.setViewportSize({width:390,height:844});
await page.waitForTimeout(100);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
if (overflow) throw new Error('Mobile page overflows');
await page.evaluate(() => window.scrollTo(0,0));
await page.screenshot({path:expected.mobile,fullPage:true});
await page.setViewportSize({width:1440,height:1000});
await page.screenshot({path:expected.screenshot,fullPage:true});
return {phase:'stale',staleBlocked:1,mobileUsable:1,regionScroll,dom:await page.content()};
"""

DIAGNOSTIC = """
await page.locator('.product-issues').filter({hasText:'Evidence changed'}).waitFor({timeout:15000});
await page.locator('#graph-node-contract').waitFor();
if (await page.locator('#graph-copy-assignment').count()) throw new Error('Invalid native evidence offers an assignment');
const nodes = await page.locator('[data-graph-node]').count();
if (nodes !== 4) throw new Error('Diagnostic graph hid the dependency path');
await page.evaluate(() => window.scrollTo(0,0));
await page.screenshot({path:expected.screenshot,fullPage:true});
return {phase:'diagnostic',diagnosticVisible:1,assignments:0,nodes,dom:await page.content()};
"""


def run(output, executable):
    output.mkdir(parents=True, exist_ok=False)
    result = dict(version=1, journey="AIM Graph", status="failed", startedAt=utc_now(), checks={}, cleanup={})
    root = Path(tempfile.mkdtemp(prefix="aim-graph-verification-")).resolve()
    repo = root / "synthetic-product"
    repo.mkdir()
    cli = PlaywrightCli(executable, output, "aim-graph-" + uuid.uuid4().hex)
    receipt = None
    attempted = tracing = False
    removable = True
    with isolated_state(root / "instances"):
        try:
            current = seed_graph(repo)
            receipt = control.start(repo, open_browser=False)
            removable = False
            result["startReceipt"] = receipt
            result["doctor"] = verify_doctor(repo, receipt, read_json(receipt["url"] + "api/health"))
            attempted = True
            cli.run("open", "open", receipt["url"], "--browser", "chromium", "--idle-timeout", "120000")
            cli.code("trace-start", "await page.context().tracing.start({screenshots:true,snapshots:true});return {phase:'trace-start'};")
            tracing = True
            before = (repo / aim_stories.FILE).read_bytes()
            result["checks"]["open"] = cli.code("open", OPEN, dict(url=receipt["url"], sha=current["storeSha256"], screenshot=str(output/"ready.png")))
            require((repo/aim_stories.FILE).read_bytes() == before, "Graph view or copy mutated the ledger")
            started = aim_stories.execute(repo, "activity", dict(deliveryId="DI-GRAPH-FIXTURE",activityId="contract",status="running",session="synthetic-dev"),current["storeSha256"])
            node = next(n for n in started["executionGraph"]["activities"] if n["id"] == "contract")
            reference(repo,"contract.py","# fixture contract v1\n")
            proof = reference(repo,".aim/contract-proof.txt","Fixture raw contract observation: fields id,title.\n")
            completed = aim_stories.execute(repo,"activity",dict(deliveryId="DI-GRAPH-FIXTURE",activityId="contract",status="completed",session="synthetic-dev",attempt=node["attempt"],sourcePaths=["contract.py"],evidence=[proof]),started["storeSha256"])
            result["checks"]["progress"] = cli.code("progress",PROGRESS,dict(screenshot=str(output/"progress.png")))
            (repo/"contract.py").write_text("# fixture contract v2: proof is obsolete\n")
            ledger = (repo/aim_stories.FILE).read_bytes()
            result["checks"]["stale"] = cli.code("stale",STALE,dict(screenshot=str(output/"stale.png"),mobile=str(output/"mobile.png")))
            require((repo/aim_stories.FILE).read_bytes() == ledger, "Freshness projection mutated the ledger")
            # Deliberately corrupt a disposable fixture's plan evidence to test
            # diagnostic display; never change actual delivery proof this way.
            (repo/".aim/graph-plan.md").write_text("Changed synthetic plan evidence.\n")
            result["checks"]["diagnostic"] = cli.code("diagnostic", DIAGNOSTIC,dict(screenshot=str(output/"diagnostic.png")))
            require((repo/aim_stories.FILE).read_bytes() == ledger, "Diagnostic projection mutated the ledger")
            result["readOnlyVerified"] = True
            result["status"] = "passed"
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            if attempted:
                try:
                    cli.code("failure", "await page.screenshot({path:expected.path,fullPage:true});return {phase:'failure',dom:await page.content()};",dict(path=str(output/"failure.png")))
                except Exception as error:
                    result["captureError"] = str(error)
        finally:
            if tracing:
                try:
                    cli.code("trace-stop", "await page.context().tracing.stop({path:expected.path});return {phase:'trace-stop'};",dict(path=str(output/"trace.zip")))
                except Exception as error:
                    result["cleanup"]["traceError"] = str(error);result["status"]="failed"
            if attempted:
                try:
                    closed=cli.run("close","close")
                    require(closed.get("status") in {"closed","not-open"},"Browser cleanup unconfirmed")
                    result["cleanup"]["browser"]=closed
                except Exception as error:
                    result["cleanup"]["browserError"]=str(error);result["status"]="failed"
            if receipt:
                try:
                    current=control.status(repo)
                    require(all(current.get(k)==receipt.get(k) for k in ("repo","pid","instanceId")),"UI instance changed before cleanup")
                    stopped=control.stop(repo);require(stopped.get("stopped") is True,"UI stop unconfirmed")
                    result["cleanup"]["ui"]=stopped;removable=True
                except Exception as error:
                    result["cleanup"]["uiError"]=str(error);result["status"]="failed"
            preserve_server_log(repo,output,result)
    finish_workspace(root,removable,result)
    result.update(finishedAt=utc_now(),cliLogs=cli.logs)
    (output/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    return result


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
