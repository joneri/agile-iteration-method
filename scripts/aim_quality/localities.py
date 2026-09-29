"""Cheap locality reference inspection; existence does not establish meaning."""
from __future__ import annotations

import stat
from pathlib import Path

from aim_installer.yaml_lite import loads
from .files import read_evidence
from .profiles import check_profiles


def _path_kind(root: Path, value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('expected a contained relative literal path')
    if any(character in value for character in '*?['):
        raise ValueError('globs are not literal locality paths')
    current = root.resolve()
    for component in path.parts:
        current = current / component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, 'st_file_attributes', 0) & 1024:
            raise ValueError('locality path traverses a link or reparse point')
    if stat.S_ISREG(metadata.st_mode):
        return 'file'
    if stat.S_ISDIR(metadata.st_mode):
        return 'directory'
    raise ValueError('locality path is not a regular file or directory')


def check_localities(root: Path, selected: list[str] | None = None) -> dict:
    report = check_profiles(root, 'repo')
    report.update(scope='Locality literal paths and declared dependency references; metadata snapshot only',
                  localities=[], overlaps=[], semanticTruthVerified=False)
    if not report['valid']:
        return report
    entries = loads(read_evidence(root, 'aim.profile.yaml').decode('utf-8'))['aimRepoProfile']['repoKnowledge']['localities']
    diagnostics = report['diagnostics']
    if len(entries) > 512:
        report.update(valid=False, diagnostics=[{"path": "localities", "error": "more than 512 entries; narrow the profile"}])
        return report
    by_id = {}
    for entry in entries:
        if entry['id'] in by_id:
            diagnostics.append({'path': entry['id'], 'error': 'duplicate locality id'})
        by_id[entry['id']] = entry
    pending = list(selected) if selected is not None else list(by_id)
    visited, owners = set(), []
    reference_count = 0
    while pending:
        identifier = pending.pop(0)
        if identifier in visited:
            continue
        visited.add(identifier)
        if identifier not in by_id:
            diagnostics.append({'path': identifier, 'error': 'unknown locality reference'})
            continue
        entry = by_id[identifier]
        item = {'id': identifier, 'references': [], 'dependsOn': []}
        for field in ('paths', 'tests', 'dependsOn'):
            values = entry.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
                diagnostics.append({'path': identifier + '.' + field, 'error': 'expected a list of nonempty strings'})
                continue
            if field == 'dependsOn':
                item[field] = values
                pending.extend(values)
                continue
            for value in values:
                reference_count += 1
                if reference_count > 4096:
                    report["valid"] = False
                    diagnostics.append({"path": identifier, "error": "reference budget exceeded; narrow locality selection"})
                    return report
                reference = {'field': field, 'path': value}
                try:
                    reference['kind'] = _path_kind(root, value)
                    if field == 'paths':
                        owners.append((identifier, Path(value)))
                except (OSError, ValueError) as exc:
                    reference['error'] = str(exc)
                    diagnostics.append({'path': identifier + '.' + field, 'reference': value, 'error': str(exc)})
                item['references'].append(reference)
        if not item['references']:
            diagnostics.append({'path': identifier, 'error': 'no inspectable code or test paths; label alone is insufficient'})
        report['localities'].append(item)
    # Shared modules and nested ownership are useful evidence, not conflicts by default.
    for index, (left_id, left) in enumerate(owners):
        for right_id, right in owners[index + 1:]:
            if left_id != right_id and (left == right or left in right.parents or right in left.parents):
                if len(report['overlaps']) >= 256:
                    report['overlapsTruncated'] = True
                    report['valid'] = not diagnostics
                    return report
                report['overlaps'].append({'localities': [left_id, right_id], 'paths': [str(left), str(right)]})
    report['valid'] = not diagnostics
    return report
