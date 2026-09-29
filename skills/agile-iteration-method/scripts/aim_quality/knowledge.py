# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/knowledge.py
"""Attribute scoped knowledge reuse without claiming semantic truth or executing evidence.

Stable profile entries may declare appliesTo (locality IDs, or ['repository']),
expectedUse and recheckWhen. Rules are fingerprinted individually so unrelated
profile changes do not invalidate them. Delivery record v1: claims [{category,
id, ruleSha256, sources:[{path,sha256}], observation?: {outcome: used|helped|
contradicted|not-used, summary, artifacts:[{path,sha256}]}}]. Outcomes are recorded
claims, never independently certified benefit. Supply None to inventory selected
rules and obtain their hashes; no implicit verification or observation is added.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from aim_installer.yaml_lite import loads
from .files import read_evidence
from .profiles import check_profiles
from .localities import check_localities


def rule_fingerprint(rule: dict) -> str:
    return hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def check_knowledge_use(root: Path, record: dict | None, selected_localities: list[str]) -> dict:
    if not isinstance(selected_localities, list) or not selected_localities or len(selected_localities) > 32 or any(not isinstance(x, str) or not x for x in selected_localities):
        raise ValueError('select 1 to 32 concrete locality IDs')
    profile_check = check_profiles(root, 'repo')
    if not profile_check['valid']:
        return {'version': 1, 'valid': False, 'diagnostics': profile_check['diagnostics'], 'semanticTruthVerified': False}
    locality_check = check_localities(root, selected_localities)
    if not locality_check['valid']:
        return {'version': 1, 'valid': False, 'diagnostics': locality_check['diagnostics'], 'semanticTruthVerified': False}
    selected = {x['id'] for x in locality_check['localities']}
    profile = loads(read_evidence(root, 'aim.profile.yaml').decode())['aimRepoProfile']['repoKnowledge']
    locality_ids = {x['id'] for x in profile.get('localities', [])}
    if record is not None and (not isinstance(record, dict) or type(record.get('version')) is not int or record['version'] != 1):
        raise ValueError('knowledge-use record version must be 1')
    claims = [] if record is None else record.get('claims')
    if not isinstance(claims, list) or len(claims) > 256:
        raise ValueError('claims must be a list of at most 256 records')
    indexed = {}
    for claim in claims:
        if not isinstance(claim, dict) or any(not isinstance(claim.get(k), str) or not claim[k] for k in ['category','id']):
            raise ValueError('each claim requires category and id')
        key = (claim['category'], claim['id'])
        if key in indexed:
            raise ValueError('duplicate knowledge record')
        indexed[key] = claim
    cache = {}
    def references(items):
        if not isinstance(items, list) or not 1 <= len(items) <= 32:
            raise ValueError('evidence needs 1 to 32 fingerprinted references')
        problems = []
        for ref in items:
            if not isinstance(ref, dict) or not isinstance(ref.get('path'), str) or not isinstance(ref.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256']):
                raise ValueError('evidence reference requires path and SHA-256')
            path = ref['path']
            if path not in cache:
                try:
                    cache[path] = hashlib.sha256(read_evidence(root, path)).hexdigest()
                except (OSError, ValueError) as exc:
                    cache[path] = exc
            actual = cache[path]
            if isinstance(actual, Exception):
                problems.append({'path': path, 'reason': 'missing or unsafe evidence'})
            elif actual != ref['sha256']:
                problems.append({'path': path, 'reason': 'changed since observation'})
        return problems
    rules, outside, missing_metadata, diagnostics, known = [], [], [], [], set()
    for category, entries in profile.items():
        if not isinstance(entries, list):
            continue
        for rule in entries:
            if not isinstance(rule, dict) or not isinstance(rule.get('id'), str):
                continue
            key = (category, rule['id']);known.add(key)
            scopes = rule.get('appliesTo')
            name = {'category': category, 'id': rule['id']}
            if scopes is None:
                if key in indexed:
                    diagnostics.append(dict(name, error='recorded rule has no explicit applicability'))
                missing_metadata.append(name);continue
            if not isinstance(scopes, list) or not scopes or any(not isinstance(x, str) or x not in locality_ids | {'repository'} for x in scopes) or ('repository' in scopes and len(scopes) != 1):
                diagnostics.append(dict(name, error='invalid or unknown applicability'));continue
            if 'repository' not in scopes and not selected.intersection(scopes):
                outside_entry = dict(name)
                recorded = indexed.get(key)
                if recorded is not None:
                    digest = recorded.get('ruleSha256')
                    if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                        raise ValueError('knowledge record requires ruleSha256')
                    outside_entry['ruleChangedSinceRecord'] = digest != rule_fingerprint(rule)
                    observation = recorded.get('observation')
                    if observation is not None:
                        if not isinstance(observation, dict) or not isinstance(observation.get('outcome'), str) or observation['outcome'] not in {'used','helped','contradicted','not-used'} or not isinstance(observation.get('summary'), str) or not observation['summary'].strip():
                            raise ValueError('observation requires explicit outcome and summary')
                        outside_entry['recordedOutcome'] = observation['outcome']
                        outside_entry['recordedSummary'] = observation['summary']
                    outside_entry['evidenceIntegrity'] = 'not-checked-outside-selected-scope'
                    outside_entry['requiresScopeReview'] = outside_entry['ruleChangedSinceRecord'] or outside_entry.get('recordedOutcome') == 'contradicted'
                outside.append(outside_entry);continue
            expected, triggers = rule.get('expectedUse'), rule.get('recheckWhen')
            if not isinstance(expected, str) or not expected.strip() or not isinstance(triggers, list) or not triggers or any(not isinstance(x,str) or not x.strip() for x in triggers):
                diagnostics.append(dict(name, error='selected rule requires expectedUse and recheckWhen'));continue
            result = dict(name, ruleSha256=rule_fingerprint(rule), expectedUse=expected,
                          recheckWhen=triggers, freshness='unverified', benefit='unmeasured', problems=[])
            claim = indexed.get(key)
            if claim is not None:
                if not isinstance(claim.get('ruleSha256'), str) or not re.fullmatch('[0-9a-f]{64}', claim['ruleSha256']):
                    raise ValueError('knowledge record requires ruleSha256')
                if claim['ruleSha256'] != result['ruleSha256']:
                    result['problems'].append({'reason': 'durable rule changed since observation'})
                result['problems'].extend(references(claim.get('sources')))
                observation = claim.get('observation')
                if observation is not None:
                    if not isinstance(observation, dict) or not isinstance(observation.get('outcome'), str) or observation['outcome'] not in {'used','helped','contradicted','not-used'} or not isinstance(observation.get('summary'), str) or not observation['summary'].strip():
                        raise ValueError('observation requires explicit outcome and summary')
                    result['problems'].extend(references(observation.get('artifacts')))
                    result['recordedOutcome'] = observation['outcome']
                    result['recordedSummary'] = observation['summary']
                    result['benefit'] = 'reported-only' if observation['outcome'] == 'helped' else 'unmeasured'
                    if observation['outcome'] == 'contradicted':
                        result['problems'].append({'reason': 'recorded contradiction requires review'})
                result['freshness'] = 'stale-or-contradicted' if result['problems'] else 'unchanged'
            rules.append(result)
    for category, identifier in indexed.keys() - known:
        diagnostics.append({'category': category, 'id': identifier, 'error': 'record references unknown durable rule'})
    return {'version': 1, 'valid': not diagnostics, 'diagnostics': diagnostics,
            'selectedLocalities': sorted(selected), 'rules': rules, 'outsideScope': outside,
            'missingApplicability': missing_metadata, 'filesChecked': len(cache),
            'needsReview': any(x['problems'] for x in rules),
            'outsideScopeNeedsReview': any(x.get('requiresScopeReview') for x in outside),
            'semanticTruthVerified': False, 'benefitVerified': False,
            'scope': 'Profile rule attribution, selected locality closure and evidence integrity; commands and observations are data, never executed.'}
