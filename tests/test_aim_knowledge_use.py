import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from aim_installer.seed import shared_profile_seed
from aim_installer.yaml_lite import loads
from aim_quality.files import fingerprint
from aim_quality.knowledge import check_knowledge_use, rule_fingerprint

class KnowledgeUseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'src').mkdir();(self.root/'src/api.py').write_text('def fee(): return 8\n')
        (self.root/'src/ui.py').write_text('render = True\n');(self.root/'result.txt').write_text('fee(1000)=8\n')
        self.profile=shared_profile_seed().replace('localities: []','''localities:
      - id: api
        paths:
          - src/api.py
      - id: ui
        paths:
          - src/ui.py''').replace('validation: []','''validation:
      - id: fee
        summary: At value 1000 the fee is 8
        appliesTo:
          - api
        expectedUse: Verify a known fee before changing pricing
        recheckWhen:
          - Fee schedule or calculation changes
      - id: display
        summary: UI display convention
        appliesTo:
          - ui
        expectedUse: Check visible formatting
        recheckWhen:
          - Rendering changes''')
        (self.root/'aim.profile.yaml').write_text(self.profile)
    def record(self):
        rule=loads(self.profile)['aimRepoProfile']['repoKnowledge']['validation'][0]
        return {'version':1,'claims':[{'category':'validation','id':'fee','ruleSha256':rule_fingerprint(rule),'sources':[fingerprint(self.root,'src/api.py')]}]}
    def test_scope_and_missing_observation_never_invent_benefit(self):
        result=check_knowledge_use(self.root,self.record(),['api'])
        self.assertTrue(result['valid']);self.assertEqual(len(result['rules']),1)
        self.assertEqual(result['rules'][0]['benefit'],'unmeasured');self.assertEqual(result['rules'][0]['freshness'],'unchanged')
        self.assertFalse(result['semanticTruthVerified']);self.assertFalse(result['benefitVerified'])
        self.assertEqual(result['outsideScope'],[{'category':'validation','id':'display'}])
    def test_observation_retains_contradiction_and_current_artifact_limits(self):
        record=self.record();record['claims'][0]['observation']={'outcome':'helped','summary':'Used known fee in new test','artifacts':[fingerprint(self.root,'result.txt')]}
        result=check_knowledge_use(self.root,record,['api'])
        self.assertEqual(result['rules'][0]['benefit'],'reported-only')
        self.assertFalse(result['benefitVerified'])
        record['claims'][0]['observation']['outcome']='contradicted'
        self.assertTrue(check_knowledge_use(self.root,record,['api'])['needsReview'])
        record['claims'][0]['observation']['outcome']='used';(self.root/'result.txt').write_text('different result')
        self.assertTrue(check_knowledge_use(self.root,record,['api'])['needsReview'])
    def test_unrelated_profile_edit_does_not_invalidate_selected_rule(self):
        record=self.record();(self.root/'aim.profile.yaml').write_text(self.profile.replace('UI display convention','Changed unrelated UI rule'))
        self.assertFalse(check_knowledge_use(self.root,record,['api'])['needsReview'])
        (self.root/'aim.profile.yaml').write_text(self.profile.replace('fee is 8','fee is 0'))
        self.assertTrue(check_knowledge_use(self.root,record,['api'])['needsReview'])
    def test_drift_and_unsafe_evidence(self):
        record=self.record();(self.root/'src/api.py').write_text('def fee(): return 0\n')
        self.assertTrue(check_knowledge_use(self.root,record,['api'])['needsReview'])
        record['claims'][0]['sources'][0]['path']='../outside'
        self.assertTrue(check_knowledge_use(self.root,record,['api'])['needsReview'])
    def test_inventory_and_unknown_ids(self):
        self.assertEqual(check_knowledge_use(self.root,None,['api'])['rules'][0]['freshness'],'unverified')
        record=self.record();record['claims'][0]['id']='missing'
        self.assertFalse(check_knowledge_use(self.root,record,['api'])['valid'])
    def test_changed_applicability_retains_outside_recorded_contradiction(self):
        record=self.record()
        record['claims'][0]['observation']={'outcome':'contradicted','summary':'Independent check found a false rule','artifacts':[fingerprint(self.root,'result.txt')]}
        (self.root/'aim.profile.yaml').write_text(self.profile.replace('appliesTo:\n          - api','appliesTo:\n          - ui'))
        result=check_knowledge_use(self.root,record,['api'])
        self.assertTrue(result['valid']);self.assertFalse(result['needsReview'])
        self.assertTrue(result['outsideScopeNeedsReview'])
        old=next(x for x in result['outsideScope'] if x['id']=='fee')
        self.assertTrue(old['ruleChangedSinceRecord']);self.assertEqual(old['recordedOutcome'],'contradicted')
        self.assertEqual(old['evidenceIntegrity'],'not-checked-outside-selected-scope')
        self.assertEqual(result['filesChecked'],0)
    def test_malformed_outcome_has_structured_validation_error(self):
        record=self.record();record['claims'][0]['observation']={'outcome':[],'summary':'bad','artifacts':[]}
        with self.assertRaises(ValueError):check_knowledge_use(self.root,record,['api'])
    def test_no_commands_executed(self):
        record=self.record();record['claims'][0]['observation']={'outcome':'used','summary':'touch /tmp/this-is-not-a-command','artifacts':[fingerprint(self.root,'result.txt')]}
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        check_knowledge_use(self.root,record,['api'])
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

if __name__=='__main__':unittest.main()
