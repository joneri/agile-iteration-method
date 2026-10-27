#!/usr/bin/env python3
"""Isolated persisted original/correction/owner journey in the real AIM UI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

import aim_observations as observations
import aim_ui_control as control
from verify_aim_ui import PlaywrightCli, isolated_state, read_json, require, utc_now, verify_doctor, preserve_server_log

ROOT = Path(__file__).resolve().parents[1]


def run(output, executable):
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_aim_story_links import StoryLinkTests
    case = StoryLinkTests()
    case.setUp()
    workspace = Path(tempfile.mkdtemp(prefix='aim-story-continuity-')).resolve()
    shutil.copytree(case.repo, workspace, dirs_exist_ok=True)
    case.repo = case.case.repo = case.case.fixture.repo = workspace
    output.mkdir(parents=True, exist_ok=False)
    cli = PlaywrightCli(executable, output, 'aim-continuity-' + uuid.uuid4().hex)
    result = dict(status='failed', startedAt=utc_now(), checks={}, cleanup={})
    removable = False
    receipt = None
    try:
        with isolated_state(workspace / 'instances'):
            try:
                case.ready_correction()
                receipt = control.start(workspace, open_browser=False)
                result['doctor'] = verify_doctor(workspace, receipt, read_json(receipt['url'] + 'api/health'))
                cli.run('open', 'open', receipt['url'], '--browser', 'chromium', '--idle-timeout', '120000')
                cli.run('snapshot', 'snapshot')
                cli.code('original-open', '''
await page.context().tracing.start({screenshots:true,snapshots:true});
await page.setViewportSize({width:1440,height:1000});
const original=page.locator('[data-story-id="US-OBS"]');
await original.waitFor();await original.locator('summary').click();
await page.locator('[data-story-id="US-CORRECTION"] summary').click();
const text=await original.innerText();
if(!text.includes('Changes requested')||!text.includes('Correction ready')||!text.includes('US-CORRECTION'))throw Error('Original correction continuity missing');
if(await original.getAttribute('data-column')!=='in_progress')throw Error('Correction invented original acceptance');
return {phase:'original-open',originalText:text,correctionText:await page.locator('[data-story-id="US-CORRECTION"]').innerText()};
''')
                case.resubmit_original()
                result['checks']['original-ready'] = cli.code('original-ready', '''
const original=page.locator('[data-story-id="US-OBS"]');
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='review');
await original.getByRole('button',{name:'Copy final owner decision request',exact:true}).waitFor();
await page.context().grantPermissions(['clipboard-read','clipboard-write']);
await original.getByRole('button',{name:'Copy final owner decision request',exact:true}).click();
const prompt=await page.evaluate(()=>navigator.clipboard.readText());
if(!prompt.includes('LOOP-EXCEPTION')||!prompt.includes('US-OBS-SECOND')||!prompt.includes('US-CORRECTION')||!prompt.includes('review_first')||!prompt.includes('changes_requested'))throw Error('Final question lost original scope or previous decision');
await page.screenshot({path:expected.path,fullPage:true});
return {phase:'original-ready',copiedPrompt:prompt};
''', dict(path=str(output / 'original-ready.png')))
                request, sha = case.decision()
                request_path = workspace / '.aim/final-owner-request.json'
                request_path.write_text(json.dumps(request, indent=2) + '\n')
                command = [sys.executable, str(ROOT / 'scripts/aim_observations.py'), 'decision', '--repo', str(workspace),
                           '--input', str(request_path), '--expected-sha256', sha]
                process = subprocess.run(command, capture_output=True, text=True)
                (output / 'decision-cli.json').write_text(json.dumps(dict(command=command, exitCode=process.returncode,
                                                stdout=process.stdout, stderr=process.stderr), indent=2) + '\n')
                require(process.returncode == 0, 'Actual decision CLI failed: ' + process.stderr)
                result['checks']['original-accepted'] = cli.code('original-accepted', '''
await page.waitForFunction(()=>document.querySelector('[data-story-id="US-OBS"]')?.dataset.column==='done');
await page.reload();await page.locator('[data-story-id="US-OBS"][data-column="done"]').waitFor();
const sibling=await page.locator('[data-story-id="US-OBS-SECOND"]').getAttribute('data-column');
const correction=await page.locator('[data-story-id="US-CORRECTION"]').getAttribute('data-column');
if(sibling!=='review'||correction!=='review')throw Error('Original decision accepted sibling/correction implicitly');
await page.setViewportSize({width:390,height:844});
await page.screenshot({path:expected.path,fullPage:true});
await page.context().tracing.stop({path:expected.trace});
return {phase:'original-accepted',reloadPersisted:true,sibling,correction};
''', dict(path=str(output / 'accepted-mobile.png'), trace=str(output / 'trace.zip')))
                require((workspace / observations.LEDGER).read_bytes() == case.original, 'Native ledger changed.')
                shutil.copyfile(workspace / observations.FILE, output / 'final-observations.json')
                result['status'] = 'passed'
            finally:
                preserve_server_log(workspace, output, result)
                if receipt:
                    stopped = control.stop(workspace)
                    result['cleanup']['server'] = stopped
                    removable = stopped.get('status') in {'stopped', 'not_running'}
                else:
                    removable = True
                try:
                    cli.run('close', 'close')
                except Exception as exc:
                    result['cleanup']['browserError'] = str(exc)
                    result['status'] = 'failed'
    except Exception as exc:
        result['error'] = str(exc)
        result['status'] = 'failed'
    finally:
        case.doCleanups()
        if removable:
            shutil.rmtree(workspace)
        else:
            result['cleanup']['recoveryWorkspace'] = str(workspace)
            result['status'] = 'failed'
        result.update(finishedAt=utc_now(), cliLogs=cli.logs)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--playwright-cli', default=str(Path.home() / '.codex/skills/playwright/scripts/playwright_cli.sh'))
    args = parser.parse_args()
    result = run(args.output.resolve(), args.playwright_cli)
    print(json.dumps(dict(status=result['status'], error=result.get('error'), evidence=str(args.output / 'result.json'))))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
