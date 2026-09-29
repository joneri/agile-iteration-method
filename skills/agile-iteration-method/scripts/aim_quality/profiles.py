# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_quality/profiles.py
"""Read project knowledge with the same parser and schemas used by AIM."""
from __future__ import annotations

import json
from pathlib import Path

from aim_installer.yaml_lite import loads
from aim_validator.profile_contract import parse_and_validate_repo_profile
from aim_validator.schema_subset import validate
from .files import read_evidence
from .skills import BUNDLE_ROOT, role_skill_issues


def _profile_schema(schema_name: str) -> dict:
    relative = f'schemas/{schema_name}'
    if not (BUNDLE_ROOT / relative).is_file():
        relative = 'references/' + relative
    return json.loads(read_evidence(BUNDLE_ROOT, relative))


def read_repo_profile(root: Path) -> tuple[object, list]:
    """Read the shared profile using the production parser and product contract."""
    return parse_and_validate_repo_profile(
        read_evidence(root, 'aim.profile.yaml').decode('utf-8'),
        _profile_schema('aim-repo-profile.schema.json'),
    )


def check_profiles(root: Path, only: str = "all") -> dict:
    """Check both shared profiles without treating readiness as factual truth."""
    if only not in {"all", "repo", "roles"}:
        raise ValueError("profile selection must be all, repo or roles")
    diagnostics, checked = [], []
    for filename, schema_name in (
        ('aim.profile.yaml', 'aim-repo-profile.schema.json'),
        ('aim.roles.yaml', 'aim-project-roles.schema.json'),
    ):
        if only != "all" and filename != {"repo": "aim.profile.yaml", "roles": "aim.roles.yaml"}[only]:
            continue
        try:
            if filename == 'aim.profile.yaml':
                document, contract_issues = read_repo_profile(root)
                issues = [str(issue) for issue in contract_issues]
            else:
                document = loads(read_evidence(root, filename).decode('utf-8'))
                issues = [str(issue) for issue in validate(document, _profile_schema(schema_name))]
            if not issues and filename == 'aim.roles.yaml':
                issues.extend(role_skill_issues(root, document))
            diagnostics.extend({'path': filename, 'error': issue} for issue in issues)
            checked.append(filename)
        except (OSError, ValueError, UnicodeError, IndexError, RecursionError) as exc:
            diagnostics.append({'path': filename, 'error': str(exc)})
    return {'version': 1, 'valid': not diagnostics, 'checked': checked,
            'diagnostics': diagnostics, 'semanticTruthVerified': False,
            'scope': 'AIM YAML syntax, published profile schemas, repo product rules and readable role-skill bindings'}
