#!/usr/bin/env python3
"""Read-only product-file observer and evidence-based AIM journey report.

This developer tool never dispatches work or modifies the observed repository.
Question/repair classification is a human review of the complete transcript,
not a keyword heuristic. An absent review produces unknown counts, not zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamps must include a timezone.')
    return result


def append_event(output: Path, kind: str, **data) -> None:
    with output.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'at': timestamp(), 'kind': kind, **data}) + '\n')


def observe(repo: Path, files: list[str], output: Path, duration: float, interval: float) -> None:
    root = repo.resolve(strict=True)
    if output.resolve().is_relative_to(root):
        raise ValueError('Observation output must be outside the observed repository.')
    paths = []
    for name in files:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Product files must be contained relative paths.')
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Product paths must not escape the repository.')
        paths.append((name, path))
    if duration <= 0 or interval <= 0:
        raise ValueError('Duration and interval must be positive.')
    seen = {}
    append_event(output, 'observation_started', files=files, intervalSeconds=interval)
    deadline = time.monotonic() + duration
    initial = True
    while time.monotonic() < deadline:
        for name, path in paths:
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                append_event(output, 'observation_gap', file=name, reason='path escaped')
                return
            if not path.is_file():
                continue
            content = path.read_bytes()
            if not content:
                continue
            digest = hashlib.sha256(content).hexdigest()
            if digest != seen.get(name):
                birth = getattr(path.stat(), 'st_birthtime', None)
                append_event(output, 'product_baseline' if initial else 'product_observed',
                             file=name, sha256=digest, bytes=len(content),
                             createdAt=datetime.fromtimestamp(birth, timezone.utc).isoformat() if birth else None)
                seen[name] = digest
        initial = False
        time.sleep(interval)
    append_event(output, 'observation_ended')


def report(events: list[dict], review: dict | None = None) -> dict:
    ordered = sorted(events, key=lambda event: parse_time(event['at']))
    authorized = [e for e in ordered if e['kind'] == 'authorized']
    if len(authorized) != 1:
        raise ValueError('Exactly one explicit authorization event is required.')
    start = parse_time(authorized[0]['at'])
    after = [e for e in ordered if parse_time(e['at']) >= start]
    products = [e for e in after if e['kind'] == 'product_observed']
    observation_started = any(e['kind'] == 'observation_started' and parse_time(e['at']) <= start for e in ordered)
    gaps = any(e['kind'] in ('observation_gap', 'product_baseline') for e in ordered)
    # An observer which stopped before the first sighting cannot prove latency.
    if products:
        gaps |= any(e['kind'] == 'observation_ended' and parse_time(e['at']) < parse_time(products[0]['at']) for e in after)
    latency = round((parse_time(products[0]['at']) - start).total_seconds(), 3) if products and observation_started and not gaps else None
    latency_source = 'continuous_polling' if latency is not None else None
    for product in products:
        if not product.get('createdAt'):
            continue
        created = parse_time(product['createdAt'])
        if start <= created <= parse_time(product['at']):
            candidate = round((created - start).total_seconds(), 3)
            if latency is None or candidate < latency:
                latency = candidate
                latency_source = 'filesystem_birthtime'
    review = review or {}
    reviewed = review.get('completeTranscriptReviewed') is True and bool(review.get('transcriptSha256'))
    classified = {}
    for name in ('unnecessaryQuestions', 'administrativeRepairs'):
        findings = review.get(name)
        if reviewed and isinstance(findings, list) and all(isinstance(f, dict) and f.get('evidence') and f.get('reason') for f in findings):
            classified[name] = {'count': len(findings), 'findings': findings}
        else:
            classified[name] = {'count': None, 'findings': findings, 'reason': 'Complete transcript review with evidence required.'}
    return {
        'authorizationAt': authorized[0]['at'],
        'firstProductCodeSeconds': latency,
        'latencySource': latency_source,
        'latencyMeaning': 'New product file creation or first nonempty observation; includes outage and operator delay. File creation is not usable code or quality.',
        'firstProductEvidence': products[0] if products else None,
        'classification': classified,
        'interventions': [e for e in after if e['kind'] == 'operator_intervention'],
        'injectedInterruptions': [e for e in after if e['kind'] == 'interruption'],
        'dispatches': [e for e in after if e['kind'] == 'dispatch'],
        'verification': [e for e in after if e['kind'] == 'product_verified'],
        'limits': review.get('limits', []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    watch = sub.add_parser('observe')
    watch.add_argument('--repo', type=Path, required=True)
    watch.add_argument('--file', action='append', required=True)
    watch.add_argument('--output', type=Path, required=True)
    watch.add_argument('--duration', type=float, default=900)
    watch.add_argument('--interval', type=float, default=0.25)
    summarize = sub.add_parser('report')
    summarize.add_argument('events', type=Path)
    summarize.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.command == 'observe':
        observe(args.repo, args.file, args.output, args.duration, args.interval)
    else:
        events = [json.loads(line) for line in args.events.read_text().splitlines() if line.strip()]
        review = json.loads(args.review.read_text()) if args.review else None
        print(json.dumps(report(events, review), indent=2))


if __name__ == '__main__':
    main()
