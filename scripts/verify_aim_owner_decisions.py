#!/usr/bin/env python3
"""Real decision CLI -> ordinary UI polling -> actual card movement, no import."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import sys
import uuid
import aim_observations as observations
import aim_ui_control as control
from verify_aim_ui import PlaywrightCli, isolated_state, read_json, require, utc_now, verify_doctor, preserve_server_log

ROOT=Path(__file__).resolve().parents[1]


def run(output, executable):
    sys.path.insert(0,str(ROOT/'tests'))
    from test_aim_observation_decisions import AutomaticDecisionTests
    case=AutomaticDecisionTests();case.setUp()
    # Fixtures prepare data; the owned server checkout must survive uncertain cleanup.
    workspace=Path(tempfile.mkdtemp(prefix='aim-owner-decisions-')).resolve()
    shutil.copytree(case.repo,workspace,dirs_exist_ok=True)
    case.repo=case.fixture.repo=workspace
    removable=False
    output.mkdir(parents=True,exist_ok=False)
    cli=PlaywrightCli(executable,output,'aim-decisions-'+uuid.uuid4().hex)
    result=dict(status='failed',startedAt=utc_now(),checks={},cleanup={})
    receipt=None
    def decide(request,sha,name):
        request_path=case.repo/'.aim'/('request-'+name+'.json')
        request_path.write_text(json.dumps(request,ensure_ascii=False))
        command=[sys.executable,str(ROOT/'scripts/aim_observations.py'),'decision','--repo',str(case.repo),'--input',str(request_path),'--expected-sha256',sha]
        process=subprocess.run(command,capture_output=True,text=True)
        (output/(name+'-cli.json')).write_text(json.dumps(dict(command=command,exitCode=process.returncode,stdout=process.stdout,stderr=process.stderr),indent=2)+'\n')
        require(process.returncode==0,'Decision CLI failed: '+process.stdout)
        return json.loads(process.stdout)
    try:
        with isolated_state(case.repo/'instances'):
            try:
                receipt=control.start(case.repo,open_browser=False)
                result['doctor']=verify_doctor(case.repo,receipt,read_json(receipt['url']+'api/health'))
                cli.run('open','open',receipt['url'],'--browser','chromium','--idle-timeout','120000')
                cli.code('arm','''
await page.context().tracing.start({screenshots:true,snapshots:true});
await page.setViewportSize({width:1440,height:1000});
await page.locator('[data-story-id="US-OBS"]').waitFor();
await page.locator('[data-story-id="US-OBS"] summary').click();await page.locator('[data-story-id="US-OBS"] summary').focus();
await page.evaluate(()=>{window.ownerMoves=[];window.ownerCard=document.querySelector('[data-story-id="US-OBS"]');const animate=Element.prototype.animate;Element.prototype.animate=function(...args){if(this.dataset.storyId)window.ownerMoves.push({id:this.dataset.storyId,column:this.dataset.column});return animate.apply(this,args);};});
return {phase:'arm',ownerWaiting:await page.locator('[data-story-id="US-OBS"] .story-priority').innerText()};
''')
                snapshots=copy.deepcopy(observations.load(case.repo)[0]['entries'])
                native=(case.repo/observations.LEDGER).read_bytes()
                request,sha=case.request_for();result['humanReceipt']=decide(request,sha,'human-accept')
                result['checks']['human']=cli.code('human','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='done');
await page.waitForFunction(()=>window.ownerMoves.length===1);
const state=await page.evaluate(()=>({same:window.ownerCard===document.querySelector('[data-story-id="US-OBS"]'),focus:document.activeElement===window.ownerCard.querySelector('summary'),open:window.ownerCard.querySelector('details').open,moves:window.ownerMoves,other:document.querySelector('[data-story-id="US-OBS-SECOND"]').dataset.column,text:window.ownerCard.innerText}));
if(!state.same||!state.focus||!state.open||state.other!=='review'||state.text.includes('Needs: Owner assesses'))throw Error('Actual decision lost continuity/selection/owner-input state');
await page.waitForTimeout(3500);if(await page.evaluate(()=>window.ownerMoves.length)!==1)throw Error('Unchanged poll repeated decision movement');
await page.screenshot({path:expected.path,fullPage:true});return {phase:'human',...state};
''',dict(path=str(output/'human-accepted.png')))
                require(observations.load(case.repo)[0]['entries']==snapshots,'Owner acceptance required an extra snapshot/status edit')
                duplicate=decide(request,sha,'same-decision-retry');require(duplicate['alreadyRecorded'],'Uncertain retry duplicated the decision')
                request,sha=case.request_for(decision='changes_requested',ident='human-changes');decide(request,sha,'human-changes')
                result['checks']['rework']=cli.code('rework','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='in_progress');
await page.waitForFunction(()=>window.ownerMoves.length===2);
if(await page.locator('[data-story-id="US-OBS-SECOND"]').getAttribute('data-column')!=='review')throw Error('UnselectedStorymoved');
await page.reload();await page.locator('[data-story-id="US-OBS"][data-column="in_progress"]').waitFor();
return {phase:'rework',persisted:true,otherUnchanged:true};
''')
                corrected=copy.deepcopy(case.request);corrected['entry']['id']='human-corrected-review'
                corrected['entry']['reportedState']='awaiting_owner'
                corrected['entry']['activities'][0]['reason']='Corrected synthetic implementation submitted for owner assessment'
                observations.import_entry(case.repo,corrected,observations.load(case.repo)[1])
                cli.code('corrected-review',"""
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='review');
if(!await page.locator('[data-story-id="US-OBS"] .story-priority').innerText().then(t=>t==='Waiting for you'))throw Error('Corrected work never returns for assessment');
return {phase:'corrected-review',waitingForFreshDecision:true};
""")
                request,sha=case.request_for(ident='human-final');decide(request,sha,'human-final')
                result['checks']['corrected']=cli.code('corrected',"""
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='done');
return {phase:'corrected',newDecisionAccepted:true};
""")
                q=copy.deepcopy(case.request);q['entry'].update(id='agent-registration',deliveryId='LOOP-DELEGATED')
                q['entry']['epic']['id']='EPIC-DELEGATED'
                for story in q['entry']['stories']:story['id']=story['id'].replace('OBS','DELEGATED')
                for a in q['entry']['activities']:a['storyIds']=[sid.replace('OBS','DELEGATED') for sid in a['storyIds']]
                mandate=case.fixture.artifact('owner-mandate.md','Synthetic actual human delegation to named owner/session, accept assessment only.')
                q['entry']['deliveryPolicy']=dict(mode='loop',owner=dict(kind='agent',id='fixture-owner',session='fixture-owner-session',mandate=mandate,decisions=['accept']))
                observations.import_entry(case.repo,q,observations.load(case.repo)[1])
                ctx=observations.decision_context(case.repo,dict(deliveryId='LOOP-DELEGATED',storyIds=['US-DELEGATED']))
                artifact=dict(ownerDecisionVersion=1,deliveryId='LOOP-DELEGATED',operation='accept',scopeSha256=ctx['scopeSha256'],id='fixture-owner',session='fixture-owner-session',decision='approved',reason='Synthetic delegated owner integrated assessment, distinct from author review.')
                ref=case.fixture.artifact('owner-acceptance.json',json.dumps(artifact))
                request=dict(id='agent-owner-1',deliveryId='LOOP-DELEGATED',storyIds=['US-DELEGATED'],scopeSha256=ctx['scopeSha256'],decision='approved',authority=dict(kind='agent',**ref,id=artifact['id'],session=artifact['session'],scopeSha256=ctx['scopeSha256']),reason=artifact['reason'],evidence=[case.source])
                cli.code('agent-arm','''
await page.locator('[data-story-id="US-DELEGATED"][data-column="review"]').waitFor();
await page.evaluate(()=>{window.ownerMoves=[];const animate=Element.prototype.animate;Element.prototype.animate=function(...args){if(this.dataset.storyId)window.ownerMoves.push({id:this.dataset.storyId,column:this.dataset.column});return animate.apply(this,args);};});
return {phase:'agent-arm'};
''')
                before=copy.deepcopy(observations.load(case.repo)[0]['entries'])
                result['agentReceipt']=decide(request,ctx['storeSha256'],'delegated-accept')
                result['checks']['delegated']=cli.code('delegated','''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-DELEGATED"]')?.dataset.column==='done');
await page.waitForFunction(()=>window.ownerMoves.length===1);
if(await page.locator('[data-story-id="US-DELEGATED-SECOND"]').getAttribute('data-column')!=='review')throw Error('Delegated assessment moved otherStory');
await page.screenshot({path:expected.path,fullPage:true});
await page.reload();await page.locator('[data-story-id="US-DELEGATED"][data-column="done"]').waitFor();
await page.context().tracing.stop({path:expected.trace});
return {phase:'delegated',persistedDone:true,otherUnchanged:true};
''',dict(path=str(output/'delegated-accepted.png'),trace=str(output/'trace.zip')))
                saved,_=observations.load(case.repo)
                require(saved['entries']==before,'Delegated acceptance required another import')
                require((case.repo/observations.LEDGER).read_bytes()==native,'Exception owner decision mutated native ledger')
                result.update(status='passed',unchangedSnapshotCount=len(before),decisions=len(saved['decisions']),nativeLedgerUnchanged=True,decisionsWithoutStatusEdits=True)
                (output/'journal.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n')
            finally:
                preserve_server_log(case.repo,output,result)
                if receipt:
                    result['cleanup']['ui']=control.stop(case.repo)
                    removable=result['cleanup']['ui'].get('stopped') is True
                    require(removable, 'UI process stop unconfirmed; preserve the recovery workspace')
                cli.run('close','close')
    except Exception as error:result.update(status='failed',error=str(error))
    finally:
        case.doCleanups()
        if removable: shutil.rmtree(workspace)
        else:
            result['cleanup']['recoveryWorkspace']=str(workspace)
            result['status']='failed'
        result.update(finishedAt=utc_now(),cliLogs=cli.logs)
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--playwright-cli',default=str(Path.home()/'.codex/skills/playwright/scripts/playwright_cli.sh'))
    args=parser.parse_args();result=run(args.output.resolve(),args.playwright_cli)
    print(json.dumps(dict(status=result['status'],error=result.get('error'),evidence=str(args.output/'result.json'))))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
