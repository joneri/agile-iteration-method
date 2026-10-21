#!/usr/bin/env python3
"""Verify persisted Story flow and explicit dependencies in a disposable real UI.

The lifecycle authority/review records are synthetic test fixtures, never product
acceptance. Browser actions use the installed Playwright skill's CLI wrapper.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile
import uuid

import aim_ui_control as control
from verify_aim_ui import PlaywrightCli, isolated_state, read_json, require, utc_now, verify_doctor, preserve_server_log

ROOT = Path(__file__).resolve().parents[1]


def run(output, executable):
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_aim_stories import StoryDeliveryTests
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status='failed', journey='Story board and dependency graph', startedAt=utc_now(), checks={}, cleanup={})
    case = StoryDeliveryTests(); case.setUp(); case.repo = case.repo.resolve()
    cli = PlaywrightCli(executable, output, 'aim-stories-' + uuid.uuid4().hex)
    receipt = None
    try:
        buyer = copy.deepcopy(case.request['stories'][0]); buyer['status'] = 'draft'
        later = copy.deepcopy(case.request['stories'][2]); later['dependsOn'] = ['US-BUYER']
        later['prerequisites'] = [dict(id='COPY', text='Owner supplies the recovery email wording', resolved=False)]
        case.mutate('refine', dict(stories=[buyer,later]))
        with isolated_state(Path(case.tmp.name) / 'instances'):
            try:
                receipt = control.start(case.repo, open_browser=False)
                result['doctor'] = verify_doctor(case.repo,receipt,read_json(receipt['url']+'api/health'))
                cli.run('open','open',receipt['url'],'--browser','chromium','--idle-timeout','120000')
                cli.code('instrument', '''
await page.context().tracing.start({screenshots:true,snapshots:true});
await page.evaluate(() => {
 window.aimMoves=[];window.aimCard=document.querySelector('[data-story-id="US-BUYER"]');
 const animate=Element.prototype.animate;
 Element.prototype.animate=function(frames,options){if(this.dataset.storyId)window.aimMoves.push({id:this.dataset.storyId,frames,options});return animate.call(this,frames,options);};
});
const nav=await page.locator('.section-tab:visible').allTextContents();
if(JSON.stringify(nav)!==JSON.stringify(['Board','Graph']))throw Error('Primary navigation not Board/Graph');
if(await page.locator('#story-board [data-column="backlog"] [data-story-id]').count()!==2)throw Error('Backlog lost');
if(await page.locator('#story-board [data-column="ready"] [data-story-id]').count()!==1)throw Error('Ready lost');
await page.locator('[data-story-id="US-BUYER"] summary').click();
await page.locator('[data-story-id="US-BUYER"] summary').focus();
return {phase:'instrument',nav,backlog:2,ready:1};
''')
                buyer['status']='ready';case.mutate('refine',dict(stories=[buyer]))
                result['checks']['ready']=cli.code('ready','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-BUYER"]')?.dataset.column==='ready');
await page.waitForFunction(()=>window.aimMoves.length===1);
const continuity=await page.evaluate(()=>({same:window.aimCard===document.querySelector('[data-story-id="US-BUYER"]'),open:window.aimCard.querySelector('details').open,focus:document.activeElement===window.aimCard.querySelector('summary'),moves:window.aimMoves}));
if(!continuity.same||!continuity.open||!continuity.focus)throw Error('Polling lost card identity, details, or keyboard focus');
await page.waitForTimeout(3500);
if(await page.evaluate(()=>window.aimMoves.length)!==1)throw Error('Unchanged poll repeated animation');
await page.screenshot({path:expected.path,fullPage:true});
return {phase:'ready',...continuity};
''',dict(path=str(output/'ready.png')))
                case.approve()
                result['checks']['working']=cli.code('working','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-BUYER"]')?.dataset.column==='in_progress');
if(await page.locator('#story-board [data-column="in_progress"] [data-story-id]').count()!==2)throw Error('Approved work not moving');
await page.locator('[data-view="graph"]').click();
await page.locator('[data-graph-story="US-LATER"]').click();
await page.waitForFunction(()=>document.querySelectorAll('#graph-edges path').length===1);
const graph=await page.evaluate(()=>({nodes:document.querySelectorAll('[data-graph-story]').length,edges:document.querySelectorAll('#graph-edges path').length,focus:document.activeElement.id,inputs:document.querySelector('#graph-inspector').innerText}));
if(graph.nodes!==3||graph.edges!==1||graph.focus!=='graph-story-US-LATER'||!graph.inputs.includes('Owner supplies'))throw Error('Graph lost Story links, external prerequisite or focus: '+JSON.stringify(graph));
await page.screenshot({path:expected.path,fullPage:true});
return {phase:'working',...graph};
''',dict(path=str(output/'dependencies.png')))
                case.mutate('review',dict(deliveryId='DI-1',bindings=[case.binding]))
                result['checks']['graph-poll']=cli.code('graph-poll','''
await page.waitForFunction(()=>document.querySelector('[data-graph-story="US-BUYER"]')?.dataset.status==='pending');
if(await page.evaluate(()=>document.activeElement.id)!=='graph-story-US-LATER')throw Error('Graph polling lost keyboard focus');
await page.locator('[data-view="stories"]').click();
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-BUYER"]')?.dataset.column==='review');
return {phase:'graph-poll',focusPreserved:true};
''')
                case.mutate('validate',dict(deliveryId='DI-1',evidence=[case.evidence]))
                case.mutate('acceptance',dict(deliveryId='DI-1',evidence=[case.evidence],criteria=case.criterion_evidence()))
                result['checks']['acceptance']=cli.code('acceptance','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-BUYER"] .story-priority')?.textContent==='Waiting for you');
if(await page.locator('#story-board [data-column="done"] [data-story-id]').count())throw Error('Unaccepted Stories shown Done');
return {phase:'acceptance',waitingForOwner:true,done:0};
''')
                case.mutate('accept',dict(deliveryId='DI-1',authority=case.authority(case.document['deliveries'][0]['acceptanceSha256'],case.acceptance)))
                result['checks']['done']=cli.code('done','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-BUYER"]')?.dataset.column==='done');
await page.reload();await page.locator('[data-story-id="US-BUYER"][data-column="done"]').waitFor();
await page.emulateMedia({reducedMotion:'reduce'});
await page.evaluate(()=>{window.aimMoves=[];const animate=Element.prototype.animate;Element.prototype.animate=function(...args){window.aimMoves.push(this.dataset.storyId);return animate.apply(this,args);};});
return {phase:'done',persistedAfterReload:true};
''')
                later['status']='ready';later['prerequisites'][0]['resolved']=True
                case.mutate('refine',dict(stories=[later]))
                result['checks']['reduced-motion']=cli.code('reduced-motion','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-LATER"]')?.dataset.column==='ready');
if(await page.evaluate(()=>window.aimMoves.length))throw Error('Reduced motion still animates');
await page.setViewportSize({width:390,height:844});
if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Mobile document overflow');
await page.screenshot({path:expected.path,fullPage:true});
await page.context().tracing.stop({path:expected.trace});
return {phase:'reduced-motion',persistedReady:true,noAnimation:true,mobileUsable:true};
''',dict(path=str(output/'mobile.png'),trace=str(output/'trace.zip')))
                result['finalLedger']=case.document
                result['status']='passed'
            finally:
                preserve_server_log(case.repo,output,result)
                if receipt:
                    result['cleanup']['ui']=control.stop(case.repo)
                    require(result['cleanup']['ui'].get('stopped'), 'Unconfirmed UI cleanup')
                cli.run('close','close')
    except Exception as error:
        result.update(status='failed',error=str(error))
    finally:
        case.doCleanups()
        result.update(finishedAt=utc_now(),cliLogs=cli.logs)
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--playwright-cli',default=str(Path.home()/'.codex/skills/playwright/scripts/playwright_cli.sh'))
    args=parser.parse_args()
    result=run(args.output.resolve(),args.playwright_cli)
    print(json.dumps(dict(status=result['status'],error=result.get('error'),evidence=str(args.output/'result.json'))))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
