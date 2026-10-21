"""Observation recovery must never create delivery authority or lose history."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_aim_stories as fixtures
from aim_observations import FILE, import_entry, load, project
from aim_stories import project_story_board
import aim_observations


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.StoryDeliveryTests(); self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo
        self.original = (self.repo / '.aim/product-backlog.json').read_bytes()
        self.source = self.fixture.artifact('exception-plan.md', 'Original exception plan and actual pending human decision.')
        self.entry = dict(id='snapshot-1',deliveryId='LOOP-EXCEPTION',title='Current exception work',
            goal='Restore a calm game feel',reportedState='rework_required',decisionBoundary='Human rejected first probe; final acceptance remains reserved.',
            epic=dict(id='EPIC-OBS',title='Calm play',outcome='Player can play comfortably'),
            stories=[dict(id='US-OBS',title='Calm camera',persona='Player',need='A steady view',benefit='Keep orientation',
                acceptanceCriteria=[dict(id='AC-1',text='A standing jump does not move the camera.')])],
            activities=[dict(id='core',title='Camera core',role='dev',status='completed',dependsOn=[],storyIds=['US-OBS'],reason='Reported core with bounded proof'),
                        dict(id='owner',title='Human playtest',role='human',status='blocked',dependsOn=['core'],storyIds=['US-OBS'],reason='Human rejected prior game feel')],sources=[self.source])
        self.request=dict(ledgerSha256=hashlib.sha256(self.original).hexdigest(),entry=self.entry)

    def test_actual_import_projects_read_only_stories_graph_and_preserves_ledger(self):
        r=import_entry(self.repo,self.request)
        b=project_story_board(self.repo)
        self.assertTrue(b['valid']); self.assertEqual(len(b['stories']),4)
        s=b['stories'][-1]; self.assertTrue(s['readOnly']); self.assertEqual(s['column'],'in_progress')
        g=b['executionGraph']; self.assertEqual(g['deliveryId'],'LOOP-EXCEPTION')
        self.assertEqual(g['recommendedIds'],[]); self.assertFalse(g['nativeEvidenceValid'])
        self.assertEqual(g['edges'],[{'from':'core','to':'owner'}])
        self.assertIn('rework required',g['summary']); self.assertFalse(r['nativeLedgerChanged'])
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),self.original)
        before=(self.repo/FILE).read_bytes()
        project_story_board(self.repo)
        self.assertEqual(before,(self.repo/FILE).read_bytes())

    def test_historical_import_preserves_active_delivery_and_prior_records(self):
        self.fixture.approve()
        self.request['ledgerSha256'] = aim_observations.fingerprint(self.repo, aim_observations.LEDGER)
        self.entry['replacesDeliveryIds'] = ['DI-1']
        native_before = (self.repo/'.aim/product-backlog.json').read_bytes()
        first = import_entry(self.repo, self.request)
        original, _ = load(self.repo)
        request = copy.deepcopy(self.request)
        request['makeCurrent'] = False
        entry = request['entry']
        entry.update(id='past-snapshot', deliveryId='PAST-CORRECTION',
                     reportedState='reported_complete')
        entry.pop('replacesDeliveryIds')
        entry['epic']['id'] = 'EPIC-PAST'
        entry['stories'][0].update(id='US-PAST', boardStatus='done')
        for activity in entry['activities']:
            activity.update(storyIds=['US-PAST'], status='completed')
        receipt = import_entry(self.repo, request, first['storeSha256'])
        saved, _ = load(self.repo)
        self.assertEqual(receipt['currentId'], original['currentId'])
        self.assertEqual(saved['entries'][:-1], original['entries'])
        board = project_story_board(self.repo)
        current = next(s for s in board['stories'] if s['id'] == 'US-OBS')
        past = next(s for s in board['stories'] if s['id'] == 'US-PAST')
        self.assertFalse(current['historical'])
        self.assertEqual(current['column'], 'in_progress')
        self.assertFalse(past['historical'])
        self.assertEqual(past['column'], 'done')
        self.assertEqual(board['executionGraph']['deliveryId'], 'LOOP-EXCEPTION')
        # Both a historical append and a later current delivery must retain the
        # prior explicit history disposition of native work.
        request = copy.deepcopy(request)
        request.pop('makeCurrent')
        request['entry']['id'] = 'past-now-current'
        import_entry(self.repo, request, receipt['storeSha256'])
        board = project_story_board(self.repo)
        native = {s['id']: s for s in board['stories'] if not s.get('observationId')}
        self.assertTrue(native['US-BUYER']['historical'])
        self.assertFalse(native['US-LATER'].get('historical', False))
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(), native_before)

    def test_historical_import_rejects_missing_current_and_current_refresh(self):
        request = copy.deepcopy(self.request)
        request['makeCurrent'] = False
        with self.assertRaisesRegex(ValueError, 'existing current'):
            import_entry(self.repo, request)
        self.assertFalse((self.repo/FILE).exists())
        first = import_entry(self.repo, self.request)
        before = (self.repo/FILE).read_bytes()
        request['entry']['id'] = 'snapshot-2'
        with self.assertRaisesRegex(ValueError, 'current import'):
            import_entry(self.repo, request, first['storeSha256'])
        for invalid in ('false', 0, None):
            request['makeCurrent'] = invalid
            with self.assertRaisesRegex(ValueError, 'boolean'):
                import_entry(self.repo, request, first['storeSha256'])
        self.assertEqual((self.repo/FILE).read_bytes(), before)

    def test_main_board_combines_actual_work_and_accepted_done_without_old_attempts(self):
        self.fixture.accept()
        self.request['ledgerSha256'] = aim_observations.fingerprint(self.repo, aim_observations.LEDGER)
        original_native = (self.repo/'.aim/product-backlog.json').read_bytes()
        self.entry.update(reportedState='reported_complete', replacesDeliveryIds=['DI-1'])
        self.entry['stories'][0]['boardStatus'] = 'done'
        first = import_entry(self.repo, self.request)
        active = copy.deepcopy(self.request)
        active['entry'].update(id='active-new', deliveryId='NEW-WORK', reportedState='in_progress')
        active['entry']['epic']['id'] = 'EPIC-NEW'
        active['entry']['stories'][0].update(id='US-NEW', boardStatus='in_progress')
        for activity in active['entry']['activities']:
            activity['storyIds'] = ['US-NEW']
        receipt = import_entry(self.repo, active, first['storeSha256'])
        rejected = copy.deepcopy(active)
        rejected['makeCurrent'] = False
        rejected['entry'].update(id='old-rejected', deliveryId='OLD-REJECTED', reportedState='rework_required')
        rejected['entry']['epic']['id'] = 'EPIC-REJECTED'
        rejected['entry']['stories'][0]['id'] = 'US-REJECTED'
        for activity in rejected['entry']['activities']:
            activity['storyIds'] = ['US-REJECTED']
        import_entry(self.repo, rejected, receipt['storeSha256'])
        board = project_story_board(self.repo)
        live = {s['id']: s['column'] for s in board['stories'] if not s.get('historical')}
        archive = {s['id'] for s in board['stories'] if s.get('historical')}
        self.assertEqual(live, {'US-BUYER': 'done', 'US-AGENT': 'done', 'US-LATER': 'backlog',
                                'US-OBS': 'done', 'US-NEW': 'in_progress'})
        self.assertEqual(archive, {'US-REJECTED'})
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(), original_native)

    def test_explicit_history_scope_preserves_unrelated_backlog_and_original_receipts(self):
        self.fixture.approve()
        self.request['ledgerSha256'] = aim_observations.fingerprint(self.repo, aim_observations.LEDGER)
        self.entry['replacesDeliveryIds'] = ['DI-1']
        self.entry['reportedState'] = 'awaiting_owner'
        self.entry['stories'][0]['boardStatus'] = 'review'
        imported = import_entry(self.repo, self.request)
        board = project_story_board(self.repo)
        native = {story['id']:story for story in board['stories'] if not story.get('observationId')}
        self.assertTrue(native['US-BUYER']['historical'])
        self.assertEqual(native['US-BUYER']['status'], 'in_progress')
        self.assertFalse(native['US-LATER'].get('historical', False))
        self.assertEqual(native['US-LATER']['column'], 'backlog')
        current = board['stories'][-1]
        self.assertEqual(current['column'], 'review')
        self.assertTrue(current['waitingForOwner'])
        self.assertFalse(current['historical'])
        old, _ = load(self.repo)
        original_record = copy.deepcopy(old['entries'][0])
        refresh = copy.deepcopy(self.request);refresh['entry']['id']='snapshot-2'
        import_entry(self.repo, refresh, imported['storeSha256'])
        saved, _ = load(self.repo)
        self.assertEqual(saved['entries'][0], original_record)

    def test_changed_source_and_corrupt_native_stay_non_authoritative(self):
        import_entry(self.repo,self.request)
        (self.repo/self.source['path']).write_text('changed')
        b=project_story_board(self.repo)
        self.assertTrue(b['observations']['entries'][0]['stale'])
        self.assertTrue(all(n['status']=='stale' for n in b['executionGraph']['activities']))
        (self.repo/'.aim/product-backlog.json').write_text('{"broken":true}')
        b=project_story_board(self.repo)
        self.assertFalse(b['valid']);self.assertFalse(b['structuralValid'])
        self.assertEqual([s['id'] for s in b['stories']],['US-OBS'])
        self.assertFalse(b['executionGraph']['nativeEvidenceValid'])

    def test_bad_imports_preserve_both_stores(self):
        import_entry(self.repo,self.request)
        before=(self.repo/FILE).read_bytes(); _,sha=load(self.repo)
        for variant in ['cas','ledger','cycle','unknown','collision','path','extra','hash','duplicate','epic-change','story-change']:
            with self.subTest(variant=variant):
                q=copy.deepcopy(self.request); q['entry']['id']='snapshot-2'; token=sha
                if variant=='cas':token='0'*64
                if variant=='ledger':q['ledgerSha256']='0'*64
                if variant=='cycle':q['entry']['activities'][0]['dependsOn']=['owner']
                if variant=='unknown':q['entry']['activities'][0]['dependsOn']=['missing']
                if variant=='collision':q['entry']['stories'][0]['id']='US-BUYER'
                if variant=='path':q['entry']['sources'][0]['path']='.aim/../../outside'
                if variant=='extra':q['entry']['authority']='accepted'
                if variant=='hash':q['entry']['sources'][0]['sha256']='0'*64
                if variant=='duplicate':q['entry']['id']='snapshot-1'
                if variant=='epic-change':q['entry']['epic']['id']='EPIC-DIFFERENT'
                if variant=='story-change':
                    q['entry']['stories'][0]['id']='US-DIFFERENT'
                    for a in q['entry']['activities']:a['storyIds']=['US-DIFFERENT']
                with self.assertRaises((ValueError,OSError)):import_entry(self.repo,q,token)
                self.assertEqual(before,(self.repo/FILE).read_bytes())
                self.assertEqual(self.original,(self.repo/'.aim/product-backlog.json').read_bytes())

    def test_symlinked_source_and_store_reject(self):
        source=self.repo/self.source['path']; target=self.repo/'private'; target.write_text('secret')
        source.unlink();source.symlink_to(target)
        with self.assertRaises((ValueError,OSError)):import_entry(self.repo,self.request)
        source.unlink();source.write_text('Original exception plan and actual pending human decision.')
        (self.repo/FILE).symlink_to(target)
        with self.assertRaises((ValueError,OSError)):import_entry(self.repo,self.request)

    def test_refresh_preserves_history_and_old_current_selection_is_diagnostic(self):
        first=import_entry(self.repo,self.request)
        q=copy.deepcopy(self.request);q['entry']['id']='snapshot-2'
        q['entry']['reportedState']='in_progress'
        import_entry(self.repo,q,first['storeSha256'])
        data,_=load(self.repo)
        self.assertEqual(len(data['entries']),2)
        b=project_story_board(self.repo)
        self.assertEqual(b['observations']['currentId'],'snapshot-2')
        self.assertEqual(len(b['observations']['entries']),1)
        data['currentId']='snapshot-1'
        (self.repo/FILE).write_text(json.dumps(data))
        b=project_story_board(self.repo)
        self.assertTrue(b['valid'])
        self.assertEqual(len(b['stories']),3)
        self.assertTrue(b['observations']['issues'])

    def test_commit_failure_and_late_source_change_preserve_prior_snapshot(self):
        first=import_entry(self.repo,self.request)
        prior=(self.repo/FILE).read_bytes()
        q=copy.deepcopy(self.request);q['entry']['id']='snapshot-2'
        with patch('aim_observations.os.replace',side_effect=OSError('injected commit failure')):
            with self.assertRaises(OSError):import_entry(self.repo,q,first['storeSha256'])
        self.assertEqual((self.repo/FILE).read_bytes(),prior)
        self.assertEqual(list((self.repo/'.aim').glob('.observation-*')),[])
        real=aim_observations.validate_entry
        calls=0
        def change_before_commit(repo, entry, verify=True):
            nonlocal calls
            if verify:
                calls+=1
                if calls==2:(self.repo/self.source['path']).write_text('producer changed')
            return real(repo,entry,verify)
        with patch('aim_observations.validate_entry',side_effect=change_before_commit):
            with self.assertRaisesRegex(ValueError,'source changed'):import_entry(self.repo,q,first['storeSha256'])
        self.assertEqual((self.repo/FILE).read_bytes(),prior)
        self.assertEqual((self.repo/'.aim/product-backlog.json').read_bytes(),self.original)
        self.assertEqual(list((self.repo/'.aim').glob('.observation-*')),[])

if __name__=='__main__':unittest.main()
